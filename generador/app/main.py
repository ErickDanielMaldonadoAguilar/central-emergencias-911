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
    ConfirmacionLoteKafka,
    EventoEmergencia,
    ResultadoEventoKafka,
    ResultadoLote,
    ResultadoLoteKafka,
    SolicitudLlamadaIndividual,
    SolicitudLote,
)
from generador.app.services.generador_eventos import (
    crear_evento_individual,
    crear_lote_eventos,
    crear_lote_eventos_completo,
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
        "individuales y por lotes, y publicarlas en Kafka."
    ),
    version="0.3.0",
)


app.mount(
    "/static",
    StaticFiles(directory=DIRECTORIO_STATIC),
    name="static",
)


# La instancia se reutiliza para las publicaciones individuales
# y masivas. No se crea un productor nuevo por cada solicitud.
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
    """Revisa la disponibilidad básica del generador."""

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
    """Genera un lote sin publicarlo en Kafka."""

    return crear_lote_eventos(solicitud)


@app.post(
    "/eventos/lote/kafka",
    response_model=ResultadoLoteKafka,
    status_code=status.HTTP_201_CREATED,
    tags=["Kafka"],
)
def generar_y_publicar_lote(
    solicitud: SolicitudLote,
) -> ResultadoLoteKafka:
    """Genera un lote completo y lo publica en Kafka."""

    lote = crear_lote_eventos_completo(
        solicitud
    )

    try:
        confirmacion = (
            productor_kafka.publicar_lote_y_confirmar(
                lote.eventos
            )
        )
    except ErrorPublicacionKafka as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "El lote fue generado, pero Kafka "
                f"no pudo confirmarlo completamente: {error}"
            ),
        ) from error

    return ResultadoLoteKafka(
        generacion=lote.resumen,
        kafka=ConfirmacionLoteKafka(
            topic=confirmacion.topic,
            cantidad_enviada=(
                confirmacion.cantidad_enviada
            ),
            cantidad_confirmada=(
                confirmacion.cantidad_confirmada
            ),
            cantidad_fallida=(
                confirmacion.cantidad_fallida
            ),
            duracion_ms=confirmacion.duracion_ms,
            eventos_por_segundo=(
                confirmacion.eventos_por_segundo
            ),
            confirmaciones_por_particion=(
                confirmacion
                .confirmaciones_por_particion
            ),
            primer_offset_por_particion=(
                confirmacion
                .primer_offset_por_particion
            ),
            ultimo_offset_por_particion=(
                confirmacion
                .ultimo_offset_por_particion
            ),
        ),
    )