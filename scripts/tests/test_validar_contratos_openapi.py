import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "validar-contratos-openapi.py"
spec = importlib.util.spec_from_file_location("validar_contratos_openapi", SCRIPT)
openapi = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = openapi
spec.loader.exec_module(openapi)


def write_java(root: Path, relative: str, source: str) -> None:
    path = root / "src/main/java" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


class RequiredContextualTest(unittest.TestCase):
    def test_required_contextual_para_primitivos_y_bean_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_java(
                root,
                "example/dto/PrimitiveResponse.java",
                "package example.dto; public record PrimitiveResponse(boolean activo) {}",
            )
            write_java(
                root,
                "example/dto/PrimitiveRequest.java",
                "package example.dto; public record PrimitiveRequest(boolean activo) {}",
            )
            write_java(
                root,
                "example/dto/OptionalPojoRequest.java",
                "package example.dto; public class OptionalPojoRequest { private boolean activo; }",
            )
            write_java(
                root,
                "example/dto/ValidationRequest.java",
                """
                package example.dto;
                import jakarta.validation.constraints.NotBlank;
                public record ValidationRequest(@NotBlank String nombre) {}
                """,
            )
            write_java(
                root,
                "example/TestController.java",
                """
                package example;
                import example.dto.*;
                import org.springframework.web.bind.annotation.*;
                @RestController
                @RequestMapping("/api/test")
                public class TestController {
                    @GetMapping("/response")
                    public PrimitiveResponse response() { return null; }
                    @PostMapping("/request")
                    public PrimitiveResponse request(@RequestBody PrimitiveRequest request) { return null; }
                    @PostMapping("/pojo")
                    public PrimitiveResponse pojo(@RequestBody OptionalPojoRequest request) { return null; }
                    @PostMapping("/validation")
                    public PrimitiveResponse validation(@RequestBody ValidationRequest request) { return null; }
                }
                """,
            )

            schemas = openapi.discover_types(root)

            self.assertEqual(["activo"], schemas["PrimitiveResponse"]["required"])
            self.assertEqual(["activo"], schemas["PrimitiveRequest"]["required"])
            self.assertNotIn("required", schemas["OptionalPojoRequest"])
            self.assertEqual(["nombre"], schemas["ValidationRequest"]["required"])


class SchemaMappingTest(unittest.TestCase):
    def test_offset_datetime_y_numericos_en_record(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_java(
                root,
                "example/dto/MetricsResponse.java",
                """
                package example.dto;
                import java.time.OffsetDateTime;
                public record MetricsResponse(
                    OffsetDateTime instante,
                    double valorDouble,
                    Double valorDoubleObjeto,
                    float valorFloat,
                    Float valorFloatObjeto
                ) {}
                """,
            )

            schema = openapi.discover_types(root)["MetricsResponse"]

            self.assertEqual(
                {"type": "string", "format": "date-time"},
                schema["properties"]["instante"],
            )
            self.assertEqual(
                {"type": "number", "format": "double"},
                schema["properties"]["valorDouble"],
            )
            self.assertEqual(
                {"type": "number", "format": "double"},
                schema["properties"]["valorDoubleObjeto"],
            )
            self.assertEqual(
                {"type": "number", "format": "float"},
                schema["properties"]["valorFloat"],
            )
            self.assertEqual(
                {"type": "number", "format": "float"},
                schema["properties"]["valorFloatObjeto"],
            )

    def test_record_con_pattern_no_pierde_componentes_posteriores(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_java(
                root,
                "example/dto/PatternRequest.java",
                r'''
                package example.dto;
                import jakarta.validation.constraints.Pattern;
                import jakarta.validation.constraints.Size;
                public record PatternRequest(
                    String primero,
                    @Pattern(
                        regexp = "^A,B,\"C\"$|^X\\,Y$",
                        message = "Debe aceptar comas, parentesis (ok) y escapes \\\""
                    )
                    String direccionIp,
                    @Pattern(regexp = "^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", message = "MAC valida")
                    String direccionMac,
                    @Size(max = 2000)
                    String observacion,
                    String despues
                ) {}
                ''',
            )

            properties = openapi.discover_types(root)["PatternRequest"]["properties"]

            self.assertEqual(
                ["primero", "direccionIp", "direccionMac", "observacion", "despues"],
                list(properties),
            )
            self.assertEqual({"type": "string"}, properties["direccionIp"])
            self.assertEqual({"type": "string"}, properties["direccionMac"])
            self.assertEqual({"type": "string"}, properties["observacion"])
            self.assertEqual({"type": "string"}, properties["despues"])

    def test_records_anidados_generan_refs_y_arrays(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_java(
                root,
                "example/dto/Contenedor.java",
                """
                package example.dto;
                import java.util.List;
                public record Contenedor(
                    Nested nested,
                    List<Item> items
                ) {
                    public record Nested(
                        boolean activo
                    ) {}

                    public record Item(
                        String nombre
                    ) {}
                }
                """,
            )

            schemas = openapi.discover_types(root)

            self.assertIn("Contenedor", schemas)
            self.assertIn("Nested", schemas)
            self.assertIn("Item", schemas)
            self.assertEqual(
                {"$ref": "#/components/schemas/Nested"},
                schemas["Contenedor"]["properties"]["nested"],
            )
            self.assertEqual(
                {"type": "array", "items": {"$ref": "#/components/schemas/Item"}},
                schemas["Contenedor"]["properties"]["items"],
            )

    def test_multiples_records_en_un_mismo_archivo(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_java(
                root,
                "example/dto/Multi.java",
                """
                package example.dto;
                public record Primero(Segundo segundo) {
                    public record Segundo(String nombre) {}
                }
                record Tercero(Integer valor) {}
                """,
            )

            schemas = openapi.discover_types(root)

            self.assertIn("Primero", schemas)
            self.assertIn("Segundo", schemas)
            self.assertIn("Tercero", schemas)
            self.assertEqual(
                {"$ref": "#/components/schemas/Segundo"},
                schemas["Primero"]["properties"]["segundo"],
            )
            self.assertEqual(
                {"type": "integer", "format": "int32"},
                schemas["Tercero"]["properties"]["valor"],
            )


if __name__ == "__main__":
    unittest.main()
