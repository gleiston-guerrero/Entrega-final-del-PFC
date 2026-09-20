package ec.edu.scli.reservas.observability;

import ec.edu.scli.reservas.presentation.dto.request.MobileHttpLatencyRequest;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import io.micrometer.prometheusmetrics.PrometheusConfig;
import io.micrometer.prometheusmetrics.PrometheusMeterRegistry;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class MobileHttpMetricsTest {

    @Test
    void registraTimerYCounterConTagsDeBajaCardinalidad() {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        MobileHttpMetrics metrics = new MobileHttpMetrics(registry);

        metrics.registrar(new MobileHttpLatencyRequest(
                "GET", "/api/v1/incidentes/{id}", 125L, 200, true));

        assertEquals(1, registry.get("app.mobile.http.latency")
                .tags("method", "GET", "route", "/api/v1/incidentes/{id}",
                        "status", "200", "outcome", "success")
                .timer()
                .count());
        assertEquals(125.0, registry.get("app.mobile.http.latency")
                .tags("method", "GET", "route", "/api/v1/incidentes/{id}",
                        "status", "200", "outcome", "success")
                .timer()
                .totalTime(java.util.concurrent.TimeUnit.MILLISECONDS));
        assertEquals(1.0, registry.get("app.mobile.http.requests")
                .tags("method", "GET", "route", "/api/v1/incidentes/{id}",
                        "status", "200", "outcome", "success")
                .counter()
                .count());
    }

    @Test
    void usaStatusIoErrorCuandoNoExisteCodigoHttp() {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        MobileHttpMetrics metrics = new MobileHttpMetrics(registry);

        metrics.registrar(new MobileHttpLatencyRequest(
                "GET", "UNKNOWN_ROUTE", 10L, null, false));

        assertEquals(1.0, registry.get("app.mobile.http.requests")
                .tags("method", "GET", "route", "UNKNOWN_ROUTE",
                        "status", "IO_ERROR", "outcome", "error")
                .counter()
                .count());
    }

    @Test
    void exportaNombresPrometheusEsperados() {
        PrometheusMeterRegistry registry =
                new PrometheusMeterRegistry(PrometheusConfig.DEFAULT);
        MobileHttpMetrics metrics = new MobileHttpMetrics(registry);

        metrics.registrar(new MobileHttpLatencyRequest(
                "POST", "/api/v1/solicitudes", 80L, 201, true));

        String scrape = registry.scrape();
        assertTrue(scrape.contains("app_mobile_http_latency_seconds_bucket"));
        assertTrue(scrape.contains("app_mobile_http_latency_seconds_count"));
        assertTrue(scrape.contains("app_mobile_http_latency_seconds_sum"));
        assertTrue(scrape.contains("app_mobile_http_requests_total"));
    }
}
