# Evidencia ISO/IEC 25010 — Seguridad

> **Antecedente / auditoría histórica.** Las secciones fechadas el 2026-09-04
> describen una revisión estática del SHA `cd61b64325480cbe132af7e56328f7fa5d8b99ef`.
> Se conservan para trazabilidad y no representan el resultado experimental E3
> posterior.

**Fecha de revisión:** 2026-09-04

**Rama:** `feature/entrega-4`
**HEAD auditado:** `cd61b64325480cbe132af7e56328f7fa5d8b99ef`

## Metodología

La revisión es estática y toma como fuente de verdad el código del HEAD indicado. Se inventarió cada combinación de método HTTP y ruta declarada en los controladores de Auth, Usuarios, Académico y Reservas. Se añadieron por separado `health`, `info` y `prometheus` de Auth, Usuarios, Académico, Reservas y API Gateway. Para cada operación se contrastaron el `SecurityConfig`, los filtros JWT, la validación de `X-Internal-Api-Key` y, cuando existe, el control de ámbito en la capa de servicio.

La matriz reproducible está en [`matriz-seguridad-endpoints.csv`](matriz-seguridad-endpoints.csv). Las operaciones `OPTIONS` de CORS no se contabilizan como operaciones de negocio. RBAC y ámbito institucional se cuentan por separado: poseer una autoridad no demuestra por sí mismo que se limite carrera, piso o identidad.

## Resultados del inventario

| Clasificación | Operaciones |
|---|---:|
| Operaciones de controlador | 183 |
| Actuator explícitos | 15 |
| Total auditado | 198 |
| Públicas de Auth | 5 |
| Externas que requieren JWT | 160 |
| Con RBAC explícito en la cadena HTTP | 145 |
| Internas con API key | 18 |
| Con ámbito institucional explícito identificado | 63 |

Los totales cuadran así: `183 = 5 públicas + 160 JWT + 18 internas`; al añadir 15 operaciones Actuator se obtienen 198 filas. El conteo de ámbito incluye controles de identidad, contexto académico, carrera del coordinador y piso del administrador de piso localizados en servicios; no incluye una mera consulta parametrizada por ID.

Distribución de operaciones de controlador: Auth 12, Usuarios 41, Académico 68 y Reservas 62.

## Autenticación

El API Gateway valida el Bearer JWT para las rutas externas no públicas y reenvía la cabecera al microservicio. Los servicios también disponen de filtro JWT y configuración stateless. Se exige token de acceso con firma, issuer y vigencia válidos; un refresh token no equivale a un access token.

Las cinco operaciones públicas reales pertenecen a `AuthController`: `login`, `refresh`, `logout`, `forgot-password` y `reset-password`. Son públicas porque forman parte del establecimiento, renovación, cierre o recuperación de credenciales. Ninguna operación de `/api/v1/auth/admin/**` es pública: exige `ROLE_ADMINISTRADOR`.

Los 18 endpoints `/api/v1/internal/**` no usan JWT de usuario. Spring los deja pasar hasta el controlador, donde se valida `X-Internal-Api-Key`: Auth aporta 4, Usuarios 9 y Académico 5. Deben permanecer fuera del perímetro público; la API key no sustituye un scope de usuario final.

## Autorización RBAC

Se identificaron 145 operaciones JWT con autoridad o rol explícito en el filtro HTTP: 3 en Auth, 28 en Usuarios, 63 en Académico y 51 en Reservas. Las 15 restantes siguen autenticadas, pero delegan decisiones adicionales a servicios o solo exigen autenticación en la cadena HTTP.

Académico ya no depende únicamente del Gateway: su `SecurityConfig` actual valida JWT y separa lectura y gestión mediante `ACADEMICO_LEER`, `LABORATORIO_LEER`, `EQUIPO_LEER`, `PLANIFICACION_GESTIONAR`, permisos de gestión y `ROLE_ADMINISTRADOR`. Esta es una diferencia sustancial frente a la evidencia histórica.

## Control de ámbito institucional

Los controles explícitos encontrados son:

- **Administrador:** acceso global únicamente donde el servicio reconoce `ROLE_ADMINISTRADOR`.
- **Administrador de piso:** `PoliticaAmbitoLaboratorio` resuelve su adscripción y compara el piso del laboratorio; Reservas, Solicitudes, bloqueos de Agenda y revisiones de planificación reutilizan esa política.
- **Coordinador:** `PlanificacionService` y `PlanificacionAgregadaService` derivan la carrera del contexto institucional autenticado y rechazan otra carrera.
- **Docente:** Asistencia valida que la reserva o bloque pertenezca al docente autenticado.
- **Estudiante:** Usuarios limita `mi-contexto`/`mis-contextos` al principal; Asistencia cruza identidad y contexto académico antes de mostrar horario o registrar presencia.

