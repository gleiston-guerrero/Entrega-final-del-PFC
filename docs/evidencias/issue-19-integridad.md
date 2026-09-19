# #19 — Integridad de evidencia

Responsable: Iván. Base auditada: `1785bdd6ddf9ee651f59b31b00abca7d77a20536`
(`origin/main` actualizado). Rama: `fix/eval2-19-manifests-ivan`; árbol inicial
limpio. No se modifican datos históricos ni manifiestos anteriores.

## Verificación reproducible

Desde la raíz, con Python >= 3.11 y Git:

```sh
python scripts/verificar-manifiestos.py
python -m unittest discover -s scripts/tests -p 'test_verificar_manifiestos.py' -v
python experimentos/verificar_manifiesto_evidencia17.py verificar --paquete experimentos/evidencia-17/20260916
python -m unittest discover -s experimentos/tests -p 'test_verificar_manifiesto_evidencia17.py' -v
```

Antes de incorporar los cuatro manifiestos nuevos a Git, ejecutar:

```sh
python scripts/verificar-manifiestos.py --include-untracked
```

El modo predeterminado usa `git ls-files -z --cached`, sin un número fijo de
manifiestos. Solo acepta los nombres `SHA256SUMS`, `SHA256SUMS.txt` y
`MANIFEST-SHA256.txt`. La opción de revisión añade `--others --exclude-standard`;
no modifica el índice. En este árbol sin stage, el modo predeterminado encuentra
**21 manifiestos / 1412 entradas / 1412 OK / 0 FAILED**. La propuesta completa
verifica **25 manifiestos / 1459 entradas / 1459 OK / 0 FAILED**. Tras versionar
los nuevos archivos, el modo predeterminado de CI encontrará los 25.

Todos los manifiestos actuales emplean SHA-256 en formato GNU:
64 dígitos hexadecimales, espacio, indicador de texto (espacio) o binario (`*`),
y ruta relativa. Se verifican también con `sha256sum --check` desde la base
indicada en el inventario. No hace falta un formato especial. El parser rechaza
líneas inválidas, manifiestos vacíos, duplicados, autorreferencias y rutas que
escapan de su base; no interpreta silenciosamente formatos desconocidos.
La única excepción explícita de base es `experimentos/resultados/SHA256SUMS`,
cuyas rutas parten de la raíz del repositorio. Todos los demás parten de su
directorio. No se elige otra base cuando un archivo falta o cambia su hash.

Cada manifiesto muestra `MANIFEST | BASE | ENTRIES | OK | FAILED`; el cierre
muestra `manifests`, `entries`, `ok`, `failed`. Los fallos de lectura, ausencia,
hash, parser o descubrimiento dan exit 1. Los errores de manifiesto también se
cuentan como fallos, aunque no pueda determinarse su número de entradas.
`--root` y `--manifest` (repetible) permiten comprobar copias temporales; el modo
explícito restringe el alcance y no sustituye el descubrimiento global de CI.

## Cobertura recalculada

El [inventario por archivo](issue-19-cobertura.csv) enumera los **1516 archivos
rastreados de la base** bajo `experimentos/`, `spark/` y `release/`, con clase,
cobertura anterior, cobertura propuesta y manifiestos que los cubren. No existe
un directorio raíz `arbiter/`: su evidencia está en
`experimentos/resultados/arbiter/`. Se consideran solo artefactos entregados en
Git, no el raw externo de la VM. El inventario no incorpora como datos nuevos
los cuatro manifiestos añadidos por esta corrección.

| Clase | Total | Cubiertos en la base | Cubiertos en la propuesta |
|---|---:|---:|---:|
| A: código, scripts, consultas, configuración y documentación | 198 | 135 | 140 |
| B: raw, registros instrumentales y capturas | 903 | 873 | 903 |
| C: derivados | 197 | 192 | 197 |
| D: manifiestos dentro de este alcance | 20 | 0 | 0 |
| E: metadata preservada | 198 | 191 | 198 |

`RAW_TOTAL=903`, `RAW_COVERED=903`, `RAW_UNCOVERED=0` en la propuesta.
Lista exacta final sin cobertura: **vacía**. Antes del cambio había 30 archivos
de clase B sin cobertura: 22 de `rep-04` y ocho capturas de release. El CSV
permite recuperar sus rutas exactas filtrando `clase=B_raw` y
`cubierto_base=no`. Los 35 archivos del paquete incompleto no son todos raw:
incluyen 22 raw, siete metadatos, un reporte derivado y cinco consultas PromQL.
No se reproduce el antiguo conteo de 83 como si siguiera vigente.

