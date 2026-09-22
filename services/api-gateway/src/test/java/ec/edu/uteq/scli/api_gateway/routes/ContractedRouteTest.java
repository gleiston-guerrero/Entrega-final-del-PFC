package ec.edu.uteq.scli.api_gateway.routes;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.web.servlet.function.ServerRequest;
import static org.assertj.core.api.Assertions.assertThat;

class ContractedRouteTest {
    @Test
    void rechazaRutaNoCatalogadaAunqueElAlcanceLaAcepte() {
        var router = GatewayRoutes.rutaContratada("test", "http://localhost", path -> true, 0);
        var request = ServerRequest.create(new MockHttpServletRequest("GET", "/api/v1/sin-contrato/recurso"), List.of());
        assertThat(router.route(request)).isEmpty();
    }

    @Test
    void aceptaOperacionCatalogadaConAlcanceCompatible() {
        var router = GatewayRoutes.rutaContratada("test", "http://localhost", path -> true, 0);
        var request = ServerRequest.create(new MockHttpServletRequest("POST", "/api/v1/auth/login"), List.of());
        assertThat(router.route(request)).isPresent();
    }

    @Test
    void rechazaOperacionCatalogadaFueraDelAlcance() {
        var router = GatewayRoutes.rutaContratada("test", "http://localhost", path -> false, 0);
        var request = ServerRequest.create(new MockHttpServletRequest("POST", "/api/v1/auth/login"), List.of());
        assertThat(router.route(request)).isEmpty();
    }
}
