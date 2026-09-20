# E4 correctiva: eficiencia poblada

Este protocolo post-evaluación prepara, pero no sustituye todavía, la evidencia
histórica. El estado de eficiencia permanece **NO CONCLUYENTE** hasta que se
conserven y analicen diez repeticiones reales.

Se reutiliza el dataset controlado de 20 reservas del preflight de
`fiabilidad_nominal_50u_1h_refresh_poblada`, verificando su SHA-256 antes de
carga. Es un dataset controlado post-evaluación; no se afirma que reconstruya
exactamente el dataset histórico.

Diseño: `eficiencia_nominal_50u_5m_poblada`, 50 usuarios, spawn-rate 10/s,
5 minutos, 10 repeticiones; análisis principal r2--r9. La población son todos
los eventos GET de `GET /api/v1/reservas` y `GET /api/v1/reservas/{id}`.
Login y refresh no entran. No se excluye ninguna observación por latencia,
éxito o código HTTP: 401 y 5xx se cuentan y permanecen en los percentiles.

Cada repetición exige duración completa, artefactos completos, ambos GET con
observaciones, dataset verificado y SHA de software/harness consistentes. Un
5xx no invalida por sí solo la repetición. p95/p99 se calculan nearest-rank
desde `locust_requests.csv`; para r2--r9 se usa IC95 t (df=7). Cumple si el
límite superior de p95 es menor que 500 ms y el de p99 menor que 750 ms.
