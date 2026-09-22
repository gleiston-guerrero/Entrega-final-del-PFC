# Evidencia de renormalizacion - estado actual de la correccion #20

Fecha de auditoria: 2026-09-22

Base auditada: `origin/main`

HEAD auditado: `b461d7fef67def578ef41fc23a45bb05af6cd301`

## Alcance

El punto #20 verifica que los finales de linea y la verificacion de
manifiestos sean reproducibles entre plataformas. Esta auditoria documental
describe el estado de `main` en el HEAD indicado. No modifica evidencia, hashes,
manifiestos ni `.gitattributes`.

## `.gitattributes` vigente

La configuracion actual mantiene la normalizacion general:

```text
* text=auto eol=lf
```

Las rutas de evidencia protegidas byte a byte son:

- `experimentos/resultados/raw/**` como `binary`;
- `experimentos/evidencia-17/**` como `binary`;
- `experimentos/evidencia-e2/smoke-refresh-25m/**` como `binary`;
- `experimentos/resultados/arbiter/campaign/**` como `binary`;
- `experimentos/resultados/iso25010-correctiva-poblada.csv` como `-text`;
- `experimentos/resultados/analisis-e3.json` como `-text`.

El manifiesto de smoke E2 se mantiene como texto LF, con `diff` y `merge`
declarados:

```text
experimentos/evidencia-e2/smoke-refresh-25m/SHA256SUMS.txt text eol=lf diff merge
```

Existe un pendiente residual de configuracion: 97 rutas unicas cubiertas por
manifiestos siguen resolviendo a `text=auto`. Se concentran principalmente en
`experimentos/resultados/evidencia-e3-canonica/**`,
`experimentos/metrics/results/**`, `release/evidence/**`,
`release/screenshots/**` y otros resultados. Estas rutas no se consideran
danadas: verifican en clones limpios. Mientras sigan en `text=auto`, su
preservacion byte a byte depende de que los archivos se generen en LF.

## Poblacion actual de manifiestos

El verificador descubre actualmente:

- 56 manifiestos;
- 3319 entradas;
- 2172 rutas unicas.

Distribucion de atributos por ruta unica:

- 2071 rutas con `text=unset`/`binary`;
- 97 rutas con `text=auto`;
- 4 rutas con `text=set`.

Distribucion por entrada de manifiesto, incluyendo rutas repetidas:

- 3216 entradas con `text=unset`/`binary`;
- 99 entradas con `text=auto`;
- 4 entradas con `text=set`.

Por tanto, la cifra historica de 76 rutas `text=auto` ya no describe
`main`.

## Verificacion en clones limpios

Se compararon dos clones temporales limpios del mismo HEAD:

| Configuracion | Manifiestos | Entradas | OK | FAILED | `git add --renormalize .` |
|---|---:|---:|---:|---:|---:|
| `core.autocrlf=false` | 56 | 3319 | 3319 | 0 | 0 cambios |
| `core.autocrlf=true` | 56 | 3319 | 3319 | 0 | 0 cambios |

Estos resultados muestran que los blobs y los clones limpios son reproducibles
en ambos modos. No se regeneraron manifiestos ni hashes.

## Diferencia observada en el checkout Windows existente

La ejecucion sobre el checkout Windows de trabajo existente obtuvo:

- 56 manifiestos;
- 3319 entradas;
- 3268 OK;
- 51 mismatches.

Los 51 hashes esperados coinciden con los blobs Git correspondientes. La
diferencia esta en los bytes del working tree existente, principalmente por
finales CRLF en rutas que el blob almacena en LF. Por ello, el resultado es
especifico de ese working tree y no implica corrupcion del repositorio.

En ambos modos de los clones limpios, `git add --renormalize .` produjo cero
cambios. En el checkout real tampoco se modifico el indice durante esta
auditoria.

## Casos historicos de CRLF

Los dos archivos historicos conservan sus bytes CRLF tanto en el blob Git como
en el working tree:

- `experimentos/resultados/iso25010-correctiva-poblada.csv`: 11 finales CRLF;
- `experimentos/resultados/analisis-e3.json`: 368 finales CRLF.

Ambos tienen `text=unset` (`-text` en `.gitattributes`), por lo que Git no los
convierte automaticamente entre LF y CRLF. El hash SHA-256 del working tree
coincide con el hash del contenido del blob en ambos casos.

## Ramas relacionadas con #20

Las ramas relacionadas que permanecen publicadas son historicas y estan detras
de `main`, con cero commits por delante:

- `origin/fix/issue-20-renormalizacion-isaias-v2`;
- `principal/fix/issue-20-renormalizacion-isaias`;
- `principal/fix/issue-20-renormalizacion-isaias-v2`.

No hay trabajo de #20 por delante de `main` pendiente de integrar.

## Estado de la correccion

La proteccion de `raw/**`, evidencia-17, smoke E2, Arbiter y los dos casos
historicos CRLF esta vigente. La verificacion en clones limpios es reproducible
con `core.autocrlf=false` y `core.autocrlf=true`: los 56 manifiestos y sus
3319 entradas verificaron 3319/3319 en ambos entornos, y la prueba de
`git add --renormalize .` produjo 0 cambios.

Las 97 rutas que actualmente resuelven a `text=auto` fueron auditadas de forma
explicita. No se encontro ninguna ruta que produjera diferencias de hash,
perdida de bytes, divergencias entre clones limpios ni cambios durante la
renormalizacion. Por tanto, no constituyen un defecto reproducible del estado
actual del repositorio.

Mantener reglas mas restrictivas para esas rutas podria reforzar de forma
preventiva la preservacion byte a byte de evidencia futura, pero no es
necesario para reproducir ni verificar la evidencia versionada actualmente.

No se requiere regenerar manifiestos, modificar hashes, renormalizar archivos
ni realizar cambios adicionales en `.gitattributes` para el estado auditado.
