# B5b link-family keying: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** link syntax (`link_value_list`) appears only under the compiler's six link
properties. A dotted or `field(...)` comparison anywhere else is an expression, and every
production tree stays byte-identical.

**Architecture:**
- The external scanner's keyed dispatch emits a fifth keyed token, `LINK_PROPERTY_NAME`, for
  `SubPageLink`, `RunPageLink`, `LinkFields`, `DataItemTableFilter`, `ColumnFilter` and
  `DataItemLink`.
- `property` gets a keyed arm whose value is a `link_value_list` or a whole-value `#if`. There
  are two conditionals:
  - the `;`-after-`#endif` one, with an optional arm `;`;
  - the `;`-inside-the-arms one, with a recursive termination witness.
- `link_value_list` leaves `_property_value`, and `link_value` loses `prec.dynamic(1)`.
- `const(...)` gains the numeric forms alc accepts.
- `tools/relation_census.py` gains the `link-shape` / `link-outside` checks, leaf-rewrite L1/L3
  classes and `--expect-no-rows`.

**Tech stack:**
- tree-sitter 0.27 grammar DSL (`grammar.js`) and its C scanner (`src/scanner.c`);
- corpus fixtures;
- pytest;
- `tools.alc_probe`;
- `tools/alc_facts`.

**Spec:** `docs/superpowers/specs/2026-10-05-link-keying-design.md`, revision 4, approved
2026-10-05. Read it before any task. Section numbers below (§) refer to it. §9 records the three
review rounds, and why each rule is the way it is.

## Global constraints

- **Rules files bind every task:** CLAUDE.md, `.claude/rules/*.md` and
  `docs/agent-brief-rules.md`.
- **Git Bash with Windows paths.** Never `2>nul`. Run `tree-sitter` only through
  `./tools/ts-lock.sh`. `python -m tools.perf ab` takes the lock itself.
- **Branch:** `fix/b5b-link-keying`, off main HEAD (`2b558d8` or later; the grammar is unchanged
  since the B5 merge `821c914`). Do not push.
- **Forbidden commands:**
  - `git stash`, `git reset --hard`, `git checkout --`, `git restore`, `git clean -f`;
  - `git worktree remove --force` (a safety hook blocks it; leave scratch worktrees and list
    them);
  - `find /`;
  - `tail -f | grep`.
- **Generated files:** commit `grammar.js`, `src/parser.c`, `src/grammar.json`,
  `src/node-types.json` and `src/scanner.c` together.
- **Commit messages:** every message ends with a measured `[BC.History: N errors, X% success]`.
- **Never commit:**
  - decompiled compiler source;
  - `__pycache__` / `.pyc` (check `git status` before every commit);
  - census manifests or other report output.
- **The keyed family is exactly these six names:** `SubPageLink`, `RunPageLink`, `LinkFields`,
  `DataItemTableFilter`, `ColumnFilter`, `DataItemLink`. Match them case-insensitively, whole
  word only. `FooLink` and `SubPageLinkX` stay generic.
- **Corpora:** `./BC.History`, `./DC`, `H:/Git/BC28.1`, `H:/Git/BCApps-29.0`.
- **Hard limits:**
  - Production trees do not change in any of the four corpora: per-corpus tree-harness reports 0
    changed files, and `relation_census.py delta --expect-no-rows` reports 0 rows and 0
    findings.
  - STATE_COUNT ≤ 17,567, measured BEFORE the grammar commit, not after.
  - Every new declared conflict carries a comment naming its two readings.
- **`-u` traps:** after any `tree-sitter test -u`, run `git diff --stat test/corpus`. Restore an
  untargeted file with `git show HEAD:path > path`.
- **File locks.** A file write that fails with "Permission denied" or Errno 22 is a transient
  lock on this machine. Retry it in a loop with `sleep 1`. Never treat it as permission to skip
  the write.
- **Scratchpad** (`$SCRATCH`):
  `C:/Users/SShadowS/AppData/Local/Temp/claude/U--Git-tree-sitter-al/7735bcff-35e6-47ee-87b9-879d6fed9fe1/scratchpad`.

## Review focus

1. **A G11 split under a keyed name.** Both shapes must parse as ONE property:
   - the non-empty unterminated prefix, `#if X A = field(B), #endif B = field(A);`;
   - the empty prefix, `#if X #endif B = field(A);`.

   The empty prefix is a silent split today. Task 3 adds fixtures, and Task 5 adds a census
   mutation.
2. **A family value silently becoming an expression,** or the reverse. Task 2's `link-shape` and
   `link-outside` checks, and Task 5's mutations, cover it.
3. **The mixed `;` placement and an exhaustive `#elif not X` with no `#else`.** Both must keep
   parsing as one property. Task 3 adds fixtures.
4. **A signed or decimal `const` argument.** It must be ONE `value` node (`unary_expression` with
   `operator` and `operand`), never an ERROR and never a split value. Task 3 adds a fixture, and
   the `check-field-types` pin covers the field.
5. **An incremental edit that turns a keyed name generic, or back.** The incremental tree must
   equal a fresh parse. Task 5 adds the test.

---

### Task 1: baselines and compiler evidence

**Files:**
- Create: `tools/alc_probe/cases/link-keying/*.al`

