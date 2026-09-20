# Registros retrospectivos de trabajo colaborativo

Los cinco documentos de este directorio fueron creados conjuntamente por el
commit [`1ce91ba05e8048fda75a8479d368684a2c338430`](https://github.com/gleiston-guerrero/Entrega-final-del-PFC/commit/1ce91ba05e8048fda75a8479d368684a2c338430): autoría a las
`2026-09-12T08:32:42Z` y consolidación a las `2026-09-12T08:33:13Z`
(`03:32:42` y `03:33:13` en UTC-05:00). Por ello se denominan **registros
retrospectivos**, no actas contemporáneas de reuniones en las fechas de los
trabajos asociados.

Git y GitHub permiten comprobar commits, autores, artefactos y ejecuciones, pero
no demuestran por sí solos que hubiera reuniones por Google Meet, una hora de
inicio o una lista de asistencia. Se retiraron esas afirmaciones. Los nombres y
responsabilidades siguientes se conservan como atribuciones del registro
consolidado y se enlazan, cuando existe, con resultados verificables:

- Freddy Farinango — Arquitectura.
- Isaías Urbina — Líder Dev.
- Iván Villamarín — Calidad.
- Harold Vinueza — Documentación.

## Cronología verificable

| Registro                  | Fecha real de consolidación | Periodo de trabajo verificable | Tema                                                  | Evidencia principal                                                                                                                |
| ------------------------- | --------------------------- | ------------------------------ | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| [Registro 01](ACTA-01.md) | 12/09/2026                  | Hito del 20/08/2026            | Planificación y arquitectura del sistema distribuido  | `ea3a5724113ae08108f447881cf2d05eda05aac2`                                                                                         |
| [Registro 02](ACTA-02.md) | 12/09/2026                  | Commits del 24–29/08/2026      | Integración, pruebas y CI/CD                          | `d0bcc23863cdd4bc1646a34458db52d2563ac283`, `e439b35d69f01307f529152589a0d87fa09a9d6e`, `30a55723cb7eb22a59669946de82984e39b1ca09` |
| [Registro 03](ACTA-03.md) | 12/09/2026                  | Commits del 11–12/09/2026      | Experimentación ISO 25010 y preparación/cierre de E3  | `fdc8e6827ae74b2b439acae84776b3e2f93b3e4e`, `fa7d75ec0f75573938bf46ed6a68f0aee99606ac`                                             |
| [Registro 04](ACTA-04.md) | 12/09/2026                  | Commits del 12/09/2026         | Trazabilidad, documentación y contratos OpenAPI E4–E6 | `cef50709177eee2c41b53f0000f9d936ddb373df`, `0bc47c61e54a8173e2ff195012d5d50e7bd975b0`, `e0c27e5e6006d1c0af9a3d9efae8b34a61da3afa` |
| [Registro 05](ACTA-05.md) | 12/09/2026                  | Commit y run del 12/09/2026    | APK Android release firmado y cierre técnico E7       | `afa9794242506c85124a6468e986768751902296`, Actions `34682703140`                                                                  |

## Alcance probatorio

Los commits acreditan la existencia y cronología de resultados técnicos; no
sustituyen evidencia contemporánea de una reunión. Las decisiones y asignaciones
se presentan como consolidación retrospectiva realizada el 12/09/2026. No se
retrofechan reuniones ni se deducen comentarios, aprobaciones o asistencia a
partir de la autoría de código.

## Actas contemporáneas

ACTA-06 corresponde a una reunión contemporánea realizada el 15/09/2026.
Estas actas son distintas de los cinco registros retrospectivos anteriores y no
modifican ni reinterpretan su alcance probatorio.

ACTA-06 documenta una reunión contemporánea, pero la evidencia del PR #10 que
allí se revisa pertenece al repositorio histórico
`iavillamarin98-pred/ORA_entrega_F`, no al repositorio oficial actual.

| Acta                  | Fecha      | Hora                  | Participantes                  | Tema principal                                                                                                                              | Evidencia                         |
| --------------------- | ---------- | --------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| [ACTA-06](ACTA-06.md) | 15/09/2026 | 21:58–22:45 UTC-05:00 | Isaías Urbina, Iván Villamarín | Cierre del punto #7, revisión cruzada del PR #10 del repositorio histórico `iavillamarin98-pred/ORA_entrega_F` y organización de pendientes | [Evidencias](evidencias/acta-06/) |
| [ACTA-07](ACTA-07.md) | 17/09/2026 | —                       | Isaías Urbina, Iván Villamarín | Revisión cruzada del PR #11 y proceso de revisión del PR #12 del repositorio oficial | [Evidencias](evidencias/acta-07/) |
| [ACTA-08](ACTA-08.md) | 19/09/2026 | Primera evidencia: 23:05; última evidencia: 23:16 UTC-05:00 | Isaías Urbina, Iván Villamarín | Revisión cruzada del PR #29 del repositorio oficial y merge a `main` para evidencia de release final | [Evidencias](evidencias/acta-08/) |

### Evidencia asociada a ACTA-06

La evidencia almacenada en [evidencias/acta-06/](evidencias/acta-06/) corresponde a elementos
revisados durante la reunión:

- [meet-revision-pr10.png](evidencias/acta-06/meet-revision-pr10.png): sesión activa de Google Meet durante la revisión
  técnica del PR #10 del repositorio histórico `iavillamarin98-pred/ORA_entrega_F`.
- [pr10-aprobado-mergeado.png](evidencias/acta-06/pr10-aprobado-mergeado.png): aprobación de `iavillamarin98-pred`,
  integración del PR #10 histórico a `feature/entrega-4` y cierre de la solicitud.

El ACTA-06 registra una reunión efectivamente realizada el 15/09/2026 y no se
presenta como reconstrucción retrospectiva de actividades anteriores.

### Evidencia asociada a ACTA-07

- [pr11-aprobado-repo-oficial.png](evidencias/acta-07/pr11-aprobado-repo-oficial.png): aprobación del PR #11 del repositorio oficial, con checks todavía en ejecución.
- [pr12-creacion-reviewer.png](evidencias/acta-07/pr12-creacion-reviewer.png): creación del PR #12 hacia `feature/entrega-4` y selección de Iván como reviewer.
- [meet-revision-pr12.png](evidencias/acta-07/meet-revision-pr12.png): revisión del PR #12 durante la sesión, con la opción `Approve` seleccionada antes de enviar; el estado final del PR quedó posteriormente registrado como `APPROVED` por `ivillamarinc` y fue integrado mediante el merge commit `29ee3d8`.

### Evidencia asociada a ACTA-08

- [acta-08-meet-revision-pr29-2305.png](evidencias/acta-08/acta-08-meet-revision-pr29-2305.png): sesión activa de Google Meet a las 23:05 durante la revisión del PR #29.
- [acta-08-pr29-abierto.png](evidencias/acta-08/acta-08-pr29-abierto.png): PR #29 abierto en el repositorio oficial `gleiston-guerrero/Entrega-final-del-PFC`.
- [acta-08-pr29-review-aprobacion-ivan.png](evidencias/acta-08/acta-08-pr29-review-aprobacion-ivan.png): comentario escrito y aprobación de `ivillamarinc` antes del merge.
- [acta-08-pr29-checks-aprobados-2314.png](evidencias/acta-08/acta-08-pr29-checks-aprobados-2314.png): checks en estado satisfactorio a las 23:14 con el PR todavía abierto.
- [acta-08-pr29-confirmacion-merge-2315.png](evidencias/acta-08/acta-08-pr29-confirmacion-merge-2315.png): pantalla de confirmación del merge a las 23:15.
- [acta-08-pr29-merge-completado-2316.png](evidencias/acta-08/acta-08-pr29-merge-completado-2316.png): PR #29 fusionado a `main` y cerrado a las 23:16.
