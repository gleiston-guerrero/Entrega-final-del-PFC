# Protocolo experimental de procesamiento distribuido

## Objetivo

Comparar la línea base implementada con pandas y el
pipeline distribuido implementado con PySpark. La comparación deberá utilizar
los mismos datos de entrada, transformaciones y resultado lógico.

Este documento define el protocolo y la estructura de registro. El protocolo
1.1 fue ejecutado para la corrección #17; sus resultados están versionados en
`experimentos/evidencia-17/20260916/`.
Los comandos del protocolo 1.1 están en [spark/README.md](../spark/README.md).
Se reutiliza `run_comparison.py`: cinco grados Spark (1,2,4,6,8), cinco
repeticiones medidas y un warmup por tratamiento/grado. Ambos motores escriben
Parquet; el tiempo incluye el proceso completo y su cierre. Cada lote se guarda
en un directorio UUID nuevo, con configuración, procedencia y registros crudos.

## Tratamientos

- `pandas-baseline`: ejecución de `spark/baseline.py`.
- `pyspark-pipeline`: ejecución de `spark/pipeline.py`.

Ambos tratamientos deben leer el mismo estado consistente de `reservas_db` y
aplicar el filtro, join, transformación temporal, agregación y clasificación
definidos en el Paso 4.

## Variables

### Variable independiente

Motor de procesamiento y grado de paralelismo local de PySpark.

### Variables dependientes

- tiempo total de ejecución, en milisegundos;
- utilización media y máxima de CPU, en porcentaje;
- memoria residente media y máxima, en MiB;
- filas procesadas;
- rendimiento, expresado en filas procesadas por segundo.

### Variables controladas

- versión y configuración del conjunto de datos;
- consulta y estado de CockroachDB antes de cada tratamiento;
- equipo, sistema operativo y recursos disponibles;
- versiones de Python, pandas, Java y Spark;
- configuración de Spark;
- número de repeticiones y calentamientos;
- procesos externos activos durante la medición.

## Diseño

1. Preparar una instantánea identificable del conjunto de datos.
2. Registrar el entorno y las versiones utilizadas.
3. Ejecutar las iteraciones de calentamiento y conservarlas con `warmup=true`,
   excluyéndolas del resumen estadístico.
4. Alternar el orden de los tratamientos para reducir el sesgo producido por
   cachés y orden de ejecución.
5. Ejecutar el número configurado de repeticiones para cada tratamiento.
6. Registrar una observación por ejecución conforme a
   `metrics/metric-schema.json`.
7. Conservar también las ejecuciones fallidas, indicando su estado y error.

`analyze_speedup.py` valida el lote y produce resumen y figura desde registros
reales. Calcula media, desviación muestral, speedup contra pandas y contra
Spark(1), eficiencia respecto de Spark(1) y ajuste restringido de Amdahl sobre
tiempos normalizados Spark.

## Condiciones de validez

- Una repetición es válida cuando termina sin error y produce el resultado
  esperado.
- Los tratamientos deben procesar la misma cantidad de filas de entrada.
- No deben modificarse los datos fuente entre tratamientos equivalentes.
- Una interrupción externa debe registrarse como ejecución fallida, no
  eliminarse silenciosamente.
- El rendimiento se calculará posteriormente a partir de filas procesadas y
  tiempo de ejecución; no se registrarán valores estimados.

## Almacenamiento

Los registros se guardarán en `experimentos/metrics/results/<UUID>/`. Cada
registro deberá cumplir el esquema JSON y conservar un identificador único de
ejecución, el tratamiento, el conjunto de datos, el entorno y las mediciones
capturadas.

Prometheus y Grafana no se incorporan en este subpaso porque no se identificó
una exigencia explícita en la rúbrica disponible. La estructura JSON permite
integrar posteriormente un recolector externo sin acoplar el protocolo a una
plataforma de observabilidad.

## Ejecución de referencia 2026-09-16

La ejecución definitiva procesó 90 000 filas con pandas y Spark `local[N]`,
para `N=1,2,4,6,8`, usando un warmup y cinco repeticiones medidas por
tratamiento/grado. La equivalencia previa se verificó antes de medir. El lote
es `experimentos/evidencia-17/20260916/benchmark-definitivo-9d94efe6-7bb7-4227-b78e-c70092e9bcfb`;
la equivalencia es
`equivalence-final-a2b60a0e-d2b5-4d69-95c5-904353062c9a` y el análisis es
`analysis-definitivo-233b34ac-a09f-40c9-be71-5570f25affbd`. Los detalles y
resultados agregados se consultan en `resumen.json` y `resumen.csv` del
análisis, sin convertir este protocolo en un informe estadístico.
