package ec.edu.scli.reservas.security;

import ec.edu.scli.reservas.application.service.DisponibilidadService;
import ec.edu.scli.reservas.config.SecurityConfig;
import ec.edu.scli.reservas.infrastructure.audit.AuditLogger;
import ec.edu.scli.reservas.presentation.controller.DisponibilidadController;
import ec.edu.scli.reservas.presentation.controller.ObservabilidadMobileController;
import ec.edu.scli.reservas.presentation.controller.SolicitudReservaController;
import ec.edu.scli.reservas.application.service.SolicitudReservaService;
import ec.edu.scli.reservas.application.service.PlanificacionService;
import ec.edu.scli.reservas.presentation.controller.PlanificacionController;
import ec.edu.scli.reservas.presentation.controller.AsistenciaController;
import ec.edu.scli.reservas.application.service.AsistenciaService;
import ec.edu.scli.reservas.observability.MobileHttpMetrics;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;
import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import org.springframework.security.access.AccessDeniedException;

@WebMvcTest({DisponibilidadController.class, SolicitudReservaController.class, PlanificacionController.class,
        AsistenciaController.class, ObservabilidadMobileController.class})
@Import({SecurityConfig.class, JwtAuthenticationFilter.class, JwtTokenProvider.class,
        ExperimentalInternalApiKeyFilter.class})
@TestPropertySource(properties = {
        "security.jwt.issuer=scli-auth-service",
        "security.jwt.secret=MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
})
class ReservasSecurityIntegrationTest {
    @Autowired private MockMvc mockMvc;
    @MockitoBean private DisponibilidadService disponibilidadService;
    @MockitoBean private SolicitudReservaService solicitudService;
    @MockitoBean private AuditLogger auditLogger;
    @MockitoBean private PlanificacionService planificacionService;
    @MockitoBean private AsistenciaService asistenciaService;
    @MockitoBean private MobileHttpMetrics mobileHttpMetrics;

    @Test
    void sinTokenResponde401() throws Exception {
        mockMvc.perform(consulta()).andExpect(status().isUnauthorized());
    }

    @Test
    void accessTokenConPermisoEsAceptado() throws Exception {
        mockMvc.perform(consulta().header("Authorization", "Bearer " + token("access", List.of("LABORATORIO_LEER"))))
                .andExpect(status().isOk());
    }

