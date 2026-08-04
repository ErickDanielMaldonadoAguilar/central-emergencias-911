import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import dotenv_values


DIRECTORIO_PROYECTO = Path(__file__).resolve().parents[1]

ARCHIVO_ENV_INFRAESTRUCTURA = (
    DIRECTORIO_PROYECTO
    / "infraestructura"
    / ".env"
)


def _leer_configuracion_local() -> dict[str, str | None]:
    """Lee las variables locales de infraestructura si existen."""

    if not ARCHIVO_ENV_INFRAESTRUCTURA.exists():
        return {}

    return dict(
        dotenv_values(
            ARCHIVO_ENV_INFRAESTRUCTURA
        )
    )


CONFIGURACION_LOCAL = _leer_configuracion_local()


def _obtener_variable(
    nombre: str,
    valor_predeterminado: str | None = None,
) -> str:
    """Obtiene una variable del sistema o del archivo local."""

    valor = (
        os.getenv(nombre)
        or CONFIGURACION_LOCAL.get(nombre)
        or valor_predeterminado
    )

    if valor is None or str(valor).strip() == "":
        raise RuntimeError(
            f"No se encontró la configuración {nombre}."
        )

    return str(valor)


MONGO_USUARIO = _obtener_variable(
    "MONGO_ROOT_USERNAME"
)

MONGO_CONTRASENA = _obtener_variable(
    "MONGO_ROOT_PASSWORD"
)

MONGO_DATABASE = _obtener_variable(
    "MONGO_DATABASE",
    "central911",
)

MONGO_HOST = _obtener_variable(
    "MONGO_HOST",
    "localhost",
)

MONGO_PORT = int(
    _obtener_variable(
        "MONGO_PORT",
        "27017",
    )
)

MONGO_COLLECTION_EVENTOS = _obtener_variable(
    "MONGO_COLLECTION_EVENTOS",
    "eventos",
)


MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    usuario_codificado = quote_plus(
        MONGO_USUARIO
    )

    contrasena_codificada = quote_plus(
        MONGO_CONTRASENA
    )

    MONGO_URI = (
        f"mongodb://{usuario_codificado}:"
        f"{contrasena_codificada}"
        f"@{MONGO_HOST}:{MONGO_PORT}/"
        f"?authSource=admin"
    )