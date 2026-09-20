package ec.edu.scli.reservas;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import ec.edu.scli.contracts.RuntimeContractVerifier;
import ec.edu.scli.contracts.SchemaContractVerifier;
import ec.edu.scli.contracts.SchemaContractVerifier.OperationSignature;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Validacion de schemas/parametros independiente del extractor regex Python:
 * usa reflexion sobre los HandlerMethod que Spring ya resolvio (tipos de
 * retorno PaginaResponse reales, anotaciones @RequestParam reales con nombre,
 * defaultValue y required efectivos) y la contrasta contra el contrato
 * OpenAPI publicado.
 */
@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:reservas_schema_contract;MODE=PostgreSQL;DB_CLOSE_DELAY=-1",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.flyway.enabled=false",
        "spring.jpa.hibernate.ddl-auto=create-drop",
        "security.jwt.secret=MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        "app.internal-api-key=contract-test-key",
        "app.experimental.arbiter.enabled=true",
        "app.experimental.arbiter.strategy=s0",
        "app.notifications.firebase.enabled=false",
        "management.tracing.enabled=false"
})
class OpenApiSchemaContractTest {
    @Autowired
    @Qualifier("requestMappingHandlerMapping")
    private RequestMappingHandlerMapping mappings;

    @MockitoBean
    private JdbcTemplate jdbcTemplate;

    @Test
    void schemasYParametrosCoincidenConHandlerMethodsReales() throws Exception {
        List<OperationSignature> runtime = SchemaContractVerifier.runtimeSignatures(
                mappings, "ec.edu.scli.reservas");
        JsonNode document = new ObjectMapper().readTree(
                RuntimeContractVerifier.repositoryFile(
                        "docs/openapi/reservas-solicitudes-service-openapi.json").toFile());

        assertThat(runtime).anyMatch(signature ->
                signature.paginacion().tipo() != SchemaContractVerifier.TipoPaginacion.NINGUNA);
        assertThat(runtime).anyMatch(signature ->
                "IncidenteResponse".equals(signature.paginacion().nombreClaseElemento()));
        assertThat(runtime).anyMatch(signature -> signature.requestBodies().stream()
                .anyMatch(body -> body.type().resolve().getSimpleName().equals("CrearIncidenteRequest")));
        assertThat(runtime).anyMatch(signature -> signature.responseBodies().stream()
                .anyMatch(body -> body.type().resolve().getSimpleName().equals("IncidenteResponse")));
        SchemaContractVerifier.assertMatches(runtime, document);
    }
}
