import json
import time
from collections import Counter
from dataclasses import dataclass
from uuid import UUID, uuid4

from confluent_kafka import (
    Consumer,
    KafkaError,
    KafkaException,
)
from pydantic import ValidationError

from consumidor.configuracion import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_COMMIT_CADA_MENSAJES,
    KAFKA_CONSUMER_GROUP_PREFIX,
    KAFKA_TOPIC_LLAMADAS,
)
from generador.app.models.evento import (
    EventoEmergencia,
)


class ErrorConsumoKafka(RuntimeError):
    """Indica que Kafka no pudo entregar los eventos esperados."""


@dataclass(frozen=True)
class ResultadoConsumoLote:
    """Resultado de leer y validar un lote desde Kafka."""

    group_id: str
    lote_id: str
    cantidad_esperada: int
    cantidad_valida: int
    cantidad_duplicada: int
    cantidad_malformada: int
    cantidad_otros_lotes: int
    total_mensajes_leidos: int
    completo: bool
    duracion_ms: float
    eventos_por_segundo: float
    distribucion_distritos: dict[str, int]
    distribucion_tipos: dict[str, int]
    distribucion_prioridades: dict[str, int]
    mensajes_por_particion: dict[int, int]
    primer_offset_por_particion: dict[int, int]
    ultimo_offset_por_particion: dict[int, int]
    errores_muestra: list[str]


class ConsumidorLoteKafka:
    """Lee, valida y contabiliza eventos almacenados en Kafka."""

    def __init__(
        self,
        group_id: str | None = None,
    ) -> None:
        identificador_grupo = (
            group_id
            or (
                f"{KAFKA_CONSUMER_GROUP_PREFIX}-"
                f"{uuid4().hex[:8]}"
            )
        )

        self.group_id = identificador_grupo

        self._consumidor = Consumer(
            {
                "bootstrap.servers":
                    KAFKA_BOOTSTRAP_SERVERS,

                "group.id":
                    identificador_grupo,

                "auto.offset.reset":
                    "earliest",

                "enable.auto.commit":
                    False,

                "enable.auto.offset.store":
                    False,
            }
        )

    @staticmethod
    def _convertir_evento(
        valor: bytes | None,
    ) -> EventoEmergencia:
        """Convierte y valida el JSON recibido desde Kafka."""

        if valor is None:
            raise ValueError(
                "El mensaje no contiene información."
            )

        texto = valor.decode("utf-8")

        contenido = json.loads(texto)

        return EventoEmergencia.model_validate(
            contenido
        )

    def consumir_lote(
        self,
        lote_id: UUID,
        cantidad_esperada: int,
        timeout_sin_mensajes: float = 15.0,
    ) -> ResultadoConsumoLote:
        """Busca y valida un lote específico dentro del topic."""

        if cantidad_esperada < 1:
            raise ValueError(
                "La cantidad esperada debe ser mayor que cero."
            )

        lote_buscado = str(lote_id)

        eventos_identificados: set[str] = set()

        contador_distritos: Counter[str] = Counter()
        contador_tipos: Counter[str] = Counter()
        contador_prioridades: Counter[str] = Counter()
        contador_particiones: Counter[int] = Counter()

        primer_offset: dict[int, int] = {}
        ultimo_offset: dict[int, int] = {}

        errores_muestra: list[str] = []

        cantidad_valida = 0
        cantidad_duplicada = 0
        cantidad_malformada = 0
        cantidad_otros_lotes = 0
        total_mensajes_leidos = 0

        mensajes_desde_commit = 0

        inicio = time.perf_counter()
        ultimo_mensaje_recibido = inicio

        self._consumidor.subscribe(
            [KAFKA_TOPIC_LLAMADAS]
        )

        try:
            while cantidad_valida < cantidad_esperada:
                mensaje = self._consumidor.poll(
                    timeout=1.0
                )

                momento_actual = time.perf_counter()

                if mensaje is None:
                    tiempo_sin_mensajes = (
                        momento_actual
                        - ultimo_mensaje_recibido
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

                ultimo_mensaje_recibido = momento_actual
                total_mensajes_leidos += 1

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
                    cantidad_malformada += 1

                    if len(errores_muestra) < 5:
                        errores_muestra.append(
                            (
                                f"Partición "
                                f"{mensaje.partition()}, "
                                f"offset {mensaje.offset()}: "
                                f"{error}"
                            )
                        )
                else:
                    evento_lote_id = (
                        str(evento.lote_id)
                        if evento.lote_id is not None
                        else None
                    )

                    if evento_lote_id != lote_buscado:
                        cantidad_otros_lotes += 1
                    else:
                        evento_id = str(
                            evento.evento_id
                        )

                        if (
                            evento_id
                            in eventos_identificados
                        ):
                            cantidad_duplicada += 1
                        else:
                            eventos_identificados.add(
                                evento_id
                            )

                            cantidad_valida += 1

                            contador_distritos[
                                evento.distrito_id.value
                            ] += 1

                            contador_tipos[
                                evento.tipo_emergencia.value
                            ] += 1

                            contador_prioridades[
                                evento.prioridad.value
                            ] += 1

                            particion = (
                                mensaje.partition()
                            )

                            offset = mensaje.offset()

                            contador_particiones[
                                particion
                            ] += 1

                            if (
                                particion
                                not in primer_offset
                            ):
                                primer_offset[
                                    particion
                                ] = offset

                            ultimo_offset[
                                particion
                            ] = offset

                # El offset se guarda únicamente después de que
                # el mensaje fue revisado.
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

            if mensajes_desde_commit > 0:
                self._consumidor.commit(
                    asynchronous=False
                )

        except KafkaException as error:
            raise ErrorConsumoKafka(
                f"Kafka devolvió un error: {error}"
            ) from error
        finally:
            self._consumidor.close()

        duracion_segundos = (
            time.perf_counter() - inicio
        )

        if duracion_segundos <= 0:
            duracion_segundos = 0.000001

        completo = (
            cantidad_valida
            == cantidad_esperada
        )

        return ResultadoConsumoLote(
            group_id=self.group_id,
            lote_id=lote_buscado,
            cantidad_esperada=cantidad_esperada,
            cantidad_valida=cantidad_valida,
            cantidad_duplicada=cantidad_duplicada,
            cantidad_malformada=cantidad_malformada,
            cantidad_otros_lotes=cantidad_otros_lotes,
            total_mensajes_leidos=(
                total_mensajes_leidos
            ),
            completo=completo,
            duracion_ms=round(
                duracion_segundos * 1000,
                3,
            ),
            eventos_por_segundo=round(
                cantidad_valida
                / duracion_segundos,
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
            mensajes_por_particion=dict(
                sorted(
                    contador_particiones.items()
                )
            ),
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
            errores_muestra=errores_muestra,
        )