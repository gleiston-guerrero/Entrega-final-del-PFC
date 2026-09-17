"""LÃƒÂ­nea base pandas funcionalmente equivalente al pipeline PySpark."""

from __future__ import annotations

import os
from uuid import UUID
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from snapshot import source_sql


TABLAS_RESERVAS = (
    "solicitudes_reserva",
    "reservas",
    "historial_solicitudes",
    "bloqueos_agenda",
    "configuraciones_reserva",
)

SALIDA_PREDETERMINADA = Path(__file__).resolve().parent / "out" / "reservas_procesadas.parquet"


@dataclass(frozen=True)
class PandasDbConfig:
    """ConfiguraciÃƒÂ³n SQL para consultar el mismo clÃƒÂºster usado por Spark."""

    url: str

    @classmethod
    def desde_entorno(cls) -> "PandasDbConfig":
        return cls(url=os.environ["RESERVAS_PANDAS_URL"])


def crear_motor(config: PandasDbConfig) -> Engine:
    """Crea el motor de lectura sin abrir conexiones anticipadamente."""

    url = make_url(config.url).set(
        drivername="cockroachdb+psycopg",
        username=os.environ["RESERVAS_DB_USERNAME"],
        password=os.environ["RESERVAS_DB_PASSWORD"],
    )
    return create_engine(
        url,
        isolation_level="AUTOCOMMIT",
        connect_args={"options": "-c timezone=UTC"},
    )


def cargar_fuentes(motor: Engine) -> dict[str, pd.DataFrame]:
    """Lee las tablas declaradas en db/schema.sql desde CockroachDB."""

    return {
        tabla: pd.read_sql_query(text(source_sql(tabla)), motor).map(
            lambda value: str(value) if isinstance(value, UUID) else value)
        for tabla in TABLAS_RESERVAS
    }


def filtrar_reservas_activas(reservas: pd.DataFrame) -> pd.DataFrame:
    """Conserva las reservas programadas o actualmente en curso."""

    estados_activos = ["PROGRAMADA", "EN_CURSO"]
    return reservas.loc[reservas["estado"].isin(estados_activos)].copy()


def unir_solicitudes_con_reservas(
    solicitudes: pd.DataFrame,
    reservas: pd.DataFrame,
) -> pd.DataFrame:
    """Relaciona cada reserva activa con su solicitud de origen."""

    reservas_base = reservas.rename(columns={"id": "reserva_id"})
    solicitudes_base = solicitudes.rename(columns={"id": "solicitud_id"})
    datos = reservas_base.merge(
        solicitudes_base,
        on="solicitud_id",
        how="inner",
        suffixes=("_reserva", "_solicitud"),
        validate="one_to_one",
    )

    return datos.loc[
        :,
        [
            "reserva_id",
            "solicitud_id",
            "laboratorio_id_reserva",
            "responsable_id",
            "fecha_reserva_reserva",
            "hora_inicio_reserva",
            "hora_fin_reserva",
            "estado_reserva",
            "codigo_reserva",
            "solicitante_id",
            "docente_id",
            "materia_id",
            "periodo_lectivo_id",
            "numero_participantes",
            "creada_en_solicitud",
        ],
    ].rename(
        columns={
            "laboratorio_id_reserva": "laboratorio_id",
            "fecha_reserva_reserva": "fecha_reserva",
            "hora_inicio_reserva": "hora_inicio",
            "hora_fin_reserva": "hora_fin",
            "creada_en_solicitud": "solicitud_creada_en",
        }
    )


def agregar_dimensiones_temporales(datos: pd.DataFrame) -> pd.DataFrame:
    """Normaliza la fecha y deriva aÃƒÂ±o, trimestre y primer dÃƒÂ­a del mes."""

    resultado = datos.copy()
    resultado["fecha_reserva"] = pd.to_datetime(resultado["fecha_reserva"])
    resultado["anio_reserva"] = resultado["fecha_reserva"].dt.year
    resultado["trimestre_reserva"] = resultado["fecha_reserva"].dt.quarter
    resultado["mes_reserva"] = (
        resultado["fecha_reserva"].dt.to_period("M").dt.to_timestamp()
    )
    return resultado


def agregar_participantes_por_periodo(datos: pd.DataFrame) -> pd.DataFrame:
    """Replica la suma Window mediante groupby(...).transform('sum')."""

    resultado = datos.copy()
    grupos = ["laboratorio_id", "anio_reserva", "trimestre_reserva"]
    resultado["participantes_laboratorio_trimestre"] = (
        resultado.groupby(grupos, dropna=False)["numero_participantes"]
        .transform("sum")
    )
    return resultado


def categorizar_numero_participantes(datos: pd.DataFrame) -> pd.DataFrame:
    """Aplica los mismos intervalos numÃƒÂ©ricos definidos por Bucketizer."""

    resultado = datos.copy()
    resultado["segmento_participantes"] = pd.cut(
        resultado["numero_participantes"],
        bins=[float("-inf"), 10.0, 20.0, 30.0, float("inf")],
        labels=False,
        right=False,
        include_lowest=True,
    ).astype("float64")
    return resultado


def construir_pipeline(fuentes: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Compone la lÃƒÂ­nea base con el mismo orden que pipeline.py."""

    reservas_activas = filtrar_reservas_activas(fuentes["reservas"])
    datos = unir_solicitudes_con_reservas(
        fuentes["solicitudes_reserva"],
        reservas_activas,
    )
    datos = agregar_dimensiones_temporales(datos)
    datos = agregar_participantes_por_periodo(datos)
    return categorizar_numero_participantes(datos)


def exportar_parquet(
    datos: pd.DataFrame,
    destino: Path = SALIDA_PREDETERMINADA,
    overwrite: bool = False,
) -> Path:
    """Escribe el resultado en spark/out sin incluir el ÃƒÂ­ndice de pandas."""

    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("wb" if overwrite else "xb") as output:
        datos.to_parquet(output, index=False)
    return destino


def ejecutar_baseline() -> Path:
    """Lee, transforma y exporta el resultado de la lÃƒÂ­nea base."""

    motor = crear_motor(PandasDbConfig.desde_entorno())
    try:
        fuentes = cargar_fuentes(motor)
        resultado = construir_pipeline(fuentes)
        return exportar_parquet(resultado)
    finally:
        motor.dispose()


if __name__ == "__main__":
    ejecutar_baseline()
