package ec.edu.scli.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import ec.edu.scli.contracts.RuntimeContractVerifier.Operation;
import org.springframework.core.DefaultParameterNameDiscoverer;
import org.springframework.core.MethodParameter;
import org.springframework.core.ResolvableType;
import org.springframework.core.annotation.AnnotatedElementUtils;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.ValueConstants;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.mvc.method.RequestMappingInfo;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

import java.math.BigDecimal;
import java.lang.reflect.RecordComponent;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Deriva la firma real de parametros y de estructura de respuesta paginada
 * desde los HandlerMethod compilados (reflexion sobre clases Java reales) y
 * la contrasta contra el contrato OpenAPI. No comparte logica ni datos con el
 * extractor regex de scripts/validar-contratos-openapi.py: por eso puede
 * detectar un contrato correcto segun el codigo que el extractor regex
 * hubiera rechazado (o un contrato incorrecto que el extractor no detecta).
 *
 * El tipo de elemento T de Page&lt;T&gt;/PaginaResponse&lt;T&gt; se deriva en
 * tiempo de ejecucion con {@link ResolvableType} sobre el metodo compilado;
 * nunca se hardcodea el nombre de un DTO concreto. Las propiedades esperadas
 * de PaginaResponse se derivan por reflexion de sus {@code RecordComponent}
 * reales, no de una lista literal en este verificador.
 */
public final class SchemaContractVerifier {

    private SchemaContractVerifier() {
    }

    /** Los 9 campos que Spring Data serializa por defecto para {@link Page}: son parte fija de esa API, no un DTO del proyecto. */
    private static final List<String> PROPIEDADES_PAGE = List.of(
            "content", "totalElements", "totalPages", "number", "size", "numberOfElements", "first", "last", "empty");

    public enum TipoPaginacion { NINGUNA, PAGE, PAGINA_RESPONSE }

    public record ParameterSignature(String name, boolean required, String type, Object defaultValue) {
    }

    public record FirmaPaginacion(
            TipoPaginacion tipo, String propiedadContenido, List<String> propiedadesEsperadas, String nombreClaseElemento) {
        static FirmaPaginacion ninguna() {
            return new FirmaPaginacion(TipoPaginacion.NINGUNA, null, List.of(), null);
        }
    }

    public record OperationSignature(Operation operation, FirmaPaginacion paginacion, List<ParameterSignature> queryParams) {
    }

    public static List<OperationSignature> runtimeSignatures(
            RequestMappingHandlerMapping mappings, String applicationPackage) {
        List<OperationSignature> signatures = new ArrayList<>();
        for (Map.Entry<RequestMappingInfo, HandlerMethod> entry : mappings.getHandlerMethods().entrySet()) {
            HandlerMethod handlerMethod = entry.getValue();
            Class<?> beanType = handlerMethod.getBeanType();
            if (!beanType.getPackageName().startsWith(applicationPackage)
                    || !AnnotatedElementUtils.hasAnnotation(beanType, RestController.class)) {
                continue;
            }
            RequestMappingInfo info = entry.getKey();
            Set<String> paths = info.getPatternValues().isEmpty() ? Set.of("/") : info.getPatternValues();
            Set<RequestMethod> methods = info.getMethodsCondition().getMethods();
            FirmaPaginacion paginacion = firmaPaginacion(handlerMethod);
            List<ParameterSignature> queryParams = parametrosQuery(handlerMethod);
            for (String path : paths) {
                for (RequestMethod method : methods) {
                    signatures.add(new OperationSignature(
                            new Operation(method.name(), path), paginacion, queryParams));
                }
            }
        }
        return signatures;
    }

    private static ResolvableType tipoRetornoResuelto(HandlerMethod handlerMethod) {
        ResolvableType tipo = ResolvableType.forMethodReturnType(handlerMethod.getMethod());
        if (ResponseEntity.class.isAssignableFrom(tipo.toClass())) {
            tipo = tipo.getGeneric(0);
        }
        return tipo;
    }

    private static FirmaPaginacion firmaPaginacion(HandlerMethod handlerMethod) {
        ResolvableType tipoResuelto = tipoRetornoResuelto(handlerMethod);
        Class<?> raw = tipoResuelto.resolve();
        if (raw == null) {
            return FirmaPaginacion.ninguna();
        }
        if (Page.class.isAssignableFrom(raw)) {
            return new FirmaPaginacion(TipoPaginacion.PAGE, "content", PROPIEDADES_PAGE, nombreElemento(tipoResuelto));
        }
        if (raw.isRecord() && "PaginaResponse".equals(raw.getSimpleName())) {
            String campoContenido = campoContenido(raw);
            return new FirmaPaginacion(
                    TipoPaginacion.PAGINA_RESPONSE,
                    campoContenido != null ? campoContenido : "contenido",
                    propiedadesDeRecord(raw),
                    nombreElemento(tipoResuelto));
        }
        return FirmaPaginacion.ninguna();
    }

