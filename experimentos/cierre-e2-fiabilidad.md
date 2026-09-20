# Cierre metodológico E2: fiabilidad, sesión y alcance de la evidencia

**Fecha de cierre documental actualizado:** 2026-09-20 (America/Guayaquil)
**Alcance:** cierre de la corrección #31 mediante una nueva campaña poblada
post-evaluación, preservando sin reescritura las campañas y los intentos
históricos.

## Dictamen

La evidencia de fiabilidad debe interpretarse cronológicamente en tres campañas
distintas. No se elimina ni se sustituye ningún raw histórico.

### 1. Campaña histórica original

La campaña original se conserva en:

`resultados/raw/fiabilidad_nominal_50u_1h/`

Fue ejecutada sobre el SHA:

`061a1050a94e1bd30d81b30c47c7e818005a33bb`

Sus diez repeticiones de aproximadamente una hora contienen 889.868 GET de
negocio, 668.367 respuestas HTTP 401 y 612 respuestas HTTP 5xx.

El harness histórico hacía login una vez y reutilizaba el access token sin
renovación. Con un TTL de 900 s, la expiración de la sesión produjo una pérdida
masiva de carga autenticada después del TTL. Los 401 permanecen en la evidencia
y no se eliminan ni se reinterpretan como 5xx.

Esta campaña constituye el antecedente que motivó la incorporación del flujo
real `POST /api/v1/auth/refresh`.

### 2. Campaña correctiva anterior con refresh, pero dataset vacío

La primera campaña con renovación de sesión se conserva en:

`resultados/raw/fiabilidad_nominal_50u_1h_refresh/`

Fue ejecutada sobre el SHA experimental:

`b94b7af7ebab2510c16eae0c70593664763de1e7`

La campaña es una ejecución real y sus raws se preservan. Sus diez repeticiones
seleccionadas suman 896.964 GET de negocio, con 0 HTTP 401 y 0 HTTP 5xx.

Sin embargo, esta campaña **no se utiliza como cierre definitivo de #31**.

La auditoría posterior comprobó que el listado devolvía una página vacía durante
las repeticiones seleccionadas. En consecuencia, el harness no obtenía IDs de
reservas y `GET /api/v1/reservas/{id}` no fue ejercitado. Por tanto, la carga no
reprodujo las mismas consultas de negocio que la campaña histórica poblada.

Sus resultados de 0 % HTTP 5xx y sus percentiles anteriores se conservan
exclusivamente como antecedente histórico de una ejecución con refresh sobre un
dataset degenerado. No se presentan como demostración de corrección definitiva
del escenario E2.

### 3. Campaña correctiva poblada post-evaluación

Para resolver la degeneración anterior se ejecutó una nueva campaña, conservada
en:

`resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/`

El software desplegado y medido corresponde al SHA:

`dd2e1923d7635857f4020c7ef5c8b6efee363d7a`

La campaña contiene diez repeticiones de aproximadamente una hora, 50 usuarios
y `spawn-rate` 10 usuarios/s. El harness conserva login, refresh preventivo y el
fallback de un único refresh y reintento ante 401.

Los cinco servicios medidos permanecieron saludables al cierre de las
repeticiones.

## Dataset correctivo y comparabilidad

No fue posible demostrar una reconstrucción exacta del dataset histórico
original. Por ello, la campaña nueva no se presenta como una réplica estricta
del conjunto de datos histórico.

Se fijó una **nueva población correctiva controlada post-evaluación** con 20
reservas visibles para el usuario de prueba. La evidencia del dataset se
conserva en el preflight de la campaña y su archivo `dataset.csv` tiene SHA-256:

`f2c07cc4698715939a9eaf6b47e694ccdf39fcd2de0502aec6164a90321f9b78`

La población permaneció estable durante las ejecuciones de solo lectura.

Esta desviación se declara expresamente: la campaña poblada corrige la
degeneración de la tabla vacía y permite ejercitar ambas consultas nominales,
pero no autoriza una comparación causal estricta con el dataset histórico.

## Población de negocio ejecutada

La población oficial incluye, por identidad y sin filtrar por resultado:

- `GET /api/v1/reservas`;
- `GET /api/v1/reservas/{id}`.

Login y refresh pertenecen a Auth y se contabilizan por separado.

Las diez repeticiones pobladas contienen:

- 670.972 GET de listado;
- 224.164 GET por id;
- **895.136 GET de negocio en total**;
- 0 HTTP 401;
- 42 HTTP 5xx.

Cada repetición contiene tráfico real por id, por lo que la carga ya no es
degenerada.

