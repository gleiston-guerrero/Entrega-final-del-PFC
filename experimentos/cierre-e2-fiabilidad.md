# Cierre metodológico E2: fiabilidad, sesión y alcance de la evidencia

**Fecha de cierre documental:** 2026-09-15 (America/Guayaquil)
**Alcance:** consolidación trazable de evidencia ya producida; no se ejecutaron
nuevas repeticiones ni se modificaron raws o resultados históricos.

## Dictamen

La campaña histórica conserva sus diez repeticiones de una hora y el defecto
observado de expiración del JWT: 668.367 respuestas HTTP 401 sobre 889.868 GET
de negocio. Esa evidencia permanece como antecedente y no se reinterpreta como
si hubiese utilizado renovación de sesión.

La causa fue corregida mediante el mecanismo real de
`POST /api/v1/auth/refresh`, sin modificar el TTL productivo. Después del smoke
técnico se ejecutó la campaña correctiva completa: diez repeticiones válidas de
una hora, 50 usuarios y `spawn-rate` 10 usuarios/s, sobre el SHA experimental
`b94b7af7ebab2510c16eae0c70593664763de1e7`.

Las diez repeticiones correctivas contienen 896.964 GET de negocio, con
0 HTTP 401 y 0 HTTP 5xx. El análisis prerregistrado r2--r9 produce una tasa
HTTP 5xx media de 0,000000 %, desviación muestral 0,000000 % e IC95
[0,000000; 0,000000] %, por lo que E2 CUMPLE el criterio de límite superior
menor que 1 %.

Como métricas descriptivas, p95 presenta media 6,680642 ms e IC95
[6,532522; 6,828763] ms; p99 presenta media 9,849009 ms e IC95
[9,439893; 10,258124] ms. Estos percentiles no constituyen un criterio nuevo
de aceptación E2.

Los intentos fallidos o abortados permanecen preservados por separado y no se
reclasifican como observaciones válidas.

## Clasificación de la evidencia

### Campaña histórica completa

- Ruta: `raw/fiabilidad_nominal_50u_1h/rep-01` a `rep-10`.
- SHA experimental: `061a1050a94e1bd30d81b30c47c7e818005a33bb`.
- Diseño ejecutado: diez ventanas de aproximadamente 3.600 s, 50 usuarios y
  `spawn-rate` 10 usuarios/s.
- Población de negocio: `GET /api/v1/reservas` y
  `GET /api/v1/reservas/{id}`. Ningún GET se excluye por su estado HTTP.
- Censo reproducido desde `locust_stats.csv` y `locust_failures.csv`: 889.868
  GET, 668.367 respuestas HTTP 401 y 612 respuestas HTTP 5xx.
- El primer 401 queda acotado por el historial acumulado entre 902,396 s y
  929,048 s según la repetición. La aparición coincide con el TTL de 900 s más
  el escalonamiento de los usuarios.
- Las diez ejecuciones completaron su duración y conservaron evidencia, pero
  quedaron experimentalmente debilitadas para representar una hora sostenida
  de carga autenticada sobre Reservas/Solicitudes: tras expirar los tokens, una
  gran parte de los GET fue rechazada antes de ejecutar la operación de negocio.

### Defecto experimental detectado

El `locustfile.py` histórico hacía login una vez por usuario y reutilizaba el
access token sin renovarlo. El TTL configurado era 900 s. Los 668.367 HTTP 401
representan el 75,108555426 % de los GET históricos y no se eliminan del
denominador, de los fallos de Locust ni de la evidencia. Son una amenaza a la
validez de la carga efectiva, no errores de servidor 5xx.

### Corrección aplicada

El harness actual conserva `accessToken`, `refreshToken` y expiración; ejecuta
refresh preventivo, reemplaza ambos tokens cuando hay rotación y permite como
fallback un solo refresh y un solo reintento ante 401. Login y refresh conservan
nombres Locust separados de los GET de negocio. No se alargó el TTL ni se
alteró la configuración JWT productiva.

### Evidencia correctiva

La campaña oficial se conserva en:

`resultados/raw/fiabilidad_nominal_50u_1h_refresh/`

Las diez repeticiones válidas corresponden a:

