package ec.edu.scli.reservas.presentation.controller;

import ec.edu.scli.reservas.observability.MobileHttpMetrics;
import ec.edu.scli.reservas.presentation.dto.request.MobileHttpLatencyRequest;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/observabilidad/mobile")
public class ObservabilidadMobileController {
    private final MobileHttpMetrics metrics;

    public ObservabilidadMobileController(MobileHttpMetrics metrics) {
        this.metrics = metrics;
    }

    @PostMapping("/http-latency")
    public ResponseEntity<Void> registrarLatenciaHttp(
            @Valid @RequestBody MobileHttpLatencyRequest request) {
        metrics.registrar(request);
        return ResponseEntity.accepted().build();
    }
}
