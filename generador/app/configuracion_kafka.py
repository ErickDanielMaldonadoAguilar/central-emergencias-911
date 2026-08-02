import os

from generador.app.models.evento import (
    DistritoId,
)


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    (
        "localhost:9092,"
        "localhost:9093,"
        "localhost:9094"
    ),
)

KAFKA_CLIENT_ID = os.getenv(
    "KAFKA_CLIENT_ID",
    "central911-generador",
)

KAFKA_TOPIC_LLAMADAS = os.getenv(
    "KAFKA_TOPIC_LLAMADAS",
    "llamadas-emergencia",
)


PARTICIONES_POR_DISTRITO: dict[
    DistritoId,
    int,
] = {
    DistritoId.CENTRO: 0,
    DistritoId.NORTE: 1,
    DistritoId.SUR: 2,
    DistritoId.ESTE: 3,
    DistritoId.OESTE: 4,
    DistritoId.COMAYAGUELA: 5,
}