Criterio de clasificación: fuentes, notebooks, consultas `.promql`, fixtures,
esquemas y Markdown son A. Los metadatos de entorno, deployment, contenedores,
fases, timestamps, procedencia, configuración de corrida, `manifest.json`,
`campaign.json`, `e3_study.json` y `checkpoint.json` son E. Análisis, comparaciones,
equivalencia, matrices ISO, resúmenes, reportes HTML de Locust, estadísticas
finales JSON y APK son C. Las mediciones exportadas por instrumentos (incluidos
CSV de Locust y reportes fuente de cobertura), registros de benchmark, eventos,
logs y capturas son B. La pertenencia a una carpeta llamada `raw` no convierte
una consulta o metadata en una medición. Los manifiestos son D y no se exige
autorreferencia. Las clases de cada archivo quedan explícitas en el CSV.

Los cuatro derivados señalados por la evaluación seguían sin cobertura:

- `experimentos/resultados/analisis-e3.json` y `iso25010-correctiva.csv`:
  nuevo `experimentos/resultados/MANIFEST-SHA256.txt` (2 entradas).
- `experimentos/metrics/results/comparacion.csv` y `comparacion.json`:
  nuevo `experimentos/metrics/results/SHA256SUMS` (2 entradas).

Se añaden ocho capturas `*release.png` a `release/screenshots/SHA256SUMS.txt`.
`panel-monitoreo.png` ya estaba cubierto por el manifiesto de entrega-3 y no se
duplica. El quinto derivado antes sin cobertura es `rep-04/locust-report.html`;
queda incluido en el manifiesto de ese paquete. Todos los 197 derivados y los
198 metadatos de la base quedan cubiertos, sin modificar sus bytes.

## Nota de integridad del intento rep-04

Ruta: `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04/`.
Contenía **35 archivos versionados**, sin manifiesto propio. Se añade únicamente
`SHA256SUMS` con esas 35 rutas relativas ordenadas, sin incluirse a sí mismo.
Antes de calcularlo se compararon sus bytes físicos con los blobs de `HEAD`.

El intento quedó abortado/incompleto por disco lleno:
`console-disk-full.log` (nombre real, con guiones) conserva en las líneas 6–13
`No space left on device` y `OSError: [Errno 28]`; al final declara ejecución
experimental no completada. `metadata.json` está truncado y no es JSON válido:
error en línea 30, columna 37, carácter 8191; termina con el literal parcial
`"reservas_log_capture_succeeded": t`. **No se reparó ni modificó**.

El manifiesto solo fija los bytes actualmente preservados. No convierte este
intento en una repetición válida, no completa su metadata y no cambia ninguna
selección experimental. Esta nota se mantiene fuera del raw.

## Preservación, CI y límites

- Smoke-refresh verifica **7/7**: los tres fallos históricos ya no están presentes.
- Evidencia-17 verifica **50/50**, tanto globalmente como con su verificador
  específico. No se regenera ninguno de estos dos manifiestos.
- `.gitattributes` sigue aplicando `-text` a evidencia-17 y a los datos de smoke:
  se preservan bytes. El manifiesto de smoke conserva su excepción `text eol=lf`.
  No se cambia `.gitattributes` ni se renormalizan archivos.
- `verify-experimental-manifest` ejecuta las pruebas y la verificación global
  en los eventos push/PR ya definidos. `publish-release` mantiene sus tres
  dependencias y añade este job. Sin éxito del gate no puede publicarse.
  No se modifica otro aspecto de #15, OpenAPI, deployment o releases.
- Las pruebas usan temporales: tres nombres soportados, base histórica,
  descubrimiento múltiple, errores de lectura, ausencia, parser y una copia
  real de los 50 archivos de #17. Una mutación de exactamente un byte produce
  `MISMATCH` y exit distinto de cero; eliminarlo produce `MISSING`.

Los checksums comprueban integridad respecto de los bytes fijados por el
manifiesto; **no prueban por sí solos originalidad ni autenticidad histórica**.
Cambiar a la vez datos y hashes podría producir una verificación correcta.
La procedencia requiere además revisar historia, metadata, SHA experimental y
las referencias internas existentes. En #17 se conservan `provenance.json`,
`source_sha256` y las reconciliaciones históricas de hashes/EOL sin reescribirlas.
La comprobación global complementa esas referencias y no las sustituye.

