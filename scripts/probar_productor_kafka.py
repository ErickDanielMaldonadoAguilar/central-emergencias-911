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


def main() -> None:
    """Genera y publica una llamada de prueba en Kafka."""

    solicitud = SolicitudLlamadaIndividual(
        distrito_id=DistritoId.CENTRO,
        tipo_emergencia=TipoEmergencia.MEDICA,
        prioridad=Prioridad.MEDIA,
        ubicacion=Ubicacion(
            sector="Bulevar Suyapa",
        ),
    )

    evento = crear_evento_individual(solicitud)

    productor = ProductorEventosKafka()

    resultado = productor.publicar_y_confirmar(evento)

    print()
    print("Evento enviado correctamente a Kafka")
    print("------------------------------------")
    print(f"Topic: {resultado.topic}")
    print(f"Partición: {resultado.particion}")
    print(f"Offset: {resultado.offset}")
    print(f"Distrito: {resultado.distrito_id}")
    print(f"Evento ID: {resultado.evento_id}")
    print()


if __name__ == "__main__":
    main()