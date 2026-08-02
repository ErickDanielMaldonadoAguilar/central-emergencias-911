import json
from typing import Callable

from confluent_kafka import (
    KafkaError,
    Message,
    Producer,
)

from generador.app.configuracion_kafka import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_LLAMADAS,
    PARTICIONES_POR_DISTRITO,
)
from generador.app.models.evento import (
    DistritoId,
    Prioridad,
    SolicitudLlamadaIndividual,
    TipoEmergencia,
    Ubicacion,
)
from generador.app.services.generador_eventos import (
    crear_evento_individual,
)


def main() -> None:
    """
    Publica un mensaje malformado, un evento válido
    y el mismo evento nuevamente como duplicado.
    """

    productor = Producer(
        {
            "bootstrap.servers":
                KAFKA_BOOTSTRAP_SERVERS,

            "client.id":
                "central911-prueba-limpieza",

            "enable.idempotence":
                True,

            "acks":
                "all",
        }
    )

    solicitud = SolicitudLlamadaIndividual(
        distrito_id=DistritoId.CENTRO,
        tipo_emergencia=TipoEmergencia.MEDICA,
        prioridad=Prioridad.MEDIA,
        ubicacion=Ubicacion(
            sector="Bulevar Suyapa",
        ),
    )

    evento = crear_evento_individual(
        solicitud
    )

    particion = PARTICIONES_POR_DISTRITO[
        evento.distrito_id
    ]

    clave = evento.distrito_id.value.encode(
        "utf-8"
    )

    evento_json = json.dumps(
        evento.model_dump(
            mode="json"
        ),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    # Este contenido está incompleto intencionalmente
    # para provocar un error de validación JSON.
    mensaje_malformado = (
        b'{"distrito_id":"D-01",'
        b'"tipo_emergencia":'
    )

    mensajes = [
        (
            "MALFORMADO",
            mensaje_malformado,
        ),
        (
            "VALIDO",
            evento_json,
        ),
        (
            "DUPLICADO",
            evento_json,
        ),
    ]

    confirmaciones: list[
        tuple[str, int, int]
    ] = []

    errores: list[str] = []

    def crear_callback(
        etiqueta: str,
    ) -> Callable[
        [KafkaError | None, Message],
        None,
    ]:
        """Crea el callback para cada mensaje enviado."""

        def registrar_confirmacion(
            error: KafkaError | None,
            mensaje: Message,
        ) -> None:
            if error is not None:
                errores.append(
                    f"{etiqueta}: {error}"
                )

                return

            confirmaciones.append(
                (
                    etiqueta,
                    mensaje.partition(),
                    mensaje.offset(),
                )
            )

        return registrar_confirmacion

    for etiqueta, contenido in mensajes:
        productor.produce(
            topic=KAFKA_TOPIC_LLAMADAS,
            key=clave,
            value=contenido,
            partition=particion,
            on_delivery=crear_callback(
                etiqueta
            ),
        )

        productor.poll(0)

    pendientes = productor.flush(
        15.0
    )

    if pendientes > 0:
        raise RuntimeError(
            "Quedaron mensajes sin confirmar: "
            f"{pendientes}"
        )

    if errores:
        raise RuntimeError(
            "Kafka reportó errores: "
            + "; ".join(errores)
        )

    if len(confirmaciones) != 3:
        raise RuntimeError(
            "Se esperaban tres confirmaciones, "
            f"pero se recibieron {len(confirmaciones)}."
        )

    print()
    print("Prueba de duplicado y mensaje malformado")
    print("----------------------------------------")
    print(
        f"Evento ID utilizado: "
        f"{evento.evento_id}"
    )
    print(
        f"Distrito: "
        f"{evento.distrito_id.value}"
    )
    print(
        f"Partición: "
        f"{particion}"
    )
    print()

    print("Mensajes confirmados por Kafka")
    print("------------------------------")

    for etiqueta, particion_obtenida, offset in (
        confirmaciones
    ):
        print(
            f"{etiqueta} | "
            f"partición={particion_obtenida} | "
            f"offset={offset}"
        )

    print()
    print(
        "Resultado: Kafka confirmó los tres "
        "mensajes de la prueba."
    )
    print()


if __name__ == "__main__":
    main()