| Rep. | GET negocio | GET por id | HTTP 401 | HTTP 5xx | p95 ms | p99 ms |
|---:|---:|---:|---:|---:|---:|---:|
| r1 | 89.426 | 22.605 | 0 | 0 | 11,442185 | 23,211503 |
| r2 | 89.512 | 22.380 | 0 | 0 | 10,937077 | 21,817036 |
| r3 | 89.582 | 22.540 | 0 | 0 | 11,479889 | 22,765938 |
| r4 | 89.568 | 22.442 | 0 | 0 | 11,002075 | 23,860754 |
| r5 | 89.511 | 22.649 | 0 | 0 | 11,148107 | 23,128024 |
| r6 | 89.500 | 22.308 | 0 | 0 | 11,348761 | 24,511521 |
| r7 | 89.550 | 22.333 | 0 | 1 | 11,168729 | 23,518065 |
| r8 | 89.485 | 22.322 | 0 | 21 | 11,513912 | 27,120606 |
| r9 | 89.391 | 22.348 | 0 | 20 | 11,453620 | 24,838927 |
| r10 | 89.611 | 22.237 | 0 | 0 | 11,297333 | 21,675963 |

Los HTTP 5xx observados no se eliminan: r7 conserva 1, r8 conserva 21 y r9
conserva 20.

## Persistencia de carga después del TTL

El tráfico por id continúa después de 900 s en todas las repeticiones. Los
conteos de `GET /api/v1/reservas/{id}` posteriores a 900 s son:

| Rep. | GET negocio después de 900 s | GET por id después de 900 s |
|---:|---:|---:|
| r1 | 67.191 | 17.002 |
| r2 | 67.214 | 16.819 |
| r3 | 67.184 | 16.942 |
| r4 | 67.216 | 16.837 |
| r5 | 67.127 | 16.959 |
| r6 | 67.199 | 16.710 |
| r7 | 67.187 | 16.772 |
| r8 | 67.136 | 16.755 |
| r9 | 67.096 | 16.691 |
| r10 | 67.266 | 16.742 |

Esto demuestra que la campaña poblada mantiene tráfico autenticado y consultas
por id más allá del TTL de 900 s sin reproducir el defecto masivo de HTTP 401
de la campaña histórica.

## Regla de validez y códigos de salida Locust

La validez de una repetición se determina por la ejecución completa de la
ventana, la carga prevista, la existencia de tráfico de negocio y por id,
tráfico posterior a 900 s y preservación de la evidencia.

El código de salida de Locust se registra, pero **no se usa por sí solo para
descartar una repetición cuando es distinto de cero debido a fallos HTTP
observados**. Hacerlo excluiría precisamente la variable de respuesta que se
pretende medir.

Por esa razón:

- r1-r6 finalizaron con exit code 0;
- r7 finalizó con exit code 1 y conserva 1 HTTP 5xx;
- r8 finalizó con exit code 1 y conserva 21 HTTP 5xx;
- r9 finalizó con exit code 1 y conserva 20 HTTP 5xx;
- r10 finalizó con exit code 0.

La enmienda metodológica está preservada en:

`resultados/raw/fiabilidad_nominal_50u_1h_refresh_poblada/enmienda-criterio-validez-locust.md`

No se elimina ninguna observación desfavorable.

## Análisis estadístico principal r2--r9

Conforme al diseño prerregistrado, r1 y r10 se preservan como controles y el
análisis estadístico principal utiliza r2--r9.

Las ocho repeticiones centrales contienen:

- 536.777 GET de listado;
- 179.322 GET por id;
- **716.099 GET de negocio**;
- 0 HTTP 401;
- **42 HTTP 5xx**.

La métrica primaria es:

`100 × GET de negocio con estado 5xx / GET de negocio`

Se aplica el IC95 Student t con `df=7` y
`t(0,975;7)=2,364624251`.

| Métrica | n | Media | s muestral | IC95 | Interpretación |
|---|---:|---:|---:|---|---|
| Tasa HTTP 5xx | 8 | 0,005870 % | 0,010535 % | [-0,002938; 0,014677] % | **CUMPLE** `<1 %` |
| p95 GET negocio | 8 | 11,256521 ms | 0,223526 ms | [11,069649; 11,443394] ms | INFORMATIVO |
| p99 GET negocio | 8 | 23,945109 ms | 1,602666 ms | [22,605247; 25,284971] ms | INFORMATIVO |

El límite inferior negativo de la tasa es una consecuencia matemática del
intervalo t no acotado aplicado a las ocho tasas por repetición; se reporta sin
truncarlo retrospectivamente. La regla de decisión usa el límite superior.

Como `0,014677 % < 1 %`, **E2 CUMPLE el criterio acotado de HTTP 5xx en la
campaña poblada medida**.

p95 y p99 son métricas descriptivas. No constituyen criterios adicionales de
aceptación para esta campaña.

## Reproducibilidad del resultado

El consolidado nuevo es:

`resultados/iso25010-correctiva-poblada.csv`

El análisis se reproduce con:

`python3 experimentos/analizar_iso25010.py experimentos/resultados/iso25010-correctiva-poblada.csv`

