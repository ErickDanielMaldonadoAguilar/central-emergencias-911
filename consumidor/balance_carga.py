import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import ASCENDING, MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from consumidor.configuracion_mongodb import (
    MONGO_COLLECTION_EVENTOS,
    MONGO_DATABASE,
    MONGO_URI,
)
from generador.app.models.evento import (
    DistritoId,
    EstadoLlamada,
    TipoEmergencia,
)


MONGO_COLLECTION_BALANCES = os.getenv(
    "MONGO_COLLECTION_BALANCES",
    "balances_distrito",
)

BALANCE_VENTANA_MINUTOS = int(
    os.getenv(
        "BALANCE_VENTANA_MINUTOS",
        "60",
    )
)


NOMBRES_DISTRITOS: dict[DistritoId, str] = {
    DistritoId.CENTRO: "Centro",
    DistritoId.NORTE: "Norte",
    DistritoId.SUR: "Sur",
    DistritoId.ESTE: "Este",
    DistritoId.OESTE: "Oeste",
    DistritoId.COMAYAGUELA: "Comayagüela",
}


# Cantidades simuladas para fines académicos.
UNIDADES_DISPONIBLES_POR_DISTRITO: dict[
    DistritoId,
    int,
] = {
    DistritoId.CENTRO: 21,
    DistritoId.NORTE: 17,
    DistritoId.SUR: 16,
    DistritoId.ESTE: 14,
    DistritoId.OESTE: 12,
    DistritoId.COMAYAGUELA: 20,
}


class ErrorBalanceCarga(RuntimeError):
    """Indica que no fue posible calcular el balance."""


@dataclass(frozen=True)
class BalanceDistrito:
    """Resultado del balance de carga de un distrito."""

    distrito_id: str
    distrito_nombre: str
    llamadas_activas: int
    unidades_disponibles: int
    saldo_unidades: int
    porcentaje_carga: float
    estado_balance: str
    distribucion_tipos: dict[str, int]
    ventana_minutos: int
    fecha_desde: datetime
    calculado_en: datetime


