package ec.edu.uteq.scli.api_gateway.routes;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.server.PathContainer;
import org.springframework.web.util.pattern.PathPattern;
import org.springframework.web.util.pattern.PathPatternParser;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.zip.InflaterInputStream;

public final class GatewayRouteCatalog {
    private static final PathPatternParser PATH_PARSER = PathPatternParser.defaultInstance;
    private static final List<Route> ROUTES = load();

    private GatewayRouteCatalog() {
    }

    static boolean accepts(String method, String path) {
        PathContainer container = PathContainer.parsePath(path);
        return ROUTES.stream().anyMatch(route -> route.method().equals(method)
            && route.matches(container));
    }

    public static List<String> operationKeys() {
        return ROUTES.stream().map(Route::normalizedKey).toList();
    }

    public static String examplePath(String method, String template) {
        return ROUTES.stream()
            .filter(route -> route.method().equals(method)
                && route.normalizedKey().equals(method + " " + template))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Operacion no catalogada: " + method + " " + template))
                .examplePath();
    }

    private static List<Route> load() {
        try (InputStream source = GatewayRouteCatalog.class.getResourceAsStream("/gateway-route-catalog.json")) {
            if (source == null) {
                throw new IllegalStateException("No se encontro gateway-route-catalog.json");
            }
            JsonNode catalog = new ObjectMapper().readTree(source);
            byte[] compressed = java.util.Base64.getDecoder().decode(catalog.path("payload").asText());
            try (InflaterInputStream payload = new InflaterInputStream(new java.io.ByteArrayInputStream(compressed))) {
                JsonNode operations = new ObjectMapper().readTree(payload);
                List<Route> routes = new ArrayList<>();
                operations.forEach(operation -> {
                    String method = operation.path("method").asText().toUpperCase(Locale.ROOT);
                    String path = operation.path("path").asText();
                    Map<String, Parameter> parameters = new java.util.HashMap<>();
                    operation.path("parameters").forEach(parameter -> parameters.put(
                            parameter.path("name").asText(), new Parameter(
                                    parameter.path("type").asText("string"),
                                    parameter.path("format").asText(null),
                                    readEnum(parameter.path("enum")))));
                    routes.add(new Route(method, path, PATH_PARSER.parse(path), parameters));
                });
                if (routes.size() != catalog.path("operationCount").asInt()) {
                    throw new IllegalStateException("Cantidad de operaciones del catalogo inconsistente");
                }
                return Collections.unmodifiableList(routes);
            }
        } catch (IOException | IllegalArgumentException exception) {
            throw new IllegalStateException("Catalogo de rutas del Gateway invalido", exception);
        }
    }

    private record Route(String method, String path, PathPattern pattern,
                         Map<String, Parameter> parameters) {

        private boolean matches(PathContainer container) {
            PathPattern.PathMatchInfo match = pattern.matchAndExtract(container);
            if (match == null) {
                return false;
            }
            return match.getUriVariables().entrySet().stream().allMatch(entry ->
                    parameters.getOrDefault(entry.getKey(), Parameter.STRING).accepts(entry.getValue()));
        }

        private String normalizedKey() {
            StringBuilder normalized = new StringBuilder();
            boolean variable = false;
            for (char character : path.toCharArray()) {
                if (character == '{') {
                    normalized.append("{}");
                    variable = true;
                } else if (character == '}') {
                    variable = false;
                } else if (!variable) {
                    normalized.append(character);
                }
            }
            return method + " " + normalized;
        }

        private String examplePath() {
            StringBuilder result = new StringBuilder();
            int start = 0;
            while (start < path.length()) {
                int open = path.indexOf('{', start);
                if (open < 0) {
                    result.append(path, start, path.length());
                    break;
                }
                int close = path.indexOf('}', open);
                result.append(path, start, open);
                Parameter parameter = parameters.get(path.substring(open + 1, close));
                result.append(parameter.exampleValue());
                start = close + 1;
            }
            return result.toString();
        }

        private Route {
            Objects.requireNonNull(method);
            Objects.requireNonNull(path);
            parameters = Map.copyOf(parameters);
        }
    }

    private record Parameter(String type, String format, Set<String> enumeration) {
        private static final Parameter STRING = new Parameter("string", null, Set.of());

        private boolean accepts(String value) {
            if (!enumeration.isEmpty()) {
                return enumeration.contains(value);
            }
            if ("uuid".equals(format)) {
                try {
                    java.util.UUID.fromString(value);
                    return true;
                } catch (IllegalArgumentException exception) {
                    return false;
                }
            }
            if ("integer".equals(type)) {
                try {
                    Integer.parseInt(value);
                    return true;
                } catch (NumberFormatException exception) {
                    return false;
                }
            }
            return true;
        }

        private String exampleValue() {
            if (!enumeration.isEmpty()) return enumeration.iterator().next();
            if ("uuid".equals(format)) return "00000000-0000-0000-0000-000000000001";
            if ("integer".equals(type)) return "1";
            return "example";
        }
    }

    private static Set<String> readEnum(JsonNode node) {
        Set<String> values = new java.util.HashSet<>();
        node.forEach(value -> values.add(value.asText()));
        return values;
    }
}
