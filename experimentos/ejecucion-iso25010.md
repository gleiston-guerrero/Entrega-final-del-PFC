# Ejecución reproducible ISO 25010 de Freddy

## Ejecutar una repetición

Eficiencia, 50 usuarios durante 5 minutos:

```powershell
powershell -ExecutionPolicy Bypass -File experimentos/ejecutar_iso25010.ps1 -Escenario eficiencia_nominal_50u_5m -Repeticion 1 -HostObjetivo http://localhost:8080
```

Fiabilidad, 50 usuarios durante 1 hora:

```powershell
powershell -ExecutionPolicy Bypass -File experimentos/ejecutar_iso25010.ps1 -Escenario fiabilidad_nominal_50u_1h -Repeticion 1 -HostObjetivo http://localhost:8080
```

Campaña correctiva E2 con renovación de sesión, en una ruta independiente:

```powershell
powershell -ExecutionPolicy Bypass -File experimentos/ejecutar_iso25010.ps1 -Escenario fiabilidad_nominal_50u_1h_refresh -Repeticion 1 -HostObjetivo http://localhost:8080
```

En Ubuntu 24.04 no se presupone la instalación de PowerShell. El launcher Bash
nativo equivalente para la campaña correctiva es:

```bash
bash experimentos/ejecutar_iso25010.sh --scenario fiabilidad_nominal_50u_1h_refresh --repetition 1 --host http://localhost:8080
```

Ambos launchers escriben exclusivamente en
`experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh/rep-NN/`, rechazan
sobrescrituras y preservan el código real de Locust en metadata. La salida tabular
correctiva se registra separadamente en `resultados/iso25010-correctiva.csv`; no se
modifican las filas históricas de `resultados/iso25010.csv`.

El primer intento conserva el nombre `rep-NN`. Si una ejecución queda inválida, su
evidencia no se borra ni sobrescribe: el reintento se declara con `-Intento 2` en
PowerShell o `--attempt 2` en Bash y se almacena como
`rep-NN-attempt-02`. Metadata y CSV separan la repetición estadística del intento;
solo un intento que complete todas las validaciones puede registrarse.

El host es obligatorio y configurable. Para la prueba integrada local debe ser el API
Gateway en `http://localhost:8080`. La herramienta no inicia servicios. Antes de una
ejecución real se debe instalar `tests/load/requirements.txt` y verificar el ambiente.

## Evidencia generada

Cada repetición real usa:

```text
experimentos/resultados/raw/<escenario>/rep-NN/
```

Locust genera `locust_stats.csv`, historial, fallos, excepciones, HTML y log. El launcher
también conserva las consultas y respuestas Prometheus, salud antes/después, estadísticas
Docker, estado de CockroachDB, logs de Reservas, huella del despliegue y manifiesto del
entorno. `metadata.json` registra rama, SHA, estado Git, versiones, ventana UTC, duración
real y planificada, código real de Locust y señales separadas de ejecución y evidencia.

Las campañas históricas de Entrega 4 pueden conservar una selección canónica
compacta cuando los derivados completos permanecen en el entorno de ejecución.
La campaña correctiva `eficiencia_nominal_50u_5m_poblada`, en cambio, conserva
dentro de su árbol versionable los artefactos capturados por repetición,
incluidos eventos individuales, estadísticas, historial, reporte HTML, logs,
metadata y trazas de integridad.

La procedencia y alcance de cada paquete se documentan en
`resultados/RESUMEN-ISO25010-E4.md`. La campaña poblada de eficiencia dispone
además de `resultados/iso25010-eficiencia-poblada.sha256`, que cubre el derivado
y su paquete de evidencia.

## Obtener métricas reales

Para PI1, la campaña histórica conserva el análisis por identidad del request en
`locust_stats.csv` y la fila `Aggregated` únicamente como antecedente. Esta última
mezcla GET de Reservas/Solicitudes con operaciones de autenticación y no define la
población del cierre correctivo.

En la campaña post-evaluación `eficiencia_nominal_50u_5m_poblada`, el resultado
reproducible se reconstruye desde cada evento de `locust_requests.csv`. Pertenecen
a la población todos los eventos:

- `GET /api/v1/reservas`;
- `GET /api/v1/reservas/{id}`.

Login y refresh pertenecen al harness y quedan fuera de PI1. No se filtran
observaciones por código HTTP, latencia ni éxito/fallo: toda respuesta de los dos
GET incluidos permanece en la población. p95 y p99 se calculan mediante
nearest-rank dentro de cada repetición.

La unidad inferencial posterior es la repetición completa: r2--r9 forman `n=8`;
r1 y r10 se conservan como evidencia. Las solicitudes individuales no se tratan
como réplicas estadísticas independientes.

Los fallos de Locust no se copian automáticamente a `failures`: pueden incluir errores
de contenido o conectividad. Para Freddy, `failures` significa exclusivamente respuestas
HTTP 5xx. Al finalizar la repetición se ejecuta en Prometheus la consulta guardada en
`prometheus-5xx-count.promql`, usando como instante de evaluación el fin UTC registrado.
Su respuesta se conserva automáticamente como `prometheus-5xx-result.txt`.

El porcentaje 5xx se obtiene con la consulta exacta guardada por la herramienta:

```promql
100 * sum(increase(http_server_requests_seconds_count{job="reservas-solicitudes-service",status=~"5.."}[DURACION])) / clamp_min(sum(increase(http_server_requests_seconds_count{job="reservas-solicitudes-service"}[DURACION])), 1)
```

`DURACION` es `5m` o `1h` según el escenario. No se debe sustituir este porcentaje por
el failure rate general de Locust.

## Registrar una fila verificada

Después de conservar las evidencias reales:

```powershell
python experimentos/registrar_iso25010.py --scenario fiabilidad_nominal_50u_1h --repetition 2 --total-requests <TOTAL_REAL> --http-5xx <CONTEO_5XX_REAL> --p95-ms <P95_REAL> --p99-ms <P99_REAL> --evidence-dir experimentos/resultados/raw/fiabilidad_nominal_50u_1h/rep-02
```

El importador calcula `failure_rate_percent`, exige la hora completa, entorno estable,
árbol Git inicialmente limpio y evidencia completa, y rechaza sobrescribir filas. El
código real de Locust no decide por sí solo la validez: una hora completa con HTTP 500
reales es válida y conserva esos errores; una ejecución abortada o incompleta se rechaza.
Las repeticiones 1 y 10 se conservan, pero el analizador las excluye.
