import argparse
from uuid import UUID

from consumidor.consumidor_kafka import (
    ConsumidorLoteKafka,
)


def leer_argumentos() -> argparse.Namespace:
    """Lee los parámetros utilizados en la verificación."""

    parser = argparse.ArgumentParser(
        description=(
            "Busca un lote en Kafka, valida sus eventos "
            "y calcula sus distribuciones."
        )
    )

    parser.add_argument(
        "--lote-id",
        type=UUID,
        required=True,
        help="Identificador UUID del lote que será buscado.",
    )

    parser.add_argument(
        "--cantidad",
        type=int,
        required=True,
        help="Cantidad de eventos esperada en el lote.",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help=(
            "Segundos de espera sin recibir mensajes "
            "antes de terminar la búsqueda."
        ),
    )

    return parser.parse_args()


def imprimir_distribucion(
    titulo: str,
    valores: dict[str, int],
) -> None:
    """Imprime una distribución de forma ordenada."""

    print()
    print(titulo)
    print("-" * len(titulo))

    for clave, cantidad in sorted(
        valores.items()
    ):
        print(f"{clave}: {cantidad}")


def main() -> None:
    """Ejecuta la comprobación de un lote publicado."""

    argumentos = leer_argumentos()

    consumidor = ConsumidorLoteKafka()

    resultado = consumidor.consumir_lote(
        lote_id=argumentos.lote_id,
        cantidad_esperada=argumentos.cantidad,
        timeout_sin_mensajes=argumentos.timeout,
    )

    print()
    print("Verificación del consumidor de Kafka")
    print("------------------------------------")
    print(f"Grupo temporal: {resultado.group_id}")
    print(f"Lote buscado: {resultado.lote_id}")
    print()

    print("Resultado general")
    print("-----------------")
    print(
        f"Cantidad esperada: "
        f"{resultado.cantidad_esperada}"
    )
    print(
        f"Cantidad válida: "
        f"{resultado.cantidad_valida}"
    )
    print(
        f"Duplicados encontrados: "
        f"{resultado.cantidad_duplicada}"
    )
    print(
        f"Mensajes malformados: "
        f"{resultado.cantidad_malformada}"
    )
    print(
        f"Mensajes de otros lotes: "
        f"{resultado.cantidad_otros_lotes}"
    )
    print(
        f"Total de mensajes leídos: "
        f"{resultado.total_mensajes_leidos}"
    )
    print(
        f"Duración: "
        f"{resultado.duracion_ms} ms"
    )
    print(
        f"Eventos válidos por segundo: "
        f"{resultado.eventos_por_segundo}"
    )

    imprimir_distribucion(
        "Distribución por distrito",
        resultado.distribucion_distritos,
    )

    imprimir_distribucion(
        "Distribución por tipo",
        resultado.distribucion_tipos,
    )

    imprimir_distribucion(
        "Distribución por prioridad",
        resultado.distribucion_prioridades,
    )

    print()
    print("Mensajes del lote por partición")
    print("--------------------------------")

    for particion, cantidad in (
        resultado.mensajes_por_particion.items()
    ):
        inicial = (
            resultado
            .primer_offset_por_particion
            .get(particion)
        )

        final = (
            resultado
            .ultimo_offset_por_particion
            .get(particion)
        )

        print(
            f"Partición {particion}: "
            f"{cantidad} eventos | "
            f"offset inicial {inicial} | "
            f"offset final {final}"
        )

    if resultado.errores_muestra:
        print()
        print("Muestra de errores")
        print("------------------")

        for error in resultado.errores_muestra:
            print(error)

    print()
    print("------------------------------------")

    if resultado.completo:
        print(
            "Resultado: el consumidor encontró "
            "todos los eventos esperados."
        )
    else:
        print(
            "Resultado: el consumidor no encontró "
            "todos los eventos esperados."
        )

        raise SystemExit(1)

    print()


if __name__ == "__main__":
    main()