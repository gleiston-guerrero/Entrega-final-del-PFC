# ISO/IEC 25010:2023 — Compatibilidad

> **Antecedente / auditoría histórica.** Las secciones fechadas el 2026-09-04
> describen el SHA `cd61b64325480cbe132af7e56328f7fa5d8b99ef` y se conservan
> sin convertir su estado PARCIAL en un resultado del experimento posterior.

**Fecha de revisión:** 2026-09-04

**Rama:** `feature/entrega-4`

**HEAD auditado:** `cd61b64325480cbe132af7e56328f7fa5d8b99ef`

## Alcance y método

La evidencia distingue configuración, ejecución histórica y ejecución verificable del HEAD. La mera presencia de un proyecto Playwright o de un nivel SDK no demuestra que la aplicación haya funcionado correctamente en ese entorno. No se ejecutaron Playwright, Docker ni emuladores localmente durante esta actualización.

## Web

`apps/web/playwright.config.ts` configura tres proyectos:

| Proyecto | Motor | Estado en HEAD |
|---|---|---|
| `chromium` | Chromium/Blink | CONFIGURADO; sin ejecución del HEAD porque `integration` fue omitido |
| `firefox` | Firefox/Gecko | CONFIGURADO; sin ejecución del HEAD porque `integration` fue omitido |
| `webkit` | WebKit | CONFIGURADO; sin ejecución del HEAD porque `integration` fue omitido |

La suite actual contiene `auth.spec.ts`, `reservas-freddy.spec.ts` y `settings-theme-i18n.spec.ts`, además de sus fixtures. El workflow instala Chromium, Firefox y WebKit y ejecuta `npm run test:e2e` dentro del job `integration`.

Para el HEAD auditado existen dos ejecuciones CI consultables:

- push: [run 33838233548](https://github.com/gleiston-guerrero/Entrega-final-del-PFC/actions/runs/33838233548);
- pull request: [run 33838236394](https://github.com/gleiston-guerrero/Entrega-final-del-PFC/actions/runs/33838236394).

Ambas concluyeron con fallo. `Test web` y `Lint - backend and web` sí terminaron correctamente, pero fallaron jobs Backend y el job `integration` quedó omitido por sus dependencias. En consecuencia, el HEAD no aporta una ejecución Playwright verde en los tres motores. El resultado histórico 9/15 del 24/08/2026 no se atribuye al HEAD ni permite declarar compatibilidad total.

**Estado Web: PARCIAL.** La matriz de tres motores está configurada y las pruebas unitarias/build Web del HEAD pasaron en CI, pero falta una ejecución E2E verde y trazable para este SHA.

## Android

La configuración actual declara:

- `minSdk = 26`;
- `targetSdk = 34`;
- `compileSdk = 34`.

El job instrumentado usa Android API 29 (`google_apis`, x86_64, perfil Pixel 2), no API 34. Las pruebas instrumentadas versionadas incluyen QR, Incidentes, Reservas, DAO y migración Room.

En el run de push 33838233548, `Test mobile`, `Test mobile instrumented` y `Build mobile APK` terminaron correctamente. Se publicaron los artifacts `mobile-coverage-cd61b...`, `mobile-instrumented-results-cd61b...` y `pfc-debug-apk-cd61b...`. En el run paralelo de pull request, la prueba instrumentada falló; por ello la evidencia no es uniforme entre ambas ejecuciones concurrentes.

La configuración y una ejecución verde en API 29 sostienen funcionamiento observado dentro del rango API 26–34, pero no prueban cada versión, fabricante o dispositivo. El APK producido es debug, no una distribución release firmada.

**Estado Android: PARCIAL.** Existe evidencia CI real para API 29 y configuración compatible desde API 26, pero no una matriz de APIs/dispositivos ni una ejecución uniforme en ambos eventos.

## Conclusión

**Compatibilidad: PARCIAL.** Web configura Chromium, Firefox y WebKit, pero el HEAD no llegó a ejecutar el job E2E. Android sí cuenta con una corrida instrumentada verde en API 29 y artifact debug para el run de push, aunque el run de PR paralelo falló y no existe una matriz completa. Para cerrar la característica se requiere una ejecución CI integral verde del mismo SHA y conservar sus reportes por motor/API.

## Resultado experimental oficial E3

La campaña oficial ejecutó tres repeticiones completas por motor sobre el SHA
`fa7d75ec0f75573938bf46ed6a68f0aee99606ac`.

| Motor | Aprobados | Fallidos | Omitidos | Flaky | IC95 Wilson | Decisión |
|---|---:|---:|---:|---:|---|---|
| Chromium | 8/8 | 0 | 0 | 0 | [0,6755924350132556; 1,0] | CUMPLE en suite |
| Firefox | 8/8 | 0 | 0 | 0 | [0,6755924350132556; 1,0] | CUMPLE en suite |
| WebKit | 8/8 | 0 | 0 | 0 | [0,6755924350132556; 1,0] | CUMPLE en suite |

Cada motor tiene tres resúmenes exitosos e idénticos; se separa 3/3 de la
estimación Wilson basada en ocho casos distintos. El paquete compacto no
conserva identificadores individuales para verificar retrospectivamente la
identidad de cada caso. La decisión experimental acredita solo comportamiento
cross-browser dentro de la suite, versiones de motores y entorno ensayados: no
demuestra la característica ISO completa de coexistencia/interoperabilidad ni
reemplaza el antecedente Android/API 29. Véanse
[`analisis-e3.json`](../../experimentos/resultados/analisis-e3.json) y la
[`matriz de trazabilidad`](../../experimentos/resultados/TRAZABILIDAD-E3-E4.md).
