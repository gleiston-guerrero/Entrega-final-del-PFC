# Documentación académica

## Fuente oficial

La única fuente oficial y acumulativa del informe final es [`docs/main.tex`](main.tex).
GitHub Actions la compila desde `docs/` y publica `main.pdf` como artifact
`informe-final-scli`. El PDF oficial no se versiona necesariamente en Git.

Para reproducir el mismo procedimiento desde la raíz:

```bash
cd docs
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

Las fuentes modulares vigentes que consume el informe están en
[`docs/secciones/`](secciones/). Los ADR, diagramas, evidencias técnicas, contratos
OpenAPI e informes ISO son documentación complementaria trazable.

## Trabajo colaborativo

Los [registros retrospectivos del equipo](actas/README.md) consolidan cinco
bloques de trabajo, los roles generales, los acuerdos respaldados por el
proyecto y su seguimiento mediante commits, ADR, workflows y documentos
versionados. Los cinco registros fueron creados el 12/09/2026 en el commit
`1ce91ba05e8048fda75a8479d368684a2c338430`. Git acredita los resultados
técnicos, pero no una reunión, su modalidad, hora o asistencia.

## Documentación histórica

`docs/entrega-3/` y `docs/entrega-4/` son snapshots históricos de entregas
anteriores. Su contenido no es fuente vigente ni reemplaza `docs/main.tex`.
`docs/entrega-4/` conserva únicamente el PDF histórico y su README explicativo;
las fuentes modulares vigentes están exclusivamente en `docs/secciones/`.
Las inconsistencias editoriales del material histórico se preservan cuando
forman parte del material originalmente entregado.

Los PDFs históricos pueden no contener integraciones documentales posteriores.
Para consultar el estado acumulativo se debe usar la fuente oficial o el artifact
producido por el workflow de documentación.

## Evidencias visuales

Existe una captura versionada del dashboard real de Grafana en
`release/screenshots/panel-monitoreo.png`. El flujo QR real en dispositivo se
encuentra documentado en `docs/evidencias/qr-e2e-2026-09-20.md`, con las capturas
`docs/evidencias/qr-escaneo-real-2026-09-20.png` y
`docs/evidencias/qr-resultado-laboratorio-2026-09-20.png`. Las evidencias
visuales incorporadas deben proceder de un entorno real, omitir secretos y datos
personales, e identificar SHA, fecha, zona horaria y entorno.
