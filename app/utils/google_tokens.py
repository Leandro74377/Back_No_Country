from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from app.config import settings
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from fastapi import status, HTTPException # <--- CAMBIO: Agregada HTTPException

# Configuración: Los datos del cliente se obtienen de app.config
# Estos datos son usados por la librería google-auth-oauthlib

CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "project_id": "fastapi-calendar-app", # Puede ser un nombre de proyecto genérico
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI], # <--- CORRECCIÓN 1
        "javascript_origins": ["http://localhost:8000"] # No crítico para backend, pero requerido por el objeto
    }
}

def get_google_auth_flow() -> Flow:
    """
    Inicializa y devuelve el objeto Flow de Google, que gestiona el proceso OAuth.
    """
    try:
        flow = Flow.from_client_config(
            client_config=CLIENT_CONFIG,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI # <--- CORRECCIÓN 2
        )
        return flow
    except Exception as e:
        print(f"Error al inicializar Google Flow: {e}")
        # <--- CAMBIO: Usando HTTPException en lugar de CustomHTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de configuración de Google OAuth."
        )

def exchange_code_for_tokens(auth_code: str) -> dict:
    """
    Intercambia el código de autorización por los tokens de acceso y refresco.
    Devuelve un diccionario con los detalles de las credenciales.
    """
    flow = get_google_auth_flow()
    
    # Realiza la solicitud al servidor de Google para obtener los tokens
    flow.fetch_token(code=auth_code)
    
    # flow.credentials contiene el access_token, refresh_token, token_uri, etc.
    return {
        "refresh_token": flow.credentials.refresh_token,
        "access_token": flow.credentials.token,
        "expiry": flow.credentials.expiry,
        "email": flow.credentials.id_token.get('email')
    }

def get_credentials_from_refresh_token(refresh_token: str) -> Optional[Credentials]:
    """
    Usa el token de refresco guardado para obtener un nuevo token de acceso.
    """
    if not refresh_token:
        return None
        
    try:
        # Crea un objeto Credentials a partir del refresh token y las credenciales del cliente
        credentials = Credentials(
            token=None,  # No necesitamos un access token actual, lo va a generar
            refresh_token=refresh_token,
            token_uri=CLIENT_CONFIG['web']['token_uri'],
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_SCOPES
        )
        
        # Refresca el token para obtener un access token válido
        credentials.refresh(Request())
        
        return credentials
    except Exception as e:
        print(f"Error al refrescar el token de Google: {e}")
        # Si el refresh token falla (por ejemplo, revocado), devolvemos None
        return None
