from typing import TypedDict

from generador.app.models.evento import (
    DistritoId,
    Prioridad,
    TipoEmergencia,
)


class PerfilDistrito(TypedDict):
    """Estructura de configuración geográfica de un distrito."""

    latitud: float
    longitud: float
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


# Perfiles geográficos simulados.
# Estas ubicaciones son académicas y no representan
# divisiones oficiales del Sistema Nacional de Emergencias 911.
PERFILES_DISTRITOS: dict[DistritoId, PerfilDistrito] = {
    DistritoId.CENTRO: {
        "latitud": 14.0723,
        "longitud": -87.1921,
        "sectores": [
            "Zona Centro A",
            "Zona Centro B",
            "Zona Centro C",
        ],
    },
    DistritoId.NORTE: {
        "latitud": 14.1200,
        "longitud": -87.1900,
        "sectores": [
            "Zona Norte A",
            "Zona Norte B",
            "Zona Norte C",
        ],
    },
    DistritoId.SUR: {
        "latitud": 14.0300,
        "longitud": -87.2050,
        "sectores": [
            "Zona Sur A",
            "Zona Sur B",
            "Zona Sur C",
        ],
    },
    DistritoId.ESTE: {
        "latitud": 14.0800,
        "longitud": -87.1500,
        "sectores": [
            "Zona Este A",
            "Zona Este B",
            "Zona Este C",
        ],
    },
    DistritoId.OESTE: {
        "latitud": 14.0800,
        "longitud": -87.2500,
        "sectores": [
            "Zona Oeste A",
            "Zona Oeste B",
            "Zona Oeste C",
        ],
    },
    DistritoId.COMAYAGUELA: {
        "latitud": 14.0900,
        "longitud": -87.2100,
        "sectores": [
            "Zona Comayagüela A",
            "Zona Comayagüela B",
            "Zona Comayagüela C",
        ],
    },
}