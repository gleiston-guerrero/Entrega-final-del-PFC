package ec.edu.scli.reservas.observability;

import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.HikariPoolMXBean;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import io.micrometer.prometheusmetrics.PrometheusConfig;
import io.micrometer.prometheusmetrics.PrometheusMeterRegistry;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class CrdbPoolActiveConnectionsMetricsTest {

    @Test
    void registraGaugeConConexionesActivasDelPoolHikari() {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        HikariPoolMXBean poolMxBean = mock(HikariPoolMXBean.class);
        HikariDataSource dataSource = mock(HikariDataSource.class);
        when(dataSource.getHikariPoolMXBean()).thenReturn(poolMxBean);
        when(poolMxBean.getActiveConnections()).thenReturn(3);

        new CrdbPoolActiveConnectionsMetrics(registry, dataSource);

        assertEquals(3.0, registry.get("crdb.pool.active.connections").gauge().value());
    }

    @Test
    void noFallaCuandoElMxBeanTodaviaNoEstaDisponible() {
        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        HikariDataSource dataSource = mock(HikariDataSource.class);
        when(dataSource.getHikariPoolMXBean()).thenReturn(null);

        new CrdbPoolActiveConnectionsMetrics(registry, dataSource);

        assertEquals(0.0, registry.get("crdb.pool.active.connections").gauge().value());
    }

    @Test
    void exportaNombrePrometheusRequerido() {
        PrometheusMeterRegistry registry =
                new PrometheusMeterRegistry(PrometheusConfig.DEFAULT);
        HikariPoolMXBean poolMxBean = mock(HikariPoolMXBean.class);
        HikariDataSource dataSource = mock(HikariDataSource.class);
        when(dataSource.getHikariPoolMXBean()).thenReturn(poolMxBean);
        when(poolMxBean.getActiveConnections()).thenReturn(2);

        new CrdbPoolActiveConnectionsMetrics(registry, dataSource);

        String scrape = registry.scrape();
        assertTrue(scrape.contains("crdb_pool_active_connections 2.0"));
    }
}
