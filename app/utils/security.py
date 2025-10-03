from datetime import datetime, timedelta
from typing import Optional, Annotated # Añadida Annotated para Type Hinting
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.config import settings

# Importaciones adicionales para la dependencia de usuario
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database import get_db
# Asumo que esta ruta es correcta para tu modelo User
from app.models.user import User

# Configuración del contexto de hashing (usando bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Funciones de Hashing de Contraseñas ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña plana."""
    return pwd_context.hash(password)

# --- Funciones de JWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token de acceso JWT con una duración de expiración."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Usa el tiempo de expiración de la configuración si no se especifica
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # Codifica el token usando la clave secreta y el algoritmo
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica y valida un token de acceso JWT."""
    try:
        # Decodifica el token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        # Devuelve None si el token es inválido o ha expirado
        return None

# --- DEPENDENCIA DE AUTENTICACIÓN (Añadida para uso en todas las rutas) ---

def get_current_user(db: Session = Depends(get_db), token: str = Header(..., alias="Authorization")):
    """
    Decodifica el token JWT y obtiene el objeto User autenticado desde la base de datos.
    Esta función se usa como dependencia en las rutas protegidas.
    """
    token = token.replace("Bearer ", "")
    payload = decode_access_token(token) # Usa la función local decode_access_token
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = payload.get("user_id")
    
    # Buscamos al usuario en la DB
    db_user = db.query(User).filter(User.id == user_id).first()
    
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        
    # Devolvemos el objeto User del ORM
    return db_user

# Definición del tipo de dependencia para usar en las rutas (ej: CurrentUserDep)
CurrentUserDep = Annotated[User, Depends(get_current_user)]
