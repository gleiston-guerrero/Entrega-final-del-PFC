package ec.edu.scli.usuarios;

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

/**
 * Validacion de schemas/parametros independiente del extractor regex Python:
 * usa reflexion sobre los HandlerMethod que Spring ya resolvio (tipos de
 * retorno Page reales, anotaciones @RequestParam/Pageable reales) y la
 * contrasta contra el contrato OpenAPI publicado.
 */
@SpringBootTest(properties = {
        "spring.datasource.url=jdbc:h2:mem:usuarios_schema_contract;MODE=PostgreSQL;DB_CLOSE_DELAY=-1",
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
                mappings, "ec.edu.scli.usuarios");
        JsonNode document = new ObjectMapper().readTree(
                RuntimeContractVerifier.repositoryFile(
                        "docs/openapi/usuarios-service-openapi.json").toFile());

        assertThat(runtime).anyMatch(signature ->
                signature.paginacion().tipo() != SchemaContractVerifier.TipoPaginacion.NINGUNA);
        SchemaContractVerifier.assertMatches(runtime, document);
    }
}