**Interfaces:**
- Produces:
  - four tree-harness snapshots, `.snapshots/baseline-b5b-{bc,dc,bc28,bcapps}`;
  - `$SCRATCH/al_base5b.dll`, the pre-change library (Tasks 2 and 5);
  - the decide-by-probe verdicts, in the commit message and in a header comment of
    `tools/alc_probe/cases/link-keying/README-verdicts.txt`:
    - an empty value, per delegate: TableFilter, ReportDataItemLink, QueryDataItemLink;
    - each `const` numeric form: `1.5`, `-1`, `-1.5`, a biginteger, signed and unsigned, a
      space or comment between sign and magnitude, unary `+`;
    - `const` with a date, time and datetime;
    - `filter((1|2)&3)`;
    - `RunPageLink` on an action area;
    - `chartpart` with `SubPageLink`;
    - `Enabled = Status = const(Open)` on a page field;
    - the trailing comma, `A = field(B),;`;
    - each host × property tuple of §5.2.

- [ ] **Step 1: Branch, baselines, base library**

```bash
cd U:/Git/tree-sitter-al
git checkout -b fix/b5b-link-keying
for c in bc:./BC.History dc:./DC bc28:H:/Git/BC28.1 bcapps:H:/Git/BCApps-29.0; do
  ./tools/ts-lock.sh ./tools/tree-harness.sh snapshot "${c#*:}" ".snapshots/baseline-b5b-${c%%:*}"
done
./tools/metrics.sh | tail -1
./tools/ts-lock.sh tree-sitter build -o "$SCRATCH/al_base5b.dll"
./tools/ts-lock.sh tree-sitter test 2>&1 | grep "^Total"
```

Expected:
- four snapshots;
- STATE_COUNT=17223;
- 1868 tests, all passing.

Record the test total; every later count check uses it as its base.

**Windows path handling.** `H:/Git/...` with a `${c#*:}` split does not survive Windows
drive-letter colons. If that loop mis-splits, write the four snapshot commands out explicitly.

- [ ] **Step 2: Write the probe cases**, one file per §5.1 item, in
  `tools/alc_probe/README.md`'s header format.
  - **Self-contained.** Every case declares every table, page, query, report and xmlport it
    references, so a missing symbol cannot pose as a rejection (CLAUDE.md, the AL0185 trap).
  - **One file per tuple.** Each §5.2 host × property × placement tuple is its own file. Name
    files `host-<host>-<property>-<placement>.al`.
  - **Decide-by-probe cases** are written `// expect: * accept`, run, and then their header is
    set to the real verdict. That is the one place the expectation follows the compiler.
  - **Delegate-valid G11 variants:**
    - `field(...)` pairs for report `DataItemLink`;
    - `DataItem.Field` pairs for query `DataItemLink`;
    - `field`/`const`/`filter` pairs for TableFilter.
  - **Each G11 shape:**
    - list-opening `#if` continued after `#endif`;
    - the whole value, with `;` after `#endif` and with `;` in the arms;
    - nested;
    - the empty prefix;
    - mixed `;` placement;
    - no `#else` with exhaustive `#elif not X`;
    - independent `X`/`Y` with no `#else` (expected: `X&!Y` and `!X&Y` accept, `!X&!Y` reject).

  Example, `host-page-action-runpagelink-flat.al`:

```al
// RunPageLink on a page action, flat, one entry (B5b §5.2).
// source: docs/superpowers/specs/2026-10-05-link-keying-design.md §5.1
// expect: * accept
table 50101 Cust { fields { field(1; "No."; Code[20]) { } } }
page 50101 CustCard { SourceTable = Cust; layout { area(Content) { field(N; Rec."No.") { } } } }
page 50100 P
{
    SourceTable = Cust;
    actions { area(Processing) { action(A) { RunObject = page CustCard; RunPageLink = "No." = field("No."); } } }
}
```

- [ ] **Step 3: Run and pin**

Run: `python -m tools.alc_probe run tools/alc_probe/cases/link-keying --check`
Expected: exit 0.

A drift on a non-decide case is a STOP: report it, do not edit `expect`.

**What the decide-by-probe verdicts change:**

| verdict | effect |
|---|---|
| any delegate accepts an empty value | Task 3 adds `optional()` on the keyed value, plus the unfielded `;`-only arms in both conditionals; the empty forms of the other delegates become over-acceptance fixtures |
| every delegate rejects an empty value | the value is required, and no `;`-only arms exist |
| a `const` numeric form accepted | Task 3 adds it to `_const_numeric` and to the `link_value.value` pin |
| `filter((...))` or `chartpart` accepted | a deferred-work item (Task 6); no grammar change in B5b |
| the trailing comma rejected | a deferred-work item for B7 |
| `RunPageLink` on an action area accepted | STOP: §3.2 item 4 assumed AL0124; report before Task 3 |
| `Enabled = Status = const(Open)` accepted | it is an L1 fixture (`property_expression`) |
| `Enabled = Status = const(Open)` rejected | it is a negative, pinned as it parses |
| a host × property tuple rejected | that tuple gets no fixture; it is reported and recorded in the verdicts file |

- [ ] **Step 4: Commit**

```bash
git add tools/alc_probe/cases/link-keying
git commit -m "test(alc): B5b link-family evidence -- alc 18.0.41

Decide-by-probe: <one line per verdict>.

[BC.History: 0 errors, 100% success]"
```

---

### Task 2: census link checks, leaf rewrites, `--expect-no-rows`

**Files:**
- Modify: `tools/relation_census.py`
- Modify: `tools/tests/test_relation_census.py`