El analizador reconstruye `total_requests`, HTTP 5xx, p95 y p99 directamente
desde cada `locust_requests.csv` y exige que coincidan con el CSV consolidado.

Una prueba controlada sobre una copia temporal de `rep-02` añadió un evento de
negocio artificial. El analizador terminó con código 2 y rechazó el consolidado
con `total_requests no coincide con raw`. El hash del raw real permaneció
inalterado y su `SHA256SUMS` continuó verificando.

## Integridad

Cada una de las diez repeticiones pobladas conserva su propio `SHA256SUMS`.

El manifiesto global:

`resultados/SHA256SUMS`

contiene 1.339 entradas verificables. Entre ellas se encuentran:

- los 550 archivos actualmente versionados de
  `raw/fiabilidad_nominal_50u_1h_refresh/`;
- `iso25010-correctiva.csv`;
- las 319 evidencias de
  `raw/fiabilidad_nominal_50u_1h_refresh_poblada/`;
- `iso25010-correctiva-poblada.csv`.

La campaña correctiva anterior permanece preservada como antecedente y sus
bytes están cubiertos por el manifiesto global, aunque no se utiliza como
evidencia definitiva de cierre debido al dataset vacío.

## Intentos no seleccionados de la campaña correctiva anterior

Los intentos descartados anteriores no se borran ni se reclasifican.

| Directorio | Evidencia observada | Motivo de no selección |
|---|---|---|
| `rep-01` | 3.600,466 s, exit code 0, SHA `75128b235be35485ad6410c32f8146c9c18aa949` | ejecución completa sobre SHA anterior; no corresponde al provenance seleccionado de la campaña `b94b7af...` |
| `rep-01-attempt-02` | abortado a 119,767 s; 4 login HTTP 401 y 143 HTTP 423 | autenticación/cuenta bloqueada; no completó la ventana |
| `rep-04` | intento abortado por `No space left on device`; `metadata.json` histórico truncado/JSON inválido | fallo operacional de disco; sus bytes históricos se preservan y no se “reparan” |
| `rep-04-attempt-02` | abortado a 295,612 s; 50 login HTTP 401 | autenticación fallida; no completó la ventana |
| `rep-06` | abortado a 108,284 s; 4 login HTTP 401 y 129 HTTP 423 | autenticación/cuenta bloqueada; no completó la ventana |

Los directorios `rep-01-attempt-03`, `rep-04-attempt-03` y
`rep-06-attempt-02` **no son intentos abortados**: completaron aproximadamente
3.600 s con exit code 0 y fueron las repeticiones seleccionadas r1, r4 y r6 de
la campaña correctiva anterior con dataset vacío.

## Smoke

El smoke permanece separado de r1--r10 y no forma parte del análisis
estadístico.

La nueva campaña poblada ejecutó además un smoke superior al TTL: 930,277 s,
50 login, 50 refresh, 23.076 GET de negocio, 5.926 GET por id, 0 HTTP 401 y
0 HTTP 5xx. Su manifiesto de 21 archivos verificó íntegramente.

Su función es comprobar el harness y el mantenimiento de la sesión antes de la
campaña oficial; no sustituye ninguna repetición.

## Alcance de la conclusión

La tasa HTTP 5xx y la disponibilidad temporal no son equivalentes.

La campaña permite concluir únicamente que, para la población correctiva
controlada y la infraestructura medida, el límite superior del IC95 de la tasa
HTTP 5xx por repetición queda por debajo de 1 %.

No se debe inferir de este resultado una disponibilidad temporal de 99,5 %,
porque tiempo apto frente a tiempo total no fue operacionalizado.

Tampoco se debe afirmar que la nueva campaña reproduce exactamente el dataset
histórico. La población de 20 reservas es una desviación controlada,
reproducible y declarada.

## Afirmaciones defendibles

Se puede defender que:

1. la campaña histórica conserva el defecto real de expiración de sesión y sus
   668.367 HTTP 401;
2. la primera campaña con refresh fue real, pero su dataset vacío impide usarla
   como cierre definitivo de #31;
3. la campaña poblada contiene diez repeticiones completas con ambas consultas
   nominales ejercitadas;
4. las diez repeticiones pobladas suman 895.136 GET de negocio, incluidos
   224.164 GET por id, con 0 HTTP 401 y 42 HTTP 5xx;
5. r2--r9 contienen 716.099 GET y producen una tasa HTTP 5xx media de
   0,005870 % e IC95 [-0,002938; 0,014677] %;
6. el límite superior 0,014677 % cumple el criterio `<1 %`;
7. p95 y p99 son descriptivos;
8. el dataset nuevo es controlado y no se presenta como reconstrucción exacta
   del histórico;
9. los raws, intentos desfavorables y códigos de salida permanecen preservados;
10. la disponibilidad temporal de 99,5 % continúa no operacionalizada y no se
    infiere desde la tasa HTTP 5xx.
