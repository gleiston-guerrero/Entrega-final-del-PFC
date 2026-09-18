# Evidencia de la corrección #17

Esta carpeta conserva la evidencia versionada de la corrección #17 del PFC.
No se eliminan carpetas históricas.

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

Dentro de `analysis-definitivo-233b34ac-a09f-40c9-be71-5570f25affbd` están:

- `resumen.json`
- `resumen.csv`
- `speedup.png`

El entorno de referencia fue Python 3.13.14, PySpark 4.0.4, Java 21 y pandas
2.3.3. Las versiones adicionales se consultan en `packages.txt` y
`provenance.json`; no se copian secretos ni URLs con credenciales.

## Intentos históricos

Las carpetas `benchmark-final`, `benchmark-full` y otros benchmarks o
diagnósticos anteriores, si existen, son intentos de diagnóstico. No forman
parte del lote utilizado para estos resultados finales.
