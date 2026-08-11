---
name: AL File Total Validation
description: Validate that the parse tree of one AL file is both COMPLETE (every construct in the source reaches the tree and is queryable) and SOUND (everything the tree claims is true of the source). Use when checking whether the parser captured an AL file correctly, investigating a suspected silent misparse, verifying a grammar change against real code, or answering "did we actually extract everything?" — not just "were there errors?".
---

# AL File Total Validation

`tree-sitter parse file.al` answering "no errors" says almost nothing. Every
defect found in 4.0.0 — 574,694 dropped bytes, three inverted precedence
levels, two node types shipping two shapes each, an omitted list separator
silently absorbed as an extra element — produced a **clean error count**. An
error count can only see what the parser noticed going wrong. It cannot see
what the parser lexed and threw away, or attached to the wrong parent, or
grouped the wrong way round.

This skill answers the two questions that actually matter, separately:

| | question | fails when |
|---|---|---|
| **Completeness** | does everything in the source reach the tree? | a token is lexed and dropped; a construct produces no node; a node is unreachable by any query |
| **Soundness** | is everything the tree claims true of the source? | a required field is empty; a captured span disagrees with the file |

## Run it

```bash
./tools/ts-lock.sh python tools/validate_al_file.py path/to/File.al
./tools/ts-lock.sh python tools/validate_al_file.py path/to/File.al --json
./tools/ts-lock.sh python tools/validate_al_file.py --self-test
```

Wrap in `tools/ts-lock.sh` — it builds the shared `al.dll` that every worktree
of this repo shares by grammar name, and a concurrent build corrupts it
without either run erroring.

Exit `0` all gating checks passed · `1` a gating check failed · `2` could not
run. `--strict-reachability` promotes the reachability NOTE to a gating check.

## The six checks

Each is written so it CAN fail, and `--self-test` proves each one does by
breaking something on purpose and requiring **the right check** — not merely
some check — to report it.

1. **parse-integrity** — ERROR and MISSING nodes with positions. Deliberately
   first and deliberately the weakest: it is the check every other tool in the
   repo already performs, and it is the one that missed every 4.0.0 defect.

2. **byte-roundtrip** *(completeness)* — reconstructs the file from its leaf
   nodes and the gaps between them, and requires the result to be byte-identical
   to the source. A gap holding anything but whitespace is a byte the parser
   lexed and dropped. **This is the check that would have caught the 574,694**,
   and no error count can substitute for it, because a dropped token leaves no
   ERROR behind.

3. **anchor-reconciliation** *(completeness)* — reads the file a **second
   time, with regexes that know nothing about the grammar**, and requires the
   two readings to agree: N lexical `field(` sites must yield N `field_keyword`
   nodes. Independence is the whole point — a count derived from the parser
   cannot detect the parser failing to emit a node, because it would be
   counting the same absence twice. Shares `anchors.ANCHORS` with the
   corpus-wide harness so the two cannot drift into disagreeing definitions.

4. **required-fields** *(soundness)* — every field `node-types.json` declares
   `required` must be populated on every live instance. Release defects 4 and 5
   were exactly this shape and surfaced only because those fields happened to
   be required.

5. **extraction-fidelity** *(soundness)* — runs a consumer-style query that
   addresses values **by field name** (`field_declaration id:/name:/type:`,
   `property name:/value:`, and so on) and checks each captured value against
   its own source span. Capturing **nothing** is a failure, not a pass: an
   empty result and a correct-but-empty file are indistinguishable.

6. **query-reachability** *(completeness, for consumers)* — named node types
   this file produces that **no shipped query in `queries/` matches**.
   Losslessness puts a byte in a node; this asks whether anyone can address it.
   Informational by default because `queries/` was written for editor
   highlighting rather than exhaustive extraction — a gap here is a note, not a
   regression.

## Reading the output

```
  PASS       byte-roundtrip           519 leaves cover 3965 bytes
  PASS       anchor-reconciliation    procedure=1/1 trigger=2/2 key(=1/1 field(=10/10
  PASS       required-fields          217 required-field slot(s) checked
  PASS       extraction-fidelity      f.id=10 f.name=10 f.type=10 p.name=21 p.value=21 var=6
  NOTE       query-reachability       68 named type(s) produced, 57 reachable
```

The headline numbers matter as much as PASS. `anchor-reconciliation` printing
`field(=0/0` on a table with fields means the regex found nothing, and a check
that compared zero against zero has told you nothing — read the counts, not
just the verdict. `CANNOT RUN` is never a pass and is rendered as its own state
for that reason.

## The trap this tool fell into on its own first run

**Never key on `node.type` without checking `is_named`.**

Every keyword rule is `alias(kw('word'), 'word')`, which gives the named
`x_keyword` node exactly one **anonymous** child whose type string is the
canonical lowercase spelling. Several of those spellings are also named rule
types:

```
procedure              named=True   kids=6      <- the rule
  procedure_keyword    named=True   kids=1
    procedure          named=False  kids=0      <- anonymous child of the keyword
```

Both report `node.type == "procedure"`. A type-keyed walk that ignores
`is_named` finds a childless `procedure` carrying no fields at all and reports
every required field on it as missing. This validator did precisely that on its
first run against a six-line file, and reported a grammar defect that did not
exist. The same collision exists for `table`, `key`, `value`, `field`,
`record` and every other keyword whose spelling doubles as a rule name.

`--self-test` pins it: one case runs the naive walk and requires it to fail.

## What this does NOT check

Stated because a validator's silence about a dimension is otherwise
indistinguishable from a pass on it:

- **Semantic validity.** The grammar's design is *parse structure, don't
  validate*. A file this tool passes may still be rejected by `alc` — the
  parser deliberately accepts syntactically plausible code that the compiler
  refuses. Use `al compile` for that question; see `CLAUDE.md` for the probe
  recipe and the three traps that make a working probe look like a rejection.
- **Whether a grouping is the one AL means.** `a + b * c` covers every byte
  correctly under either grouping. Precedence and associativity are pinned by
  `test/corpus/operator_precedence_test.txt` and measured against `alc` in
  `docs/al-operator-precedence.md`.
- **Optional fields that nothing populates.** Only `required` fields are
  checked dynamically; that is 245 of 396 declarations. The corpus-wide
  question belongs to `qc`'s detector 8.
- **Anything about other files.** This is a single-file tool. For corpus-wide
  answers use `python -m tools.query_coverage.qc run` and
  `./parse-al-parallel.sh ./BC.History/ .`.

## When a check fails

- **byte-roundtrip** — a real grammar defect. Find the construct at the
  reported byte offset; it is almost certainly a bare `kw()` token, which
  tree-sitter renders as a hidden `aux_sym_*` symbol that lands in no node.
  The fix is `alias(kw('word'), 'word')`.
- **anchor-reconciliation** — either the grammar stopped producing a node, or
  the regex is over-matching (check for the word inside a comment or string).
  Read the source at each site before touching the grammar.
- **required-fields** — a field declared required is empty on a live instance.
  Either the grammar is wrong or the field should not be required; do not
  "fix" it by relaxing the declaration without establishing which.
- **extraction-fidelity** — if it reports the query failed to compile, a
  shipped query names a node type the grammar no longer declares. That raises
  rather than returning nothing, which is why it is a hard failure here.
