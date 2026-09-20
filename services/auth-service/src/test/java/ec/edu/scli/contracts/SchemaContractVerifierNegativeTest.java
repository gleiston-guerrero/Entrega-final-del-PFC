package ec.edu.scli.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import org.junit.jupiter.api.Test;
import org.springframework.core.ResolvableType;

import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class SchemaContractVerifierNegativeTest {
    private static final ObjectMapper MAPPER = new ObjectMapper();

    @Test
    void fallaCuandoFaltaPropiedadDto() throws Exception {
        JsonNode document = baseDocument();
        ((ObjectNode) document.path("components").path("schemas").path("ProbeDto").path("properties")).remove("nombre");

        List<String> problems = compare(document);

        assertThat(problems).anyMatch(problem -> problem.contains("DTO_PROPIEDAD_FALTANTE")
                && problem.contains("ProbeDto.nombre"));
    }

    @Test
    void fallaCuandoSobraPropiedadDto() throws Exception {
        JsonNode document = baseDocument();
        ((ObjectNode) document.path("components").path("schemas").path("ProbeDto").path("properties"))
                .putObject("extra").put("type", "string");

        List<String> problems = compare(document);

        assertThat(problems).anyMatch(problem -> problem.contains("DTO_PROPIEDAD_EXTRA")
                && problem.contains("ProbeDto.extra"));
    }

    @Test
    void fallaConUuidFechaYDateTimeIncorrectos() throws Exception {
        JsonNode document = baseDocument();
        ObjectNode properties = (ObjectNode) document.path("components").path("schemas").path("ProbeDto").path("properties");
        properties.putObject("id").put("type", "string");
        properties.putObject("fecha").put("type", "string").put("format", "date-time");
        properties.putObject("creadoEn").put("type", "string").put("format", "date");

        List<String> problems = compare(document);

        assertThat(problems).anyMatch(problem -> problem.contains("DTO_TIPO_INCORRECTO")
                && problem.contains("ProbeDto.id"));
        assertThat(problems).anyMatch(problem -> problem.contains("DTO_TIPO_INCORRECTO")
                && problem.contains("ProbeDto.fecha"));
        assertThat(problems).anyMatch(problem -> problem.contains("DTO_TIPO_INCORRECTO")
                && problem.contains("ProbeDto.creadoEn"));
    }

    @Test
    void fallaConEnumIncorrecto() throws Exception {
        JsonNode document = baseDocument();
        ObjectNode enumSchema = (ObjectNode) document.path("components").path("schemas").path("EstadoProbe");
        enumSchema.putArray("enum").add("ACTIVO");

        List<String> problems = compare(document);

        assertThat(problems).anyMatch(problem -> problem.contains("DTO_ENUM_INCORRECTO")
                && problem.contains("ProbeDto.estado"));
    }

    @Test
    void fallaConNestedRefIncorrecto() throws Exception {
        JsonNode document = baseDocument();
        ((ObjectNode) document.path("components").path("schemas").path("ProbeDto")
                .path("properties").path("nested")).put("$ref", "#/components/schemas/OtroDto");

        List<String> problems = compare(document);

        assertThat(problems).anyMatch(problem -> problem.contains("DTO_REF_INCORRECTO")
                && problem.contains("ProbeDto.nested"));
    }

    @Test
    void primitiveResponseSerializadoSiempreDebeEstarEnRequired() throws Exception {
        JsonNode document = primitiveDocument();

        List<String> problems = compare(document, PrimitiveResponseDto.class, SchemaContractVerifier.BodyKind.RESPONSE);

        assertThat(problems).anyMatch(problem -> problem.contains("DTO_REQUIRED_FALTANTE")
                && problem.contains("PrimitiveResponseDto.activo"));
    }

    @Test
    void primitiveRequestEstrictoDebeEstarEnRequired() throws Exception {
        JsonNode document = primitiveDocument();

        List<String> problems = compare(document, PrimitiveRequestDto.class, SchemaContractVerifier.BodyKind.REQUEST);

        assertThat(problems).anyMatch(problem -> problem.contains("DTO_REQUIRED_FALTANTE")
                && problem.contains("PrimitiveRequestDto.activo"));
    }

    @Test
    void primitiveRequestSinEvidenciaNoSeAsumeRequired() throws Exception {
        JsonNode document = primitiveDocument();

        List<String> problems = compare(document, PrimitivePojoRequestDto.class, SchemaContractVerifier.BodyKind.REQUEST);

        assertThat(problems).noneMatch(problem -> problem.contains("DTO_REQUIRED_FALTANTE")
                && problem.contains("PrimitivePojoRequestDto.activo"));
    }

    @Test
    void beanValidationMarcaRequiredSinDependerDePrimitivos() throws Exception {
        JsonNode document = validationDocument();

        List<String> problems = compare(document, ValidationRequestDto.class, SchemaContractVerifier.BodyKind.REQUEST);

        assertThat(problems).anyMatch(problem -> problem.contains("DTO_REQUIRED_FALTANTE")
                && problem.contains("ValidationRequestDto.id"));
        assertThat(problems).anyMatch(problem -> problem.contains("DTO_REQUIRED_FALTANTE")
                && problem.contains("ValidationRequestDto.nombre"));
        assertThat(problems).anyMatch(problem -> problem.contains("DTO_REQUIRED_FALTANTE")
                && problem.contains("ValidationRequestDto.codigos"));
    }

    private static List<String> compare(JsonNode document) {
        return SchemaContractVerifier.compareTypeAgainstSchema(
                "negative-test",
                ResolvableType.forClass(ProbeDto.class),
                document.path("components").path("schemas").path("ProbeDto"),
                document);
    }

    private static List<String> compare(JsonNode document, Class<?> type, SchemaContractVerifier.BodyKind kind) {
        return SchemaContractVerifier.compareTypeAgainstSchema(
                "negative-test",
                ResolvableType.forClass(type),
                kind,
                document.path("components").path("schemas").path(type.getSimpleName()),
                document);
    }

    private static JsonNode baseDocument() throws Exception {
        return MAPPER.readTree("""
                {
                  "components": {
                    "schemas": {
                      "ProbeDto": {
                        "type": "object",
                        "properties": {
                          "id": { "type": "string", "format": "uuid" },
                          "fecha": { "type": "string", "format": "date" },
                          "creadoEn": { "type": "string", "format": "date-time" },
                          "estado": { "$ref": "#/components/schemas/EstadoProbe" },
                          "nested": { "$ref": "#/components/schemas/NestedProbe" },
                          "nombre": { "type": "string" }
                        }
                      },
                      "EstadoProbe": {
                        "type": "string",
                        "enum": ["ACTIVO", "INACTIVO"]
                      },
                      "NestedProbe": {
                        "type": "object",
                        "properties": {
                          "valor": { "type": "string" }
                        }
                      }
                    }
                  }
                }
                """);
    }

    private static JsonNode primitiveDocument() throws Exception {
        return MAPPER.readTree("""
                {
                  "components": {
                    "schemas": {
                      "PrimitiveResponseDto": {
                        "type": "object",
                        "properties": {
                          "activo": { "type": "boolean" }
                        }
                      },
                      "PrimitiveRequestDto": {
                        "type": "object",
                        "properties": {
                          "activo": { "type": "boolean" }
                        }
                      },
                      "PrimitivePojoRequestDto": {
                        "type": "object",
                        "properties": {
                          "activo": { "type": "boolean" }
                        }
                      }
                    }
                  }
                }
                """);
    }

    private static JsonNode validationDocument() throws Exception {
        return MAPPER.readTree("""
                {
                  "components": {
                    "schemas": {
                      "ValidationRequestDto": {
                        "type": "object",
                        "properties": {
                          "id": { "type": "string" },
                          "nombre": { "type": "string" },
                          "codigos": { "type": "array", "items": { "type": "string" } }
                        }
                      }
                    }
                  }
                }
                """);
    }

    record ProbeDto(UUID id, LocalDate fecha, Instant creadoEn, EstadoProbe estado, NestedProbe nested, String nombre) {
    }

    enum EstadoProbe { ACTIVO, INACTIVO }

    record NestedProbe(String valor) {
    }

    record PrimitiveResponseDto(boolean activo) {
    }

    record PrimitiveRequestDto(boolean activo) {
    }

    static final class PrimitivePojoRequestDto {
        @SuppressWarnings("unused")
        private boolean activo;
    }

    record ValidationRequestDto(@NotNull String id, @NotBlank String nombre, @NotEmpty List<String> codigos) {
    }
}
