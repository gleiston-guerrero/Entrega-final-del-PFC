# Contratos OpenAPI de SCLI

Esta carpeta contiene los contratos de los cuatro servicios HTTP y de la fachada del API Gateway. Los snapshots corresponden al código de `feature/entrega-4` en el SHA `cef50709177eee2c41b53f0000f9d936ddb373df`.

| Archivo | Alcance | Productor |
|---|---|---|
| `auth-service-openapi.json` | API de autenticación y administración interna | Extracción determinista de controladores y DTO de `auth-service` |
| `usuarios-service-openapi.json` | API externa e interna de usuarios | Extracción determinista de controladores y DTO de `usuarios-service` |
| `academico-laboratorios-service-openapi.json` | API externa e interna académica | Extracción determinista de controladores y DTO de `academico-laboratorios-service` |
| `reservas-solicitudes-service-openapi.json` | Reservas, solicitudes, agenda, asistencia y planificación | Extracción determinista de controladores y DTO de `reservas-solicitudes-service` |
| `api-gateway-openapi.json` | Fachada que el Gateway enruta hacia los servicios | Composición de los contratos anteriores según `GatewayRoutes.java` |

## Producción reproducible del snapshot

Los servicios requieren infraestructura externa para arrancar y el repositorio no define un perfil común que permita obtener `/v3/api-docs` de los cuatro de forma aislada. Para evitar cambios funcionales o snapshots dependientes del entorno, los contratos se producen con Python estándar desde las anotaciones Spring MVC y los DTO vigentes:

```bash
python scripts/validar-contratos-openapi.py --generate
```

El productor descubre los controladores en `src/main/java`, combina `@RequestMapping` con `@GetMapping`, `@PostMapping`, `@PutMapping`, `@PatchMapping` y `@DeleteMapping`, y obtiene parámetros, cuerpos y tipos de respuesta de las firmas Java. También extrae las propiedades de records, clases DTO y enums. No toma endpoints de documentos históricos.

La generación crea OpenAPI 3.1.0. La versión de Reservas es 1.1.0, de acuerdo con su `OpenApiConfig`; los restantes contratos comienzan en 1.0.0 como versión documental de sus snapshots.

Para validar sin escribir archivos:

```bash
python scripts/validar-contratos-openapi.py
```

La validación Python comprueba JSON, campos básicos, métodos HTTP, `operationId`, referencias locales, esquemas de seguridad y que el snapshot no derive respecto de su productor determinista. En el Gateway contrasta la composición documental y comprueba que estén presentes los seis marcadores de familias. Cualquier deriva termina con código distinto de cero.

Este mecanismo se conserva por trazabilidad y generación, pero **no es la fuente autoritativa de completitud método+ruta**. Históricamente, el mismo extractor por expresiones regulares producía el conjunto esperado y lo comparaba con el snapshot; una anotación no reconocida podía quedar fuera de ambos lados. Esa comprobación era circular para demostrar completitud.

## Validación independiente contra Spring runtime

La fuente autoritativa actual son pruebas Java ejecutadas por `mvn verify` en los cinco módulos. Los cuatro servicios arrancan su `ApplicationContext` de prueba, obtienen `RequestMappingHandlerMapping` y comparan bidireccionalmente los `RequestMappingInfo` procesados por Spring con el OpenAPI versionado. Se filtran solo los `@RestController` del paquete propio. Spring resuelve los prefijos de clase, mappings compuestos, varios paths y métodos, `@RequestMapping(method=...)` y los shortcuts HTTP; no se leen fuentes `.java`, no se usan regex y no se comparte código con `discover_operations()`.

La utilidad común normaliza únicamente el nombre de las variables de path y reporta `MISSING_IN_CONTRACT`, `EXTRA_IN_CONTRACT`, `METHOD_MISMATCH`, `PATH_MISMATCH` y `DUPLICATE_OPERATION`. Sus pruebas negativas alteran colecciones en memoria, nunca los cinco contratos.

El resultado independiente es Auth 12/12, Usuarios 44/44, Académico 71/71 y Reservas 79/79 con ARBITER habilitado. Reservas tiene 77 operaciones activas por defecto: las dos rutas bajo `/api/v1/internal/experimentos/arbiter` solo aparecen con `app.experimental.arbiter.enabled=true`. Por tanto, el contrato de 79 representa la **superficie habilitable**, no la superficie activa predeterminada. Una segunda prueba arranca el contexto con el flag deshabilitado y acredita 77 operaciones y ausencia de ambas rutas.

El Gateway usa `RouterFunction`, no controladores MVC. Su prueba forma la población desde los contratos de backend previamente contrastados con Spring runtime y envía cada operación mediante `MockMvc` a los routers reales. `ProxyExchangeHandlerFunction` está sustituido por un doble Mockito que devuelve 204 y registra el backend y la ruta transformada; no se levantan servicios locales ni se realiza una llamada de red. La definición formal de completitud es bidireccional: todas las operaciones runtime aceptadas por el `RouterFunction` deben aparecer en OpenAPI y todas las operaciones documentadas deben ser aceptadas, incluyendo los alias explícitos realmente enrutados. El resultado es 182 operaciones canónicas, 8 alias Auth y 34 alias Usuarios: 224/224.

No es necesario modificar el workflow: el job matricial existente ejecuta `mvn verify` sin flags opcionales para los cinco módulos en cada `push` y `pull_request`; una discrepancia hace fallar el pipeline.

## Seguridad representada

Las rutas externas protegidas declaran `bearerAuth`, con esquema HTTP Bearer y formato JWT. Las operaciones públicas de login, renovación, cierre de sesión y recuperación de contraseña no declaran JWT. Las APIs internas declaran `internalApiKey`, un encabezado `X-Internal-Api-Key`, en lugar de Bearer. El contrato del Gateway excluye las rutas internas porque no forman parte de la fachada externa.

Los alias `/auth-service/**` y `/usuarios-service/**` continúan en `GatewayRoutes.java`; sus operaciones externas se documentan como obsoletas y de compatibilidad heredada. El Gateway elimina ese primer segmento antes de enviar la solicitud. Las rutas internas de Usuarios están excluidas expresamente del alias por el propio código de routing.

## OpenAPI, Pact y alcance

OpenAPI describe la superficie HTTP, sus parámetros, cuerpos, respuestas y mecanismos de autenticación. Los tests Pact del repositorio verifican interacciones concretas entre consumidores y proveedores. Un contrato no sustituye al otro: OpenAPI ofrece el inventario de interfaz y Pact comprueba escenarios de integración seleccionados.

Los cuatro contratos de servicio incluyen sus APIs externas e internas. El contrato del Gateway representa únicamente rutas que el código de routing expone y reutiliza los schemas de los servicios; no atribuye controladores propios al Gateway.

La extracción estática no ejecuta validaciones de negocio ni demuestra que todos los códigos de error ocurran en producción. Las respuestas documentadas son las derivables de las firmas y construcciones explícitas de los controladores. Los contratos deben regenerarse y pasar tanto la validación estructural Python como la validación independiente Spring cuando cambien controladores, DTO, seguridad o rutas del Gateway.
