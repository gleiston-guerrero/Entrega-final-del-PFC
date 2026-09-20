package ec.edu.scli.reservas.observability;

import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.HikariPoolMXBean;
import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Component;

@Component
public class CrdbPoolActiveConnectionsMetrics {
    static final String METRIC_NAME = "crdb.pool.active.connections";

    public CrdbPoolActiveConnectionsMetrics(
            MeterRegistry meterRegistry,
            HikariDataSource dataSource
    ) {
        Gauge.builder(METRIC_NAME, dataSource, CrdbPoolActiveConnectionsMetrics::activeConnections)
                .description("Conexiones activas del pool Hikari hacia CockroachDB")
                .register(meterRegistry);
    }

    private static double activeConnections(HikariDataSource dataSource) {
        HikariPoolMXBean poolMxBean = dataSource.getHikariPoolMXBean();
        if (poolMxBean == null) {
            return 0.0;
        }
        return poolMxBean.getActiveConnections();
    }
}
