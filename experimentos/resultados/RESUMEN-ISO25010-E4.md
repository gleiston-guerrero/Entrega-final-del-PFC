# Resumen verificable ISO 25010 — Entrega 4

## Proveniencia

- Host de ejecución: `servidor-proyectos`.
- Repositorio de ejecución: `/home/ffarinangog2/proyectos/miscli`.
- Git SHA probado: `a47f0441f644bea5f52944b7a11216f37b2242de`.
- Locust: 2.31.6, Python 3.11.10.
- Evidencia recuperada sin modificar los originales de la VM.
- Integridad: `SHA256SUMS` contiene los hashes de los archivos seleccionados.

Los reportes HTML y los CSV `locust_stats_history.csv` completos permanecen en la
VM. No se versionan porque son derivados voluminosos; se preservan aquí los CSV
agregados canónicos, fallos, excepciones, logs, metadata, consultas/resultados
Prometheus, salud del entorno y estadísticas de contenedores.

## Rampa exploratoria 0 → 200 usuarios, 10 minutos

- Directorio: `raw/ramp_0_200_10m/run-20260830T041941Z/`.
- Inicio UTC: `2026-08-30T04:19:41Z`.
- Fin UTC: `2026-08-30T04:30:01Z`.
- Solicitudes canónicas: 29.217.
- HTTP 500: 1 (`GET /api/v1/reservas`).
- Tasa: `1 / 29.217 × 100 = 0,00342266 %`.
- p95 Locust: 180 ms.
- p99 Locust: 1.100 ms.
- Máximo Locust: 14.024,163663 ms.
- Estado registrado: `failed`, coherente con `--exit-code-on-error 1` y el HTTP 500.

La rampa es exploratoria y no forma parte de las ocho muestras del CSV ISO central.

## Eficiencia nominal, 50 usuarios, 5 minutos

Las diez repeticiones finalizaron con `exit_code=0`, pertenecen al SHA indicado y
registran 0 fallos HTTP. El análisis estadístico usa exclusivamente r2–r9; r1 y r10
se conservan, pero se excluyen según el protocolo.

Resultados oficiales corregidos por `experimentos/analizar_iso25010.py` directamente
desde las filas GET identificadas de los `locust_stats.csv` raw. Se incluye toda
respuesta de esos GET sin filtrar por código HTTP, latencia ni éxito/fallo. El login se
excluye exclusivamente porque pertenece a Auth y no a la población formal de consultas
de solo lectura de Reservas/Solicitudes:

| Métrica | n | Media | s muestral | IC95 | Decisión |
| --- | ---: | ---: | ---: | --- | --- |
| HTTP 5xx | 8 | 0 % | 0 % | [0; 0] % | CUMPLE `<1 %` |
| p95 Locust | 8 | 45,500000 ms | 21,764978 ms | [27,304023; 63,695977] ms | Descriptivo; NO CONCLUYENTE para el escenario prerregistrado |
| p99 Locust | 8 | 371,250000 ms | 364,032475 ms | [66,911235; 675,588765] ms | Descriptivo; NO CONCLUYENTE para el escenario prerregistrado |

El cálculo usa `df=7` y `t(0,975;7)=2,364624251`. Las ocho repeticiones
centrales contienen 57.241 observaciones de la población formal.

### Análisis histórico preservado

El análisis anterior tomó la fila `Aggregated`, que mezcla GET de
Reservas/Solicitudes con 50 observaciones de `POST /api/v1/auth/login` por repetición,
y no corresponde a la población formal utilizada para responder PI1. Produjo p95 media
57,500000 ms, desviación 37,132966 ms e IC95 [26,456064; 88,543936] ms, por lo que
p95 cumplía. Para p99 produjo media 624,000000 ms, desviación 606,585526 ms e IC95
[116,881810; 1.131,118190] ms, por lo que p99 no cumplía `<750 ms`. Estos valores se
mantienen visibles únicamente como trazabilidad del análisis histórico incorrectamente
poblado; no se alteraron ni repitieron las campañas ni los raws.

Los criterios, umbrales, r2–r9, regla del IC y diseño de carga basado en consultas GET
fueron declarados antes de la ejecución. Las preguntas PI1/PI2 se formalizaron
posteriormente en el manuscrito utilizando esos criterios preexistentes.

Como contraste, los resultados Prometheus p95 de r2–r9 producen:

- media: 18,283375 ms;
- desviación estándar muestral: 8,240924 ms;
- IC95: [11,393791; 25,172960] ms;
- HTTP 5xx en las diez ventanas: 0.

