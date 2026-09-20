package ec.edu.uteq.scli.mobile.common.di

import android.content.Context
import androidx.room.Room
import ec.edu.uteq.scli.mobile.data.local.AppDatabase
import ec.edu.uteq.scli.mobile.BuildConfig
import ec.edu.uteq.scli.mobile.common.network.BearerAuthInterceptor
import ec.edu.uteq.scli.mobile.common.network.GatewayClientFactory
import ec.edu.uteq.scli.mobile.common.network.MobileHttpLatencyInterceptor
import ec.edu.uteq.scli.mobile.common.network.RefreshAuthenticator
import ec.edu.uteq.scli.mobile.features.auth.data.AuthApi
import ec.edu.uteq.scli.mobile.features.auth.data.AuthRepository
import ec.edu.uteq.scli.mobile.features.auth.data.EncryptedAuthStorage
import ec.edu.uteq.scli.mobile.features.auth.data.RemoteAuthRepository
import ec.edu.uteq.scli.mobile.features.incidentes.data.IncidenteLocalRepository
import ec.edu.uteq.scli.mobile.features.incidentes.data.IncidentesApi
import ec.edu.uteq.scli.mobile.features.incidentes.data.RemoteIncidenteRepository
import ec.edu.uteq.scli.mobile.features.incidentes.domain.IncidenteRepository
import ec.edu.uteq.scli.mobile.features.institutional.data.InstitutionalApi
import ec.edu.uteq.scli.mobile.features.institutional.data.InstitutionalRepository
import ec.edu.uteq.scli.mobile.features.notifications.NotificationHelper
import ec.edu.uteq.scli.mobile.features.notifications.DeviceRegistrationApi
import ec.edu.uteq.scli.mobile.features.notifications.DeviceTokenRegistrar
import ec.edu.uteq.scli.mobile.features.notifications.PushNavigationManager
import ec.edu.uteq.scli.mobile.features.notifications.data.NotificationsApi
import ec.edu.uteq.scli.mobile.features.notifications.data.NotificationsRepository
import ec.edu.uteq.scli.mobile.features.observability.data.DefaultMobileMetricsReporter
import ec.edu.uteq.scli.mobile.features.observability.data.MobileMetricsApi
import ec.edu.uteq.scli.mobile.features.profile.data.SettingsRepository
import ec.edu.uteq.scli.mobile.features.profile.data.ProfileApi
import ec.edu.uteq.scli.mobile.features.profile.data.ProfileRepository
import ec.edu.uteq.scli.mobile.features.qr.data.RemoteQrRepository
import ec.edu.uteq.scli.mobile.features.qr.data.QrRepository
import ec.edu.uteq.scli.mobile.features.qr.data.QrApi
import ec.edu.uteq.scli.mobile.features.reservas.data.RemoteReservaRepository
import ec.edu.uteq.scli.mobile.features.reservas.data.remote.ReservasApi
import ec.edu.uteq.scli.mobile.features.reservas.data.remote.CatalogosApi
import ec.edu.uteq.scli.mobile.features.reservas.data.remote.CatalogosRepository
import ec.edu.uteq.scli.mobile.features.reservas.domain.ReservaRepository
import okhttp3.OkHttpClient

/**
 * Contenedor de dependencias manual (sin Hilt) para mantener el scaffold
 * simple. Se instancia una vez en [ec.edu.uteq.scli.mobile.ScliMobileApplication]
 * y se comparte desde ahí.
 */
class AppContainer(context: Context) {

    private val database: AppDatabase = Room.databaseBuilder(
        context.applicationContext,
        AppDatabase::class.java,
        "scli-mobile.db",
    ).addMigrations(AppDatabase.MIGRATION_1_2, AppDatabase.MIGRATION_2_3).build()

    val settingsRepository: SettingsRepository = SettingsRepository(context.applicationContext)
    val profileRepository: ProfileRepository by lazy {
        ProfileRepository(authenticatedGatewayRetrofit.create(ProfileApi::class.java))
    }

    val notificationHelper: NotificationHelper = NotificationHelper(context.applicationContext)

    private val authStorage = EncryptedAuthStorage(context.applicationContext)
    private val gatewayRetrofit = GatewayClientFactory.createRetrofit(BuildConfig.API_BASE_URL)
    val authRepository: AuthRepository = RemoteAuthRepository(
        gatewayRetrofit.create(AuthApi::class.java),
        authStorage,
    )
    private val mobileMetricsRetrofit = GatewayClientFactory.createRetrofit(
        BuildConfig.API_BASE_URL,
        OkHttpClient.Builder()
            .addInterceptor(BearerAuthInterceptor {
                authRepository.restoreSession()?.accessToken
            })
            .authenticator(RefreshAuthenticator(authRepository))
            .build(),
    )
    private val mobileMetricsReporter = DefaultMobileMetricsReporter(
        mobileMetricsRetrofit.create(MobileMetricsApi::class.java),
    )
    private val authenticatedGatewayRetrofit = GatewayClientFactory.createRetrofit(
        BuildConfig.API_BASE_URL,
        OkHttpClient.Builder()
            .addInterceptor(MobileHttpLatencyInterceptor(mobileMetricsReporter))
            .addInterceptor(BearerAuthInterceptor {
                authRepository.restoreSession()?.accessToken
            })
            .authenticator(RefreshAuthenticator(authRepository))
            .build(),
    )
    val incidenteRepository: IncidenteRepository = RemoteIncidenteRepository(
        authenticatedGatewayRetrofit.create(IncidentesApi::class.java), database.incidenteDao(),
    )
    private val reservasApi = authenticatedGatewayRetrofit.create(ReservasApi::class.java)
    val reservaRepository: ReservaRepository = RemoteReservaRepository(reservasApi, database.reservaDao())
    val catalogosRepository = CatalogosRepository(authenticatedGatewayRetrofit.create(CatalogosApi::class.java))
    val institutionalRepository = InstitutionalRepository(authenticatedGatewayRetrofit.create(InstitutionalApi::class.java))
    private val qrApi = authenticatedGatewayRetrofit.create(QrApi::class.java)
    val qrRepository: QrRepository = RemoteQrRepository(qrApi)
    val deviceTokenRegistrar = DeviceTokenRegistrar(
        context.applicationContext, authenticatedGatewayRetrofit.create(DeviceRegistrationApi::class.java),
    )
    private val notificationsApi = authenticatedGatewayRetrofit.create(NotificationsApi::class.java)
    val notificationsRepository: NotificationsRepository = NotificationsRepository(notificationsApi)
    val pushNavigationManager: PushNavigationManager = PushNavigationManager()

    init {
        authRepository.onAuthenticated { deviceTokenRegistrar.registrarPendiente() }
        authRepository.onBeforeLogout {
            deviceTokenRegistrar.desregistrarActual()
            pushNavigationManager.clear()
        }
    }
}
