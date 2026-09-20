package ec.edu.uteq.scli.mobile.common.network

import android.os.SystemClock
import ec.edu.uteq.scli.mobile.features.observability.data.MobileHttpLatencyMetric
import ec.edu.uteq.scli.mobile.features.observability.data.MobileMetricsReporter
import okhttp3.Interceptor
import okhttp3.Response
import java.util.concurrent.TimeUnit

class MobileHttpLatencyInterceptor(
    private val reporter: MobileMetricsReporter,
    private val nanoTime: () -> Long = { SystemClock.elapsedRealtimeNanos() },
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val route = MobileRouteNormalizer.normalize(request.url.encodedPath)
            ?: return chain.proceed(request)
        val startedAt = nanoTime()
        var status: Int? = null
        var success = false
        try {
            val response = chain.proceed(request)
            status = response.code
            success = response.isSuccessful
            return response
        } catch (exception: Exception) {
            success = false
            throw exception
        } finally {
            val elapsedNanos = (nanoTime() - startedAt).coerceAtLeast(0L)
            reporter.report(
                MobileHttpLatencyMetric(
                    method = request.method,
                    route = route,
                    durationMs = TimeUnit.NANOSECONDS.toMillis(elapsedNanos),
                    status = status,
                    success = success,
                ),
            )
        }
    }
}