Locust y Prometheus miden en puntos distintos del sistema y no deben presentarse
como métricas intercambiables.

## Fiabilidad nominal, 50 usuarios, 1 hora

La campaña histórica se conserva como antecedente metodológico. Fue ejecutada
sobre el SHA `061a1050a94e1bd30d81b30c47c7e818005a33bb` y produjo
668.367 respuestas HTTP 401 por ausencia de renovación del JWT. Sus raws no se
eliminan ni se reinterpretan.

La primera campaña con refresh,
`raw/fiabilidad_nominal_50u_1h_refresh/`, fue ejecutada sobre
`b94b7af7ebab2510c16eae0c70593664763de1e7` y completó diez repeticiones
seleccionadas. Sin embargo, el listado permaneció vacío y no se ejecutó
`GET /api/v1/reservas/{id}`. Por ello, sus 896.964 GET y 0 HTTP 5xx se
conservan como antecedente, pero **no constituyen el cierre definitivo de E2**.

La corrección post-evaluación se ejecutó en
`raw/fiabilidad_nominal_50u_1h_refresh_poblada/` sobre el software desplegado
`dd2e1923d7635857f4020c7ef5c8b6efee363d7a`.

Se fijó una nueva población controlada de 20 reservas. Su `dataset.csv` tiene
SHA-256
`f2c07cc4698715939a9eaf6b47e694ccdf39fcd2de0502aec6164a90321f9b78`.
No se afirma que sea una reconstrucción exacta del dataset histórico; la
limitación de comparabilidad estricta queda declarada.

Las diez repeticiones pobladas contienen 895.136 GET de negocio: 670.972 de
listado y 224.164 por id, con 0 HTTP 401 y 42 HTTP 5xx. Los 5xx se preservan:
r7=1, r8=21 y r9=20.

El análisis estadístico principal utiliza r2--r9 según el diseño establecido.
Estas ocho repeticiones contienen 716.099 GET de negocio, incluidos 179.322
GET por id.

Los resultados son reproducibles mediante:

`python3 experimentos/analizar_iso25010.py experimentos/resultados/iso25010-correctiva-poblada.csv`

El analizador reconstruye las métricas desde `locust_requests.csv` y exige su
coincidencia con el consolidado.

| Métrica | n | Media | s muestral | IC95 | Interpretación |
| --- | ---: | ---: | ---: | --- | --- |
| Tasa HTTP 5xx | 8 | 0,005870 % | 0,010535 % | [-0,002938; 0,014677] % | **CUMPLE** `<1 %` |
| p95 GET negocio | 8 | 11,256521 ms | 0,223526 ms | [11,069649; 11,443394] ms | INFORMATIVO |
| p99 GET negocio | 8 | 23,945109 ms | 1,602666 ms | [22,605247; 25,284971] ms | INFORMATIVO |

El cálculo usa `df=7` y `t(0,975;7)=2,364624251`. El límite inferior negativo
de la tasa procede del intervalo t no acotado y se conserva sin truncarlo. La
regla de decisión utiliza el límite superior.

Como `0,014677 % < 1 %`, **E2 CUMPLE el criterio acotado de HTTP 5xx en la
campaña poblada medida**. p95 y p99 son únicamente descriptivos.

El código de salida de Locust no se usa como criterio automático de exclusión:
r7, r8 y r9 conservan exit code 1 porque registraron fallos HTTP observados.
Excluirlas habría eliminado resultados desfavorables.

Cada repetición poblada tiene `SHA256SUMS`. El manifiesto global
`resultados/SHA256SUMS` contiene 1.339 entradas. Incluye los 550 archivos
actualmente versionados de la campaña correctiva anterior, su
`iso25010-correctiva.csv`, las 319 evidencias de la campaña poblada y
`iso25010-correctiva-poblada.csv`.

Los intentos históricos descartados permanecen preservados y documentados en
`../cierre-e2-fiabilidad.md`; no se corrigen ni se eliminan sus bytes.

La tasa HTTP 5xx no equivale a disponibilidad temporal. El resultado decide el
criterio acotado de errores, pero **no demuestra por sí solo disponibilidad
mayor o igual que 99,5 %**.

## Consolidación oficial E3: seguridad, mantenibilidad y compatibilidad

> Corrección #32. Seguridad: las tres repeticiones verifican los mismos siete
> casos y resultados; el intervalo Wilson usa 7/7, mientras 3/3 se informa como
> repetibilidad. Compatibilidad: cada motor tiene 8/8 observaciones distintas y
> 3/3 resúmenes exitosos e idénticos; el paquete compacto no permite verificar
> retrospectivamente los identificadores individuales de esos ocho casos. La
> evidencia se limita a comportamiento cross-browser de la suite Web ensayada,
> no a coexistencia/interoperabilidad ISO completa ni Android. La matriz estática
> de 198 operaciones de seguridad es antecedente de superficie, no prueba dinámica.

