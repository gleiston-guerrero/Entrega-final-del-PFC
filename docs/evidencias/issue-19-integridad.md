# #19 — Integridad de evidencia

Base de esta corrección: `0aae3050bb363aaa0e6de0ae3875e1bcfdf9519d`.
Rama: `fix/eval3-19-integridad-isaias`. Se auditan archivos rastreados y sus
bytes en el árbol de trabajo. Al inicio había una modificación sin commit
únicamente en `.gitattributes`. No se realiza stage, commit ni push.

## Verificación reproducible

Desde la raíz del repositorio, en Windows, con el lanzador `py`:

```powershell
git branch --show-current
git rev-parse HEAD
py scripts/verificar-manifiestos.py
py -m unittest discover -s scripts/tests -p "test_verificar_manifiestos.py" -v
git ls-files -- experimentos/ spark/ release/
git ls-files -- '*.sha256'
git check-attr -a -- experimentos/resultados/iso25010-correctiva-poblada.csv experimentos/resultados/analisis-e3.json
git diff --check
git status --short
git diff --stat
git diff -- .gitattributes docs/evidencias/issue-19-integridad.md
```

El verificador descubre mediante `git ls-files -z --cached` los nombres
`SHA256SUMS`, `SHA256SUMS.txt`, `MANIFEST-SHA256.txt`,
`iso25010-eficiencia-poblada.sha256`, `dataset.csv.sha256` y
`dataset-metadata.json.sha256`. Se conserva el soporte de eficiencia existente
y se añaden únicamente los dos nombres de descriptores del preflight.
`ROOT_BASED` no cambia: los descriptores se resuelven desde su propio directorio.
Las bases son el directorio del manifiesto, salvo
`experimentos/resultados/SHA256SUMS` y
`experimentos/resultados/iso25010-eficiencia-poblada.sha256`, que parten de la raíz.
El parser exige formato GNU SHA-256 y rechaza líneas inválidas, duplicados,
manifiestos vacíos, autorreferencias y rutas que escapan de su base.
`--include-untracked` amplía el descubrimiento; no es necesario para esta corrección.

Resultado final real: **54 manifiestos / 3314 entradas / 3314 OK / 0 FAILED**,
exit code **0**. Las entradas pueden cubrir un mismo archivo desde varios
manifiestos; no equivalen al número de archivos únicos del inventario.
Pruebas del verificador: **13 ejecutadas, todas OK**, exit code **0**.
La comprobación es local; no acredita una ejecución remota de GitHub Actions.

## Cobertura recalculada

El [CSV por archivo](issue-19-cobertura.csv) contiene **2221 archivos rastreados**
bajo `experimentos/`, `spark/` y `release/`, obtenidos mediante `git ls-files`.
No incluye datos externos de la VM. Conserva el esquema
`ruta,clase,cubierto_base,cubierto_propuesta,manifiestos_propuesta`.
`cubierto_base` se recalcula con las entradas de los manifiestos del commit
indicado arriba; `cubierto_propuesta` usa las del árbol corregido. La cobertura
indica una referencia explícita desde un manifiesto descubierto, no transitividad
ni autenticidad. La validación global comprueba además los hashes de esos bytes.
Ambas columnas de sí/no coinciden porque los datos ya estaban cubiertos en la
base. Se ajustan únicamente las listas `manifiestos_propuesta` de `dataset.csv`
y `dataset-metadata.json` del preflight para incluir sus descriptores ahora
descubiertos; no cambian rutas inventariadas, clases ni conteos de cobertura.
Para la columna de base se usa el descubrimiento del verificador de ese commit,
que todavía no incluía los dos descriptores absolutos.

| Clase | Total | Cubiertos en base | Cubiertos en propuesta |
|---|---:|---:|---:|
| A_codigo_documentacion | 207 | 144 | 144 |
| B_raw | 1152 | 1152 | 1152 |
| C_derived | 259 | 259 | 259 |
| D_manifest | 53 | 41 | 41 |
| E_metadata | 550 | 550 | 550 |

**RAW_TOTAL=1152, RAW_COVERED=1152, RAW_UNCOVERED=0**.
Todos los derivados y metadatos del alcance están cubiertos.
Hay **75 archivos sin checksum: 63 de código/documentación y 12 manifiestos**.
Sus rutas exactas están en el CSV, filtrando `cubierto_propuesta=no`.
No se exige checksum al código/documentación por existir, ni autorreferencia a
los manifiestos. La lista vacía se refiere exclusivamente a raw sin cobertura,
no a todos los archivos del repositorio.

