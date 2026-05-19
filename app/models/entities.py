
# Modelos SQLAlchemy para las tablas frames, detections y persons.
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.session import Base

#Tabla frames: Representa una imagen recibida por la API, almacena los metadatos.
# id frame, modelo usado, coordenadas, metadatos extra (json libre), URL de imagen en seaweed, timestamp de creación.
class Frame(Base):
    
    __tablename__ = "frames"

    frameId = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    image_url = Column(String(500), nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    #relacion oneToMany con detections, cascade delete para eliminar detecciones al borrar un frame
    detections = relationship(
        "Detection",
        back_populates="frame",
        cascade="all, delete-orphan",
    )

#Tabla detections: detección individual producida por YOLO.
#id detección, id del frame padre, clase detectada (acá se haria el embedding i guess), nivel de confianza, bounding box (json con coordenadas x1,y1,x2,y2).
class Detection(Base):
    
    __tablename__ = "detections"

    detectionId = Column(Integer, primary_key=True, autoincrement=True)
    frame_id = Column(
        Integer,
        ForeignKey("frames.frameId", ondelete="CASCADE"),
        nullable=False,
    )
    class_name = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)
    bounding_box = Column(JSON, nullable=False)
    #relacion manyToOne con frame, back_populates para acceso bidireccional
    frame = relationship("Frame", back_populates="detections")


class Person(Base):

    __tablename__ = "persons"

    personId = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    extra = Column(JSON, nullable=True)
