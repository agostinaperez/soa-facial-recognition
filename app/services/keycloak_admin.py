# Cliente para la Admin REST API de Keycloak.
# Usa client_credentials grant del client "soa" (mismo KEYCLOAK_CLIENT_ID/SECRET que ya
# tiene la API) contra su service account, que debe tener asignados los roles de client
# "realm-management": manage-users, view-users, query-users (ver keycloak-setup.sh).

import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException, status

from security import (
    KEYCLOAK_CLIENT_ID,
    KEYCLOAK_CLIENT_SECRET,
    KEYCLOAK_REALM,
    KEYCLOAK_SERVER_URL,
)

_TOKEN_URL = f"{KEYCLOAK_SERVER_URL.rstrip('/')}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
_ADMIN_BASE = f"{KEYCLOAK_SERVER_URL.rstrip('/')}/admin/realms/{KEYCLOAK_REALM}"
_TIMEOUT = 15

# Roles propios de la app. Todo usuario de Keycloak trae además roles de
# infraestructura del realm (p. ej. "default-roles-soa", "offline_access",
# "uma_authorization") que no son relevantes para nuestra autorización.
APP_ROLES = {"admin", "operator", "viewer"}

_admin_token: Optional[str] = None
_admin_token_expires_at: float = 0.0


def _get_admin_token() -> str:
    """Obtiene (y cachea) un token de service account con permisos realm-management."""
    global _admin_token, _admin_token_expires_at

    if _admin_token and time.time() < _admin_token_expires_at:
        return _admin_token

    resp = httpx.post(
        _TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
        },
        timeout=_TIMEOUT,
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo autenticar contra la Admin API de Keycloak "
            "(revisar que el client 'soa' tenga service accounts habilitado)",
        )
    data = resp.json()
    _admin_token = data["access_token"]
    # Refrescar 30s antes de que expire para evitar condiciones de carrera.
    _admin_token_expires_at = time.time() + max(data.get("expires_in", 60) - 30, 10)
    return _admin_token


def _admin_headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {_get_admin_token()}"}


def create_keycloak_user(
    username: str,
    email: str,
    password: str,
    roles: List[str],
    first_name: str = "",
    last_name: str = "",
) -> str:
    """Crea un usuario en el realm 'soa', le setea password y le asigna roles de realm.

    Devuelve el id (sub) del usuario creado.
    """
    with httpx.Client(timeout=_TIMEOUT) as client:
        create_resp = client.post(
            f"{_ADMIN_BASE}/users",
            headers=_admin_headers(),
            json={
                "username": username,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": True,
                "requiredActions": [],
            },
        )
        if create_resp.status_code == 409:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un usuario de Keycloak con ese username o email",
            )
        if create_resp.status_code != 201:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al crear el usuario en Keycloak: {create_resp.text}",
            )

        location = create_resp.headers.get("Location", "")
        user_id = location.rstrip("/").rsplit("/", 1)[-1]
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Keycloak no devolvió el id del usuario creado",
            )

        password_resp = client.put(
            f"{_ADMIN_BASE}/users/{user_id}/reset-password",
            headers=_admin_headers(),
            json={"type": "password", "value": password, "temporary": False},
        )
        if password_resp.status_code != 204:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al setear la contraseña en Keycloak: {password_resp.text}",
            )

        if roles:
            _assign_realm_roles(client, user_id, roles)

    return user_id


def _assign_realm_roles(client: httpx.Client, user_id: str, roles: List[str]) -> None:
    role_reps: List[Dict[str, Any]] = []
    for role_name in roles:
        role_resp = client.get(
            f"{_ADMIN_BASE}/roles/{role_name}", headers=_admin_headers()
        )
        if role_resp.status_code != 200:
            continue
        role_reps.append(role_resp.json())

    if not role_reps:
        return

    assign_resp = client.post(
        f"{_ADMIN_BASE}/users/{user_id}/role-mappings/realm",
        headers=_admin_headers(),
        json=role_reps,
    )
    if assign_resp.status_code not in (204,):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al asignar roles en Keycloak: {assign_resp.text}",
        )


def exchange_token_for_user(keycloak_user_id: str) -> Dict[str, Any]:
    """Token Exchange (RFC 8693, variante impersonation): usa el token del propio
    service account para pedirle a Keycloak un access_token genuino (RS256) para
    otro usuario, identificado solo por su id, sin necesitar su contraseña.

    Requiere KC_FEATURES=token-exchange en el servidor y el rol de client
    "impersonation" (realm-management) asignado al service account de "soa".
    """
    resp = httpx.post(
        _TOKEN_URL,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "client_id": KEYCLOAK_CLIENT_ID,
            "client_secret": KEYCLOAK_CLIENT_SECRET,
            "subject_token": _get_admin_token(),
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "requested_subject": keycloak_user_id,
        },
        timeout=_TIMEOUT,
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo emitir un token de Keycloak para el usuario: {resp.text}",
        )
    return resp.json()


def get_user_realm_roles(keycloak_user_id: str) -> List[str]:
    """Devuelve los roles de realm propios de la app (admin/operator/viewer) asignados
    a un usuario de Keycloak, sin los roles de infraestructura del realm."""
    resp = httpx.get(
        f"{_ADMIN_BASE}/users/{keycloak_user_id}/role-mappings/realm",
        headers=_admin_headers(),
        timeout=_TIMEOUT,
    )
    if resp.status_code != 200:
        return []
    return [r["name"] for r in resp.json() if r.get("name") in APP_ROLES]


def list_users() -> List[Dict[str, Any]]:
    """Lista los usuarios del realm con sus roles de realm (username/email/id/roles)."""
    resp = httpx.get(f"{_ADMIN_BASE}/users", headers=_admin_headers(), timeout=_TIMEOUT)
    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al listar usuarios de Keycloak: {resp.text}",
        )
    users = resp.json()
    result = []
    for u in users:
        result.append(
            {
                "id": u["id"],
                "username": u.get("username"),
                "email": u.get("email"),
                "roles": get_user_realm_roles(u["id"]),
            }
        )
    return result
