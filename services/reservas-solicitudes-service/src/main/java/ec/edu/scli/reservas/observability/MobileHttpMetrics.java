package ec.edu.scli.reservas.observability;

import ec.edu.scli.reservas.presentation.dto.request.MobileHttpLatencyRequest;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.stereotype.Component;

import java.time.Duration;

@Component
public class MobileHttpMetrics {
    static final String LATENCY_METRIC = "app.mobile.http.latency";
    static final String REQUESTS_METRIC = "app.mobile.http.requests";

    private final MeterRegistry meterRegistry;

    public MobileHttpMetrics(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    public void registrar(MobileHttpLatencyRequest request) {
        String method = request.method();
        String route = request.route();
        String status = request.status() == null ? "IO_ERROR" : request.status().toString();
        String outcome = Boolean.TRUE.equals(request.success()) ? "success" : "error";

        Timer.builder(LATENCY_METRIC)
                .description("Latencia HTTP E2E medida desde la aplicacion movil")
                .publishPercentileHistogram()
                .tag("method", method)
                .tag("route", route)
                .tag("status", status)
                .tag("outcome", outcome)
                .register(meterRegistry)
                .record(Duration.ofMillis(request.durationMs()));

        meterRegistry.counter(
                REQUESTS_METRIC,
                "method", method,
                "route", route,
                "status", status,
                "outcome", outcome
        ).increment();
    }
}