    @Test
    void refreshTokenEsRechazadoCon401() throws Exception {
        mockMvc.perform(consulta().header("Authorization", "Bearer " + token("refresh", List.of("LABORATORIO_LEER"))))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void accessTokenSinPermisoResponde403() throws Exception {
        mockMvc.perform(consulta().header("Authorization", "Bearer " + token("access", List.of("RESERVA_LEER"))))
                .andExpect(status().isForbidden());
    }

    @Test
    void accessTokenSinPermisoAuditaAccesoDenegado() throws Exception {
        mockMvc.perform(consulta().header("Authorization", "Bearer " + token("access", List.of("RESERVA_LEER"))))
                .andExpect(status().isForbidden());

        verify(auditLogger).registrarEvento(
                eq("acceso_denegado"), any(), any(), org.mockito.ArgumentMatchers.contains("/api/v1/disponibilidad/laboratorios/"));
    }

    @Test
    void metricasMobileRequiereJwt() throws Exception {
        mockMvc.perform(post("/api/v1/observabilidad/mobile/http-latency")
                        .contentType("application/json")
                        .content(metricasJson()))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void metricasMobileAceptaAccessTokenSinPermisoArtificial() throws Exception {
        mockMvc.perform(post("/api/v1/observabilidad/mobile/http-latency")
                        .header("Authorization", "Bearer " + token("access", List.of()))
                        .contentType("application/json")
                        .content(metricasJson()))
                .andExpect(status().isAccepted());
    }

    @Test
    void metricasMobileValidaDto() throws Exception {
        mockMvc.perform(post("/api/v1/observabilidad/mobile/http-latency")
                        .header("Authorization", "Bearer " + token("access", List.of()))
                        .contentType("application/json")
                        .content("{\"method\":\"TRACE\",\"route\":\"\",\"durationMs\":-1,\"success\":true}"))
                .andExpect(status().isBadRequest());
    }

    @Test
    void docenteConPermisoActualPuedeAceptarPropuesta() throws Exception {
        UUID perfilId = UUID.randomUUID();
        mockMvc.perform(post("/api/v1/solicitudes/{id}/propuesta/aceptar", UUID.randomUUID())
                        .header("Authorization", "Bearer " + token(
                                "access", "DOCENTE", perfilId, List.of("SOLICITUD_CREAR")))
                        .contentType("application/json").content("{\"comentario\":\"Acepto\"}"))
                .andExpect(status().isOk());
    }

    @Test
    void docenteAjenoEsRechazadoPorOwnershipAunqueTengaPermisoHttp() throws Exception {
        UUID perfilAjeno = UUID.randomUUID();
        UUID solicitudId = UUID.randomUUID();
        when(solicitudService.aceptarPropuesta(eq(solicitudId), any(), eq(perfilAjeno)))
                .thenThrow(new AccessDeniedException("La solicitud pertenece a otro usuario"));
        mockMvc.perform(post("/api/v1/solicitudes/{id}/propuesta/aceptar", solicitudId)
                        .header("Authorization", "Bearer " + token(
                                "access", "DOCENTE", perfilAjeno, List.of("SOLICITUD_CREAR")))
                        .contentType("application/json").content("{}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void administradorPisoNoPuedeAceptarSinPermisoDeCreacion() throws Exception {
        mockMvc.perform(post("/api/v1/solicitudes/{id}/propuesta/aceptar", UUID.randomUUID())
                        .header("Authorization", "Bearer " + token(
                                "access", "ADMINISTRADOR_PISO", UUID.randomUUID(),
                                List.of("SOLICITUD_APROBAR")))
                        .contentType("application/json").content("{}"))
                .andExpect(status().isForbidden());
    }

    @Test
    void coordinadorConPermisoPuedeCrearPlanificacion() throws Exception {
        when(planificacionService.crear(any())).thenReturn(new ec.edu.scli.reservas.presentation.dto.response.PlanificacionResponse(
                UUID.randomUUID(), UUID.randomUUID(), UUID.randomUUID(), UUID.randomUUID(), null,
                UUID.randomUUID(), "LUNES", java.time.LocalTime.of(8, 0), java.time.LocalTime.of(10, 0),
                "BORRADOR", null, UUID.randomUUID(), java.time.Instant.now(), java.time.Instant.now(), 0L));
        mockMvc.perform(post("/api/v1/planificaciones")
                        .header("Authorization", "Bearer " + token("access", "COORDINADOR", UUID.randomUUID(),
                                List.of("PLANIFICACION_GESTIONAR")))
                        .contentType("application/json").content(planificacionJson()))
                .andExpect(status().isCreated());
    }

    @Test
    void docenteYEstudianteNoPuedenGestionarPlanificacion() throws Exception {
        for (String rol : List.of("DOCENTE", "ESTUDIANTE")) {
            mockMvc.perform(post("/api/v1/planificaciones")
                            .header("Authorization", "Bearer " + token("access", rol, UUID.randomUUID(),
                                    List.of("ACADEMICO_LEER")))
                            .contentType("application/json").content(planificacionJson()))
                    .andExpect(status().isForbidden());
        }
    }

    @Test
    void planificacionSinJwtEs401YRefreshEsRechazado() throws Exception {
        mockMvc.perform(get("/api/v1/planificaciones")).andExpect(status().isUnauthorized());
        mockMvc.perform(get("/api/v1/planificaciones")
                        .header("Authorization", "Bearer " + token("refresh", "COORDINADOR", UUID.randomUUID(),
                                List.of("PLANIFICACION_GESTIONAR"))))
                .andExpect(status().isUnauthorized());
    }

    @Test void estudianteSoloConsultaSuHorarioYNoPuedeAbrirSesiones() throws Exception {
        String token=token("access","ESTUDIANTE",UUID.randomUUID(),List.of("ACADEMICO_LEER"));
        mockMvc.perform(get("/api/v1/asistencias/mi-horario").header("Authorization","Bearer "+token)).andExpect(status().isOk());
        mockMvc.perform(post("/api/v1/asistencias/sesiones").header("Authorization","Bearer "+token)
                .contentType("application/json").content("{\"bloqueId\":\""+UUID.randomUUID()+"\"}"))
                .andExpect(status().isForbidden());
    }

    @Test void docentePuedeAbrirPeroNoConsultarHorarioDeEstudiante() throws Exception {
        String token=token("access","DOCENTE",UUID.randomUUID(),List.of("RESERVA_LEER"));
        mockMvc.perform(post("/api/v1/asistencias/sesiones").header("Authorization","Bearer "+token)
                .contentType("application/json").content("{\"bloqueId\":\""+UUID.randomUUID()+"\"}"))
                .andExpect(status().isCreated());
        mockMvc.perform(get("/api/v1/asistencias/mi-horario").header("Authorization","Bearer "+token)).andExpect(status().isForbidden());
    }

    private String planificacionJson() {
        return """
                {"planificacionId":"%s","nivel":5,\
                 "periodoId":"%s","carreraId":"%s","materiaId":"%s",\
                 "laboratorioId":"%s","diaSemana":"LUNES",\
                 "horaInicio":"08:00","horaFin":"10:00"}
                """.formatted(UUID.randomUUID(), UUID.randomUUID(), UUID.randomUUID(),
                        UUID.randomUUID(), UUID.randomUUID());
    }

    private String metricasJson() {
        return """
                {"method":"GET","route":"/api/v1/incidentes/{id}",\
                 "durationMs":125,"status":200,"success":true}
                """;
    }

    private org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder consulta() {
        return get("/api/v1/disponibilidad/laboratorios/{id}", UUID.randomUUID())
                .param("fecha", "2030-01-01").param("horaInicio", "08:00").param("horaFin", "09:00");
    }

    private String token(String type, List<String> permissions) {
        return token(type, "DOCENTE", UUID.randomUUID(), permissions);
    }

    private String token(String type, String role, UUID perfilId, List<String> permissions) {
        return Jwts.builder().issuer("scli-auth-service")
                .subject(UUID.randomUUID().toString())
                .claim("perfilId", perfilId.toString())
                .claim("username", "usuario@scli.edu.ec")
                .claim("type", type).claim("roles", List.of(role))
                .claim("permissions", permissions)
                .expiration(new Date(System.currentTimeMillis() + 60_000))
                .signWith(Keys.hmacShaKeyFor("0123456789abcdef0123456789abcdef"
                        .getBytes(StandardCharsets.UTF_8))).compact();
    }
}
