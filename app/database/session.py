
# Configuración de SQLAlchemy:
# engine, SessionLocal, Base declarativa y generador get_db para inyección de dependencias en FastAPI.

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# URL de conexión a MySQL.
# Se sobreescribe con la variable de entorno DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://admin:admin@localhost:3306/soa_db")

# Engine (objeto que sabe como conectarse a mysql) compartido por toda la aplicación
engine = create_engine(DATABASE_URL)

# Fábrica de sesiones (autocommit y autoflush desactivados)
# cada sesión es como una transacción independiente con la DB que se cierra al finalizar el request.
# el autocommit en falso hace q cada vez q yo haga un cambio en la DB, tenga que hacer un commit explícito para que se guarde.
# onda nuevo = Usuario(nombre="Agos")
# db.add(nuevo)
# db.commit()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base guardada para que los modelos la extiendan y SQLAlchemy pueda mapearlos a tablas.
# guarda los metadatos de los modelos y se usa para crear las tablas en la DB.
Base = declarative_base()


def get_db():
    # acá si obtengo una sesión real de la fábrica de sesiones
    # Uso en rutas:
    # def mi_endpoint(db: Session = Depends(get_db)):
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
