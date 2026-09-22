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

El Gateway usa `RouterFunction`, no controladores MVC. Su prueba forma la población desde los contratos de backend previamente contrastados con Spring runtime y envía cada operación mediante `MockMvc` a los routers reales. `ProxyExchangeHandlerFunction` está sustituido por un doble Mockito que devuelve 204 y registra el backend y la ruta transformada; no se levantan servicios locales ni se realiza una llamada de red. La definición formal de completitud es bidireccional: todas las operaciones runtime aceptadas por el `RouterFunction` deben aparecer en OpenAPI y todas las operaciones documentadas deben ser aceptadas, incluyendo los alias explícitos realmente enrutados. El Gateway aplica además una allowlist método+ruta cargada desde el artefacto generado `services/api-gateway/src/main/resources/gateway-route-catalog.json`; el catálogo se deriva de este snapshot y su hash y cantidad se verifican en la prueba. El resultado es 183 operaciones canónicas, 8 alias Auth y 34 alias Usuarios: 225/225.

Además, los seis beans delegan la construcción completa en `GatewayRoutes.rutaContratada`.
El helper construye `.route(..., http())` con la condición obligatoria
`GatewayRouteCatalog.accepts(method, path) && scope.test(path)`; el alcance solo
recibe el path. Conserva destinos y `stripPrefix` de los alias.
`RouterFunctionCatalogGuardTest` inspecciona el bytecode de producción mediante
ASM: exige delegación en ese helper, rechaza llamadas de construcción o
composición de routers Spring fuera de él (también indirectas) y comprueba que
el helper alcanza el catálogo. No interpreta operadores del código fuente ni
pretende demostrar por alcanzabilidad la semántica de una expresión booleana.
`ContractedRouteTest` prueba el router real: rechaza
`/api/v1/sin-contrato/recurso` incluso con alcance siempre verdadero, acepta una
operación catalogada con alcance compatible y la rechaza con alcance falso.

CI ejecuta las pruebas unitarias Python del generador en
`validate-openapi-contracts`, además de validar los snapshots. Este job es una
dependencia de `publish-release`; se ejecuta también en pushes de tags `v*`,
sin filtro de ramas a nivel del job. El job matricial conserva `mvn verify`
para los cinco módulos.

## Validación independiente de schemas y parámetros

La completitud método+ruta no implica que los *schemas* de respuesta ni los
parámetros de consulta sean correctos: ambos se derivan del mismo extractor
regex que genera el snapshot, por lo que compararlo contra sí mismo no prueba
nada sobre su exactitud semántica. Para eso existe `SchemaContractVerifier`
(`tests/openapi-runtime/src/main/java/ec/edu/scli/contracts/SchemaContractVerifier.java`, única fuente canónica): usa reflexión sobre los `HandlerMethod` que Spring
ya resolvió para obtener, del código compilado y no de texto Java, (a) si el
tipo de retorno real es `Page<T>` o `PaginaResponse<T>` y (b) el nombre real,
`required` efectivo y `defaultValue` de cada `@RequestParam`, así como los
parámetros `page`/`size`/`sort` cuando el controlador recibe `Pageable`. Esa
firma se contrasta contra el JSON publicado. Las pruebas
`OpenApiSchemaContractTest` de Auth, Académico, Usuarios y Reservas ejecutan esta
comprobación en cada `mvn verify`. El verificador exige un objeto con las nueve
propiedades de `Page` o todos los componentes reales del record
`PaginaResponse`, un contenido de tipo array y la referencia al elemento `T`
derivado mediante `ResolvableType`. No basta con sustituir el array por
cualquier objeto. Con `MethodParameter` contrasta nombres, obligatoriedad,
tipos simples y defaults derivables de los parámetros compilados.

Los cuatro servicios incorporan `../../tests/openapi-runtime/src/main/java`
como fuente de pruebas mediante `build-helper-maven-plugin:add-test-source`
en `generate-test-sources`. No hay copias locales de `SchemaContractVerifier`.
También se retiraron las cuatro copias idénticas de `RuntimeContractVerifier`
para evitar clases duplicadas al compilar esa carpeta; ambos verificadores se
compilan desde la fuente compartida, sin copiar archivos en CI ni usar symlinks.

