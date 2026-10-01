'use strict';
// Classified traversal over the all-branches AL tree (roadmap F0, spec 5.1 and 6).
//
// ONE implementation for both JS runtimes: it touches only the SyntaxNode API
// that the native `tree-sitter` binding and `web-tree-sitter` share (type,
// isNamed, startIndex, endIndex, childCount, child(i), fieldNameForChild(i),
// parent, id). It never requires the native addon, so it is browser-safe.
//
// Both runtimes index the source as UTF-16 code units. Every position this
// module reports is a canonical UTF-8 byte offset, converted from the text.
// Node classes come from the hand-maintained policy.json, never from a name.

const BUNDLED = require('./policy.json');

const SCHEMA = 1;
const CLASSES = ['ordinary', 'branch-container', 'assembler', 'fragment', 'token-alias', 'directive', 'trivia'];
// Only these get a SplitInfo on their visit (see the Python module).
const SPLIT_CLASSES = ['branch-container', 'assembler', 'fragment'];

class PolicyError extends Error {}
class WrongDocument extends Error {}

class Policy {
  constructor(types) { this.types = types; }
  cls(type) { const e = this.types[type]; return e ? e.class : 'ordinary'; }
  role(type) { const e = this.types[type]; return (e && e.role) || null; }
  hostPolicy(container, parent, field) {
    const e = this.types[container];
    const hosts = (e && e.hosts) || {};
    const p = hosts[`${parent}:${field || '<children>'}`];
    return p === undefined ? null : p;
  }
}

function loadPolicy(data = BUNDLED) {
  if (data.schema !== SCHEMA) throw new PolicyError(`policy schema ${data.schema}, expected ${SCHEMA}`);
  for (const [type, entry] of Object.entries(data.types)) {
    if (!CLASSES.includes(entry.class)) throw new PolicyError(`${type}: unknown class ${entry.class}`);
  }
  return new Policy(data.types);
}

function fnv1a64(bytes) {
  let h = 0xcbf29ce484222325n;
  for (const b of bytes) h = ((h ^ BigInt(b)) * 0x100000001b3n) & 0xffffffffffffffffn;
  return h.toString(16).padStart(16, '0');
}

// UTF-16 index -> UTF-8 byte offset, for every index 0..text.length.
function byteTable(text) {
  const t = new Uint32Array(text.length + 1);
  let b = 0;
  let i = 0;
  while (i < text.length) {
    t[i] = b;
    const c = text.charCodeAt(i);
    if (c >= 0xd800 && c <= 0xdbff && i + 1 < text.length) {
      const d = text.charCodeAt(i + 1);
      if (d >= 0xdc00 && d <= 0xdfff) { t[i + 1] = b; b += 4; i += 2; continue; }
    }
    b += c < 0x80 ? 1 : c < 0x800 ? 2 : 3;
    i += 1;
  }
  t[text.length] = b;
  return t;
}

function kids(node) {
  const out = [];
  for (let i = 0; i < node.childCount; i++) out.push([node.fieldNameForChild(i) || null, node.child(i)]);
  return out;
}

class Document {
  constructor(tree, text, policy) {
    this.tree = tree;
    this.text = text;
    this.bytes = byteTable(text);
    this.revision = fnv1a64(new TextEncoder().encode(text));
    const { groups, unpaired, byParent } = pair(this, policy);
    this.groups = groups;
    this.unpaired = unpaired;
    this.byParent = byParent;
  }
  start(node) { return this.bytes[node.startIndex]; }
  // UTF-8 byte offset -> the first UTF-16 index at or after it (binary search).
  index(byte) {
    let lo = 0;
    let hi = this.text.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (this.bytes[mid] < byte) lo = mid + 1; else hi = mid;
    }
    return lo;
  }
  end(node) { return this.bytes[node.endIndex]; }
  descriptors() { return this.groups.flatMap((g) => g.arms); }
}

