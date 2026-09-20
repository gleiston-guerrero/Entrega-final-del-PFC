package ec.edu.scli.reservas.observability;

import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.dao.CannotAcquireLockException;
import org.springframework.dao.PessimisticLockingFailureException;
import org.springframework.orm.ObjectOptimisticLockingFailureException;
import org.springframework.retry.RetryCallback;
import org.springframework.retry.RetryContext;
import org.springframework.retry.RetryListener;
import org.springframework.retry.policy.SimpleRetryPolicy;
import org.springframework.stereotype.Component;

import java.util.Set;

@Component
public class CrdbTransactionRetryMetrics implements RetryListener {

    static final String METRIC_NAME = "crdb.transaction.retries";

    private static final Set<Class<? extends Throwable>> CRDB_RETRYABLE_EXCEPTIONS = Set.of(
            CannotAcquireLockException.class,
            PessimisticLockingFailureException.class,
            ObjectOptimisticLockingFailureException.class
    );

    private final Counter retries;

    public CrdbTransactionRetryMetrics(MeterRegistry meterRegistry) {
        this.retries = Counter.builder(METRIC_NAME)
                .description("CockroachDB transactional retries triggered by Spring Retry")
                .register(meterRegistry);
    }

    @Override
    public <T, E extends Throwable> void onError(
            RetryContext context,
            RetryCallback<T, E> callback,
            Throwable throwable) {
        if (willRetry(context, throwable)) {
            retries.increment();
        }
    }

    private boolean willRetry(RetryContext context, Throwable throwable) {
        return isCrdbRetryable(throwable)
                && !context.isExhaustedOnly()
                && context.getRetryCount() < maxAttempts(context);
    }

    private boolean isCrdbRetryable(Throwable throwable) {
        return CRDB_RETRYABLE_EXCEPTIONS.stream()
                .anyMatch(exceptionType -> exceptionType.isInstance(throwable));
    }

    private int maxAttempts(RetryContext context) {
        Object value = context.getAttribute(RetryContext.MAX_ATTEMPTS);
        if (value instanceof Number attempts) {
            return attempts.intValue();
        }
        return SimpleRetryPolicy.DEFAULT_MAX_ATTEMPTS;
    }
}
