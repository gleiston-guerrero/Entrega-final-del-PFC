# Evidencia FCM extremo a extremo

**HEAD auditado:** `201346d5942b20969355dc7dfeba74692006eb5b`

**Estado:** VALIDACION E2E EJECUTADA CORRECTAMENTE.

## Cadena validada

1. Android obtiene el token FCM mediante `ScliFirebaseMessagingService`.
2. `DeviceTokenRegistrar` registra el dispositivo autenticado mediante `/api/v1/notificaciones/dispositivos`.
3. Reservas persiste el token por perfil y plataforma.
4. `NotificacionService` localiza los dispositivos activos asociados al perfil.
5. Con `FIREBASE_ENABLED=true`, `FirebaseNotificationAdapter` utiliza Firebase Admin SDK para realizar el envio.
6. El cambio de estado de un incidente genera una notificacion al perfil reportante.
7. La notificacion fue recibida correctamente en un dispositivo Android fisico.

## Validacion E2E realizada

**Fecha:** 2026-09-17

**Hora de recepción:** 02:58 (UTC-05:00)

**Entorno:** ejecucion local con servicios Docker y dispositivo Android fisico conectado al entorno de desarrollo.

**Proyecto Firebase:** cliente Android y backend fueron configurados con el mismo proyecto Firebase durante la validacion E2E; las credenciales y archivos sensibles permanecen fuera del control de versiones.

**Evento utilizado:** cambio de estado de incidente.

Se creo un incidente de prueba con estado inicial:

`REPORTADO`

Posteriormente se realizo la transicion valida:

`REPORTADO -> EN_REVISION`

El backend proceso correctamente el cambio de estado y el dispositivo recibio la notificacion:

**Titulo:** `Incidente actualizado`

**Mensaje:** `El incidente ahora esta EN_REVISION`

La prueba confirma el flujo completo:

`evento backend -> NotificacionService -> Firebase Admin SDK -> FCM -> dispositivo Android`

## Registro del dispositivo

Durante la validacion se confirmo que:

- el token FCM estaba presente en el dispositivo;
- el registro mediante `/api/v1/notificaciones/dispositivos` respondio correctamente;
- el dispositivo quedo persistido como plataforma `ANDROID` y activo en `dispositivos_notificacion`;
- no se versionaron tokens FCM, credenciales Firebase ni otros secretos.

## Evidencia visual

Permiso de notificaciones solicitado por la aplicacion Android:

`fcm-permiso-notificaciones-2026-09-17.png`

Recepcion real de la notificacion FCM en el dispositivo:

`fcm-e2e-2026-09-17.png`

La captura de recepcion muestra la notificacion **"Incidente actualizado"** con el mensaje **"El incidente ahora esta EN_REVISION"**.

## Manejo de secretos

`google-services.json`, las credenciales de Firebase Admin SDK y los tokens FCM permanecen fuera del control de versiones.

La configuracion sensible se proporciona unicamente mediante archivos ignorados por Git o variables de entorno.

## Resultado

La capacidad de notificaciones FCM queda validada extremo a extremo con un evento real y recepcion comprobada en un dispositivo Android fisico.
