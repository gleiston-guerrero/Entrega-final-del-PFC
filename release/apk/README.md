# APK release firmado

Los APK release firmados se generan, firman, verifican y publican mediante
GitHub Actions. Actualmente este directorio conserva una copia historica
verificada en `scli-mobile-0.1.0-release.apk` y su checksum en
`SHA256SUMS.txt`; las claves privadas y contrasenas de firma no se almacenan en
Git. La version Android actual del proyecto es `versionName` 1.0.1 y
`versionCode` 2, pero el APK final 1.0.1+ aun esta pendiente de generacion
oficial por CI, publicacion y preservacion en este directorio.

El artifact de origen correspondiente al SHA fuente
`0b755310a0acf34da2456290a4f978475a8e17f9` es:

```text
scli-mobile-release-0b755310a0acf34da2456290a4f978475a8e17f9
```

Fue publicado por el run de CI `34688947156`. Esa ejecucion es evidencia
historica, no la evidencia final vigente del release 1.0.1+. El job
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
GitHub → Actions → CI → run 34688947156 → Artifacts
```

Actions continua siendo la fuente reproducible del proceso de generacion, firma
y verificacion. Cuando CI genere oficialmente el APK final 1.0.1+, este
artefacto historico debera ser reemplazado o acompanado por el nuevo APK firmado
y su `SHA256SUMS.txt`. El keystore y sus credenciales permanecen fuera del
repositorio y se gestionan mediante GitHub Secrets durante la ejecucion del
workflow.
