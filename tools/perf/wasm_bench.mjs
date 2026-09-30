// WASM (web-tree-sitter) full-parse timing, driven by tools/perf/wasm.py.
//
//   node tools/perf/wasm_bench.mjs MANIFEST.json OUT.json
//
// MANIFEST: {"wasm": path, "repeats": 3, "files": [path, ...]}
// OUT:      {"web_tree_sitter", "read_seconds", "invalid_utf8": [index],
//            "has_error": [bool per file], "ns": [[ns per file] per repeat]}
//
// Files are read into memory (Buffers) before any timing. Each file is decoded to a JS
// string just before its parse, outside the timed region: only parser.parse() is timed,
// the same as the native run. The BOM is kept (ignoreBOM), so both runtimes see the same
// text. A warm-up pass is discarded; trees are deleted after each parse (WASM heap).
import { readFileSync, writeFileSync } from 'node:fs';
import { Parser, Language } from 'web-tree-sitter';

const [manifestPath, outPath] = process.argv.slice(2);
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const version = JSON.parse(readFileSync(new URL('../../node_modules/web-tree-sitter/package.json', import.meta.url), 'utf8')).version;

let t0 = process.hrtime.bigint();
const buffers = manifest.files.map((f) => readFileSync(f));
const readSeconds = Number(process.hrtime.bigint() - t0) / 1e9;

await Parser.init();
const parser = new Parser();
parser.setLanguage(await Language.load(manifest.wasm));

const lenient = new TextDecoder('utf-8', { ignoreBOM: true });
const strict = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
const invalid = [];
buffers.forEach((b, i) => { try { strict.decode(b); } catch { invalid.push(i); } });

function pass(record) {
  const ns = [], errors = [];
  for (const b of buffers) {
    const text = lenient.decode(b);
    const t = process.hrtime.bigint();
    const tree = parser.parse(text);
    ns.push(Number(process.hrtime.bigint() - t));
    if (record) errors.push(tree.rootNode.hasError);
    tree.delete();
  }
  return { ns, errors };
}

const warm = pass(true);
const runs = [];
for (let r = 0; r < manifest.repeats; r++) {
  process.stderr.write(`perf: wasm pass ${r + 1}/${manifest.repeats}\n`);
  runs.push(pass(false).ns);
}
writeFileSync(outPath, JSON.stringify({
  web_tree_sitter: version, read_seconds: readSeconds, invalid_utf8: invalid,
  has_error: warm.errors, ns: runs,
}));
