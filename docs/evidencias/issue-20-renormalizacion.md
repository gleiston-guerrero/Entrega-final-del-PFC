\# Evidencia de renormalización — Corrección #20



Fecha: 2026-09-17

Rama base: feature/entrega-4

HEAD base: 699c799



\## Configuración



La raíz del repositorio contiene:



`\* text=auto eol=lf`



La evidencia experimental original se preserva mediante:



`experimentos/resultados/raw/\*\* binary`



\## Ejecución



Se ejecutó:



`git add --renormalize .`



sobre el árbol versionado del HEAD indicado.



\## Resultado



La operación no produjo diferencias respecto del índice actual:



\- 0 archivos modificados por la renormalización;

\- 0 archivos staged;

\- 0 archivos bajo `experimentos/resultados/raw/\*\*` modificados;

\- no fue necesario regenerar manifiestos ni checksums.



Comprobaciones:



`git diff --cached --stat` → sin salida

`git diff --cached --name-only` → sin salida

`git diff --cached --name-only -- experimentos/resultados/raw` → sin salida

`git status --short` → sin salida



\## Conclusión



En el HEAD `699c799`, el árbol versionado ya se encontraba normalizado

conforme a las reglas vigentes de `.gitattributes`. La ejecución explícita

de `git add --renormalize .` confirmó que no quedaban cambios pendientes

de normalización y que la evidencia raw permanecía byte a byte sin cambios.
