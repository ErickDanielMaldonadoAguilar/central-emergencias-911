from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from generador.app.models.evento import (
    EstadoLlamada,
    EventoEmergencia,
    SolicitudLlamadaIndividual,
)


ZONA_HORARIA_HONDURAS = ZoneInfo("America/Tegucigalpa")


def crear_evento_individual(
    solicitud: SolicitudLlamadaIndividual,
) -> EventoEmergencia:
    """Construye un evento individual válido a partir de una solicitud."""

    fecha_actual = datetime.now(ZONA_HORARIA_HONDURAS)
    evento_id = uuid4()

    numero_reporte = (
        f"EMG-{fecha_actual:%Y%m%d-%H%M%S}-"
        f"{evento_id.hex[:6].upper()}"
    )

    return EventoEmergencia(
        evento_id=evento_id,
        numero_reporte=numero_reporte,
        distrito_id=solicitud.distrito_id,
        tipo_emergencia=solicitud.tipo_emergencia,
        prioridad=solicitud.prioridad,
        estado=EstadoLlamada.REPORTADA,
        ubicacion=solicitud.ubicacion,
        fecha_hora_evento=fecha_actual,
        modo_generacion="individual",
        lote_id=None,
        escenario="normal",
        version_esquema="1.0",
    )