# Corrección #22 — Bibliografía con identificadores visibles

Fecha: 2026-09-18. Rama: `fix/eval2-22-bibliografia-ivan`.
Base: `b1a03332a798be3257d67b985498034a94adb8f0`.
Alcance: `docs/main.tex`, su bibliografía y una comprobación reproducible.
Se revisaron también los cinco archivos de `docs/secciones/`; no necesitaron cambios.

## Hallazgos y correcciones

La fuente inicial citaba 34 claves distintas. `ieeetr` no imprime los campos
`doi`, `isbn` y `url`: 21 referencias carecían de identificador visible.
Se conserva el estilo y se añade a `note` un único identificador por entrada
citada, en orden DOI > ISBN verificado > URL oficial. Se conservan las notas
preexistentes y los campos estructurados para otros consumidores del BibTeX.

| Atribución | Clave incorrecta | Corrección |
|---|---|---|
| RFC 7519 | `venckauskas2023jwt` | `jones2015jwt` |
| Fielding / REST | `li2021microservices` | `fielding2000rest` |
| Newman, dos menciones | `li2021microservices` | `newman2015microservices` |
| Brewer / CAP | `lee2023cap` | `brewer2012cap` |
| Abadi / PACELC | `lee2023cap` | `abadi2012pacelc` |
| Ongaro y Ousterhout / Raft | `huang2020tidb` | `ongaro2014raft` |
| Cooper / YCSB | `taipalus2023dbms` | `cooper2010ycsb` |
| Jain, protocolo | `baltes2022sampling` | `jain1991performance` |
| Wohlin, protocolo | `verdecchia2023` | `wohlin2012experimentation` |
| RDD, linaje y recómputo | `wang2022spark` | `zaharia2012rdd` |

Son diez clases de error y once menciones por las dos de Newman. Se conserva
el par de citas correctas de Jain/Wohlin en trabajos relacionados. También
se corrigen las citas de la explicación de PACELC y la descomposición de Raft;
el párrafo sobre quórum de CockroachDB remite a Taft y Ongaro, en vez de TiDB.
PACELC se describe como extensión de CAP. No se modifican fórmulas, datos,
manifiestos experimentales ni el punto #31.

Se incorporan siete entradas: `jones2015jwt`, `fielding2000rest`,
`newman2015microservices`, `brewer2012cap`, `abadi2012pacelc`,
`ongaro2014raft` y `cooper2010ycsb`. Dejan de citarse seis entradas
(`venckauskas2023jwt`, `li2021microservices`, `taipalus2023dbms`,
`baltes2022sampling`, `verdecchia2023`, `wang2022spark`); se mantienen en el
archivo `.bib`. Así, 34 − 6 + 7 = 35 referencias finales.

Campos corregidos:

