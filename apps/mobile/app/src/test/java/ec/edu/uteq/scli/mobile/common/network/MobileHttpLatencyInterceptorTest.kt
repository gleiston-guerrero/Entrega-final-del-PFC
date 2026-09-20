package ec.edu.uteq.scli.mobile.common.network

import ec.edu.uteq.scli.mobile.features.observability.data.MobileHttpLatencyMetric
import ec.edu.uteq.scli.mobile.features.observability.data.MobileMetricsReporter
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class MobileHttpLatencyInterceptorTest {
    private lateinit var server: MockWebServer

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    @Test
    fun `mide duracion con reloj monotonico alrededor de chain proceed`() {
        server.enqueue(MockResponse().setResponseCode(204))
        val reporter = CapturingReporter()
        val times = mutableListOf(1_000_000_000L, 1_125_000_000L)
        val client = OkHttpClient.Builder()
            .addInterceptor(MobileHttpLatencyInterceptor(reporter) { times.removeAt(0) })
            .build()

        client.newCall(Request.Builder().url(server.url("/api/v1/incidentes")).build())
            .execute().use { response -> assertEquals(204, response.code) }

        assertEquals(1, reporter.metrics.size)
        assertEquals(125L, reporter.metrics.single().durationMs)
        assertEquals("GET", reporter.metrics.single().method)
        assertEquals("/api/v1/incidentes", reporter.metrics.single().route)
        assertEquals(204, reporter.metrics.single().status)
        assertTrue(reporter.metrics.single().success)
    }

    @Test
    fun `no reporta el endpoint de metricas para evitar recursion`() {
        server.enqueue(MockResponse().setResponseCode(202))
        val reporter = CapturingReporter()
        val client = OkHttpClient.Builder()
            .addInterceptor(MobileHttpLatencyInterceptor(reporter))
            .build()

        client.newCall(Request.Builder().url(server.url(MobileRouteNormalizer.METRICS_ENDPOINT)).build())
            .execute().use { response -> assertEquals(202, response.code) }

        assertEquals(0, reporter.metrics.size)
    }

    private class CapturingReporter : MobileMetricsReporter {
        val metrics = mutableListOf<MobileHttpLatencyMetric>()
        override fun report(metric: MobileHttpLatencyMetric) {
            metrics += metric
        }
    }
}
