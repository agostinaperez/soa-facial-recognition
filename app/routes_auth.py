import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.session import get_db
from models.entities import Person
from schemas.dtos import (
    AuthMeResponse,
    FaceLoginRequest,
    FaceLoginResponse,
    FaceVerifyRequest,
    FaceVerifyResponse,
    KeycloakLinkRequest,
    KeycloakLinkResponse,
    PersonResponse,
)
from security import (
    create_face_auth_token,
    get_current_user,
    require_roles,
)
from worker.celery_app import celery_app

router = APIRouter()

# Roles asignados al token de face-auth (por defecto "operator").
FACE_AUTH_DEFAULT_ROLES = os.getenv("FACE_AUTH_DEFAULT_ROLES", "operator").split(",")

#endpoint para autenticar a una persona por su rostro
#recibe la imágen, la manda al worker que hace el reconocimiento facial y devuelve el personId
#si la persona con ese personId tiene un keycloak_user_id vinculado,
#llama a security.py y genera un token local con create_face_auth_token
@router.post("/auth/face/login", response_model=FaceLoginResponse)
def face_login(body: FaceLoginRequest, db: Session = Depends(get_db)):
    task = celery_app.send_task(
        "worker.tasks.face_recognition_task",
        args=[body.image, body.threshold],
    )
    result = task.get(timeout=30)

    if "error" in result:
        raise HTTPException(status_code=401, detail="No se pudo identificar el rostro")

    person_id = result.get("personId")
    if not person_id:
        raise HTTPException(status_code=401, detail="Rostro no reconocido")

    person = db.query(Person).filter(Person.personId == person_id).first()
    if not person:
        raise HTTPException(status_code=401, detail="Persona no encontrada")

    # La persona debe tener un keycloak_user_id vinculado (vía /auth/link-keycloak).
    if not person.keycloak_user_id:
        raise HTTPException(
            status_code=401,
            detail="La persona no tiene un usuario de Keycloak vinculado. "
            "Asocie un personId con su usuario de Keycloak primero.",
        )

    # Genera un token HS256 firmado localmente (no Keycloak).
    token = create_face_auth_token(
        keycloak_user_id=person.keycloak_user_id,
        email=person.email,
        preferred_username=f"{person.nombre} {person.apellido}",
        roles=FACE_AUTH_DEFAULT_ROLES,
    )

    return FaceLoginResponse(
        access_token=token,
        expires_in=3600,
        personId=person.personId,
        nombre=person.nombre,
        apellido=person.apellido,
    )

#PRUEBA DE VIDA: verificar q el dueño del token es quien dice ser
#pide el token con el rol, busca a la persona vinculada al keycloak_user_id, envía la imágen al worker para reconocimiento facial
#compara el personId devuelto por el worker con el personid de la persona del token. Si coinciden, está verificado 
#a esto lo puedo usar si me autentico con el login, y después quiero acceder (en la interfaz web) a una zona restringida, como para re-validar
@router.post("/auth/face/verify", response_model=FaceVerifyResponse)
def face_verify(
    body: FaceVerifyRequest,
    user: dict = Depends(require_roles(["admin", "operator", "viewer"])),
    db: Session = Depends(get_db),
):
    # Verifica que el rostro en la imagen corresponde a la persona vinculada al token.
    keycloak_user_id = user.get("sub")
    if not keycloak_user_id:
        raise HTTPException(status_code=401, detail="Token sin sub claim")

    person = db.query(Person).filter(
        Person.keycloak_user_id == keycloak_user_id
    ).first()
    if not person:
        raise HTTPException(
            status_code=404,
            detail="No hay una persona vinculada a este usuario de Keycloak",
        )

    task = celery_app.send_task(
        "worker.tasks.face_recognition_task",
        args=[body.image, body.threshold],
    )
    result = task.get(timeout=30)

    if "error" in result:
        return FaceVerifyResponse(
            verified=False,
            confidence=0.0,
            message="No se pudo procesar la imagen",
        )

    matched_person_id = result.get("personId")
    confidence = result.get("confidence", 0.0)

    # Compara el personId detectado con el de la persona vinculada.
    if matched_person_id == person.personId:
        return FaceVerifyResponse(
            verified=True,
            confidence=confidence,
            message="Rostro verificado correctamente",
        )

    return FaceVerifyResponse(
        verified=False,
        confidence=confidence,
        message="El rostro no coincide con la persona vinculada",
    )

#asociar un personId con un user de keycloak. busca a person, verifica q no tenga otro user id, asigna el user id.
@router.post("/auth/link-keycloak", response_model=KeycloakLinkResponse)
def link_keycloak(
    body: KeycloakLinkRequest,
    user: dict = Depends(require_roles(["admin", "operator"])),
    db: Session = Depends(get_db),
):
    keycloak_user_id = user.get("sub")
    if not keycloak_user_id:
        raise HTTPException(status_code=401, detail="Token sin sub claim")

    # El mismo keycloak_user_id no puede estar vinculado a otra persona.
    existing = db.query(Person).filter(
        Person.keycloak_user_id == keycloak_user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Este usuario de Keycloak ya esta vinculado a la persona {existing.personId}",
        )

    person = db.query(Person).filter(Person.personId == body.personId).first()
    if not person:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    # Una persona no puede tener dos vínculos.
    if person.keycloak_user_id:
        raise HTTPException(
            status_code=409,
            detail=f"La persona {person.personId} ya esta vinculada a otro usuario de Keycloak",
        )

    person.keycloak_user_id = keycloak_user_id
    db.commit()

    return KeycloakLinkResponse(
        personId=person.personId,
        keycloak_user_id=keycloak_user_id,
        message="Vinculacion exitosa entre persona y usuario de Keycloak",
    )

# Devuelve info del usuario autenticado y su persona vinculada (si existe). devuelve el sub (sujeto, es como el userId)
@router.get("/auth/me", response_model=AuthMeResponse)
def auth_me(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    keycloak_user_id = user.get("sub")
    realm_roles = (user.get("realm_access") or {}).get("roles") or []

    linked_person = None
    if keycloak_user_id:
        person = db.query(Person).filter(
            Person.keycloak_user_id == keycloak_user_id
        ).first()
        if person:
            linked_person = PersonResponse.model_validate(person)

    return AuthMeResponse(
        sub=keycloak_user_id or "",
        email=user.get("email"),
        preferred_username=user.get("preferred_username"),
        roles=realm_roles,
        linked_person=linked_person,
    )


@router.delete("/auth/link-keycloak", status_code=200)
def unlink_keycloak(
    user: dict = Depends(require_roles(["admin", "operator"])),
    db: Session = Depends(get_db),
):
    # Desvincula la persona del usuario de Keycloak.
    keycloak_user_id = user.get("sub")
    person = db.query(Person).filter(
        Person.keycloak_user_id == keycloak_user_id
    ).first()
    if not person:
        raise HTTPException(
            status_code=404,
            detail="No hay una persona vinculada a este usuario",
        )
    person.keycloak_user_id = None
    db.commit()
    return {"message": "Vinculacion eliminada correctamente"}
