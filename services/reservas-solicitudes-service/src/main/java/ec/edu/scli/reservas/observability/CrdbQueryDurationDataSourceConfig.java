package ec.edu.scli.reservas.observability;

import com.zaxxer.hikari.HikariDataSource;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import javax.sql.DataSource;

@Configuration(proxyBeanMethods = false)
public class CrdbQueryDurationDataSourceConfig {

    @Bean
    @ConfigurationProperties("spring.datasource.hikari")
    HikariDataSource crdbHikariDataSource(DataSourceProperties properties) {
        return properties.initializeDataSourceBuilder()
                .type(HikariDataSource.class)
                .build();
    }

    @Bean
    @Primary
    DataSource crdbQueryDurationDataSource(
            HikariDataSource crdbHikariDataSource,
            CrdbQueryDurationMetrics metrics
    ) {
        return new CrdbQueryDurationDataSource(crdbHikariDataSource, metrics);
    }
}
