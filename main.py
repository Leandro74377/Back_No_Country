from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole # Importamos el Enum del modelo

# --- Esquemas de Usuario y Autenticación ---

class UserBase(BaseModel):
    """Esquema base para la creación o lectura de datos de usuario."""
    email: EmailStr = Field(..., example="medico.ejemplo@clinic.com")

class UserCreate(UserBase):
    """Esquema para el registro de un nuevo usuario."""
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.PATIENT # Por defecto es Paciente

class UserOut(UserBase):
    """Esquema para retornar datos de usuario (sin password hash)."""
    id: int
    role: UserRole
    is_active: bool
    
    class Config:
        # Permite mapear campos de SQLAlchemy a Pydantic
        from_attributes = True 

class Token(BaseModel):
    """Esquema para el token de autenticación retornado en el login."""
    access_token: str
    token_type: str = "bearer"
    role: UserRole

class TokenData(BaseModel):
    """Esquema para los datos decodificados dentro del JWT."""
    sub: Optional[str] = None # Usado para el user ID (subject)
    role: Optional[UserRole] = None

# --- Esquemas de Citas ---

class AppointmentBase(BaseModel):
    """Esquema base para datos de una cita."""
    start_time: datetime
    end_time: datetime
    is_virtual: bool = True
    status: str = "scheduled"

class AppointmentCreate(AppointmentBase):
    """Esquema para la creación de una cita."""
    doctor_id: int
    # patient_id no es necesario aquí si se obtiene del token

class AppointmentOut(AppointmentBase):
    """Esquema para la lectura de una cita."""
    id: int
    patient_id: int
    doctor_id: int
    video_url: Optional[str] = None
    
    class Config:
        from_attributes = True 