    private static String nombreElemento(ResolvableType tipoContenedor) {
        Class<?> elemento = tipoContenedor.getGeneric(0).resolve();
        return elemento == null ? null : elemento.getSimpleName();
    }

    /** Propiedades reales del record, derivadas por reflexion (no hardcodeadas). */
    private static List<String> propiedadesDeRecord(Class<?> tipoRecord) {
        List<String> nombres = new ArrayList<>();
        for (RecordComponent componente : tipoRecord.getRecordComponents()) {
            nombres.add(componente.getName());
        }
        return nombres;
    }

    /** El componente de tipo coleccion del record es el campo de contenido paginado, derivado por reflexion. */
    private static String campoContenido(Class<?> tipoRecord) {
        for (RecordComponent componente : tipoRecord.getRecordComponents()) {
            if (Collection.class.isAssignableFrom(componente.getType())) {
                return componente.getName();
            }
        }
        return null;
    }

    private static List<ParameterSignature> parametrosQuery(HandlerMethod handlerMethod) {
        List<ParameterSignature> params = new ArrayList<>();
        DefaultParameterNameDiscoverer discoverer = new DefaultParameterNameDiscoverer();
        for (MethodParameter parameter : handlerMethod.getMethodParameters()) {
            parameter.initParameterNameDiscovery(discoverer);
            if (Pageable.class.isAssignableFrom(parameter.getParameterType())) {
                params.add(new ParameterSignature("page", false, "integer", 0));
                params.add(new ParameterSignature("size", false, "integer", 20));
                params.add(new ParameterSignature("sort", false, "array", null));
                continue;
            }
            RequestParam requestParam = parameter.getParameterAnnotation(RequestParam.class);
            if (requestParam == null) {
                continue;
            }
            String name = !requestParam.name().isEmpty() ? requestParam.name()
                    : !requestParam.value().isEmpty() ? requestParam.value()
                    : parameter.getParameterName();
            boolean tieneDefault = !ValueConstants.DEFAULT_NONE.equals(requestParam.defaultValue());
            boolean required = requestParam.required() && !tieneDefault;
            String tipo = tipoOpenApi(parameter.getParameterType());
            Object valorPorDefecto = tieneDefault ? convertirDefault(requestParam.defaultValue(), tipo) : null;
            params.add(new ParameterSignature(name, required, tipo, valorPorDefecto));
        }
        return params;
    }

    /** {@code null} cuando el tipo Java no tiene una correspondencia simple derivable (p. ej. enums propios). */
    private static String tipoOpenApi(Class<?> tipoJava) {
        if (tipoJava == int.class || tipoJava == Integer.class || tipoJava == long.class || tipoJava == Long.class) {
            return "integer";
        }
        if (tipoJava == double.class || tipoJava == Double.class || tipoJava == float.class || tipoJava == Float.class
                || BigDecimal.class.isAssignableFrom(tipoJava)) {
            return "number";
        }
        if (tipoJava == boolean.class || tipoJava == Boolean.class) {
            return "boolean";
        }
        if (tipoJava == String.class || UUID.class.isAssignableFrom(tipoJava)
                || LocalDate.class.isAssignableFrom(tipoJava) || LocalDateTime.class.isAssignableFrom(tipoJava)) {
            return "string";
        }
        return null;
    }

    private static Object convertirDefault(String valor, String tipo) {
        if ("integer".equals(tipo)) {
            try {
                return Integer.parseInt(valor);
            } catch (NumberFormatException ignored) {
                return valor;
            }
        }
        if ("number".equals(tipo)) {
            try {
                return Double.parseDouble(valor);
            } catch (NumberFormatException ignored) {
                return valor;
            }
        }
        if ("boolean".equals(tipo)) {
            return Boolean.parseBoolean(valor);
        }
        return valor;
    }

    public static Map<Operation, JsonNode> operationsIndex(JsonNode document) {
        Map<Operation, JsonNode> index = new HashMap<>();
        document.path("paths").fields().forEachRemaining(pathEntry -> {
            String rawPath = pathEntry.getKey();
            pathEntry.getValue().fields().forEachRemaining(methodEntry -> {
                try {
                    Operation operation = new Operation(methodEntry.getKey(), rawPath);
                    index.put(operation, methodEntry.getValue());
                } catch (IllegalArgumentException ignored) {
                    // no es una clave de metodo HTTP (p. ej. "parameters" a nivel de path)
                }
            });
        });
        return index;
    }

    private static JsonNode resolverSchema(JsonNode schema, JsonNode document) {
        JsonNode actual = schema;
        int saltos = 0;
        while (actual.has("$ref") && saltos < 5) {
            String ref = actual.path("$ref").asText();
            actual = document.at(ref.startsWith("#") ? ref.substring(1) : ref);
            saltos++;
        }
        return actual;
    }

