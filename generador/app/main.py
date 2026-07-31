from pathlib import Path

from fastapi import FastAPI, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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


DIRECTORIO_APP = Path(__file__).resolve().parent
DIRECTORIO_STATIC = DIRECTORIO_APP / "static"


app = FastAPI(
    title="Central de Emergencias 911 - Generador",
    description=(
        "Servicio encargado de generar llamadas de emergencia "
        "individuales y por lotes para la simulación."
    ),
    version="0.1.0",
)


app.mount(
    "/static",
    StaticFiles(directory=DIRECTORIO_STATIC),
    name="static",
)


@app.get(
    "/",
    response_class=FileResponse,
    include_in_schema=False,
)
def mostrar_interfaz() -> FileResponse:
    """Muestra la interfaz web del generador."""

    return FileResponse(
        DIRECTORIO_STATIC / "index.html"
    )


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