package ec.edu.uteq.scli.api_gateway.contracts;

import ec.edu.scli.contracts.RuntimeContractVerifier;
import ec.edu.scli.contracts.RuntimeContractVerifier.Operation;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.cloud.gateway.server.mvc.common.MvcUtils;
import org.springframework.cloud.gateway.server.mvc.handler.ProxyExchangeHandlerFunction;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.HttpMethod;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.web.servlet.function.ServerRequest;
import org.springframework.web.servlet.function.ServerResponse;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentLinkedQueue;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.reset;
import static org.mockito.Mockito.when;

@SpringBootTest
@AutoConfigureMockMvc(addFilters = false)
class GatewayOpenApiRuntimeCompletenessTest {
    private static final Map<String, String> CONTRACTS = Map.of(
            "auth", "docs/openapi/auth-service-openapi.json",
            "usuarios", "docs/openapi/usuarios-service-openapi.json",
            "academico", "docs/openapi/academico-laboratorios-service-openapi.json",
            "reservas", "docs/openapi/reservas-solicitudes-service-openapi.json");
    private static final Map<String, String> BACKEND_URLS = Map.of(
            "auth", "http://auth.test.invalid:18081",
            "usuarios", "http://usuarios.test.invalid:18082",
            "academico", "http://academico.test.invalid:18083",
            "reservas", "http://reservas.test.invalid:18084");

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private ProxyExchangeHandlerFunction proxyExchangeHandler;

    private final ConcurrentLinkedQueue<RoutedRequest> routedRequests =
            new ConcurrentLinkedQueue<>();

    @DynamicPropertySource
    static void backendUrls(DynamicPropertyRegistry registry) {
        registry.add("AUTH_SERVICE_URL", () -> BACKEND_URLS.get("auth"));
        registry.add("USUARIOS_SERVICE_URL", () -> BACKEND_URLS.get("usuarios"));
        registry.add("ACADEMICO_SERVICE_URL", () -> BACKEND_URLS.get("academico"));
        registry.add("RESERVAS_SOLICITUDES_SERVICE_URL", () -> BACKEND_URLS.get("reservas"));
    }

    @BeforeEach
    void captureRequestsAfterRouterFilters() {
        routedRequests.clear();
        reset(proxyExchangeHandler);
        when(proxyExchangeHandler.handle(any(ServerRequest.class))).thenAnswer(invocation -> {
            ServerRequest request = invocation.getArgument(0);
            String backend = MvcUtils.<java.net.URI>getAttribute(
                    request, MvcUtils.GATEWAY_REQUEST_URL_ATTR).toString();
            routedRequests.add(new RoutedRequest(
                    request.method().name(), request.uri().getRawPath(), backend));
            return ServerResponse.noContent().build();
        });
    }

    @Test
    void fachadaSeDerivaDeBackendsValidadosYRouterFunctionsReales() throws Exception {
        Map<Operation, String> canonical = new HashMap<>();
        Map<String, List<Operation>> backendOperations = new HashMap<>();
        for (Map.Entry<String, String> entry : CONTRACTS.entrySet()) {
            List<Operation> operations = RuntimeContractVerifier.openApiOperations(
                    RuntimeContractVerifier.repositoryFile(entry.getValue()));
            backendOperations.put(entry.getKey(), operations);
            for (Operation operation : operations) {
                if (!isInternal(operation.path())) {
                    String previous = canonical.put(operation, entry.getKey());
                    assertThat(previous)
                            .as("una operacion publica pertenece a un solo backend: %s", operation)
                            .isNull();
                }
            }
        }

        Map<Operation, String> expected = new HashMap<>(canonical);
        addAliases(expected, backendOperations.get("auth"), "auth", "/auth-service");
        addAliases(expected, backendOperations.get("usuarios"), "usuarios", "/usuarios-service");

        List<Operation> gateway = RuntimeContractVerifier.openApiOperations(
                RuntimeContractVerifier.repositoryFile("docs/openapi/api-gateway-openapi.json"));

        assertThat(canonical).hasSize(182);
        assertThat(expected.keySet().stream()
                .filter(operation -> operation.path().startsWith("/auth-service/"))).hasSize(8);
        assertThat(expected.keySet().stream()
                .filter(operation -> operation.path().startsWith("/usuarios-service/"))).hasSize(34);
        assertThat(expected).hasSize(224);
        assertThat(gateway).hasSize(224);
        List<Operation> runtime = probeAcceptedOperations(expected);
        RuntimeContractVerifier.assertMatches(runtime, gateway);
    }

