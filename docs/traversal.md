# Walking `#if` code: the classified traversal helper

tree-sitter-al parses **every** branch of every `#if` into one tree. That is what
editors, diff tools and analysers need, but it means the tree holds nodes that are
not ordinary code: conditional containers, constructs assembled from pieces in
different branches, fragments of those constructs, and the directive lines
themselves. A walker that does not know which is which either drops `#if` content or
misreads it.

The traversal helper (roadmap F0) gives every runtime the same answer: one policy
file that classifies every special node type, and one `walk` that reports each node
with its class, its field, its byte span, the `#if` arms it sits in and, for split
constructs, a `SplitInfo` that lists every arm's pieces.

It does **not** pick a configuration. Every arm is reported; which one a given set
of preprocessor symbols selects is the job of the configured API (roadmap F1).

## Recursion alone does not fix node-kind recognition

Descending into every child finds the procedures inside a `preproc_conditional`.
It does not make a `preproc_split_procedure` look like a procedure: that node has
no `procedure` type, its header is spread over two arms, and its body is shared
after `#endif`. A consumer that matches `type === 'procedure'` misses it however
deep it recurses. **Use `SplitInfo`**: it hands you each arm's header pieces with
their field names, and the shared body, so you can recognise the construct and
read every variant of it.

## The classes

| Class | What it is | What `walk` does |
|---|---|---|
| ordinary | not a configuration node | descends normally |
| branch-container | a `#if` whose arms are alternatives in one host slot | visits it with its host policy and a `SplitInfo`, then every arm |
| assembler | one construct built from arm pieces plus shared parts, possibly crossing `#endif` | visits it with a `SplitInfo`; never presents its children as a flat list |
| fragment | a piece that only makes sense inside an assembler | visits it with class `fragment`; its assembler's `SplitInfo` lists it |
| token-alias | a keyword emitted by a split token (`preproc_split_begin` is a `begin`) | visits it like any token |
| directive | `#if` / `#elif` / `#else` / `#endif` and their parts | skipped unless `include_directives` |
| trivia | `#pragma`, `#region`, `#endregion`, `#define`, `#undef` | skipped unless `include_trivia` |