| Rep. | Directorio válido | Intento | GET negocio | HTTP 401 | HTTP 5xx | p95 ms | p99 ms |
|---:|---|---:|---:|---:|---:|---:|---:|
| r1 | `rep-01-attempt-03` | 3 | 89.658 | 0 | 0 | 6,620457 | 9,827799 |
| r2 | `rep-02` | 1 | 89.685 | 0 | 0 | 6,704423 | 10,300085 |
| r3 | `rep-03` | 1 | 89.689 | 0 | 0 | 6,443099 | 9,093202 |
| r4 | `rep-04-attempt-03` | 3 | 89.691 | 0 | 0 | 7,060784 | 10,711798 |
| r5 | `rep-05` | 1 | 89.726 | 0 | 0 | 6,684224 | 9,806598 |
| r6 | `rep-06-attempt-02` | 2 | 89.721 | 0 | 0 | 6,664765 | 9,655038 |
| r7 | `rep-07` | 1 | 89.624 | 0 | 0 | 6,710125 | 9,970236 |
| r8 | `rep-08` | 1 | 89.718 | 0 | 0 | 6,600037 | 9,677521 |
| r9 | `rep-09` | 1 | 89.732 | 0 | 0 | 6,577682 | 9,577590 |
| r10 | `rep-10` | 1 | 89.720 | 0 | 0 | 6,831006 | 10,226293 |

El total oficial es de 896.964 GET de negocio. Los contadores finales de
Locust, incluyendo tráfico de sesión, registran 899.464 requests y 0 fallos.

Cada repetición válida conserva `metadata.json`, eventos raw,
`locust-final-stats.json`, estadísticas, logs y manifiesto SHA-256. Los
resultados oficiales se reconstruyen desde `locust_requests.csv`, sin depender
de snapshots periódicos incompletos de `locust_stats.csv`.

Los intentos inválidos o abortados permanecen preservados en directorios
separados. No se eliminan, renombran ni reclasifican como repeticiones válidas.

El smoke correctivo permanece separado y no forma parte de r1--r10 ni del
análisis estadístico r2--r9.

### Selección canónica del smoke

La selección contiene exclusivamente `start_utc.txt`, `end_utc.txt`,
`experimental_sha.txt`, `locust.log`, `locust_stats.csv`,
`locust_failures.csv` y `locust_exceptions.csv`, más `SHA256SUMS.txt`, que
verifica los siete archivos sin incluirse a sí mismo. Los hashes de cada copia
coinciden con los del raw original.

Los archivos fijan inicio `2026-09-13T04:32:45Z`, fin
`2026-09-13T04:57:45Z`, duración de 1.500 s y SHA experimental
`164914219f304d17d1a3e9a6989de4e3e9d0a17c`. Locust registra 50 usuarios,
ejecución hasta el límite temporal, 50 login sin fallos, 50 refresh sin fallos,
27.207 GET de listado con 151 fallos y 9.124 GET por id con 68 fallos. Los 219
fallos GET preservados son exclusivamente HTTP 500; no existe HTTP 401 en
`locust_failures.csv`. Esta evidencia se usa únicamente para verificar que el
mecanismo de refresh conserva autenticación durante una ejecución que supera el
TTL de 900 s; no sustituye ninguna repetición histórica u oficial.

## Métricas que no deben mezclarse

### 1. HTTP 401 de autenticación

Los 401 pertenecen a los GET intentados y permanecen en su población. Se
reportan como defecto experimental histórico porque revelan pérdida de sesión y
reducción de carga de negocio efectiva después del TTL. No se transforman en
5xx ni se excluyen para mejorar el resultado.

### 2. HTTP 5xx

Para cada repetición, la métrica primaria prerregistrada es:

`100 × GET de negocio con estado 5xx / GET de negocio`.

La campaña histórica permanece publicada como antecedente metodológico. Su
interpretación quedó limitada por la expiración del JWT y la aparición masiva
de HTTP 401 después del TTL.

La campaña correctiva elimina ese defecto observado. Sobre las repeticiones
centrales r2--r9:

