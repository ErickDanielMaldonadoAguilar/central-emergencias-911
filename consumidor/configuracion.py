import os


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

KAFKA_TOPIC_LLAMADAS = os.getenv(
    "KAFKA_TOPIC_LLAMADAS",
    "llamadas-emergencia",
)

KAFKA_CONSUMER_GROUP_PREFIX = os.getenv(
    "KAFKA_CONSUMER_GROUP_PREFIX",
    "central911-verificacion",
)

KAFKA_COMMIT_CADA_MENSAJES = int(
    os.getenv(
        "KAFKA_COMMIT_CADA_MENSAJES",
        "100",
    )
)