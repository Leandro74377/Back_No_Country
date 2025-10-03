import os
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Carga las variables del archivo .env
load_dotenv()

class Settings(BaseSettings):
    """
    Configuración centralizada para la aplicación.
    Lee variables de entorno como SECRET_KEY, DATABASE_URL y credenciales de Google.
    """
    # --- Configuración del Servidor y Seguridad ---
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "super_secreto_y_largo_default"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # --- Configuración de la Base de Datos ---
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./sql_app.db"))
    
    # --- Configuración de Google OAuth y Calendar/Meet ---
    # Todos los campos de Google deben estar definidos
    GOOGLE_CLIENT_ID: str = Field(default=os.getenv("GOOGLE_CLIENT_ID", ""))
    GOOGLE_CLIENT_SECRET: str = Field(default=os.getenv("GOOGLE_CLIENT_SECRET", ""))
    GOOGLE_REDIRECT_URI: str = Field(default=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback"))
    TIME_ZONE: str = Field(default=os.getenv("TIME_ZONE", "America/Bogota"))


    class Config:
        case_sensitive = True

settings = Settings()