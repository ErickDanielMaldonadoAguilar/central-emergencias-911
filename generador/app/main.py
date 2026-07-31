from fastapi import FastAPI

app = FastAPI(
    title="Central de Emergencias 911 - Generador",
    description=(
        "Servicio encargado de generar llamadas de emergencia "
        "individuales y por lotes para la simulación."
    ),
    version="0.1.0",
)


@app.get("/", tags=["Estado"])
def obtener_inicio() -> dict[str, str]:
    """Confirma que el servicio generador está funcionando."""
    return {
        "mensaje": "Generador de emergencias funcionando",
        "estado": "activo",
    }


@app.get("/health", tags=["Estado"])
def verificar_salud() -> dict[str, str]:
    """Endpoint básico para revisar la disponibilidad del servicio."""
    return {
        "status": "ok",
        "servicio": "generador-emergencias",
    }