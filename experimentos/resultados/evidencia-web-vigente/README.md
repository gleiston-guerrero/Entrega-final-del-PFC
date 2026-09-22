# Evidencia vigente de cobertura Web

Esta evidencia corresponde a la medición Web vigente del commit
`a9fc56f9e19d6a694b4338a4de23796cc6e422ac`. Es una ejecución local
reproducible del commit indicado y no es evidencia histórica E3.

## Reproducción

Desde `apps/web`:

```text
npm run test:coverage
```

Entorno registrado:

- Node.js `v24.15.0`
- npm `11.12.1`
- Vitest `4.1.11` (dependencia instalada del proyecto)

La ejecución produjo 296/296 pruebas aprobadas y superó los umbrales
en 43/43 archivos de prueba. Las métricas globales copiadas desde
`coverage-summary.json` son:

| Métrica | Cubiertas | Total | Porcentaje |
|---|---:|---:|---:|
| Statements | 2307 | 2817 | 81,89 % |
| Branches | 1558 | 2219 | 70,21 % |
| Functions | 851 | 1085 | 78,43 % |
| Lines | 1959 | 2308 | 84,87 % |

`coverage-summary.json` es una copia exacta del archivo generado por Vitest.
Este directorio contiene la medición Web vigente y no forma parte de la
evidencia histórica E3 ubicada en `evidencia-e3-canonica/`. Esta evidencia
documenta una ejecución local; no afirma resultados de CI remoto.
