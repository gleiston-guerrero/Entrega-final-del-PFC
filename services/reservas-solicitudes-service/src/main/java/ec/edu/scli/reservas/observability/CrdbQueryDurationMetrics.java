package ec.edu.scli.reservas.observability;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.Locale;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.TimeUnit;

@Component
public class CrdbQueryDurationMetrics {
    static final String METRIC_NAME = "crdb.query.duration";
    static final String COMPONENT_TAG = "jdbc";

    private static final String OPERATION_SELECT = "select";
    private static final String OPERATION_INSERT = "insert";
    private static final String OPERATION_UPDATE = "update";
    private static final String OPERATION_DELETE = "delete";
    private static final String OPERATION_OTHER = "other";

    private static final Duration[] BUCKETS = {
            Duration.ofMillis(1),
            Duration.ofMillis(5),
            Duration.ofMillis(10),
            Duration.ofMillis(25),
            Duration.ofMillis(50),
            Duration.ofMillis(100),
            Duration.ofMillis(250),
            Duration.ofMillis(500),
            Duration.ofSeconds(1),
            Duration.ofSeconds(2),
            Duration.ofSeconds(5)
    };

    private final MeterRegistry meterRegistry;
    private final ConcurrentMap<String, Timer> timers = new ConcurrentHashMap<>();

    public CrdbQueryDurationMetrics(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
    }

    void record(String sql, long durationNanos) {
        timer(operation(sql)).record(durationNanos, TimeUnit.NANOSECONDS);
    }

    String operation(String sql) {
        if (sql == null || sql.isBlank()) {
            return OPERATION_OTHER;
        }

        String normalized = sql.stripLeading().toLowerCase(Locale.ROOT);
        if (normalized.startsWith(OPERATION_SELECT) || normalized.startsWith("with ")) {
            return OPERATION_SELECT;
        }
        if (normalized.startsWith(OPERATION_INSERT)) {
            return OPERATION_INSERT;
        }
        if (normalized.startsWith(OPERATION_UPDATE)) {
            return OPERATION_UPDATE;
        }
        if (normalized.startsWith(OPERATION_DELETE)) {
            return OPERATION_DELETE;
        }
        return OPERATION_OTHER;
    }

    private Timer timer(String operation) {
        return timers.computeIfAbsent(operation, this::newTimer);
    }

    private Timer newTimer(String operation) {
        return Timer.builder(METRIC_NAME)
                .description("Duracion de ejecucion de consultas JDBC hacia CockroachDB")
                .tag("operation", operation)
                .tag("component", COMPONENT_TAG)
                .publishPercentileHistogram()
                .serviceLevelObjectives(BUCKETS)
                .register(meterRegistry);
    }
}
