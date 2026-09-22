package ec.edu.uteq.scli.api_gateway.routes;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.function.RouterFunction;
import org.springframework.web.servlet.function.ServerResponse;

import static org.springframework.cloud.gateway.server.mvc.filter.BeforeFilterFunctions.stripPrefix;
import static org.springframework.cloud.gateway.server.mvc.filter.BeforeFilterFunctions.uri;
import static org.springframework.cloud.gateway.server.mvc.handler.GatewayRouterFunctions.route;
import static org.springframework.cloud.gateway.server.mvc.handler.HandlerFunctions.http;

@Configuration
public class GatewayRoutes {

        @Bean
        public RouterFunction<ServerResponse> authApiRoute(
                        @Value("${AUTH_SERVICE_URL:http://auth-service:8081}") String authServiceUrl) {
                return rutaContratada("auth_api", authServiceUrl, path -> esRutaAuth(path), 0);
        }

    @Bean
    public RouterFunction<ServerResponse> authServiceRoute(
            @Value("${AUTH_SERVICE_URL:http://auth-service:8081}") String authServiceUrl) {
        return rutaContratada("auth_service", authServiceUrl, path -> path.startsWith("/auth-service/"), 1);
    }

    @Bean
    public RouterFunction<ServerResponse> usuariosServiceRoute(
            @Value("${USUARIOS_SERVICE_URL:http://usuarios-service:8082}") String usuariosServiceUrl) {
        return rutaContratada("usuarios_service", usuariosServiceUrl, path -> esRutaUsuariosLegacy(path), 1);
    }

    @Bean
    public RouterFunction<ServerResponse> usuariosApiRoute(
            @Value("${USUARIOS_SERVICE_URL:http://usuarios-service:8082}") String usuariosServiceUrl) {
        return rutaContratada("usuarios_api", usuariosServiceUrl, path -> esRutaUsuarios(path), 0);
    }

    @Bean
    public RouterFunction<ServerResponse> reservasSolicitudesServiceRoute(
            @Value("${RESERVAS_SOLICITUDES_SERVICE_URL:http://reservas-solicitudes-service:8084}")
            String reservasSolicitudesServiceUrl) {
        return rutaContratada("reservas_solicitudes_service", reservasSolicitudesServiceUrl, path -> esRutaReservas(path), 0);
    }

        @Bean
        public RouterFunction<ServerResponse> academicoServiceRoute(
                        @Value("${ACADEMICO_SERVICE_URL:http://academico-laboratorios-service:8083}")
                        String academicoServiceUrl) {
                return rutaContratada("academico_service", academicoServiceUrl, path -> esRutaAcademica(path), 0);
        }

    private boolean esRutaReservas(String path) {
        return esRutaReservasCanonica(path);
    }

    /** Constructor unico; scope solo recibe el path y no puede alterar el resultado del catalogo.
     * Acceso de paquete para probar el router real sin llamadas de red.
     */
    static RouterFunction<ServerResponse> rutaContratada(
            String nombre, String url, java.util.function.Predicate<String> scope, int segmentos) {
        var builder = route(nombre)
                .route(request -> GatewayRouteCatalog.accepts(request.method().name(), request.path())
                        && scope.test(request.path()), http())
                .before(uri(url));
        if (segmentos > 0) {
            builder.before(stripPrefix(segmentos));
        }
        return builder.build();
    }

    static boolean esRutaAuth(String path) {
        return coincide(path, "/api/v1/auth");
    }

    static boolean esRutaUsuarios(String path) {
        return coincideAlguna(path,
                "/api/v1/perfiles", "/api/v1/docentes", "/api/v1/estudiantes",
                "/api/v1/administradores");
    }

    static boolean esRutaUsuariosLegacy(String path) {
        return path.startsWith("/usuarios-service/")
                && !path.equals("/usuarios-service/api/v1/internal")
                && !path.startsWith("/usuarios-service/api/v1/internal/");
    }

    static boolean esRutaAcademica(String path) {
        return coincideAlguna(path,
                "/api/v1/campus", "/api/v1/bloques", "/api/v1/pisos",
                "/api/v1/laboratorios", "/api/v1/equipos", "/api/v1/tipos-equipo",
                "/api/v1/facultades", "/api/v1/carreras", "/api/v1/materias",
                "/api/v1/periodos-lectivos", "/api/v1/horarios");
    }

    static boolean esRutaReservasCanonica(String path) {
        return coincideAlguna(path, "/api/v1/reservas", "/api/v1/solicitudes",
                "/api/v1/agenda", "/api/v1/disponibilidad", "/api/v1/incidentes",
                "/api/v1/notificaciones", "/api/v1/planificaciones",
                "/api/v1/planificaciones-agregadas", "/api/v1/asistencias",
                "/api/v1/observabilidad");
    }

    private static boolean coincideAlguna(String path, String... bases) {
        for (String base : bases) {
            if (coincide(path, base)) {
                return true;
            }
        }
        return false;
    }

    private static boolean coincide(String path, String base) {
        return path.equals(base) || path.startsWith(base + "/");
    }
}
