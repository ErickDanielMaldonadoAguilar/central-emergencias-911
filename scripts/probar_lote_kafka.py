import argparse

from generador.app.models.evento import SolicitudLote
from generador.app.services.generador_eventos import (
    crear_lote_eventos_completo,
)
from generador.app.services.productor_kafka import (
    ProductorEventosKafka,
)


def leer_argumentos() -> argparse.Namespace:
    """Lee la cantidad y la semilla desde la terminal."""

    parser = argparse.ArgumentParser(
        description=(
            "Genera un lote de emergencias "
            "y lo publica en Apache Kafka."
        )
    )

    parser.add_argument(
        "--cantidad",
        type=int,
        default=1000,
        choices=range(1, 10001),
        metavar="1-10000",
        help=(
            "Cantidad de eventos que se enviarán. "
            "Valor predeterminado: 1000."
        ),
    )

    parser.add_argument(
        "--semilla",
        type=int,
        default=911,
        help=(
            "Semilla utilizada para repetir "
            "la distribución del lote."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Genera y publica un lote completo en Kafka."""

    argumentos = leer_argumentos()

    solicitud = SolicitudLote(
        cantidad=argumentos.cantidad,
        semilla=argumentos.semilla,
        escenario="normal",
    )

    lote = crear_lote_eventos_completo(
        solicitud
    )

    productor = ProductorEventosKafka()

    resultado_kafka = (
        productor.publicar_lote_y_confirmar(
            lote.eventos
        )
    )

    print()
    print("Prueba de pico masivo hacia Kafka")
    print("--------------------------------")
    print(f"Lote ID: {lote.resumen.lote_id}")
    print()

    print("Generación en memoria")
    print("---------------------")
    print(
        "Cantidad generada: "
        f"{lote.resumen.cantidad_generada}"
    )
    print(
        "Duración: "
        f"{lote.resumen.duracion_ms} ms"
    )
    print(
        "Eventos por segundo: "
        f"{lote.resumen.eventos_por_segundo}"
    )
    print()

    print("Publicación en Kafka")
    print("--------------------")
    print(
        "Cantidad enviada: "
        f"{resultado_kafka.cantidad_enviada}"
    )
    print(
        "Cantidad confirmada: "
        f"{resultado_kafka.cantidad_confirmada}"
    )
    print(
        "Cantidad fallida: "
        f"{resultado_kafka.cantidad_fallida}"
    )
    print(
        "Duración: "
        f"{resultado_kafka.duracion_ms} ms"
    )
    print(
        "Eventos por segundo: "
        f"{resultado_kafka.eventos_por_segundo}"
    )
    print()

    print("Confirmaciones por partición")
    print("----------------------------")

    for particion, cantidad in (
        resultado_kafka
        .confirmaciones_por_particion
        .items()
    ):
        primer_offset = (
            resultado_kafka
            .primer_offset_por_particion
            .get(particion)
        )

        ultimo_offset = (
            resultado_kafka
            .ultimo_offset_por_particion
            .get(particion)
        )

        print(
            f"Partición {particion}: "
            f"{cantidad} eventos | "
            f"offset inicial {primer_offset} | "
            f"offset final {ultimo_offset}"
        )

    print()
    print("--------------------------------")

    if resultado_kafka.cantidad_fallida == 0:
        print(
            "Resultado: todos los eventos "
            "fueron confirmados por Kafka."
        )

    print()


if __name__ == "__main__":
    main()