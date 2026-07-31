from fastapi import FastAPI, status

from generador.app.models.evento import (
    EventoEmergencia,
    ResultadoLote,
    SolicitudLlamadaIndividual,
    SolicitudLote,
)
from generador.app.services.generador_eventos import (
    crear_evento_individual,
    crear_lote_eventos,
)


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
    """Revisa la disponibilidad básica del servicio."""

    return {
        "status": "ok",
        "servicio": "generador-emergencias",
    }


@app.post(
    "/eventos/individual",
    response_model=EventoEmergencia,
    status_code=status.HTTP_201_CREATED,
    tags=["Eventos"],
)
def generar_evento_individual(
    solicitud: SolicitudLlamadaIndividual,
) -> EventoEmergencia:
    """Genera una llamada individual validada."""

    return crear_evento_individual(solicitud)


@app.post(
    "/eventos/lote",
    response_model=ResultadoLote,
    status_code=status.HTTP_201_CREATED,
    tags=["Eventos"],
)
def generar_eventos_lote(
    solicitud: SolicitudLote,
) -> ResultadoLote:
    """Genera múltiples llamadas en una sola operación."""

    return crear_lote_eventos(solicitud)