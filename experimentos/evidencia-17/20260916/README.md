# Evidencia de la corrección #17

Esta carpeta conserva la evidencia versionada de la corrección #17 del PFC.
Esta carpeta conserva el paquete canónico versionado de la corrección #17. Los
intentos previos de diagnóstico que pudieron existir localmente no forman parte
del historial Git y no se presentan como evidencia auditable.

## Evidencia válida final

- Equivalencia funcional: `equivalence-final-a2b60a0e-d2b5-4d69-95c5-904353062c9a`
- Benchmark definitivo: `benchmark-definitivo-9d94efe6-7bb7-4227-b78e-c70092e9bcfb`
- Análisis definitivo: `analysis-definitivo-233b34ac-a09f-40c9-be71-5570f25affbd`

La equivalencia se verificó antes de medir y cubre las 20 columnas del
resultado. El benchmark procesó 90 000 filas por ejecución: 1 warmup y 5
repeticiones medidas para pandas, y 1 warmup y 5 repeticiones medidas para
cada `N=1,2,4,6,8` de Spark. Los registros válidos terminaron con
`status=completed`.

## Resultados

| Tratamiento | Media ms | Desv. ms | Speedup vs pandas | Speedup vs Spark(1) | Eficiencia |
| --- | ---: | ---: | ---: | ---: | ---: |
| pandas | 17326.5594 | 1504.0669 | 1.0000 | -- | -- |
| Spark N=1 | 40932.1306 | 5654.1916 | 0.4233 | 1.0000 | 1.0000 |
| Spark N=2 | 39071.1490 | 1280.0474 | 0.4435 | 1.0476 | 0.5238 |
| Spark N=4 | 40681.5648 | 5748.0534 | 0.4259 | 1.0062 | 0.2515 |
| Spark N=6 | 39392.2152 | 2369.4410 | 0.4398 | 1.0391 | 0.1732 |
| Spark N=8 | 41187.6932 | 1088.0059 | 0.4207 | 0.9938 | 0.1242 |

El ajuste OLS de Amdahl produjo `f=0.9765853071`, fracción paralelizable
efectiva `0.0234146929` y RMSE normalizado `0.0215078993`. La fracción `f` es
efectiva e incluye arranque, JDBC, E/S, escritura y sobrecarga; no representa
el porcentaje de código inherentemente serial. Para esta carga local no se
observó una mejora relevante al aumentar `N`.

## Artefactos principales

Dentro de `equivalence-final-a2b60a0e-d2b5-4d69-95c5-904353062c9a` está
`equivalence.json`. Dentro de
`benchmark-definitivo-9d94efe6-7bb7-4227-b78e-c70092e9bcfb` están:

- `equivalence.json`
- `comparacion.json`
- `comparacion.csv`
- `config.json`
- `inventory.json`
- `provenance.json`
- `packages.txt`
- `RECONCILIACION-PROVENANCE.md` (documenta la reconciliación de la
  procedencia de las fuentes medidas; ver más abajo)
- `RECONCILIACION-HASHES-EOL.md` (documenta la discrepancia CRLF/LF de los
  hashes internos de `comparacion.json`/`config.json`; ver más abajo)

Dentro de `analysis-definitivo-233b34ac-a09f-40c9-be71-5570f25affbd` están:

- `resumen.json`
- `resumen.csv`
- `speedup.png`

El entorno de referencia fue Python 3.13.14, PySpark 4.0.4, Java 21 y pandas
2.3.3. Las versiones adicionales se consultan en `packages.txt` y
`provenance.json`; no se copian secretos ni URLs con credenciales.

## Procedencia (`provenance.json`) y hashes internos

`provenance.json` declara `git_head = 21d2d3e19c68546638e2760074cd35ccd6c05402`,
pero ese SHA no contiene exactamente las fuentes registradas por hash. Los
SHA-256 de las fuentes medidas coinciden con las versiones posteriormente
incorporadas en `197ce3305c821a37c788f4c8f7a783996121f6cc`; por cronología, la
evidencia indica que el benchmark se ejecutó sobre un árbol de trabajo no
confirmado. No es posible atribuir honestamente la ejecución a un commit
exacto. Se conserva `provenance.json` sin reescribir como evidencia histórica y
la discrepancia queda documentada en
`benchmark-definitivo-9d94efe6-7bb7-4227-b78e-c70092e9bcfb/RECONCILIACION-PROVENANCE.md`.

Los hashes `sha256`/`config_sha256` registrados en `resumen.json` coinciden
exactamente con los bytes CRLF preservados por #20. Las rutas
`comparacion.json` y `config.json` están protegidas como binarias (`text:
unset`) para evitar normalización EOL futura. El detalle, incluidos los hashes
verificados, está en
`benchmark-definitivo-9d94efe6-7bb7-4227-b78e-c70092e9bcfb/RECONCILIACION-HASHES-EOL.md`.

## Integridad del paquete

`experimentos/verificar_manifiesto_evidencia17.py` genera y verifica un
manifiesto SHA256 para todo este paquete. `SHA256SUMS.txt` ya está generado y
es versionable: cubre los 50 archivos del paquete actual, usa rutas relativas,
mantiene un orden determinista y no se incluye a sí mismo. La verificación real
completa los 50 archivos correctamente. El script está probado
(`experimentos/tests/test_verificar_manifiesto_evidencia17.py`, incluye una
prueba de fallo ante alteración de un byte) y puede ejecutarse localmente en
cualquier momento:

```
py experimentos/verificar_manifiesto_evidencia17.py generar --paquete experimentos/evidencia-17/20260916
py experimentos/verificar_manifiesto_evidencia17.py verificar --paquete experimentos/evidencia-17/20260916
```

La prueba negativa sobre una copia temporal detecta la alteración de
`README.md` y devuelve un código de salida distinto de cero. La integración
de este manifiesto al CI general se realizará en #19; todavía no se afirma que
CI lo ejecute.

## Intentos históricos

Únicamente el paquete canónico descrito arriba
(`equivalence-final-a2b60a0e-d2b5-4d69-95c5-904353062c9a`,
`benchmark-definitivo-9d94efe6-7bb7-4227-b78e-c70092e9bcfb` y
`analysis-definitivo-233b34ac-a09f-40c9-be71-5570f25affbd`) está versionado en
este repositorio. Intentos previos de diagnóstico (por ejemplo carpetas con
nombres como `benchmark-final` o `benchmark-full`) no forman parte del
repositorio Git y no pueden auditarse desde aquí; si existieron localmente,
no se incluyeron ni se referencian como evidencia.