Criterios de clasificación conservados:

- A: fuentes, scripts, notebooks, consultas `.promql`, fixtures, esquemas,
  configuración general, Markdown y marcadores `.gitkeep`/`.gitignore`.
- B: mediciones instrumentales, CSV de Locust, reportes fuente de cobertura,
  registros de benchmark, eventos, logs y capturas. Los nuevos snapshots
  `dataset.csv`, respuestas de preflight, exportaciones de observabilidad,
  mediciones de disco, escaneos y observaciones operativas pertenecen a B.
- C: análisis, comparaciones, equivalencia, matrices ISO, resúmenes, reportes HTML
  de Locust, estadísticas finales JSON y APK.
- D: manifiestos; incluye los dos `.sha256` históricos del preflight, ahora
  reconciliados a rutas relativas y descubiertos directamente.
- E: metadata de entorno, deployment, contenedores, fases, timestamps, procedencia,
  configuración de corrida, `manifest.json`, `campaign.json`, `e3_study.json` y
  `checkpoint.json`. Incluye hashes de procedencia del dataset/harness, SHA del
  software/evidencia, código de salida, duración y contexto de captura.

Para reproducir la clasificación se conservan las clases de las rutas existentes
en el CSV de la base indicada y se aplican esos criterios a las rutas nuevas.
En las nuevas rutas, los nombres de metadata son:
`00-contexto-final.txt`, `dataset-metadata.json`, `dataset-sha256.txt`,
`deployed-software-sha.txt`, `deployment-after.txt`, `deployment-before.txt`,
`deployment-images.txt`, `deployment-state.txt`, `elapsed-seconds.txt`,
`end_epoch.txt`, `end_utc.txt`, `environment.txt`, `evidence-git-sha.txt`,
`harness-after-sha256.txt`, `harness-before-sha256.txt`, `harness-sha256.txt`,
`locust-exit-code.txt`, `metadata.json`, `panel-monitoreo.metadata.txt`,
`phase-boundaries.json`, `start_epoch.txt` y `start_utc.txt`.
Los nuevos derivados son `http5xx-summary.json`,
`iso25010-correctiva-poblada.csv`, `iso25010-eficiencia-poblada.csv`,
`locust-final-stats.json`, `locust-report.html`, `rep-summary.json` y
`smoke-summary.json`. Los nuevos `.py`, `.sh`, `.md` y `.gitkeep` son A;
los manifiestos son D y el resto de las nuevas rutas son B.
La carpeta `raw` por sí sola no determina la clase.

La cobertura se obtiene parseando cada manifiesto con `parse`, resolviendo su
base con `manifest_base` y su destino con `safe_path`, del verificador actual.
Se agrupan los destinos relativos a la raíz y se cruzan con `git ls-files`;
los nombres de manifiesto se ordenan y separan con `;` en cada fila del CSV.

### Captura de monitoreo

`release/screenshots/panel-monitoreo.png` **no está referenciado** en
`docs/entrega-3/SHA256SUMS.txt`. Su cobertura actual se comprueba en:

- `experimentos/resultados/SHA256SUMS` (ruta desde la raíz).
- `release/screenshots/SHA256SUMS.txt` (ruta desde su directorio).

```powershell
rg -n 'panel-monitoreo.png' docs/entrega-3/SHA256SUMS.txt experimentos/resultados/SHA256SUMS release/screenshots/SHA256SUMS.txt
```

## Auditoría de todos los archivos rastreados *.sha256

Los dos descriptores históricos siguen rastreados bajo
`experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/preflight/`.
Se reconciliaron cambiando únicamente sus rutas absolutas por rutas relativas
al preflight: `/tmp/issue31-dataset-snapshot/dataset.csv` pasa a `dataset.csv`
y `/tmp/issue31-dataset-snapshot/metadata.json` pasa a `dataset-metadata.json`.
Los hashes internos y los finales de línea de ambos descriptores se conservan.
No se modificaron `dataset.csv` ni `dataset-metadata.json`: su comparación
binaria con HEAD coincide y `git diff --` sobre ambos produce salida vacía.

