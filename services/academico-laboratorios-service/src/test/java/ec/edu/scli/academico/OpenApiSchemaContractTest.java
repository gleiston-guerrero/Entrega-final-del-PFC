package ec.edu.scli.academico;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import ec.edu.scli.contracts.RuntimeContractVerifier;
import ec.edu.scli.contracts.SchemaContractVerifier;
import ec.edu.scli.contracts.SchemaContractVerifier.OperationSignature;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Validacion de schemas/parametros independiente del extractor regex Python:
 * usa reflexion sobre los HandlerMethod que Spring ya resolvio (tipos de
 * retorno Page/PaginaResponse reales, anotaciones @RequestParam/Pageable
 * reales) y la contrasta contra el contrato OpenAPI publicado.
 */
@SpringBootTest(properties = {
        "app.initial-data.enabled=false",
        "management.tracing.enabled=false"
})
@ActiveProfiles("test")
class OpenApiSchemaContractTest {
    @Autowired
    @Qualifier("requestMappingHandlerMapping")
    private RequestMappingHandlerMapping mappings;

    @Test
    void schemasYParametrosCoincidenConHandlerMethodsReales() throws Exception {
        List<OperationSignature> runtime = SchemaContractVerifier.runtimeSignatures(
                mappings, "ec.edu.scli.academico");
        JsonNode document = new ObjectMapper().readTree(
                RuntimeContractVerifier.repositoryFile(
                        "docs/openapi/academico-laboratorios-service-openapi.json").toFile());

        assertThat(runtime).anyMatch(signature ->
                signature.paginacion().tipo() != SchemaContractVerifier.TipoPaginacion.NINGUNA);
        assertThat(runtime).anyMatch(signature -> signature.requestBodies().stream()
                .anyMatch(body -> body.type().resolve().getSimpleName().equals("PeriodoLectivoRequest")));
        assertThat(runtime).anyMatch(signature -> signature.responseBodies().stream()
                .anyMatch(body -> body.type().resolve().getSimpleName().equals("PeriodoLectivoResponse")));
        assertThat(runtime).anyMatch(signature -> signature.responseBodies().stream()
                .anyMatch(body -> body.type().resolve().getSimpleName().equals("HorarioAcademicoResponse")));
        SchemaContractVerifier.assertMatches(runtime, document);
    }
}
