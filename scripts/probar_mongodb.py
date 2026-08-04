from consumidor.almacenamiento_mongodb import (
    AlmacenamientoEventosMongoDB,
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
    """Comprueba conexión, inserción y duplicados."""

    almacenamiento = (
        AlmacenamientoEventosMongoDB()
    )

    try:
        conexion_correcta = (
            almacenamiento.comprobar_conexion()
        )

        almacenamiento.preparar_indices()

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

        primer_resultado = (
            almacenamiento.guardar_evento(
                evento=evento,
                topic="prueba-mongodb",
                particion=0,
                offset=0,
            )
        )

        segundo_resultado = (
            almacenamiento.guardar_evento(
                evento=evento,
                topic="prueba-mongodb",
                particion=0,
                offset=0,
            )
        )

        cantidad_guardada = (
            almacenamiento.contar_evento(
                str(evento.evento_id)
            )
        )

        print()
        print("Prueba de almacenamiento en MongoDB")
        print("----------------------------------")
        print(
            "Conexión correcta: "
            f"{conexion_correcta}"
        )
        print(
            "Evento ID: "
            f"{evento.evento_id}"
        )
        print()

        print("Primera inserción")
        print("-----------------")
        print(
            "Insertado: "
            f"{primer_resultado.insertado}"
        )
        print(
            "Duplicado: "
            f"{primer_resultado.duplicado}"
        )
        print(
            "Documento ID: "
            f"{primer_resultado.documento_id}"
        )
        print()

        print("Segunda inserción")
        print("-----------------")
        print(
            "Insertado: "
            f"{segundo_resultado.insertado}"
        )
        print(
            "Duplicado: "
            f"{segundo_resultado.duplicado}"
        )
        print(
            "Documento ID: "
            f"{segundo_resultado.documento_id}"
        )
        print()

        print(
            "Cantidad final de documentos "
            f"con ese evento_id: {cantidad_guardada}"
        )

        print()

        if (
            primer_resultado.insertado
            and segundo_resultado.duplicado
            and cantidad_guardada == 1
        ):
            print(
                "Resultado: MongoDB guardó el evento "
                "una sola vez y detectó el duplicado."
            )
        else:
            raise RuntimeError(
                "La prueba de duplicados no produjo "
                "el resultado esperado."
            )

        print()

    finally:
        almacenamiento.cerrar()


if __name__ == "__main__":
    main()