class ServicioBalanceCargaMongoDB:
    """Calcula y guarda el balance utilizando MongoDB."""

    def __init__(self) -> None:
        self._cliente = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
        )

        base_datos = self._cliente[
            MONGO_DATABASE
        ]

        self._eventos: Collection[
            dict[str, Any]
        ] = base_datos[
            MONGO_COLLECTION_EVENTOS
        ]

        self._balances: Collection[
            dict[str, Any]
        ] = base_datos[
            MONGO_COLLECTION_BALANCES
        ]

    def comprobar_conexion(self) -> bool:
        """Comprueba que MongoDB esté disponible."""

        try:
            respuesta = self._cliente.admin.command(
                "ping"
            )
        except PyMongoError as error:
            raise ErrorBalanceCarga(
                "No fue posible conectar con MongoDB: "
                f"{error}"
            ) from error

        return respuesta.get("ok") == 1.0

    def preparar_indices(self) -> None:
        """Crea los índices de la colección de balances."""

        try:
            self._balances.create_index(
                [
                    (
                        "distrito_id",
                        ASCENDING,
                    )
                ],
                unique=True,
                name="uq_balance_distrito",
            )

            self._balances.create_index(
                [
                    (
                        "calculado_en",
                        ASCENDING,
                    )
                ],
                name="idx_balance_calculado_en",
            )
        except PyMongoError as error:
            raise ErrorBalanceCarga(
                "No fue posible crear los índices "
                f"del balance: {error}"
            ) from error

    @staticmethod
    def _clasificar_estado(
        saldo_unidades: int,
    ) -> str:
        """Clasifica el estado según la capacidad restante."""

        if saldo_unidades > 0:
            return "disponible"

        if saldo_unidades == 0:
            return "saturado"

        return "sobrecargado"

    def calcular_balances(
        self,
    ) -> list[BalanceDistrito]:
        """Agrega llamadas activas por distrito y tipo."""

        calculado_en = datetime.now(
            timezone.utc
        )

        fecha_desde = calculado_en - timedelta(
            minutes=BALANCE_VENTANA_MINUTOS
        )

        estados_activos = [
            EstadoLlamada.REPORTADA.value,
            EstadoLlamada.EN_ATENCION.value,
        ]

        pipeline = [
            {
                "$match": {
                    "estado": {
                        "$in": estados_activos,
                    },
                    "fecha_hora_evento": {
                        "$gte": fecha_desde,
                    },
                }
            },
            {
                "$group": {
                    "_id": {
                        "distrito_id": "$distrito_id",
                        "tipo_emergencia": (
                            "$tipo_emergencia"
                        ),
                    },
                    "cantidad": {
                        "$sum": 1,
                    },
                }
            },
        ]

        try:
            resultados_agregados = list(
                self._eventos.aggregate(
                    pipeline
                )
            )
        except PyMongoError as error:
            raise ErrorBalanceCarga(
                "No fue posible agregar los eventos: "
                f"{error}"
            ) from error

        cantidades: dict[
            str,
            dict[str, int],
        ] = {}

        for resultado in resultados_agregados:
            identificador = resultado["_id"]

            distrito_id = identificador[
                "distrito_id"
            ]

            tipo_emergencia = identificador[
                "tipo_emergencia"
            ]

            cantidades.setdefault(
                distrito_id,
                {},
            )

            cantidades[distrito_id][
                tipo_emergencia
            ] = resultado["cantidad"]

        balances: list[BalanceDistrito] = []

        for distrito in DistritoId:
            distribucion_tipos = {
                tipo.value: cantidades.get(
                    distrito.value,
                    {},
                ).get(
                    tipo.value,
                    0,
                )
                for tipo in TipoEmergencia
            }

            llamadas_activas = sum(
                distribucion_tipos.values()
            )

            unidades_disponibles = (
                UNIDADES_DISPONIBLES_POR_DISTRITO[
                    distrito
                ]
            )

            saldo_unidades = (
                unidades_disponibles
                - llamadas_activas
            )

            porcentaje_carga = round(
                (
                    llamadas_activas
                    / unidades_disponibles
                )
                * 100,
                2,
            )

            balance = BalanceDistrito(
                distrito_id=distrito.value,
                distrito_nombre=(
                    NOMBRES_DISTRITOS[
                        distrito
                    ]
                ),
                llamadas_activas=(
                    llamadas_activas
                ),
                unidades_disponibles=(
                    unidades_disponibles
                ),
                saldo_unidades=saldo_unidades,
                porcentaje_carga=(
                    porcentaje_carga
                ),
                estado_balance=(
                    self._clasificar_estado(
                        saldo_unidades
                    )
                ),
                distribucion_tipos=(
                    distribucion_tipos
                ),
                ventana_minutos=(
                    BALANCE_VENTANA_MINUTOS
                ),
                fecha_desde=fecha_desde,
                calculado_en=calculado_en,
            )

            balances.append(balance)

        return balances

    def guardar_balances(
        self,
        balances: list[BalanceDistrito],
    ) -> None:
        """Guarda o actualiza un balance por distrito."""

        operaciones = [
            UpdateOne(
                {
                    "distrito_id":
                        balance.distrito_id,
                },
                {
                    "$set": asdict(balance),
                },
                upsert=True,
            )
            for balance in balances
        ]

        if not operaciones:
            return

        try:
            self._balances.bulk_write(
                operaciones,
                ordered=False,
            )
        except PyMongoError as error:
            raise ErrorBalanceCarga(
                "No fue posible guardar los balances: "
                f"{error}"
            ) from error

    def calcular_y_guardar(
        self,
    ) -> list[BalanceDistrito]:
        """Calcula los seis balances y los guarda."""

        balances = self.calcular_balances()

        self.guardar_balances(
            balances
        )

        return balances

    def cerrar(self) -> None:
        """Cierra la conexión con MongoDB."""

        self._cliente.close()