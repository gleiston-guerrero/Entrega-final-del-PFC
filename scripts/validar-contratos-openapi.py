#!/usr/bin/env python3
"""Genera snapshots y ejecuta validaciones OpenAPI estructurales auxiliares.

No requiere paquetes externos. Use --generate para actualizar docs/openapi/*.json;
sin argumentos, el programa solo valida y nunca modifica archivos.

Responsabilidad de este script (y limites explicitos):

- Genera los snapshots deterministas a partir de controladores y DTO.
- Valida invariantes estructurales no circulares: JSON valido, campos basicos,
  operationId sin duplicados, referencias $ref resolubles, esquemas de
  seguridad declarados y consistencia catalogo-gateway.
- La completitud metodo+ruta NO se acredita con este extractor regex: la
  fuente autoritativa son las pruebas Java sobre RequestMappingHandlerMapping
  y los RouterFunction reales (RuntimeContractVerifier), ejecutadas por
  ``mvn verify`` en cada modulo.
- La correccion SEMANTICA de schemas de respuesta (p. ej. que un endpoint
  paginado no se describa como array plano) y de parametros de consulta
  (nombre real, required, defaultValue, Pageable) tampoco se acredita aqui:
  ese extractor y este validador comparten la misma interpretacion regex, por
  lo que no pueden servir de evidencia independiente el uno del otro. Esa
  evidencia la produce SchemaContractVerifier (reflexion sobre HandlerMethod
  compilados), tambien ejecutado por ``mvn verify``. Este script solo puede
  detectar que el snapshot publicado diverge de lo que el extractor generaria
  hoy; no puede demostrar que el extractor mismo sea correcto.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "openapi"
HTTP = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}
SERVICES = {
    "Auth": (ROOT / "services/auth-service", "auth-service-openapi.json", "SCLI - Auth API", "1.0.0"),
    "Usuarios": (ROOT / "services/usuarios-service", "usuarios-service-openapi.json", "SCLI - Usuarios API", "1.0.0"),
    "Académico": (ROOT / "services/academico-laboratorios-service", "academico-laboratorios-service-openapi.json", "SCLI - Académico y Laboratorios API", "1.0.0"),
    "Reservas": (ROOT / "services/reservas-solicitudes-service", "reservas-solicitudes-service-openapi.json", "SCLI - Reservas y Solicitudes API", "1.1.0"),
}
MAP_METHOD = {"GetMapping": "get", "PostMapping": "post", "PutMapping": "put", "DeleteMapping": "delete", "PatchMapping": "patch"}
PRIMITIVES = {
    "String": {"type": "string"}, "UUID": {"type": "string", "format": "uuid"},
    "LocalDate": {"type": "string", "format": "date"}, "LocalDateTime": {"type": "string", "format": "date-time"},
    "Instant": {"type": "string", "format": "date-time"}, "LocalTime": {"type": "string", "format": "time"},
    "Boolean": {"type": "boolean"}, "boolean": {"type": "boolean"}, "Integer": {"type": "integer", "format": "int32"},
    "int": {"type": "integer", "format": "int32"}, "Long": {"type": "integer", "format": "int64"},
    "long": {"type": "integer", "format": "int64"}, "Double": {"type": "number", "format": "double"},
    "BigDecimal": {"type": "number"}, "Void": {}, "void": {}, "Map": {"type": "object"}, "Object": {},
}

def clean_java(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)

def annotation_path(args: str | None) -> str:
    if not args:
        return ""
    hit = re.search(r'"([^"]*)"', args)
    return hit.group(1) if hit else ""

def join_path(base: str, suffix: str) -> str:
    value = "/" + "/".join(x.strip("/") for x in (base, suffix) if x.strip("/"))
    return value if value != "" else "/"

def split_top(value: str) -> list[str]:
    out, start, depth = [], 0, 0
    for i, ch in enumerate(value):
        depth += ch in "<(["
        depth -= ch in ">)]"
        if ch == "," and depth == 0:
            out.append(value[start:i].strip()); start = i + 1
    tail = value[start:].strip()
    return out + ([tail] if tail else [])

def strip_wrappers(value: str) -> str:
    value = re.sub(r"@[A-Za-z0-9_.]+(?:\([^)]*\))?\s*", "", value).strip()
    value = value.replace("? extends ", "")
    for wrapper in ("ResponseEntity", "Optional"):
        if value.startswith(wrapper + "<"):
            return strip_wrappers(value[len(wrapper)+1:-1])
    return value

def unwrap_type(value: str) -> tuple[str, bool]:
    value = strip_wrappers(value)
    for wrapper in ("List", "Set", "Collection"):
        if value.startswith(wrapper + "<"):
            inner, _ = unwrap_type(value[len(wrapper)+1:-1])
            return inner, True
    return value.split(".")[-1], False

def parse_annotation_args(args: str | None) -> dict[str, str]:
    """Interpreta los atributos de una anotacion Java (name/value/required/defaultValue).

    Un literal simple entre comillas sin clave se interpreta como el atributo
    ``value`` (equivalente a ``name`` en @RequestParam/@PathVariable).
    """
    if not args:
        return {}
    bare = re.match(r'^\s*"([^"]*)"\s*$', args)
    if bare:
        return {"value": bare.group(1)}
    result: dict[str, str] = {}
    for match in re.finditer(r'(\w+)\s*=\s*("([^"]*)"|[\w.]+)', args):
        result[match.group(1)] = match.group(3) if match.group(3) is not None else match.group(2)
    return result

def convert_default(raw_value: str, schema: dict) -> object:
    kind = schema.get("type")
    if kind == "integer":
        try: return int(raw_value)
        except ValueError: return raw_value
    if kind == "number":
        try: return float(raw_value)
        except ValueError: return raw_value
    if kind == "boolean":
        return raw_value.lower() == "true"
    return raw_value

def pageable_parameters() -> list[dict]:
    return [
        {"name": "page", "in": "query", "required": False,
         "description": "Numero de pagina solicitado (0-index).",
         "schema": {"type": "integer", "format": "int32", "default": 0}},
        {"name": "size", "in": "query", "required": False,
         "description": "Cantidad de elementos por pagina.",
         "schema": {"type": "integer", "format": "int32", "default": 20}},
        {"name": "sort", "in": "query", "required": False,
         "description": "Criterios de orden, formato propiedad,(asc|desc). Repetible.",
         "schema": {"type": "array", "items": {"type": "string"}}},
    ]

def paginated_schema(inner_expr: str, kind: str, known: set[str], extra_schemas: dict[str, dict]) -> dict:
    item_schema = schema_for_type(inner_expr.strip(), known)
    item_name = item_schema.get("$ref", "").rsplit("/", 1)[-1]
    schema_name = f"{kind}{item_name}" if item_name else kind
    if schema_name not in extra_schemas:
        if kind == "PaginaResponse":
            extra_schemas[schema_name] = {
                "type": "object",
                "description": "Pagina generica devuelta por PaginaResponse<T> del codigo fuente.",
                "properties": {
                    "contenido": {"type": "array", "items": item_schema},
                    "pagina": {"type": "integer", "format": "int32"},
                    "tamanio": {"type": "integer", "format": "int32"},
                    "totalElementos": {"type": "integer", "format": "int64"},
                    "totalPaginas": {"type": "integer", "format": "int32"},
                    "primera": {"type": "boolean"},
                    "ultima": {"type": "boolean"},
                },
                "required": ["contenido", "pagina", "tamanio", "totalElementos", "totalPaginas", "primera", "ultima"],
            }
        else:
            extra_schemas[schema_name] = {
                "type": "object",
                "description": "Representacion serializada por defecto de org.springframework.data.domain.Page.",
                "properties": {
                    "content": {"type": "array", "items": item_schema},
                    "totalElements": {"type": "integer", "format": "int64"},
                    "totalPages": {"type": "integer", "format": "int32"},
                    "number": {"type": "integer", "format": "int32"},
                    "size": {"type": "integer", "format": "int32"},
                    "numberOfElements": {"type": "integer", "format": "int32"},
                    "first": {"type": "boolean"},
                    "last": {"type": "boolean"},
                    "empty": {"type": "boolean"},
                },
                "required": ["content", "totalElements", "totalPages", "number", "size", "numberOfElements", "first", "last", "empty"],
            }
    return {"$ref": f"#/components/schemas/{schema_name}"}

def schema_for_type(value: str, known: set[str]) -> dict:
    name, array = unwrap_type(value)
    if array:
        return {"type": "array", "items": schema_for_type(name, known)}
    if name in PRIMITIVES:
        return dict(PRIMITIVES[name])
    if name in known:
        return {"$ref": f"#/components/schemas/{name}"}
    return {"type": "string", "description": f"Valor Java {name}"}

def discover_types(root: Path) -> dict[str, dict]:
    definitions: dict[str, list[tuple[str, str, bool]]] = {}
    enums: dict[str, list[str]] = {}
    for path in root.glob("src/main/java/**/*.java"):
        text = clean_java(path.read_text(encoding="utf-8"))
        em = re.search(r"\benum\s+(\w+)\s*\{([^;}]*)", text, re.S)
        if em:
            vals = [x.strip() for x in em.group(2).split(",") if re.fullmatch(r"[A-Z][A-Z0-9_]*", x.strip())]
            enums[em.group(1)] = vals
        rm = re.search(r"\brecord\s+(\w+)\s*\((.*?)\)\s*\{", text, re.S)
        if rm:
            fields = []
            for item in split_top(rm.group(2)):
                required = bool(re.search(r"@(NotNull|NotBlank|NotEmpty)\b", item))
                plain = re.sub(r"@[A-Za-z0-9_.]+(?:\([^)]*\))?\s*", "", item).strip()
                fm = re.search(r"([\w.<>?, ]+)\s+(\w+)$", plain)
                if fm: fields.append((fm.group(2), fm.group(1).strip(), required))
            definitions[rm.group(1)] = fields
            continue
        cm = re.search(r"\b(?:class|interface)\s+(\w+)", text)
        if cm and ("dto" in str(path).lower() or path.name.endswith(("Request.java", "Response.java"))):
            fields = []
            for fm in re.finditer(r"(?m)^\s*(?:private|public|protected)\s+(?!static\b)(?:final\s+)?([\w.<>?, ]+)\s+(\w+)\s*;", text):
                fields.append((fm.group(2), fm.group(1).strip(), False))
            definitions[cm.group(1)] = fields
    known = set(definitions) | set(enums)
    schemas = {}
    for name, values in sorted(enums.items()):
        schemas[name] = {"type": "string", "enum": values}
    for name, fields in sorted(definitions.items()):
        props = {field: schema_for_type(kind, known) for field, kind, _ in fields}
        schema = {"type": "object", "properties": props}
        required = [field for field, _, req in fields if req]
        if required: schema["required"] = required
        schemas[name] = schema
    return schemas

def controllers(root: Path) -> list[Path]:
    return sorted(root.glob("src/main/java/**/*Controller.java"))

def discover_operations(root: Path, extra_schemas: dict[str, dict] | None = None) -> dict[tuple[str, str], dict]:
    if extra_schemas is None:
        extra_schemas = {}
    schemas = discover_types(root)
    known = set(schemas)
    operations = {}
    for path in controllers(root):
        text = clean_java(path.read_text(encoding="utf-8"))
        class_pos = text.find(" class ")
        prefix = text[:class_pos] if class_pos >= 0 else text
        base_matches = list(re.finditer(r"@RequestMapping\s*(?:\((.*?)\))?", prefix, re.S))
        base = annotation_path(base_matches[-1].group(1)) if base_matches else ""
        controller = path.stem
        pattern = re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*(?:\((.*?)\))?\s*((?:@[\w.]+(?:\([^)]*\))?\s*)*)public\s+([\w.<>?, ]+)\s+(\w+)\s*\((.*?)\)\s*\{", re.S)
        for match in pattern.finditer(text):
            method = MAP_METHOD[match.group(1)]
            route = join_path(base, annotation_path(match.group(2)))
            return_type, _ = unwrap_type(match.group(4).strip())
            params = split_top(match.group(6))
            op_params, body_type = [], None
            for raw in params:
                plain = re.sub(r"@[A-Za-z0-9_.]+(?:\([^)]*\))?\s*", "", raw).strip()
                pm = re.search(r"([\w.<>?, ]+)\s+(\w+)$", plain)
                if not pm: continue
                ptype, pname = pm.group(1).strip(), pm.group(2)
                if "@RequestBody" in raw:
                    body_type = ptype
                elif ptype.split(".")[-1] == "Pageable":
                    op_params.extend(pageable_parameters())
                elif "@PathVariable" in raw or "@RequestParam" in raw:
                    ann = "PathVariable" if "@PathVariable" in raw else "RequestParam"
                    am = re.search(rf"@{ann}(?:\(([^)]*)\))?", raw)
                    attrs = parse_annotation_args(am.group(1) if am else None)
                    explicit = attrs.get("name") or attrs.get("value") or ""
                    param_schema = schema_for_type(ptype, known)
                    if ann == "PathVariable":
                        required = True
                    elif "defaultValue" in attrs:
                        required = False
                    elif "required" in attrs:
                        required = attrs["required"] != "false"
                    else:
                        required = True
                    if "defaultValue" in attrs:
                        param_schema = dict(param_schema)
                        param_schema["default"] = convert_default(attrs["defaultValue"], param_schema)
                    op_params.append({"name": explicit or pname, "in": "path" if ann == "PathVariable" else "query", "required": required, "schema": param_schema})
            success = "204" if return_type in ("Void", "void") else ("201" if method == "post" and "ResponseEntity.created" in text[match.end():match.end()+700] else "200")
            peeled_return = strip_wrappers(match.group(4).strip())
            page_match = re.match(r"^(Page|PaginaResponse)<(.*)>$", peeled_return, re.S)
            if page_match:
                response_schema = paginated_schema(page_match.group(2), page_match.group(1), known, extra_schemas)
            else:
                response_schema = schema_for_type(match.group(4).strip(), known)
            operation = {"operationId": f"{controller}_{match.group(5)}", "tags": [controller], "responses": {success: {"description": "Respuesta satisfactoria"}}}
            if response_schema and success != "204": operation["responses"][success]["content"] = {"application/json": {"schema": response_schema}}
            if op_params: operation["parameters"] = op_params
            if body_type:
                operation["requestBody"] = {"required": True, "content": {"application/json": {"schema": schema_for_type(body_type, known)}}}
            if route.startswith("/api/v1/internal/") or route.startswith("/api/v1/internal/experimentos/"):
                operation["security"] = [{"internalApiKey": []}]
            elif not (route.startswith("/api/v1/auth/") and route.split("/")[-1] in {"login", "refresh", "logout", "forgot-password", "reset-password"}):
                operation["security"] = [{"bearerAuth": []}]
            operations[(method, route)] = operation
    return operations

def make_contract(label: str, root: Path, title: str, version: str) -> dict:
    extra_schemas: dict[str, dict] = {}
    ops = discover_operations(root, extra_schemas)
    paths = {}
    for (method, route), operation in sorted(ops.items(), key=lambda x: (x[0][1], x[0][0])):
        paths.setdefault(route, {})[method] = operation
    all_schemas = dict(discover_types(root))
    all_schemas.update(extra_schemas)
    return {"openapi": "3.1.0", "info": {"title": title, "version": version,
            "description": "Snapshot determinista derivado de controladores y DTO del código fuente vigente."},
            "paths": paths, "components": {"securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
                "internalApiKey": {"type": "apiKey", "in": "header", "name": "X-Internal-Api-Key"}},
                "schemas": dict(sorted(all_schemas.items()))}}

def gateway_contract(contracts: dict[str, dict]) -> dict:
    public_prefixes = ("/api/v1/auth", "/api/v1/perfiles", "/api/v1/docentes", "/api/v1/estudiantes", "/api/v1/administradores",
        "/api/v1/reservas", "/api/v1/solicitudes", "/api/v1/agenda", "/api/v1/disponibilidad", "/api/v1/incidentes",
        "/api/v1/notificaciones", "/api/v1/planificaciones", "/api/v1/planificaciones-agregadas", "/api/v1/asistencias",
        "/api/v1/observabilidad",
        "/api/v1/campus", "/api/v1/bloques", "/api/v1/pisos", "/api/v1/laboratorios", "/api/v1/equipos",
        "/api/v1/tipos-equipo", "/api/v1/facultades", "/api/v1/carreras", "/api/v1/materias", "/api/v1/periodos-lectivos", "/api/v1/horarios")
    paths, schemas = {}, {}
    for label, contract in contracts.items():
        schemas.update(contract["components"]["schemas"])
        for route, item in contract["paths"].items():
            if route.startswith(public_prefixes) and "/internal/" not in route:
                copied = json.loads(json.dumps(item))
                for operation in copied.values():
                    operation["description"] = f"Atendido por el servicio {label}."
                paths[route] = copied
    # GatewayRoutes conserva este alias de Auth; se documenta sin inventar un handler.
    for route, item in contracts["Auth"]["paths"].items():
        if "/internal/" in route:
            continue
        legacy = "/auth-service" + route
        copied = json.loads(json.dumps(item))
        for operation in copied.values():
            operation["operationId"] = "legacy_" + operation["operationId"]
            operation["deprecated"] = True
            operation["description"] = "Alias heredado atendido por Auth; Gateway elimina el primer segmento."
        paths[legacy] = copied
    for route, item in contracts["Usuarios"]["paths"].items():
        if route.startswith("/internal/") or route.startswith("/api/v1/internal/"):
            continue
        legacy = "/usuarios-service" + route
        copied = json.loads(json.dumps(item))
        for operation in copied.values():
            operation["operationId"] = "legacyUsuarios_" + operation["operationId"]
            operation["deprecated"] = True
            operation["description"] = "Alias heredado atendido por Usuarios; Gateway elimina el primer segmento."
        paths[legacy] = copied
    return {"openapi": "3.1.0", "info": {"title": "SCLI - API Gateway", "version": "1.0.0",
        "description": "Contrato de fachada compuesto desde GatewayRoutes y los contratos de servicio. No representa controladores propios."},
        "paths": dict(sorted(paths.items())), "components": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}}, "schemas": dict(sorted(schemas.items()))}}

def local_refs(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str): yield value
            yield from local_refs(value)
    elif isinstance(node, list):
        for value in node: yield from local_refs(value)

def resolve_ref(doc, ref):
    if not ref.startswith("#/"): return False
    cur = doc
    try:
        for part in ref[2:].split("/"): cur = cur[part.replace("~1", "/").replace("~0", "~")]
        return True
    except (KeyError, TypeError): return False

def validate_doc(path: Path) -> tuple[dict | None, list[str]]:
    errors = []
    try: doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: return None, [f"{path}: JSON inválido: {exc}"]
    for field in ("openapi", "info", "paths"):
        if field not in doc: errors.append(f"{path}: falta {field}")
    ids = []
    schemes = doc.get("components", {}).get("securitySchemes", {})
    for route, item in doc.get("paths", {}).items():
        for method, op in item.items():
            if method not in HTTP: errors.append(f"{path}: método inválido {method} en {route}"); continue
            if op.get("operationId"): ids.append(op["operationId"])
            for req in op.get("security", []):
                for name in req:
                    if name not in schemes: errors.append(f"{path}: securityScheme inexistente {name}")
    for oid, count in Counter(ids).items():
        if count > 1: errors.append(f"{path}: operationId duplicado {oid}")
    for ref in local_refs(doc):
        if not resolve_ref(doc, ref): errors.append(f"{path}: $ref no resoluble {ref}")
    return doc, errors

def operation_keys(doc):
    return {(method, route) for route, item in doc.get("paths", {}).items() for method in item if method in HTTP}

def canonical_json_bytes(document: dict) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

def gateway_catalog_payload(document: dict) -> dict:
    operations = []
    for method, route in sorted(operation_keys(document), key=lambda item: (item[1], item[0])):
        operation = document["paths"][route][method]
        parameters = []
        for parameter in operation.get("parameters", []):
            if parameter.get("in") != "path":
                continue
            schema = parameter.get("schema", {})
            if "$ref" in schema:
                schema = document["components"]["schemas"][schema["$ref"].rsplit("/", 1)[-1]]
            metadata = {"name": parameter["name"], "type": schema.get("type", "string")}
            if "format" in schema:
                metadata["format"] = schema["format"]
            if "enum" in schema:
                metadata["enum"] = schema["enum"]
            parameters.append(metadata)
        operations.append({"method": method.upper(), "path": route, "parameters": parameters})
    raw = json.dumps(operations, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "format": "deflate-base64-json-v1",
        "source": "docs/openapi/api-gateway-openapi.json",
        "sourceSha256": hashlib.sha256(canonical_json_bytes(document)).hexdigest(),
        "operationCount": len(operations),
        "payload": base64.b64encode(zlib.compress(raw, 9)).decode("ascii"),
    }

def validate_gateway_catalog(path: Path, gateway: dict) -> list[str]:
    errors = []
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
        payload = zlib.decompress(base64.b64decode(catalog["payload"])).decode("utf-8")
        operations = json.loads(payload)
        actual = {(item["method"].lower(), item["path"]) for item in operations}
        expected = operation_keys(gateway)
        if actual != expected:
            errors.append("Gateway: el catalogo runtime no coincide con OpenAPI")
        if catalog.get("operationCount") != len(expected):
            errors.append("Gateway: operationCount del catalogo no coincide")
        expected_hash = hashlib.sha256(canonical_json_bytes(gateway)).hexdigest()
        if catalog.get("sourceSha256") != expected_hash:
            errors.append("Gateway: el hash del catalogo no coincide con api-gateway-openapi.json")
    except (OSError, KeyError, TypeError, ValueError, zlib.error) as exc:
        errors.append(f"Gateway: catalogo runtime invalido: {exc}")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate", action="store_true", help="regenera los cinco snapshots")
    args = parser.parse_args()
    expected = {}; generated = {}
    for label, (root, filename, title, version) in SERVICES.items():
        expected[label] = set(discover_operations(root))
        generated[label] = make_contract(label, root, title, version)
    gateway = gateway_contract(generated)
    if args.generate:
        DOCS.mkdir(parents=True, exist_ok=True)
        for label, (_, filename, _, _) in SERVICES.items():
            (DOCS / filename).write_bytes(canonical_json_bytes(generated[label]))
        (DOCS / "api-gateway-openapi.json").write_bytes(canonical_json_bytes(gateway))
        catalog_path = ROOT / "services/api-gateway/src/main/resources/gateway-route-catalog.json"
        catalog_path.write_text(json.dumps(gateway_catalog_payload(gateway), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    errors = []
    loaded = {}
    for label, (_, filename, _, _) in SERVICES.items():
        doc, structural = validate_doc(DOCS / filename); errors += structural
        actual = operation_keys(doc or {})
        missing, extra = expected[label] - actual, actual - expected[label]
        if missing: errors.append(f"{label}: faltan {sorted(missing)}")
        if extra: errors.append(f"{label}: sobran {sorted(extra)}")
        if any(route.startswith("/api/v1/tecnicos") for _, route in actual): errors.append(f"{label}: contiene /api/v1/tecnicos obsoleto")
        if doc != generated[label]: errors.append(f"{label}: el snapshot difiere de la extracción determinista vigente")
        loaded[label] = doc or {}
        print(f"{label}: {len(actual & expected[label])}/{len(expected[label])} coincidencias auxiliares del snapshot; extras={len(extra)}")
    gateway_doc, structural = validate_doc(DOCS / "api-gateway-openapi.json"); errors += structural
    expected_gateway = operation_keys(gateway)
    actual_gateway = operation_keys(gateway_doc or {})
    if expected_gateway != actual_gateway: errors.append("Gateway: deriva respecto de GatewayRoutes/contratos de servicio")
    if gateway_doc != gateway: errors.append("Gateway: el snapshot difiere de la composición determinista vigente")
    errors += validate_gateway_catalog(
        ROOT / "services/api-gateway/src/main/resources/gateway-route-catalog.json", gateway_doc or {})
    gateway_files = list((ROOT / "services/api-gateway").glob("src/main/java/**/GatewayRoutes.java"))
    if len(gateway_files) != 1:
        errors.append(f"Gateway: se esperaba un GatewayRoutes.java y se encontraron {len(gateway_files)}")
        gateway_source = ""
    else:
        gateway_source = gateway_files[0].read_text(encoding="utf-8")
    for marker in ("authApiRoute", "authServiceRoute", "usuariosServiceRoute", "usuariosApiRoute", "reservasSolicitudesServiceRoute", "academicoServiceRoute"):
        if marker not in gateway_source: errors.append(f"Gateway: falta familia configurada {marker}")
    print(f"Gateway: {len(actual_gateway)}/{len(expected_gateway)} coincidencias auxiliares de fachada; 6/6 marcadores presentes")
    print(f"OpenAPI structural validation: {'OK' if not errors else 'FAIL'} ({len(errors)} errores)")
    for error in errors: print(f"ERROR: {error}")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
