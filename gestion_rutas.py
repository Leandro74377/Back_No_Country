from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer # Importación necesaria

# Cargar variables de entorno (para SECRET_KEY)
load_dotenv()

# --- Configuración de Hashing de Contraseñas (BCrypt) ---
# Usamos BCrypt, un algoritmo seguro para hashear passwords.
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash."""
    return password_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña plana."""
    return password_context.hash(password)

# --- Configuración de JWT (JSON Web Tokens) ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# Asegurar que la clave secreta esté presente para evitar errores
if not SECRET_KEY:
    raise ValueError("La variable de entorno SECRET_KEY es requerida para la seguridad.")

# Define el esquema de seguridad que el frontend debe seguir (Bearer Token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Genera un JWT para mantener la sesión del usuario.
    Incluye el ID de usuario (sub) y el rol.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Agrega el tiempo de expiración (exp) al payload del token
    to_encode.update({"exp": expire})
    
    # Crea el token firmado con la clave secreta y el algoritmo
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica y valida el JWT. Retorna el payload si es válido, sino None.
    """
    try:
        # Decodifica y verifica la firma y la expiración del token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Esto captura errores como token inválido, expiración, etc.
        return None