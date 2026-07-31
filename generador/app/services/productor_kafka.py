import json
from dataclasses import dataclass
from typing import Any

from confluent_kafka import KafkaError, Message, Producer

from generador.app.configuracion_kafka import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CLIENT_ID,
    KAFKA_TOPIC_LLAMADAS,
    PARTICIONES_POR_DISTRITO,
)
from generador.app.models.evento import EventoEmergencia


class ErrorPublicacionKafka(RuntimeError):
    """Indica que un evento no pudo confirmarse en Kafka."""


@dataclass(frozen=True)
class ResultadoPublicacionKafka:
    """Información devuelta después de publicar un evento."""

    topic: str
    particion: int
    offset: int
    distrito_id: str
    evento_id: str


class ProductorEventosKafka:
    """Publica eventos de emergencia en Apache Kafka."""

    def __init__(self) -> None:
        self._productor = Producer(
            {
                "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
                "client.id": KAFKA_CLIENT_ID,
                "enable.idempotence": True,
                "acks": "all",
            }
        )

    def publicar_y_confirmar(
        self,
        evento: EventoEmergencia,
        timeout_segundos: float = 10.0,
    ) -> ResultadoPublicacionKafka:
        """Publica un evento y espera la confirmación del broker."""

        particion = PARTICIONES_POR_DISTRITO[
            evento.distrito_id
        ]

        contenido_evento = evento.model_dump(
            mode="json"
        )

        mensaje_json = json.dumps(
            contenido_evento,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        clave = evento.distrito_id.value.encode(
            "utf-8"
        )

        confirmacion: dict[str, Any] = {}

        def registrar_confirmacion(
            error: KafkaError | None,
            mensaje: Message,
        ) -> None:
            if error is not None:
                confirmacion["error"] = str(error)
                return

            confirmacion["mensaje"] = mensaje

        try:
            self._productor.produce(
                topic=KAFKA_TOPIC_LLAMADAS,
                key=clave,
                value=mensaje_json,
                partition=particion,
                on_delivery=registrar_confirmacion,
            )
        except BufferError as error:
            raise ErrorPublicacionKafka(
                "La cola local del productor está llena."
            ) from error

        mensajes_pendientes = self._productor.flush(
            timeout_segundos
        )

        if mensajes_pendientes > 0:
            raise ErrorPublicacionKafka(
                "Kafka no confirmó el evento dentro "
                "del tiempo permitido."
            )

        if "error" in confirmacion:
            raise ErrorPublicacionKafka(
                "Kafka rechazó el evento: "
                f"{confirmacion['error']}"
            )

        mensaje_confirmado = confirmacion.get(
            "mensaje"
        )

        if mensaje_confirmado is None:
            raise ErrorPublicacionKafka(
                "No se recibió la confirmación "
                "del mensaje enviado."
            )

        return ResultadoPublicacionKafka(
            topic=mensaje_confirmado.topic(),
            particion=mensaje_confirmado.partition(),
            offset=mensaje_confirmado.offset(),
            distrito_id=evento.distrito_id.value,
            evento_id=str(evento.evento_id),
        )