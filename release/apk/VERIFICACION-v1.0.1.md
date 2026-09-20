# Verificacion de release v1.0.1

Este archivo registra la evidencia textual de la release oficial verificada del
APK correspondiente al punto #35. La validacion se realizo sobre el APK
descargado directamente desde la GitHub Release `v1.0.1`; no se incluyen
secretos, keystores, contrasenas ni valores sensibles.

## Identificacion

- Tag: `v1.0.1`
- Commit etiquetado: `166a2c4c48f1f6dfebc3ef087652d60b9f7ed3a8`
- APK publicado: `scli-mobile-v1.0.1-release.apk`
- SHA-256 del APK:
  `a6504201aa9d7aaf16299c6417ff33d8f1b42f129508ce708335b859dd454ad8`
- Resultado de checksum: coincide exactamente con `SHA256SUMS.txt`
- GitHub Actions: el run asociado al tag `v1.0.1` termino en `Success`

## Verificacion de firma APK

Resumen de `apksigner`:

```text
Verified using v1 scheme: false
Verified using v2 scheme: true
Verified using v3 scheme: true
Verified using v3.1 scheme: false
Verified using v4 scheme: false
Number of signers: 1
```

Datos del certificado:

- DN: `CN=scli, OU=uteq, O=uteq, L=Quevedo, ST=Los Rios, C=EC`
- Algoritmo: `RSA`
- Tamano: `2048 bits`
- Certificado SHA-256:
  `2ff3f1862f0dfd56f650855aeeb4f8e18d0c5976756097737ef707fd2903dcd7`

## Assets publicados

- `scli-mobile-v1.0.1-release.apk`
- `SHA256SUMS.txt`
- `SCLI-PFC-v1.0.1.pdf`
- `Source code (zip)`
- `Source code (tar.gz)`

El APK binario no se incorpora al repositorio en esta actualizacion documental;
se mantiene publicado como asset de la GitHub Release.
