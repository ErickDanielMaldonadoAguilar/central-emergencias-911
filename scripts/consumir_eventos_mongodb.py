import argparse

from consumidor.procesador_eventos import (
    ProcesadorEventosKafkaMongoDB,
)


def leer_argumentos() -> argparse.Namespace:
    """Lee la configuración de la ejecución."""

    parser = argparse.ArgumentParser(
        description=(
            "Consume llamadas desde Kafka "
            "y las almacena en MongoDB."
        )
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=None,
        help=(
            "Cantidad de eventos válidos que serán "
            "procesados antes de finalizar."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help=(
            "Tiempo máximo sin recibir mensajes "
            "antes de finalizar."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Ejecuta el consumidor Kafka hacia MongoDB."""

    argumentos = leer_argumentos()

    print()
    print("Consumidor Kafka → MongoDB")
    print("--------------------------")
    print(
        "Esperando eventos nuevos en "
        "llamadas-emergencia..."
    )
    print()

    procesador = (
        ProcesadorEventosKafkaMongoDB()
    )

    resultado = procesador.ejecutar(
        limite_eventos=argumentos.limite,
        timeout_sin_mensajes=argumentos.timeout,
    )

    print()
    print("Resumen del procesamiento")
    print("-------------------------")
    print(f"Grupo: {resultado.group_id}")
    print(
        f"Mensajes leídos: "
        f"{resultado.mensajes_leidos}"
    )
    print(
        f"Eventos insertados: "
        f"{resultado.eventos_insertados}"
    )
    print(
        f"Eventos duplicados: "
        f"{resultado.eventos_duplicados}"
    )
    print(
        f"Mensajes malformados: "
        f"{resultado.mensajes_malformados}"
    )
    print(
        f"Duración: "
        f"{resultado.duracion_ms} ms"
    )
    print(
        f"Eventos por segundo: "
        f"{resultado.eventos_por_segundo}"
    )
    print(
        f"Prueba completa: "
        f"{resultado.completo}"
    )
    print()


if __name__ == "__main__":
    main()