    public static List<String> compareSchemas(List<OperationSignature> runtimeSignatures, JsonNode openApiDocument) {
        Map<Operation, JsonNode> operationsIndex = operationsIndex(openApiDocument);
        List<String> problems = new ArrayList<>();
        for (OperationSignature signature : runtimeSignatures) {
            JsonNode operationNode = operationsIndex.get(signature.operation());
            if (operationNode == null) {
                // la completitud metodo+ruta la acredita RuntimeContractVerifier por separado
                continue;
            }
            if (signature.paginacion().tipo() != TipoPaginacion.NINGUNA) {
                problems.addAll(compararPaginacion(signature, operationNode, openApiDocument));
            }
            problems.addAll(compararQueryParams(signature, operationNode));
        }
        return problems;
    }

    private static List<String> compararPaginacion(
            OperationSignature signature, JsonNode operationNode, JsonNode document) {
        List<String> problems = new ArrayList<>();
        JsonNode schemaDeclarado = operationNode.path("responses").path("200")
                .path("content").path("application/json").path("schema");
        if ("array".equals(schemaDeclarado.path("type").asText(null))) {
            problems.add("SCHEMA_PAGINADO_COMO_ARRAY " + signature.operation());
            return problems;
        }
        JsonNode schemaResuelto = resolverSchema(schemaDeclarado, document);
        if (!"object".equals(schemaResuelto.path("type").asText(null))) {
            problems.add("SCHEMA_PAGINADO_SIN_OBJETO " + signature.operation());
            return problems;
        }
        JsonNode propiedades = schemaResuelto.path("properties");
        for (String propiedadEsperada : signature.paginacion().propiedadesEsperadas()) {
            if (!propiedades.has(propiedadEsperada)) {
                problems.add("SCHEMA_PAGINADO_PROPIEDAD_FALTANTE " + signature.operation() + " " + propiedadEsperada);
            }
        }
        String campoContenido = signature.paginacion().propiedadContenido();
        JsonNode contenido = propiedades.path(campoContenido);
        if (contenido.isMissingNode()) {
            problems.add("SCHEMA_PAGINADO_SIN_CONTENIDO " + signature.operation() + " " + campoContenido);
            return problems;
        }
        if (!"array".equals(contenido.path("type").asText(null))) {
            problems.add("SCHEMA_PAGINADO_CONTENIDO_NO_ARRAY " + signature.operation());
            return problems;
        }
        String elementoEsperado = signature.paginacion().nombreClaseElemento();
        String refItems = contenido.path("items").path("$ref").asText(null);
        if (elementoEsperado != null && (refItems == null || !refItems.endsWith("/" + elementoEsperado))) {
            problems.add("SCHEMA_PAGINADO_ELEMENTO_INCORRECTO " + signature.operation()
                    + " esperado=" + elementoEsperado + " declarado=" + refItems);
        }
        return problems;
    }

    private static List<String> compararQueryParams(OperationSignature signature, JsonNode operationNode) {
        List<String> problems = new ArrayList<>();
        Map<String, JsonNode> declarados = new HashMap<>();
        for (JsonNode parameterNode : operationNode.path("parameters")) {
            if ("query".equals(parameterNode.path("in").asText())) {
                declarados.put(parameterNode.path("name").asText(), parameterNode);
            }
        }
        for (ParameterSignature esperado : signature.queryParams()) {
            JsonNode declarado = declarados.get(esperado.name());
            if (declarado == null) {
                problems.add("QUERY_PARAM_FALTANTE " + signature.operation() + " " + esperado.name());
                continue;
            }
            boolean requiredDeclarado = declarado.path("required").asBoolean(false);
            if (requiredDeclarado != esperado.required()) {
                problems.add("QUERY_PARAM_REQUIRED_INCORRECTO " + signature.operation()
                        + " " + esperado.name() + " esperado=" + esperado.required()
                        + " declarado=" + requiredDeclarado);
            }
            JsonNode schemaParametro = declarado.path("schema");
            if (esperado.type() != null) {
                String tipoDeclarado = schemaParametro.path("type").asText(null);
                if (!esperado.type().equals(tipoDeclarado)) {
                    problems.add("QUERY_PARAM_TIPO_INCORRECTO " + signature.operation() + " " + esperado.name()
                            + " esperado=" + esperado.type() + " declarado=" + tipoDeclarado);
                }
            }
            if (esperado.defaultValue() != null) {
                JsonNode defaultNode = schemaParametro.path("default");
                String defaultDeclarado = defaultNode.isMissingNode() ? null : defaultNode.asText();
                String defaultEsperado = String.valueOf(esperado.defaultValue());
                if (!defaultEsperado.equals(defaultDeclarado)) {
                    problems.add("QUERY_PARAM_DEFAULT_INCORRECTO " + signature.operation() + " " + esperado.name()
                            + " esperado=" + defaultEsperado + " declarado=" + defaultDeclarado);
                }
            }
        }
        return problems;
    }

    public static void assertMatches(List<OperationSignature> runtimeSignatures, JsonNode openApiDocument) {
        List<String> problems = compareSchemas(runtimeSignatures, openApiDocument);
        if (!problems.isEmpty()) {
            throw new AssertionError(String.join(System.lineSeparator(), problems));
        }
    }
}
