from datetime import datetime, timedelta
from typing import List, Optional

# Este módulo simula la interacción con APIs externas (Google Calendar, Zoom, etc.)
# En un entorno real, aquí iría la lógica de autenticación OAuth2 de Google/Zoom
# y las llamadas HTTP a sus endpoints.

# --- 1. Simulación de Integración de Calendario (Disponibilidad) ---

def get_doctor_available_slots(doctor_id: int, date: datetime) -> List[datetime]:
    """
    SIMULACIÓN: Consulta la API de Google Calendar del doctor para slots disponibles.
    
    En la realidad:
    1. Se autenticaría usando las credenciales OAuth2 del doctor.
    2. Se llamaría al endpoint de 'free/busy' de Google Calendar.
    3. Se calcularían los slots disponibles (ej. cada 30 minutos).
    """
    
    # Para la demostración, el doctor siempre está disponible de 9:00 a 12:00
    if date.weekday() in [5, 6]: # Sábado o Domingo
        return []

    available_slots = []
    start_hour = 9
    end_hour = 12
    slot_duration_minutes = 30

    current_time = datetime(date.year, date.month, date.day, start_hour, 0, 0)
    end_of_day = datetime(date.year, date.month, date.day, end_hour, 0, 0)

    while current_time < end_of_day:
        available_slots.append(current_time)
        current_time += timedelta(minutes=slot_duration_minutes)
        
    return available_slots


# --- 2. Simulación de Integración de Videollamadas ---

def generate_teleconsult_link(appointment_id: int, is_virtual: bool) -> Optional[str]:
    """
    SIMULACIÓN: Genera o recupera la URL para la teleconsulta.

    En la realidad:
    1. Si es virtual, se llama a la API de Zoom o Google Meet para crear una reunión.
    2. Se almacena el ID de la reunión en la DB y se retorna el URL.
    """
    if not is_virtual:
        return None
    
    # Ejemplo de URL simulada, en producción sería un enlace único de Zoom o Meet
    unique_id = f"{appointment_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
    return f"https://meet.healthtech.com/consult/{unique_id}"