| Archivo | Entradas GNU | Descubierto | Rutas |
|---|---:|---|---|
| `experimentos/resultados/iso25010-eficiencia-poblada.sha256` | 328 | Sí | Relativas a la raíz; todas verificadas |
| `preflight/dataset.csv.sha256` (prefijo anterior) | 1 | Sí | `dataset.csv` |
| `preflight/dataset-metadata.json.sha256` (prefijo anterior) | 1 | Sí | `dataset-metadata.json` |

Todos los `.sha256` rastreados tienen formato GNU, rutas relativas y se descubren
y verifican directamente mediante `scripts/verificar-manifiestos.py`.
La prueba de descubrimiento real exige explícitamente los dos descriptores;
se conservan las pruebas existentes de bases relativas y rechazo de rutas absolutas.

El `preflight/SHA256SUMS` actual usa rutas relativas y verifica **8/8 entradas**,
incluidos `dataset.csv`, `dataset-metadata.json` y los bytes de ambos `.sha256`
reconciliados. Sus nuevos bytes quedan protegidos por ese manifiesto y por
`experimentos/resultados/SHA256SUMS`. Solo se actualizan las entradas de los
descriptores y, en el global, la entrada dependiente del propio
`preflight/SHA256SUMS`, cuyo contenido también cambió. No se regeneran manifiestos
ni se cambian entradas ajenas a esta cadena de integridad.

SHA-256 de los descriptores portables:

- `dataset.csv.sha256`: `c535fb5ebe68c8681d31a84fc67907e77b991666168bdae0bede3f98ee324ec9`.
- `dataset-metadata.json.sha256`: `af5e7002bb87d13661e0fe96615fc934d77e6c02f3579e4fbadb669d05e8e40f`.

No quedan observaciones pendientes de las señaladas para #19 dentro del alcance
auditado. Esto no modifica las limitaciones de procedencia descritas más abajo.

## Reconciliación histórica de finales de línea

`iso25010-correctiva-poblada.csv` y `analisis-e3.json` habían sido normalizados de
CRLF a LF y sus manifiestos realineados. Se restauran exclusivamente los finales
CRLF, sin modificar texto, valores, columnas, orden ni contenido lógico.
Los hashes binarios finales coinciden con los históricos indicados:

| Archivo en experimentos/resultados/ | SHA-256 final |
|---|---|
| `iso25010-correctiva-poblada.csv` | `60cd6afbbddd630c7d5364b4303aa356afbc1ae048b36e1acfe4afa3ddcc31dc` |
| `analisis-e3.json` | `0a2d7fa3bcc98a23deb0cacbfae2db6b0d1208242c9ed1d3cf6fc675ba622ba0` |

Se cambian únicamente sus respectivas entradas en `experimentos/resultados/SHA256SUMS`
y `experimentos/resultados/MANIFEST-SHA256.txt`. Además, el global incorpora los
ajustes vinculados a la reconciliación del preflight descritos arriba.
`.gitattributes` declara `-text -eol` para ambos; `git check-attr -a` confirma
`text: unset` y `eol: unset`, anulando para ellos la regla global `eol=lf`.
El atributo local `whitespace=cr-at-eol` permite a `git diff --check` reconocer
el CR histórico como parte del final de línea, sin transformar bytes ni desactivar
la comprobación de espacios del resto del repositorio. La comprobación final
`git diff --check` termina con exit code 0.

Comprobación binaria y lógica ejecutable desde PowerShell:

```powershell
@'
from pathlib import Path
import hashlib, subprocess
expected = {
    "experimentos/resultados/iso25010-correctiva-poblada.csv":
        "60cd6afbbddd630c7d5364b4303aa356afbc1ae048b36e1acfe4afa3ddcc31dc",
    "experimentos/resultados/analisis-e3.json":
        "0a2d7fa3bcc98a23deb0cacbfae2db6b0d1208242c9ed1d3cf6fc675ba622ba0",
}
for path, digest in expected.items():
    before = subprocess.check_output(["git", "show", "HEAD:" + path])
    after = Path(path).read_bytes()
    assert hashlib.sha256(after).hexdigest() == digest
    assert before.replace(b"\r\n", b"\n") == after.replace(b"\r\n", b"\n")
    assert b"\n" not in after.replace(b"\r\n", b"")
    print(path, digest, "ONLY_EOL=True")
'@ | py -
```

