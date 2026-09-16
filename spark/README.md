# Corrección #17 — IVÁN

**Evidencia experimental pendiente de ejecución real.** No existen mediciones
Spark en las plantillas históricas `experimentos/metrics/results/comparacion.*`.
Los resultados HTTP/Locust de otros experimentos no sirven para esta comparación.

`construir_pipeline()` solo compone transformaciones. `ejecutar_pipeline()` ahora
ejecuta la acción terminal de escritura Parquet: todas las columnas se evalúan.
Spark genera un directorio con partes Parquet; pandas exporta un archivo Parquet
sin índice. Ambos rechazan destinos existentes por defecto. Spark permite
sobrescritura explícita con `--overwrite`; pandas con `overwrite=True` en su API.
El notebook es una demostración pandas sin resultados ejecutados, no un benchmark.

## Preparación del entorno real

Desde la raíz del repositorio, usar Python 3.11 o 3.12, Java 17, un JAR JDBC
PostgreSQL local y una copia inmutable identificable de `reservas_db` (esquema
`db/schema.sql`). Las dos conexiones deben apuntar a esa misma copia, sin
escrituras concurrentes. Mantener el mismo equipo, almacenamiento y carga externa.
Los grados predeterminados requieren al menos ocho CPU lógicas disponibles.
No basta con introducir un nombre de snapshot: registrar cómo se restauró y
verificar previamente la equivalencia del resultado de ambas implementaciones.

Comandos PowerShell (sustituir los valores entre `<...>` por datos reales):

```powershell
python -m venv .venv-spark
.\.venv-spark\Scripts\Activate.ps1
python -m pip install -r spark/requirements.txt
$env:JAVA_HOME = '<directorio-JDK-17>'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
$env:POSTGRES_JDBC_JAR = '<ruta-absoluta-postgresql.jar>'
$env:RESERVAS_JDBC_URL = 'jdbc:postgresql://<host>:<puerto>/reservas_db?sslmode=<modo>'
$env:RESERVAS_DB_USERNAME = '<usuario>'
$env:RESERVAS_DB_PASSWORD = '<clave>'
$env:RESERVAS_PANDAS_URL = 'postgresql+psycopg://<usuario>:<clave-url-encoded>@<host>:<puerto>/reservas_db?sslmode=<modo>'
$config = Get-Content experimentos/experiment-config.json -Raw | ConvertFrom-Json
$config.dataset.snapshot_id = '<identificador-real-del-snapshot>'
$config | ConvertTo-Json -Depth 10 | Set-Content experimentos/experiment-config.local.json -Encoding ascii
python experimentos/run_comparison.py --config experimentos/experiment-config.local.json
```

El medidor imprime el directorio UUID del lote. Para analizarlo:

```powershell
python experimentos/analyze_speedup.py --input experimentos/metrics/results/<UUID>/comparacion.json --output experimentos/metrics/results/<UUID>/analisis
```

Materialización independiente, fuera de la medición:

```powershell
python spark/pipeline.py --output spark/out/spark-real --parallelism 4
python spark/baseline.py
```

## Protocolo 1.1 y límites

Se reutilizan `experimentos/run_comparison.py`, su configuración y esquema JSON.
Se comparan pandas secuencial (librerías numéricas limitadas a un hilo) y Spark
`local[N]` para N=1,2,4,6,8: cinco repeticiones medidas y un calentamiento por
tratamiento/grado. El orden se invierte en rondas pares. Cada observación usa un
proceso nuevo; el calentamiento precalienta almacenamiento/BD, no reutiliza JVM.
Se fijan paralelismo por defecto y particiones shuffle a N y se desactiva AQE.
Esto mide escalamiento local, no un clúster multinodo. La lectura JDBC permanece
sin particionado explícito; no se afirma que existan 16 lectores.

El tiempo de pared incluye arranque, lecturas, transformaciones, escritura
Parquet, lectura de metadatos para contar filas de salida, cierre y limpieza
temporal. No se interpreta como tiempo exclusivo de CPU. Los cinco orígenes se
registran en Spark de forma perezosa; pandas los carga, por lo que los costes de
extracción de ambos motores difieren. El speedup contra pandas compara estas
implementaciones completas, no aísla el efecto del paralelismo.

Los Parquet temporales se eliminan tras medir; los JSON individuales y la
comparación JSON/CSV conservan tiempos, filas **de salida**, estado, fecha,
snapshot, lote, paralelismo, repetición, warmup y entorno. Las ejecuciones
fallidas y warmups se conservan. CPU/RSS son muestreos aproximados del árbol de
procesos cada 200 ms; no representan métricas de ejecutores remotos.
El lote guarda configuración y procedencia; archivar además inventario/tamaño de
las tablas del snapshot, comando de restauración y `pip freeze` con el lote.
Nunca versionar contraseñas ni cadenas de conexión privadas.

El análisis exige un lote completo, sin fallos, con igual snapshot, entorno y
conteo no vacío de salida. Igual número de filas es necesario pero no demuestra
igualdad de contenido: contrastar los Parquet independientes por `reserva_id`,
normalizando fecha/tipos y orden antes de aceptar evidencia final.
Excluye warmups y calcula media y desviación muestral; speedup contra pandas
es media(pandas)/media(Spark N). El escalamiento usa Spark(1)/Spark(N) y su
eficiencia divide por N. Amdahl ajusta por mínimos cuadrados
T(N)/T(1)=f+(1-f)/N con f restringida a [0,1]; informa también ajuste libre,
RMSE y si se alcanzó un límite. Es una fracción serial efectiva, que incluye
arranque, JDBC, I/O y sobrecostes; un ajuste malo no valida la ley.

Solo tras una ejecución real, revisar y versionar el lote crudo, `resumen.csv`,
`resumen.json` y `speedup.png`, junto con timestamp, entorno, tamaño del dataset,
grados, repeticiones y comando. El análisis rechaza sobrescribir su directorio.
No se puede cerrar #17 únicamente con estos scripts.

## Verificación

```powershell
python -m py_compile spark/pipeline.py spark/baseline.py experimentos/run_comparison.py experimentos/analyze_speedup.py experimentos/tests/test_speedup.py
python -m unittest discover -s experimentos/tests -p test_speedup.py -v
python -m unittest discover -s experimentos/tests -p 'test_*.py' -v
git diff --check
```
