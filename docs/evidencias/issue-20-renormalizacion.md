# Evidencia de renormalización — Corrección #20



Fecha: 2026-09-17

Rama base: feature/entrega-4

HEAD base: 699c799



## Configuración



La raíz del repositorio contiene:



`* text=auto eol=lf`



La evidencia experimental original se preserva mediante:



`experimentos/resultados/raw/** binary`



## Ejecución



Se ejecutó:



`git add --renormalize .`



sobre el árbol versionado del HEAD indicado.



## Resultado



La operación no produjo diferencias respecto del índice actual:



- 0 archivos modificados por la renormalización;

- 0 archivos staged;

- 0 archivos bajo `experimentos/resultados/raw/**` modificados;

- no fue necesario regenerar manifiestos ni checksums.



Comprobaciones:



`git diff --cached --stat` → sin salida

`git diff --cached --name-only` → sin salida

`git diff --cached --name-only -- experimentos/resultados/raw` → sin salida

`git status --short` → sin salida



## Conclusión



En el HEAD `699c799`, el árbol versionado ya se encontraba normalizado

conforme a las reglas vigentes de `.gitattributes`. La ejecución explícita

de `git add --renormalize .` confirmó que no quedaban cambios pendientes

de normalización y que la evidencia raw permanecía byte a byte sin cambios.

## Verificación final en worktree limpio

Se realizó una validación adicional sobre un worktree limpio creado desde el commit
`351642c63cfa41884cdeb9fe91288c0bd6615564`.

La creación del worktree se ejecutó con soporte de rutas largas de Git debido a las
limitaciones de longitud de rutas de Windows.

### Estado de finales de línea

Para:

`experimentos/resultados/iso25010.csv`

Git reportó:

`i/lf w/lf attr/text=auto eol=lf`

Los atributos efectivos fueron:

- `text: auto`
- `eol: lf`

El SHA-256 físico del archivo fue:

`ceee0ab3200aaccbcc1e3ed534c3a721727bfc7cc25f666535a4be6e6927d866`

que coincide con el valor registrado en
`experimentos/resultados/SHA256SUMS`.

### Regeneración del manifiesto

Se recalcularon las 468 entradas del manifiesto a partir de los archivos del
worktree limpio y se generó una copia temporal fuera del repositorio.

Resultados:

- `MANIFEST_LINES=468`
- `CURRENT_SHA256=af61ab37b44a7a789e8658fd5ba8ef46b535075c989260b0ca0f3f03ea06789f`
- `REGENERATED_SHA256=af61ab37b44a7a789e8658fd5ba8ef46b535075c989260b0ca0f3f03ea06789f`
- `DIFF_LINES=0`
- discrepancias: ninguna

El worktree permaneció limpio al finalizar la verificación.

### Conclusión

La regeneración completa del manifiesto sobre un checkout limpio produce
exactamente el mismo contenido actualmente versionado. Por tanto, las reglas
de normalización vigentes son reproducibles y el manifiesto corresponde al
contenido normalizado del repositorio.
