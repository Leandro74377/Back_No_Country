from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Annotated, Optional

# Importaciones de módulos locales
from app.database import get_db
from app.models.user import User, UserRole
# CORRECCIÓN DE IMPORTACIÓN: Importamos las clases específicas de Pydantic, incluyendo AppointmentCreate
from app.utils.schemas import BaseModel, UserOut, UserCreate, UserLogin, Token, AppointmentCreate 
from app.utils import security 
from app.config import settings
from app.utils.google_tokens import get_google_auth_flow, exchange_code_for_tokens
from app.utils.servicios_meet_calendar import create_google_calendar_event # <-- Servicio de Meet/Calendar
from app.excepciones import GoogleCalendarError 
from starlette.responses import RedirectResponse

# Crea el router para las rutas de autenticación
router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)

# Dependencia de inyección para la sesión de base de datos
SessionDep = Annotated[Session, Depends(get_db)]

# --- Utilidad para obtener el usuario autenticado ---
def get_current_user(db: Session = Depends(get_db), token: str = Header(..., alias="Authorization")):
    """
    Decodifica el token JWT y obtiene el usuario autenticado.
    """
    token = token.replace("Bearer ", "")
    payload = security.decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("user_id")
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return db_user

CurrentUserDep = Annotated[User, Depends(get_current_user)]

# --- Esquema Específico para Citas con Meet (usa email, no IDs) ---
class GoogleAppointmentCreate(BaseModel):
    """
    Esquema específico para la ruta de Meet, que requiere el email del paciente
    y detalles específicos del evento de Google.
    """
    patient_email: str
    start_time: datetime
    end_time: datetime
    summary: str = "Consulta Médica Online"
    description: str = "Videoconsulta agendada por el sistema."


# --- Rutas de Autenticación Estándar (Existentes) ---

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED) # <--- CORREGIDO: Usamos UserOut
def register_user(user_data: UserCreate, db: SessionDep): # <--- Usa UserCreate importado directamente
    """
    Registra un nuevo usuario en el sistema.
    """
    # 1. Verificar si el email ya existe
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # 2. Hashear la contraseña
    hashed_password = security.get_password_hash(user_data.password)

    # 3. Crear el nuevo objeto User del ORM
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role # El rol por defecto es 'patient' según el esquema
    )

    # 4. Guardar en la base de datos
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token) # <--- Usa Token importado directamente
def login_for_access_token(user_data: UserLogin, db: SessionDep): # <--- Usa UserLogin importado directamente
    """
    Verifica las credenciales y devuelve un token JWT si son válidas.
    """
    # 1. Buscar el usuario por email
    db_user = db.query(User).filter(User.email == user_data.email).first()
    
    # 2. Verificar existencia y contraseña
    if not db_user or not security.verify_password(user_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Crear el token de acceso
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"user_id": db_user.id, "role": db_user.role.value},
        expires_delta=access_token_expires
    )
    
    # 4. Devolver el token
    return {"access_token": access_token}


# --- Rutas de Google OAuth (Nuevas) ---

@router.get("/google/login")
def google_login():
    """
    Inicia el flujo de autenticación de Google OAuth 2.0.
    Redirige al usuario a la página de consentimiento de Google.
    """
    flow = get_google_auth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        # Solicita el refresh_token para poder usarlo después
        prompt='consent' 
    )
    # Guarda el state en la sesión si estuvieras usando sesiones reales. 
    # Por simplicidad aquí, confiamos en la validez del estado.
    return RedirectResponse(authorization_url)


@router.get("/google/callback")
def google_callback(code: str, db: SessionDep):
    """
    Maneja la respuesta del servidor de Google (callback).
    Intercambia el código por tokens y guarda el refresh_token del doctor.
    """
    try:
        # 1. Intercambiar el código por tokens de Google
        tokens = exchange_code_for_tokens(code)
        refresh_token = tokens.get('refresh_token')
        google_email = tokens.get('email')

        if not refresh_token:
            # Puede ocurrir si no se solicita el 'prompt=consent' o el usuario ya autorizó
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo obtener el token de refresco (Refresh Token). Reintente, asegurándose de dar todos los permisos."
            )

        # 2. Encontrar el usuario por email
        # NOTA: En un sistema real, el usuario debe estar logueado para vincular su cuenta.
        # Aquí, por simplicidad, asumimos que el email de Google es el mismo que el de registro.
        db_user = db.query(User).filter(User.email == google_email).first()

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Usuario con email {google_email} no encontrado en la base de datos."
            )

        # 3. Guardar el refresh token en la base de datos
        db_user.google_refresh_token = refresh_token
        db.commit()

        # 4. Redirigir a una página de éxito (debe ser una URL de tu frontend)
        return RedirectResponse(
            url="/", 
            status_code=status.HTTP_302_FOUND,
            # Mensaje de éxito o token, dependiendo de tu frontend
            headers={"X-Auth-Status": "Google Calendar conectado con éxito."}
        )

    except HTTPException:
        # Re-lanza la excepción HTTPException si ya ocurrió en el bloque try
        raise
    except Exception as e:
        print(f"Error en el callback de Google: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error al procesar la autenticación de Google."
        )

# --- Ruta de Creación de Citas con Meet (Ejemplo) ---

@router.post("/appointments/create", status_code=status.HTTP_201_CREATED)
def create_appointment_with_meet(
    appointment_data: GoogleAppointmentCreate,
    db: SessionDep,
    current_user: CurrentUserDep
):
    """
    Crea una nueva cita. Si el usuario actual es un Doctor,
    intenta crear un evento de Google Calendar con un enlace de Meet.
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Solo los doctores pueden crear citas de calendario."
        )

    # 1. Verificar si el doctor tiene el token de Google
    if not current_user.google_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El doctor debe conectar su calendario de Google a través de /auth/google/login primero."
        )

    # 2. Crear el evento de Google Calendar
    try:
        # Simular la creación de la cita en tu DB (aquí solo se crea el evento de Google)
        
        # Llama al servicio de Google
        meet_info = create_google_calendar_event(
            doctor=current_user,
            summary=appointment_data.summary,
            description=appointment_data.description,
            start_time=appointment_data.start_time,
            end_time=appointment_data.end_time,
            patient_email=appointment_data.patient_email
        )
        
        # En un escenario real, aquí se guardaría la cita en la DB local
        # appointment = Appointment(
        #     doctor_id=current_user.id,
        #     video_url=meet_info['meet_url'],
        #     ...
        # )

        return {
            "message": "Cita agendada y evento de Google Calendar/Meet creado con éxito.",
            "meet_url": meet_info['meet_url'],
            "calendar_url": meet_info['event_url']
        }

    except GoogleCalendarError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el evento de Google: {e.detail}"
        )
