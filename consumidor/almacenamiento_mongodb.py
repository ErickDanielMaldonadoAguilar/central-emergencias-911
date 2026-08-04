from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import (
    DuplicateKeyError,
    PyMongoError,
)

from consumidor.configuracion_mongodb import (
    MONGO_COLLECTION_EVENTOS,
    MONGO_DATABASE,
    MONGO_URI,
)
from generador.app.models.evento import (
    EventoEmergencia,
)


class ErrorAlmacenamientoMongoDB(RuntimeError):
    """Indica que no se pudo trabajar con MongoDB."""


@dataclass(frozen=True)
class ResultadoGuardadoEvento:
    """Resultado de intentar guardar un evento."""

    evento_id: str
    insertado: bool
    duplicado: bool
    documento_id: str | None


class AlmacenamientoEventosMongoDB:
    """Administra los eventos de emergencia en MongoDB."""

    def __init__(self) -> None:
        self._cliente = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
        )

        self._base_datos = self._cliente[
            MONGO_DATABASE
        ]

        self._coleccion: Collection[
            dict[str, Any]
        ] = self._base_datos[
            MONGO_COLLECTION_EVENTOS
        ]

    def comprobar_conexion(self) -> bool:
        """Comprueba que MongoDB responda correctamente."""

        try:
            respuesta = self._cliente.admin.command(
                "ping"
            )
        except PyMongoError as error:
            raise ErrorAlmacenamientoMongoDB(
                "No fue posible conectar con MongoDB: "
                f"{error}"
            ) from error

        return respuesta.get("ok") == 1.0

    def preparar_indices(self) -> None:
        """Crea los índices necesarios para los eventos."""

        try:
            self._coleccion.create_index(
                [
                    (
                        "evento_id",
                        ASCENDING,
                    )
                ],
                unique=True,
                name="uq_evento_id",
            )

            self._coleccion.create_index(
                [
                    (
                        "lote_id",
                        ASCENDING,
                    )
                ],
                name="idx_lote_id",
            )
        except PyMongoError as error:
            raise ErrorAlmacenamientoMongoDB(
                "No fue posible crear los índices: "
                f"{error}"
            ) from error

    @staticmethod
    def _convertir_documento(
        evento: EventoEmergencia,
        topic: str | None,
        particion: int | None,
        offset: int | None,
    ) -> dict[str, Any]:
        """Convierte un evento a un documento de MongoDB."""

        documento = evento.model_dump(
            mode="json"
        )

        documento["fecha_hora_evento"] = (
            evento.fecha_hora_evento
        )

        documento["fecha_ingesta"] = datetime.now(
            timezone.utc
        )

        documento["kafka"] = {
            "topic": topic,
            "particion": particion,
            "offset": offset,
        }

        return documento

    def guardar_evento(
        self,
        evento: EventoEmergencia,
        topic: str | None = None,
        particion: int | None = None,
        offset: int | None = None,
    ) -> ResultadoGuardadoEvento:
        """Guarda un evento o identifica que ya existía."""

        evento_id = str(
            evento.evento_id
        )

        documento = self._convertir_documento(
            evento=evento,
            topic=topic,
            particion=particion,
            offset=offset,
        )

        try:
            resultado = self._coleccion.insert_one(
                documento
            )
        except DuplicateKeyError:
            documento_existente = (
                self._coleccion.find_one(
                    {
                        "evento_id": evento_id,
                    },
                    {
                        "_id": 1,
                    },
                )
            )

            documento_id = None

            if documento_existente is not None:
                documento_id = str(
                    documento_existente["_id"]
                )

            return ResultadoGuardadoEvento(
                evento_id=evento_id,
                insertado=False,
                duplicado=True,
                documento_id=documento_id,
            )
        except PyMongoError as error:
            raise ErrorAlmacenamientoMongoDB(
                "No fue posible guardar el evento: "
                f"{error}"
            ) from error

        return ResultadoGuardadoEvento(
            evento_id=evento_id,
            insertado=True,
            duplicado=False,
            documento_id=str(
                resultado.inserted_id
            ),
        )

    def contar_evento(
        self,
        evento_id: str,
    ) -> int:
        """Cuenta cuántas veces existe un evento."""

        try:
            return self._coleccion.count_documents(
                {
                    "evento_id": evento_id,
                }
            )
        except PyMongoError as error:
            raise ErrorAlmacenamientoMongoDB(
                "No fue posible contar el evento: "
                f"{error}"
            ) from error

    def cerrar(self) -> None:
        """Cierra la conexión con MongoDB."""

        self._cliente.close()