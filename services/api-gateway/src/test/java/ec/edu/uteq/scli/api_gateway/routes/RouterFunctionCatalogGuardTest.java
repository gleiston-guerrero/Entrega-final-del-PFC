package ec.edu.uteq.scli.api_gateway.routes;

import org.junit.jupiter.api.Test;
import org.springframework.asm.AnnotationVisitor;
import org.springframework.asm.ClassReader;
import org.springframework.asm.ClassVisitor;
import org.springframework.asm.Handle;
import org.springframework.asm.MethodVisitor;
import org.springframework.asm.Opcodes;

import java.io.IOException;
import java.io.InputStream;
import java.net.URISyntaxException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Inspecciona bytecode de produccion: los beans delegan en el constructor contratado
 * y no alcanzan construcciones/composiciones alternativas fuera de ese limite.
 * La semantica del constructor se comprueba ademas con pruebas del router real.
 */
class RouterFunctionCatalogGuardTest {

    private static final String HELPER = "ec/edu/uteq/scli/api_gateway/routes/GatewayRoutes#rutaContratada(Ljava/lang/String;Ljava/lang/String;Ljava/util/function/Predicate;I)Lorg/springframework/web/servlet/function/RouterFunction;";
    private static final String CATALOG_OWNER = "ec/edu/uteq/scli/api_gateway/routes/GatewayRouteCatalog";
    private static final String CATALOG_METHOD = "accepts";
    private static final String BEAN_ANNOTATION_DESC = "Lorg/springframework/context/annotation/Bean;";
    private static final String ROUTER_FUNCTION_DESC_FRAGMENT = "Lorg/springframework/web/servlet/function/RouterFunction;";

    @Test
    void todosLosBeansDeleganSinConstruccionesAlternativas() throws IOException, URISyntaxException {
        MethodGraph grafo = MethodGraph.leer(Path.of(GatewayRoutes.class.getProtectionDomain()
                .getCodeSource().getLocation().toURI()));
        assertThat(grafo.metodosBeanRouterFunction).as("beans RouterFunction de produccion").isNotEmpty();
        assertThat(grafo.incumplimientos()).as("beans RouterFunction que omiten rutaContratada o construyen rutas fuera del helper")
                .isEmpty();
        assertThat(grafo.invocaCatalogo(HELPER)).as("rutaContratada alcanza GatewayRouteCatalog.accepts").isTrue();
    }

    @Test
    void detectaBeanQueConsultaCatalogoPeroConstruyeRutaDirecta() throws IOException {
        MethodGraph grafo = new MethodGraph();
        try (InputStream entrada = BypassFixture.class.getResourceAsStream("RouterFunctionCatalogGuardTest$BypassFixture.class")) {
            new ClassReader(entrada).accept(grafo.new Visitor(), 0);
        }
        assertThat(grafo.incumplimientos()).hasSize(2);
        assertThat(grafo.incumplimientos()).anyMatch(method -> method.contains("#bypassDocente("))
                .anyMatch(method -> method.contains("#sinHelper("));
    }

    static class BypassFixture {
        @org.springframework.context.annotation.Bean
        public org.springframework.web.servlet.function.RouterFunction<org.springframework.web.servlet.function.ServerResponse> sinHelper() {
            return construccionIndirecta();
        }

        private org.springframework.web.servlet.function.RouterFunction<org.springframework.web.servlet.function.ServerResponse> construccionIndirecta() {
            return org.springframework.cloud.gateway.server.mvc.handler.GatewayRouterFunctions.route("sinHelper")
                    .route(request -> true,
                            org.springframework.cloud.gateway.server.mvc.handler.HandlerFunctions.http()).build();
        }

        @org.springframework.context.annotation.Bean
        public org.springframework.web.servlet.function.RouterFunction<org.springframework.web.servlet.function.ServerResponse> bypassDocente() {
            GatewayRoutes.rutaContratada("ignorada", "http://localhost", path -> true, 0);
            return org.springframework.cloud.gateway.server.mvc.handler.GatewayRouterFunctions.route("bypass")
                    .route(request -> GatewayRouteCatalog.accepts(request.method().name(), request.path())
                            || request.path().startsWith("/api/v1/sin-contrato/"),
                            org.springframework.cloud.gateway.server.mvc.handler.HandlerFunctions.http()).build();
        }
    }
    /** Grafo de todas las clases de produccion; excluye target/test-classes. */
    private static final class MethodGraph {
        private final Set<String> metodosBeanRouterFunction = new HashSet<>();
        private final Map<String, Set<String>> llamadasInternas = new HashMap<>();
        private final Set<String> llamanDirectamenteAlCatalogo = new HashSet<>();

