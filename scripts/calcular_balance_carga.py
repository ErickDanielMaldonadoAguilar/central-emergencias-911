from consumidor.balance_carga import (
    ServicioBalanceCargaMongoDB,
)


def main() -> None:
    """Calcula y guarda el balance de los distritos."""

    servicio = ServicioBalanceCargaMongoDB()

    try:
        conexion_correcta = (
            servicio.comprobar_conexion()
        )

        if not conexion_correcta:
            raise RuntimeError(
                "MongoDB no respondió correctamente."
            )

        servicio.preparar_indices()

        balances = (
            servicio.calcular_y_guardar()
        )

        print()
        print("Balance de carga por distrito")
        print("-----------------------------")
        print()

        total_llamadas = 0
        total_unidades = 0
        distritos_sobrecargados = 0
        exceso_total = 0

        for balance in balances:
            total_llamadas += (
                balance.llamadas_activas
            )

            total_unidades += (
                balance.unidades_disponibles
            )

            if (
                balance.estado_balance
                == "sobrecargado"
            ):
                distritos_sobrecargados += 1

                exceso_total += abs(
                    balance.saldo_unidades
                )

            print(
                f"{balance.distrito_id} — "
                f"{balance.distrito_nombre}"
            )

            print(
                "  Llamadas activas: "
                f"{balance.llamadas_activas}"
            )

            print(
                "  Unidades disponibles: "
                f"{balance.unidades_disponibles}"
            )

            print(
                "  Saldo de unidades: "
                f"{balance.saldo_unidades}"
            )

            print(
                "  Porcentaje de carga: "
                f"{balance.porcentaje_carga}%"
            )

            print(
                "  Estado: "
                f"{balance.estado_balance.upper()}"
            )

            print("  Distribución por tipo:")

            for tipo, cantidad in (
                balance
                .distribucion_tipos
                .items()
            ):
                print(
                    f"    {tipo}: {cantidad}"
                )

            print()

        saldo_central = (
            total_unidades
            - total_llamadas
        )

        print("Exposición general de la central")
        print("--------------------------------")
        print(
            f"Llamadas activas: {total_llamadas}"
        )
        print(
            f"Unidades disponibles: "
            f"{total_unidades}"
        )
        print(
            f"Saldo general: {saldo_central}"
        )
        print(
            "Distritos sobrecargados: "
            f"{distritos_sobrecargados}"
        )
        print(
            "Llamadas que exceden la capacidad: "
            f"{exceso_total}"
        )
        print()

        print(
            "Resultado: los balances fueron "
            "calculados y guardados en MongoDB."
        )
        print()

    finally:
        servicio.cerrar()


if __name__ == "__main__":
    main()