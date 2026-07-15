from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.session import get_db
from models.entities import Person
from schemas.dtos import (
    AuthMeResponse,
    CreateKeycloakUserRequest,
    CreateKeycloakUserResponse,
    FaceLoginRequest,
    FaceLoginResponse,
    FaceVerifyRequest,
    FaceVerifyResponse,
    KeycloakLinkRequest,
    KeycloakLinkResponse,
    KeycloakUserSummary,
    PersonResponse,
)
from security import (
    get_current_user,
    require_roles,
)
from services.keycloak_admin import (
    create_keycloak_user,
    exchange_token_for_user,
    list_users,
)
from services.person_service import get_or_create_person
from worker.celery_app import celery_app

router = APIRouter()

#endpoint para autenticar a una persona por su rostro
#recibe la imágen, la manda al worker que hace el reconocimiento facial y devuelve el personId
#si la persona con ese personId tiene un keycloak_user_id vinculado,
#le pide a Keycloak (Token Exchange) un access_token real para ese usuario
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

    # Token Exchange: le pedimos a Keycloak un access_token genuino (RS256)
    # para este usuario, con sus roles reales, sin necesitar su contraseña.
    exchanged = exchange_token_for_user(person.keycloak_user_id)

    return FaceLoginResponse(
        access_token=exchanged["access_token"],
        expires_in=exchanged.get("expires_in", 300),
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
#si no se manda personId, se busca automaticamente una persona cuyo email coincida con el
#email del token (autoservicio: cualquier usuario autenticado puede vincular su propia cuenta).
@router.post("/auth/link-keycloak", response_model=KeycloakLinkResponse)
def link_keycloak(
    body: Optional[KeycloakLinkRequest] = None,
    user: dict = Depends(require_roles(["admin", "operator", "viewer"])),
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

    person_id = body.personId if body else None
    if person_id:
        person = db.query(Person).filter(Person.personId == person_id).first()
        if not person:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
    else:
        email = user.get("email")
        if not email:
            raise HTTPException(
                status_code=400,
                detail="El token no tiene email; no se puede vincular automaticamente. "
                "Especifica un personId.",
            )
        person = db.query(Person).filter(Person.email == email).first()
        if not person:
            raise HTTPException(
                status_code=404,
                detail="No hay ninguna persona con tu email. Pedile al administrador "
                "que te cree una primero.",
            )

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
    user: dict = Depends(require_roles(["admin", "operator", "viewer"])),
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


# Alta de usuarios: crea el usuario en Keycloak (username/password/roles) y su
# Person correspondiente, ya vinculados por keycloak_user_id (sin depender de que
# los emails coincidan, a diferencia del auto-link de /auth/link-keycloak).
@router.post("/auth/users", response_model=CreateKeycloakUserResponse, status_code=201)
def create_user(
    body: CreateKeycloakUserRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(["admin"])),
) -> CreateKeycloakUserResponse:
    existing_person = db.query(Person).filter(Person.email == body.email).first()
    if existing_person and existing_person.keycloak_user_id:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe una persona ({existing_person.personId}) con ese "
            "email vinculada a otro usuario de Keycloak",
        )

    keycloak_user_id = create_keycloak_user(
        username=body.username,
        email=body.email,
        password=body.password,
        roles=body.roles,
        first_name=body.nombre,
        last_name=body.apellido,
    )

    person = get_or_create_person(
        db,
        nombre=body.nombre,
        apellido=body.apellido,
        email=body.email,
        keycloak_user_id=keycloak_user_id,
    )

    return CreateKeycloakUserResponse(
        keycloak_user_id=keycloak_user_id,
        username=body.username,
        email=body.email,
        roles=body.roles,
        person=PersonResponse.model_validate(person),
    )


@router.get("/auth/users", response_model=list[KeycloakUserSummary])
def list_keycloak_users(
    _: dict = Depends(require_roles(["admin"])),
) -> list[KeycloakUserSummary]:
    return [KeycloakUserSummary(**u) for u in list_users()]
