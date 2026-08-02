import os


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    (
        "localhost:9092,"
        "localhost:9093,"
        "localhost:9094"
    ),
)

KAFKA_TOPIC_LLAMADAS = os.getenv(
    "KAFKA_TOPIC_LLAMADAS",
    "llamadas-emergencia",
)

KAFKA_CONSUMER_GROUP_PREFIX = os.getenv(
    "KAFKA_CONSUMER_GROUP_PREFIX",
    "central911-verificacion",
)

KAFKA_CONSUMER_GROUP_PROCESAMIENTO = os.getenv(
    "KAFKA_CONSUMER_GROUP_PROCESAMIENTO",
    "central911-procesamiento-mongodb",
)

KAFKA_COMMIT_CADA_MENSAJES = int(
    os.getenv(
        "KAFKA_COMMIT_CADA_MENSAJES",
        "100",
    )
)

KAFKA_POLL_TIMEOUT_SEGUNDOS = float(
    os.getenv(
        "KAFKA_POLL_TIMEOUT_SEGUNDOS",
        "1.0",
    )
)