import json
import time
from dataclasses import dataclass

from confluent_kafka import (
    Consumer,
    KafkaError,
    KafkaException,
)
from pydantic import ValidationError

from consumidor.almacenamiento_mongodb import (
    AlmacenamientoEventosMongoDB,
    ErrorAlmacenamientoMongoDB,
)
from consumidor.configuracion import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_COMMIT_CADA_MENSAJES,
    KAFKA_CONSUMER_GROUP_PROCESAMIENTO,
    KAFKA_POLL_TIMEOUT_SEGUNDOS,
    KAFKA_TOPIC_LLAMADAS,
)
from generador.app.models.evento import (
    EventoEmergencia,
)


class ErrorProcesamientoEventos(RuntimeError):
    """Indica que el consumidor no pudo procesar los eventos."""


@dataclass(frozen=True)
class ResultadoProcesamiento:
    """Resumen de una ejecución del consumidor."""

    group_id: str
    mensajes_leidos: int
    eventos_insertados: int
    eventos_duplicados: int
    mensajes_malformados: int
    completo: bool
    duracion_ms: float
    eventos_por_segundo: float


class ProcesadorEventosKafkaMongoDB:
    """Consume eventos de Kafka y los almacena en MongoDB."""

    def __init__(self) -> None:
        self.group_id = (
            KAFKA_CONSUMER_GROUP_PROCESAMIENTO
        )

        self._consumidor = Consumer(
            {
                "bootstrap.servers":
                    KAFKA_BOOTSTRAP_SERVERS,

                "group.id":
                    self.group_id,

                # En la primera ejecución procesa únicamente
                # eventos publicados después de iniciar.
                "auto.offset.reset":
                    "latest",

                # Los offsets se controlan manualmente.
                "enable.auto.commit":
                    False,

                "enable.auto.offset.store":
                    False,
            }
        )

        self._almacenamiento = (
            AlmacenamientoEventosMongoDB()
        )

    @staticmethod
    def _convertir_evento(
        valor: bytes | None,
    ) -> EventoEmergencia:
        """Convierte el mensaje JSON en un evento validado."""

        if valor is None:
            raise ValueError(
                "El mensaje recibido no contiene información."
            )

        texto = valor.decode("utf-8")

        contenido = json.loads(texto)

        return EventoEmergencia.model_validate(
            contenido
        )

    def ejecutar(
        self,
        limite_eventos: int | None = None,
        timeout_sin_mensajes: float | None = None,
    ) -> ResultadoProcesamiento:
        """
        Procesa eventos hasta alcanzar el límite indicado.

        Si no se indica un límite, permanece ejecutándose
        continuamente hasta que el usuario lo detenga.
        """

        if (
            limite_eventos is not None
            and limite_eventos < 1
        ):
            raise ValueError(
                "El límite debe ser mayor que cero."
            )

        if (
            timeout_sin_mensajes is not None
            and timeout_sin_mensajes <= 0
        ):
            raise ValueError(
                "El timeout debe ser mayor que cero."
            )

        mensajes_leidos = 0
        eventos_insertados = 0
        eventos_duplicados = 0
        mensajes_malformados = 0

        eventos_validos_procesados = 0
        mensajes_desde_commit = 0

        inicio = time.perf_counter()
        ultimo_mensaje = inicio

        conexion_correcta = (
            self._almacenamiento.comprobar_conexion()
        )

        if not conexion_correcta:
            raise ErrorProcesamientoEventos(
                "MongoDB no respondió correctamente."
            )

        self._almacenamiento.preparar_indices()

        self._consumidor.subscribe(
            [KAFKA_TOPIC_LLAMADAS]
        )

        try:
            while True:
                mensaje = self._consumidor.poll(
                    timeout=KAFKA_POLL_TIMEOUT_SEGUNDOS
                )

                momento_actual = time.perf_counter()

                if mensaje is None:
                    if timeout_sin_mensajes is None:
                        continue

                    tiempo_sin_mensajes = (
                        momento_actual
                        - ultimo_mensaje
                    )

                    if (
                        tiempo_sin_mensajes
                        >= timeout_sin_mensajes
                    ):
                        break

                    continue

                if mensaje.error():
                    if (
                        mensaje.error().code()
                        == KafkaError._PARTITION_EOF
                    ):
                        continue

                    raise KafkaException(
                        mensaje.error()
                    )

                ultimo_mensaje = momento_actual
                mensajes_leidos += 1

                try:
                    evento = self._convertir_evento(
                        mensaje.value()
                    )
                except (
                    UnicodeDecodeError,
                    json.JSONDecodeError,
                    ValidationError,
                    ValueError,
                ) as error:
                    mensajes_malformados += 1

                    print(
                        "Mensaje malformado descartado | "
                        f"partición={mensaje.partition()} | "
                        f"offset={mensaje.offset()} | "
                        f"error={error}"
                    )

                    # Se confirma porque fue revisado y se decidió
                    # descartarlo. Así no crea un ciclo infinito.
                    self._consumidor.store_offsets(
                        message=mensaje
                    )

                    mensajes_desde_commit += 1
                else:
                    try:
                        resultado_guardado = (
                            self._almacenamiento.guardar_evento(
                                evento=evento,
                                topic=mensaje.topic(),
                                particion=(
                                    mensaje.partition()
                                ),
                                offset=mensaje.offset(),
                            )
                        )
                    except ErrorAlmacenamientoMongoDB:
                        # No se guarda el offset del evento que
                        # falló. Kafka podrá entregarlo nuevamente.
                        raise

                    if resultado_guardado.insertado:
                        eventos_insertados += 1

                        estado = "INSERTADO"
                    else:
                        eventos_duplicados += 1

                        estado = "DUPLICADO"

                    eventos_validos_procesados += 1

                    print(
                        f"{estado} | "
                        f"distrito="
                        f"{evento.distrito_id.value} | "
                        f"partición="
                        f"{mensaje.partition()} | "
                        f"offset={mensaje.offset()} | "
                        f"evento_id={evento.evento_id}"
                    )

                    # El offset se guarda únicamente después
                    # de que MongoDB respondió correctamente.
                    self._consumidor.store_offsets(
                        message=mensaje
                    )

                    mensajes_desde_commit += 1

                if (
                    mensajes_desde_commit
                    >= KAFKA_COMMIT_CADA_MENSAJES
                ):
                    self._consumidor.commit(
                        asynchronous=False
                    )

                    mensajes_desde_commit = 0

                if (
                    limite_eventos is not None
                    and eventos_validos_procesados
                    >= limite_eventos
                ):
                    break

        except (
            KafkaException,
            ErrorAlmacenamientoMongoDB,
        ) as error:
            raise ErrorProcesamientoEventos(
                f"El procesamiento fue interrumpido: {error}"
            ) from error

        finally:
            # Confirma los últimos mensajes procesados aunque
            # todavía no se haya completado un grupo de 100.
            if mensajes_desde_commit > 0:
                self._consumidor.commit(
                    asynchronous=False
                )

            self._consumidor.close()
            self._almacenamiento.cerrar()

        duracion_segundos = (
            time.perf_counter() - inicio
        )

        if duracion_segundos <= 0:
            duracion_segundos = 0.000001

        completo = (
            limite_eventos is None
            or eventos_validos_procesados
            >= limite_eventos
        )

        return ResultadoProcesamiento(
            group_id=self.group_id,
            mensajes_leidos=mensajes_leidos,
            eventos_insertados=eventos_insertados,
            eventos_duplicados=eventos_duplicados,
            mensajes_malformados=mensajes_malformados,
            completo=completo,
            duracion_ms=round(
                duracion_segundos * 1000,
                3,
            ),
            eventos_por_segundo=round(
                eventos_validos_procesados
                / duracion_segundos,
                2,
            ),
        )