**Interfaces:**
- Consumes:
  - `$SCRATCH/al_base5b.dll`;
  - the existing census API: `check_tree`, `check`, `delta`, `DeltaResult`, `parser_for`,
    `walk`, `prop_name`, `_read`, `_al_files`.
- Produces, for Tasks 3 and 5:
  - `LINK_NAMES: frozenset[str]`, the six lowercase names;
  - finding kinds `link-shape` and `link-outside` from `check_tree`;
  - `rewrite_records(name, old_value, new_value, *, approved_const_forms) -> list[Rewrite]`,
    where `Rewrite = (slot_path: tuple[int, ...], cls: str)` and `cls ∈ {"L1", "L3"}`;
    `Unclassifiable` is raised on anything else;
  - a `delta` that keeps D1/D2/D3 and adds L1/L3 rows, one per rewrite record;
  - the CLI flag `delta --expect-no-rows`, which exits 1 when any row exists;
  - the env var `B5B_BASE_LIB`, which tests that pin pre-change trees read and skip without.

- [ ] **Step 1: Write the failing tests** in `tools/tests/test_relation_census.py`. They run
  against today's grammar.

```python
B5B_BASE = os.environ.get("B5B_BASE_LIB")
needs_b5b_base = pytest.mark.skipif(not B5B_BASE, reason="set B5B_BASE_LIB to the pre-B5b library")


def _page_action(prop: bytes) -> bytes:
    return (b"page 50100 P\n{\n    actions { area(Processing) { action(A)\n    {\n        "
            + prop + b"\n    }\n    }\n    }\n}\n")


def test_link_names_are_the_six():
    assert rc.LINK_NAMES == {"subpagelink", "runpagelink", "linkfields",
                             "dataitemtablefilter", "columnfilter", "dataitemlink"}


@needs_b5b_base
def test_link_outside_flags_todays_leak(tmp_path):
    p = rc.parser_for(Path(B5B_BASE))
    (tmp_path / "a.al").write_bytes(_page_action(b"Visible = Flag = Rec.OtherFlag;"))
    kinds = {f.kind for f in rc.check([tmp_path], p)}
    assert "link-outside" in kinds


@needs_b5b_base
def test_link_shape_clean_on_a_real_link(tmp_path):
    p = rc.parser_for(Path(B5B_BASE))
    (tmp_path / "a.al").write_bytes(_page_action(b'RunPageLink = "No." = field("No.");'))
    kinds = {f.kind for f in rc.check([tmp_path], p)}
    assert "link-shape" not in kinds and "link-outside" not in kinds


def test_expect_no_rows_exits_1_on_a_row(tmp_path, monkeypatch):
    # a fake delta that returns one classified row and no findings
    monkeypatch.setattr(rc, "delta", lambda *a, **k: rc.DeltaResult([], [("x", 0, 1, "h", "n", "L1", "a", "b")], 0))
    (tmp_path / "a.al").write_bytes(b"codeunit 1 C { }")
    assert rc.main(["delta", "--root", str(tmp_path), "--base-lib", "x", "--expect-no-rows"]) == 1
```

  `DeltaResult`'s field order must match `tools/relation_census.py:89`. Read it first, and adapt
  the fake if the fields differ.

Run: `B5B_BASE_LIB="$SCRATCH/al_base5b.dll" python -m pytest tools/tests/test_relation_census.py -q`
Expected: the four new tests FAIL; the existing ones pass.

- [ ] **Step 2: Implement `link-shape` and `link-outside`** in `check_tree`, alongside the
  relation checks:

```python
LINK_NAMES = frozenset({"subpagelink", "runpagelink", "linkfields",
                        "dataitemtablefilter", "columnfilter", "dataitemlink"})
LINK_TYPES = {"link_value_list", "link_value", "preproc_conditional_link_values"}


def _link_owner(n) -> str | None:
    """The name of the nearest enclosing property, or None."""
    a = n.parent
    while a is not None and a.type != "property":
        a = a.parent
    return prop_name(a) if a is not None else None


def _link_shape_ok(v) -> bool:
    if v.type == "link_value_list":
        return True
    if v.type == "preproc_conditional_property_value":
        arms = v.children_by_field_name("value")
        return bool(arms) and all(_link_shape_ok(a) for a in arms)
    return False
```

  **The checks:**
  - **link-shape:** every `property` whose name is in `LINK_NAMES` and that has a `value` must
    satisfy `_link_shape_ok(value)`.
  - **link-outside:** any node whose type is in `LINK_TYPES` must have `_link_owner(node)` in
    `LINK_NAMES`. Report the outermost such node per site, as `relation-outside` does.

  **The unfielded `;`-only arm, if Task 1 enables empty values.** A wrapper whose arms are all
  `;`-only has no `value` field. If such a wrapper can occur, `_link_shape_ok` accepts a
  conditional with no `value` arms only when every arm is a `;`-only arm. Spell that out in
  code; do not loosen the `bool(arms)` rule silently.

