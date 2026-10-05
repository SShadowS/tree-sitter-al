'use strict';
// The ONE JS implementation (traversal/index.js) under BOTH JS runtimes, against the
// expected-visit files the Python walker wrote (D4, D5). Run: node --test tests/traversal/js/
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const REPO = path.resolve(__dirname, '..', '..', '..');
const FIX = path.join(REPO, 'tests', 'traversal', 'fixtures');
const T = require(path.join(REPO, 'traversal'));
const req = require('node:module').createRequire(path.join(REPO, 'package.json'));

const FIXTURES = fs.readdirSync(FIX).filter((f) => f.endsWith('.al')).sort();
const policy = T.loadPolicy();
const parsers = {};

test.before(async () => {
  const { Parser, Language } = req('web-tree-sitter');
  await Parser.init();
  const web = new Parser();
  web.setLanguage(await Language.load(path.join(REPO, 'tree-sitter-al.wasm')));
  parsers['web-tree-sitter'] = web;
  const Native = req('tree-sitter');
  const native = new Native();
  native.setLanguage(require(path.join(REPO, 'bindings', 'node')));
  parsers['native tree-sitter'] = native;
});

test('there are fourteen fixtures, each with an expected-visits file', () => {
  assert.strictEqual(FIXTURES.length, 14);
  for (const f of FIXTURES) assert.ok(fs.existsSync(path.join(FIX, f.replace(/\.al$/, '.visits.json'))), f);
});

for (const runtime of ['web-tree-sitter', 'native tree-sitter']) {
  for (const f of FIXTURES) {
    test(`${runtime}: ${f} matches its expected visits`, () => {
      const text = fs.readFileSync(path.join(FIX, f), 'utf8');
      const want = JSON.parse(fs.readFileSync(path.join(FIX, f.replace(/\.al$/, '.visits.json')), 'utf8'));
      const doc = new T.Document(parsers[runtime].parse(text), text, policy);
      const got = { revision: doc.revision, visits: T.visitsToJson(T.walk(doc, policy), doc) };
      // A native mismatch with a clean web run is almost always a STALE native build
      // (build/Release predates src/): rebuild with `npx node-gyp rebuild`.
      assert.deepStrictEqual(got, want);
    });
  }
}

for (const runtime of ['web-tree-sitter', 'native tree-sitter']) {
  test(`${runtime}: assemblers.al matches its expected arm pieces`, () => {
    const text = fs.readFileSync(path.join(FIX, 'assemblers.al'), 'utf8');
    const want = JSON.parse(fs.readFileSync(path.join(FIX, 'assemblers.arm_pieces.json'), 'utf8'));
    const doc = new T.Document(parsers[runtime].parse(text), text, policy);
    const arms = [];
    for (const v of T.walk(doc, policy)) {
      if (!v.split) continue;
      for (const g of v.split.groups) {
        for (const a of g.arms) {
          arms.push({ type: v.type, start: v.start, if: g.groupId[1], arm: a.descriptor.armId,
            pieces: T.armPieces(a, doc, policy).map((f) => [f.field, f.node.type, f.node.isNamed, doc.start(f.node), doc.end(f.node)]) });
        }
      }
    }
    assert.deepStrictEqual({ revision: doc.revision, arms }, want);
  });
}