A **host policy** says how a container's arm fits its slot: `splice-repeat` (the
arm's items join a repeated list), `single-slot` / `optional-slot` (the arm fills
one slot), `list-run` (the arm carries items **and** separators, and for
permissions the property's own `;` terminator).

The classes live in `traversal/policy.json`, shipped in every package. Nothing is
classified by its name: a type is special because the policy says so, and
`tools/traversal_census.py` fails the build when the grammar gains a special type
the policy does not cover.

## What a visit carries

| Field | Meaning |
|---|---|
| `class` | one of the seven classes (`cls` on Python and JS objects, `class` in Rust) |
| `type`, `field` | the node type and the field it fills in its parent (`kind` in Rust) |
| `start`, `end` | UTF-8 byte offsets into the source, in every runtime (JS converts from UTF-16) |
| `arms` | `(if_offset, arm_id)` for every arm that wholly contains the node, outermost first |
| `host` | a branch container's host policy |
| `split` | for containers, assemblers and fragments that hold directives: `SplitInfo` |

`SplitInfo.groups` lists each `#if` group the node holds (a node can hold several),
each with **every** arm as `ArmFragments`: the descriptor (group id, arm id,
directive offsets, raw byte range) and the pieces inside that range in source order,
with field names, anonymous tokens kept as tokens. `SplitInfo.shared` lists the
node's own children outside every arm.

An arm can cross node boundaries: in `preproc_split_block_end_in_else` the `#else`
arm closes one procedure and opens the next, and its pieces say so.

### Lower-level accessors

| Python | JavaScript | Rust |
|---|---|---|
| `groups_of(node, doc)` | `groupsOf(node, doc)` | `groups_of(node, &doc)` |
| `bind_arm(descriptor, doc, policy)` | `bindArm(descriptor, doc, policy)` | `bind_arm(&descriptor, &doc, &policy)` |
| `arm_pieces(arm_fragments, doc, policy) -> list[Fragment]` | `armPieces(armFragments, doc, policy)` | `arm_pieces(&ArmFragments, &Document, &Policy) -> Result<Vec<Fragment>, WrongDocument>` |
| `split_info(node, doc, policy)` | `splitInfo(node, doc, policy)` | `split_info(node, &doc, &policy)` |

`bind_arm` turns an `ArmDescriptor` into its `ArmFragments`.

**`arm_pieces` returns an arm's pieces with every `fragment`-class piece replaced,
recursively and in source order, by its own children** (field names kept, anonymous
tokens kept). It exists because a fragment lying wholly inside one arm gets no
`SplitInfo` of its own; without it every consumer re-implements the expansion, and
the first canary got that wrong.

Limitation: **`arm_pieces` expands the arm's pieces only. It does not expand
`SplitInfo.shared`**; shared parts are returned as they are.

`bind_arm` and `arm_pieces` reject a descriptor that came from another document
(another revision of the source) with `WrongDocument`: raised in Python and JS,
returned as `Err(WrongDocument)` in Rust.

## Python

```python
from tree_sitter import Language, Parser
import tree_sitter_al
from tree_sitter_al import traversal

policy = traversal.load_policy()   # reads the policy shipped inside the installed package;
                                   # from a checkout pass traversal/policy.json explicitly
source = open("MyCodeunit.Codeunit.al", "rb").read()
tree = Parser(Language(tree_sitter_al.language())).parse(source)
doc = traversal.Document(tree, source, policy)

for v in traversal.walk(doc, policy):
    if v.type == "procedure":
        print("procedure", v.node.child_by_field_name("name").text.decode(), "arms", v.arms)
    elif v.cls == "assembler" and v.split:
        for group in v.split.groups:
            for arm in group.arms:
                pieces = traversal.arm_pieces(arm, doc, policy)
                name = next((f for f in pieces if f.field == "name"), None)
                if name and any(f.type == "procedure_keyword" for f in pieces):
                    print("split procedure", name.node.text.decode(), "arm", arm.descriptor.arm_id)
```

## JavaScript (native `tree-sitter` or `web-tree-sitter`)

One implementation serves both runtimes and never loads the native addon, so it works with a
bundler that resolves a JSON `require` (`traversal/index.js` is CommonJS and requires
`./policy.json`). It is not tested in a real browser yet; that is deferred to F1b.

```js
const T = require('@sshadows/tree-sitter-al/traversal');
const policy = T.loadPolicy();
const doc = new T.Document(parser.parse(text), text, policy);   // pass the same text you parsed
for (const v of T.walk(doc, policy)) {
  if (v.cls === 'branch-container') console.log(v.type, v.host, v.split.groups.length, 'group(s)');
}
```

`v.start` / `v.end` are UTF-8 byte offsets. For a JS string index use the node's own
`startIndex`, or `doc.index(byteOffset)`.

## Rust

```toml
tree-sitter-al = { version = "5", features = ["traversal"] }
```

```rust
use tree_sitter_al::traversal::{walk, Document, Policy, WalkOptions};

let policy = Policy::bundled();
let doc = Document::new(&tree, source.as_bytes(), &policy);
for v in walk(&doc, &policy, None, WalkOptions::default()) {
    if v.class == "assembler" { /* v.split: Option<SplitInfo>, v.kind: the node type */ }
}
```

The feature adds the `tree-sitter` runtime (`>=0.25, <0.27`) and `serde_json`; without
it the crate is unchanged.

## Migrating the patterns we have seen

**"Find every procedure"** (a recursion that stops at `type === 'procedure'`). Walk
instead, keep `type === 'procedure'`, and add split procedures from `SplitInfo` as in
the Python example. Each definition then carries `arms`, so a reviewer can tell the
`#if` and `#else` variants apart.

**"Collect members of known container types"** (a fixed list of section and body
types). Every `#if` container is a `branch-container` in the policy; treat any visit
of that class as transparent and its arms as members of its host. For a split object
declaration (`preproc_split_declaration`), the object's name is in each arm's
`object_name` fragment and its body is the shared `body`.

**"Is this statement in statement position?"** (a check on the parent's type). A
branch container splices its arm into its own host slot, so climb through
`branch-container` parents before asking: a call directly inside a
`preproc_conditional_statement` in a `statement_block` is a statement.

**"Tag nodes with their `#if` condition."** `arms` gives every arm of every kind, not
only statement-level ones. Only a path of arm-0 arms has an exact condition (the
`and` of the `#if` conditions); an `#elif` or `#else` arm's real condition negates
every arm before it, and needs the symbolic API (not in F0). Report those as
unsupported rather than guessing `!last-condition`. Two defects this catches in
existing walkers: an outer `#if` range that shadows a nested `#if`, and an `#elif`
arm that drops its negation.

## Keeping it correct

- `python tools/traversal_census.py` (validate-grammar.sh Step 5f): every special
  type classified, every entry still declared, the policy agreeing with
  `tools/config_oracle/contracts.py`.
- `python -m pytest tests/traversal`: the walker, `SplitInfo`, a witness per policy
  entry (each with a mutant that must fail), the consumer canaries, and the shared
  expected visits.
- `npm test` (the traversal JS tests) and `cargo test --features traversal`: the
  other runtimes against the same files.
- After a deliberate walker change, `python tests/traversal/regen_expected.py`, then
  read the diff: those files only make the runtimes agree with Python; the
  hand-written tests say whether Python is right.

Tested runtimes: Python >= 3.12 with py-tree-sitter 0.25; Node 18 and 24 (the CI
matrix, verified on Linux) with `tree-sitter` 0.25 and `web-tree-sitter` 0.27; Rust
with `tree-sitter` 0.25 and 0.26. Development note, not a support claim: the Windows
prebuild of `tree-sitter` 0.25.1 crashes under Node 18 and 20.
