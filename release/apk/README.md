# APK release firmado

Los APK release firmados se generan, firman, verifican y publican mediante
GitHub Actions. La release oficial verificada correspondiente al punto #35 es
`v1.0.1`, asociada al commit etiquetado
`166a2c4c48f1f6dfebc3ef087652d60b9f7ed3a8`. El APK publicado como asset de la
GitHub Release es `scli-mobile-v1.0.1-release.apk`; no se copia en este
directorio para evitar versionar el binario de 35 MB mientras permanece
disponible como asset oficial. Las claves privadas y contrasenas de firma no se
almacenan en Git.

El SHA-256 verificado del APK publicado es:

```text
a6504201aa9d7aaf16299c6417ff33d8f1b42f129508ce708335b859dd454ad8
```

Ese hash coincide exactamente con el contenido publicado en `SHA256SUMS.txt`.
La validacion con `apksigner` confirma firma valida mediante APK Signature
Scheme v2 y v3, con un firmante RSA de 2048 bits y certificado:

```text
CN=scli, OU=uteq, O=uteq, L=Quevedo, ST=Los Rios, C=EC
```

La release `v1.0.1` contiene tambien `SHA256SUMS.txt`,
`SCLI-PFC-v1.0.1.pdf`, `Source code (zip)` y `Source code (tar.gz)`. La
verificacion documental esta registrada en
[`VERIFICACION-v1.0.1.md`](VERIFICACION-v1.0.1.md).

El artifact de origen correspondiente al SHA fuente
`0b755310a0acf34da2456290a4f978475a8e17f9` es:

```text
scli-mobile-release-0b755310a0acf34da2456290a4f978475a8e17f9
```

Fue publicado por el run de CI `34688947156`. Esa ejecucion es evidencia
historica, no la evidencia vigente de la release verificada `v1.0.1`. El job
`Build - Android release signed` termino con estado `completed/success` despues
de ejecutar `zipalign`, firmar con `apksigner`, verificar la firma mediante
`apksigner verify`, generar `SHA256SUMS.txt` y comprobar el checksum incluido.

El artifact historico contiene exclusivamente:

```text
scli-mobile-0.1.0-release.apk
SHA256SUMS.txt
```

Para revisar esa evidencia historica, abra el repositorio en GitHub y siga esta
ruta:

```text
GitHub -> Actions -> CI -> run 34688947156 -> Artifacts
```

Actions continua siendo la fuente reproducible del proceso de generacion, firma
y verificacion. El APK `scli-mobile-0.1.0-release.apk` se conserva unicamente
como artefacto historico y no debe interpretarse como la release vigente. El
keystore y sus credenciales permanecen fuera del repositorio y se gestionan
mediante GitHub Secrets durante la ejecucion del workflow.