function pair(doc, policy) {
  const open = [];
  const done = [];
  const unpaired = [];
  // parent id -> ordered set of '#if' offsets. The parent id rides on the stack:
  // calling .parent per directive and scanning a list were both quadratic.
  const byParentOffsets = new Map();
  const stack = [[doc.tree.rootNode, null]];
  while (stack.length) {
    const [node, pid] = stack.pop();
    const role = node.isNamed ? policy.role(node.type) : null;
    if (role === null) {
      for (let i = node.childCount - 1; i >= 0; i--) stack.push([node.child(i), node.id]);
      continue;
    }
    const d = { role, start: doc.start(node), end: doc.end(node), node };
    if (role === 'if') open.push([d]);
    else if (!open.length) { unpaired.push(d); continue; } else open[open.length - 1].push(d);
    const group = open[open.length - 1];
    if (!byParentOffsets.has(pid)) byParentOffsets.set(pid, new Set());
    byParentOffsets.get(pid).add(group[0].start);
    if (role === 'endif') done.push(open.pop());
  }
  done.push(...open);
  done.sort((a, b) => a[0].start - b[0].start);
  const eof = doc.bytes[doc.text.length];
  const byIf = new Map();
  for (const ds of done) {
    const arms = [];
    ds.forEach((d, idx) => {
      if (d.role === 'endif') return;
      const closer = idx + 1 < ds.length ? ds[idx + 1] : null;
      const end = closer ? closer.start : eof;
      // The first byte after the newline ending the directive's line, or EOF. #if/#elif
      // nodes end after their newline and #else before it; every arm starts here, so a
      // trailing comment on any directive line is outside the arm (spec 3.3).
      const nl = doc.text.indexOf('\n', Math.max(d.node.endIndex - 1, 0));
      const lineEnd = doc.bytes[nl < 0 ? doc.text.length : nl + 1];
      arms.push({
        groupId: [doc.revision, ds[0].start],
        armId: arms.length,
        directiveOffsets: closer ? [d.start, closer.start] : [d.start],
        rawRange: [Math.min(lineEnd, end), end], // min: a MISSING #endif can sit before the newline
      });
    });
    byIf.set(ds[0].start, { ifOffset: ds[0].start, directives: ds, arms });
  }
  const byParent = new Map();
  for (const [pid, offs] of byParentOffsets) byParent.set(pid, [...offs].map((o) => byIf.get(o)));
  return { groups: [...byIf.values()], unpaired, byParent };
}

function groupsOf(node, doc) { return doc.byParent.get(node.id) || []; }

function bindArm(descriptor, doc, policy) {
  if (descriptor.groupId[0] !== doc.revision) {
    throw new WrongDocument(`descriptor revision ${descriptor.groupId[0]} != document ${doc.revision}`);
  }
  const [lo, hi] = descriptor.rawRange;
  const out = [];
  // Start at the smallest node holding the whole arm (see the Python module).
  let top = doc.tree.rootNode.descendantForIndex(doc.index(lo), doc.index(hi)) || doc.tree.rootNode;
  while (top.parent && lo <= doc.start(top) && doc.end(top) <= hi) top = top.parent;
  const stack = [[top, null]];
  while (stack.length) {
    const [node, field] = stack.pop();
    const s = doc.start(node);
    const e = doc.end(node);
    if (e <= lo || s >= hi) continue;
    if (lo <= s && e <= hi) {
      if (!(node.isNamed && policy.cls(node.type) === 'directive')) out.push({ field, node });
      continue;
    }
    const ks = kids(node);
    for (let i = ks.length - 1; i >= 0; i--) stack.push([ks[i][1], ks[i][0]]);
  }
  return { descriptor, fragments: out };
}

// An arm's fragments with every `fragment`-class piece replaced, in place and
// recursively, by its own children (field names kept, anonymous tokens kept). A
// fragment wholly inside one arm gets no SplitInfo of its own; this reaches inside it.
function armPieces(armFragments, doc, policy) {
  const d = armFragments.descriptor;
  if (d.groupId[0] !== doc.revision) throw new WrongDocument(`descriptor revision ${d.groupId[0]} != document ${doc.revision}`);
  const out = [];
  const add = (pieces) => {
    for (const f of pieces) {
      if (f.node.isNamed && policy.cls(f.node.type) === 'fragment') add(kids(f.node).map(([field, node]) => ({ field, node })));
      else out.push(f);
    }
  };
  add(armFragments.fragments);
  return out;
}

