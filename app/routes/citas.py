from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

# Importaciones del proyecto
from app.database import get_db
from app.models.user import User, UserRole
from app.models.appointment import Appointment, AppointmentStatus, PriorityLevel
from app.utils.schemas import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from app.utils.security import get_current_user # Tu archivo de seguridad (validacion_s.py)

# Inicialización del router
router = APIRouter(prefix="/citas", tags=["Citas Médicas"])

# ----------------------------------------------------------------------
# LÓGICA DEL ALGORITMO DE ASIGNACIÓN (Placeholder)
# ----------------------------------------------------------------------

def assign_priority_and_schedule(db: Session, appointment: Appointment):
    """
    Función que implementará el Algoritmo de Asignación por Prioridad.
    
    CRITERIOS DE PRIORIDAD:
    1. UrgencyLevel (el más alto va primero).
    2. Tiempo de espera (FIFO para misma prioridad).
    3. Disponibilidad de doctores.
    
    Esta es una implementación MOCK, se expandirá más adelante.
    """
    
    # 1. Mapear UrgencyLevel a un factor numérico de prioridad (ya hecho por el Enum)
    priority_score = appointment.urgency_level.value
    
    # 2. Buscar al doctor con menor carga (MOCK)
    # Por ahora, simplemente asignaremos un doctor ficticio con role DOCTOR
    available_doctor = db.query(User).filter(User.role == UserRole.DOCTOR).first()

    if available_doctor:
        appointment.doctor_id = available_doctor.id
        
        # 3. Asignar una hora ficticia basada en la prioridad (MOCK: Citas más urgentes tienen 
        # una hora de programación más cercana)
        if priority_score == PriorityLevel.CRITICAL.value:
            scheduled_time = datetime.utcnow() + timedelta(minutes=30)
        elif priority_score == PriorityLevel.HIGH.value:
            scheduled_time = datetime.utcnow() + timedelta(hours=2)
        else:
            scheduled_time = datetime.utcnow() + timedelta(hours=24)

        appointment.scheduled_at = scheduled_time
        appointment.status = AppointmentStatus.CONFIRMED
        
        # Opcional: Aquí se podría integrar la lógica para crear el evento en Google Calendar
        # create_google_calendar_event(appointment)
        
    else:
        # Si no hay doctor disponible, se queda en pendiente o se rechaza
        appointment.status = AppointmentStatus.PENDING 

    return appointment

# ----------------------------------------------------------------------
# ENDPOINTS
# ----------------------------------------------------------------------

@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def request_appointment(
    appointment_data: AppointmentCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permite a un paciente solicitar una nueva cita. 
    Solo los usuarios con rol 'Paciente' pueden acceder.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los pacientes pueden solicitar citas."
        )

    # Crear la nueva cita en la base de datos
    db_appointment = Appointment(
        patient_id=current_user.id,
        reason=appointment_data.reason,
        urgency_level=appointment_data.urgency_level,
        is_telemedicine=appointment_data.is_telemedicine,
        status=AppointmentStatus.PENDING # Inicia siempre pendiente
    )
    
    # Ejecutar la lógica de asignación (incluso si es la primera vez)
    db_appointment = assign_priority_and_schedule(db, db_appointment)

    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    return db_appointment

@router.get("/my", response_model=List[AppointmentResponse])
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene todas las citas solicitadas por el usuario autenticado (paciente o doctor).
    """
    if current_user.role == UserRole.PATIENT:
        # Si es paciente, listar sus citas como paciente
        appointments = db.query(Appointment).filter(
            Appointment.patient_id == current_user.id
        ).all()
    elif current_user.role == UserRole.DOCTOR:
        # Si es doctor, listar las citas que tiene asignadas
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == current_user.id
        ).all()
    else:
        # Si es ADMIN, podría listar todas, pero por ahora solo le mostramos un error para simplificar
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso no autorizado para este rol. Por favor use una ruta específica de administrador."
        )
        
    return appointments
