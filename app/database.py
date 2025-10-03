from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import os

# Determina el tipo de motor de base de datos a usar. 
# Si la URL apunta a PostgreSQL, usa ese motor.
# Si la URL apunta a SQLite (como el valor predeterminado), usa SQLite.
DATABASE_URL = settings.DATABASE_URL

# Configuración del motor de SQLAlchemy
# La opción 'pool_pre_ping=True' ayuda a manejar reconexiones si la DB se cae temporalmente.
# 'future=True' habilita las características futuras de SQLAlchemy 2.0.
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    future=True
)

# Sesión de la base de datos
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    future=True
)

# Clase base para los modelos declarativos de SQLAlchemy
Base = declarative_base()

# Función de utilidad para obtener la sesión de la base de datos
def get_db():
    """Dependencia para obtener la sesión de la base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
