
#Servicio 5:
# 5.1 CRUD de personas
# POST /persons — crea una nueva persona
# GET  /persons/{personId} — obtiene una persona por ID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.session import get_db
from models.entities import Person
from schemas.dtos import PersonCreate, PersonResponse

router = APIRouter()


@router.post("/persons", response_model=PersonResponse, status_code=201)
def create_person(body: PersonCreate, db: Session = Depends(get_db)) -> Person:
    person = Person(
        nombre=body.nombre,
        apellido=body.apellido,
        email=body.email,
        extra=body.extra,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


@router.get("/persons/{personId}", response_model=PersonResponse)
def get_person(personId: str, db: Session = Depends(get_db)) -> Person:
    person = db.query(Person).filter(Person.personId == personId).first()
    if not person:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return person
