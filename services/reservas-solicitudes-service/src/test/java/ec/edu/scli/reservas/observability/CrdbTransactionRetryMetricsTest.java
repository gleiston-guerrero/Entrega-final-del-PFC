package ec.edu.scli.reservas.observability;

import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.dao.CannotAcquireLockException;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.EnableRetry;
import org.springframework.retry.annotation.Retryable;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.test.util.AopTestUtils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

@SpringJUnitConfig(CrdbTransactionRetryMetricsTest.TestConfig.class)
class CrdbTransactionRetryMetricsTest {

    private final SimpleMeterRegistry meterRegistry;
    private final RetryProbe retryProbe;
    private double initialRetries;

    @Autowired
    CrdbTransactionRetryMetricsTest(SimpleMeterRegistry meterRegistry, RetryProbe retryProbe) {
        this.meterRegistry = meterRegistry;
        this.retryProbe = retryProbe;
    }

    @BeforeEach
    void reset() throws Exception {
        target().reset();
        initialRetries = retries();
    }

    @Test
    void noIncrementaCuandoNoHayRetry() throws Exception {
        retryProbe.succeed();

        assertEquals(0.0, retriesDelta());
        assertEquals(1, target().attempts());
    }

    @Test
    void incrementaUnaVezPorCadaRetryReal() throws Exception {
        retryProbe.failTwiceThenSucceed();

        assertEquals(2.0, retriesDelta());
        assertEquals(3, target().attempts());
    }

    @Test
    void noIncrementaParaFalloNoRetryable() throws Exception {
        assertThrows(IllegalArgumentException.class, retryProbe::failWithNonRetryableException);

        assertEquals(0.0, retriesDelta());
        assertEquals(1, target().attempts());
    }

    private double retries() {
        return meterRegistry.find(CrdbTransactionRetryMetrics.METRIC_NAME)
                .counter()
                .count();
    }

    private double retriesDelta() {
        return retries() - initialRetries;
    }

    private RetryProbe target() throws Exception {
        return AopTestUtils.getTargetObject(retryProbe);
    }

    interface RetryProbe {
        void succeed();

        void failTwiceThenSucceed();

        void failWithNonRetryableException();

        void reset();

        int attempts();
    }

    static class RetryProbeImpl implements RetryProbe {

        private int attempts;

        @Override
        @Retryable(
                retryFor = CannotAcquireLockException.class,
                maxAttempts = 3,
                backoff = @Backoff(delay = 1, maxDelay = 1))
        public void succeed() {
            attempts++;
        }

        @Override
        @Retryable(
                retryFor = CannotAcquireLockException.class,
                maxAttempts = 3,
                backoff = @Backoff(delay = 1, maxDelay = 1))
        public void failTwiceThenSucceed() {
            attempts++;
            if (attempts < 3) {
                throw new CannotAcquireLockException("retryable conflict");
            }
        }

        @Override
        @Retryable(
                retryFor = CannotAcquireLockException.class,
                maxAttempts = 3,
                backoff = @Backoff(delay = 1, maxDelay = 1))
        public void failWithNonRetryableException() {
            attempts++;
            throw new IllegalArgumentException("not retryable");
        }

        @Override
        public void reset() {
            attempts = 0;
        }

        @Override
        public int attempts() {
            return attempts;
        }
    }

    @Configuration
    @EnableRetry
    static class TestConfig {

        @Bean
        SimpleMeterRegistry meterRegistry() {
            return new SimpleMeterRegistry();
        }

        @Bean
        CrdbTransactionRetryMetrics crdbTransactionRetryMetrics(SimpleMeterRegistry meterRegistry) {
            return new CrdbTransactionRetryMetrics(meterRegistry);
        }

        @Bean
        RetryProbe retryProbe() {
            return new RetryProbeImpl();
        }
    }
}
