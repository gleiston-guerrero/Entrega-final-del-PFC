"""Pipeline Spark para preparar el anÃ¡lisis del dominio de reservas.

El mÃ³dulo obtiene las fuentes desde CockroachDB por JDBC y construye las
transformaciones del Paso 4. La ejecuciÃ³n escribe todas las columnas en Parquet.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from snapshot import source_sql

from pyspark.ml.feature import Bucketizer
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


TABLAS_RESERVAS = (
    "solicitudes_reserva",
    "reservas",
    "historial_solicitudes",
    "bloqueos_agenda",
    "configuraciones_reserva",
)


@dataclass(frozen=True)
class JdbcConfig:
    """ParÃ¡metros de conexiÃ³n al esquema de reservas en CockroachDB E3."""

    url: str
    usuario: str
    password: str
    driver: str = "org.postgresql.Driver"

    @classmethod
    def desde_entorno(cls) -> "JdbcConfig":
        return cls(
            url=os.environ["RESERVAS_JDBC_URL"],
            usuario=os.environ["RESERVAS_DB_USERNAME"],
            password=os.environ["RESERVAS_DB_PASSWORD"],
        )

    def propiedades(self) -> dict[str, str]:
        return {
            "user": self.usuario,
            "password": self.password,
            "driver": self.driver,
            "options": "-c timezone=UTC",
        }


def crear_sesion(paralelismo: int | None = None) -> SparkSession:
    """Crea la sesiÃ³n sin ejecutar lecturas ni transformaciones."""

    builder = SparkSession.builder.appName("scli-reservas-pipeline")
    if paralelismo is not None:
        if paralelismo < 1:
            raise ValueError("El paralelismo debe ser positivo")
        builder = (builder.master(f"local[{paralelismo}]")
                   .config("spark.default.parallelism", paralelismo)
                   .config("spark.sql.shuffle.partitions", paralelismo)
                   .config("spark.sql.adaptive.enabled", "false"))
    builder = (builder.config("spark.sql.session.timeZone", "UTC")
               .config("spark.driver.extraJavaOptions", "-Duser.timezone=UTC"))
    jdbc_jar = os.getenv("POSTGRES_JDBC_JAR")
    if jdbc_jar:
        jdbc_path = str(Path(jdbc_jar).resolve())
        builder = (
            builder
            .config("spark.driver.extraClassPath", jdbc_path)
            .config("spark.executor.extraClassPath", jdbc_path)
        )
    return builder.getOrCreate()


def cargar_fuentes(
    spark: SparkSession,
    jdbc: JdbcConfig,
) -> dict[str, DataFrame]:
    """Registra las tablas fuente definidas en db/schema.sql mediante JDBC."""

    return {
        tabla: spark.read.jdbc(
            url=jdbc.url,
            table=source_sql(tabla).removeprefix("SELECT * FROM "),
            properties=jdbc.propiedades(),
        )
        for tabla in TABLAS_RESERVAS
    }


def filtrar_reservas_activas(reservas: DataFrame) -> DataFrame:
    """Conserva reservas que aÃºn participan en la operaciÃ³n del laboratorio."""

    return reservas.filter(F.col("estado").isin("PROGRAMADA", "EN_CURSO"))


def unir_solicitudes_con_reservas(
    solicitudes: DataFrame,
    reservas: DataFrame,
) -> DataFrame:
    """Relaciona cada reserva activa con los datos de su solicitud de origen."""

    solicitud = solicitudes.alias("solicitud")
    reserva = reservas.alias("reserva")

    return solicitud.join(
        reserva,
        F.col("solicitud.id") == F.col("reserva.solicitud_id"),
        "inner",
    ).select(
        F.col("reserva.id").alias("reserva_id"),
        F.col("reserva.solicitud_id"),
        F.col("reserva.laboratorio_id"),
        F.col("reserva.responsable_id"),
        F.col("reserva.fecha_reserva"),
        F.col("reserva.hora_inicio"),
        F.col("reserva.hora_fin"),
        F.col("reserva.estado").alias("estado_reserva"),
        F.col("reserva.codigo_reserva"),
        F.col("solicitud.solicitante_id"),
        F.col("solicitud.docente_id"),
        F.col("solicitud.materia_id"),
        F.col("solicitud.periodo_lectivo_id"),
        F.col("solicitud.numero_participantes"),
        F.col("solicitud.creada_en").alias("solicitud_creada_en"),
    )


def agregar_dimensiones_temporales(datos: DataFrame) -> DataFrame:
    """Normaliza la fecha y deriva dimensiones de calendario para el anÃ¡lisis."""

    fecha = F.to_date(F.col("fecha_reserva"))
    return (
        datos.withColumn("fecha_reserva", fecha)
        .withColumn("anio_reserva", F.year(fecha))
        .withColumn("trimestre_reserva", F.quarter(fecha))
        .withColumn("mes_reserva", F.date_trunc("month", fecha))
    )


def agregar_participantes_por_periodo(datos: DataFrame) -> DataFrame:
    """Suma participantes por laboratorio, aÃ±o y trimestre usando Window."""

    periodo = Window.partitionBy(
        "laboratorio_id",
        "anio_reserva",
        "trimestre_reserva",
    )
    return datos.withColumn(
        "participantes_laboratorio_trimestre",
        F.sum("numero_participantes").over(periodo),
    )


def categorizar_numero_participantes(datos: DataFrame) -> DataFrame:
    """Agrupa el tamaÃ±o de la reserva en intervalos numÃ©ricos con Spark ML."""

    bucketizer = Bucketizer(
        splits=[float("-inf"), 10.0, 20.0, 30.0, float("inf")],
        inputCol="numero_participantes",
        outputCol="segmento_participantes",
        handleInvalid="keep",
    )
    return bucketizer.transform(datos)


def construir_pipeline(fuentes: dict[str, DataFrame]) -> DataFrame:
    """Compone las transformaciones sin provocar evaluaciÃ³n ni escritura."""

    reservas_activas = filtrar_reservas_activas(fuentes["reservas"])
    datos = unir_solicitudes_con_reservas(
        fuentes["solicitudes_reserva"],
        reservas_activas,
    )
    datos = agregar_dimensiones_temporales(datos)
    datos = agregar_participantes_por_periodo(datos)
    return categorizar_numero_participantes(datos)


def exportar_parquet(datos: DataFrame, destino: str, overwrite: bool = False) -> None:
    """AcciÃ³n terminal: evalÃºa todas las transformaciones y escribe Parquet."""

    datos.write.mode("overwrite" if overwrite else "errorifexists").parquet(destino)


def ejecutar_pipeline(destino: str, paralelismo: int | None = None,
                      overwrite: bool = False) -> None:
    """Lee, transforma y materializa; rechaza destinos existentes por defecto."""

    spark = crear_sesion(paralelismo)
    try:
        jdbc = JdbcConfig.desde_entorno()
        fuentes = cargar_fuentes(spark, jdbc)
        exportar_parquet(construir_pipeline(fuentes), destino, overwrite)
    finally:
        spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--parallelism", type=int)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    ejecutar_pipeline(args.output, args.parallelism, args.overwrite)
