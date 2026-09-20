package ec.edu.scli.reservas.presentation.dto.request;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.PositiveOrZero;

public record MobileHttpLatencyRequest(
        @NotBlank
        @Pattern(regexp = "GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS")
        String method,

        @NotBlank
        String route,

        @NotNull
        @PositiveOrZero
        Long durationMs,

        @Min(100)
        @Max(599)
        Integer status,

        @NotNull
        Boolean success
) {
}
