package ec.edu.uteq.scli.mobile.features.observability.data

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import timber.log.Timber

interface MobileMetricsReporter {
    fun report(metric: MobileHttpLatencyMetric)
}

class DefaultMobileMetricsReporter(
    private val api: MobileMetricsApi,
    private val scope: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.IO),
) : MobileMetricsReporter {
    override fun report(metric: MobileHttpLatencyMetric) {
        scope.launch {
            runCatching { api.reportHttpLatency(metric) }
                .onFailure { Timber.tag("MobileMetrics").w(it, "No se pudo reportar latencia HTTP movil") }
        }
    }
}