Las tres campañas se ejecutaron sobre el software del SHA
`fa7d75ec0f75573938bf46ed6a68f0aee99606ac`. El HEAD documental posterior
incorpora análisis y documentación y no se presenta como el software medido.
La fuente consolidada inalterada es [`analisis-e3.json`](analisis-e3.json).
Las líneas backend se recalculan desde los `jacoco.csv` canónicos:
Usuarios 329 missed/1735 covered = 84,06007751937985 % y Reservas 506/2730 =
84,36341161928307 %. La complejidad JaCoCo es descriptiva, no una puntuación de
calidad: Auth 133+219=352 (56 clases, media 6,285714, máximo 34);
Usuarios 239+619=858 (107, 8,018692, máximo 68); Académico 260+944=1204
(141, 8,539007, máximo 57); Reservas 711+1318=2029 (203, 9,995074, máximo
178); Gateway 17+44=61 (9, 6,777778, máximo 28). El paquete canónico no
conserva salida cuantitativa y exit code de Checkstyle para reconstruir E3.

### Seguridad

| Repeticiones | Correctas | Proporción | IC95 Wilson | Falsos permitidos | Falsos rechazados | Flaky | Decisión |
|---:|---:|---:|---|---:|---:|---:|---|
| 3 (repetibilidad 3/3) | 7/7 casos distintos | 1,0 | [0,6456695648259365; 1,0] | 0 | 0 | 0 | **CUMPLE en alcance dinámico reducido** |

La decisión se limita a las siete decisiones dinámicas por repetición, fixtures,
Gateway y entorno ensayados. No constituye una garantía universal de seguridad.

### Mantenibilidad

| Componente | Métrica | Media/IC95 | Umbral | Decisión |
|---|---|---:|---:|---|
| Auth | Líneas | 88,042203985932 % | 70 % | CUMPLE |
| Usuarios | Líneas | 84,06007751937985 % | 70 % | CUMPLE |
| Académico | Líneas | 83,16089903674634 % | 70 % | CUMPLE |
| Reservas | Líneas | 84,36341161928307 % | 80 % | CUMPLE |
| Reservas | Ramas | 56,72559569561876 % | 48 % | CUMPLE |
| Gateway | Líneas | 88,88888888888889 % | 70 % | CUMPLE |
| Web | Líneas | 89,91 % | 70 % | CUMPLE |
| Web | Ramas | 73,69 % | 70 % | CUMPLE |
| Web | Funciones | 81,87 % | 70 % | CUMPLE |
| Web | Sentencias | 85,96 % | 70 % | CUMPLE |
| Android | Líneas | **38,34070796460177 %** | 70 % | **NO CUMPLE** |

Los tres valores de cada métrica fueron idénticos: `sample_sd = 0` y el IC95 t
es `[media; media]`. Esto describe repetición idéntica del proceso sobre el
mismo SHA, no certeza universal. La decisión global es **NO CUMPLE únicamente
por Android**.

### Compatibilidad

| Motor | Aprobados | Fallidos | Omitidos | Flaky | IC95 Wilson | Decisión |
|---|---:|---:|---:|---:|---|---|
| Chromium | 8/8 | 0 | 0 | 0 | [0,6755924350132556; 1,0] | CUMPLE en suite |
| Firefox | 8/8 | 0 | 0 | 0 | [0,6755924350132556; 1,0] | CUMPLE en suite |
| WebKit | 8/8 | 0 | 0 | 0 | [0,6755924350132556; 1,0] | CUMPLE en suite |

La decisión global es **CUMPLE** para la suite, motores y entorno ensayados; no
se extrapola a todos los navegadores, versiones o dispositivos.

El diseño y las reglas están en [`../protocolo-e4.md`](../protocolo-e4.md), y
la cadena requisito → protocolo → productor → raw → análisis → documento está
en [`TRAZABILIDAD-E3-E4.md`](TRAZABILIDAD-E3-E4.md). La selección compacta
[`evidencia-e3-canonica/`](evidencia-e3-canonica/) conserva manifiestos,
resultados consumidos por el analizador y reportes fuente de cobertura. El raw
E3 completo continúa disponible en el entorno de ejecución y no se versiona por
su volumen; la selección canónica no sustituye ni modifica esos originales.
