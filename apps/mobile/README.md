# apps/mobile

App Android (Kotlin + Jetpack Compose), arquitectura MVVM + repositorio por feature.

- `minSdk`: 26
- `targetSdk` / `compileSdk`: 34
- El Gateway se configura con `SCLI_API_BASE_URL` como propiedad Gradle
  o variable de entorno (barra final obligatoria). Debug usa por defecto
  `http://10.0.2.2:8080/`; release exige una URL explícita, sin fallback.

## Wrapper de Gradle

El repositorio incluye `gradlew`, `gradlew.bat`,
`gradle/wrapper/gradle-wrapper.properties` y `gradle-wrapper.jar` (Gradle 8.13).
No es necesario disponer de una instalación global de Gradle.

## Estructura

```
common/
  di/            AppContainer: DI manual (sin Hilt) instanciado en ScliMobileApplication
  logging/       Timber + JsonTree (logs en JSON con trace_id de sesión)
   navigation/    NavHost + bottom navigation, protegido por autenticación

data/local/      AppDatabase (Room)

features/
   auth/          login contra el Gateway + sesión en EncryptedSharedPreferences
  incidentes/    domain (modelo + interfaz de repositorio), data (Room),
                 presentation (ViewModel + pantalla con listado y formulario)
  notifications/ FirebaseMessagingService, canal de notificaciones,
                 solicitud de permiso POST_NOTIFICATIONS
  profile/       perfil del técnico + settings, persistido con DataStore
```

`IncidenteRepository` es una interfaz; hoy la única implementación es
`IncidenteLocalRepository` (Room). El día que se agregue una fuente remota
(Retrofit) — o una estrategia combinada local+remota — se implementa detrás de
esa misma interfaz sin tocar el ViewModel ni la UI.

## Notificaciones push (Firebase) — validación E2E realizada

El cliente Android recibe mensajes, presenta notificaciones y registra el token
en el backend cuando existe una sesión autenticada. Reservas persiste esos
dispositivos y usa el adaptador Firebase para enviar notificaciones mediante
Firebase Admin SDK.

La cadena FCM fue validada extremo a extremo con el cliente Android y el backend
configurados con el mismo proyecto Firebase durante la prueba. La validación se
ejecutó con un dispositivo Android físico y un evento real de cambio de estado
de incidente.

El flujo validado fue:

`evento backend -> NotificacionService -> Firebase Admin SDK -> FCM -> dispositivo Android`

La evidencia está versionada en
`docs/evidencias/fcm-e2e-2026-09-20.md` e incluye las capturas de recepción real
de la notificación FCM en el dispositivo y en la pantalla interna de SCLI. En la
misma validación se documentó que un token antiguo devolvió `UNREGISTERED`, sin
invalidar el envío exitoso al dispositivo actual.

`google-services.json`, las credenciales de Firebase Admin SDK y los tokens FCM
permanecen fuera del repositorio. Las variables sensibles siguen
proporcionándose mediante archivos ignorados por Git o variables de entorno.

## Settings del técnico

Se guardan con Jetpack DataStore (Preferences), no con `SharedPreferences`:
nombre del técnico y el toggle de notificaciones habilitadas.

## Tests

- Unitarios/Robolectric (`src/test` y `src/testDebug`): ViewModels, repositorios,
  autenticación/refresh, mapeos, notificaciones y UI Compose.
- Instrumentados (`src/androidTest`): flujos de reservas, incidentes y QR, Room en
  memoria y migración de la base local.

CI ejecuta `testDebugUnitTest`, el reporte JaCoCo, Android lint y
`connectedDebugAndroidTest` en un emulador API 29. El APK debug se publica como
artefacto únicamente después de superar esos gates.

## APK release firmado

Las tareas release exigen `SCLI_API_BASE_URL`, `SCLI_VERSION_NAME` y
`SCLI_VERSION_CODE`, mediante propiedades Gradle o variables de entorno.
No se necesita configurar esos valores para pruebas debug:

```powershell
.\gradlew.bat testDebugUnitTest lint
```

Una compilación `assembleRelease` con los valores requeridos deja el resultado
sin firma en:

```text
app/build/outputs/apk/release/app-release-unsigned.apk
```

La firma de publicacion se realiza en GitHub Actions para pushes, segun el
workflow vigente, cuando esten configurados estos secrets del repositorio:

- `ANDROID_SIGNING_KEYSTORE_BASE64`
- `ANDROID_SIGNING_STORE_PASSWORD`
- `ANDROID_SIGNING_KEY_ALIAS`
- `ANDROID_SIGNING_KEY_PASSWORD`

