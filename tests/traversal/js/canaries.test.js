'use strict';
// Consumer canaries (spec 6.2 item 3, roadmap F0). Each one reproduces a consumer's
// ACTUAL rule, cited by file:line (.superpowers/sdd/a7/consumers.md), shows the
// failure on the naive walk (`before`), and the same question answered on F0 (`after`).
// F0 enables the fixes; it does not perform them in the consumers' repos.
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const REPO = path.resolve(__dirname, '..', '..', '..');
const FIX = path.join(REPO, 'tests', 'traversal', 'fixtures');
const T = require(path.join(REPO, 'traversal'));
const { Parser, Language } = require('module').createRequire(path.join(REPO, 'package.json'))('web-tree-sitter');

let parser;
const policy = T.loadPolicy();

test.before(async () => {
  await Parser.init();
  parser = new Parser();
  parser.setLanguage(await Language.load(path.join(REPO, 'tree-sitter-al.wasm')));
});

function load(name) {
  const text = fs.readFileSync(path.join(FIX, name), 'utf8');
  const tree = parser.parse(text);
  return { text, tree, doc: new T.Document(tree, text, policy) };
}

const textOf = (doc, n) => doc.text.slice(n.startIndex, n.endIndex);

// A split construct that is a procedure in every arm: each arm carries a
// procedure_keyword fragment and a `name` fragment. Consumer-side recognition
// over SplitInfo, not an F0 API: F0 hands over the arms, the consumer decides.
function splitNames(split, keyword, nameField, doc) {
  const names = [];
  for (const g of split.groups) {
    for (const a of g.arms) {
      const kw = a.fragments.some((f) => f.node.type === keyword);
      const name = a.fragments.find((f) => f.field === nameField);
      if (!kw || !name) return null;
      names.push(textOf(doc, name.node));
    }
  }
  return names.length ? names : null;
}

// ---------------------------------------------------------------------------
// DevOpsWorker: scripts/al-symbol/resolver.ts:86-97 (aceea15), verbatim.
function procedureNodes(root) {
  const result = [];
  function recurse(n) {
    if (n.type === 'procedure') { result.push(n); return; }
    for (let i = 0; i < n.namedChildCount; i++) recurse(n.namedChild(i));
  }
  recurse(root);
  return result;
}

test('DevOpsWorker: a split procedure is invisible to findDefinition before F0', () => {
  const { tree, doc } = load('assemblers.al');
  const before = procedureNodes(tree.rootNode).map((n) => textOf(doc, n.childForFieldName('name')));
  assert.deepStrictEqual(before, ['First', 'Tail', 'CaseEnd']);

  const after = [];
  for (const v of T.walk(doc, policy)) {
    if (v.type === 'procedure') after.push(textOf(doc, v.node.childForFieldName('name')));
    else if (v.cls === 'assembler' && v.split) {
      const names = splitNames(v.split, 'procedure_keyword', 'name', doc);
      if (names) after.push(...new Set(names));
    }
  }
  assert.deepStrictEqual(after, ['First', 'Split', 'Tail', 'CaseEnd']);
});

// ---------------------------------------------------------------------------
// al-differ: src/engine/walker.ts (5590605). MATCHABLE_TYPES :10-61 and
// CONTAINER_TYPES :63-136 are the subsets this fixture can reach; collectMatchable
// :185-195 is verbatim; callers :288 and :423 recurse into each matched node.
const MATCHABLE_TYPES = new Set(['codeunit_declaration', 'procedure', 'trigger_declaration', 'property',
  'variable_declaration', 'field_declaration']);
const CONTAINER_TYPES = new Set(['fields_section', 'var_section', 'declaration_body', 'fields_body', 'var_body']);

function collectMatchable(parent) {
  const results = [];
  for (const child of parent.namedChildren) {
    if (MATCHABLE_TYPES.has(child.type)) results.push(child);
    else if (CONTAINER_TYPES.has(child.type)) results.push(...collectMatchable(child));
  }
  return results;
}

function allMatchable(root) {
  const out = [];
  for (const m of collectMatchable(root)) out.push(m, ...allMatchable(m));
  return out;
}

const nameOf = (doc, n) => {
  const f = n.childForFieldName('name') || n.childForFieldName('object_name');
  return f ? textOf(doc, f) : null;
};

test('al-differ: definitions in every conditional arm, and through split declarations', () => {
  const c = load('containers.al');
  assert.deepStrictEqual(allMatchable(c.tree.rootNode), [], 'before: #if content is absent from the diff');

  const after = T.walk(c.doc, policy).filter((v) => MATCHABLE_TYPES.has(v.type) && v.type !== 'variable_declaration')
    .map((v) => [v.type, nameOf(c.doc, v.node), v.arms.map(([g, a]) => `${g}/${a}`).join(' ')]);
  assert.deepStrictEqual(after, [
    ['codeunit_declaration', '"Containers Æ"', '93/0'],
    ['codeunit_declaration', '"Containers Ø"', '93/1'],
    ['procedure', 'A', '93/1 179/0'],
    ['procedure', 'B', '93/1 179/1'],
    ['procedure', 'C', '93/1 179/2'],
    ['procedure', 'Stmts', '93/1'],
  ]);

  const s = load('split_declaration.al');
  assert.deepStrictEqual(allMatchable(s.tree.rootNode), [], 'before: a split declaration hides its object');
  const decl = T.walk(s.doc, policy).find((v) => v.type === 'preproc_split_declaration');
  assert.deepStrictEqual(splitNames(decl.split, 'codeunit_keyword', 'object_name', s.doc), ['"Test Impl"', '"Test Impl"']);
  const body = decl.split.shared.find((f) => f.field === 'body').node;
  assert.deepStrictEqual(T.walk(s.doc, policy, { root: body }).filter((v) => v.type === 'procedure')
    .map((v) => nameOf(s.doc, v.node)), ['TestMethod']);
});

