package ec.edu.uteq.scli.auth_service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import ec.edu.scli.contracts.RuntimeContractVerifier;
import ec.edu.scli.contracts.SchemaContractVerifier;
import ec.edu.scli.contracts.SchemaContractVerifier.OperationSignature;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:auth_schema_contract;MODE=PostgreSQL;DB_CLOSE_DELAY=-1",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.flyway.enabled=false",
        "spring.jpa.hibernate.ddl-auto=create-drop",
        "app.initial-data.enabled=false",
        "management.tracing.enabled=false"
})
class OpenApiSchemaContractTest {
    @Autowired
    @Qualifier("requestMappingHandlerMapping")
    private RequestMappingHandlerMapping mappings;

    @Test
    void schemasYParametrosCoincidenConHandlerMethodsReales() throws Exception {
        List<OperationSignature> runtime = SchemaContractVerifier.runtimeSignatures(
                mappings, "ec.edu.uteq.scli.auth_service");
        JsonNode document = new ObjectMapper().readTree(
                RuntimeContractVerifier.repositoryFile("docs/openapi/auth-service-openapi.json").toFile());

        assertThat(runtime)
                .anyMatch(signature -> signature.requestBodies().stream()
                        .anyMatch(body -> body.type().resolve().getSimpleName().equals("LoginRequest")))
                .anyMatch(signature -> signature.responseBodies().stream()
                        .anyMatch(body -> body.type().resolve().getSimpleName().equals("LoginResponse")));
        SchemaContractVerifier.assertMatches(runtime, document);
    }
}
