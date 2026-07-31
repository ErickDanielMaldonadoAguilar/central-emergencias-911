from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DistritoId(str, Enum):
    """Distritos operativos simulados."""

    CENTRO = "D-01"
    NORTE = "D-02"
    SUR = "D-03"
    ESTE = "D-04"
    OESTE = "D-05"
    COMAYAGUELA = "D-06"


class TipoEmergencia(str, Enum):
    """Tipos de emergencia utilizados en la simulación."""

    MEDICA = "EM-01"
    ACCIDENTE_TRANSITO = "EM-02"
    INCENDIO = "EM-03"
    SEGURIDAD = "EM-04"
    RESCATE = "EM-05"
    INUNDACION_DESLIZAMIENTO = "EM-06"


class Prioridad(str, Enum):
    """Niveles de prioridad de una llamada."""

    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class EstadoLlamada(str, Enum):
    """Estados básicos del ciclo de una llamada."""

    REPORTADA = "reportada"
    EN_ATENCION = "en_atencion"
    RESUELTA = "resuelta"
    CANCELADA = "cancelada"


class Ubicacion(BaseModel):
    """Sector simulado donde ocurre la emergencia."""

    model_config = ConfigDict(extra="forbid")

    sector: str = Field(min_length=2, max_length=80)


class SolicitudLlamadaIndividual(BaseModel):
    """Información ingresada para generar una llamada individual."""

    distrito_id: DistritoId
    tipo_emergencia: TipoEmergencia
    prioridad: Prioridad
    ubicacion: Ubicacion


class EventoEmergencia(SolicitudLlamadaIndividual):
    """Evento completo que posteriormente será enviado a Kafka."""

    evento_id: UUID
    numero_reporte: str
    estado: EstadoLlamada
    fecha_hora_evento: datetime
    modo_generacion: Literal["individual", "lote"]
    lote_id: UUID | None = None
    escenario: str = "normal"
    version_esquema: str = "1.0"


class SolicitudLote(BaseModel):
    """Parámetros para generar un lote masivo de llamadas."""

    cantidad: int = Field(ge=1, le=10_000)
    semilla: int | None = Field(default=None, ge=0)
    escenario: Literal["normal"] = "normal"


class ResultadoLote(BaseModel):
    """Resumen de una generación masiva de llamadas."""

    lote_id: UUID
    cantidad_solicitada: int
    cantidad_generada: int
    duracion_ms: float
    eventos_por_segundo: float
    distribucion_distritos: dict[str, int]
    distribucion_tipos: dict[str, int]
    distribucion_prioridades: dict[str, int]
    muestra: list[EventoEmergencia]