// ---------------------------------------------------------------------------
// LethAL R214 part 1: packages/engine/src/ast/tree-walks.ts (19b70fc5).
// isStatementPosition :33-37, SINGLE_STATEMENT_SLOTS :47-62, isStatementSlot :81-86. The
// mutation-site rule is the operators' gate on it: packages/builtin-tier1/src/void-method-call.ts:19-24
// (`call_expression`, node-kinds.ts:103) and remove-assignment.ts:67-72 (`assignment_statement`).
// ALNodeKind.block is the raw kind "code_block" (node-kinds.ts:56).
const SINGLE_STATEMENT_SLOTS = new Set(['if_statement.then_branch', 'if_statement.else_branch', 'case_branch.body',
  'while_statement.body', 'for_statement.body', 'foreach_statement.body',
  'preproc_split_if_statement.then_branch', 'preproc_split_if_statement.else_branch',
  'preproc_split_if_else_statement.then_branch', 'preproc_split_if_else_statement.else_branch',
  'preproc_split_case_extended.body']);

function fieldOf(node) {
  const p = node.parent;
  if (!p) return null;
  for (let i = 0; i < p.childCount; i++) if (p.child(i).id === node.id) return p.fieldNameForChild(i) || null;
  return null;
}

function isStatementSlot(node, field) {
  const parent = node.parent;
  if (parent === null) return false;
  if (parent.type === 'statement_block' || parent.type === 'code_block') return true;
  if (field === null) return false;
  return SINGLE_STATEMENT_SLOTS.has(`${parent.type}.${field}`);
}

// The rewrite on F0: a branch container splices its arm into its OWN host slot,
// so the slot question is asked of the container, climbing nested containers.
function isStatementSlotF0(visit) {
  let node = visit.node;
  let field = visit.field;
  while (node.parent && policy.cls(node.parent.type) === 'branch-container') {
    node = node.parent;
    field = fieldOf(node);
  }
  return isStatementSlot(node, field);
}

const SITE_TYPES = new Set(['call_expression', 'assignment_statement']);

test('LethAL R214 part 1: statements under conditional parents pass site selection', () => {
  const { tree, doc } = load('containers.al');
  const stmts = T.walk(doc, policy).find((v) => v.type === 'procedure' && nameOf(doc, v.node) === 'Stmts');
  const visits = T.walk(doc, policy, { root: stmts.node }).filter((v) => SITE_TYPES.has(v.type));

  const before = visits.filter((v) => isStatementSlot(v.node, fieldOf(v.node))).map((v) => textOf(doc, v.node));
  assert.deepStrictEqual(before, ["Message('control')"], 'before: every site inside #if is lost');

  const after = visits.filter(isStatementSlotF0).map((v) => [textOf(doc, v.node), v.arms.map(([g, a]) => `${g}/${a}`).join(' ')]);
  assert.deepStrictEqual(after, [
    ["Message('control')", '93/1'],
    ['DoThing(X)', '93/1 441/0'],
    ['X := 1', '93/1 441/0'],
    ['X := 3', '93/1 441/0 489/0'],
    ['X := 4', '93/1 441/1'],
    ['X := 2', '93/1 441/2'],
  ]);
  assert.ok(tree.rootNode, 'tree kept alive for the visits above');
});

// Statements an assembler holds directly -- an arm piece or a shared part -- are
// statements when the assembler itself fills a statement slot. SplitInfo says which
// pieces those are; the parent-type check never could.
function assemblerStatementSites(v) {
  if (v.cls !== 'assembler' || !v.split || !isStatementSlotF0(v)) return [];
  const pieces = [...v.split.groups.flatMap((g) => g.arms.flatMap((a) => a.fragments)), ...v.split.shared];
  return pieces.filter((f) => f.field === null && SITE_TYPES.has(f.node.type)).map((f) => f.node);
}

test('LethAL R214 part 1: statements held by a split construct are found through SplitInfo', () => {
  const { doc } = load('assemblers.al');
  const visits = T.walk(doc, policy);
  const held = visits.filter((v) => SITE_TYPES.has(v.type) && policy.cls(v.node.parent.type) === 'assembler');
  assert.deepStrictEqual(held.map((v) => textOf(doc, v.node)), ["Message('a')", "Message('b')"]);
  assert.deepStrictEqual(held.filter((v) => isStatementSlot(v.node, v.field)), [], 'before: both are lost');
  const after = visits.flatMap(assemblerStatementSites).map((n) => textOf(doc, n));
  assert.deepStrictEqual(after, ["Message('a')", "Message('b')"]);
});