- [ ] **Step 3: Implement the leaf rewrites (§4.2).** `rewrite_records` walks the old and new
  value subtrees together, with an all-child cursor over named AND anonymous children:
  - **Unchanged conditional envelopes.** A `preproc_conditional_property_value`,
    `preproc_conditional_link_values` or `preproc_if` node, or a directive child, must match
    in type, field name, span and anonymous text. The walk descends into it.
  - **Rewrite roots.** These are where the two trees diverge:
    - **L1** (name not in `LINK_NAMES`): the old side is `link_value_list` → `link_value`, and
      the new side is `property_expression` → `comparison_expression`. The old `field` span is
      the new `left` span, the old `=` span is the new operator span, and the old right-hand
      side covers exactly the new `right` span.
    - **L3** (name in `LINK_NAMES`): the old side is `property_expression` →
      `comparison_expression`, and the new side is `link_value_list` → `link_value`. Same span
      mapping, and the new `const` argument's node type and text must match one of
      `approved_const_forms`, for example `{"decimal", "unary_expression"}`.
  - **Anything else** raises `Unclassifiable`.
  - **Records.** One `Rewrite` per root, with the `slot_path` of child indexes from the value
    root.

  Then, in `delta`:
  - for a property whose value differs, try the existing D1/D2/D3 predicates first;
  - if none matches, call `rewrite_records`, which must return at least one record, and emit one
    manifest row per record;
  - add `--expect-no-rows`: when set, `main` returns 1 if `rows` is non-empty.

- [ ] **Step 4: Tests for the leaf rewrites.** Build the pairs by parsing the same source with
  the base library and an in-memory alternative.
  - **Where a real pair is not yet available,** before Task 3, use the `_P`/`_Fake` proxy style
    already in `test_relation_census.py`.
  - **Positive cases:**
    - an L1 inside a whole-value `#if` arm, with the envelope unchanged;
    - two L3 rewrites in one envelope.
  - **Negative cases**, each raising `Unclassifiable`:
    - an L3 with a `const` argument outside `approved_const_forms`;
    - an envelope whose `#else` moved;
    - an L1 where the `right` span differs.

Run: `B5B_BASE_LIB="$SCRATCH/al_base5b.dll" python -m pytest tools/tests/test_relation_census.py -q`
Expected: all pass. Without the env var, the base-library tests skip.

- [ ] **Step 5: Today's corpus, as a baseline fact**

```bash
python tools/relation_census.py check --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0
```

Expected: exit 1, with ONLY the 2 known BCApps has-error files. That gives `link-outside` 0 and
`link-shape` 0, matching spec §2.2. Any link finding today is a STOP: the census disagrees with
the spec's census.

- [ ] **Step 6: Commit**

```bash
git add tools/relation_census.py tools/tests/test_relation_census.py
git commit -m "test(b5b): census link-shape/link-outside, L1/L3 leaf rewrites, --expect-no-rows

[BC.History: 0 errors, 100% success]"
```

---

### Task 3: keying, conditionals, `const` numerics, fixtures

**Files:**
- Modify: `src/scanner.c`:
  - the `TokenType` enum (`:32`);
  - the `IdentifierWord` enum (`:288`) and `read_identifier_word` (`:330`);
  - the three guards (`:570`, `:956`, `:1030`);
  - the emission chain (`:1063`).
- Modify: `grammar.js`:
  - `externals` (`:233`);
  - `property` (`:820`);
  - `_property_with_terminator_in_if` (`:989`);
  - `_property_value` (`:1177`);
  - `link_value` (`:1582-1630`, the `prec.dynamic` and the `const` arm at `:1613`);
  - the `conflicts` block (`:300-440`).
- Modify: `tools/check-field-types.py:77-84`.
- Create:
  - `test/corpus/link_keying_test.txt`
  - `test/corpus/link_keying_negative_test.txt`
- Modify:
  - existing fixtures whose trees change, by hand, each hunk traced to L1 or L3;
  - `tools/deliberate-negatives.txt`;
  - oracle classification files only if the quick tier asks.

**Interfaces:**
- Consumes: Task 1's verdicts; Task 2's census.
- Produces:
  - the external `$._link_property_name`, which is [18];
  - the hidden rules `_link_property_value`, `_link_whole_conditional`,
    `_link_whole_conditional_in_if`, `_link_in_if_arm`, `_link_in_if_tail` and
    `_const_numeric`.

- [ ] **Step 1: Write the failing positive fixture**, `test/corpus/link_keying_test.txt`. The
  cases:
  - every row of §4.1;
  - every delegate-valid G11 variant from Task 1;
  - the mixed `;` placement and a nested mixed placement;
  - the empty prefix, which must be ONE property;
  - `#if X …; #elif not X …; #endif` with no `#else`, ONE property;
  - independent `X`/`Y` with no `#else`;
  - empty arms beside a terminated arm;
  - each `const` numeric form Task 1 accepted;
  - the leak cases, `Visible = Flag = Rec.OtherFlag;` and `Caption = A = B.C;`, each a
    `property_expression`;
  - the §5.2 regressions: SourceTableView, SubPageView, RunPageView, DataItemTableView,
    Filters, CalcFormula and TableRelation, each with `where`, plus `Implementation = A = B;`
    and `FooLink = A = field(B);`;
  - the 3 production list-internal `SubPageLink` sites and one comment-bearing production
    `DataItemLink`, verbatim. Find them with `python tools/relation_census.py check --root ...
    --manifest` or `./tools/corpus-grep.sh`.

  The original `link_list_opening_conditional_test.txt` stays UNCHANGED, including its two
  generic `Caption` cases.

Run: `./tools/ts-lock.sh tree-sitter test --file-name link_keying_test.txt`
Expected: FAIL on:
- the leak cases;
- the empty prefix (two properties today);
- the no-`#else` and mixed cases, if they misparse today;
- the numeric `const` cases (`property_expression` today).

