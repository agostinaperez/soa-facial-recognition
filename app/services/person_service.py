# Lógica compartida de creación de personas (Person), usada tanto por el CRUD
# admin/operator (routes_s5.create_person) como por el alta de usuarios (routes_auth).

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.entities import Person


def get_or_create_person(
    db: Session,
    nombre: str,
    apellido: str,
    email: str,
    extra: Optional[Dict[str, Any]] = None,
    keycloak_user_id: Optional[str] = None,
) -> Person:
    """Busca una Person por email; si no existe, la crea.

    Si se pasa keycloak_user_id y la persona ya existía sin vincular, la vincula.
    """
    person = db.query(Person).filter(Person.email == email).first()

    if person:
        if keycloak_user_id and not person.keycloak_user_id:
            person.keycloak_user_id = keycloak_user_id
            db.commit()
            db.refresh(person)
        return person

    person = Person(
        nombre=nombre,
        apellido=apellido,
        email=email,
        extra=extra,
        keycloak_user_id=keycloak_user_id,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person
