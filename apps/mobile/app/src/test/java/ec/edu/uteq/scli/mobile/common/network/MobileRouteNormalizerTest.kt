package ec.edu.uteq.scli.mobile.common.network

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MobileRouteNormalizerTest {
    @Test
    fun `ignora query params sensibles`() {
        assertEquals(
            "/api/v1/solicitudes",
            MobileRouteNormalizer.normalize("/api/v1/solicitudes?token=secreto"),
        )
    }

    @Test
    fun `normaliza numeros y uuid como id`() {
        assertEquals(
            "/api/v1/incidentes/{id}/estado",
            MobileRouteNormalizer.normalize("/api/v1/incidentes/123/estado"),
        )
        assertEquals(
            "/api/v1/solicitudes/{id}/aprobar",
            MobileRouteNormalizer.normalize(
                "/api/v1/solicitudes/550e8400-e29b-41d4-a716-446655440000/aprobar",
            ),
        )
    }

    @Test
    fun `normaliza identificadores opacos largos`() {
        assertEquals(
            "/api/v1/notificaciones/{id}/leer",
            MobileRouteNormalizer.normalize("/api/v1/notificaciones/0123456789abcdef0123/leer"),
        )
    }

    @Test
    fun `usa unknown route si no reconoce la plantilla`() {
        assertEquals(
            MobileRouteNormalizer.UNKNOWN_ROUTE,
            MobileRouteNormalizer.normalize("/api/v1/no-catalogada/123"),
        )
    }

    @Test
    fun `excluye endpoint de metricas`() {
        assertNull(MobileRouteNormalizer.normalize(MobileRouteNormalizer.METRICS_ENDPOINT))
    }
}
