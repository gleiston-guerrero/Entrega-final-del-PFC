package ec.edu.scli.reservas;

import ec.edu.scli.contracts.RuntimeContractVerifier;
import ec.edu.scli.contracts.RuntimeContractVerifier.Operation;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:reservas_contract_default;MODE=PostgreSQL;DB_CLOSE_DELAY=-1",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.flyway.enabled=false",
        "spring.jpa.hibernate.ddl-auto=create-drop",
        "security.jwt.secret=MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
        "app.internal-api-key=contract-test-key",
        "app.experimental.arbiter.enabled=false",
        "app.notifications.firebase.enabled=false",
        "management.tracing.enabled=false"
})
class OpenApiRuntimeDefaultSurfaceTest {
    @Autowired
    @Qualifier("requestMappingHandlerMapping")
    private RequestMappingHandlerMapping mappings;

    @Test
    void superficieNormalExcluyeLasDosOperacionesExperimentales() {
        List<Operation> runtime = RuntimeContractVerifier.runtimeOperations(
                mappings, "ec.edu.scli.reservas");

        assertThat(runtime).hasSize(78);
        assertThat(runtime).noneMatch(operation ->
                operation.path().startsWith("/api/v1/internal/experimentos/arbiter"));
    }
}
