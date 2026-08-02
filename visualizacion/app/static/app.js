const estadoServicio = document.getElementById(
    "estadoServicio"
);

const selectorDistrito = document.getElementById(
    "selectorDistrito"
);

const botonActualizar = document.getElementById(
    "botonActualizar"
);

const fechaCalculo = document.getElementById(
    "fechaCalculo"
);

const estadoCentral = document.getElementById(
    "estadoCentral"
);

const centralLlamadas = document.getElementById(
    "centralLlamadas"
);

const centralUnidades = document.getElementById(
    "centralUnidades"
);

const centralSaldo = document.getElementById(
    "centralSaldo"
);

const centralPorcentaje = document.getElementById(
    "centralPorcentaje"
);

const centralSobrecargados = document.getElementById(
    "centralSobrecargados"
);

const centralExcedentes = document.getElementById(
    "centralExcedentes"
);

const nombreDistrito = document.getElementById(
    "nombreDistrito"
);

const estadoDistrito = document.getElementById(
    "estadoDistrito"
);

const llamadasActivas = document.getElementById(
    "llamadasActivas"
);

const unidadesDisponibles = document.getElementById(
    "unidadesDisponibles"
);

const saldoUnidades = document.getElementById(
    "saldoUnidades"
);

const porcentajeCarga = document.getElementById(
    "porcentajeCarga"
);

const textoCarga = document.getElementById(
    "textoCarga"
);

const barraCarga = document.getElementById(
    "barraCarga"
);

const distribucionTipos = document.getElementById(
    "distribucionTipos"
);

const tablaDistritos = document.getElementById(
    "tablaDistritos"
);


const nombresTipos = {
    "EM-01": "Emergencia médica",
    "EM-02": "Accidente de tránsito",
    "EM-03": "Incendio",
    "EM-04": "Seguridad ciudadana",
    "EM-05": "Rescate",
    "EM-06": "Inundación o deslizamiento"
};


let datosActuales = null;


function formatearNumero(valor) {
    return Number(valor).toLocaleString(
        "es-HN"
    );
}


function formatearFecha(fecha) {
    if (!fecha) {
        return "Sin información";
    }

    return new Date(fecha).toLocaleString(
        "es-HN"
    );
}


function aplicarEstado(elemento, estado) {
    elemento.className = "insignia";

    elemento.classList.add(estado);

    elemento.textContent = estado;
}


function mostrarCentral(central) {
    centralLlamadas.textContent = formatearNumero(
        central.llamadas_activas
    );

    centralUnidades.textContent = formatearNumero(
        central.unidades_disponibles
    );

    centralSaldo.textContent = formatearNumero(
        central.saldo_general
    );

    centralPorcentaje.textContent =
        `${formatearNumero(
            central.porcentaje_carga
        )} %`;

    centralSobrecargados.textContent =
        central.distritos_sobrecargados;

    centralExcedentes.textContent =
        central.llamadas_excedentes;

    fechaCalculo.textContent = formatearFecha(
        central.calculado_en
    );

    aplicarEstado(
        estadoCentral,
        central.estado_general
    );
}


function cargarSelector(distritos) {
    const valorAnterior = (
        selectorDistrito.value
    );

    selectorDistrito.innerHTML = "";

    for (const distrito of distritos) {
        const opcion = document.createElement(
            "option"
        );

        opcion.value = distrito.distrito_id;

        opcion.textContent =
            `${distrito.distrito_id} — `
            + distrito.distrito_nombre;

        selectorDistrito.appendChild(
            opcion
        );
    }

    const existeValorAnterior = distritos.some(
        distrito =>
            distrito.distrito_id
            === valorAnterior
    );

    if (existeValorAnterior) {
        selectorDistrito.value = valorAnterior;
    }
}


function mostrarDistribucion(distribucion) {
    distribucionTipos.innerHTML = "";

    const cantidades = Object.values(
        distribucion
    );

    const maximo = Math.max(
        ...cantidades,
        1
    );

    for (
        const [tipo, cantidad]
        of Object.entries(distribucion)
    ) {
        const fila = document.createElement(
            "div"
        );

        fila.className = "fila-tipo";

        const nombre = document.createElement(
            "span"
        );

        nombre.textContent =
            nombresTipos[tipo] || tipo;

        const fondo = document.createElement(
            "div"
        );

        fondo.className = "barra-tipo-fondo";

        const barra = document.createElement(
            "div"
        );

        barra.className = "barra-tipo";

        barra.style.width =
            `${(cantidad / maximo) * 100}%`;

        fondo.appendChild(barra);

        const total = document.createElement(
            "strong"
        );

        total.textContent = cantidad;

        fila.append(
            nombre,
            fondo,
            total
        );

        distribucionTipos.appendChild(
            fila
        );
    }
}


