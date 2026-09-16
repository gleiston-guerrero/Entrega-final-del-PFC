# Interpretación de las métricas experimentales

## Archivos generados

Al ejecutar `experimentos/run_comparison.py`, el directorio `experimentos/metrics/results/<UUID>/`
contendrá:

- un JSON por repetición, que conserva la observación completa y su entorno;
- `comparacion.json`, con todas las repeticiones medidas del lote;
- `comparacion.csv`, con las mismas observaciones en formato tabular.

Las plantillas históricas están vacías y se conservan. El automatizador crea
un lote nuevo únicamente cuando se ejecutan experimentos reales.

## Comparación válida

Se deben comparar observaciones de `pandas-baseline` y `pyspark-pipeline` que:

- tengan `status` igual a `completed`;
- pertenezcan al mismo `dataset_id` y `dataset_snapshot_id`;
- hayan procesado el mismo valor de `rows_processed`;
- se hayan obtenido con condiciones de entorno equivalentes.

Los calentamientos aparecen con `warmup=true` y se excluyen del análisis.
Los fallos y timeouts se conservan; el análisis rechaza lotes incompletos o con
fallos. Cada grado Spark debe contener todas las repeticiones configuradas.

## Campos principales

### `duration_ms`

Tiempo de pared desde el inicio del proceso hasta su finalización. Un valor
menor representa menor latencia total para el mismo trabajo y conjunto de
datos. Incluye el arranque del motor correspondiente.

### `cpu_percent_mean` y `cpu_percent_max`

Uso medio y máximo de CPU del proceso y sus hijos. PySpark puede utilizar
varios núcleos, por lo que el porcentaje acumulado puede superar 100 %. Estos
campos deben interpretarse junto con `logical_cpu_count`.

### `memory_mib_mean` y `memory_mib_max`

Memoria residente media y máxima, en MiB, sumada para todo el árbol de
procesos. Un valor menor indica menor presión de memoria, pero no implica por
sí solo mayor rendimiento.

### `rows_processed`

Cantidad de filas del resultado materializado. Debe coincidir entre los dos
tratamientos; una diferencia invalida la comparación funcional.

### `throughput_rows_per_second`

Relación entre filas procesadas y duración total. Para el mismo resultado, un
valor mayor representa más rendimiento. No debe compararse entre conjuntos de
datos o condiciones diferentes.

### `status` y `error`

`status` puede ser `completed`, `failed` o `timeout`. Cuando la ejecución no se
completa, `error` conserva la causa disponible y las métricas restantes sirven
solo para diagnóstico.

## Metadatos del entorno

Las columnas de host, sistema operativo, CPU, memoria y versiones permiten
detectar cambios de entorno. Si difieren entre ejecuciones, la variación puede
deberse a la plataforma y no al motor de procesamiento.

## Uso posterior

Los gráficos, estadísticos agregados y conclusiones finales deben construirse
solo después de ejecutar el protocolo completo. Las plantillas vacías no
representan resultados ni deben interpretarse como mediciones.
