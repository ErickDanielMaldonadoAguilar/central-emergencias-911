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
from generador.app.services.productor_kafka import (
    ProductorEventosKafka,
)


CASOS_DE_PRUEBA = [
    (
        DistritoId.CENTRO,
        "Zona Centro A",
        0,
    ),
    (
        DistritoId.NORTE,
        "Zona Norte A",
        1,
    ),
    (
        DistritoId.SUR,
        "Zona Sur A",
        2,
    ),
    (
        DistritoId.ESTE,
        "Zona Este A",
        3,
    ),
    (
        DistritoId.OESTE,
        "Zona Oeste A",
        4,
    ),
    (
        DistritoId.COMAYAGUELA,
        "Zona Comayagüela A",
        5,
    ),
]


def main() -> None:
    """Envía una emergencia por cada distrito simulado."""

    productor = ProductorEventosKafka()

    resultados_correctos = 0

    print()
    print("Prueba de distribución por particiones")
    print("-------------------------------------")

    for distrito, sector, particion_esperada in CASOS_DE_PRUEBA:
        solicitud = SolicitudLlamadaIndividual(
            distrito_id=distrito,
            tipo_emergencia=TipoEmergencia.MEDICA,
            prioridad=Prioridad.MEDIA,
            ubicacion=Ubicacion(
                sector=sector,
            ),
        )

        evento = crear_evento_individual(
            solicitud
        )

        resultado = productor.publicar_y_confirmar(
            evento
        )

        es_correcto = (
            resultado.particion
            == particion_esperada
        )

        estado = (
            "CORRECTO"
            if es_correcto
            else "INCORRECTO"
        )

        print()
        print(
            f"Distrito: {resultado.distrito_id}"
        )
        print(
            f"Partición esperada: {particion_esperada}"
        )
        print(
            f"Partición obtenida: {resultado.particion}"
        )
        print(
            f"Offset: {resultado.offset}"
        )
        print(
            f"Resultado: {estado}"
        )

        if not es_correcto:
            raise RuntimeError(
                "La asignación de particiones "
                f"falló para {resultado.distrito_id}."
            )

        resultados_correctos += 1

    print()
    print("-------------------------------------")
    print(
        "Prueba finalizada correctamente: "
        f"{resultados_correctos} de "
        f"{len(CASOS_DE_PRUEBA)} distritos."
    )
    print()


if __name__ == "__main__":
    main()