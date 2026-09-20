package ec.edu.scli.reservas;

import ec.edu.scli.contracts.RuntimeContractVerifier;
import ec.edu.scli.contracts.RuntimeContractVerifier.Operation;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:reservas_contract_enabled;MODE=PostgreSQL;DB_CLOSE_DELAY=-1",
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
class OpenApiRuntimeCompletenessTest {
    @Autowired
    @Qualifier("requestMappingHandlerMapping")
    private RequestMappingHandlerMapping mappings;

    @MockitoBean
    private JdbcTemplate jdbcTemplate;

    @Test
    void superficieHabilitableCoincideConContratoCompleto() throws Exception {
        List<Operation> runtime = RuntimeContractVerifier.runtimeOperations(
                mappings, "ec.edu.scli.reservas");
        List<Operation> contract = RuntimeContractVerifier.openApiOperations(
                RuntimeContractVerifier.repositoryFile(
                        "docs/openapi/reservas-solicitudes-service-openapi.json"));

        assertThat(runtime).hasSize(80);
        assertThat(contract).hasSize(80);
        RuntimeContractVerifier.assertMatches(runtime, contract);
    }
}