for (const runtime of ['web-tree-sitter', 'native tree-sitter']) {
  // Ports of the two Python fixes that came after the plan (Task 2 rulings).
  test(`${runtime}: a subtree walk's root visit equals its full-walk visit`, () => {
    const text = fs.readFileSync(path.join(FIX, 'containers.al'), 'utf8');
    const doc = new T.Document(parsers[runtime].parse(text), text, policy);
    const containers = T.walk(doc, policy).filter((v) => v.cls === 'branch-container');
    assert.ok(containers.length && containers.every((v) => v.host !== null));
    for (const v of containers) {
      const sub = T.walk(doc, policy, { root: v.node })[0];
      assert.deepStrictEqual(T.visitsToJson([sub], doc), T.visitsToJson([v], doc));
    }
  });

  test(`${runtime}: walk also visits an assembler's arm pieces (dedupe by node id)`, () => {
    const text = fs.readFileSync(path.join(FIX, 'assemblers.al'), 'utf8');
    const doc = new T.Document(parsers[runtime].parse(text), text, policy);
    const visits = T.walk(doc, policy);
    const byId = new Map(visits.map((v) => [v.node.id, v]));
    const v = visits.find((x) => x.type === 'preproc_split_procedure');
    for (const g of v.split.groups) {
      for (const a of g.arms) {
        const named = a.fragments.filter((f) => f.node.isNamed);
        assert.ok(named.length);
        for (const f of named) {
          assert.ok(byId.has(f.node.id), f.node.type);
          assert.deepStrictEqual(byId.get(f.node.id).arms.at(-1), [g.groupId[1], a.descriptor.armId]);
        }
      }
    }
  });

  test(`${runtime}: armPieces never keeps a directive of an expanded fragment (policy override)`, () => {
    // See the Python test: no grammar fixture can trigger it, so the nested statement
    // conditional of containers.al (#if at 489, in arm 0 of 441) is made a fragment.
    const text = fs.readFileSync(path.join(FIX, 'containers.al'), 'utf8');
    const over = T.loadPolicy({ schema: 1, types: { ...policy.types, preproc_conditional_statement: { class: 'fragment' } } });
    const doc = new T.Document(parsers[runtime].parse(text), text, over);
    const outer = doc.groups.find((g) => g.ifOffset === 441);
    const arm = T.bindArm(outer.arms[0], doc, over);
    assert.ok(arm.fragments.some((f) => doc.start(f.node) === 489));
    const pieces = T.armPieces(arm, doc, over);
    assert.deepStrictEqual(pieces.filter((f) => f.node.isNamed && over.cls(f.node.type) === 'directive').map((f) => f.node.type), []);
    assert.deepStrictEqual(pieces.filter((f) => f.node.type === 'assignment_statement').map((f) => f.node.text), ['X := 1', 'X := 3']);
  });

  test(`${runtime}: an unclosed #else on the last line has an empty arm, never an inverted one`, () => {
    for (const [src, want] of [['codeunit 1 C\n{\n}\n#if A\n#else', [28, 28]], ['codeunit 1 C\n{\n}\n#if A\n#else // c', [33, 33]],
      ['codeunit 1 C\n{\n}\n#if A\n#else\n', [28, 28]], ['codeunit 1 C\r\n{\r\n}\r\n#if A\r\n#else\r\n', [32, 32]]]) {
      const doc = new T.Document(parsers[runtime].parse(src), src, policy);
      assert.deepStrictEqual(doc.groups[0].arms[1].rawRange, want, JSON.stringify(src));
    }
  });

  test(`${runtime}: pairing and walking are linear in the number of groups, and iterative`, () => {
    let groups = '';
    for (let i = 0; i < 2000; i++) {
      groups += `#if C${i}\n    procedure P${i}()\n    begin\n        X := ${i};\n    end;\n#else\n`
        + `    procedure Q${i}()\n    begin\n    end;\n#endif\n`;
    }
    const src = `codeunit 50100 Big\n{\n${groups}}\n`;
    const t0 = performance.now();
    const doc = new T.Document(parsers[runtime].parse(src), src, policy);   // construction is timed too
    const visits = T.walk(doc, policy);
    assert.ok(performance.now() - t0 < 3000, 'pairing or walk is quadratic in the number of groups again');
    assert.strictEqual(doc.groups.length, 2000);
    assert.strictEqual(visits.filter((v) => v.type === 'procedure').length, 4000);
    const deep = `codeunit 1 D\n{\n procedure P()\n begin\n  X := ${'('.repeat(5000)}1${')'.repeat(5000)};\n end;\n}\n`;
    const d2 = new T.Document(parsers[runtime].parse(deep), deep, policy);
    assert.ok(T.walk(d2, policy).length > 5000);   // no stack overflow
  });
}

// B11 witness (spec 5.5): a value sequence owns no directives; each of its groups
// carries its own split, with its arms.
for (const runtime of ['web-tree-sitter', 'native tree-sitter']) {
  test(`${runtime}: every group of a value sequence carries its own split`, () => {
    const text = fs.readFileSync(path.join(FIX, 'value_run.al'), 'utf8');
    const doc = new T.Document(parsers[runtime].parse(text), text, policy);
    const visits = T.walk(doc, policy);
    const seq = visits.filter((v) => v.type === 'preproc_conditional_property_value_sequence');
    assert.strictEqual(seq.length, 1);
    assert.strictEqual(seq[0].split, null);
    const groups = visits.filter((v) => v.type === 'preproc_conditional_property_value');
    const arm = (lit) => [[['value', 'string_literal', lit], [null, ';', ';']]];
    assert.deepStrictEqual(groups.map((v) => v.split.groups[0].arms.map((a) => a.fragments.map(
      (f) => [f.field, f.node.type, text.slice(f.node.startIndex, f.node.endIndex)]))), [arm("'a'"), arm("'b'")]);
  });
}

test('fnv1a64 reference vectors', () => {
  assert.strictEqual(T.fnv1a64(new Uint8Array([])), 'cbf29ce484222325');
  assert.strictEqual(T.fnv1a64(new TextEncoder().encode('a')), 'af63dc4c8601ec8c');
});

test('byteTable maps UTF-16 indexes to UTF-8 byte offsets, surrogate pairs included', () => {
  assert.deepStrictEqual(Array.from(T.byteTable('a\u{1F600}é')), [0, 1, 1, 5, 7]);
  assert.deepStrictEqual(Array.from(T.byteTable('\ud800a')), [0, 3, 4]); // lone surrogate = U+FFFD, 3 bytes
});

test('loadPolicy rejects an unknown schema or class', () => {
  assert.throws(() => T.loadPolicy({ schema: 2, types: {} }), T.PolicyError);
  assert.throws(() => T.loadPolicy({ schema: 1, types: { x: { class: 'special' } } }), T.PolicyError);
});

test('bindArm rejects a descriptor from another document', () => {
  const p = parsers['web-tree-sitter'];
  const read = (f) => fs.readFileSync(path.join(FIX, f), 'utf8');
  const a = new T.Document(p.parse(read('containers.al')), read('containers.al'), policy);
  const b = new T.Document(p.parse(read('elif_chain.al')), read('elif_chain.al'), policy);
  assert.throws(() => T.bindArm(a.descriptors()[0], b, policy), T.WrongDocument);
});

test('the traversal module never loads the native addon', () => {
  const src = fs.readFileSync(path.join(REPO, 'traversal', 'index.js'), 'utf8');
  assert.deepStrictEqual(src.match(/require\([^)]*\)/g), ["require('./policy.json')"]);
});
