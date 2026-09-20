package ec.edu.uteq.scli.mobile.features.observability.data

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

data class MobileHttpLatencyMetric(
    val method: String,
    val route: String,
    val durationMs: Long,
    val status: Int?,
    val success: Boolean,
)

interface MobileMetricsApi {
    @POST("api/v1/observabilidad/mobile/http-latency")
    suspend fun reportHttpLatency(@Body metric: MobileHttpLatencyMetric): Response<Unit>
}
