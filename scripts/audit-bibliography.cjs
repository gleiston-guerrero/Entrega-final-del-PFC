#!/usr/bin/env node
// Run after the four LaTeX/BibTeX phases and pdftotext main.pdf main.text.txt.
// No dependencies. Checks actual .aux, .bbl and PDF text, not just .bib fields.
const fs = require('node:fs');
const path = require('node:path');
const docs = path.resolve(__dirname, '../docs');
const read = name => fs.readFileSync(path.join(docs, name), 'utf8').replace(/\r\n/g, '\n');
const errors = [];
const uncomment = text => text.replace(/(?<!\\)%[^\n]*/g, '');
const sources = new Map();
function source(name) {
  if (sources.has(name)) return '';
  const text = uncomment(read(name));
  sources.set(name, text);
  return text + [...text.matchAll(/\\(?:input|include)\{([^}]+)\}/g)]
    .map(m => source(m[1].endsWith('.tex') ? m[1] : m[1] + '.tex')).join('\n');
}
const tex = source('main.tex');
const keys = (text, pattern) => new Set([...text.matchAll(pattern)].flatMap(m => m[1].split(',').map(s => s.trim())));
const cited = keys(tex, /\\cite(?:\[[^\]]*\])?\{([^}]+)\}/g);
const aux = keys(read('main.aux'), /\\citation\{([^}]+)\}/g);
const bib = new Map([...read('Referencias.bib').matchAll(/@\w+\{([^,]+),([\s\S]*?)^\}/gm)].map(m => [m[1], m[2]]));
const items = [...read('main.bbl').matchAll(/\\bibitem\{([^}]+)\}([\s\S]*?)(?=\\bibitem|\\end\{thebibliography\})/g)];
const printed = new Set(items.map(m => m[1]));
function equal(a, b, name) {
  const difference = [...a].filter(k => !b.has(k)).concat([...b].filter(k => !a.has(k)));
  if (difference.length) errors.push(name + ': ' + difference.join(', '));
}
equal(cited, aux, 'Source/aux mismatch');
equal(cited, printed, 'Cited/printed mismatch');
const orphaned = [...bib.keys()].filter(key => !cited.has(key));
const missingBib = [...cited].filter(key => !bib.has(key));
console.log(`REFERENCIAS_BIB=${bib.size}`);
console.log(`REFERENCIAS_HUERFANAS=${orphaned.length}`);
console.log(`CLAVES_HUERFANAS=${orphaned.join(',')}`);
console.log(`CLAVES_CITADAS_INEXISTENTES=${missingBib.join(',')}`);
if (orphaned.length) errors.push('Orphan bibliography entries: ' + orphaned.join(', '));
if (missingBib.length) errors.push('Cited keys missing from bibliography: ' + missingBib.join(', '));
if (items.length !== printed.size) errors.push('Duplicate bibitems');
if (!cited.size) errors.push('No citations found');
const pdfText = read('main.text.txt');
const headings = [...pdfText.matchAll(/Referencias|Bibliography/gi)];
if (!headings.length) throw Error('Bibliography heading missing in extracted PDF text');
const start = headings.at(-1).index;
const pdf = new Map([...pdfText.slice(start).matchAll(/(?:^|\n)\[(\d+)\]\s([\s\S]*?)(?=\n\[\d+\]\s|$)/g)].map(m => [Number(m[1]), m[2]]));
equal(new Set(items.map((_, i) => i + 1)), new Set(pdf.keys()), 'BBL/PDF numbering mismatch');
// pdftotext may omit a hyphen at a physical line break; normalize separators only.
const compact = text => text.replace(/[\s{}~\-\u00ad\u2010-\u2014]/g, '').toLowerCase();
function validIsbn(value) {
  const digits = value.replace(/-/g, '');
  return /^\d{13}$/.test(digits) && [...digits].reduce((sum, d, i) => sum + Number(d) * (i % 2 ? 3 : 1), 0) % 10 === 0;
}
function normalizeName(value) {
  return value
    .replace(/\\[a-zA-Z]+(?:\{([^}]*)\})?/g, '$1')
    .replace(/[{}\\]/g, '')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/[^a-z0-9]/g, '');
}
function authorSurnames(entry) {
  const author = entry.match(/\bauthor\s*=\s*\{([\s\S]*?)\}(?=\s*,|\s*$)/)?.[1] || '';
  return author.split(/\s+and\s+/i).map(authorPart => {
    const commaParts = authorPart.split(',');
    return normalizeName((commaParts.length > 1 ? commaParts[0] : authorPart).trim().split(/\s+/).pop());
  }).filter(Boolean);
}
// This checks only explicit surname-to-citation constructions, not whether the
// surrounding prose semantically describes the cited work correctly.
const nominalCitations = /([A-ZÁÉÍÓÚÜÑ][\p{L}'-]+)~(?:\\emph\{et al\.\}~)?\\cite(?:\[[^\]]*\])?\{([^}]+)\}/gu;
for (const match of tex.matchAll(nominalCitations)) {
  const surname = normalizeName(match[1]);
  for (const key of match[2].split(',').map(value => value.trim())) {
    if (bib.has(key) && !authorSurnames(bib.get(key)).includes(surname)) {
      errors.push(`Nominal attribution mismatch: ${match[1]} -> ${key}`);
    }
  }
}
const missing = [];
console.log('CLAVES_CITADAS=' + [...cited].sort().join(','));
console.log('CLAVES_IMPRESAS=' + [...printed].join(','));
for (const [i, item] of items.entries()) {
  const key = item[1];
  const entry = bib.get(key) || '';
  const field = name => entry.match(new RegExp('\\b' + name + '\\s*=\\s*\\{([^}]+)\\}'))?.[1];
  const type = field('doi') ? 'doi' : field('isbn') ? 'isbn' : 'url';
  const id = field(type);
  if (type === 'isbn' && !validIsbn(id)) errors.push('Invalid ISBN: ' + key);
  const target = id && compact(id);
  const bblText = compact(item[2]);
  const rendered = compact(pdf.get(i + 1) || '');
  if (!target || !bblText.includes(target) || !rendered.includes(target)) missing.push(key);
  if (target && (bblText.split(target).length !== 2 || rendered.split(target).length !== 2)) errors.push('Identifier missing/duplicated: ' + key);
  console.log(`[${i + 1}] ${key} | ${type}: ${id} | BBL=${Boolean(target && bblText.includes(target))} PDF=${Boolean(target && rendered.includes(target))}`);
}
const log = read('main.log');
const blg = read('main.blg');
const undefinedCitations = (log.match(/LaTeX Warning: Citation[^\n]*undefined/g) || []).length;
const undefinedReferences = (log.match(/LaTeX Warning: Reference[^\n]*undefined/g) || []).length;
if (/undefined|Rerun to get cross-references right/.test(log) || /Warning--|error message/i.test(blg)) errors.push('LaTeX/BibTeX unresolved diagnostics');
console.log(`REFERENCIAS_CITADAS=${cited.size}\nREFERENCIAS_IMPRESAS=${printed.size}\nCON_IDENTIFICADOR_PERSISTENTE=${printed.size - missing.length}\nSIN_IDENTIFICADOR_PERSISTENTE=${missing.length}`);
console.log('CLAVES_SIN_IDENTIFICADOR=' + missing.join(','));
console.log(`UNDEFINED_CITATIONS=${undefinedCitations}\nUNDEFINED_REFERENCES=${undefinedReferences}`);
if (missing.length) errors.push('Missing identifiers');
if (errors.length) { console.error(errors.join('\n')); process.exitCode = 1; }