CI reconstruye temporalmente el keystore dentro de `$RUNNER_TEMP`, alinea el APK
con `zipalign`, firma con `apksigner` y verifica la firma y el certificado con
`apksigner verify --verbose --print-certs`. Despues genera y comprueba
`SHA256SUMS.txt`. La release histórica verificada correspondiente al punto #35 fue
publicada por GitHub Actions como `v1.0.1`, asociada al commit etiquetado
`166a2c4c48f1f6dfebc3ef087652d60b9f7ed3a8`, y contiene:

```text
scli-mobile-v1.0.1-release.apk
SHA256SUMS.txt
SCLI-PFC-v1.0.1.pdf
Source code (zip)
Source code (tar.gz)
```

El SHA-256 verificado de `scli-mobile-v1.0.1-release.apk` es
`a6504201aa9d7aaf16299c6417ff33d8f1b42f129508ce708335b859dd454ad8` y coincide
con `SHA256SUMS.txt`. `apksigner` valido APK Signature Scheme v2 y v3, con un
firmante RSA de 2048 bits y certificado `CN=scli, OU=uteq, O=uteq, L=Quevedo,
ST=Los Rios, C=EC`. La evidencia se resume en
`release/apk/VERIFICACION-v1.0.1.md`.

Como evidencia historica, para el SHA fuente
`0b755310a0acf34da2456290a4f978475a8e17f9`, el job
`Build - Android release signed` termino con estado `completed/success`. El
artifact `scli-mobile-release-0b755310a0acf34da2456290a4f978475a8e17f9` fue
generado, firmado y verificado correctamente en GitHub Actions, dentro del run
de CI `34688947156`. Esa evidencia corresponde al APK historico
`release/apk/scli-mobile-0.1.0-release.apk`, con su checksum en
`release/apk/SHA256SUMS.txt`. Actions
continua siendo la fuente reproducible del proceso. El identificador del paquete
es `ec.edu.uteq.scli.mobile`.

Para instalar el APK oficial publicado y comprobar su `applicationId`:

```bash
adb install -r scli-mobile-v1.0.1-release.apk
adb shell pm list packages ec.edu.uteq.scli.mobile
```

El keystore privado y las contraseñas de firma nunca se suben a Git. Debe
conservarse cifrado y respaldado
en una ubicación externa controlada por el equipo: perderlo impediría firmar
futuras actualizaciones con la misma identidad.

### Configuración reproducible del criterio #35

CI obtiene el backend de la GitHub Actions Repository Variable
`SCLI_RELEASE_API_BASE_URL` y lo pasa a Gradle como `SCLI_API_BASE_URL`.
Debe ser una URL `http://` o `https://`, con hostname y barra final, sin
credenciales, query ni fragmento. No hay backend release fijo en el código.
`SCLI_VERSION_NAME` se deriva de `vX.Y.Z` como `X.Y.Z`; en pushes sin tag usa
`0.0.0-dev.<run>.<SHA corto>`. `SCLI_VERSION_CODE` usa `github.run_number`,
validado como entero entre 1 y 2100000000. Gradle rechaza tareas release si
faltan estos valores. Tras firmar, `aapt dump badging` compara las versiones
internas del APK con las entradas de CI y falla ante cualquier diferencia.

La política general de red bloquea cleartext. Si `SCLI_RELEASE_API_BASE_URL`
usa HTTP, CI genera temporalmente un recurso exclusivo de release con una
excepción limitada al hostname configurado, sin incluir subdominios; HTTPS no
habilita cleartext. Debug tiene una excepción propia limitada a `10.0.2.2`.
HTTP no proporciona confidencialidad ni autenticidad de transporte:
credenciales y tokens pueden ser interceptados o manipulados en una red hostil.
Esta excepción corresponde únicamente al entorno académico/demostrativo actual.
Un despliegue de producción debe utilizar HTTPS/TLS y retirar la excepción
cleartext.

El PDF recibe el tag y SHA mediante `SCLIReleaseVersion` y `SCLIReleaseCommit`,
inicializados por una entrada LaTeX temporal de CI, con valores locales por
defecto. La publicación verifica la suma original del APK firmado, reúne
`scli-mobile-vX.Y.Z-release.apk` y `SCLI-PFC-vX.Y.Z.pdf` en una carpeta final y
genera allí `SHA256SUMS.txt` con exactamente dos entradas de nombre base.
Los tres assets descargados juntos se validan con
`sha256sum --check SHA256SUMS.txt`. Antes de publicar, CI obtiene la historia
completa, resuelve el commit real del tag (incluidos tags anotados) y exige
`git merge-base --is-ancestor <commit> origin/main`. Se mantienen los gates de
firma, Firebase obligatorio, imágenes, manifiestos, contratos y documentación;
la publicación se limita a `refs/tags/v*`. Las referencias a `v1.0.1` anteriores
son evidencia histórica, no la versión de futuras releases.
