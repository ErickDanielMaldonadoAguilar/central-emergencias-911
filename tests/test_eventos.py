from fastapi.testclient import TestClient

from generador.app.main import app


client = TestClient(app)


def test_servicio_generador_esta_disponible() -> None:
    """Comprueba que el endpoint de salud responda correctamente."""

    respuesta = client.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "status": "ok",
        "servicio": "generador-emergencias",
    }


def test_generar_evento_individual_valido() -> None:
    """Comprueba la creación de una llamada individual válida."""

    solicitud = {
        "distrito_id": "D-01",
        "tipo_emergencia": "EM-02",
        "prioridad": "alta",
        "ubicacion": {
            "sector": "Bulevar Suyapa",
        },
    }

    respuesta = client.post(
        "/eventos/individual",
        json=solicitud,
    )

    assert respuesta.status_code == 201

    evento = respuesta.json()

    assert evento["distrito_id"] == "D-01"
    assert evento["tipo_emergencia"] == "EM-02"
    assert evento["prioridad"] == "alta"
    assert evento["ubicacion"] == {
        "sector": "Bulevar Suyapa",
    }
    assert evento["estado"] == "reportada"
    assert evento["modo_generacion"] == "individual"
    assert evento["lote_id"] is None
    assert evento["escenario"] == "normal"
    assert evento["version_esquema"] == "1.0"

    assert evento["evento_id"]
    assert evento["numero_reporte"].startswith("EMG-")
    assert evento["fecha_hora_evento"]


def test_rechazar_evento_individual_invalido() -> None:
    """Comprueba que la API rechace valores no permitidos."""

    solicitud_invalida = {
        "distrito_id": "D-20",
        "tipo_emergencia": "EM-02",
        "prioridad": "urgente",
        "ubicacion": {
            "sector": "X",
            "latitud": 14.081,
            "longitud": -87.176,
        },
    }

    respuesta = client.post(
        "/eventos/individual",
        json=solicitud_invalida,
    )

    assert respuesta.status_code == 422

    errores = respuesta.json()["detail"]

    ubicaciones_errores = {
        tuple(error["loc"])
        for error in errores
    }

    assert (
        "body",
        "distrito_id",
    ) in ubicaciones_errores

    assert (
        "body",
        "prioridad",
    ) in ubicaciones_errores

    assert (
        "body",
        "ubicacion",
        "sector",
    ) in ubicaciones_errores

    assert (
        "body",
        "ubicacion",
        "latitud",
    ) in ubicaciones_errores

    assert (
        "body",
        "ubicacion",
        "longitud",
    ) in ubicaciones_errores


def test_generar_lote_de_mil_eventos() -> None:
    """Comprueba la generación masiva y sus totales."""

    solicitud = {
        "cantidad": 1000,
        "semilla": 911,
        "escenario": "normal",
    }

    respuesta = client.post(
        "/eventos/lote",
        json=solicitud,
    )

    assert respuesta.status_code == 201

    resultado = respuesta.json()

    assert resultado["cantidad_solicitada"] == 1000
    assert resultado["cantidad_generada"] == 1000
    assert resultado["duracion_ms"] > 0
    assert resultado["eventos_por_segundo"] > 0

    assert sum(
        resultado["distribucion_distritos"].values()
    ) == 1000

    assert sum(
        resultado["distribucion_tipos"].values()
    ) == 1000

    assert sum(
        resultado["distribucion_prioridades"].values()
    ) == 1000

    muestra = resultado["muestra"]

    assert len(muestra) == 5

    lote_id = resultado["lote_id"]

    for evento in muestra:
        assert evento["modo_generacion"] == "lote"
        assert evento["lote_id"] == lote_id
        assert evento["escenario"] == "normal"
        assert evento["estado"] == "reportada"

        assert set(evento["ubicacion"].keys()) == {
            "sector",
        }


def test_semilla_repite_las_distribuciones() -> None:
    """Comprueba que una semilla produzca resultados repetibles."""

    solicitud = {
        "cantidad": 1000,
        "semilla": 911,
        "escenario": "normal",
    }

    primera_respuesta = client.post(
        "/eventos/lote",
        json=solicitud,
    )

    segunda_respuesta = client.post(
        "/eventos/lote",
        json=solicitud,
    )

    assert primera_respuesta.status_code == 201
    assert segunda_respuesta.status_code == 201

    primer_resultado = primera_respuesta.json()
    segundo_resultado = segunda_respuesta.json()

    assert (
        primer_resultado["distribucion_distritos"]
        == segundo_resultado["distribucion_distritos"]
    )

    assert (
        primer_resultado["distribucion_tipos"]
        == segundo_resultado["distribucion_tipos"]
    )

    assert (
        primer_resultado["distribucion_prioridades"]
        == segundo_resultado["distribucion_prioridades"]
    )

    assert (
        primer_resultado["lote_id"]
        != segundo_resultado["lote_id"]
    )


def test_rechazar_cantidad_mayor_al_limite() -> None:
    """Comprueba el límite máximo de diez mil eventos."""

    solicitud = {
        "cantidad": 10001,
        "semilla": 911,
        "escenario": "normal",
    }

    respuesta = client.post(
        "/eventos/lote",
        json=solicitud,
    )

    assert respuesta.status_code == 422