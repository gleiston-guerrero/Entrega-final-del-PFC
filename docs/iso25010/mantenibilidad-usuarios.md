# ISO/IEC 25010 — Mantenibilidad

> **Antecedente / auditoría histórica.** Las secciones fechadas el 2026-09-04
> corresponden al SHA `cd61b64325480cbe132af7e56328f7fa5d8b99ef`. Sus cifras,
> incluido Android 45,69 %, se conservan como antecedentes y no son el resultado
> oficial E3 actual.

**Fecha de revisión:** 2026-09-04

**HEAD auditado:** `cd61b64325480cbe132af7e56328f7fa5d8b99ef`

## Metodología

Se contrastaron las reglas JaCoCo de cada POM, Vitest/V8, JaCoCo Android, Checkstyle, ESLint/lint y los jobs del workflow con los resultados accesibles del HEAD. Una configuración de umbral se informa como gate, no como porcentaje ejecutado. Cuando no existe reporte cuantitativo actual de complejidad o cobertura, se declara no concluyente.

No se ejecutaron suites pesadas. Los runs consultados fueron [push 33838233548](https://github.com/gleiston-guerrero/Entrega-final-del-PFC/actions/runs/33838233548) y [pull request 33838236394](https://github.com/gleiston-guerrero/Entrega-final-del-PFC/actions/runs/33838236394).

## Resultados del antecedente histórico

| Componente | Cobertura disponible | Umbral configurado | Complejidad disponible | Gate CI del HEAD | Estado sustentable |
|---|---|---|---|---|---|
| Auth | El job `mvn verify` del HEAD pasó; por la regla implica líneas >=70%, sin porcentaje persistido | JaCoCo LINE >=70% | Sin medición global versionada | Backend: verde | PARCIAL |
| Usuarios | Medición histórica: 83,81% líneas; no es atribuible al HEAD actual | JaCoCo LINE >=70% | Histórica: media 1,16 y máximo 6; Checkstyle no es gate CI para este servicio | Backend: rojo | NO CONCLUYENTE |
| Académico | El job `mvn verify` del HEAD pasó; implica líneas >=70%, sin porcentaje persistido | JaCoCo LINE >=70% | Checkstyle configurado y lint CI verde; sin media global persistida | Backend y Checkstyle: verdes | PARCIAL |
| Reservas | Sin porcentaje válido del HEAD porque `mvn verify` falló | JaCoCo LINE >=80%; BRANCH >=48% | Sin medición global versionada | Backend: rojo | NO CONCLUYENTE |
| Gateway | El job `mvn verify` del HEAD pasó; implica líneas >=70%, sin porcentaje persistido | JaCoCo LINE >=70% | Sin medición global versionada | Backend: verde | PARCIAL |
| Web | Reporte local actual: líneas 86,55%, statements 82,96%, functions 74,81%, branches 70,33%; `Test web` y ESLint verdes en CI | Vitest: 70% en líneas, statements, functions y branches | Sin complejidad ciclomática global | Web y ESLint: verdes | PARCIAL |
| Android | Reporte JaCoCo histórico: líneas 45,69%, branches 12,92% | No existe umbral JaCoCo que falle el build | Sin complejidad global | Unit tests/lint verdes; instrumentado verde en push y rojo en PR | PARCIAL |

## Interpretación

Los gates de Auth, Académico, Gateway y Web acreditan sus mínimos configurados en el run de push. No se publica el reporte JaCoCo Backend como artifact, por lo que no se asignan porcentajes exactos. Usuarios y Reservas fallaron en `mvn verify`; aunque sus causas puedan ser pruebas concretas y no cobertura, un job rojo no demuestra cumplimiento del HEAD.

La cifra de Usuarios (83,81% de líneas, complejidad media 1,16 y máximo 6) se conserva como medición histórica documentada, no como resultado actual. En CI solo Académico ejecuta Checkstyle desde el job `lint`; Usuarios tiene configuración Checkstyle, pero el workflow actual no la invoca explícitamente.

En ese reporte histórico, Web supera sus cuatro umbrales. Android producía y
publicaba cobertura, pero carecía de gate mínimo y su cobertura de líneas de
45,69 % estaba por debajo del objetivo documental de 70 %; este antecedente no
se usa como resultado E3 actual.

## Conclusión

**Mantenibilidad: PARCIAL.** Hay automatización y umbrales efectivos en Backend y Web, lint en Web/Android y Checkstyle en Académico. No obstante, faltan reportes cuantitativos persistidos para todo Backend, no existe complejidad comparable en todos los módulos, Android permanece bajo 70% y dos servicios Backend no completaron su gate en el HEAD. Una conclusión global de cumplimiento no está sustentada.

## Resultado experimental oficial E3

La campaña oficial ejecutó tres veces el proceso completo de cobertura sobre el
SHA `fa7d75ec0f75573938bf46ed6a68f0aee99606ac`.

| Componente | Métrica | Media/IC95 | Umbral | Decisión |
|---|---|---:|---:|---|
| Auth | Líneas | 88,042203985932 % | 70 % | CUMPLE |
| Usuarios | Líneas | 84,06007751937985 % | 70 % | CUMPLE |
| Académico | Líneas | 83,16089903674634 % | 70 % | CUMPLE |
| Reservas | Líneas | 84,36341161928307 % | 80 % | CUMPLE |
| Reservas | Ramas | 56,72559569561876 % | 48 % | CUMPLE |
| Gateway | Líneas | 88,88888888888889 % | 70 % | CUMPLE |
| Web | Líneas (HISTÓRICA / E3) | 89,91 % | 70 % | CUMPLE |
| Web | Ramas (HISTÓRICA / E3) | 73,69 % | 70 % | CUMPLE |
| Web | Funciones (HISTÓRICA / E3) | 81,87 % | 70 % | CUMPLE |
| Web | Sentencias (HISTÓRICA / E3) | 85,96 % | 70 % | CUMPLE |
| Android | Líneas | **38,34070796460177 %** | 70 % | **NO CUMPLE** |

Las cifras Web de la tabla anterior pertenecen a una medición E3 previa que no
incluía la totalidad de `src/` y quedan marcadas como **HISTÓRICA / E3**; no
representan la cobertura vigente del cliente Web.

Las cinco coberturas backend se derivan de `LINE_COVERED / (LINE_COVERED +
LINE_MISSED)` en los `jacoco.csv` canónicos de cada repetición. La complejidad
JaCoCo se presenta solamente como evidencia descriptiva: Auth 133 missed, 219
covered, total 352, 56 clases, media 6,285714 y máximo 34
(`PasswordRecoveryService`); Usuarios 239, 619, 858, 107, 8,018692 y 68
(`InitialProfilesBootstrap`); Académico 260, 944, 1204, 141, 8,539007 y 57
(`PoliticaAmbitoAcademico`); Reservas 711, 1318, 2029, 203, 9,995074 y 178
(`PlanificacionAgregadaService`); Gateway 17, 44, 61, 9, 6,777778 y 28
(`GatewayRoutes`). No se interpreta el porcentaje de complejidad cubierta como
puntuación de calidad. El prerregistro contempló Checkstyle, pero el paquete E3
canónico no preserva una salida cuantitativa con exit code para reconstruirlo;
el CI actual, si se cita, es evidencia posterior separada.

## MEDICIÓN WEB VIGENTE

| Métrica | Resultado | Umbral | Decisión |
|---|---:|---:|---|
| Sentencias (statements) | 81,89 % | 70 % | CUMPLE |
| Ramas (branches) | 70,25 % | 70 % | CUMPLE |
| Funciones (functions) | 78,43 % | 70 % | CUMPLE |
| Líneas (lines) | 84,87 % | 70 % | CUMPLE |

- **Comando exacto:** `npm run test:coverage` (equivalente a `vitest run --coverage`), ejecutado en `apps/web`.
- **Alcance:** `apps/web/src/**/*.{ts,tsx}`.
- **Threshold del gate:** 70 % mínimo en statements, branches, functions y lines (sin reducir).
- **Suite:** 43 archivos, 296 pruebas; 3/3 repeticiones consecutivas en PASS.
- **Contexto:** rama `fix/eval2-7-web-ivan`, base en el commit `c10abc0` del repositorio oficial `gleiston-guerrero/Entrega-final-del-PFC`.

En las tres repeticiones cada métrica produjo el mismo valor: `sample_sd = 0`
y el IC95 t degeneró en `[media; media]`. Ese resultado refleja el carácter
determinista de ejecutar la misma suite sobre el mismo SHA; ni la desviación
nula ni el intervalo degenerado demuestran por sí mismos independencia o una
precisión inferencial fuerte. La procedencia experimental separada se acredita
mediante las ventanas de ejecución no solapadas, los manifiestos independientes
y los identificadores internos de los reportes fuente:

| Repetición | Inicio UTC | Fin UTC | Duración | SHA-256 `metricas.csv` | SHA-256 informe Android | `sessioninfo` JaCoCo Android | Cobertura Android |
|---|---|---|---:|---|---|---|---:|
| `rep-01` | 2026-09-12 05:38:47.397078 | 2026-09-12 05:52:30.095802 | 822,698724 s | `d336496f1f9ec8d144853b64e310dceb9c2262885b1d061029062cfbeb5eeac5` | `3152520eb897ae2bbf7044cbb884036f6e35ec5297fc481573a4eda0b810fd0e` | `DESKTOP-N45EJGV-f3ab9b30` | 38,34070796460177 % |
| `rep-02` | 2026-09-12 05:53:48.384042 | 2026-09-12 06:05:14.745791 | 686,361749 s | `d336496f1f9ec8d144853b64e310dceb9c2262885b1d061029062cfbeb5eeac5` | `689c514199693da3a1d3f0f208697fc6cae7f8c4d299868ef714c7d611d77815` | `DESKTOP-N45EJGV-b268151` | 38,34070796460177 % |
| `rep-03` | 2026-09-12 06:07:00.038156 | 2026-09-12 06:18:59.123202 | 719,085046 s | `d336496f1f9ec8d144853b64e310dceb9c2262885b1d061029062cfbeb5eeac5` | `07d393d05fedd9e569bbe2c566e0441d1a6cfb6645940ebf64449658ba11338a` | `DESKTOP-N45EJGV-f0c2743e` | 38,34070796460177 % |

Por tanto, `rep-01`, `rep-02` y `rep-03` son invocaciones separadas del
instrumental. Que `metricas.csv` tenga el mismo hash acredita igualdad del
resultado, no reutilización de una única ejecución. Para Android se preservan
además informes con hashes y sesiones JaCoCo distintos.

El resultado estadístico se conserva sin reinterpretarlo: media =
38,34070796460177 %, `sample_sd = 0`, IC95 =
[38,34070796460177; 38,34070796460177], umbral = 70 % y decisión = **NO
CUMPLE**. La decisión global experimental es **NO CUMPLE únicamente por
Android**.
La fuente es [`analisis-e3.json`](../../experimentos/resultados/analisis-e3.json)
y la relación con protocolo y raw consta en
[`TRAZABILIDAD-E3-E4.md`](../../experimentos/resultados/TRAZABILIDAD-E3-E4.md).
