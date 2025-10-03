import enum
from sqlalchemy import Column, Integer, String, Enum, Boolean, Text
from sqlalchemy.orm import relationship

# Importación de la base de datos (corregido a importación absoluta)
from app.database import Base 

# Definición del Enum
class UserRole(enum.Enum):
    """Define los roles de usuario disponibles en el sistema."""
    PATIENT = "Paciente"
    DOCTOR = "Doctor"
    ADMIN = "Admin"

class User(Base):
    """
    Define la tabla de usuarios en la base de datos.
    Incluye campos para la integración de Google Calendar/Meet.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Rol del usuario (usa el Enum definido arriba)
    role = Column(Enum(UserRole), default=UserRole.PATIENT)
    is_active = Column(Boolean, default=True)

    # --- Campos para la Integración de Google Meet/Calendar ---
    google_refresh_token = Column(Text, nullable=True) 

    # --- Relaciones (Historiales y Citas) ---

    # Relación con el historial clínico (back_populates debe coincidir con el atributo en ClinicalRecord)
    patient_records = relationship(
        "ClinicalRecord", 
        back_populates="patient", # Asume que ClinicalRecord tiene un atributo 'patient'
        foreign_keys="ClinicalRecord.patient_id",
        lazy="joined",
        cascade="all, delete-orphan"
    )

    # Relación con el historial clínico creado por el doctor/admin
    doctor_records = relationship(
        "ClinicalRecord", 
        back_populates="doctor", # Asume que ClinicalRecord tiene un atributo 'doctor'
        foreign_keys="ClinicalRecord.doctor_id",
        lazy="joined"
    )

    # Relación con las citas como paciente (back_populates debe coincidir con el atributo en Appointment)
    patient_appointments = relationship(
        "Appointment", 
        back_populates="patient", # Corregido: Asume que Appointment tiene un atributo 'patient'
        foreign_keys="Appointment.patient_id",
        lazy="joined"
    )

    # Relación con las citas como doctor (back_populates debe coincidir con el atributo en Appointment)
    doctor_appointments = relationship(
        "Appointment", 
        back_populates="doctor", # Corregido: Asume que Appointment tiene un atributo 'doctor'
        foreign_keys="Appointment.doctor_id",
        lazy="joined"
    )