- `zaharia2012rdd`: Murphy **McCauley**, según la primera página del
  [artículo original de USENIX](https://www.usenix.org/system/files/conference/nsdi12/nsdi12-final138.pdf).
  El BibTeX de la página de USENIX conserva la errata «McCauly» y el ISBN
  `978-931971-92-8`, que no tiene longitud válida. Se elimina ese ISBN sin
  inventar un reemplazo y se conserva/imprime la URL oficial de la obra.
- `salloum2016spark`: se añade `number = {3--4}`. Springer y Crossref confirman
  volumen 1, páginas 145–164, año 2016 y DOI `10.1007/s41060-016-0027-9`.
- Se protegen `{Apache Spark}`, `{OAuth 2.0}`, `{DevSecOps}` y `{SQuaRE}`;
  las entradas nuevas protegen también JSON Web Token/JWT, CAP y YCSB.
- Los ISBN restantes se mantienen; el ISBN de Observability Engineering se
  confirmó en la página de copyright de O'Reilly.

## Fuentes consultadas y cobertura de la auditoría

Se consultó realmente la API pública de Crossref (`GET
https://api.crossref.org/works/{DOI}`) para los 21 DOI existentes, incluidos
los seis que dejan de citarse, y para los artículos nuevos de Brewer,
Abadi y Cooper. Se contrastaron título, autores, año y los campos de
volumen/número/páginas disponibles. La búsqueda por título de Abadi devolvió
`10.1109/MC.2012.33`; no se asignaron DOI por inferencia.

| Clave auditada | Identificador / fuente autoritativa |
|---|---|
| ozsu2020 | [10.1007/978-3-030-26253-2](https://doi.org/10.1007/978-3-030-26253-2) |
| kleppmann2022 | [10.1145/3563901](https://doi.org/10.1145/3563901) |
| lee2023cap | [10.1145/3609119](https://doi.org/10.1145/3609119) |
| taft2020 | [10.1145/3318464.3386134](https://doi.org/10.1145/3318464.3386134) |
| huang2020tidb | [10.14778/3415478.3415535](https://doi.org/10.14778/3415478.3415535) |
| wang2022spark | [10.1016/j.jss.2022.111488](https://doi.org/10.1016/j.jss.2022.111488) |
| poolla2023amdahl | [10.1016/j.micpro.2022.104745](https://doi.org/10.1016/j.micpro.2022.104745) |
| sun2023gustafson | [10.1007/s11390-022-2911-1](https://doi.org/10.1007/s11390-022-2911-1) |
| verdecchia2023 | [10.1016/j.infsof.2023.107329](https://doi.org/10.1016/j.infsof.2023.107329) |
| baltes2022sampling | [10.1007/s10664-021-10072-8](https://doi.org/10.1007/s10664-021-10072-8) |
| taipalus2023dbms | [10.1016/j.jss.2023.111872](https://doi.org/10.1016/j.jss.2023.111872) |
| li2021microservices | [10.1016/j.infsof.2020.106449](https://doi.org/10.1016/j.infsof.2020.106449) |
| venckauskas2023jwt | [10.3390/s23063363](https://doi.org/10.3390/s23063363) |
| aksakalli2021deployment | [10.1016/j.jss.2021.111014](https://doi.org/10.1016/j.jss.2021.111014) |
| berardi2022microservicesecurity | [10.7717/peerj-cs.779](https://doi.org/10.7717/peerj-cs.779) |
| chandramouli2020nist | [10.6028/NIST.SP.800-204A](https://doi.org/10.6028/NIST.SP.800-204A) |
| lodderstedt2025rfc9700 | [10.17487/RFC9700](https://doi.org/10.17487/RFC9700) |
| spath2022proandroid | [10.1007/978-1-4842-8745-3](https://doi.org/10.1007/978-1-4842-8745-3) |
| chandramouli2022nistdevsecops | [10.6028/NIST.SP.800-204C](https://doi.org/10.6028/NIST.SP.800-204C) |
| salloum2016spark | [Springer: 10.1007/s41060-016-0027-9](https://link.springer.com/article/10.1007/s41060-016-0027-9) |
| wohlin2012experimentation | [10.1007/978-3-642-29044-2](https://doi.org/10.1007/978-3-642-29044-2) |
| majors2022observability | [O'Reilly, ISBN 9781492076445](https://www.oreilly.com/library/view/observability-engineering/9781492076438/copyright-page01.html) |
| bass2021softwarearchitecture | [InformIT, ISBN 9780136886099](https://www.informit.com/store/software-architecture-in-practice-9780136886099) |
| farley2021modernsoftwareengineering | [InformIT, ISBN 9780137314744](https://www.informit.com/store/modern-software-engineering-doing-what-works-to-build-9780137314744) |
| winters2020softwareengineeringgoogle | [O'Reilly, ISBN 9781492082781](https://www.oreilly.com/library/view/software-engineering-at/9781492082781/) |
| chambers2018spark | [O'Reilly, ISBN 9781491912201](https://www.oreilly.com/library/view/spark-the-definitive/9781491912201/) |
| jain1991performance | [Wiley, ISBN 9780471503361](https://uat.store.wiley.com/en-us/the-art-of-computer-systems-performance-analysis-techniques-for-experimental-design-measurement-simulation-and-modeling-p-9780471503361) |
| zaharia2012rdd | [USENIX, ficha y artículo original](https://www.usenix.org/conference/nsdi12/technical-sessions/presentation/zaharia) |
| iso25010_2023 | [ISO, ficha 78176](https://www.iso.org/standard/78176.html) |
| iso29119_2_2021 | [ISO, ficha 79428](https://www.iso.org/standard/79428.html) |
| android2026offlinefirst | [Android Developers](https://developer.android.com/topic/architecture/data-layer/offline-first) |
| opentelemetry2026signals | [OpenTelemetry, Signals](https://opentelemetry.io/docs/concepts/signals/) |
| acm2018code | [ACM, código oficial](https://www.acm.org/code-of-ethics) |
| acmieee1999secode | [ACM, código conjunto](https://www.acm.org/code-of-ethics/software-engineering-code) |
| jones2015jwt | [RFC Editor: autores, fecha y DOI 10.17487/RFC7519](https://www.rfc-editor.org/info/rfc7519/) |
| fielding2000rest | [UCI, tesis de Fielding (2000)](https://ics.uci.edu/~fielding/pubs/dissertation/abstract.htm) |
| newman2015microservices | [O'Reilly, ISBN 9781491950357](https://www.oreilly.com/library/view/building-microservices/9781491950340/copyright-page01.html) |
| brewer2012cap | [10.1109/MC.2012.37](https://doi.org/10.1109/MC.2012.37) |
| abadi2012pacelc | [10.1109/MC.2012.33](https://doi.org/10.1109/MC.2012.33), [artículo del autor](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf) |
| ongaro2014raft | [USENIX, ISBN 9781931971102](https://www.usenix.org/conference/atc14/technical-sessions/presentation/ongaro) |
| cooper2010ycsb | [10.1145/1807128.1807152](https://doi.org/10.1145/1807128.1807152) |

Las dos páginas canónicas de ACM respondieron HTTP 403 a la recuperación
directa. Se conservan sus URL oficiales; la identidad de las obras se
contrastó con los resultados indexados de fuentes primarias:
[comunicado ACM de 2018](https://www.acm.org/binaries/content/assets/press-releases/2018/july/acm-updates-code-of-ethics.pdf),
[publicación ACM GSE2009, referencia a la versión 5.2 de 1999](https://www.acm.org/binaries/content/assets/education/gsew2009.pdf)
y [anuncio de IEEE Computer Society](https://www.computer.org/press-room/2016-news/code-of-ethics/).
Esto verifica la identidad y procedencia; no se afirma haber descargado
íntegramente esas dos páginas ni que Crossref verificó recursos sin DOI.

## Reproducción y resultado

Con MiKTeX/TeX Live, BibTeX, `pdftotext` y Node.js disponibles en PATH,
ejecutar desde `docs/`, sin cambiar las cuatro órdenes de compilación:

```text
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdftotext main.pdf main.text.txt
node ../scripts/audit-bibliography.cjs
git diff --check
```

Las cuatro fases devolvieron **0 / 0 / 0 / 0** con MiKTeX 25.12.
La comprobación contrasta las citas de las fuentes realmente incluidas con
`main.aux`, las claves `bibitem` de `main.bbl` y el identificador en el
bloque numerado correspondiente del texto extraído del PDF. Comprueba
ISBN-13, ausencia de duplicación del identificador, asociaciones incorrectas
y diagnósticos sin resolver. Enumera todas las claves citadas/impresas y el
resultado BBL/PDF por referencia. No sustituye la verificación documental
de los metadatos realizada arriba.

```text
REFERENCIAS_CITADAS=35
REFERENCIAS_IMPRESAS=35
CON_IDENTIFICADOR_PERSISTENTE=35
SIN_IDENTIFICADOR_PERSISTENTE=0
CLAVES_SIN_IDENTIFICADOR=
UNDEFINED_CITATIONS=0
UNDEFINED_REFERENCES=0
```

BibTeX: cero warnings, incluidas claves inexistentes. No hay referencias
citadas ausentes ni identificadores duplicados. `git diff --check`: pasa.
Prueba negativa del verificador: al retirar temporalmente el DOI de RFC 7519
del texto extraído, devuelve código 1; restaurado el archivo, vuelve a 0.
El PDF tiene 37 páginas. Persisten avisos de tamaño de figuras y cajas
desbordadas fuera de la bibliografía, además del aviso de mantenimiento de
MiKTeX; no son errores de compilación ni referencias/citas indefinidas.
No se modificó la maquetación ajena a #22 para suprimirlos.

Tras comprobar el PDF se eliminaron exclusivamente los productos no
versionados `docs/main.pdf`, `.aux`, `.bbl`, `.blg`, `.log`, `.out`,
`main.text.txt`, `main.audit.txt`, `main.negative.txt` y `main.phase1.txt`
a `main.phase4.txt`. Para repetir la
auditoría hay que regenerarlos con los comandos anteriores.

NO STAGE. NO COMMIT. NO PUSH.
