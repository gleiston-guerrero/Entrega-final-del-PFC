# Reconciliación de `provenance.json` (corrección #17)

`provenance.json` declara `git_head = 21d2d3e19c68546638e2760074cd35ccd6c05402`
("feat(spark): materializar pipeline y preparar medicion de speedup",
2026-09-16T12:41:28-05:00). Ese commit **no** corresponde a las fuentes
realmente medidas: al comparar, byte a byte, los blobs de Git referenciados
en `source_sha256` contra el árbol de ese commit, ninguno coincide.

## Evidencia contrastada

Para cada ruta de `source_sha256` se calculó el SHA256 del blob de Git en el
commit declarado y se comparó con el valor registrado:

| Ruta | SHA256 registrado | SHA256 en `21d2d3e` | ¿Coincide? |
| --- | --- | --- | --- |
| `experimentos/run_comparison.py` | `4207ea92…d7c87a` | `0fdeb68a…8a75c877e` | No |
| `spark/pipeline.py` | `93d11b9f…3c1bef8` | (blob `db236b0c`, distinto de `51fb4726` registrado en HEAD) | No |
| `spark/baseline.py` | `c88780f2…4400705` | (blob `877660e7`, distinto de `89248d1e` registrado en HEAD) | No |
| `experimentos/analyze_speedup.py` | `e0333c6b…d38579a1f35` | (blob `ed75b171`, distinto de `fcb51c40` registrado en HEAD) | No |

En cambio, los cuatro archivos coinciden exactamente (mismo blob de Git) con
el estado del commit `197ce3305c821a37c788f4c8f7a783996121f6cc`
("feat(spark): registrar benchmark real y analisis de speedup",
2026-09-16T20:07:29-05:00):

| Ruta | Blob en `197ce33` | Blob en `21d2d3e` (declarado) |
| --- | --- | --- |
| `experimentos/run_comparison.py` | `232978e3…` | `a6c08ae7…` (distinto) |
| `spark/pipeline.py` | `51fb4726…` | `db236b0c…` (distinto) |
| `spark/baseline.py` | `89248d1e…` | `877660e7…` (distinto) |
| `experimentos/analyze_speedup.py` | `fcb51c40…` | `ed75b171…` (distinto) |

`21d2d3e` es ancestro directo de `197ce33` (`git merge-base --is-ancestor`
confirma esta relación) y `197ce33` es exactamente el commit siguiente que
modifica estos cuatro archivos. La cronología también es consistente: el
lote se generó entre 2026-09-17T00:21Z y 2026-09-17T00:43Z, es decir,
**después** de `197ce33` (2026-09-16T20:07Z) y antes del merge que hoy es
HEAD de `main` (2026-09-18T09:26Z, posterior a la propia evidencia).

## Conclusión

El `git_head` real de las fuentes usadas para esta evidencia es
`197ce3305c821a37c788f4c8f7a783996121f6cc`, no `21d2d3e19c68546638e2760074cd35ccd6c05402`
como declara `provenance.json`. El registro original de `git_head` quedó un
commit desactualizado (probablemente por captura del `HEAD` antes del commit
que introdujo el orquestador y el script de análisis definitivos, o por un
error en el script generador en esa ejecución particular).

No se modifica `provenance.json` (evidencia cruda histórica). Este archivo
derivado documenta la reconciliación y debe considerarse la referencia
correcta para auditoría de procedencia de la corrección #17.

**Nivel de certeza:** alto (demostrado por comparación byte a byte de blobs
de Git, no por inferencia).