- [ ] **Step 2: Scanner**

```c
// enum TokenType -- append
  LINK_PROPERTY_NAME = 18,  // one of the six compiler link-family names followed by = (B5b)

// enum IdentifierWord -- append after WORD_TABLE_RELATION
  WORD_LINK_PROPERTY,  // value grammar: TableFilter / Report- / QueryDataItemLink (B5b)

// The compiler's link-family property names, lowercase. Source: tools/alc_facts/property-hosts.tsv
// (value kinds TableFilter, ReportDataItemLink, QueryDataItemLink), alc 18.0.41.62505.
// Never derive this from a suffix: `FooLink` has no link grammar in alc.
static const char *const LINK_PROPERTY_NAMES[] = {
  "columnfilter", "dataitemlink", "dataitemtablefilter", "linkfields", "runpagelink", "subpagelink",
};
```

  In `read_identifier_word`, after the `tablerelation` line:

```c
  for (size_t i = 0; i < sizeof(LINK_PROPERTY_NAMES) / sizeof(LINK_PROPERTY_NAMES[0]); i++) {
    if (strcmp(buf, LINK_PROPERTY_NAMES[i]) == 0) return WORD_LINK_PROPERTY;
  }
```

  **Guards and emission:**
  - Add `&& valid_symbols[LINK_PROPERTY_NAME]` to the recovery guard (`:570`).
  - Add `|| valid_symbols[LINK_PROPERTY_NAME]` to the dispatch guard (`:956`) and the
    property-block guard (`:1030`).
  - After the TableRelation branch (`:1063`):

```c
        } else if (word == WORD_LINK_PROPERTY && valid_symbols[LINK_PROPERTY_NAME]) {
          lexer->result_symbol = LINK_PROPERTY_NAME;
```

  Extend the comment above the chain by one sentence citing spec 2026-10-05 §2.1.

- [ ] **Step 3: Grammar.** Make all of these in one edit.

```javascript
// externals: append
    $._link_property_name,  // [18] one of the six compiler link-family names followed by = (B5b)

// property: a keyed arm after TableRelation. optional() ONLY if Task 1 found an empty value accepted.
      seq(
        field('name', alias($._link_property_name, $.property_name)),
        '=',
        field('value', $._link_property_value),
        ';'
      ),

    // The six link-family names reach the compiler's TableFilter / ReportDataItemLink /
    // QueryDataItemLink grammars (spec 2026-10-05 §2.1). One neutral union grammar
    // (link_value) serves all three: deliberate over-acceptance, not equivalence.
    _link_property_value: $ => choice(
      $.link_value_list,
      alias($._link_whole_conditional, $.preproc_conditional_property_value),
    ),
    // `;` after #endif: arms MAY end in `;` (mixed placement is valid AL; the compiler's
    // property list accepts a standalone `;`, ObjectParser.cs:7505-7516).
    _link_whole_conditional: $ => keyedValueConditional($,
      seq(field('value', $._link_property_value), optional(';'))),
    // `;` inside the arms: arms may be absent and #else is optional, but the conditional
    // must hold at least one present arm, recursively -- the termination witness that
    // excludes the empty-prefix split (`#if X #endif B = field(A);`), spec §3.2 item 2.
    _link_in_if_arm: $ => choice(
      seq(field('value', $._link_property_value), ';'),
      field('value', alias($._link_whole_conditional_in_if, $.preproc_conditional_property_value)),
    ),
    _link_in_if_tail: $ => seq(
      repeat(seq($.preproc_elif, optional($._link_in_if_arm))),
      optional(seq($.preproc_else, optional($._link_in_if_arm))),
      $.preproc_endif,
    ),
    _link_whole_conditional_in_if: $ => choice(
      seq($.preproc_if, $._link_in_if_arm, $._link_in_if_tail),
      seq($.preproc_if,
        repeat($.preproc_elif),
        choice(
          seq($.preproc_elif, $._link_in_if_arm, $._link_in_if_tail),
          seq($.preproc_else, $._link_in_if_arm, $.preproc_endif),
        )),
    ),

    // const(...)'s numeric argument: sign and magnitude are ONE value node. Local `-`, not the
    // external NEGATIVE_* tokens, which decline before `)` (spec §3.2 item 6).
    _const_unsigned_numeric: $ => choice($.integer /* + each accepted: $.decimal, $.biginteger_literal */),
    _const_numeric: $ => choice(
      $._const_unsigned_numeric,
      alias(seq(field('operator', '-'), field('operand', $._const_unsigned_numeric)), $.unary_expression),
    ),
