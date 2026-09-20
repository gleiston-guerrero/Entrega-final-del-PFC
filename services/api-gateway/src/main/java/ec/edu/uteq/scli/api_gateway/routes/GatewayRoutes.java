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
                return route("auth_api")
                            .route(request -> acepta(request) && esRutaAuth(request.path()), http())
                                .before(uri(authServiceUrl))
                                .build();
        }

    @Bean
    public RouterFunction<ServerResponse> authServiceRoute(
            @Value("${AUTH_SERVICE_URL:http://auth-service:8081}") String authServiceUrl) {
        return route("auth_service")
            .route(request -> acepta(request) && request.path().startsWith("/auth-service/"), http())
                .before(uri(authServiceUrl))
                .before(stripPrefix(1))
                .build();
    }

    @Bean
    public RouterFunction<ServerResponse> usuariosServiceRoute(
            @Value("${USUARIOS_SERVICE_URL:http://usuarios-service:8082}") String usuariosServiceUrl) {
        return route("usuarios_service")
            .route(request -> acepta(request) && esRutaUsuariosLegacy(request.path()), http())
                .before(uri(usuariosServiceUrl))
                .before(stripPrefix(1))
                .build();
    }

    @Bean
    public RouterFunction<ServerResponse> usuariosApiRoute(
            @Value("${USUARIOS_SERVICE_URL:http://usuarios-service:8082}") String usuariosServiceUrl) {
        return route("usuarios_api")
            .route(request -> acepta(request) && esRutaUsuarios(request.path()), http())
                .before(uri(usuariosServiceUrl))
                .build();
    }

    @Bean
    public RouterFunction<ServerResponse> reservasSolicitudesServiceRoute(
            @Value("${RESERVAS_SOLICITUDES_SERVICE_URL:http://reservas-solicitudes-service:8084}")
            String reservasSolicitudesServiceUrl) {
        return route("reservas_solicitudes_service")
            .route(request -> acepta(request) && esRutaReservas(request.path()), http())
                .before(uri(reservasSolicitudesServiceUrl))
                .build();
    }

        @Bean
        public RouterFunction<ServerResponse> academicoServiceRoute(
                        @Value("${ACADEMICO_SERVICE_URL:http://academico-laboratorios-service:8083}")
                        String academicoServiceUrl) {
                return route("academico_service")
                    .route(request -> acepta(request) && esRutaAcademica(request.path()), http())
                                .before(uri(academicoServiceUrl))
                                .build();
        }

    private boolean esRutaReservas(String path) {
        return esRutaReservasCanonica(path);
    }

    private static boolean acepta(org.springframework.web.servlet.function.ServerRequest request) {
        return GatewayRouteCatalog.accepts(request.method().name(), request.path());
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
