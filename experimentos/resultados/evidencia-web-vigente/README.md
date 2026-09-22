# Evidencia vigente de cobertura Web

Esta evidencia corresponde a la medición Web vigente de la rama
`fix/eval5-07-web-coverage-deterministic-isaias`, creada desde el SHA base
`5f909ed87f4983c12ffb20a69dbcf2e3eadbec03`. Es una ejecución local
reproducible del árbol corregido y no es evidencia histórica E3.

## Reproducción

Desde `apps/web`:

```text
npm run test:coverage
```

Entorno registrado:

- Node.js `v24.15.0`
- npm `11.12.1`
- Vitest `4.1.11` (dependencia instalada del proyecto)

Cada una de las tres ejecuciones produjo 296/296 pruebas aprobadas y superó los
umbrales en 43/43 archivos de prueba. Las métricas globales copiadas desde
`coverage-summary.json` son:

| Métrica | Cubiertas | Total | Porcentaje |
|---|---:|---:|---:|
| Statements | 2307 | 2817 | 81,89 % |
| Branches | 1558 | 2219 | 70,21 % |
| Functions | 851 | 1085 | 78,43 % |
| Lines | 1959 | 2308 | 84,87 % |

`coverage-summary.json` es una copia exacta del archivo generado por Vitest.
Las tres ejecuciones produjeron los mismos contadores: 2307/2817 statements,
1558/2219 branches, 851/1085 functions y 1959/2308 lines. La variación previa
de branches se debía al día real del sistema leído por `MainPage.tsx` durante
`MainPage.test.tsx`; la prueba ahora fija explícitamente la fecha y restaura los
timers después de cada caso.
Este directorio contiene la medición Web vigente y no forma parte de la
evidencia histórica E3 ubicada en `evidencia-e3-canonica/`. Esta evidencia
documenta una ejecución local; no afirma resultados de CI remoto.