## Preservación y límites

Se conserva el intento abortado/incompleto `rep-04` de
`experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/`, incluido su
registro de disco lleno y su metadata truncada. Tener checksum no convierte
ese intento en una repetición válida ni completa sus metadatos.
No se altera la evidencia de #17, smoke, sus notas de procedencia ni las
selecciones experimentales. Tampoco se regeneran manifiestos completos.

Los checksums comprueban integridad de bytes respecto de un manifiesto;
**no demuestran autenticidad absoluta ni procedencia histórica por sí solos**.
Cambiar datos y hashes simultáneamente puede producir una verificación correcta.
La procedencia requiere también historia, metadata y referencias experimentales.
Aquí la equivalencia lógica con HEAD y la coincidencia con los hashes históricos
aportados respaldan la restauración EOL concreta, no una autenticación universal.

## Inventario actual de manifiestos verificados

| MANIFEST | BASE | ENTRIES | OK | FAILED |
|---|---|---:|---:|---:|
| docs/entrega-3/SHA256SUMS.txt | docs/entrega-3 | 21 | 21 | 0 |
| experimentos/evidencia-17/20260916/SHA256SUMS.txt | experimentos/evidencia-17/20260916 | 50 | 50 | 0 |
| experimentos/evidencia-e2/smoke-refresh-25m/SHA256SUMS.txt | experimentos/evidencia-e2/smoke-refresh-25m | 7 | 7 | 0 |
| experimentos/metrics/results/SHA256SUMS | experimentos/metrics/results | 2 | 2 | 0 |
| experimentos/resultados/MANIFEST-SHA256.txt | experimentos/resultados | 2 | 2 | 0 |
| experimentos/resultados/SHA256SUMS | . | 1339 | 1339 | 0 |
| experimentos/resultados/arbiter/campaign/SHA256SUMS | experimentos/resultados/arbiter/campaign | 315 | 315 | 0 |
| experimentos/resultados/evidencia-e3-canonica/MANIFEST-SHA256.txt | experimentos/resultados/evidencia-e3-canonica | 50 | 50 | 0 |
| experimentos/resultados/iso25010-eficiencia-poblada.sha256 | . | 328 | 328 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/preflight/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/preflight | 2 | 2 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-01/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-01 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-02/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-02 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-03/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-03 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-04/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-04 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-05/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-05 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-06/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-06 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-07/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-07 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-08/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-08 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-09/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-09 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-10/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-10 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada_smoke/run-01/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada_smoke/run-01 | 25 | 25 | 0 |
| experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada_smoke/run-02/SHA256SUMS | experimentos/resultados/raw/eficiencia_nominal_50u_5m_poblada_smoke/run-02 | 25 | 25 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01-attempt-02/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01-attempt-02 | 35 | 35 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01-attempt-03/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01-attempt-03 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-01 | 35 | 35 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-02/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-02 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-03/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-03 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04-attempt-02/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04-attempt-02 | 35 | 35 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04-attempt-03/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04-attempt-03 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-04 | 35 | 35 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-05/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-05 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-06-attempt-02/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-06-attempt-02 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-06/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-06 | 35 | 35 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-07/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-07 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-08/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-08 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-09/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-09 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-10/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-10 | 36 | 36 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/preflight/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/preflight | 8 | 8 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/preflight/dataset-metadata.json.sha256 | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/preflight | 1 | 1 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/preflight/dataset.csv.sha256 | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/preflight | 1 | 1 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-01/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-01 | 29 | 29 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-02/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-02 | 29 | 29 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-03/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-03 | 29 | 29 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-04/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-04 | 29 | 29 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-05/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-05 | 29 | 29 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-06/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-06 | 29 | 29 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-07/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-07 | 31 | 31 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-08/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-08 | 31 | 31 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-09/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-09 | 31 | 31 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-10/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-10 | 31 | 31 | 0 |
| experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada_smoke/SHA256SUMS | experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada_smoke | 21 | 21 | 0 |
| release/apk/SHA256SUMS.txt | release/apk | 1 | 1 | 0 |
| release/evidence/observabilidad/SHA256SUMS.txt | release/evidence/observabilidad | 23 | 23 | 0 |
| release/screenshots/SHA256SUMS.txt | release/screenshots | 10 | 10 | 0 |