    @Test
    void gatewayDocumentadoPeroNoAceptadoEsDetectado() throws Exception {
        Map<Operation, String> expected = expectedOperations();
        List<Operation> runtime = probeAcceptedOperations(expected);
        List<Operation> documentadoConFantasma = new java.util.ArrayList<>(runtime);
        documentadoConFantasma.add(new Operation("GET", "/api/v1/fantasma"));

        assertThat(RuntimeContractVerifier.compare(runtime, documentadoConFantasma))
                .anyMatch(problem -> problem.startsWith("EXTRA_IN_CONTRACT"));
    }

    @Test
    void gatewayAceptaRutaFantasmaPeroContratoLaOmiteEsDetectado() throws Exception {
        Operation aceptadaPorPrefijo = new Operation("GET", "/api/v1/laboratorios/fantasma");
        List<Operation> runtime = probeAcceptedOperations(
                Map.of(aceptadaPorPrefijo, "academico"));

        assertThat(runtime).containsExactly(aceptadaPorPrefijo);
        assertThat(RuntimeContractVerifier.compare(runtime, List.of()))
                .anyMatch(problem -> problem.startsWith("MISSING_IN_CONTRACT"));
    }

            @Test
    void gatewayAceptaRutaRealPeroContratoLaOmiteEsDetectado() throws Exception {
        Map<Operation, String> expected = expectedOperations();
        List<Operation> runtime = probeAcceptedOperations(expected);
        Operation rutaReal = runtime.get(0);
        List<Operation> contratoIncompleto = runtime.stream()
                .filter(operation -> !operation.equals(rutaReal))
                .toList();

        assertThat(RuntimeContractVerifier.compare(runtime, contratoIncompleto))
                .anyMatch(problem -> problem.startsWith("MISSING_IN_CONTRACT"));
    }

    private Map<Operation, String> expectedOperations() throws IOException {
        Map<Operation, String> canonical = new HashMap<>();
        Map<String, List<Operation>> backendOperations = new HashMap<>();
        for (Map.Entry<String, String> entry : CONTRACTS.entrySet()) {
            List<Operation> operations = RuntimeContractVerifier.openApiOperations(
                    RuntimeContractVerifier.repositoryFile(entry.getValue()));
            backendOperations.put(entry.getKey(), operations);
            for (Operation operation : operations) {
                if (!isInternal(operation.path())) {
                    String previous = canonical.put(operation, entry.getKey());
                    assertThat(previous)
                            .as("una operacion publica pertenece a un solo backend: %s", operation)
                            .isNull();
                }
            }
        }
        Map<Operation, String> expected = new HashMap<>(canonical);
        addAliases(expected, backendOperations.get("auth"), "auth", "/auth-service");
        addAliases(expected, backendOperations.get("usuarios"), "usuarios", "/usuarios-service");
        return expected;
    }

    private List<Operation> probeAcceptedOperations(Map<Operation, String> expected) throws Exception {
        List<Operation> runtime = new ArrayList<>();
        for (Map.Entry<Operation, String> entry : expected.entrySet()) {
            Operation operation = entry.getKey();
            routedRequests.clear();
            MvcResult result = mockMvc.perform(MockMvcRequestBuilders.request(
                            HttpMethod.valueOf(operation.method()), concretePath(operation.path())))
                    .andReturn();
            if (result.getResponse().getStatus() == 204) {
                runtime.add(operation);
                assertThat(routedRequests)
                        .as("request transformada por el router para %s", operation)
                        .containsExactly(new RoutedRequest(
                                operation.method(), expectedBackendPath(concretePath(operation.path())),
                                BACKEND_URLS.get(entry.getValue())));
            }
        }
        return runtime;
    }

    private static void addAliases(
            Map<Operation, String> expected, List<Operation> backend,
            String service, String prefix) {
        for (Operation operation : backend) {
            if (!isInternal(operation.path())) {
                Operation alias = new Operation(operation.method(), prefix + operation.path());
                assertThat(expected.put(alias, service)).isNull();
            }
        }
    }

    private static boolean isInternal(String path) {
        return path.startsWith("/api/v1/internal/") || path.equals("/api/v1/internal");
    }

    private static String expectedBackendPath(String gatewayPath) {
        for (String prefix : List.of("/auth-service", "/usuarios-service")) {
            if (gatewayPath.startsWith(prefix + "/")) {
                return gatewayPath.substring(prefix.length());
            }
        }
        return gatewayPath;
    }

    private static String concretePath(String template) {
        StringBuilder result = new StringBuilder();
        int variable = 0;
        for (int index = 0; index < template.length(); index++) {
            char character = template.charAt(index);
            if (character == '{') {
                int close = template.indexOf('}', index);
                if (close < 0) {
                    throw new IllegalArgumentException("Path invalido: " + template);
                }
                result.append("00000000-0000-0000-0000-")
                        .append(String.format("%012d", ++variable));
                index = close;
            } else {
                result.append(character);
            }
        }
        return result.toString();
    }

    private record RoutedRequest(String method, String path, String backend) {
    }
}