function splitInfo(node, doc, policy) {
  const groups = groupsOf(node, doc);
  if (!groups.length) return null;
  const ranges = groups.flatMap((g) => g.arms.map((a) => a.rawRange));
  // an arm's directive line, '#' to the arm start: a trailing comment there is the directive's
  for (const g of groups) for (const a of g.arms) ranges.push([a.directiveOffsets[0], a.rawRange[0]]);
  const shared = [];
  for (const [field, child] of kids(node)) {
    if (child.isNamed && policy.cls(child.type) === 'directive') continue;
    const s = doc.start(child);
    const e = doc.end(child);
    if (ranges.some(([lo, hi]) => lo <= s && e <= hi)) continue;
    shared.push({ field, node: child });
  }
  return {
    groups: groups.map((g) => ({ groupId: [doc.revision, g.ifOffset], arms: g.arms.map((a) => bindArm(a, doc, policy)) })),
    shared,
  };
}

function walk(doc, policy, { root = null, includeDirectives = false, includeTrivia = false } = {}) {
  const arms = doc.descriptors().slice().sort((a, b) => (a.rawRange[0] - b.rawRange[0]) || (b.rawRange[1] - a.rawRange[1]));
  let active = [];
  let k = 0;
  const out = [];
  // A subtree root keeps its real parent and field, so a branch container walked
  // directly reports the same host and field as it does in a full walk.
  const start0 = root || doc.tree.rootNode;
  const parent0 = start0.parent || null;
  let field0 = null;
  if (parent0) {
    for (let i = 0; i < parent0.childCount; i++) {
      if (parent0.child(i).id === start0.id) { field0 = parent0.fieldNameForChild(i) || null; break; }
    }
  }
  const stack = [[start0, field0, parent0]];
  while (stack.length) {
    const [node, field, parent] = stack.pop();
    if (!node.isNamed) continue;
    const cls = policy.cls(node.type);
    if ((cls === 'directive' && !includeDirectives) || (cls === 'trivia' && !includeTrivia)) continue;
    const start = doc.start(node);
    const end = doc.end(node);
    while (k < arms.length && arms[k].rawRange[0] <= start) active.push(arms[k++]);
    active = active.filter((a) => a.rawRange[1] > start);
    const path = active.filter((a) => a.rawRange[1] >= end).map((a) => [a.groupId[1], a.armId]);
    const host = cls === 'branch-container' && parent ? policy.hostPolicy(node.type, parent.type, field) : null;
    out.push({ node, cls, type: node.type, field, start, end, arms: path, host, split: SPLIT_CLASSES.includes(cls) ? splitInfo(node, doc, policy) : null });
    const ks = kids(node);
    for (let i = ks.length - 1; i >= 0; i--) stack.push([ks[i][1], ks[i][0], node]);
  }
  return out;
}

function fragJson(f, doc) { return [f.field, f.node.type, f.node.isNamed, doc.start(f.node), doc.end(f.node)]; }

function splitToJson(s, doc) {
  return {
    groups: s.groups.map((g) => ({
      if: g.groupId[1],
      arms: g.arms.map((a) => ({ arm: a.descriptor.armId, range: [...a.descriptor.rawRange], fragments: a.fragments.map((f) => fragJson(f, doc)) })),
    })),
    shared: s.shared.map((f) => fragJson(f, doc)),
  };
}

function visitsToJson(visits, doc) {
  return visits.map((v) => ({
    class: v.cls, type: v.type, field: v.field, start: v.start, end: v.end,
    arms: v.arms, host: v.host, split: v.split ? splitToJson(v.split, doc) : null,
  }));
}

module.exports = {
  SCHEMA, CLASSES, SPLIT_CLASSES, PolicyError, WrongDocument, Policy, loadPolicy, fnv1a64, byteTable,
  Document, groupsOf, bindArm, armPieces, splitInfo, walk, visitsToJson,
};