Se corrigieron 25 GET paginados de backend: 14 `Page<T>` y 11
`PaginaResponse<T>`, además de 23 parámetros mal nombrados. `pagina`,
`tamanio` y `rangoMinutos` son enteros opcionales con defaults 0, 20 y 60.
Para `Pageable`, `page` y `size` son enteros opcionales con defaults 0 y 20;
`sort` es un array opcional de strings sin default. No existen overrides de
estos defaults en las anotaciones ni en la configuración actual del proyecto.

La validación previa acreditó cuatro mutaciones negativas, todas revertidas:
un objeto paginado con propiedades falsas, la ausencia de `totalPaginas` en
`PaginaResponse`, un default incorrecto de `pagina` y un `RouterFunction`
con una ruta arbitraria que omitía el catálogo. Cada una hizo fallar su prueba
independiente. Estas evidencias no dependen de regenerar el snapshot.

## Seguridad representada

Las rutas externas protegidas declaran `bearerAuth`, con esquema HTTP Bearer y formato JWT. Las operaciones públicas de login, renovación, cierre de sesión y recuperación de contraseña no declaran JWT. Las APIs internas declaran `internalApiKey`, un encabezado `X-Internal-Api-Key`, en lugar de Bearer. El contrato del Gateway excluye las rutas internas porque no forman parte de la fachada externa.

Los alias `/auth-service/**` y `/usuarios-service/**` continúan en `GatewayRoutes.java`; sus operaciones externas se documentan como obsoletas y de compatibilidad heredada. El Gateway elimina ese primer segmento antes de enviar la solicitud. Las rutas internas de Usuarios están excluidas expresamente del alias por el propio código de routing.

## OpenAPI, Pact y alcance

OpenAPI describe la superficie HTTP; sus parámetros de consulta relevantes (incluidos `pagina`/`tamanio`/`rangoMinutos` y `page`/`size`/`sort` para `Pageable`) y los schemas de respuesta paginada se describen correctamente solo a partir de la corrección de este punto, y esa afirmación se sostiene en `SchemaContractVerifier`, no en la comparación del extractor Python contra sí mismo. Los tests Pact del repositorio verifican interacciones concretas entre consumidores y proveedores. Un contrato no sustituye al otro: OpenAPI ofrece el inventario de interfaz y Pact comprueba escenarios de integración seleccionados.

Los cuatro contratos de servicio incluyen sus APIs externas e internas. El contrato del Gateway representa únicamente rutas que el código de routing expone y reutiliza los schemas de los servicios; no atribuye controladores propios al Gateway.

La extracción estática no ejecuta validaciones de negocio ni demuestra que todos los códigos de error ocurran en producción. Las respuestas documentadas son las derivables de las firmas y construcciones explícitas de los controladores. Los contratos deben regenerarse y pasar tanto la validación estructural Python como la validación independiente Spring cuando cambien controladores, DTO, seguridad o rutas del Gateway.

## Verificación del cierre de #30

Validación local ejecutada en Windows con Maven y Java 21:

- `validar-contratos-openapi.py`: OK, cero errores estructurales.
- `test_validar_contratos_openapi.py`: 5 pruebas, todas correctas.
- `api-gateway` (`mvn test`): 41 pruebas, sin fallos, errores ni omisiones.
- `OpenApiSchemaContractTest`: 1 prueba correcta en cada uno de Auth, Usuarios,
  Académico y Reservas. Los cuatro registros de entradas del compilador apuntan
  a la fuente canónica compartida de `SchemaContractVerifier`.
- Dos mutaciones temporales de producción hicieron fallar el guard y nombraron
  `bypassDocenteTemporal` (consulta el catálogo y el helper, pero construye otra
  ruta con una alternativa booleana) y `sinHelperTemporal` (omite el helper).
  Ambas se retiraron antes de la ejecución final satisfactoria.
