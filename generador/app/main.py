from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    status,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from generador.app.models.evento import (
    ConfirmacionKafka,
    EventoEmergencia,
    ResultadoEventoKafka,
    ResultadoLote,
    SolicitudLlamadaIndividual,
    SolicitudLote,
)
from generador.app.services.generador_eventos import (
    crear_evento_individual,
    crear_lote_eventos,
)
from generador.app.services.productor_kafka import (
    ErrorPublicacionKafka,
    ProductorEventosKafka,
)


DIRECTORIO_APP = Path(__file__).resolve().parent
DIRECTORIO_STATIC = DIRECTORIO_APP / "static"


app = FastAPI(
    title="Central de Emergencias 911 - Generador",
    description=(
        "Servicio encargado de generar llamadas de emergencia "
        "individuales y por lotes para la simulación."
    ),
    version="0.2.0",
)


app.mount(
    "/static",
    StaticFiles(directory=DIRECTORIO_STATIC),
    name="static",
)


# Se crea una sola instancia y se reutiliza.
# No se crea un productor nuevo por cada clic.
productor_kafka = ProductorEventosKafka()


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
    """Genera una llamada sin enviarla a Kafka."""

    return crear_evento_individual(solicitud)


@app.post(
    "/eventos/individual/kafka",
    response_model=ResultadoEventoKafka,
    status_code=status.HTTP_201_CREATED,
    tags=["Kafka"],
)
def generar_y_publicar_evento_individual(
    solicitud: SolicitudLlamadaIndividual,
) -> ResultadoEventoKafka:
    """Genera una llamada y espera su confirmación en Kafka."""

    evento = crear_evento_individual(solicitud)

    try:
        confirmacion = (
            productor_kafka.publicar_y_confirmar(
                evento
            )
        )
    except ErrorPublicacionKafka as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El evento fue generado, pero Kafka "
                f"no pudo confirmarlo: {error}"
            ),
        ) from error

    return ResultadoEventoKafka(
        evento=evento,
        kafka=ConfirmacionKafka(
            topic=confirmacion.topic,
            particion=confirmacion.particion,
            offset=confirmacion.offset,
            distrito_id=confirmacion.distrito_id,
            evento_id=confirmacion.evento_id,
        ),
    )


@app.post(
    "/eventos/lote",
    response_model=ResultadoLote,
    status_code=status.HTTP_201_CREATED,
    tags=["Eventos"],
)
def generar_eventos_lote(
    solicitud: SolicitudLote,
) -> ResultadoLote:
    """Genera múltiples llamadas todavía sin enviarlas a Kafka."""

    return crear_lote_eventos(solicitud)