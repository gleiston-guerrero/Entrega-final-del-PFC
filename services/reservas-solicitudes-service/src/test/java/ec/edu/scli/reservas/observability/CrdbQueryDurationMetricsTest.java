package ec.edu.scli.reservas.observability;

import io.micrometer.core.instrument.Timer;
import io.micrometer.prometheusmetrics.PrometheusConfig;
import io.micrometer.prometheusmetrics.PrometheusMeterRegistry;
import org.h2.jdbcx.JdbcDataSource;
import org.junit.jupiter.api.Test;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class CrdbQueryDurationMetricsTest {

    @Test
    void registraTimerConDuracionPositivaParaOperacionJdbcInstrumentada() throws Exception {
        PrometheusMeterRegistry registry = new PrometheusMeterRegistry(PrometheusConfig.DEFAULT);
        DataSource dataSource = instrumentedDataSource(registry);

        try (Connection connection = dataSource.getConnection();
             Statement statement = connection.createStatement()) {
            statement.execute("create table reservas_metric_test (id int primary key, nombre varchar(40))");
            statement.executeUpdate("insert into reservas_metric_test (id, nombre) values (1, 'laboratorio')");
            statement.executeQuery("select nombre from reservas_metric_test where id = 1").close();
        }

        Timer timer = registry.find("crdb.query.duration")
                .tag("operation", "select")
                .tag("component", "jdbc")
                .timer();

        assertNotNull(timer);
        assertTrue(timer.count() > 0);
        assertTrue(timer.totalTime(TimeUnit.NANOSECONDS) > 0);
    }

    @Test
    void exportaHistogramBucketsParaPrometheus() throws Exception {
        PrometheusMeterRegistry registry = new PrometheusMeterRegistry(PrometheusConfig.DEFAULT);
        DataSource dataSource = instrumentedDataSource(registry);

        try (Connection connection = dataSource.getConnection();
             Statement statement = connection.createStatement()) {
            statement.execute("select 1");
        }

        String scrape = registry.scrape();

        assertTrue(scrape.contains("crdb_query_duration_seconds_bucket"));
        assertTrue(scrape.contains("crdb_query_duration_seconds_count"));
        assertTrue(scrape.contains("crdb_query_duration_seconds_sum"));
    }

    @Test
    void noUsaSqlNiParametrosSensiblesComoTags() throws Exception {
        PrometheusMeterRegistry registry = new PrometheusMeterRegistry(PrometheusConfig.DEFAULT);
        DataSource dataSource = instrumentedDataSource(registry);

        try (Connection connection = dataSource.getConnection();
             Statement statement = connection.createStatement()) {
            statement.execute("create table crdb_sensitive_metric_test (id int primary key, token varchar(80))");
        }
        try (Connection connection = dataSource.getConnection();
             PreparedStatement statement = connection.prepareStatement(
                     "insert into crdb_sensitive_metric_test (id, token) values (?, ?)")) {
            statement.setInt(1, 1);
            statement.setString(2, "jwt-valor-sensible-123");
            statement.executeUpdate();
        }

        String scrape = registry.scrape();

        assertFalse(scrape.contains("crdb_sensitive_metric_test"));
        assertFalse(scrape.contains("jwt-valor-sensible-123"));
        assertTrue(scrape.contains("component=\"jdbc\""));
        assertTrue(scrape.contains("operation=\"insert\""));
    }

    @Test
    void clasificaOperacionesConTagsDeBajaCardinalidad() {
        CrdbQueryDurationMetrics metrics =
                new CrdbQueryDurationMetrics(new PrometheusMeterRegistry(PrometheusConfig.DEFAULT));

        assertTrue("select".equals(metrics.operation("select * from reservas")));
        assertTrue("select".equals(metrics.operation("with datos as (select 1) select * from datos")));
        assertTrue("insert".equals(metrics.operation("insert into reservas values (1)")));
        assertTrue("update".equals(metrics.operation("update reservas set estado = 'A'")));
        assertTrue("delete".equals(metrics.operation("delete from reservas")));
        assertTrue("other".equals(metrics.operation("create table reservas (id int)")));
    }

    private static DataSource instrumentedDataSource(PrometheusMeterRegistry registry) {
        JdbcDataSource delegate = new JdbcDataSource();
        delegate.setURL("jdbc:h2:mem:" + System.nanoTime() + ";MODE=PostgreSQL;DB_CLOSE_DELAY=-1");
        delegate.setUser("sa");
        delegate.setPassword("");
        return new CrdbQueryDurationDataSource(delegate, new CrdbQueryDurationMetrics(registry));
    }
}
