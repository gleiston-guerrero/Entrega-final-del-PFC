package ec.edu.uteq.scli.mobile.common.network

object MobileRouteNormalizer {
    const val METRICS_ENDPOINT = "/api/v1/observabilidad/mobile/http-latency"
    const val UNKNOWN_ROUTE = "UNKNOWN_ROUTE"

    private val uuid = Regex(
        "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
    )
    private val numeric = Regex("^\\d+$")
    private val longHex = Regex("^[0-9a-fA-F]{16,}$")
    private val longOpaque = Regex("^[A-Za-z0-9_]{20,}$")

    private val knownRoutes = setOf(
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/forgot-password",
        "/api/v1/perfiles",
        "/api/v1/perfiles/me",
        "/api/v1/docentes",
        "/api/v1/docentes/planificacion",
        "/api/v1/docentes/perfil/{id}",
        "/api/v1/estudiantes/mi-contexto",
        "/api/v1/estudiantes/mis-contextos",
        "/api/v1/horarios/docente/{id}",
        "/api/v1/asistencias/mi-horario",
        "/api/v1/asistencias/mi-horario-docente",
        "/api/v1/asistencias/historial",
        "/api/v1/asistencias/sesiones",
        "/api/v1/asistencias/sesiones/abiertas",
        "/api/v1/asistencias/sesiones/{id}",
        "/api/v1/asistencias/sesiones/{id}/cerrar",
        "/api/v1/asistencias/sesiones/{id}/registros",
        "/api/v1/asistencias/sesiones/{id}/registro-propio",
        "/api/v1/planificaciones",
        "/api/v1/planificaciones/{id}",
        "/api/v1/planificaciones/{id}/aceptar",
        "/api/v1/planificaciones/{id}/rechazar",
        "/api/v1/planificaciones/{id}/proponer-alternativa",
        "/api/v1/planificaciones/{id}/aceptar-propuesta",
        "/api/v1/planificaciones-agregadas",
        "/api/v1/planificaciones-agregadas/disponibilidad",
        "/api/v1/planificaciones-agregadas/{id}/revisiones/mi-piso/aprobar",
        "/api/v1/planificaciones-agregadas/{id}/revisiones/mi-piso/rechazar",
        "/api/v1/planificaciones-agregadas/{id}/revisiones/mi-piso/proponer-cambio",
        "/api/v1/materias",
        "/api/v1/laboratorios",
        "/api/v1/laboratorios/{id}/detalle-completo",
        "/api/v1/carreras",
        "/api/v1/pisos",
        "/api/v1/periodos-lectivos",
        "/api/v1/periodos-lectivos/actual",
        "/api/v1/incidentes",
        "/api/v1/incidentes/{id}",
        "/api/v1/incidentes/{id}/estado",
        "/api/v1/notificaciones",
        "/api/v1/notificaciones/no-leidas",
        "/api/v1/notificaciones/{id}/leer",
        "/api/v1/notificaciones/leer-todas",
        "/api/v1/notificaciones/dispositivos",
        "/api/v1/reservas",
        "/api/v1/reservas/{id}",
        "/api/v1/reservas/{id}/cancelar",
        "/api/v1/reservas/{id}/iniciar",
        "/api/v1/reservas/{id}/finalizar",
        "/api/v1/solicitudes",
        "/api/v1/solicitudes/{id}",
        "/api/v1/solicitudes/{id}/historial",
        "/api/v1/solicitudes/{id}/revision",
        "/api/v1/solicitudes/{id}/aprobar",
        "/api/v1/solicitudes/{id}/rechazar",
        "/api/v1/solicitudes/{id}/cancelar",
        "/api/v1/solicitudes/{id}/propuesta",
        "/api/v1/solicitudes/{id}/propuesta/aceptar",
        "/api/v1/solicitudes/{id}/propuesta/rechazar",
        "/api/v1/disponibilidad/laboratorios/{id}",
    )

    fun normalize(encodedPath: String): String? {
        val path = encodedPath.substringBefore('?').ifBlank { "/" }
        if (path == METRICS_ENDPOINT) return null
        val normalized = path.split('/')
            .filter { it.isNotBlank() }
            .joinToString(prefix = "/", separator = "/") { segment ->
                if (isDynamicIdentifier(segment)) "{id}" else segment
            }
        return normalized.takeIf { it in knownRoutes } ?: UNKNOWN_ROUTE
    }

    private fun isDynamicIdentifier(segment: String): Boolean =
        uuid.matches(segment) ||
            numeric.matches(segment) ||
            longHex.matches(segment) ||
            longOpaque.matches(segment)
}
