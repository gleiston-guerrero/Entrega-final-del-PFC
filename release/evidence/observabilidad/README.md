# Evidencia versionada de observabilidad

Este directorio conserva exportaciones runtime de Prometheus, Tempo y Loki.
Los JSON son resultados historicos y no se regeneran ni se reinterpretan para
hacer coincidir una captura posterior.

## Consultas de metricas

`09-panel5-cpu.json` y `10-panel5-memory.json` son **sondeos de presencia de
serie**: usan `count(...)` sobre las familias de CPU y memoria de cAdvisor. No
reproducen el valor mostrado por el panel 5, cuyas consultas calculan CPU por
contenedor con `rate(...)` y memoria con `sum by (container)`.

`11-panel6-mobile-count.json` es un **sondeo de presencia y acumulado** de la
familia movil mediante `sum(..._count)`. No es la consulta del panel 6, que
calcula el p95 con `histogram_quantile(...)`. `12-panel6-mobile-p95.json`
conserva la consulta del p95 del panel y documenta `0.151554183275` s en una
consulta posterior a la captura; `11` documenta 408 observaciones en esa misma
serie temporal posterior.

Las demas exportaciones de panel deben interpretarse segun la consulta `query`
que contienen y no como una reproduccion automatica de la captura.

## Trazas y correlacion

La numeracion historica salta de `13-tempo-search.json` a
`16-tempo-reservas-search.json`: no existen exportaciones `14` ni `15` en este
conjunto versionado. No se crean archivos ficticios para completar la
secuencia.

`22-loki-trace-correlated.json` conserva una busqueda Loki sin resultados
(`result: []`, cero lineas); por tanto no es evidencia positiva de correlacion.
La correlacion positiva documentada usa el mismo trace ID
`3302a606e9fb236618a03f4b06b5a6a7` en `23-loki-business-http.json`, donde
aparece `GET /api/v1/laboratorios -> 200`, y en
`24-tempo-correlated-trace.json`.

El manifiesto `SHA256SUMS.txt` cubre unicamente los JSON de este directorio;
este README es inventario interpretativo y no altera esos hashes.
