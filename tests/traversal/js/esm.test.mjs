// The documented subpath from an ES module (final review I1): without an `exports` map,
// `import '@sshadows/tree-sitter-al/traversal'` threw ERR_UNSUPPORTED_DIR_IMPORT. The
// package resolves itself by name (self-reference), through the same exports map a
// consumer gets.
import test from 'node:test';
import assert from 'node:assert';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

test('the traversal entry imports from an ES module, by its documented subpath', async () => {
  const T = await import('@sshadows/tree-sitter-al/traversal');
  assert.strictEqual(typeof T.walk, 'function');   // CommonJS named exports are detected
  const { Parser, Language } = await import('web-tree-sitter');
  await Parser.init();
  const p = new Parser();
  p.setLanguage(await Language.load(require.resolve('@sshadows/tree-sitter-al/tree-sitter-al.wasm')));
  const text = 'codeunit 1 C\n{\n#if A\n    procedure P()\n    begin\n    end;\n#endif\n}\n';
  const policy = T.loadPolicy();
  const doc = new T.Document(p.parse(text), text, policy);
  const v = T.walk(doc, policy).find((x) => x.type === 'preproc_conditional');
  assert.strictEqual(v.cls, 'branch-container');
});

test('the main entry and bindings/node still import, and old deep paths resolve', async () => {
  const main = await import('@sshadows/tree-sitter-al');
  assert.strictEqual(main.default, (await import('@sshadows/tree-sitter-al/bindings/node')).default);
  assert.ok(main.default.nodeTypeInfo);
  for (const s of ['@sshadows/tree-sitter-al/traversal/index.js', '@sshadows/tree-sitter-al/traversal/policy.json',
    '@sshadows/tree-sitter-al/src/node-types.json', '@sshadows/tree-sitter-al/package.json']) {
    assert.ok(require.resolve(s), s);
  }
});
