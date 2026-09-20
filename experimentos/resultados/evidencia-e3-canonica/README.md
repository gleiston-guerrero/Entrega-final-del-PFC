# Evidencia E3 canónica

Esta carpeta contiene una selección compacta y versionable de los insumos que
sostienen [`../analisis-e3.json`](../analisis-e3.json). El software medido
corresponde al SHA experimental
`fa7d75ec0f75573938bf46ed6a68f0aee99606ac`; los commits posteriores pueden
incorporar análisis y documentación sin cambiar la identidad del software
ensayado.

Los archivos son copias byte a byte del raw local. No se alteraron resultados,
conteos, manifiestos ni porcentajes. El raw completo permanece fuera de Git por
su volumen y conserva, entre otros derivados, los reportes HTML. Esta selección
no sustituye ni modifica los originales ni las evidencias históricas de SHA
anteriores, que permanecen separadas y etiquetadas como antecedentes.

## Relación con el análisis oficial

| Contenido canónico | Función en la cadena de evidencia |
|---|---|
| `e3_study.json` | Identifica el SHA y la rama comunes del estudio. |
| `e3_*/campaign.json` | Registra metadatos consolidados y las tres repeticiones de cada campaña. |
| `e3_*/rep-NN/manifest.json` | Registra SHA, entorno, comando, estado e integridad de cada repetición. |
| `e3_seguridad/rep-NN/decisiones.csv` | Fuente de siete decisiones distintas. El analizador valida los mismos casos y resultados en tres repeticiones, informa repetibilidad 3/3 por separado y calcula Wilson sobre n=7, no n=21. |
| `e3_compatibilidad/rep-NN/<motor>/summary.json` | Fuente de ocho casos distintos por motor. Las tres ejecuciones se usan para repetibilidad; Wilson se calcula sobre n=8 por motor, no n=24. |
| `e3_mantenibilidad/rep-NN/metricas.csv` | Conserva porcentajes históricos, umbrales y códigos de salida de E3; no se modifica para adecuarlo al análisis posterior. |
| `e3_mantenibilidad/rep-NN/<servicio>/report/jacoco.csv` | Fuente vigente #32 para recalcular líneas de los cinco servicios Java desde `LINE_MISSED` y `LINE_COVERED`, y para derivar contadores `COMPLEXITY`; no se alteran los CSV históricos. |
| `e3_mantenibilidad/rep-NN/web/report/coverage-summary.json` | Reporte fuente compacto de cobertura Web. |
| `e3_mantenibilidad/rep-NN/android/report/jacocoTestReport.xml` | Reporte fuente compacto de cobertura Android. |
| `MANIFEST-SHA256.txt` | Hash SHA-256 de cada archivo incluido en este paquete, salvo el propio manifiesto. |

## Procedencia de las repeticiones de mantenibilidad

Las tres repeticiones son invocaciones separadas del instrumental, ejecutadas
en ventanas UTC no solapadas. Sus manifiestos registran respectivamente las
repeticiones 1, 2 y 3, el mismo SHA experimental y comandos completos. Los
hashes SHA-256 de esos manifiestos son `9847d840af99d40be19a6d3f81dc4eb84958271769e13b127dde8a17895e219b`,
`e3eea04f7860e7ba6ff4523898e19eb1133f0f4f34c1a0298651fac792897deb` y
`3bf1c5aa18e87ff01f4ed5c68bed220abfc3c73900583cc11520bdf7ebff652e`.

| Repetición | Ventana UTC | SHA-256 `metricas.csv` | SHA-256 informe Android | `sessioninfo` JaCoCo Android | Cobertura Android |
|---|---|---|---|---|---:|
| `rep-01` | 2026-09-12 05:38:47.397078–05:52:30.095802 | `d336496f1f9ec8d144853b64e310dceb9c2262885b1d061029062cfbeb5eeac5` | `3152520eb897ae2bbf7044cbb884036f6e35ec5297fc481573a4eda0b810fd0e` | `DESKTOP-N45EJGV-f3ab9b30` | 38,34070796460177 % |
| `rep-02` | 2026-09-12 05:53:48.384042–06:05:14.745791 | `d336496f1f9ec8d144853b64e310dceb9c2262885b1d061029062cfbeb5eeac5` | `689c514199693da3a1d3f0f208697fc6cae7f8c4d299868ef714c7d611d77815` | `DESKTOP-N45EJGV-b268151` | 38,34070796460177 % |
| `rep-03` | 2026-09-12 06:07:00.038156–06:18:59.123202 | `d336496f1f9ec8d144853b64e310dceb9c2262885b1d061029062cfbeb5eeac5` | `07d393d05fedd9e569bbe2c566e0441d1a6cfb6645940ebf64449658ba11338a` | `DESKTOP-N45EJGV-f0c2743e` | 38,34070796460177 % |

La igualdad de `metricas.csv` y de la cobertura es el resultado determinista de
la misma suite sobre el mismo SHA. No se utiliza `sample_sd = 0` ni el IC95
degenerado como prueba de independencia o precisión fuerte: la separación se
establece por la procedencia registrada y por los reportes Android con sesiones
y hashes diferentes. El raw completo conserva los logs, pero estos metadatos y
reportes compactos bastan para comprobar la separación sin versionar derivados
voluminosos.

`analizar_e3.py` no necesita los `playwright.json` para producir
`analisis-e3.json`; por eso no se incluyeron. Tampoco se copiaron HTML, logs ni
otros derivados voluminosos. La trazabilidad completa está en
[`../TRAZABILIDAD-E3-E4.md`](../TRAZABILIDAD-E3-E4.md).

## Resultado desfavorable preservado

La selección incluye sin ocultarlo el resultado Android de
38,34070796460177 % de líneas frente al umbral de 70 %. Por esta única puerta,
la decisión global experimental de mantenibilidad es **NO CUMPLE**.
