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
// :185-195 is verbatim; it is called at :288-289 (diffChildren) and :423-424 (walkRoots).
// allMatchable is NOT al-differ's recursion: al-differ descends only into matched
// pairs (walkPair :238-245; makeAdded/makeDeleted give children: []), while this
// descends into every match. It over-approximates what al-differ can see, so an
// empty `before` here is empty in al-differ too.
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

  const after = T.walk(c.doc, policy).filter((v) => MATCHABLE_TYPES.has(v.type))
    .map((v) => [v.type, nameOf(c.doc, v.node), v.arms.map(([g, a]) => `${g}/${a}`).join(' ')]);
  assert.deepStrictEqual(after, [
    ['codeunit_declaration', '"Containers Æ"', '93/0'],
    ['codeunit_declaration', '"Containers Ø"', '93/1'],
    ['procedure', 'A', '93/1 179/0'],
    ['procedure', 'B', '93/1 179/1'],
    ['procedure', 'C', '93/1 179/2'],
    ['procedure', 'Stmts', '93/1'],
    ['variable_declaration', 'X', '93/1'],
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
// The fields LethAL already treats as holding one statement (SINGLE_STATEMENT_SLOTS' field half).
const STATEMENT_FIELDS = new Set([...SINGLE_STATEMENT_SLOTS].map((s) => s.split('.')[1]));

// Statements a split construct holds -- an arm piece or a shared part of an assembler,
// or a piece of a fragment in one of its arms (T.armPieces expands those) -- are
// statements when the assembler itself fills a statement slot. SplitInfo says which
// pieces those are; the parent-type check never could.
function splitStatementSites(v, doc) {
  if (v.cls !== 'assembler' || !v.split || !isStatementSlotF0(v)) return [];
  const pieces = [...v.split.groups.flatMap((g) => g.arms.flatMap((a) => T.armPieces(a, doc, policy))), ...v.split.shared];
  return pieces.filter((f) => (f.field === null || STATEMENT_FIELDS.has(f.field)) && SITE_TYPES.has(f.node.type))
    .map((f) => f.node);
}

// EVERY call and assignment the walk reaches in the fixture, never a filtered subset:
// [text, arm path, selected by LethAL's rule as it is, selected by the F0 rewrite].
function siteTable(name) {
  const { doc } = load(name);
  const visits = T.walk(doc, policy);
  const held = new Set(visits.flatMap((v) => splitStatementSites(v, doc)).map((n) => n.id));
  return visits.filter((v) => SITE_TYPES.has(v.type)).map((v) => [
    textOf(doc, v.node).split(/\r?\n/)[0],
    v.arms.map(([g, a]) => `${g}/${a}`).join(' '),
    isStatementSlot(v.node, fieldOf(v.node)),
    isStatementSlotF0(v) || held.has(v.node.id),
  ]);
}

test('LethAL R214 part 1: statements under conditional parents pass site selection', () => {
  assert.deepStrictEqual(siteTable('containers.al'), [
    ["Message('å')", '93/1 179/0', true, true],
    ["Message('control')", '93/1', true, true],
    ['DoThing(X)', '93/1 441/0', false, true],
    ['X := 1', '93/1 441/0', false, true],
    ['X := 3', '93/1 441/0 489/0', false, true],
    ['X := 4', '93/1 441/1', false, true],
    ['X := 2', '93/1 441/2', false, true],
  ]);
});

// Message('a') and Message('b') are held by an assembler (preproc_split_if_then_begin);
// Message('two') and Message('deux') sit in the `body` of a fragment
// (preproc_split_case_end_branch) inside one (preproc_split_case_statement_end).
// No site in this fixture needs configuration to decide; none is out of scope.
test('LethAL R214 part 1: statements held by a split construct are found through SplitInfo', () => {
  assert.deepStrictEqual(siteTable('assemblers.al'), [
    ["Message('x')", '', true, true],
    ['X := X', '', true, true],
    ["Message('a')", '539/0', false, true],
    ["Message('b')", '', false, true],
    ["Message('one')", '', true, true],
    ["Message('two')", '899/0', false, true],
    ["Message('after a')", '899/0', true, true],
    ["Message('deux')", '899/1', false, true],
    ["Message('after b')", '899/1', true, true],
  ]);
});
