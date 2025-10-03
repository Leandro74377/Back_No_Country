from fastapi import HTTPException, status

# Excepción base para errores de negocio específicos
class BusinessException(HTTPException):
    """
    Clase base para manejar errores de la lógica de negocio.
    Hereda de HTTPException para que FastAPI lo maneje automáticamente.
    """
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

# Excepción específica para errores de Google Calendar
class GoogleCalendarError(BusinessException):
    """
    Se lanza cuando hay un problema al interactuar con la API de Google Calendar/Meet.
    """
    def __init__(self, detail: str):
        # Usamos 500 porque es un error de servicio externo.
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)