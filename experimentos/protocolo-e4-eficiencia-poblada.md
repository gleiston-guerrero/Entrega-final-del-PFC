# E4 correctiva: eficiencia poblada

Este protocolo documenta la campaña correctiva post-evaluación
`eficiencia_nominal_50u_5m_poblada`. La campaña histórica se conserva sin
alteraciones y no se presenta como equivalente a esta corrección.

## Población y entorno

Se reutilizó el dataset controlado de 20 reservas generado para la campaña
correctiva de fiabilidad. Su `dataset.csv` tiene SHA-256:

`f2c07cc4698715939a9eaf6b47e694ccdf39fcd2de0502aec6164a90321f9b78`

Las diez repeticiones oficiales utilizaron exactamente ese mismo dataset. Es
una población controlada post-evaluación; no se afirma que reconstruya
exactamente el dataset histórico.

El software desplegado medido fue:

`dd2e1923d7635857f4020c7ef5c8b6efee363d7a`

La evidencia fue producida con el código de instrumentación identificado por:

`a60f523921d3be5a80d54f723997f60a613701ed`

## Diseño

- Escenario: `eficiencia_nominal_50u_5m_poblada`.
- Usuarios: 50.
- Spawn-rate: 10 usuarios/s.
- Duración nominal: 5 minutos.
- Repeticiones oficiales: 10.
- Análisis estadístico principal: r2--r9.
- Unidad inferencial: una repetición completa de 5 minutos (`n=8`).
- r1 y r10 se conservan como evidencia, pero no participan en el análisis
  principal.
- Las solicitudes individuales son observaciones dentro de cada repetición;
  no se tratan como réplicas estadísticas independientes.

La población de solicitudes está formada exclusivamente por todos los eventos:

- `GET /api/v1/reservas`
- `GET /api/v1/reservas/{id}`

Login y refresh pertenecen al harness y no forman parte de PI1. No se eliminan
observaciones por latencia, éxito o código HTTP. Los HTTP 401 y 5xx, si
existieran, permanecen en la población y en los percentiles.

p95 y p99 se reconstruyen desde `locust_requests.csv` mediante nearest-rank.
Para r2--r9 se utiliza IC95 t con `df=7` y
`t(0,975;7)=2,364624251`.

La regla de decisión es conservadora:

- p95 cumple si el límite superior de su IC95 es menor que 500 ms;
- p99 cumple si el límite superior de su IC95 es menor que 750 ms.

## Validez e integridad

Las diez repeticiones oficiales:

- completaron la duración prevista;
- conservaron evidencia completa;
- verificaron el dataset;
- mantuvieron el mismo software desplegado;
- mantuvieron el mismo harness;
- conservaron estado de despliegue antes y después;
- finalizaron con `locust_exit_code=0`;
- contienen observaciones de ambos GET de negocio;
- tienen `SHA256SUMS` verificable.

Los diez `locust_requests.csv` poseen diez SHA-256 distintos. Por tanto, los
raw de solicitudes no son copias byte a byte entre repeticiones. El dataset,
en cambio, conserva un único SHA-256 en las diez ejecuciones, como exige el
diseño controlado.

El analizador `experimentos/analizar_iso25010.py` valida automáticamente la
integridad SHA-256 de cada repetición, la coherencia cruzada de Git SHA,
software, dataset y harness, y rechaza una campaña con raw de solicitudes
duplicado. Estas garantías tienen pruebas unitarias negativas específicas.

## Resultado observado

Las diez repeticiones oficiales contienen 74.098 GET de negocio y registran
0 HTTP 401 y 0 HTTP 5xx.

Las ocho repeticiones principales r2--r9 contienen 59.278 GET de negocio.

| Métrica | n | Media | s muestral | Límite superior IC95 | Umbral | Resultado |
|---|---:|---:|---:|---:|---:|---|
| p95 GET negocio | 8 | 9,952465 ms | 0,426872 ms | 10,309339 ms | <500 ms | CUMPLE |
| p99 GET negocio | 8 | 19,744969 ms | 3,437219 ms | 22,618556 ms | <750 ms | CUMPLE |

Los resultados derivados reproducibles se conservan en:

- `resultados/iso25010-eficiencia-poblada.csv`;
- `resultados/iso25010-eficiencia-poblada.sha256`;
- `resultados/raw/eficiencia_nominal_50u_5m_poblada/rep-01..10/`.

Los dos smoke tests se conservan por trazabilidad, pero no forman parte del
análisis inferencial. `run-01` documenta el defecto inicial de verificación
del dataset y `run-02` valida la corrección previa a la campaña oficial.

## Incidencia operativa de almacenamiento

Después de r3 y antes de r4 se detectó crecimiento del log local `json-file`
del OTel Collector hasta aproximadamente 7,2 GB. Se preservó una muestra
final y se truncó únicamente ese archivo de log entre repeticiones.

No se reiniciaron los servicios backend, no se modificaron volúmenes ni datos
de la base y la intervención ocurrió fuera de una ventana de medición. La
trazabilidad se conserva en:

- `disk-maintenance-before-rep04.txt`;
- `otel-log-tail-before-rep04.txt`.

La intervención no se utiliza para excluir ni modificar ninguna repetición.