function mostrarDistrito(distrito) {
    if (!distrito) {
        return;
    }

    nombreDistrito.textContent =
        `${distrito.distrito_id} — `
        + distrito.distrito_nombre;

    llamadasActivas.textContent =
        distrito.llamadas_activas;

    unidadesDisponibles.textContent =
        distrito.unidades_disponibles;

    saldoUnidades.textContent =
        distrito.saldo_unidades;

    porcentajeCarga.textContent =
        `${distrito.porcentaje_carga} %`;

    textoCarga.textContent =
        `${distrito.porcentaje_carga} %`;

    aplicarEstado(
        estadoDistrito,
        distrito.estado_balance
    );

    barraCarga.className = "barra-progreso";

    barraCarga.classList.add(
        distrito.estado_balance
    );

    barraCarga.style.width =
        `${Math.min(
            distrito.porcentaje_carga,
            100
        )}%`;

    mostrarDistribucion(
        distrito.distribucion_tipos
    );

    mostrarTabla(
        datosActuales.distritos,
        distrito.distrito_id
    );
}


function mostrarTabla(
    distritos,
    distritoSeleccionado
) {
    tablaDistritos.innerHTML = "";

    for (const distrito of distritos) {
        const fila = document.createElement(
            "tr"
        );

        if (
            distrito.distrito_id
            === distritoSeleccionado
        ) {
            fila.classList.add(
                "fila-seleccionada"
            );
        }

        fila.innerHTML = `
            <td>
                ${distrito.distrito_id} —
                ${distrito.distrito_nombre}
            </td>

            <td>
                ${distrito.llamadas_activas}
            </td>

            <td>
                ${distrito.unidades_disponibles}
            </td>

            <td>
                ${distrito.saldo_unidades}
            </td>

            <td>
                ${distrito.porcentaje_carga} %
            </td>

            <td>
                <span class="insignia
                    ${distrito.estado_balance}">
                    ${distrito.estado_balance}
                </span>
            </td>
        `;

        fila.addEventListener(
            "click",
            () => {
                selectorDistrito.value =
                    distrito.distrito_id;

                mostrarDistrito(
                    distrito
                );
            }
        );

        tablaDistritos.appendChild(
            fila
        );
    }
}


async function cargarDatos() {
    botonActualizar.disabled = true;

    estadoServicio.className =
        "estado-servicio cargando";

    estadoServicio.textContent =
        "Actualizando balance...";

    try {
        const respuesta = await fetch(
            "/api/balances",
            {
                cache: "no-store"
            }
        );

        const contenido = await respuesta.json();

        if (!respuesta.ok) {
            throw contenido;
        }

        datosActuales = contenido;

        mostrarCentral(
            contenido.central
        );

        cargarSelector(
            contenido.distritos
        );

        const distritoSeleccionado =
            contenido.distritos.find(
                distrito =>
                    distrito.distrito_id
                    === selectorDistrito.value
            )
            || contenido.distritos[0];

        if (distritoSeleccionado) {
            selectorDistrito.value =
                distritoSeleccionado.distrito_id;

            mostrarDistrito(
                distritoSeleccionado
            );
        }

        estadoServicio.className =
            "estado-servicio activo";

        estadoServicio.textContent =
            "MongoDB conectado";

    } catch (error) {
        console.error(error);

        estadoServicio.className =
            "estado-servicio error";

        estadoServicio.textContent =
            "No se pudieron cargar los datos";

        tablaDistritos.innerHTML = `
            <tr>
                <td colspan="6">
                    No fue posible consultar MongoDB.
                </td>
            </tr>
        `;

    } finally {
        botonActualizar.disabled = false;
    }
}


selectorDistrito.addEventListener(
    "change",
    () => {
        if (!datosActuales) {
            return;
        }

        const distrito = (
            datosActuales.distritos.find(
                elemento =>
                    elemento.distrito_id
                    === selectorDistrito.value
            )
        );

        mostrarDistrito(distrito);
    }
);


botonActualizar.addEventListener(
    "click",
    cargarDatos
);


cargarDatos();


setInterval(
    cargarDatos,
    10000
);