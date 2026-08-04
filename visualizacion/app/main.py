from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from consumidor.balance_carga import (
    ErrorBalanceCarga,
    ServicioBalanceCargaMongoDB,
)


DIRECTORIO_APP = Path(__file__).resolve().parent
DIRECTORIO_STATIC = DIRECTORIO_APP / "static"


app = FastAPI(
    title="Central de Emergencias 911 - Visualización",
    description=(
        "Dashboard para consultar el balance de carga "
        "de la central y de cada distrito simulado."
    ),
    version="0.1.0",
)


app.mount(
    "/static",
    StaticFiles(directory=DIRECTORIO_STATIC),
    name="static",
)


def _clasificar_estado_general(
    saldo_general: int,
) -> str:
    """Clasifica la capacidad general de la central."""

    if saldo_general > 0:
        return "disponible"

    if saldo_general == 0:
        return "saturado"

    return "sobrecargado"


def _obtener_datos_balance() -> dict[str, Any]:
    """Calcula los balances y crea el resumen general."""

    servicio = ServicioBalanceCargaMongoDB()

    try:
        if not servicio.comprobar_conexion():
            raise ErrorBalanceCarga(
                "MongoDB no respondió correctamente."
            )

        servicio.preparar_indices()

        balances = servicio.calcular_y_guardar()

    except ErrorBalanceCarga as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(error),
        ) from error

    finally:
        servicio.cerrar()

    total_llamadas = sum(
        balance.llamadas_activas
        for balance in balances
    )

    total_unidades = sum(
        balance.unidades_disponibles
        for balance in balances
    )

    saldo_general = (
        total_unidades
        - total_llamadas
    )

    porcentaje_carga = 0.0

    if total_unidades > 0:
        porcentaje_carga = round(
            (
                total_llamadas
                / total_unidades
            )
            * 100,
            2,
        )

    distritos_sobrecargados = sum(
        1
        for balance in balances
        if balance.estado_balance
        == "sobrecargado"
    )

    distritos_saturados = sum(
        1
        for balance in balances
        if balance.estado_balance
        == "saturado"
    )

    llamadas_excedentes = sum(
        abs(balance.saldo_unidades)
        for balance in balances
        if balance.saldo_unidades < 0
    )

    capacidad_libre = sum(
        balance.saldo_unidades
        for balance in balances
        if balance.saldo_unidades > 0
    )

    fecha_calculo = None
    ventana_minutos = 60

    if balances:
        fecha_calculo = (
            balances[0].calculado_en
        )

        ventana_minutos = (
            balances[0].ventana_minutos
        )

    respuesta = {
        "central": {
            "llamadas_activas": total_llamadas,
            "unidades_disponibles": total_unidades,
            "saldo_general": saldo_general,
            "porcentaje_carga": porcentaje_carga,
            "estado_general": (
                _clasificar_estado_general(
                    saldo_general
                )
            ),
            "distritos_sobrecargados": (
                distritos_sobrecargados
            ),
            "distritos_saturados": (
                distritos_saturados
            ),
            "llamadas_excedentes": (
                llamadas_excedentes
            ),
            "capacidad_libre": capacidad_libre,
            "ventana_minutos": ventana_minutos,
            "calculado_en": fecha_calculo,
        },
        "distritos": [
            asdict(balance)
            for balance in balances
        ],
    }

    return jsonable_encoder(
        respuesta
    )


@app.get(
    "/",
    response_class=FileResponse,
    include_in_schema=False,
)
def mostrar_dashboard() -> FileResponse:
    """Muestra la interfaz visual del balance."""

    return FileResponse(
        DIRECTORIO_STATIC / "index.html"
    )


@app.get("/health", tags=["Estado"])
def verificar_salud() -> dict[str, str]:
    """Comprueba la conexión de la visualización."""

    servicio = ServicioBalanceCargaMongoDB()

    try:
        conexion_correcta = (
            servicio.comprobar_conexion()
        )

    except ErrorBalanceCarga as error:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail=str(error),
        ) from error

    finally:
        servicio.cerrar()

    if not conexion_correcta:
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
            ),
            detail="MongoDB no está disponible.",
        )

    return {
        "status": "ok",
        "servicio": "visualizacion-balance",
    }


@app.get("/api/balances", tags=["Balance"])
def consultar_todos_los_balances() -> dict[str, Any]:
    """Devuelve el balance general y los seis distritos."""

    return _obtener_datos_balance()


@app.get(
    "/api/balances/{distrito_id}",
    tags=["Balance"],
)
def consultar_balance_distrito(
    distrito_id: str,
) -> dict[str, Any]:
    """Devuelve el balance de un distrito específico."""

    datos = _obtener_datos_balance()

    distrito_buscado = distrito_id.upper()

    distrito = next(
        (
            balance
            for balance in datos["distritos"]
            if balance["distrito_id"]
            == distrito_buscado
        ),
        None,
    )

    if distrito is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No existe el distrito "
                f"{distrito_buscado}."
            ),
        )

    return {
        "central": datos["central"],
        "distrito": distrito,
    }