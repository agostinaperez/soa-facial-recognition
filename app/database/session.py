
# Configuración de SQLAlchemy:
# engine, SessionLocal, Base declarativa y generador get_db para inyección de dependencias en FastAPI.

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

MYSQL_USER = os.getenv("MYSQL_USER", "admin")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "admin")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "soa_db")


DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 10))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 5))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", 3600))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", 30))

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:3306/{MYSQL_DATABASE}"
)

# Engine (objeto que sabe como conectarse a mysql) compartido por toda la aplicación
engine = create_engine(DATABASE_URL,
    # --- pool_size ---
    # Variable de entorno: DB_POOL_SIZE (Por defecto: 10)
    # El tamaño base del pool de conexiones.
    # Define el número de conexiones físicas a la base de datos que 
    # se mantendrán persistentemente abiertas en memoria. Si la app está inactiva, 
    # este número de conexiones seguirá listo para usarse instantáneamente.
    pool_size=DB_POOL_SIZE,
    
    # --- max_overflow ---
    # Variable de entorno: DB_MAX_OVERFLOW (Por defecto: 5)
    # El límite de desbordamiento permitido.
    # Si las conexiones del `pool_size` están siendo usadas al mismo 
    # tiempo por peticiones concurrentes, SQLAlchemy creará dinámicamente conexiones 
    # nuevas hasta llegar a este límite. En este caso, la app podrá manejar un total 
    # máximo de (DB_POOL_SIZE + DB_MAX_OVERFLOW) conexiones simultáneas. 
    # Estas conexiones extra se cierran en cuanto se desocupan.
    max_overflow=DB_MAX_OVERFLOW,
    
    # --- pool_recycle ---
    # DB_POOL_RECYCLE (Por defecto: 3600 segundos / 1 hora)
    # El tiempo de reciclaje (en segundos).
    # Obliga al pool a cerrar y recrear una conexión si ha estado abierta 
    # por más tiempo del aquí indicado. Esto es CRUCIAL para MySQL, ya que el servidor 
    # MySQL corta por defecto las conexiones inactivas tras unas horas (wait_timeout). 
    # Reciclándolas desde el código evitas el famoso error "MySQL server has gone away".
    pool_recycle=DB_POOL_RECYCLE,
    
    # --- pool_timeout ---
    # Variable de entorno: DB_POOL_TIMEOUT (Por defecto: 30 segundos)
    # El tiempo de espera máximo (en segundos).
    # Si la aplicación está saturada y todas las conexiones posibles están 
    # ocupadas, las nuevas peticiones entrantes se pondrán en fila de espera. 
    # Si pasa este tiempo y ninguna conexión se libera, SQLAlchemy lanzará una 
    # excepción (TimeoutError) en lugar de dejar colgado al usuario indefinidamente.
    pool_timeout=DB_POOL_TIMEOUT)

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