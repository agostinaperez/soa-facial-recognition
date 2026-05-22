
# Configuración de SQLAlchemy:
# engine, SessionLocal, Base declarativa y generador get_db para inyección de dependencias en FastAPI.

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

MYSQL_USER = os.getenv("MYSQL_USER", "admin")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "admin")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "soa_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:3306/{MYSQL_DATABASE}"
)

# Engine (objeto que sabe como conectarse a mysql) compartido por toda la aplicación
engine = create_engine(DATABASE_URL)

# Fábrica de sesiones (autocommit y autoflush desactivados)
# cada sesión es como una transacción independiente con la DB que se cierra al finalizar el request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base guardada para que los modelos la extiendan y SQLAlchemy pueda mapearlos a tablas.
Base = declarative_base()

def get_db():
    # acá si obtengo una sesión real de la fábrica de sesiones
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()