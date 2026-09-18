# Correccion #17: benchmark Spark vs pandas

La evidencia experimental definitiva de la corrección #17 está versionada en
`experimentos/evidencia-17/20260916/`. Este README describe el código y resume
únicamente ese lote real.
Los resultados HTTP/Locust y las plantillas historicas no son evidencia Spark.

## Entorno y versiones

Trabajar desde la raiz, en `fix/spark-speedup-ivan`, con CockroachDB local en
`localhost:26261`. Usar las migraciones del servicio para el esquema; `db/schema.sql`
es referencia historica, no una instalacion nueva. `db/seeds.sql` contiene 410001
filas: solicitudes_reserva=100000, reservas=100000, historial_solicitudes=200000,
bloqueos_agenda=10000 y configuraciones_reserva=1. No volver a cargar la semilla
sobre la base ya preparada.

La ejecución de referencia probó Python 3.13.14. El código usa Python 3.11+ y
la dependencia es
Spark 4.0.x: [Apache documenta Java 17/21 y Python 3.9+](https://spark.apache.org/docs/4.0.0/).
Esto reemplaza la restriccion anterior Spark 3.5, cuyo soporte documentado no
incluye Java 21. Puede usarse el JDK 21 disponible; Java 8 no sirve para Spark 4.
La compatibilidad efectiva en este Windows se demostró con la equivalencia
Parquet antes del benchmark, no inferirse solo de una lista de versiones.

SQLAlchemy usa el [dialecto CockroachDB con psycopg 3](https://github.com/cockroachdb/sqlalchemy-cockroachdb/blob/master/README.psycopg.md)
(CockroachDB 22.2.6/23.1.0 o posterior). Se acepta una URL
`postgresql+psycopg://...` o `cockroachdb+psycopg://...`; internamente se selecciona
el dialecto CockroachDB. Se evita la reflexion PostgreSQL de `read_sql_table`.

El inventario y la procedencia registran versiones efectivas de Python, Java,
Spark, pandas y dependencias, CPU, SO y SHA-256 del JAR JDBC. Puede usarse el
PostgreSQL JDBC 42.7.11 existente. No se etiqueta ninguna version como probada
hasta que la ejecucion real termine. No cambiar paquetes, JAR ni codigo entre
la equivalencia y la medicion.

## PowerShell: preparar sin mostrar secretos

En una terminal que tenga el Python deseado disponible:

```powershell
python --version
python -m venv .venv-spark
$python = (Resolve-Path .\.venv-spark\Scripts\python.exe).Path
& $python -m pip install -r spark/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se instalaron las dependencias' }

# Lee solo nombres permitidos y asigna valores literales; no imprime ni ejecuta env.
. .\experimentos\load-env.ps1
# Las credenciales siguen viniendo exclusivamente del entorno.
$env:RESERVAS_JDBC_URL = 'jdbc:postgresql://localhost:26261/reservas_db?sslmode=disable'
$env:RESERVAS_PANDAS_URL = 'cockroachdb+psycopg://localhost:26261/reservas_db?sslmode=disable'
# JAVA_HOME debe identificar el JDK 21 (o 17) realmente instalado.
# POSTGRES_JDBC_JAR debe identificar el archivo JDBC 42.7.11 existente.
if (-not $env:JAVA_HOME) { throw 'Configure JAVA_HOME con la ruta real del JDK' }
& "$env:JAVA_HOME\bin\java.exe" -version
if (-not (Test-Path -LiteralPath $env:POSTGRES_JDBC_JAR -PathType Leaf)) { throw 'Falta el JAR JDBC local' }
```

`load-env.ps1` admite `KEY=VALUE`, comillas exteriores simples/dobles y prefijo
`export`; no expande variables, no interpreta escapes ni comentarios al final
del valor. Las variables requeridas son `RESERVAS_DB_USERNAME`,
`RESERVAS_DB_PASSWORD`, `RESERVAS_JDBC_URL`, `RESERVAS_PANDAS_URL` y
`POSTGRES_JDBC_JAR`. Si ya estan en el entorno, omitir la carga del archivo.
No usar `Get-Content env`, `Get-ChildItem Env:` ni transcripciones para evidencias.
`env`, configuracion local, entorno virtual y Parquet de equivalencia estan ignorados.
La URL pandas puede omitir usuario/clave: ambos se toman de las variables separadas.
Si contiene credenciales, deben coincidir. Ambos endpoints y sslmode deben coincidir
exactamente; no se aceptan opciones que redirijan la conexion o cambien el esquema.

En Windows, la escritura Hadoop/Parquet puede requerir herramientas nativas
compatibles con la distribucion Spark instalada (`HADOOP_HOME`, `bin` en PATH).
El cargador admite HADOOP_HOME si ya esta configurado. Un fallo de JVM, JDBC o
escritura Parquet invalida la equivalencia; corregir el entorno y usar otro
directorio nuevo. No sustituir Parquet por `count()` ni aceptar una ejecucion fallida.

## Snapshot, validacion y equivalencia (sin medir tiempos)

```powershell
$config = 'experimentos/experiment-config.local.json'
$id = [guid]::NewGuid().ToString()
$equiv = "experimentos/local-evidence/$id"
$lote = "experimentos/metrics/results/$id"

& $python experimentos/prepare_local.py prepare --config $config
if ($LASTEXITCODE -ne 0) { throw 'Fallo preparando snapshot' }
& $python experimentos/prepare_local.py validate --config $config --output $lote
if ($LASTEXITCODE -ne 0) { throw 'Fallo prevalidacion' }
& $python experimentos/verify_equivalence.py --config $config --output $equiv
if ($LASTEXITCODE -ne 0) { throw 'Fallo equivalencia; no medir' }
```

`prepare` crea la configuracion local desde la plantilla y rechaza sobrescribirla.
Incluye inventario con columnas, conteos, total, hash del contenido ordenado por
`id`, SHA-256 de los bytes de `db/seeds.sql` y un `snapshot_id` SHA-256 del inventario
canonico sin credenciales. La fecha de lectura HLC no participa del hash: el mismo
contenido y semilla producen la misma identidad en el mismo endpoint.

Las consultas pandas y JDBC usan el mismo `AS OF SYSTEM TIME` absoluto de
CockroachDB. No es un backup permanente: ejecutar la secuencia dentro de la ventana
de retencion MVCC configurada. Si expira, conservar los intentos anteriores,
archivar/renombrar la configuracion local y preparar otro snapshot; nunca cambiar
silenciosamente a datos actuales. Evitar escrituras y cambios de esquema durante
la campana. La semilla debe conservar exactamente sus bytes para repetir el hash.

`validate` comprueba >=8 CPU logicas, protocolo exacto, variables, JAR, versiones,
endpoints, tablas, conteos exactos no vacios, huellas y destino inexistente.
El benchmark repite esta comprobacion y crea el directorio exclusivamente.
`verify_equivalence` escribe pandas y Spark local[1,2,4,6,8] en destinos nuevos,
compara **las 20 columnas** por `reserva_id`, rechaza claves nulas/duplicadas,
normaliza UUID/texto, numeros, orden, horas y fechas UTC a microsegundos.
Un cambio de contenido con igual numero de filas falla. Solo entonces crea
`equivalence.json`, ligado a snapshot, timestamp, entorno y hashes del codigo.
No registra tiempos ni genera resultados de rendimiento.

## Medicion y analisis reales

```powershell
& $python experimentos/run_comparison.py --config $config --output $lote --equivalence "$equiv/equivalence.json"
if ($LASTEXITCODE -ne 0) { throw 'Lote invalido; conservarlo para diagnostico' }
& $python experimentos/analyze_speedup.py --input "$lote/comparacion.json" --output "$lote/analisis"
if ($LASTEXITCODE -ne 0) { throw 'Fallo analisis' }
Get-ChildItem -LiteralPath $lote -Recurse -File | Select-Object FullName,Length
Get-ChildItem -LiteralPath $equiv -Recurse -File | Select-Object FullName,Length
```

Protocolo 1.1: pandas secuencial, Spark `local[N]`, N=1,2,4,6,8; un warmup y
cinco repeticiones medidas por tratamiento/grado (36 registros, 30 medidos).
Cada observacion usa proceso nuevo; el warmup precalienta BD/almacenamiento,
no reutiliza JVM. Se invierte el orden en rondas pares. AQE desactivado,
paralelismo y particiones shuffle=N; JDBC sin particionado. Pandas carga las cinco
tablas; Spark registra las cinco de forma perezosa. Se comparan implementaciones
completas, no unicamente capacidad de CPU ni un cluster multinodo.

La accion terminal es escritura real de todas las columnas a Parquet. El tiempo
incluye arranque, lecturas, transformaciones, escritura, conteo de metadatos,
cierre y limpieza temporal. Los Parquet medidos se eliminan tras cada observacion.
Se conservan JSON individuales (tambien warmups/fallos), `comparacion.json` y
`comparacion.csv`, `config.json`, `inventory.json`, `equivalence.json` y
`provenance.json` y `packages.txt` (versiones instaladas, sin URLs). CPU/RSS son muestras aproximadas del arbol cada 200 ms.
Los errores de driver se resumen por tipo, sin persistir cadenas de conexion.

El analisis exige equivalencia, un lote completo sin fallos, identidad/entorno
consistentes y filas no vacias. Excluye warmups. Produce `analisis/resumen.csv`,
`analisis/resumen.json` y `analisis/speedup.png`: media, desviacion muestral,
speedup pandas/Spark(N), Spark(1)/Spark(N), eficiencia respecto a Spark(1)/N.
Amdahl ajusta T(N)/T(1)=f+(1-f)/N por minimos cuadrados, f en [0,1], e informa
ajuste libre, RMSE y limite alcanzado. f es una fraccion serial efectiva que
incluye arranque, JDBC e I/O; un ajuste malo no valida la ley.

El lote crudo y analisis son versionables; revisar antes de agregarlos a Git.
Archivar tambien el comando de restauracion real y la revision de codigo usada.
No versionar `env`, URLs privadas, configuracion local ni datos Parquet.
Los scripts no hacen commit, push ni PR.

## Pruebas sin servicios externos

```powershell
& $python -m py_compile spark/pipeline.py spark/baseline.py spark/snapshot.py experimentos/prepare_local.py experimentos/verify_equivalence.py experimentos/run_comparison.py experimentos/analyze_speedup.py
& $python -m unittest discover -s experimentos/tests -p test_speedup.py -v
& $python -m unittest discover -s experimentos/tests -p test_local_benchmark.py -v
git diff --check
git status --short
```

Las fixtures unitarias no son mediciones y no producen lotes experimentales.
La prueba integrada requiere CockroachDB, JDK, JDBC y escritura Parquet reales.

## Resultado experimental de la corrección #17

El lote definitivo es `experimentos/evidencia-17/20260916/benchmark-definitivo-9d94efe6-7bb7-4227-b78e-c70092e9bcfb`.
La equivalencia previa es `equivalence-final-a2b60a0e-d2b5-4d69-95c5-904353062c9a`.
Se procesaron 90 000 filas: 1 warmup y 5 repeticiones medidas para pandas, y
1 warmup y 5 repeticiones medidas para cada Spark `local[N]`, con
`N=1,2,4,6,8`. Todos los registros terminaron en `completed`.

| Tratamiento | Media ms | Desv. ms | Speedup vs pandas | Speedup vs Spark(1) | Eficiencia |
| --- | ---: | ---: | ---: | ---: | ---: |
| pandas | 17326.5594 | 1504.0669 | 1.0000 | -- | -- |
| Spark N=1 | 40932.1306 | 5654.1916 | 0.4233 | 1.0000 | 1.0000 |
| Spark N=2 | 39071.1490 | 1280.0474 | 0.4435 | 1.0476 | 0.5238 |
| Spark N=4 | 40681.5648 | 5748.0534 | 0.4259 | 1.0062 | 0.2515 |
| Spark N=6 | 39392.2152 | 2369.4410 | 0.4398 | 1.0391 | 0.1732 |
| Spark N=8 | 41187.6932 | 1088.0059 | 0.4207 | 0.9938 | 0.1242 |

El entorno registrado fue Python 3.13.14, PySpark 4.0.4, Java 21 y pandas
2.3.3; las demás versiones están en `packages.txt` y `provenance.json` del
lote. El ajuste OLS de Amdahl sobre Spark(1) produjo `f=0.9765853071`,
fracción paralelizable efectiva `0.0234146929` y RMSE normalizado
`0.0215078993`. Esta fracción efectiva incluye arranque, JDBC, E/S, escritura
y sobrecarga, por lo que no representa porcentaje de código serial.

La carga concreta no mostró una mejora relevante al aumentar `N`: Spark tardó
aproximadamente 39--41 s frente a 17.33 s de pandas. El mejor speedup frente a
Spark(1) fue N=2, aproximadamente 1.0476x; N=8 no mejoró frente a N=1.

Artefactos principales del lote: `equivalence.json`, `comparacion.json`,
`comparacion.csv`, `config.json`, `inventory.json`, `provenance.json`,
`packages.txt`, `analisis/resumen.json`, `analisis/resumen.csv` y
`analisis/speedup.png`. La carpeta de análisis es
`analysis-definitivo-233b34ac-a09f-40c9-be71-5570f25affbd`.