| Métrica | n | Media | s muestral | IC95 | Interpretación |
|---|---:|---:|---:|---|---|
| Tasa HTTP 5xx | 8 | 0,000000 % | 0,000000 % | [0,000000; 0,000000] % | CUMPLE `<1 %` |
| p95 GET negocio | 8 | 6,680642 ms | 0,177173 ms | [6,532522; 6,828763] ms | INFORMATIVO |
| p99 GET negocio | 8 | 9,849009 ms | 0,489360 ms | [9,439893; 10,258124] ms | INFORMATIVO |

El límite superior del IC95 de HTTP 5xx es 0,000000 %, por debajo del 1 %
prerregistrado; por tanto, E2 cumple su criterio acotado en el escenario
correctivo medido.

p95 y p99 se reconstruyen directamente desde `locust_requests.csv` sobre todos
los GET de negocio, sin excluir observaciones por código HTTP, éxito, fallo o
latencia. Son métricas descriptivas y no constituyen nuevos criterios de
aceptación E2.

### 3. Población business GET

Se incluyen por identidad, con independencia del resultado:

- `GET /api/v1/reservas`;
- `GET /api/v1/reservas/{id}`, cuando tenga observaciones.

Se preservan como tráfico de sesión, pero se excluyen del denominador y de los
percentiles de negocio por pertenecer a Auth:

- `POST /api/v1/auth/login`;
- `POST /api/v1/auth/refresh`.

No se filtra un GET por responder 200, 401, 500 u otro código.

## Amenazas a la validez y acciones correctivas

La campaña histórica sufrió una amenaza de validez interna y de constructo:
después del TTL de 900 s una proporción elevada de GET fue rechazada por
autenticación antes de alcanzar la operación de negocio esperada.

La campaña correctiva aplicó el mecanismo real de refresh sin modificar el TTL.
Las diez repeticiones oficiales válidas completaron aproximadamente una hora,
mantuvieron tráfico autenticado y registraron 0 HTTP 401 y 0 HTTP 5xx sobre
896.964 GET de negocio.

Esto elimina, para el escenario correctivo medido, el defecto de sesión
observado en la campaña histórica. Sin embargo, persisten amenazas de validez
externa: la ejecución corresponde a una infraestructura, dataset y patrón de
carga controlados.

Además, la tasa HTTP 5xx no operacionaliza tiempo apto frente a tiempo total.
Por ello, el cumplimiento de E2 no permite inferir por sí solo una
disponibilidad de 99,5 %.

El smoke permanece excluido del análisis estadístico. Los intentos correctivos
no válidos se conservan para auditoría y no forman parte de r2--r9.

## Afirmaciones defendibles y límites

Se puede defender que:

1. la campaña histórica conserva diez ejecuciones completas de una hora y sus
   conteos siguen reproducibles desde los raws;
2. la campaña histórica sufrió un defecto de renovación que produjo 668.367
   HTTP 401 y debilitó la carga efectiva después del TTL;
3. la causa fue identificada y corregida mediante el mecanismo real de refresh;
4. la campaña correctiva contiene diez repeticiones oficiales válidas de una
   hora ejecutadas sobre el SHA
   `b94b7af7ebab2510c16eae0c70593664763de1e7`;
5. las diez repeticiones correctivas suman 896.964 GET de negocio, con
   0 HTTP 401 y 0 HTTP 5xx;
6. en r2--r9 la tasa HTTP 5xx tiene media 0,000000 % e IC95
   [0,000000; 0,000000] %, por lo que E2 cumple el criterio `<1 %`;
7. p95 y p99 correctivos se reconstruyen desde los eventos raw y se reportan
   únicamente como métricas descriptivas;
8. los intentos fallidos o abortados permanecen preservados y no se utilizan
   como muestras oficiales.

No se debe afirmar que:

1. las diez repeticiones históricas utilizaron refresh;
2. el smoke o los intentos inválidos forman parte de r2--r9;
3. p95 o p99 constituyen un nuevo criterio de aceptación E2;
4. cero HTTP 5xx equivale por sí solo a una disponibilidad de 99,5 %;
5. los resultados observados en esta VM garantizan idéntico comportamiento en
   cualquier infraestructura, dataset o patrón de carga futuro.
