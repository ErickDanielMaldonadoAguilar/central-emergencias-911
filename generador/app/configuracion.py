from typing import TypedDict

from generador.app.models.evento import (
    DistritoId,
    Prioridad,
    TipoEmergencia,
)


class PerfilDistrito(TypedDict):
    """Información simulada asociada a un distrito."""

    sectores: list[str]


# Distribución base de llamadas por distrito.
# Los porcentajes suman 100.
PESOS_DISTRITOS: dict[DistritoId, int] = {
    DistritoId.CENTRO: 21,
    DistritoId.NORTE: 17,
    DistritoId.SUR: 16,
    DistritoId.ESTE: 14,
    DistritoId.OESTE: 12,
    DistritoId.COMAYAGUELA: 20,
}


# Distribución base por tipo de emergencia.
# Los porcentajes suman 100.
PESOS_TIPOS_EMERGENCIA: dict[TipoEmergencia, int] = {
    TipoEmergencia.MEDICA: 28,
    TipoEmergencia.ACCIDENTE_TRANSITO: 24,
    TipoEmergencia.INCENDIO: 10,
    TipoEmergencia.SEGURIDAD: 25,
    TipoEmergencia.RESCATE: 8,
    TipoEmergencia.INUNDACION_DESLIZAMIENTO: 5,
}


# Distribución base por nivel de prioridad.
# Los porcentajes suman 100.
PESOS_PRIORIDADES: dict[Prioridad, int] = {
    Prioridad.BAJA: 30,
    Prioridad.MEDIA: 40,
    Prioridad.ALTA: 23,
    Prioridad.CRITICA: 7,
}


# Sectores simulados utilizados en cada distrito.
# No representan divisiones oficiales del 911.
PERFILES_DISTRITOS: dict[DistritoId, PerfilDistrito] = {
    DistritoId.CENTRO: {
        "sectores": [
            "Zona Centro A",
            "Zona Centro B",
            "Zona Centro C",
        ],
    },
    DistritoId.NORTE: {
        "sectores": [
            "Zona Norte A",
            "Zona Norte B",
            "Zona Norte C",
        ],
    },
    DistritoId.SUR: {
        "sectores": [
            "Zona Sur A",
            "Zona Sur B",
            "Zona Sur C",
        ],
    },
    DistritoId.ESTE: {
        "sectores": [
            "Zona Este A",
            "Zona Este B",
            "Zona Este C",
        ],
    },
    DistritoId.OESTE: {
        "sectores": [
            "Zona Oeste A",
            "Zona Oeste B",
            "Zona Oeste C",
        ],
    },
    DistritoId.COMAYAGUELA: {
        "sectores": [
            "Zona Comayagüela A",
            "Zona Comayagüela B",
            "Zona Comayagüela C",
        ],
    },
}