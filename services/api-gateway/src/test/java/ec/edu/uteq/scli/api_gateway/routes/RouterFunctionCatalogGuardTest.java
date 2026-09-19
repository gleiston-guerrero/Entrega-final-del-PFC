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
 * Garantia por construccion (arquitectura), no por lista de rutas: analiza el
 * bytecode YA COMPILADO de las clases de configuracion del Gateway y
 * comprueba que TODO metodo {@code @Bean} que devuelve {@code RouterFunction}
 * invoca, directa o transitivamente (incluyendo lambdas y metodos privados
 * de las clases de produccion), {@code GatewayRouteCatalog.accepts(...)}.
 *
 * No depende de conocer de antemano ningun path: cualquier RouterFunction
 * futuro, con cualquier ruta nueva, que omita esa consulta hace fallar este
 * test porque su grafo de llamadas internas nunca alcanza el catalogo.
 */
class RouterFunctionCatalogGuardTest {

    private static final String CATALOG_OWNER = "ec/edu/uteq/scli/api_gateway/routes/GatewayRouteCatalog";
    private static final String CATALOG_METHOD = "accepts";
    private static final String BEAN_ANNOTATION_DESC = "Lorg/springframework/context/annotation/Bean;";
    private static final String ROUTER_FUNCTION_DESC_FRAGMENT = "Lorg/springframework/web/servlet/function/RouterFunction;";

    @Test
    void todosLosBeansRouterFunctionConsultanElCatalogoDeFormaTransitiva() throws IOException, URISyntaxException {
        Path clasesProduccion = Path.of(GatewayRoutes.class.getProtectionDomain()
                .getCodeSource().getLocation().toURI());
        MethodGraph grafo = MethodGraph.leer(clasesProduccion);
        assertThat(grafo.metodosBeanRouterFunction).as("beans RouterFunction de produccion").isNotEmpty();
        List<String> incumplimientos = new ArrayList<>();
        for (String beanMethod : grafo.metodosBeanRouterFunction) {
            if (!grafo.invocaCatalogo(beanMethod)) {
                incumplimientos.add(beanMethod);
            }
        }
        assertThat(incumplimientos)
                .as("beans RouterFunction que no consultan GatewayRouteCatalog.accepts(...) "
                        + "ni directa ni transitivamente")
                .isEmpty();
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
