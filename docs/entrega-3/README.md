# Entrega 3 — snapshot reproducible reconstruida

Esta carpeta es una **snapshot reproducible reconstruida y congelada el
2026-09-13** a partir del commit histórico
`859bc582f9473b68cde1531f1bd4d6f0f5b34500` (`Entrega anterior`, autor y
commit del 2026-08-15T20:53:10-05:00). Se creó ahora para corregir la falta de
aislamiento de la copia documental anterior; no se presenta como evidencia
creada en agosto ni modifica la fecha o el contenido sustantivo de la entrega.

## Hallazgo y alcance de la reconstrucción

El PDF histórico `Informe_E3_SCLI_LATEX.pdf` ya era el mismo blob conservado
en el commit de origen. En cambio, el `main.tex` que anteriormente ocupaba
esta carpeta provenía de una revisión posterior: se identificaba como Entrega
4, importaba cinco secciones E4 y resolvía diagramas y evidencias desde
directorios vivos mediante rutas `../`. Una recompilación podía, por tanto,
incorporar contenido actual y fallaba por la figura ausente
`figuras/panel-monitoreo.png`.

La reconstrucción conserva el `main.tex` y `Referencias.bib` de la Entrega 3
del commit de origen y copia dentro de `evidencias/` las trece imágenes que ese
documento referencia. No hay `\\input` de secciones actuales ni rutas de
figuras que salgan de esta carpeta. Las únicas dependencias externas son las
herramientas y paquetes estándar de LaTeX declarados en `main.tex`.

## Procedencia y estado Git

- Commit histórico de origen: `859bc582f9473b68cde1531f1bd4d6f0f5b34500`.
- HEAD sobre el que se preparó esta congelación: `6507bb4f7fc41e0c02b1ada2e411d4f5656f8559`.
- Commit que congela la snapshot:
  `ed6b48b7b9c4372c1c3432e57f731196e0f2a3ac`
  (`docs(e6): congelar snapshot reproducible de entrega 3`,
  2026-09-13T17:27:07-05:00).
- Fecha real de reconstrucción: `2026-09-13`.
- El PDF entregado históricamente se preserva sin cambios como
  `Informe_E3_SCLI_LATEX.pdf`.
- El PDF producido con la receta reproducible actual se conserva como
  `Informe_E3_SCLI_RECONSTRUIDO.pdf` y no sustituye al entregado.

## Archivos congelados

- `main.tex` y `Referencias.bib`;
- `.gitattributes` y `.gitignore`, que fijan finales de línea y excluyen
  productos intermedios;
- `evidencias/cluster_3_nodos_docker.png`;
- `evidencias/cluster_3_nodos_estado.png`;
- `evidencias/schema_tablas_cluster.png`;
- `evidencias/replicacion_num_replicas_3.png`;
- `evidencias/carga_100000_registros.png`;
- `evidencias/seeds_sql_creado.png`;
- `evidencias/carga_lote_01_10000.png`;
- `evidencias/tolerancia_fallo_un_nodo.png`;
- `evidencias/tolerancia_fallo_dos_nodos.png`;
- `evidencias/recuperacion_cluster_3_nodos.png`;
- `evidencias/latencia_antes_fallo.png`;
- `evidencias/latencia_un_nodo_caido.png`;
- `evidencias/latencia_despues_recuperacion.png`;
- los dos PDFs, esta nota, `compilar.sh` y `SHA256SUMS.txt`.

`SHA256SUMS.txt` cubre todos los archivos anteriores salvo el propio
manifiesto, para evitar autorreferencia.

## Compilación exacta

Desde esta carpeta, con `pdflatex` y `bibtex` disponibles:

```sh
sh ./compilar.sh
```

La validación de esta reconstrucción se realizó con la imagen inmutable:

```sh
docker run --rm \
  -v "$PWD:/work" -w /work \
  texlive/texlive@sha256:4984977ccf5afe883cb382d0163f267de0d029d140bb7a9e8f4c19f0b781d57b \
  sh ./compilar.sh
```

La receta fija `SOURCE_DATE_EPOCH=1786845190`, correspondiente al commit de
origen, y ejecuta pdfLaTeX, BibTeX y dos pasadas finales de pdfLaTeX. Dos
compilaciones limpias con esa imagen deben producir el mismo SHA-256. El log
final debe carecer de referencias/citas indefinidas y de figuras ausentes.

El script genera exclusivamente `build/main.pdf`; no sobrescribe
`Informe_E3_SCLI_LATEX.pdf` ni `Informe_E3_SCLI_RECONSTRUIDO.pdf`, porque ambos
son artefactos congelados cubiertos por `SHA256SUMS.txt`. Para evitar depender
del separador de rutas de `BIBINPUTS`, la bibliografia se copia al directorio
temporal `build/` y BibTeX se ejecuta alli.

Las referencias textuales `experiments/...` que permanecen dentro de
`main.tex` forman parte del contenido historico congelado de E3 y no representan
rutas vigentes del documento acumulativo actual.

Los hashes de la snapshot quedan registrados en `SHA256SUMS.txt`; deben
verificarse desde esta carpeta con `sha256sum -c SHA256SUMS.txt`. Ejecutar
`compilar.sh` no debe modificar ningun archivo versionado ni invalidar ese
manifiesto.
