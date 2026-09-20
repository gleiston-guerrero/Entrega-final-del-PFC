package ec.edu.uteq.scli.mobile.features.observability.data

import ec.edu.uteq.scli.mobile.common.network.GatewayClientFactory
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import okhttp3.OkHttpClient
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test

class MobileMetricsReporterTest {
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
    fun `reporta por cliente separado sin interceptor de latencia`() = runTest {
        server.enqueue(MockResponse().setResponseCode(202))
        val api = GatewayClientFactory.createRetrofit(
            server.url("/").toString(),
            OkHttpClient.Builder().build(),
        ).create(MobileMetricsApi::class.java)
        val reporter = DefaultMobileMetricsReporter(api, TestScope(testScheduler))

        reporter.report(MobileHttpLatencyMetric("GET", "/api/v1/incidentes", 12, 200, true))
        advanceUntilIdle()

        val request = server.takeRequest()
        assertEquals("/api/v1/observabilidad/mobile/http-latency", request.path)
        assertEquals("POST", request.method)
    }
}
