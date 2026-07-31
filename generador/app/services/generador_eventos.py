import random
import time
from collections import Counter
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from generador.app.configuracion import (
    PERFILES_DISTRITOS,
    PESOS_DISTRITOS,
    PESOS_PRIORIDADES,
    PESOS_TIPOS_EMERGENCIA,
)
from generador.app.models.evento import (
    DistritoId,
    EstadoLlamada,
    EventoEmergencia,
    Prioridad,
    ResultadoLote,
    SolicitudLlamadaIndividual,
    SolicitudLote,
    TipoEmergencia,
    Ubicacion,
)


ZONA_HORARIA_HONDURAS = ZoneInfo("America/Tegucigalpa")


def _crear_numero_reporte(
    fecha_evento: datetime,
    evento_id: UUID,
) -> str:
    """Crea un número de reporte legible para cada emergencia."""

    return (
        f"EMG-{fecha_evento:%Y%m%d-%H%M%S}-"
        f"{evento_id.hex[:6].upper()}"
    )


def _construir_evento(
    distrito_id: DistritoId,
    tipo_emergencia: TipoEmergencia,
    prioridad: Prioridad,
    ubicacion: Ubicacion,
    modo_generacion: Literal["individual", "lote"],
    lote_id: UUID | None,
    escenario: str,
) -> EventoEmergencia:
    """Construye un evento completo con sus campos técnicos."""

    fecha_actual = datetime.now(ZONA_HORARIA_HONDURAS)
    evento_id = uuid4()

    return EventoEmergencia(
        evento_id=evento_id,
        numero_reporte=_crear_numero_reporte(
            fecha_actual,
            evento_id,
        ),
        distrito_id=distrito_id,
        tipo_emergencia=tipo_emergencia,
        prioridad=prioridad,
        estado=EstadoLlamada.REPORTADA,
        ubicacion=ubicacion,
        fecha_hora_evento=fecha_actual,
        modo_generacion=modo_generacion,
        lote_id=lote_id,
        escenario=escenario,
        version_esquema="1.0",
    )


def crear_evento_individual(
    solicitud: SolicitudLlamadaIndividual,
) -> EventoEmergencia:
    """Construye un evento individual válido."""

    return _construir_evento(
        distrito_id=solicitud.distrito_id,
        tipo_emergencia=solicitud.tipo_emergencia,
        prioridad=solicitud.prioridad,
        ubicacion=solicitud.ubicacion,
        modo_generacion="individual",
        lote_id=None,
        escenario="normal",
    )


def crear_lote_eventos(
    solicitud: SolicitudLote,
) -> ResultadoLote:
    """Genera un lote de eventos con distribuciones ponderadas."""

    generador_aleatorio = random.Random(solicitud.semilla)
    lote_id = uuid4()

    distritos = list(PESOS_DISTRITOS.keys())
    tipos_emergencia = list(PESOS_TIPOS_EMERGENCIA.keys())
    prioridades = list(PESOS_PRIORIDADES.keys())

    pesos_distritos = list(PESOS_DISTRITOS.values())
    pesos_tipos = list(PESOS_TIPOS_EMERGENCIA.values())
    pesos_prioridades = list(PESOS_PRIORIDADES.values())

    contador_distritos: Counter[str] = Counter()
    contador_tipos: Counter[str] = Counter()
    contador_prioridades: Counter[str] = Counter()

    eventos: list[EventoEmergencia] = []

    inicio = time.perf_counter()

    for _ in range(solicitud.cantidad):
        distrito = generador_aleatorio.choices(
            distritos,
            weights=pesos_distritos,
            k=1,
        )[0]

        tipo_emergencia = generador_aleatorio.choices(
            tipos_emergencia,
            weights=pesos_tipos,
            k=1,
        )[0]

        prioridad = generador_aleatorio.choices(
            prioridades,
            weights=pesos_prioridades,
            k=1,
        )[0]

        perfil = PERFILES_DISTRITOS[distrito]

        sector = generador_aleatorio.choice(
            perfil["sectores"]
        )

        evento = _construir_evento(
            distrito_id=distrito,
            tipo_emergencia=tipo_emergencia,
            prioridad=prioridad,
            ubicacion=Ubicacion(
                sector=sector,
            ),
            modo_generacion="lote",
            lote_id=lote_id,
            escenario=solicitud.escenario,
        )

        eventos.append(evento)

        contador_distritos[distrito.value] += 1
        contador_tipos[tipo_emergencia.value] += 1
        contador_prioridades[prioridad.value] += 1

    duracion_segundos = time.perf_counter() - inicio

    if duracion_segundos <= 0:
        duracion_segundos = 0.000001

    eventos_por_segundo = (
        len(eventos) / duracion_segundos
    )

    return ResultadoLote(
        lote_id=lote_id,
        cantidad_solicitada=solicitud.cantidad,
        cantidad_generada=len(eventos),
        duracion_ms=round(
            duracion_segundos * 1000,
            3,
        ),
        eventos_por_segundo=round(
            eventos_por_segundo,
            2,
        ),
        distribucion_distritos=dict(
            contador_distritos
        ),
        distribucion_tipos=dict(
            contador_tipos
        ),
        distribucion_prioridades=dict(
            contador_prioridades
        ),
        muestra=eventos[:5],
    )