import json
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any

from confluent_kafka import (
    KafkaError,
    Message,
    Producer,
)

from generador.app.configuracion_kafka import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CLIENT_ID,
    KAFKA_TOPIC_LLAMADAS,
    PARTICIONES_POR_DISTRITO,
)
from generador.app.models.evento import (
    EventoEmergencia,
)


class ErrorPublicacionKafka(RuntimeError):
    """Indica que Kafka no confirmó uno o más eventos."""


@dataclass(frozen=True)
class ResultadoPublicacionKafka:
    """Confirmación de un solo evento publicado."""

    topic: str
    particion: int
    offset: int
    distrito_id: str
    evento_id: str


@dataclass(frozen=True)
class ResultadoPublicacionLoteKafka:
    """Resumen de la publicación masiva hacia Kafka."""

    topic: str
    cantidad_enviada: int
    cantidad_confirmada: int
    cantidad_fallida: int
    duracion_ms: float
    eventos_por_segundo: float
    confirmaciones_por_particion: dict[int, int]
    primer_offset_por_particion: dict[int, int]
    ultimo_offset_por_particion: dict[int, int]


class ProductorEventosKafka:
    """Publica eventos de emergencia en Apache Kafka."""

    def __init__(self) -> None:
        self._productor = Producer(
            {
                "bootstrap.servers":
                    KAFKA_BOOTSTRAP_SERVERS,

                "client.id":
                    KAFKA_CLIENT_ID,

                "enable.idempotence":
                    True,

                "acks":
                    "all",
            }
        )

    @staticmethod
    def _serializar_evento(
        evento: EventoEmergencia,
    ) -> bytes:
        """Convierte un evento validado a JSON en UTF-8."""

        contenido_evento = evento.model_dump(
            mode="json"
        )

        return json.dumps(
            contenido_evento,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

    def publicar_y_confirmar(
        self,
        evento: EventoEmergencia,
        timeout_segundos: float = 10.0,
    ) -> ResultadoPublicacionKafka:
        """Publica un evento y espera la confirmación del broker."""

        particion = PARTICIONES_POR_DISTRITO[
            evento.distrito_id
        ]

        mensaje_json = self._serializar_evento(
            evento
        )

        clave = evento.distrito_id.value.encode(
            "utf-8"
        )

        confirmacion: dict[str, Any] = {}

        def registrar_confirmacion(
            error: KafkaError | None,
            mensaje: Message,
        ) -> None:
            if error is not None:
                confirmacion["error"] = str(
                    error
                )
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

        mensajes_pendientes = (
            self._productor.flush(
                timeout_segundos
            )
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

    def publicar_lote_y_confirmar(
        self,
        eventos: list[EventoEmergencia],
        timeout_segundos: float = 60.0,
    ) -> ResultadoPublicacionLoteKafka:
        """Publica un lote y espera las confirmaciones de Kafka."""

        if not eventos:
            raise ValueError(
                "El lote no contiene eventos."
            )

        particiones = sorted(
            set(
                PARTICIONES_POR_DISTRITO.values()
            )
        )

        confirmaciones: Counter[int] = Counter(
            {
                particion: 0
                for particion in particiones
            }
        )

        primer_offset: dict[int, int] = {}
        ultimo_offset: dict[int, int] = {}

        errores: list[str] = []

        def registrar_confirmacion(
            error: KafkaError | None,
            mensaje: Message,
        ) -> None:
            if error is not None:
                if len(errores) < 10:
                    errores.append(str(error))
                return

            particion = mensaje.partition()
            offset = mensaje.offset()

            confirmaciones[particion] += 1

            if particion not in primer_offset:
                primer_offset[particion] = offset

            ultimo_offset[particion] = offset

        inicio = time.perf_counter()

        for evento in eventos:
            particion = PARTICIONES_POR_DISTRITO[
                evento.distrito_id
            ]

            clave = evento.distrito_id.value.encode(
                "utf-8"
            )

            mensaje_json = self._serializar_evento(
                evento
            )

            while True:
                try:
                    self._productor.produce(
                        topic=KAFKA_TOPIC_LLAMADAS,
                        key=clave,
                        value=mensaje_json,
                        partition=particion,
                        on_delivery=registrar_confirmacion,
                    )

                    break
                except BufferError:
                    self._productor.poll(0.1)

            self._productor.poll(0)

        pendientes = self._productor.flush(
            timeout_segundos
        )

        duracion_segundos = (
            time.perf_counter() - inicio
        )

        if duracion_segundos <= 0:
            duracion_segundos = 0.000001

        cantidad_confirmada = sum(
            confirmaciones.values()
        )

        cantidad_enviada = len(eventos)

        cantidad_fallida = (
            cantidad_enviada
            - cantidad_confirmada
        )

        if pendientes > 0:
            errores.append(
                f"Quedaron {pendientes} mensajes "
                "sin confirmar al vencer el tiempo."
            )

        if cantidad_fallida > 0:
            detalle_errores = "; ".join(
                errores
            )

            raise ErrorPublicacionKafka(
                "Kafka no confirmó todo el lote. "
                f"Enviados: {cantidad_enviada}. "
                f"Confirmados: {cantidad_confirmada}. "
                f"Fallidos: {cantidad_fallida}. "
                f"Detalles: {detalle_errores}"
            )

        return ResultadoPublicacionLoteKafka(
            topic=KAFKA_TOPIC_LLAMADAS,
            cantidad_enviada=cantidad_enviada,
            cantidad_confirmada=cantidad_confirmada,
            cantidad_fallida=cantidad_fallida,
            duracion_ms=round(
                duracion_segundos * 1000,
                3,
            ),
            eventos_por_segundo=round(
                cantidad_confirmada
                / duracion_segundos,
                2,
            ),
            confirmaciones_por_particion={
                particion: confirmaciones[
                    particion
                ]
                for particion in particiones
            },
            primer_offset_por_particion=dict(
                sorted(
                    primer_offset.items()
                )
            ),
            ultimo_offset_por_particion=dict(
                sorted(
                    ultimo_offset.items()
                )
            ),
        )