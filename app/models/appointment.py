import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship
from datetime import datetime

# Asume que ya tienes un archivo 'database.py' que define Base
# Usamos una importación absoluta desde la raíz 'app'
from app.database import Base 

# --- Enums para la lógica de negocio ---

class PriorityLevel(enum.Enum):
    """Define los niveles de prioridad para el algoritmo de asignación."""
    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"
    URGENT = "Urgente"

class AppointmentStatus(enum.Enum):
    """Define los estados posibles de una cita."""
    REQUESTED = "Solicitada"      # Cita creada, esperando asignación
    CONFIRMED = "Confirmada"      # Cita asignada a un doctor y hora
    CANCELLED = "Cancelada"       # Cancelada por paciente, doctor, o admin
    COMPLETED = "Completada"      # Cita que ya ocurrió
    NO_SHOW = "No Presentado"     # Paciente no asistió

# --- Modelo de Cita ---

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    
    # 1. Relaciones con Usuarios
    patient_id = Column(Integer, ForeignKey("users.id"), index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # Puede ser NULL si aún no está asignado

    # 2. Detalles del Agendamiento
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_virtual = Column(Boolean, default=True)
    
    # 3. Datos de Prioridad y Estado
    priority_level = Column(Enum(PriorityLevel), default=PriorityLevel.MEDIUM)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.REQUESTED)
    
    # 4. Integración de Teleconsulta
    video_url = Column(Text, nullable=True) # URL de Google Meet, Zoom, etc.
    
    # 5. Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 6. Definición de Relaciones ORM
    
    # Relación con el paciente
    patient = relationship(
        "User", 
        back_populates="patient_appointments", 
        foreign_keys=[patient_id],
        lazy="joined"
    )

    # Relación con el doctor
    doctor = relationship(
        "User", 
        back_populates="doctor_appointments", 
        foreign_keys=[doctor_id],
        lazy="joined"
    )