# Evidencia de renormalizacion - Correccion #20

Fecha de auditoria: 2026-09-20

Base auditada: `origin/main`

HEAD auditado: `0659e20f8434a9aaf6664bf08882f954eefba380`

## Alcance

El objetivo del punto #20 es asegurar que la verificacion de manifiestos sea
reproducible independientemente de la politica local de finales de linea.

La correccion actual mantiene:

- normalizacion general con `* text=auto eol=lf`;
- manifiesto global `experimentos/resultados/SHA256SUMS` como texto LF;
- evidencia raw protegida byte a byte con `experimentos/resultados/raw/** binary`;
- evidencia Arbiter protegida con `experimentos/resultados/arbiter/campaign/** binary`;
- evidencia Spark #17 protegida con `experimentos/evidencia-17/** binary`;
- evidencia smoke E2 protegida con `experimentos/evidencia-e2/smoke-refresh-25m/** binary`;
- `experimentos/evidencia-e2/smoke-refresh-25m/SHA256SUMS.txt` como texto LF,
  diffable y mergeable.

No se modifico evidencia cruda y no fue necesario regenerar hashes.

## Normalizacion

La prueba segura de renormalizacion se ejecuto en un checkout temporal desde el
HEAD auditado.

Resultado:

- `git add --renormalize .` produjo 0 archivos cambiados;
- el arbol versionado ya estaba normalizado;
- no hubo cambios sobre evidencia raw;
- no hubo necesidad de actualizar manifiestos.

El estado de finales de linea no presento archivos mixtos:

- `i/mixed`: 0;
- `w/mixed`: 0.

## Verificacion de manifiestos

La verificacion de lectura descubrio 37 manifiestos:

- entradas totales: 2657;
- LF: 2657/2657 OK;
- `core.autocrlf=true`: 2657/2657 OK;
- fallos: 0.

Tambien se compararon dos checkouts temporales del mismo commit:

- checkout con `core.autocrlf=false`;
- checkout con `core.autocrlf=true`;
- archivos comparados: 3242;
- diferencias de bytes: 0.

Estos resultados confirman que los manifiestos actuales son reproducibles sin
regenerar checksums.

## Evidencia Spark #17

Ruta: `experimentos/evidencia-17/**`

Estado:

- protegida como `binary/-text`;
- `comparacion.json` conserva bytes;
- `config.json` conserva bytes;
- `resumen.json` referencia los hashes correctos;
- `provenance.json` conserva bytes;
- manifiesto: 50/50 OK;
- resultado LF: OK;
- resultado con `core.autocrlf=true`: OK.

El defecto original de Spark por transformacion CRLF/LF ya no se reproduce.

## Smoke E2

Ruta: `experimentos/evidencia-e2/smoke-refresh-25m/**`

Estado:

- evidencia del directorio protegida como `binary/-text`;
- `SHA256SUMS.txt` declarado explicitamente como `text eol=lf diff merge`;
- `locust_stats.csv` conserva bytes;
- `locust_failures.csv` conserva bytes;
- `locust_exceptions.csv` conserva bytes;
- manifiesto: 7/7 OK;
- resultado LF: OK;
- resultado con `core.autocrlf=true`: OK.

El defecto original de 4/7 archivos fallando ya no se reproduce.

## Ramas remotas

La rama `origin/fix/issue-20-renormalizacion-isaias` corresponde a un enfoque
antiguo/rechazado de renormalizacion. Sigue publicada temporalmente, pero no
forma parte de `main` ni representa trabajo pendiente que deba integrarse para
cerrar el punto #20.

Su eliminacion remota queda como limpieza de cierre, no como requisito tecnico
de reproducibilidad.

La rama `origin/fix/eval2-32-iso25010-ivan` no se clasifica como obsoleta de
#20. Contiene trabajo activo/valido de otro entregable y no forma parte de esta
correccion.

## Conclusion

El estado actual de `origin/main` cumple la reproducibilidad de finales de linea:

- los manifiestos verifican en LF y con `core.autocrlf=true`;
- no hay archivos `mixed`;
- la evidencia cruda esta preservada byte a byte;
- Spark #17 y smoke E2 verifican correctamente;
- `git add --renormalize .` no produciria cambios.

La correccion de cierre elimina la regla inefectiva de `raw/*.txt` y declara
explicitamente el tratamiento del manifiesto smoke E2 como texto LF,
diffable y mergeable. Estas modificaciones no alteran evidencia cruda ni
requieren regenerar manifiestos o hashes.
