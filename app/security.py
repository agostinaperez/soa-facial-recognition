import os
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwk, jwt

#ESTE ES EL NÚCLEO DE AUTENTICACIÓN Y AUTORIZACIÓN.
#lee variables de entorno para keycloak y valida los tokens (RS256) que emite.

# Keycloak OIDC config (desde .env o docker-compose).
KEYCLOAK_SERVER_URL: str = os.getenv("KEYCLOAK_SERVER_URL", "")
KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "")
KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "")
KEYCLOAK_CLIENT_SECRET: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_JWKS_CACHE_TTL: int = int(os.getenv("KEYCLOAK_JWKS_CACHE_TTL", "600"))

bearer_scheme = HTTPBearer(auto_error=False)


#descarga y cachea las claves públicas de keycloak
class JWKSClient:
    """Cliente caché de JWKS de Keycloak. Refresca cada KEYCLOAK_JWKS_CACHE_TTL segundos."""

    def __init__(self) -> None:
        self._jwks_url: str = (
            f"{KEYCLOAK_SERVER_URL.rstrip('/')}"
            f"/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
        )
        self._keys: Dict[str, Any] = {}
        self._fetched_at: float = 0.0

    def _should_refetch(self) -> bool:
        return (time.time() - self._fetched_at) > KEYCLOAK_JWKS_CACHE_TTL

    def _fetch_jwks(self) -> None:
        try:
            resp = httpx.get(self._jwks_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo obtener JWKS desde Keycloak: {exc}",
            )
        self._keys = {}
        for jwk_dict in data.get("keys", []):
            kid = jwk_dict.get("kid")
            if kid:
                self._keys[kid] = jwk.construct(jwk_dict)
        self._fetched_at = time.time()

    def get_key(self, kid: str) -> Any:
        if self._should_refetch() or kid not in self._keys:
            self._fetch_jwks()
        key = self._keys.get(kid)
        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token firmado con una clave (kid) desconocida",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return key


_jwks_client = JWKSClient()

#valida un token de Keycloak: busca la clave pública del cliente, verifica firma, expiración, y q esté en el realm

def decode_and_validate_jwt(token: str) -> Dict[str, Any]:
    """Decodifica y valida un JWT RS256 emitido por Keycloak."""
    try:
        headers = jwt.get_unverified_header(token)
        kid = headers.get("kid")
        alg = headers.get("alg", "RS256")

        if alg == "RS256":
            # Token de Keycloak: validar con JWKS público.
            if not kid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token RSA sin campo 'kid' en el header",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            public_key = _jwks_client.get_key(kid)
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=KEYCLOAK_CLIENT_ID,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": False,
                    "verify_aud": True,
                    "require_exp": True,
                    "require_iss": True,
                },
            )
            # Keycloak en start-dev usa el Host header como issuer.
            # Validamos manualmente que el path contenga /realms/{realm}.
            expected_iss = f"/realms/{KEYCLOAK_REALM}"
            if expected_iss not in (payload.get("iss") or ""):
                raise jwt.JWTClaimsError(
                    f"El issuer del token no corresponde al realm '{KEYCLOAK_REALM}'"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Algoritmo de firma no soportado: {alg}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token ha expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTClaimsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Reclamo invalido en el token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalido: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """Dependencia: extrae y valida el token del header Authorization."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere un token de acceso. Envie el header: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_and_validate_jwt(credentials.credentials)


def get_user_roles(user: Dict[str, Any]) -> set:
    """Extrae el set de roles (realm + client) de un token ya decodificado."""
    realm_roles: List[str] = (user.get("realm_access") or {}).get("roles") or []
    resource_roles: List[str] = []
    if KEYCLOAK_CLIENT_ID:
        resource_access = user.get("resource_access") or {}
        client_roles = resource_access.get(KEYCLOAK_CLIENT_ID, {})
        resource_roles = client_roles.get("roles") or []
    return set(realm_roles + resource_roles)


def user_has_any_role(user: Dict[str, Any], roles: List[str]) -> bool:
    return bool(get_user_roles(user).intersection(roles))


def require_roles(allowed_roles: List[str]) -> callable:
    """Factory de dependencia: requiere que el token tenga al menos uno de los roles listados."""
    def _role_checker(
        user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        if not user_has_any_role(user, allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acceso denegado. Se requiere uno de los roles: "
                    f"{', '.join(allowed_roles)}"
                ),
            )
        return user

    return _role_checker


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[Dict[str, Any]]:
    """Similar a get_current_user pero no falla si no hay token."""
    if credentials is None:
        return None
    try:
        return decode_and_validate_jwt(credentials.credentials)
    except HTTPException:
        return None