```

  **If Task 1 enabled empty values,** also add:
  - an unfielded `';'` alternative to `_link_whole_conditional`'s branch;
  - an unfielded `';'` alternative to `_link_in_if_arm`.

  **The other edits, in the same step:**
  - `_property_with_terminator_in_if`: add a keyed arm. Its name is
    `alias($._link_property_name, $.property_name)`, then `'='`, then
    `field('value', alias($._link_whole_conditional_in_if, $.preproc_conditional_property_value))`.
  - `_property_whole_value_in_if`: no keyed arm (Task 1's action-area verdict; spec §3.2
    item 4).
  - `_property_value`: delete the `$.link_value_list,` line (`:1177`).
  - `link_value`: remove the `prec.dynamic(1, …)` wrapper (`:1599`), keeping its inner
    `choice`. Rewrite the comment block above it to say:
    - the expression competitor is gone, because keying sends a generic name to the expression
      path;
    - the G11 whole-value against list-opening choice was never decided by `prec.dynamic`.
  - `link_value`'s `const` arm (`:1613`): replace `$.integer` with `$._const_numeric`.
  - `tools/check-field-types.py:77-84`: add the accepted node types (`decimal`,
    `biginteger_literal`, `unary_expression` as approved) to the `link_value.value` set.

- [ ] **Step 4: Generate, measure, settle conflicts**

```bash
./tools/ts-lock.sh tree-sitter generate 2>&1 | tail -10
./tools/metrics.sh --vs 821c914 | tail -2
```

  **Conflicts.**
  - Re-check every `conflicts` entry naming `preproc_conditional_link_values`,
    `_link_value_branch` or `link_value_list` (`:353-434`).
  - Delete an unneeded entry, or remove just its unneeded token, as B5 Task 2 did. Record each
    generator message verbatim.
  - For the keyed conditionals, declare exactly what the generator asks for: whole value against
    list-opening, and outside against inside. Each gets a comment naming both readings.
  - A request for a broader conflict is a STOP: report the message and the edit tried.

  **Budget.** STATE_COUNT must be ≤ 17,567 BEFORE you go further. Over budget is a STOP: report
  `tree-sitter generate --report-states-for-rule -` (top 25) and the per-rule cost of the new
  rules. This is B5's lesson: measure before the commit, not after.

- [ ] **Step 5: Run the fixtures; rewrite the existing ones**

```bash
./tools/ts-lock.sh tree-sitter test --file-name link_keying_test.txt
./tools/ts-lock.sh tree-sitter test --file-name link_list_opening_conditional_test.txt
./tools/ts-lock.sh tree-sitter test 2>&1 | grep -E "✗|failure|^Total" | head -60
```

  `link_list_opening_conditional_test.txt` must pass UNCHANGED. A G11 tree that moved is a STOP.

  For every other failing case, assign each hunk to L1 or L3. A hunk that fits neither is a
  STOP. Rewrite by hand. If you use `-u`, use it per file, then run `git diff --stat test/corpus`
  and restore untargeted files with `git show HEAD:path > path`.

- [ ] **Step 6: Prove the fixture can fail.** Rename one `field:` to `bogus:`, see FAIL, revert.

- [ ] **Step 7: Negative fixture**, `link_keying_negative_test.txt`, with Task 1's rejects
  pinned as they really parse:
  - over-accepted ones (`RunPageLink = A = B.C;`, `DataItemLink = A = const(1);`) are clean link
    trees, and the case header says so;
  - genuine ERRORs show the ERROR inside the value.

  Add the file to `tools/deliberate-negatives.txt`, citing the probe files. Then run:
  - `./tools/ts-lock.sh tree-sitter test --file-name link_keying_negative_test.txt` (PASS);
  - `python tools/has_error_sweep.py --corpus-fixtures` (exit 0).

- [ ] **Step 8: Quick gates**

```bash
./tools/ts-lock.sh ./validate-grammar.sh
python tools/check-field-types.py
python tools/relation_census.py check --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0
python -m tools.config_oracle run --tier quick
```

Expected:
- `validate-grammar.sh` exits 0, with the case count equal to Task 1's total plus the cases
  added. qc, the grammar-health snapshot and the wasm may be red; those belong to Task 6. Name
  each red step in the report.
- `check-field-types.py` exits 0.
- census `check`: `link-shape` 0, `link-outside` 0, and only the 2 known BCApps has-error files.
- The oracle quick tier exits 0. A new record is classified with alc_probe evidence.

- [ ] **Step 9: Commit.** Run `./parse-al-parallel.sh ./BC.History/ .` for the count.

```bash
git status --short | grep -v '^??'      # nothing unexpected; no .pyc
git add src/scanner.c grammar.js src/parser.c src/grammar.json src/node-types.json \
  tools/check-field-types.py tools/deliberate-negatives.txt test/corpus tools/config_oracle
git commit -m "fix(grammar): key the link family by name; generic values lose link syntax (B5b)

STATE_COUNT <n> (vs 17,223). Conflicts: <added/removed>.

[BC.History: 0 errors, 100% success]"
```

---

### Task 4: scanner-state audit and the host × property × placement matrix

**Files:**
- Modify: `test/corpus/link_keying_test.txt`, adding the host cases and the audit header.

**Interfaces:**
- Consumes: Task 3's grammar; Task 1's host probes.

- [ ] **Step 1: The two-direction audit (§5.4).** Read `ts_external_scanner_states` in
  `src/parser.c`. For every row, record:
  - (a) `property_name` without `_link_property_name`;
  - (b) a keyed token without `property_name`.

  Map each row to its grammar host, with a debug parse as evidence for every (a) row. Each (a)
  host must be one where no family name can occur. Expected (a) hosts:
  - the `caption_value` sub-fields;
  - `_permissions_head`;
  - `_property_whole_value_in_if`'s action-area and assembly hosts (spec §3.2 item 4).

  Write the table into the fixture header, in the format of B5's
  `table_relation_keying_test.txt` header.

  **If a real family host lacks the keyed token,** give it the keyed arm. Do not paper over it.

- [ ] **Step 2: The matrix.** For every host × property × placement tuple that Task 1 accepted,
  add one fixture case.
  - **Placements:**
    - flat;
    - `;` after `#endif`;
    - `;` in the arms;
    - mixed;
    - list-internal `#if`;
    - a comment between the name and `=`;
    - the whole property inside a body-level `#if`/`#else`.
  - **Hosts and properties:** the §5.2 table.
  - **Expected trees** come from `tree-sitter parse` with field labels, each checked by hand.
  - **A tuple Task 1 rejected** gets no fixture, and is listed in the header.

