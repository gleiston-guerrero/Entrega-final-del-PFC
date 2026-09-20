package ec.edu.scli.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.MissingNode;
import ec.edu.scli.contracts.RuntimeContractVerifier.Operation;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import org.springframework.core.DefaultParameterNameDiscoverer;
import org.springframework.core.MethodParameter;
import org.springframework.core.ResolvableType;
import org.springframework.core.annotation.AnnotatedElementUtils;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.ValueConstants;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.mvc.method.RequestMappingInfo;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.lang.reflect.RecordComponent;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Verifica schemas OpenAPI contra HandlerMethod compilados. La validacion deriva
 * requests, responses, propiedades y tipos desde clases Java reales; no reutiliza
 * la logica del extractor Python que genera snapshots.
 */
public final class SchemaContractVerifier {

    private SchemaContractVerifier() {
    }

    private static final List<String> PROPIEDADES_PAGE = List.of(
            "content", "totalElements", "totalPages", "number", "size", "numberOfElements", "first", "last", "empty");

    public enum TipoPaginacion { NINGUNA, PAGE, PAGINA_RESPONSE }

    public enum BodyKind { REQUEST, RESPONSE, SCHEMA }

    public record ParameterSignature(String name, boolean required, String type, Object defaultValue) {
    }

    public record FirmaPaginacion(
            TipoPaginacion tipo, String propiedadContenido, List<String> propiedadesEsperadas, String nombreClaseElemento) {
        static FirmaPaginacion ninguna() {
            return new FirmaPaginacion(TipoPaginacion.NINGUNA, null, List.of(), null);
        }
    }

    public record BodySignature(String location, ResolvableType type, BodyKind kind) {
    }

    private static final JacksonBehavior JACKSON_BEHAVIOR = JacksonBehavior.detect();

