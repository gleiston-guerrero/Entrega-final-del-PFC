# Reconciliación de hashes internos (`comparacion.json` / `config.json`)

`resumen.json` registra dos huellas SHA256 propias:

- `sha256` (de `comparacion.json`): `1761eec8a90e49cf232ab44ac146346e17ab06744140cb57522b57b73094aacf`
- `config_sha256` (de `config.json`): `f21a2157def850f8870f7f5a25307956f03d6e0578db28f475ada57b5493a9d8`

## Estado resuelto

| Archivo | SHA256 registrado en `resumen.json` | SHA256 físico actual | ¿Coincide? |
| --- | --- | --- | --- |
| `comparacion.json` | `1761eec8a90e49cf232ab44ac146346e17ab06744140cb57522b57b73094aacf` | `1761eec8a90e49cf232ab44ac146346e17ab06744140cb57522b57b73094aacf` | Sí |
| `config.json` | `f21a2157def850f8870f7f5a25307956f03d6e0578db28f475ada57b5493a9d8` | `f21a2157def850f8870f7f5a25307956f03d6e0578db28f475ada57b5493a9d8` | Sí |

La corrección #20 restauró y preservó criptográficamente los bytes originales con
terminador de línea CRLF. Los hashes físicos actuales coinciden exactamente con
los valores `sha256` y `config_sha256` de `resumen.json`.

## Relación con #20

La corrección **#20** ya fusionada en `main` protege `comparacion.json` y
`config.json` como archivos binarios (`text: unset`). Así se evita cualquier
normalización EOL futura y se preservan los bytes CRLF demostrados por las
huellas SHA256 anteriores.

**Estado: RESUELTO mediante #20.**

## Estado previo a #20 (histórico)

Antes de #20, Git normalizaba los finales de línea a LF. En ese estado, los
hashes físicos no coincidían con los valores registrados, que correspondían a
la representación CRLF original. Esta situación queda documentada únicamente
como antecedente histórico; no describe el estado actual del paquete.
