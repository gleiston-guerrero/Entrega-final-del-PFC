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
| p95 Locust | 8 | 45,500000 ms | 21,764978 ms | [27,304023; 63,695977] ms | CUMPLE `<500 ms` |
| p99 Locust | 8 | 371,250000 ms | 364,032475 ms | [66,911235; 675,588765] ms | CUMPLE `<750 ms` |

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
668.367 respuestas HTTP 401 debido a la ausencia de renovación del JWT.
Sus raws no se eliminan ni se reinterpretan como campaña correctiva.

La campaña correctiva oficial se ejecutó sobre el SHA
`b94b7af7ebab2510c16eae0c70593664763de1e7`. Completó diez repeticiones
válidas de una hora con 50 usuarios y `spawn-rate` 10 usuarios/s.

Las diez repeticiones correctivas suman 896.964 GET de negocio, con
0 HTTP 401 y 0 HTTP 5xx. El análisis estadístico principal utiliza r2–r9;
r1 y r10 se conservan, pero se excluyen de medias e IC95 según el
prerregistro.

Los resultados son reproducibles mediante
`python3 experimentos/analizar_iso25010.py experimentos/resultados/iso25010-correctiva.csv`.
El analizador reconstruye las métricas directamente desde los
`locust_requests.csv` raw y verifica su coincidencia con el CSV consolidado.

| Métrica | n | Media | s muestral | IC95 | Interpretación |
| --- | ---: | ---: | ---: | --- | --- |
| Tasa HTTP 5xx | 8 | 0,000000 % | 0,000000 % | [0,000000; 0,000000] % | **CUMPLE** `<1 %` |
| p95 GET negocio | 8 | 6,680642 ms | 0,177173 ms | [6,532522; 6,828763] ms | INFORMATIVO |
| p99 GET negocio | 8 | 9,849009 ms | 0,489360 ms | [9,439893; 10,258124] ms | INFORMATIVO |

El cálculo usa `df=7` y `t(0,975;7)=2,364624251`. La métrica primaria es
`100 × HTTP 5xx / GET de negocio`. p95 y p99 se calculan sobre la distribución
raw completa de GET de negocio, sin excluir observaciones por código HTTP,
éxito, fallo o latencia. Login y refresh se contabilizan por separado.

Los contadores finales exactos de Locust registran 899.464 requests al incluir
tráfico de sesión y 0 fallos. Para E2, el denominador oficial permanece en los
896.964 GET de negocio.

Los intentos inválidos o abortados permanecen preservados en sus directorios
originales y no se reutilizan como observaciones oficiales.

El resultado permite decidir el criterio acotado de HTTP 5xx y **E2 CUMPLE**
en el escenario correctivo medido. No demuestra por sí solo una disponibilidad
temporal mayor o igual que 99,5 %.

## Consolidación oficial E3: seguridad, mantenibilidad y compatibilidad

Las tres campañas se ejecutaron sobre el software del SHA
`fa7d75ec0f75573938bf46ed6a68f0aee99606ac`. El HEAD documental posterior
incorpora análisis y documentación y no se presenta como el software medido.
La fuente consolidada inalterada es [`analisis-e3.json`](analisis-e3.json).

### Seguridad

| Repeticiones | Correctas | Proporción | IC95 Wilson | Falsos permitidos | Falsos rechazados | Flaky | Decisión |
|---:|---:|---:|---|---:|---:|---:|---|
| 3 | 21/21 | 1,0 | [0,845360981013798; 1,0] | 0 | 0 | 0 | **CUMPLE** |

La decisión se limita a las siete decisiones dinámicas por repetición, fixtures,
Gateway y entorno ensayados. No constituye una garantía universal de seguridad.

### Mantenibilidad

| Componente | Métrica | Media/IC95 | Umbral | Decisión |
|---|---|---:|---:|---|
| Auth | Líneas | 88,042203985932 % | 70 % | CUMPLE |
| Usuarios | Líneas | 84,0523509452254 % | 70 % | CUMPLE |
| Académico | Líneas | 83,16089903674634 % | 70 % | CUMPLE |
| Reservas | Líneas | 84,35857805255023 % | 80 % | CUMPLE |
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
| Chromium | 24/24 | 0 | 0 | 0 | [0,862023795269197; 1,0] | CUMPLE |
| Firefox | 24/24 | 0 | 0 | 0 | [0,862023795269197; 1,0] | CUMPLE |
| WebKit | 24/24 | 0 | 0 | 0 | [0,862023795269197; 1,0] | CUMPLE |

La decisión global es **CUMPLE** para la suite, motores y entorno ensayados; no
se extrapola a todos los navegadores, versiones o dispositivos.

El diseño y las reglas están en [`../protocolo-e4.md`](../protocolo-e4.md), y
la cadena requisito → protocolo → productor → raw → análisis → documento está
en [`TRAZABILIDAD-E3-E4.md`](TRAZABILIDAD-E3-E4.md). La selección compacta
[`evidencia-e3-canonica/`](evidencia-e3-canonica/) conserva manifiestos,
resultados consumidos por el analizador y reportes fuente de cobertura. El raw
E3 completo continúa disponible en el entorno de ejecución y no se versiona por
su volumen; la selección canónica no sustituye ni modifica esos originales.
