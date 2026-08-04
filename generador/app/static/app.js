const estadoServicio = document.getElementById(
    "estadoServicio"
);

const formularioIndividual = document.getElementById(
    "formularioIndividual"
);

const formularioLote = document.getElementById(
    "formularioLote"
);

const botonIndividual = document.getElementById(
    "botonIndividual"
);

const botonLote = document.getElementById(
    "botonLote"
);

const mensajeResultado = document.getElementById(
    "mensajeResultado"
);

const estadoResultado = document.getElementById(
    "estadoResultado"
);

const salida = document.getElementById(
    "salida"
);

const metricas = document.getElementById(
    "metricas"
);

const cantidadGenerada = document.getElementById(
    "cantidadGenerada"
);

const duracionGeneracion = document.getElementById(
    "duracionGeneracion"
);

const eventosSegundo = document.getElementById(
    "eventosSegundo"
);


function cambiarEstadoResultado(tipo, texto) {
    estadoResultado.className = "";
    estadoResultado.textContent = texto;

    if (tipo === "exito") {
        estadoResultado.classList.add(
            "resultado-exito"
        );
    }

    if (tipo === "error") {
        estadoResultado.classList.add(
            "resultado-error"
        );
    }

    if (tipo === "procesando") {
        estadoResultado.classList.add(
            "resultado-procesando"
        );
    }
}


function mostrarError(error) {
    metricas.classList.add("oculto");

    mensajeResultado.textContent =
        "No se pudo completar la operación.";

    salida.textContent = JSON.stringify(
        error,
        null,
        2
    );

    cambiarEstadoResultado(
        "error",
        "Error"
    );
}


async function enviarDatos(url, datos) {
    const respuesta = await fetch(url, {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(datos)
    });

    const contenido = await respuesta.json();

    if (!respuesta.ok) {
        throw contenido;
    }

    return contenido;
}


async function comprobarServicio() {
    try {
        const respuesta = await fetch("/health");

        if (!respuesta.ok) {
            throw new Error(
                "El servicio respondió con un error."
            );
        }

        estadoServicio.textContent =
            "Servicio generador activo";

        estadoServicio.className =
            "estado estado-activo";
    } catch (error) {
        estadoServicio.textContent =
            "Servicio generador no disponible";

        estadoServicio.className =
            "estado estado-error";
    }
}


formularioIndividual.addEventListener(
    "submit",
    async (eventoFormulario) => {
        eventoFormulario.preventDefault();

        botonIndividual.disabled = true;

        botonIndividual.textContent =
            "Enviando a Kafka...";

        metricas.classList.add("oculto");

        mensajeResultado.textContent =
            "Generando la llamada y esperando "
            + "la confirmación de Kafka.";

        salida.textContent =
            "Procesando solicitud...";

        cambiarEstadoResultado(
            "procesando",
            "Procesando"
        );

        const solicitud = {
            distrito_id:
                document.getElementById(
                    "distrito"
                ).value,

            tipo_emergencia:
                document.getElementById(
                    "tipoEmergencia"
                ).value,

            prioridad:
                document.getElementById(
                    "prioridad"
                ).value,

            ubicacion: {
                sector:
                    document.getElementById(
                        "sector"
                    ).value.trim()
            }
        };

        try {
            const resultado = await enviarDatos(
                "/eventos/individual/kafka",
                solicitud
            );

            mensajeResultado.textContent =
                "La llamada fue generada y "
                + "confirmada por Kafka.";

            salida.textContent = JSON.stringify(
                resultado,
                null,
                2
            );

            cambiarEstadoResultado(
                "exito",
                "Confirmado"
            );
        } catch (error) {
            mostrarError(error);
        } finally {
            botonIndividual.disabled = false;

            botonIndividual.textContent =
                "Generar llamada";
        }
    }
);


formularioLote.addEventListener(
    "submit",
    async (eventoFormulario) => {
        eventoFormulario.preventDefault();

        botonLote.disabled = true;

        botonLote.textContent =
            "Enviando lote a Kafka...";

        metricas.classList.add("oculto");

        mensajeResultado.textContent =
            "Generando los eventos y esperando "
            + "las confirmaciones de Kafka.";

        salida.textContent =
            "Procesando lote masivo...";

        cambiarEstadoResultado(
            "procesando",
            "Procesando"
        );

        const semillaTexto =
            document.getElementById(
                "semilla"
            ).value;

        const solicitud = {
            cantidad: Number(
                document.getElementById(
                    "cantidad"
                ).value
            ),

            semilla:
                semillaTexto === ""
                    ? null
                    : Number(semillaTexto),

            escenario: "normal"
        };

        try {
            const resultado = await enviarDatos(
                "/eventos/lote/kafka",
                solicitud
            );

            cantidadGenerada.textContent =
                resultado.kafka
                    .cantidad_confirmada
                    .toLocaleString("es-HN");

            duracionGeneracion.textContent =
                `${resultado.kafka.duracion_ms
                    .toLocaleString("es-HN")} ms`;

            eventosSegundo.textContent =
                resultado.kafka
                    .eventos_por_segundo
                    .toLocaleString("es-HN");

            metricas.classList.remove("oculto");

            mensajeResultado.textContent =
                "El lote fue generado y todos los eventos "
                + "fueron confirmados por Kafka.";

            salida.textContent = JSON.stringify(
                resultado,
                null,
                2
            );

            cambiarEstadoResultado(
                "exito",
                "Confirmado"
            );
        } catch (error) {
            mostrarError(error);
        } finally {
            botonLote.disabled = false;

            botonLote.textContent =
                "Generar y enviar lote";
        }
    }
);


comprobarServicio();