Académico aplica RBAC, pero no implementa por sí mismo scope de carrera o piso en sus catálogos. Eso se registra como `NINGUNO_EXPLICITO` en la matriz y no se presenta como aislamiento institucional.

## Semántica 401 y 403

- Ruta externa protegida sin JWT, con JWT inválido o con token que no sea de acceso: **401**.
- JWT válido sin rol/autoridad suficiente: **403**.
- Rol/autoridad válidos pero recurso fuera de carrera, piso, bloque, contexto o identidad cuando el servicio aplica ese control: **403**.
- Ruta interna sin API key o con clave inválida: **403** según los controladores internos actuales.

Evidencia automatizada existente: `GatewaySecurityIntegrationTests`, `JwtAuthenticationEntryPointTest`, `AdminUsuarioSecurityTest`, `UsuariosSecurityIntegrationTest`, `PerfilPropioSecurityTest`, `AcademicoSecurityIntegrationTest`, `ReservasSecurityIntegrationTest` y pruebas de controladores internos. Esta actualización no ejecutó dichas pruebas y no convierte su mera existencia en evidencia de una corrida del HEAD.

## Actuator

Se separaron 15 operaciones Actuator del negocio: `health`, `info` y `prometheus` en cinco componentes. Los `SecurityConfig` las declaran `permitAll` y los `application.yml` limitan la exposición a esas rutas. Que sean públicas en la aplicación exige restricción de red y revisión operativa, especialmente para Prometheus; no se contabilizan dentro de las 160 operaciones JWT.

## Limitaciones y brechas observadas

- La evidencia es estática; no demuestra una campaña dinámica completa de 401/403 sobre las 198 filas.
- En Reservas, los `GET` de Agenda consultan por laboratorio pero `AgendaServiceImpl.listar` no invoca `PoliticaAmbitoLaboratorio`; la autoridad existe, pero el aislamiento por piso no queda demostrado en esa ruta.
- En Incidentes, un actor con permiso gestor obtiene lectura amplia; no se encontró filtro de piso equivalente a `PoliticaAmbitoLaboratorio` para administrador de piso.
- En Usuarios, algunas consultas de docente quedan como `authenticated` en la cadena HTTP; no todas acreditan ownership o carrera en el propio endpoint.
- Académico tiene defensa JWT/RBAC interna, pero no scope institucional por carrera/piso.
- Los endpoints internos dependen de un secreto compartido y de su aislamiento de red; no se evaluaron rotación, rate limiting, MFA, escaneo SCA ni secret scanning.
- Actuator/Prometheus público y los detalles efectivos expuestos deben verificarse en el despliegue real.

## Conclusión ISO/IEC 25010

**Estado: PARCIAL.** El HEAD demuestra autenticación JWT en las 160 operaciones externas protegidas, RBAC explícito en 145 y API key en 18 operaciones internas. También existen controles de ámbito concretos en 63 operaciones. Sin embargo, RBAC y scope no son uniformes en todos los dominios, se identifican brechas de aislamiento potencial en Agenda e Incidentes, y falta una validación dinámica integral. Por ello no corresponde declarar seguridad perfecta ni cumplimiento total.

## Resultado experimental oficial E3

La campaña dinámica oficial se ejecutó tres veces sobre el software del SHA
`fa7d75ec0f75573938bf46ed6a68f0aee99606ac`. Evaluó siete decisiones
prerregistradas por repetición, para 21 observaciones binarias en total.

| Indicador | Resultado |
|---|---:|
| Casos distintos correctos | 7/7 |
| Proporción observada | 1,0 |
| IC95 Wilson (n=7) | [0,6456695648259365; 1,0] |
| Accesos incorrectamente permitidos | 0 |
| Accesos incorrectamente rechazados | 0 |
| Flaky | 0 |
| Repetibilidad | 3/3; mismo conjunto y mismos resultados |
| Decisión | **CUMPLE en alcance dinámico reducido** |

El resultado **CUMPLE** dentro de las siete decisiones dinámicas, fixtures,
Gateway y entorno ensayados. Las tres repeticiones son deterministas: no se
sumaron como 21 observaciones independientes. No garantiza seguridad universal
ni reemplaza las limitaciones de la auditoría estática anterior. Las 198 filas
de la matriz son antecedente estático/análisis de superficie, no pruebas
dinámicas; las rutas dinámicas se limitan a login, reservas y solicitudes,
incluidas revisión y propuesta.
La fuente consolidada es
[`analisis-e3.json`](../../experimentos/resultados/analisis-e3.json) y su cadena
de evidencia se documenta en
[`TRAZABILIDAD-E3-E4.md`](../../experimentos/resultados/TRAZABILIDAD-E3-E4.md).