    public record OperationSignature(
            Operation operation,
            FirmaPaginacion paginacion,
            List<ParameterSignature> queryParams,
            List<BodySignature> requestBodies,
            List<BodySignature> responseBodies) {
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
            List<BodySignature> requests = requestBodies(handlerMethod);
            List<BodySignature> responses = responseBodies(handlerMethod);
            for (String path : paths) {
                for (RequestMethod method : methods) {
                    signatures.add(new OperationSignature(
                            new Operation(method.name(), path), paginacion, queryParams, requests, responses));
                }
            }
        }
        return signatures;
    }

    private static ResolvableType tipoRetornoResuelto(HandlerMethod handlerMethod) {
        return unwrapResponseEntity(ResolvableType.forMethodReturnType(handlerMethod.getMethod()));
    }

    private static ResolvableType unwrapResponseEntity(ResolvableType type) {
        Class<?> raw = type.resolve();
        if (raw != null && ResponseEntity.class.isAssignableFrom(raw)) {
            return type.getGeneric(0);
        }
        return type;
    }

    private static List<BodySignature> responseBodies(HandlerMethod handlerMethod) {
        ResolvableType type = tipoRetornoResuelto(handlerMethod);
        if (!debeValidar(type)) {
            return List.of();
        }
        return List.of(new BodySignature("response", type, BodyKind.RESPONSE));
    }

    private static List<BodySignature> requestBodies(HandlerMethod handlerMethod) {
        List<BodySignature> bodies = new ArrayList<>();
        for (MethodParameter parameter : handlerMethod.getMethodParameters()) {
            if (parameter.hasParameterAnnotation(RequestBody.class)) {
                ResolvableType type = ResolvableType.forMethodParameter(parameter);
                if (!debeValidar(type)) {
                    continue;
                }
                bodies.add(new BodySignature("requestBody", type, BodyKind.REQUEST));
            }
        }
        return bodies;
    }

    private static boolean debeValidar(ResolvableType type) {
        Class<?> raw = type.resolve();
        if (raw == null || raw == Void.TYPE || raw == Void.class) {
            return false;
        }
        if (HttpEntity.class.isAssignableFrom(raw)) {
            return debeValidar(type.getGeneric(0));
        }
        if (raw.isArray()) {
            return debeValidar(ResolvableType.forClass(raw.getComponentType()));
        }
        if (Collection.class.isAssignableFrom(raw) || Page.class.isAssignableFrom(raw)) {
            return debeValidar(type.getGeneric(0));
        }
        if (raw.isEnum()) {
            return true;
        }
        String packageName = raw.getPackageName();
        return !packageName.startsWith("java.")
                && !packageName.startsWith("jakarta.")
                && !packageName.startsWith("org.springframework.");
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

    private static List<String> propiedadesDeRecord(Class<?> tipoRecord) {
        List<String> nombres = new ArrayList<>();
        for (RecordComponent componente : tipoRecord.getRecordComponents()) {
            nombres.add(componente.getName());
        }
        return nombres;
    }

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
                || LocalDate.class.isAssignableFrom(tipoJava) || LocalDateTime.class.isAssignableFrom(tipoJava)
                || OffsetDateTime.class.isAssignableFrom(tipoJava) || Instant.class.isAssignableFrom(tipoJava)) {
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
        while (actual.has("$ref") && saltos < 8) {
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
                continue;
            }
            if (signature.paginacion().tipo() != TipoPaginacion.NINGUNA) {
                problems.addAll(compararPaginacion(signature, operationNode, openApiDocument));
            }
            problems.addAll(compararQueryParams(signature, operationNode));
            problems.addAll(compararRequestBodies(signature, operationNode, openApiDocument));
            problems.addAll(compararResponseBodies(signature, operationNode, openApiDocument));
        }
        return problems;
    }

    private static List<String> compararRequestBodies(
            OperationSignature signature, JsonNode operationNode, JsonNode document) {
        List<String> problems = new ArrayList<>();
        for (BodySignature request : signature.requestBodies()) {
            JsonNode schema = operationNode.path("requestBody").path("content").path("application/json").path("schema");
            if (schema.isMissingNode()) {
                problems.add("REQUEST_BODY_SCHEMA_FALTANTE " + signature.operation());
                continue;
            }
            compareType(signature.operation().toString(), request.location(), request.type(), request.kind(), schema, document, problems);
        }
        return problems;
    }

    private static List<String> compararResponseBodies(
            OperationSignature signature, JsonNode operationNode, JsonNode document) {
        List<String> problems = new ArrayList<>();
        for (BodySignature response : signature.responseBodies()) {
            JsonNode schema = responseSchema(operationNode);
            if (schema.isMissingNode()) {
                problems.add("RESPONSE_SCHEMA_FALTANTE " + signature.operation());
                continue;
            }
            compareType(signature.operation().toString(), response.location(), response.type(), response.kind(), schema, document, problems);
        }
        return problems;
    }

    private static JsonNode responseSchema(JsonNode operationNode) {
        for (String status : List.of("200", "201", "202")) {
            JsonNode schema = operationNode.path("responses").path(status)
                    .path("content").path("application/json").path("schema");
            if (!schema.isMissingNode()) {
                return schema;
            }
        }
        return MissingNode.getInstance();
    }

    public static List<String> compareTypeAgainstSchema(String context, ResolvableType type, JsonNode schema, JsonNode document) {
        List<String> problems = new ArrayList<>();
        compareType(context, "schema", type, BodyKind.SCHEMA, schema, document, problems);
        return problems;
    }

    public static List<String> compareTypeAgainstSchema(
            String context, ResolvableType type, BodyKind kind, JsonNode schema, JsonNode document) {
        List<String> problems = new ArrayList<>();
        compareType(context, kind.name().toLowerCase(), type, kind, schema, document, problems);
        return problems;
    }

    private static void compareType(
            String operation, String location, ResolvableType type, BodyKind kind,
            JsonNode schema, JsonNode document, List<String> problems) {
        type = unwrapResponseEntity(type);
        Class<?> raw = type.resolve();
        if (raw == null || raw == Void.class || raw == Void.TYPE || !debeValidar(type)) {
            return;
        }
        if (raw.isArray()) {
            compareArray(operation, location, ResolvableType.forClass(raw.getComponentType()), kind, schema, document, problems);
            return;
        }
        if (Collection.class.isAssignableFrom(raw)) {
            compareArray(operation, location, type.getGeneric(0), kind, schema, document, problems);
            return;
        }
        if (Page.class.isAssignableFrom(raw) || (raw.isRecord() && "PaginaResponse".equals(raw.getSimpleName()))) {
            compareContainerObject(operation, location, type, kind, schema, document, problems);
            return;
        }
        if (raw.isEnum()) {
            compareEnum(operation, location, raw, schema, document, problems);
            return;
        }
        compareObjectDto(operation, location, raw, kind, schema, document, problems);
    }

    private static void compareArray(
            String operation, String location, ResolvableType elementType, BodyKind kind,
            JsonNode schema, JsonNode document, List<String> problems) {
        JsonNode resolved = resolverSchema(schema, document);
        if (!"array".equals(resolved.path("type").asText(null))) {
            problems.add("DTO_TIPO_INCORRECTO " + operation + " " + location + " esperado=array declarado="
                    + resolved.path("type").asText(null));
            return;
        }
        compareType(operation, location + "[]", elementType, kind, resolved.path("items"), document, problems);
    }

    private static void compareContainerObject(
            String operation, String location, ResolvableType type, BodyKind kind,
            JsonNode schema, JsonNode document, List<String> problems) {
        JsonNode resolved = resolverSchema(schema, document);
        if (!"object".equals(resolved.path("type").asText(null))) {
            problems.add("DTO_TIPO_INCORRECTO " + operation + " " + location + " esperado=object declarado="
                    + resolved.path("type").asText(null));
            return;
        }
        ResolvableType elementType = type.getGeneric(0);
        Class<?> raw = type.resolve();
        String contentName = Page.class.isAssignableFrom(raw) ? "content" : "contenido";
        JsonNode content = resolved.path("properties").path(contentName);
        if (!content.isMissingNode()) {
            compareArray(operation, location + "." + contentName, elementType, kind, content, document, problems);
        }
    }

    private static void compareObjectDto(
            String operation, String location, Class<?> raw, BodyKind kind,
            JsonNode schema, JsonNode document, List<String> problems) {
        if (!schema.has("$ref")) {
            JsonNode resolved = resolverSchema(schema, document);
            if (!"object".equals(resolved.path("type").asText(null))) {
                problems.add("DTO_TIPO_INCORRECTO " + operation + " " + location + " esperado=object declarado="
                        + resolved.path("type").asText(null));
                return;
            }
        } else if (!schema.path("$ref").asText().endsWith("/" + raw.getSimpleName())) {
            problems.add("DTO_REF_INCORRECTO " + operation + " " + location + " esperado=" + raw.getSimpleName()
                    + " declarado=" + schema.path("$ref").asText());
        }

        JsonNode resolved = resolverSchema(schema, document);
        JsonNode propertiesNode = resolved.path("properties");
        Map<String, DtoProperty> expected = propiedadesDto(raw);
        Set<String> declaredNames = new LinkedHashSet<>();
        propertiesNode.fieldNames().forEachRemaining(declaredNames::add);

        for (DtoProperty property : expected.values()) {
            JsonNode declared = propertiesNode.path(property.name());
            if (declared.isMissingNode()) {
                problems.add("DTO_PROPIEDAD_FALTANTE " + operation + " " + raw.getSimpleName() + "." + property.name()
                        + " java=" + javaDescription(property.type()) + " openapi=<faltante>");
                continue;
            }
            compareProperty(operation, raw.getSimpleName(), property, declared, document, problems);
        }
        for (String declared : declaredNames) {
            if (!expected.containsKey(declared)) {
                problems.add("DTO_PROPIEDAD_EXTRA " + operation + " " + raw.getSimpleName() + "." + declared
                        + " java=<faltante> openapi=" + resumenSchema(propertiesNode.path(declared)));
            }
        }

        Set<String> required = requiredNames(resolved);
        for (DtoProperty property : expected.values()) {
            if (isRequired(property, raw, kind) && !required.contains(property.name())) {
                problems.add("DTO_REQUIRED_FALTANTE " + operation + " " + raw.getSimpleName() + "." + property.name());
            }
        }
    }

    private static void compareProperty(
            String operation, String owner, DtoProperty property, JsonNode schema, JsonNode document, List<String> problems) {
        ResolvableType type = property.type();
        Class<?> raw = type.resolve();
        if (raw == null) {
            return;
        }
        if (raw.isArray()) {
            compareArray(operation, owner + "." + property.name(), ResolvableType.forClass(raw.getComponentType()), BodyKind.SCHEMA, schema, document, problems);
            return;
        }
        if (Collection.class.isAssignableFrom(raw)) {
            compareArray(operation, owner + "." + property.name(), type.getGeneric(0), BodyKind.SCHEMA, schema, document, problems);
            return;
        }
        if (raw.isEnum()) {
            compareEnum(operation, owner + "." + property.name(), raw, schema, document, problems);
            return;
        }
        if (debeValidar(type)) {
            if (!schema.has("$ref") || !schema.path("$ref").asText().endsWith("/" + raw.getSimpleName())) {
                problems.add("DTO_REF_INCORRECTO " + operation + " " + owner + "." + property.name()
                        + " esperado=" + raw.getSimpleName() + " declarado=" + resumenSchema(schema));
            }
            return;
        }
        ExpectedScalar expected = scalar(raw);
        if (expected == null) {
            return;
        }
        String declaredType = schema.path("type").asText(null);
        String declaredFormat = schema.path("format").asText(null);
        if (!expected.type().equals(declaredType) || (expected.format() != null && !expected.format().equals(declaredFormat))) {
            problems.add("DTO_TIPO_INCORRECTO " + operation + " " + owner + "." + property.name()
                    + " java=" + expected + " openapi=" + resumenSchema(schema));
        }
    }

    private static void compareEnum(
            String operation, String location, Class<?> enumType, JsonNode schema, JsonNode document, List<String> problems) {
        JsonNode enumSchema = schema.has("$ref") ? resolverSchema(schema, document) : schema;
        if (!schema.has("$ref") && !"string".equals(enumSchema.path("type").asText(null))) {
            problems.add("DTO_TIPO_INCORRECTO " + operation + " " + location + " java=enum openapi=" + resumenSchema(schema));
            return;
        }
        if (schema.has("$ref") && !schema.path("$ref").asText().endsWith("/" + enumType.getSimpleName())) {
            problems.add("DTO_REF_INCORRECTO " + operation + " " + location + " esperado=" + enumType.getSimpleName()
                    + " declarado=" + schema.path("$ref").asText());
        }
        Set<String> expectedValues = new LinkedHashSet<>();
        for (Object constant : enumType.getEnumConstants()) {
            expectedValues.add(((Enum<?>) constant).name());
        }
        Set<String> declaredValues = new LinkedHashSet<>();
        enumSchema.path("enum").forEach(value -> declaredValues.add(value.asText()));
        if (!expectedValues.equals(declaredValues)) {
            problems.add("DTO_ENUM_INCORRECTO " + operation + " " + location
                    + " java=" + expectedValues + " openapi=" + declaredValues);
        }
    }

    private static ExpectedScalar scalar(Class<?> raw) {
        if (raw == String.class) {
            return new ExpectedScalar("string", null);
        }
        if (raw == UUID.class) {
            return new ExpectedScalar("string", "uuid");
        }
        if (raw == int.class || raw == Integer.class) {
            return new ExpectedScalar("integer", "int32");
        }
        if (raw == long.class || raw == Long.class) {
            return new ExpectedScalar("integer", "int64");
        }
        if (raw == float.class || raw == Float.class || raw == double.class || raw == Double.class
                || raw == BigDecimal.class) {
            return new ExpectedScalar("number", null);
        }
        if (raw == boolean.class || raw == Boolean.class) {
            return new ExpectedScalar("boolean", null);
        }
        if (raw == LocalDate.class) {
            return new ExpectedScalar("string", "date");
        }
        if (raw == Instant.class || raw == OffsetDateTime.class || raw == LocalDateTime.class) {
            return new ExpectedScalar("string", "date-time");
        }
        return null;
    }

    private static Map<String, DtoProperty> propiedadesDto(Class<?> raw) {
        Map<String, DtoProperty> properties = new LinkedHashMap<>();
        if (raw.isRecord()) {
            for (RecordComponent component : raw.getRecordComponents()) {
                properties.put(component.getName(), new DtoProperty(
                        component.getName(),
                        ResolvableType.forType(component.getGenericType()),
                        component.getType(),
                        recordComponentAnnotations(raw, component)));
            }
            return properties;
        }
        Arrays.stream(raw.getDeclaredFields())
                .filter(field -> !java.lang.reflect.Modifier.isStatic(field.getModifiers()))
                .forEach(field -> properties.put(field.getName(), new DtoProperty(
                        field.getName(),
                        ResolvableType.forField(field),
                        field.getType(),
                        field.getAnnotations())));
        return properties;
    }

    private static boolean isRequired(DtoProperty property, Class<?> owner, BodyKind kind) {
        if (hasExplicitRequiredEvidence(property.annotations())) {
            return true;
        }
        if (!property.rawType().isPrimitive()) {
            return false;
        }
        if (kind == BodyKind.RESPONSE) {
            return JACKSON_BEHAVIOR.serializesPrimitiveValues()
                    && !hasOmittingJacksonAnnotation(owner.getAnnotations())
                    && !hasOmittingJacksonAnnotation(property.annotations());
        }
        if (kind == BodyKind.REQUEST) {
            return owner.isRecord()
                    && JACKSON_BEHAVIOR.failsOnMissingPrimitiveCreatorProperty()
                    && !hasOmittingJacksonAnnotation(property.annotations());
        }
        return false;
    }

    private static boolean hasExplicitRequiredEvidence(Annotation[] annotations) {
        for (Annotation annotation : annotations) {
            Class<? extends Annotation> type = annotation.annotationType();
            if (type == NotNull.class || type == NotBlank.class || type == NotEmpty.class) {
                return true;
            }
            if (annotationBooleanValue(annotation, "required")) {
                return true;
            }
        }
        return false;
    }

    private static boolean hasOmittingJacksonAnnotation(Annotation[] annotations) {
        for (Annotation annotation : annotations) {
            String name = annotation.annotationType().getName();
            if (name.endsWith(".JsonInclude") || name.endsWith(".JsonFilter") || name.endsWith(".JsonSerialize")) {
                return true;
            }
        }
        return false;
    }

    private static boolean annotationBooleanValue(Annotation annotation, String methodName) {
        try {
            Method method = annotation.annotationType().getMethod(methodName);
            Object value = method.invoke(annotation);
            return Boolean.TRUE.equals(value);
        } catch (ReflectiveOperationException ignored) {
            return false;
        }
    }

    private static Annotation[] recordComponentAnnotations(Class<?> owner, RecordComponent component) {
        List<Annotation> annotations = new ArrayList<>();
        annotations.addAll(Arrays.asList(component.getAnnotations()));
        annotations.addAll(Arrays.asList(component.getAccessor().getAnnotations()));
        try {
            annotations.addAll(Arrays.asList(owner.getDeclaredField(component.getName()).getAnnotations()));
        } catch (NoSuchFieldException ignored) {
            // Los records normales exponen campo privado final; si no existe, las otras fuentes bastan.
        }
        return annotations.toArray(Annotation[]::new);
    }

    private static Set<String> requiredNames(JsonNode schema) {
        Set<String> names = new HashSet<>();
        schema.path("required").forEach(node -> names.add(node.asText()));
        return names;
    }

    private static String javaDescription(ResolvableType type) {
        Class<?> raw = type.resolve();
        return raw == null ? type.toString() : raw.getSimpleName();
    }

    private static String resumenSchema(JsonNode schema) {
        if (schema.has("$ref")) {
            return schema.path("$ref").asText();
        }
        String type = schema.path("type").asText(null);
        String format = schema.path("format").asText(null);
        return format == null ? String.valueOf(type) : type + "(" + format + ")";
    }

    private static List<String> compararPaginacion(
            OperationSignature signature, JsonNode operationNode, JsonNode document) {
        List<String> problems = new ArrayList<>();
        JsonNode schemaDeclarado = responseSchema(operationNode);
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

    private record DtoProperty(String name, ResolvableType type, Class<?> rawType, Annotation[] annotations) {
    }

    private record ExpectedScalar(String type, String format) {
        @Override
        public String toString() {
            return format == null ? type : type + "(" + format + ")";
        }
    }

    private record JacksonBehavior(boolean serializesPrimitiveValues, boolean failsOnMissingPrimitiveCreatorProperty) {
        static JacksonBehavior detect() {
            boolean failOnMissing = isDeserializationFeatureEnabled("FAIL_ON_MISSING_CREATOR_PROPERTIES");
            boolean failOnNullPrimitives = isDeserializationFeatureEnabled("FAIL_ON_NULL_FOR_PRIMITIVES");
            return new JacksonBehavior(true, failOnMissing || failOnNullPrimitives);
        }

        private static boolean isDeserializationFeatureEnabled(String featureName) {
            Boolean toolsValue = featureEnabled(
                    "tools.jackson.databind.ObjectMapper",
                    "tools.jackson.databind.DeserializationFeature",
                    featureName);
            if (toolsValue != null) {
                return toolsValue;
            }
            Boolean fasterXmlValue = featureEnabled(
                    "com.fasterxml.jackson.databind.ObjectMapper",
                    "com.fasterxml.jackson.databind.DeserializationFeature",
                    featureName);
            return fasterXmlValue != null && fasterXmlValue;
        }

        private static Boolean featureEnabled(String mapperClassName, String featureClassName, String featureName) {
            try {
                Class<?> mapperClass = Class.forName(mapperClassName);
                Class<?> featureClass = Class.forName(featureClassName);
                Object mapper = mapperClass.getConstructor().newInstance();
                Object feature = Enum.valueOf(featureClass.asSubclass(Enum.class), featureName);
                Method isEnabled = mapperClass.getMethod("isEnabled", featureClass);
                return (Boolean) isEnabled.invoke(mapper, feature);
            } catch (ReflectiveOperationException | LinkageError ignored) {
                return null;
            }
        }
    }
}
