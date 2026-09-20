package ec.edu.uteq.scli.api_gateway.routes;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class GatewayRoutesTest {

    @Test
    void reconoceRutasCanonicasDeTodosLosServicios() {
        assertThat(GatewayRoutes.esRutaAuth("/api/v1/auth/login")).isTrue();
        assertThat(GatewayRoutes.esRutaAuth("/api/v1/auth/admin/usuarios")).isTrue();
        assertThat(GatewayRoutes.esRutaUsuarios("/api/v1/perfiles/123")).isTrue();
        assertThat(GatewayRoutes.esRutaUsuarios("/api/v1/docentes")).isTrue();
        assertThat(GatewayRoutes.esRutaAcademica("/api/v1/laboratorios/123")).isTrue();
        assertThat(GatewayRoutes.esRutaReservasCanonica("/api/v1/solicitudes/123/aprobar")).isTrue();
        assertThat(GatewayRoutes.esRutaReservasCanonica("/api/v1/incidentes")).isTrue();
        assertThat(GatewayRoutes.esRutaReservasCanonica("/api/v1/notificaciones/dispositivos")).isTrue();
        assertThat(GatewayRoutes.esRutaReservasCanonica(
                "/api/v1/observabilidad/mobile/http-latency")).isTrue();
        assertThat(GatewayRoutes.esRutaReservasCanonica(
                "/api/v1/planificaciones-agregadas/123/enviar")).isTrue();
    }

    @Test
    void noExponeRutasInternasComoRutaCanonica() {
        assertThat(GatewayRoutes.esRutaAuth("/api/v1/internal/auth")).isFalse();
        assertThat(GatewayRoutes.esRutaUsuarios("/api/v1/internal/perfiles/123")).isFalse();
        assertThat(GatewayRoutes.esRutaAcademica("/api/v1/internal/laboratorios/123/exists")).isFalse();
        assertThat(GatewayRoutes.esRutaReservasCanonica("/api/v1/internal/reservas/123")).isFalse();
        assertThat(GatewayRoutes.esRutaReservasCanonica("/api/v1/internal/observabilidad/mobile")).isFalse();
        assertThat(GatewayRoutes.esRutaUsuariosLegacy(
                "/usuarios-service/api/v1/internal/perfiles/123")).isFalse();
    }

    @Test
    void noAceptaPrefijosParecidos() {
        assertThat(GatewayRoutes.esRutaUsuarios("/api/v1/docentes-internal")).isFalse();
        assertThat(GatewayRoutes.esRutaAcademica("/api/v1/laboratorios-internal")).isFalse();
        assertThat(GatewayRoutes.esRutaReservasCanonica("/api/v1/reservas-internal")).isFalse();
        assertThat(GatewayRoutes.esRutaReservasCanonica("/api/v1/observabilidad-internal")).isFalse();
    }
}