- [ ] **Step 3: Run and commit**

```bash
./tools/ts-lock.sh tree-sitter test --file-name link_keying_test.txt
python -m tools.alc_probe run tools/alc_probe/cases/link-keying --check
git add test/corpus/link_keying_test.txt
git commit -m "test(b5b): scanner-state audit and host x property x placement matrix

[BC.History: 0 errors, 100% success]"
```

---

### Task 5: zero-delta gate, mutations, incremental

**Files:**
- Create: `tools/config_oracle/tests/test_link_incremental.py`
- Modify: `tools/tests/test_relation_census.py` (mutation tests)

**Interfaces:**
- Consumes:
  - Task 2's census;
  - `$SCRATCH/al_base5b.dll`;
  - Task 1's four snapshots.

- [ ] **Step 1: Production zero-delta**

```bash
./tools/ts-lock.sh tree-sitter build -o "$SCRATCH/al_b5b.dll"
python tools/relation_census.py delta --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0 \
  --base-lib "$SCRATCH/al_base5b.dll" --cur-lib "$SCRATCH/al_b5b.dll" --expect-no-rows
```

Expected: exit 0, with 0 rows and 0 findings. Any row or finding is a STOP: report it with
paths. Do not loosen the census.

- [ ] **Step 2: Per-corpus tree-harness**, using the four snapshots from Task 1 Step 1:

```bash
./tools/ts-lock.sh ./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-b5b-bc
./tools/ts-lock.sh ./tools/tree-harness.sh verify ./DC .snapshots/baseline-b5b-dc
./tools/ts-lock.sh ./tools/tree-harness.sh verify H:/Git/BC28.1 .snapshots/baseline-b5b-bc28
./tools/ts-lock.sh ./tools/tree-harness.sh verify H:/Git/BCApps-29.0 .snapshots/baseline-b5b-bcapps
```

Expected: 0 changed files in each of the four. This is also the reparenting gate, which the
census cannot see.

- [ ] **Step 3: Mutation proofs**, as pytest cases using the `_P`/`_Fake` proxies, each asserting
  its finding kind:
  - a family value forced to `property_expression` → `link-shape`;
  - a `link_value_list` under `Visible` → `link-outside`;
  - a dropped property → `site-dropped`;
  - a whole-value conditional whose arm became list-internal, and the reverse → `link-shape`, or
    `Unclassifiable` in `rewrite_records`;
  - the empty-prefix split, a property ending at `#endif` with a sibling property `B` →
    `site-dropped` (the census reports a property present on one side only with that kind, in
    either direction).

  **Two scratch-build mutations**, run once by hand in a scratch worktree and recorded in the
  commit message:
  - comment out the `LINK_PROPERTY_NAME` emission: expect `link-shape`;
  - restore `$.link_value_list` in `_property_value`: expect `link-outside`.

  Leave the scratch worktree and list it; do not force-remove it.

- [ ] **Step 4: Incremental test**, `tools/config_oracle/tests/test_link_incremental.py`. Copy
  `_edit` and the test function verbatim from `test_table_relation_incremental.py`, with:

```python
HOST = (b"page 50100 P\n{\n    actions { area(Processing) { action(A)\n    {\n        %s\n"
        b"    }\n    }\n    }\n}\n")

EDITS = [
    (b'RunPageLink = "No." = field("No.");', b'RunPageLinkX = "No." = field("No.");'),
    (b'RunPageLinkX = "No." = field("No.");', b'RunPageLink = "No." = field("No.");'),
    (b'RunPageLink = "No." = field("No.");', b'Visible = "No." = field("No.");'),
    (b'Visible = Flag = Rec.OtherFlag;', b'RunPageLink = Flag = Rec.OtherFlag;'),
    (b'RunPageLink = "No." = field("No.");', b'runpagelink = "No." = field("No.");'),
    (b'RunPageLink = "No." = field("No.");', b'RunPageLink = "No." = field("No."), A = const(1);'),
    (b'RunPageLink = "No." = field("No.");',
     b'RunPageLink =\n#if X\n "No." = field("No.")\n#else\n "No." = field(Code)\n#endif\n;'),
    (b'RunPageLink =\n#if X\n "No." = field("No."),\n#endif\n A = field(B);',
     b'RunPageLink =\n#if X\n "No." = field("No."),\n#endif\n;'),
    (b'RunPageLink = "No." = field("No.");', b'RunPageLink  = "No." = field("No.");'),
]
```

Run: `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_link_incremental.py -q`
Expected: PASS.

Prove it can fail: disable `tree.edit`, see failures, restore.

- [ ] **Step 5: Oracle full tier and sweeps.** Run in the background, waiting with an `until`
  loop on the output file:

```bash
./tools/ts-lock.sh python -m tools.config_oracle run --tier full --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0
for r in ./BC.History ./DC H:/Git/BC28.1 H:/Git/BCApps-29.0; do python tools/has_error_sweep.py --root "$r"; done
```