        static MethodGraph leer(Path clasesProduccion) throws IOException {
            MethodGraph grafo = new MethodGraph();
            try (var archivos = Files.walk(clasesProduccion)) {
                for (Path archivo : archivos.filter(path -> path.toString().endsWith(".class")).toList()) {
                    try (InputStream entrada = Files.newInputStream(archivo)) {
                        new ClassReader(entrada).accept(
                                grafo.new Visitor(), ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
                    }
                }
            }
            return grafo;
        }

        List<String> incumplimientos() {
            List<String> fallos = new ArrayList<>();
            for (String bean : metodosBeanRouterFunction) {
                Deque<String> pendientes = new ArrayDeque<>();
                Set<String> visitados = new HashSet<>();
                boolean contratado = false;
                boolean alternativa = false;
                pendientes.add(bean);
                while (!pendientes.isEmpty()) {
                    String actual = pendientes.poll();
                    if (!visitados.add(actual)) continue;
                    if (HELPER.equals(actual)) {
                        contratado = true;
                        continue; // La construccion solo se permite dentro de este limite confiable.
                    }
                    if (actual.startsWith("org/springframework/")
                            && (actual.contains("RouterFunction") || actual.contains("#route("))) {
                        alternativa = true;
                    }
                    pendientes.addAll(llamadasInternas.getOrDefault(actual, Set.of()));
                }
                if (!contratado || alternativa) fallos.add(bean);
            }
            return fallos;
        }

        boolean invocaCatalogo(String metodo) {
            Deque<String> pendientes = new ArrayDeque<>();
            Set<String> visitados = new HashSet<>();
            pendientes.add(metodo);
            while (!pendientes.isEmpty()) {
                String actual = pendientes.poll();
                if (!visitados.add(actual)) {
                    continue;
                }
                if (llamanDirectamenteAlCatalogo.contains(actual)) {
                    return true;
                }
                pendientes.addAll(llamadasInternas.getOrDefault(actual, Set.of()));
            }
            return false;
        }

        /** Visitor de clase: registra, por metodo, sus llamadas internas y las lambdas que crea. */
        private final class Visitor extends ClassVisitor {
            private String nombreInternoClase;

            Visitor() {
                super(Opcodes.ASM9);
            }

            @Override
            public void visit(int version, int access, String name, String signature,
                    String superName, String[] interfaces) {
                this.nombreInternoClase = name;
            }

            @Override
            public MethodVisitor visitMethod(int access, String name, String descriptor,
                    String signature, String[] exceptions) {
                String clave = nombreInternoClase + "#" + name + descriptor;
                boolean posibleBeanRouterFunction = descriptor.endsWith(")" + ROUTER_FUNCTION_DESC_FRAGMENT);
                return new MethodVisitor(Opcodes.ASM9) {
                    @Override
                    public AnnotationVisitor visitAnnotation(String annotationDescriptor, boolean visible) {
                        if (BEAN_ANNOTATION_DESC.equals(annotationDescriptor) && posibleBeanRouterFunction) {
                            metodosBeanRouterFunction.add(clave);
                        }
                        return null;
                    }

                    @Override
                    public void visitMethodInsn(int opcode, String owner, String invokedName,
                            String invokedDescriptor, boolean isInterface) {
                        registrarLlamada(clave, owner, invokedName, invokedDescriptor);
                    }

                    @Override
                    public void visitInvokeDynamicInsn(String invokedName, String invokedDescriptor,
                            Handle bootstrapMethodHandle, Object... bootstrapMethodArguments) {
                        for (Object argumento : bootstrapMethodArguments) {
                            if (argumento instanceof Handle implementacion) {
                                registrarLlamada(clave, implementacion.getOwner(),
                                        implementacion.getName(), implementacion.getDesc());
                            }
                        }
                    }
                };
            }

            private void registrarLlamada(String origen, String owner, String invokedName, String invokedDescriptor) {
                if (CATALOG_OWNER.equals(owner) && CATALOG_METHOD.equals(invokedName)) {
                    llamanDirectamenteAlCatalogo.add(origen);
                    return;
                }
                llamadasInternas.computeIfAbsent(origen, k -> new HashSet<>())
                        .add(owner + "#" + invokedName + invokedDescriptor);
            }
        }
    }
}
