from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy.exc import OperationalError
from starlette.middleware.cors import CORSMiddleware
import logging

# Configuración de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importaciones de la DB y modelos
from app.database import Base, engine
from app.routes import ruta, citas # Rutas de Autenticación (auth.py) y Citas

# Bloque try-except para manejar el error de conexión a la DB durante el startup
try:
    # Intenta crear todas las tablas en la DB (si no existen)
    Base.metadata.create_all(bind=engine)
    logger.info("Conexión exitosa a la base de datos. Tablas creadas/verificadas.")
except OperationalError as e:
    logger.error(f"⚠️ ERROR: Falló la conexión a la base de datos PostgreSQL en el inicio. Esto es esperado si el servicio de DB no está corriendo. Detalles: {e}")
    # Nota: La aplicación seguirá cargando, pero las operaciones de DB fallarán hasta que el servicio esté disponible.


# Contexto de inicio y cierre de la aplicación
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lógica que se ejecuta al iniciar la aplicación
    logger.info("Iniciando FastAPI server...")
    yield
    # Lógica que se ejecuta al cerrar la aplicación
    logger.info("Cerrando FastAPI server...")

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="No Country - API de Gestión Médica",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración de CORS
origins = [
    "*", # Permite cualquier origen por ahora (para desarrollo)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de las rutas
app.include_router(ruta.router, prefix="/api/v1/auth", tags=["Autenticación"])
app.include_router(citas.router, prefix="/api/v1/appointments", tags=["Citas"])

# Ruta de prueba o health check
@app.get("/")
def read_root():
    return {"message": "API de Gestión Médica funcionando."}
