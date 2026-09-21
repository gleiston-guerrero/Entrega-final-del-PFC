#!/usr/bin/env sh
set -eu

SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1786845190}"
export SOURCE_DATE_EPOCH
export FORCE_SOURCE_DATE=1
export TZ=UTC

build_dir="build"
mkdir -p "$build_dir"
rm -f "$build_dir/main.aux" "$build_dir/main.bbl" "$build_dir/main.blg" \
  "$build_dir/main.fdb_latexmk" "$build_dir/main.fls" "$build_dir/main.log" \
  "$build_dir/main.out" "$build_dir/main.pdf" "$build_dir/main.toc"

cp Referencias.bib "$build_dir/Referencias.bib"

pdflatex -interaction=nonstopmode -halt-on-error -recorder \
  -output-directory="$build_dir" main.tex
(
  cd "$build_dir"
  bibtex main
)
pdflatex -interaction=nonstopmode -halt-on-error -recorder \
  -output-directory="$build_dir" main.tex
pdflatex -interaction=nonstopmode -halt-on-error -recorder \
  -output-directory="$build_dir" main.tex
printf '%s\n' "PDF generado en $build_dir/main.pdf"
