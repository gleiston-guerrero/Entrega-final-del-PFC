# Addendum post-evaluación E2 — campaña correctiva con población no degenerada

**Fecha:** 2026-09-19 (America/Guayaquil)  
**Elemento corregido:** #31 — Escenario de fiabilidad ejecutado  
**Naturaleza:** addendum definido antes del nuevo smoke y antes de las nuevas
repeticiones oficiales.

## Motivo

La evaluación posterior de la campaña correctiva
`fiabilidad_nominal_50u_1h_refresh` detectó una amenaza de validez no advertida
durante su ejecución: el listado `GET /api/v1/reservas?pagina=0&tamanio=20`
respondía con una página vacía de aproximadamente 105 bytes.

Como consecuencia, el usuario Locust no obtenía UUID de reservas y la tarea
`GET /api/v1/reservas/{id}` no se ejercitaba durante aquella campaña. Por tanto,
los resultados históricos permanecen preservados, pero no se reinterpretan como
evidencia de carga representativa sobre ambos GET de negocio.

Este addendum no modifica ni sobrescribe el prerregistro histórico. Define una
nueva ejecución post-evaluación destinada específicamente a corregir la
población degenerada.

## Desviación declarada respecto del prerregistro original

El prerregistro correctivo anterior indicaba "misma infraestructura, datos y
consultas nominales". El dataset exacto utilizado en la campaña histórica no se
puede reconstruir de forma verificable a partir de la evidencia disponible.

Por ello, la nueva ejecución utilizará una **población correctiva nueva,
controlada y explícitamente documentada**, creada antes de medir mediante el
flujo real de negocio:

1. autenticación de `demo.docente`;
2. creación de solicitud;
3. transición a revisión por `demo.admin.piso`;
4. aprobación;
5. creación de reserva `PROGRAMADA`.

Esta diferencia limita la comparabilidad estricta con la campaña histórica y se
declarará en cualquier conclusión posterior. No se afirmará que el nuevo dataset
es idéntico al histórico.

## Dataset correctivo congelado

La población contiene exactamente:

- 20 reservas;
- 20 UUID de reserva distintos;
- 20 fechas distintas;
- fechas entre 2026-11-03 y 2026-11-30;
- estado de reserva `PROGRAMADA`;
- solicitud asociada en estado `APROBADA`;
- mismo docente, laboratorio, materia y periodo lectivo;
- horario 08:00–09:00;
- creación mediante API, sin `INSERT` SQL directo.

SHA-256 canónico de `dataset.csv`:

`f2c07cc4698715939a9eaf6b47e694ccdf39fcd2de0502aec6164a90321f9b78`

Antes de carga se verificó mediante API:

- login HTTP 200;
- `expiresIn = 900`;
- listado HTTP 200;
- `contenido_count = 20`;
- `totalElementos = 20`;
- tamaño de respuesta = 8965 bytes;
- `GET /api/v1/reservas/{id}` HTTP 200;
- reserva consultada en estado `PROGRAMADA`.

También se verificaron los 20 UUID individualmente antes del redeploy:
20 intentados, 20 HTTP 200 y 0 fallos.

## Software experimental

El software medido corresponde al SHA:

`dd2e1923d7635857f4020c7ef5c8b6efee363d7a`

Los cinco servicios participantes se desplegaron desde imágenes GHCR con ese
mismo SHA:

- api-gateway;
- auth-service;
- usuarios-service;
- academico-laboratorios-service;
- reservas-solicitudes-service.

Después del redeploy los cinco servicios quedaron `healthy` y el dataset
mantuvo sus 20 reservas.

El `tests/load/locustfile.py` usado por el escenario tiene SHA-256:

`079e39c46161aaf5dec41cc3ac4744d2f937e4f39455806d20ee35720edb6f3b`

## Smoke técnico nuevo

Antes de las diez repeticiones se ejecutará un nuevo smoke independiente del
smoke histórico.

Ruta prevista:

`experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada_smoke/`

Duración prevista: 1500 s.

Carga:

- 50 usuarios;
- spawn-rate 10 usuarios/s;
- mismo `tests/load/locustfile.py`;
- Gateway `http://127.0.0.1:8080`.

El smoke debe demostrar, como mínimo:

1. login real exitoso;
2. al menos un `POST /api/v1/auth/refresh`;
3. ejecución de GET después de t >= 900 s;
4. `GET /api/v1/reservas` con observaciones;
5. `GET /api/v1/reservas/{id}` con observaciones mayores que cero;
6. mantenimiento de tráfico hacia Reservas/Solicitudes después del TTL;
7. preservación íntegra de fallos, 401 y 5xx, si aparecen.

El smoke no forma parte de r1--r10 y no participa en medias, desviaciones ni
intervalos de confianza.

## Nueva campaña oficial

Solo si el smoke anterior demuestra una población no degenerada se ejecutarán
10 repeticiones independientes de una hora en:

`experimentos/resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/rep-01`
a
`rep-10`.

Se mantienen las reglas estadísticas ya prerregistradas:

- 50 usuarios;
- spawn-rate 10 usuarios/s;
- 3600 s por repetición;
- r1 y r10 preservadas;
- análisis principal r2--r9;
- IC95 con distribución t, df = 7;
- métrica primaria: porcentaje HTTP 5xx sobre todos los GET de negocio;
- criterio: límite superior del IC95 menor que 1 %;
- p95 y p99 únicamente descriptivos;
- login y refresh fuera del denominador de GET de negocio;
- ninguna observación desfavorable será eliminada por su resultado.

Los intentos abortados o inválidos, si ocurren, se preservarán y justificarán;
no serán borrados ni reescritos.
