# ACTA-06 — Reunión contemporánea de cierre y revisión del PFC

**Fecha:** 15/09/2026

**Hora de inicio:** 21:58

**Hora de fin:** 22:45

**Zona horaria:** UTC-05:00

**Medio:** Google Meet

**Nota de revision posterior:** el 17/09/2026 se corrigio el alcance de esta
acta para identificar el PR #10 como evidencia del repositorio historico
`iavillamarin98-pred/ORA_entrega_F`, no del repositorio oficial actual. Esta
revision adicional no formaba parte del acta original del 15/09/2026.

## Participantes

- Isaías Urbina
  - GitHub: `IsaiasUrb`
  - Rol: desarrollo, revisión de avances y corrección de observaciones.
- Iván Villamarín
  - GitHub: `iavillamarin98-pred`
  - Rol: revisión de cambios, validación de evidencias y observaciones sobre las correcciones.

Nota objetiva: las capturas de Google Meet muestran 3 participantes conectados,
pero solo permiten identificar nominalmente a Isaias e Ivan. No se atribuye
identidad al tercer participante por falta de evidencia suficiente.

## Objetivo

Revisar el cierre del punto #7 de la guía del PFC, revisar el estado ya
integrado del PR #10 del repositorio historico y organizar el tratamiento de
los puntos pendientes.

## Temas tratados

### 1. Punto #7 — Calidad Web

Se revisaron los siguientes resultados de las pruebas de la aplicación Web:

- 43 archivos de prueba.
- 296 pruebas aprobadas.
- Statements: 81.89 %.
- Branches: 70.25 %.
- Functions: 78.43 %.
- Lines: 84.87 %.

> **Nota de rectificación posterior — 21/09/2026:** el 70,25 % de branches
> fue el valor consignado en esta acta y se conserva como registro histórico.
> La reproducción independiente posterior del docente (1558/2219 ramas) y
> [GitHub Actions CI #536, job `Test web`](https://github.com/gleiston-guerrero/Entrega-final-del-PFC/actions/runs/35564968302/job/106224985293)
> sobre el SHA `00947b366b0484af7c5ea997e13d07e018484339` producen 70,21 %,
> que se adopta como cifra vigente documentada. Statements/functions/lines permanecen
> en 81,89 / 78,43 / 84,87 %. Esta nota no formaba parte del acta original ni
> acredita el cierre de la corrección #7 actual; los acuerdos originales que
> siguen se conservan como antecedentes.

La revisión abarcó los porcentajes de cobertura y la reproducibilidad de los resultados. Se revisó el procedimiento para reproducir la medición desde la raíz del repositorio:

```bash
cd apps/web && npm ci && npm run test:coverage
```

**Estado acordado:** punto #7 cerrado con base en la evidencia reproducible revisada y su integración mediante los PR correspondientes.

### 2. Revisión cruzada del PR #10 del repositorio histórico

Durante la reunion se reviso el estado ya integrado del PR #10 del repositorio
historico `iavillamarin98-pred/ORA_entrega_F`, utilizado como evidencia
verificable del proceso de revision seguido por el equipo.

Las capturas disponibles muestran el PR #10 ya aprobado y fusionado antes de la
revision visible en la reunion: a las 22:12 se observa la aprobacion como
ocurrida hace 39 minutos y el merge como ocurrido hace 37 minutos. Por ello,
esta acta no afirma que la aprobacion ni el merge ocurrieran durante la ventana
21:58-22:45.

- Repositorio: `iavillamarin98-pred/ORA_entrega_F`.
- PR: #10 — `docs(web): precisar comando reproducible de cobertura`.
- Autor: `IsaiasUrb`.
- Reviewer: `iavillamarin98-pred`.
- Review: `APPROVED`.
- Merge commit: `4ba4325`.
- Rama destino: `feature/entrega-4`.

La revisión fue realizada por Iván Villamarín, una persona distinta al autor
del cambio, Isaías Urbina.

> Nota de trazabilidad: este PR #10 pertenece al repositorio histórico
> `iavillamarin98-pred/ORA_entrega_F` y no debe confundirse con el PR #10
> posterior del repositorio oficial `gleiston-guerrero/Entrega-final-del-PFC`.

Se acordó el siguiente flujo de trabajo:

1. El autor realiza el cambio y abre el PR.
2. El reviewer revisa el diff y las evidencias.
3. Si hay errores, el reviewer deja observaciones.
4. El autor corrige.
5. El reviewer vuelve a comprobar.
6. El merge se realiza solo después de la aprobación.

### 3. Estado general del PFC

La version original de esta acta registro "Puntos cerrados: 27/37". No se
conserva en esta carpeta una fuente verificable para esa cifra, por lo que esta
revision posterior no la usa como dato probado.

- Punto parcial: #36 — Actas y revisión cruzada.

Puntos pendientes registrados como seguimiento de trabajo, sin que esta acta
los use para reconstruir una cifra total verificable:

- #9 — Cámara / FCM.
- #15 — Pipeline y publicación etiquetada.
- #16 — Observabilidad.
- #17 — Spark / speedup.
- #22 — Bibliografía.
- #26 — LICENSE + CITATION + README.
- #28 — Capturas Web / Mobile.
- #35 — APK firmado / release.
- #37 — Documento único.

### 4. Próximo trabajo

- El siguiente punto específico quedó por definir.
- Responsable: Isaías Urbina o Iván Villamarín.
- Reviewer: el participante que no haga el cambio.
- Rama: específica para el punto.
- Evidencia: código o documentación modificada, pruebas, CI en verde y evidencia requerida por la guía.
- Criterio de cierre: verificable desde el repositorio y con revisión cruzada antes del merge.

## Acuerdos

- Los futuros cambios se realizarán mediante PR con revisión de una persona distinta al autor.
- Las observaciones deben resolverse antes de aprobar.
- Las próximas reuniones también se registrarán de forma contemporánea.

## Decisiones

- Cerrar el punto #7 con la evidencia revisada.
- Mantener la revisión cruzada para los siguientes cambios.

## Riesgos

- Integrar cambios sin review.
- Marcar observaciones como resueltas sin comprobar la corrección.

## Evidencias

La captura `meet-revision-pr10.png` muestra la sesión activa de Google Meet a
las 22:14 durante la revision del estado ya fusionado del PR #10 del repositorio
historico `iavillamarin98-pred/ORA_entrega_F`.

![Sesion de Google Meet revisando el PR #10 historico ya fusionado](evidencias/acta-06/meet-revision-pr10.png)

La captura `pr10-aprobado-mergeado.png` documenta la aprobación de
`iavillamarin98-pred` y la integración del PR #10 del repositorio historico,
visibles a las 22:12 como eventos ya ocurridos antes de la revision de la
captura.

![PR #10 historico aprobado e integrado antes de la revision visible](evidencias/acta-06/pr10-aprobado-mergeado.png)

Nota de formato: `meet-revision-pr10.png` y `pr10-aprobado-mergeado.png`
conservan su extension historica `.png`, pero su contenido real esta codificado
como JPEG segun los magic bytes `FFD8FFE0`. No fueron renombrados ni
convertidos para preservar la trazabilidad de la evidencia.

## Cierre

- Hora final: 22:45 (UTC-05:00) del 15/09/2026.
- Isaías Urbina — conforme.
- Iván Villamarín — conforme.