Expected: the oracle exits 0 with 0 discrepancies, and there are no new error files. BCApps keeps
its 2.

- [ ] **Step 6: Commit**

```bash
git add tools/tests/test_relation_census.py tools/config_oracle/tests/test_link_incremental.py
git commit -m "test(b5b): zero-delta gate, census mutations, incremental parse

delta: 0 rows, 0 findings; tree-harness 0 changed files x 4 corpora. Scratch mutations: <results>.

[BC.History: 0 errors, 100% success]"
```

---

### Task 6: budget, full gates, WASM, docs

**Files:**
- Modify:
  - `CHANGELOG.md`
  - `CLAUDE.md`
  - `.claude/rules/scanner.md`
  - `docs/deferred-work.md`
  - `docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`
  - `tree-sitter-al.wasm` and `tree-sitter-al.wasm.inputs.sha256`
  - `tools/query_coverage/baseline.json` and `.grammar_baseline.json`, as the gates require

- [ ] **Step 1: Size and speed**

```bash
./tools/metrics.sh --vs 821c914 | tail -2
python -m tools.perf ab --lib-a "$SCRATCH/al_base5b.dll" --lib-b "$SCRATCH/al_b5b.dll" --corpus dc --rounds 24
```

`al_base5b.dll` (Task 1) IS the B5 library, so it is lib A.

Expected:
- STATE_COUNT ≤ 17,567.
- `ab` times EVERY DC file, because no DC tree changed. If `ab` refuses because trees differ,
  that contradicts Task 5: STOP. The confidence interval must contain 1.0, or the slowdown must
  be within its stated resolution.

- [ ] **Step 2: Full gates**

```bash
./tools/ts-lock.sh ./validate-grammar.sh --full
python tools/snip.py --census --root ./BC.History
python -m tools.query_coverage.qc run
python tools/traversal_census.py
./tools/ts-lock.sh python -m pytest tests/traversal -q && npm test
python -m pytest tools/tests tools/alc_facts/tests -q
```

  **How each gate is settled:**
  - **qc.** New `fields|skipped|hidden-rule` entries for the new hidden link rules, and nothing
    else: run `qc accept`, retrying on a file lock, and name the entries in the docs commit. Any
    other regression is a STOP.
  - **Step 8, the grammar-health snapshot.** Refresh `.grammar_baseline.json` the way
    `validate-grammar.sh` Step 8 says. Verify that every new `missing_definitions` entry is an
    external or an alias-only name, and record that in the `BASELINE_NOTE` comment in
    `tools/check_grammar_health.py`, as B5 did.
  - **The census step.** `validate-grammar.sh --full`'s Step 6c covers the new link checks.
    Confirm it ran.
  - **Everything else** exits 0. The only acceptable red is the WASM, which Step 3 fixes.

- [ ] **Step 3: WASM**, as its own commit:

```bash
./tools/ts-lock.sh tree-sitter build --wasm -o tree-sitter-al.wasm
./tools/check-wasm-fresh.sh --update && ./tools/check-wasm-fresh.sh
git add tree-sitter-al.wasm tree-sitter-al.wasm.inputs.sha256
git commit -m "build: rebuild tree-sitter-al.wasm for B5b

[BC.History: 0 errors, 100% success]"
```

- [ ] **Step 4: Docs** (spec §6). Follow B5's docs commit `296e263` for style.
  - **CHANGELOG `[Unreleased]` / `### Changed`:**
    - link syntax appears only under the six link properties;
    - a dotted or `field(...)` comparison elsewhere is a `property_expression`;
    - signed or decimal `const` arguments (if added) are links;
    - production trees are unchanged in all four corpora;
    - the STATE_COUNT and `ab` result.
  - **CLAUDE.md:**
    - keyed families go from four to five;
    - a `LINK_PROPERTY_NAME` token-table row;
    - the emission order: CalcFormula → ML → Namespaces → TableRelation → Link → generic →
      decline;
    - one sentence on deliberate over-acceptance across the three link delegates;
    - the identifier-initial scanner token count, eleven.
  - **`.claude/rules/scanner.md`:** the token row, "Eleven tokens", the emission order, and the
    three guards.
  - **`docs/deferred-work.md`,** new items with their probe evidence:
    - the trailing comma (B7);
    - `filter((...))`, if accepted;
    - `chartpart`, if accepted;
    - the generic `_in_if` empty-prefix split. Probe it, and count production with
      `./tools/corpus-grep.sh`, before writing the item.
  - **Roadmap:** a B5b done note with STATE_COUNT, `ab` and the zero-delta evidence.

- [ ] **Step 5: Commit the docs**

```bash
git status --short | grep -v '^??'
git add CHANGELOG.md CLAUDE.md .claude/rules/scanner.md docs/deferred-work.md \
  docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md
# plus tools/query_coverage/baseline.json, .grammar_baseline.json and tools/check_grammar_health.py if changed
git commit -m "docs: B5b done -- link family keyed by name, generic values lose link syntax

[BC.History: 0 errors, 100% success]"
```

- [ ] **Step 6: Cleanup.**
  - Delete the four snapshots:
    `for d in bc dc bc28 bcapps; do P=.snapshots/baseline-b5b-$d; rm -rf "${P:?}"; done`.
  - List any scratch worktrees (`git worktree list`) in the report. Do not force-remove them.
  - Kill only processes you started.