Se contrastaron las referencias adicionales de #17: los dos hashes internos
de `resumen.json` coinciden con `comparacion.json` y `config.json` (2/2).
Los cuatro `source_sha256` coinciden con los blobs del commit reconciliado
`197ce3305c821a37c788f4c8f7a783996121f6cc` (4/4). No coinciden con el
`git_head` histórico declarado en `provenance.json`, discrepancia ya explicada
por `RECONCILIACION-PROVENANCE.md` de #17. Se preservan ambos documentos y no
se presenta el gate de checksums como reparación de esa metadata histórica.

La validación aquí es local. Un workflow preparado y con sintaxis validada no
equivale a una ejecución remota de GitHub Actions en verde.

## Validación local realizada

- Verificador global: 25/1459/1459/0, exit 0 con `--include-untracked`;
  modo exclusivamente rastreado: 21/1412/1412/0, exit 0.
- Comprobación independiente con GNU `sha256sum --check`: los 25 manifiestos
  pasan desde sus bases respectivas, 1459 entradas correctas.
- Pruebas automatizadas: 12/12 del verificador global y 4/4 de evidencia-17.
- Verificador específico de evidencia-17: 50/50, exit 0.
- `analizar_iso25010.py`, tanto sobre `iso25010.csv` como sobre
  `iso25010-correctiva.csv`: exit 0, solo lectura, sin regenerar resultados.
- Workflow: YAML parseado y dependencias de publicación comprobadas por
  aserciones. No se ejecutó GitHub Actions remotamente.
- Manuscrito: `pdflatex`, `bibtex`, `pdflatex`, `pdflatex`, todos exit 0;
  36 páginas, cero errores LaTeX, referencias indefinidas o citas indefinidas.
  Se compiló una copia temporal en un contenedor con el repositorio montado
  solo para lectura; no se deja PDF, log ni auxiliar en el árbol de trabajo.

## Inventario de manifiestos

El inventario siguiente comprende los 21 históricos y los cuatro nuevos.
Todas las entradas usan SHA-256 GNU y admiten `sha256sum --check` desde BASE.

| MANIFEST | BASE | ENTRADAS | OK | FAILED |
|---|---|---:|---:|---:|
| `docs/entrega-3/SHA256SUMS.txt` | `docs/entrega-3` | 21 | 21 | 0 |
| `experimentos/evidencia-17/20260916/SHA256SUMS.txt` | `experimentos/evidencia-17/20260916` | 50 | 50 | 0 |
| `experimentos/evidencia-e2/smoke-refresh-25m/SHA256SUMS.txt` | `experimentos/evidencia-e2/smoke-refresh-25m` | 7 | 7 | 0 |
| `experimentos/metrics/results/SHA256SUMS` | `experimentos/metrics/results` | 2 | 2 | 0 |
| `experimentos/resultados/MANIFEST-SHA256.txt` | `experimentos/resultados` | 2 | 2 | 0 |
| `experimentos/resultados/SHA256SUMS` | `.` | 468 | 468 | 0 |
| `experimentos/resultados/arbiter/campaign/SHA256SUMS` | `experimentos/resultados/arbiter/campaign` | 315 | 315 | 0 |
| `experimentos/resultados/evidencia-e3-canonica/MANIFEST-SHA256.txt` | `experimentos/resultados/evidencia-e3-canonica` | 50 | 50 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01-attempt-02/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01-attempt-02` | 35 | 35 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01-attempt-03/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01-attempt-03` | 36 | 36 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01` | 35 | 35 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-02/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-02` | 36 | 36 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-03/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-03` | 36 | 36 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04-attempt-02/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04-attempt-02` | 35 | 35 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04-attempt-03/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04-attempt-03` | 36 | 36 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04` | 35 | 35 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-05/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-05` | 36 | 36 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-06-attempt-02/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-06-attempt-02` | 36 | 36 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-06/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-06` | 35 | 35 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-07/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-07` | 36 | 36 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-08/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-08` | 36 | 36 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-09/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-09` | 36 | 36 | 0 |
| `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-10/SHA256SUMS` | `experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-10` | 36 | 36 | 0 |
| `release/apk/SHA256SUMS.txt` | `release/apk` | 1 | 1 | 0 |
| `release/screenshots/SHA256SUMS.txt` | `release/screenshots` | 8 | 8 | 0 |
