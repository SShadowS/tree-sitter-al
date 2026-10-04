# B5 `TableRelation` keying: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** every `TableRelation` value is relation-shaped with one `qualified_name` target, no
other property's dotted value is a relation, and G10 parses clean, matching alc 18.0.41.

**Architecture:**
- The external scanner's single-read identifier dispatch emits a fourth keyed token,
  `TABLE_RELATION_PROPERTY_NAME`, for `TableRelation`.
- `property` gets a keyed arm whose value is a value-start relation (never beginning with
  `#if`) or a recursive whole-value `#if`.
- `table_relation_value` leaves the generic `_property_value` and the two generic `_in_if`
  hosts.
- `simple_table_relation` gets one `target: (qualified_name ...)`, whose segments follow the
  compiler's `ParseQualifiedName`.
- A committed census (`tools/relation_census.py`) checks the contract and classifies every
  tree difference against a pre-change parser library.

**Tech stack:**
- tree-sitter 0.27 grammar DSL (`grammar.js`) and its C external scanner (`src/scanner.c`).
- Corpus fixtures (`test/corpus/`).
- pytest.
- `tools.alc_probe` for compiler evidence.
- ilspycmd 11.0, for extracting compiler facts.

**Spec:** `docs/superpowers/specs/2026-10-04-table-relation-keying-design.md`, revision 3,
approved 2026-10-05. Read it before any task. Section numbers below (§) refer to it.

## Global constraints

- **Rules files bind every task:** CLAUDE.md, `.claude/rules/*.md` and
  `docs/agent-brief-rules.md`.
- **Git Bash with Windows paths.** Never `2>nul`. Run `tree-sitter` only through
  `./tools/ts-lock.sh`. `python -m tools.perf ab` takes the lock itself, so do not wrap it.
- **Branch:** `fix/b5-table-relation-keying`, off main HEAD. The grammar is unchanged since
  the B4 merge `6b15b9b`. Do not push.
- **Forbidden commands:**
  - `git stash`, `git reset --hard`, `git checkout --`, `git restore`, `git clean -f`.
  - `find /`, or any search outside the repo, the scratchpad or the four corpus roots.
  - `tail -f | grep` watchers.
- **Generated files:** commit `grammar.js`, `src/parser.c`, `src/grammar.json` and
  `src/node-types.json` together, plus `src/scanner.c` when it changed.
- **Commit messages:** every message ends with `[BC.History: N errors, X% success]`,
  measured, not copied.
- **The keyed name is exactly `TableRelation`.** Match it case-insensitively, whole word only.
  `ValidateTableRelation` and `TestTableRelation` stay generic.
- **Corpora:** `./BC.History`, `./DC`, `H:/Git/BC28.1`, `H:/Git/BCApps-29.0`.
- **Hard limits:**
  - Production trees may change only as D1, D2 and D3 (§4.2), proven by
    `relation_census.py delta`.
  - STATE_COUNT ≤ 17,231.
  - No new declared conflict unless it is necessary, and each one gets a comment explaining it.
- **`-u` traps:** after any `tree-sitter test -u`, run `git diff --stat test/corpus`. Restore
  untargeted files with `git show HEAD:path > path`.
- **Never commit decompiled compiler source.** Only the extracted facts files, the extractor,
  and line citations.
- **Scratchpad** (`$SCRATCH` in the commands below; set it first with `SCRATCH=<that path>`):
  `C:/Users/SShadowS/AppData/Local/Temp/claude/U--Git-tree-sitter-al/7735bcff-35e6-47ee-87b9-879d6fed9fe1/scratchpad`.
- **The compiler DLL** (`$ALC_DLL`):
  `C:/Users/SShadowS/.dotnet/tools/.store/microsoft.dynamics.businesscentral.development.tools/18.0.41.62505/microsoft.dynamics.businesscentral.development.tools/18.0.41.62505/tools/net10.0/any/Microsoft.Dynamics.Nav.CodeAnalysis.dll`.

## Review focus

1. **A compiler-allowed keyword token leaking into a generic value state.** `Visible = Table;`,
   `Image = Filter;`, `ApplicationArea = Assembly;` and `Description = Field;` must stay
   `identifier` leaves (the issue #27 class). Task 5 checks the lex states and adds these as
   regression fixtures.
2. **A quoted segment that contains a dot** (`"Acc. Schedule Name".Name`,
   `"G/L Account"."No."`). It is one segment, never split. Pinned in Task 4's fixture and by
   Task 3's normalisation test.
3. **A whole `TableRelation` property inside a `#if` in a field body**, as opposed to a `#if`
   inside its value: `#if X TableRelation = A; #else TableRelation = B; #endif`. The keyed
   token must be offered there. Task 5, host fixtures.
4. **An incremental edit that grows a target** (`Customer` → `System.Customer`, or adding
   `."No."`). The incremental tree must equal a fresh parse. Task 6, incremental test.
5. **A `TableRelation` comment between segments or before `where`**
   (`Customer /* c */ ."No." where(...)`). It stays one target, with the comment as an extra.
   Task 4 fixture, probed in Task 1.

---

### Task 1: baselines, compiler facts and compiler evidence

**Files:**
- Create:
  - `tools/alc_facts/__init__.py` (empty)
  - `tools/alc_facts/extract.py`
  - `tools/alc_facts/keyword-allowed-identifiers.txt`
  - `tools/alc_facts/property-hosts.tsv`
  - `tools/alc_facts/tests/test_extract.py`
  - `tools/alc_probe/cases/table-relation-keying/*.al`

**Interfaces:**
- Produces:
  - `.snapshots/baseline-b5`;
  - `$SCRATCH/al_base.dll`, the pre-change library used by Tasks 3 and 6;
  - `keyword-allowed-identifiers.txt`: one lowercase spelling per line after a `#` header;
  - `property-hosts.tsv`: columns `name_upper`, `host_kind`, `value_kind`, `delegate`;
  - `extract.load_keywords() -> list[str]`;
  - `extract.load_property_hosts() -> list[tuple[str, str, str, str]]`;
  - the decide-by-probe verdicts, recorded in the Task 1 commit message:
    - `TableRelation = ;`;
    - each integer form;
    - a continuation after a value-start `#if`.

- [ ] **Step 1: Branch, baselines, base library**

```bash
cd U:/Git/tree-sitter-al
git checkout -b fix/b5-table-relation-keying
./tools/ts-lock.sh ./tools/tree-harness.sh snapshot ./BC.History .snapshots/baseline-b5
./tools/metrics.sh > "$SCRATCH/metrics-base-b5.txt"; cat "$SCRATCH/metrics-base-b5.txt"
./tools/ts-lock.sh tree-sitter build -o "$SCRATCH/al_base.dll"
./tools/ts-lock.sh tree-sitter test 2>&1 | tail -1
```

Expected:
- the snapshot reports 15,358 files;
- STATE_COUNT=16893;
- `al_base.dll` exists;
- the test total is recorded. Use it as the base of every later count check; do not take it
  from CLAUDE.md.

- [ ] **Step 2: Write the failing extractor test**, `tools/alc_facts/tests/test_extract.py`:

```python
"""The committed compiler facts match what ObjectParser/SyntaxFacts say (spec §2.1)."""
from tools.alc_facts import extract


def test_keyword_set_has_the_compiler_size_and_known_members():
    kws = extract.load_keywords()
    assert len(kws) == 101
    for w in ("system", "table", "tabledata", "page", "codeunit", "field", "type",
              "filter", "order", "enum", "namespace", "group"):   # group = PageGroupKeyword
        assert w in kws
    for w in ("begin", "end", "where", "if", "else", "pagegroup"):
        assert w not in kws
    assert kws == sorted(set(kws))


def test_property_hosts_known_rows():
    rows = {(n, h): (vk, d) for n, h, vk, d in extract.load_property_hosts()}
    assert rows[("ENABLED", "PageField")][1] == "ParseClientSideBooleanExpressionPropertyValue"
    assert rows[("ENABLED", "Field")][1] == "ParseBooleanPropertyValue"
    assert rows[("INDENTATIONCOLUMN", "PageGroup")][1] == "ParseIntegerExpressionPropertyValue"
    assert rows[("AUTOFORMATEXPRESSION", "Field")][1] == "ParseTextExpressionPropertyValue"
    assert rows[("TABLERELATION", "Field")][1] == "ParseTableRelationPropertyValue"
    assert rows[("TABLERELATION", "PageField")][1] == "ParseTableRelationPropertyValue"
```

Run: `python -m pytest tools/alc_facts/tests/test_extract.py -q`
Expected: FAIL, with the module missing.

- [ ] **Step 3: Write `tools/alc_facts/extract.py`.**
  - It decompiles the three types with ilspycmd into a temp dir, never into the repo.
  - It extracts two things, then writes both data files with a provenance header: alc version,
    the DLL's sha256, the ilspycmd version, and the date:
    - the keyword spellings: every `case SyntaxKind.XKeyword:` in the `IsKeywordAllowedIdentifier`
      switch, mapped through `SyntaxKind.XKeyword => "text"` in `SyntaxFacts`;
    - every `instance.Add("NAME", new PropertyTypeInfo(...))` row with its host kind (the
      last string argument), its value kind (the 4th argument), and its delegate, resolving a
      `parseFuncN` variable or inline lambda to the `p.ParseXxxPropertyValue` it calls.

```python
"""Extract compiler facts from alc's CodeAnalysis DLL (spec 2026-10-04 §2.1).

    python -m tools.alc_facts.extract --dll "$ALC_DLL"   # rewrites the two data files

The decompiled source is read from a temp dir and never committed.
"""
from __future__ import annotations

import argparse, hashlib, re, subprocess, sys, tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYWORDS = HERE / "keyword-allowed-identifiers.txt"
HOSTS = HERE / "property-hosts.tsv"
TYPES = {
    "SyntaxFacts": "Microsoft.Dynamics.Nav.CodeAnalysis.SyntaxFacts",
    "ObjectParser": "Microsoft.Dynamics.Nav.CodeAnalysis.InternalSyntax.ObjectParser",
}


def _decompile(dll: Path, out: Path) -> dict[str, str]:
    src = {}
    for short, full in TYPES.items():
        r = subprocess.run(["ilspycmd", "-t", full, str(dll)], capture_output=True, text=True,
                           encoding="utf-8", check=True)
        src[short] = r.stdout
    return src


def keywords_from(syntax_facts: str) -> list[str]:
    body = syntax_facts.split("bool IsKeywordAllowedIdentifier", 1)[1]
    body = body.split("return true", 1)[0]
    kinds = re.findall(r"case SyntaxKind\.(\w+Keyword):", body)
    text = dict(re.findall(r"SyntaxKind\.(\w+Keyword) => \"([^\"]+)\"", syntax_facts))
    missing = [k for k in kinds if k not in text]
    if missing:
        raise SystemExit(f"no text for {missing}")
    return sorted({text[k].lower() for k in kinds})


ADD = re.compile(r'instance\.Add\("([A-Z0-9]+)", new PropertyTypeInfo\(PropertyKind\.\w+, "\w+", '
                 r'"[^"]*", "([^"]*)", (.*?)\)\);\s*$', re.M)
FUNC = re.compile(r"(parseFunc\d+) = .*?p\.(Parse\w+PropertyValue)\(", re.S)
INLINE = re.compile(r"p\.(Parse\w+PropertyValue)\(")


def hosts_from(object_parser: str) -> list[tuple[str, str, str, str]]:
    funcs = dict(FUNC.findall(object_parser))
    rows = []
    for m in ADD.finditer(object_parser):
        name, value_kind, rest = m.group(1), m.group(2), m.group(3)
        host = re.findall(r'"(\w+)"\s*$', rest)
        f = re.match(r"(parseFunc\d+)", rest)
        inline = INLINE.search(rest)
        delegate = funcs.get(f.group(1)) if f else (inline.group(1) if inline else None)
        if not host or not delegate:
            raise SystemExit(f"unparsed row {name}: {rest[:120]}")
        rows.append((name, host[0], value_kind, delegate))
    return sorted(set(rows))
```

  **The parser is checked against the source.** The `ADD` regex has to cope with rows whose
  delegate is an inline `delegate(ObjectParser p, ...) { ... }` block spanning several lines;
  ObjectParser line 862 is one. Adjust the regexes until:
  - every `instance.Add("` in the file yields exactly one row;
  - the count of rows equals `grep -c 'instance.Add("' ObjectParser.cs`.

  An unparsed row is an error, never a skip.

  Add the loaders and the CLI:

```python
def load_keywords() -> list[str]:
    return [l.strip() for l in KEYWORDS.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


def load_property_hosts() -> list[tuple[str, str, str, str]]:
    out = []
    for l in HOSTS.read_text(encoding="utf-8").splitlines():
        if l and not l.startswith("#"):
            out.append(tuple(l.split("\t")))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dll", required=True, type=Path)
    a = ap.parse_args(argv)
    sha = hashlib.sha256(a.dll.read_bytes()).hexdigest()
    ver = subprocess.run(["ilspycmd", "--version"], capture_output=True, text=True).stdout.split()[1]
    head = (f"# extracted {date.today()} from {a.dll.name} sha256={sha}\n"
            f"# alc 18.0.41.62505, ilspycmd {ver}; tools/alc_facts/extract.py; spec 2026-10-04 §2.1\n")
    with tempfile.TemporaryDirectory() as td:
        src = _decompile(a.dll, Path(td))
    kws = keywords_from(src["SyntaxFacts"])
    rows = hosts_from(src["ObjectParser"])
    KEYWORDS.write_text(head + "\n".join(kws) + "\n", encoding="utf-8", newline="\n")
    HOSTS.write_text(head + "# name_upper\thost_kind\tvalue_kind\tdelegate\n"
                     + "".join("\t".join(r) + "\n" for r in rows), encoding="utf-8", newline="\n")
    print(f"keywords={len(kws)} property-host rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Run:

```bash
python -m tools.alc_facts.extract --dll "$ALC_DLL"
python -m pytest tools/alc_facts/tests/test_extract.py -q
```

Expected: `keywords=101`, and both tests pass. If the keyword count is not 101, the switch
parse is wrong. Fix the extractor; never edit the data file by hand.

- [ ] **Step 4: Write the alc_probe cases**, one file per §5.1 item, under
  `tools/alc_probe/cases/table-relation-keying/`, in the header format of
  `tools/alc_probe/README.md`.

  **Every case is self-contained.** It declares the tables it relates to (`Customer`,
  `"G/L Account"`, `Vendor`, and so on) with a `"No."` field, so an unknown symbol cannot pose
  as a rejection. Namespace-qualified cases declare `namespace System.Environment;` in a
  separate object file of the same case. If one file cannot hold two namespaces, use
  `tools/alc_probe`'s multi-file form, as its README describes.

  Example, `bare-table-field.al`:

```al
// A bare TableRelation target in a table field: a relation to alc (B5 §2.1).
// source: docs/superpowers/specs/2026-10-04-table-relation-keying-design.md §5.1
// expect: * accept
table 50101 Customer { fields { field(1; "No."; Code[20]) { } } }
table 50100 T
{
    fields { field(1; F; Code[20]) { TableRelation = Customer; } }
}
```

  **The full case list:**
  - **Accept:** each of these in a table field AND in a page field. A page needs
    `SourceTable`, and its field uses `TableRelation` on a page field.
    - bare, quoted, dotted, quoted-with-dot (`"Acc. Sched. Name".Name`);
    - a keyword first segment;
    - `where`, `if`/`else`;
    - `tablerelation`;
    - a comment between segments;
    - whole-value `#if`, with the `;` after `#endif`, with it in the arms, and nested;
    - the DC `else` + `#if`-arms-with-`;` shape;
    - `AutoFormatExpression = Rec."Currency Code";`;
    - `AutoFormatExpression = Rec2[1]."Currency Code";`, where `Rec2` is an array global.
  - **Keyword segments:** 12 spellings from `keyword-allowed-identifiers.txt`. They are
    `system`, `table`, `field`, `order`, `filter`, `group`, `enum`, `type`, `page`,
    `namespace`, `dataset` and `labels`. Each one is a table name used in three places:
    - first segment;
    - middle segment, under a namespace;
    - last segment, as a field name.

    Use a mixed-case spelling. Each case declares a table, or a field, named that way.
    Expected: accept.
  - **Two segments outside the set,** `begin` and `where`, as table names. Expected: reject.
  - **Decide-by-probe:**
    - `TableRelation = ;`;
    - `= 18;`, `= 18."No.";`, `= Customer.18;`, `= 18 where("No." = const('A'));`;
    - `#if X if (F = const(1)) A #else if (F = const(2)) B #endif else C;`.

    Write each with `// expect: * accept`, run it, then record the real verdict in the header.
    A decide-by-probe case is the one place the expectation follows the compiler.
  - **G10:** use the four-way form, `// expect: X accept` and `!X accept`, with `X` defined and
    undefined.
  - **Reject:**
    - `MakeCustomer()."No."`, with `MakeCustomer` a local procedure;
    - `Customers[1]."No."`;
    - `(A + B).F`;
    - `TableRelation = where("No." = const('A'));`;
    - `Enabled = Rec."X";` in a table field.

- [ ] **Step 5: Run and pin**

Run: `python -m tools.alc_probe run tools/alc_probe/cases/table-relation-keying --check`
Expected: exit 0. A drift on a non-decide case is a STOP. Report it: it means §5.1's premise
is wrong, so do not edit `expect` to make it pass.

**What the decide-by-probe verdicts change:**

| verdict | effect |
|---|---|
| `TableRelation = ;` rejected | Task 4 drops `optional()` around the keyed value, and the case becomes a negative |
| any integer form accepted | STOP: §3.2 item 2 must be revised with the accepting path, before Task 4 |
| value-start `#if` + continuation accepted | STOP: §3.2 item 4 must be redesigned before Task 4 |

- [ ] **Step 6: Commit**

```bash
git add tools/alc_facts tools/alc_probe/cases/table-relation-keying
git commit -m "test(alc): B5 compiler facts and TableRelation evidence -- alc 18.0.41

Decide-by-probe: TableRelation = ; <accept|reject>; integer targets <...>;
value-start #if continuation <...>.

[BC.History: 0 errors, 100% success]"
```

---

### Task 2: G10, measured in isolation (§3.3)

**Files:**
- Scratch only: a git worktree at `$SCRATCH/wt-g10`. Nothing is committed in this task.

**Interfaces:**
- Produces:
  - the G10 tree, after both generic relation routes are removed;
  - a verdict, PASS or STOP. Task 4 records it in its commit message.

- [ ] **Step 1: Worktree and removal**

```bash
git worktree add --detach "$SCRATCH/wt-g10" HEAD
cd "$SCRATCH/wt-g10"
```

  In `grammar.js`:
  - delete the `$.table_relation_value,` line from `_property_value`;
  - in `_property_with_terminator_in_if`, delete
    `alias($._table_relation_split_value, $.table_relation_value),` from the value choice.

  Nothing else changes. `TableRelation` regresses in this worktree, and that is expected.

- [ ] **Step 2: Generate and parse G10**

```bash
tree-sitter generate 2>&1 | tail -5
printf 'page 50100 P\n{\n    layout { area(Content) { field(F; Rec.F)\n    {\n        Visible = Rec.A\n#if X\n            and B\n#endif\n        ;\n    }\n    }\n    }\n}\n' > "$SCRATCH/g10.al"
tree-sitter parse "$SCRATCH/g10.al"
```

  Generation may report a conflict only because an entry in `conflicts` now names a rule that
  is no longer in conflict. If so, delete that entry here, and note its text for Task 4.

**Expected for PASS:**
- `has_error` is false;
- the value is `property_expression`, with a member-expression `Rec.A` and a
  `preproc_conditional_expression_tail` holding `and B`;
- the fields are exact.

Confirm with:

```bash
python -c "
import sys; sys.path.insert(0, r'$SCRATCH/wt-g10')
from tools.query_coverage import loader
from pathlib import Path
p = loader.make_parser(loader.load_language(loader.ensure_library(Path(r'$SCRATCH/wt-g10'))))
t = p.parse(open(r'$SCRATCH/g10.al','rb').read()); print(t.root_node.has_error); print(t.root_node)"
```

- [ ] **Step 3: Verdict.**
  - **PASS:** record the printed tree, then remove the worktree with
    `git worktree remove --force "$SCRATCH/wt-g10"`.
  - **ERROR:** STOP. Report the debug parse (`tree-sitter parse -d`) and
    `python parse_bug_finder.py`. The fix becomes its own task, planned from that evidence. Do
    not start Task 4.

---

### Task 3: the relation census (`tools/relation_census.py`)

**Files:**
- Create:
  - `tools/relation_census.py`
  - `tools/tests/test_relation_census.py`

**Interfaces:**
- Consumes:
  - `$SCRATCH/al_base.dll` (Task 1);
  - `tools.alc_facts.extract.load_property_hosts()` (Task 1);
  - `tools.query_coverage.loader.load_language(path)`, `make_parser(lang)`,
    `ensure_library(repo_root)`.
- Produces, for Tasks 4 to 6:
  - the CLI
    `python tools/relation_census.py check|delta [--root DIR]... [--base-lib DLL] [--cur-lib DLL] [--manifest OUT.tsv]`;
  - its exit codes: 0 clean, 1 finding, 2 cannot run;
  - `normalise_old_target(node) -> list[tuple[int, int, bytes]]`, raising
    `Unclassifiable` on any other base;
  - `segments(qualified_name_node) -> list[tuple[int, int, bytes]]`;
  - `CONTEXT_HOSTS`, a dict from a tree-context key to a tuple of compiler host kinds;
  - `check_tree(path: str, tree, src: bytes) -> list[Finding]`, the per-file core of `check`;
  - `classify(name: str, old_value, new_value) -> str`. It returns `"D1"`, `"D2"` or `"D3"`,
    or raises `Unclassifiable`, the per-site core of `delta`.

  Task 6's mutation tests call these two functions on in-memory trees.

- [ ] **Step 1: Write the failing tests**, in `tools/tests/test_relation_census.py`. They run
  against the CURRENT library, before any grammar change, and pin the normalisation on today's
  trees:

```python
import pytest
from tools import relation_census as rc


def _value(src: bytes):
    tree = rc.parser_for(None).parse(src)
    props = [n for n in rc.walk(tree.root_node) if n.type == "property"]
    return props[0].child_by_field_name("value"), src


def _field(prop):
    return b"table 50100 T\n{\n    fields { field(1; F; Code[20])\n    {\n        " + prop + b"\n    }\n    }\n}\n"


@pytest.mark.parametrize("prop,want", [
    (b'TableRelation = Customer."No.";', [b"Customer", b'"No."']),
    (b'TableRelation = "Acc. Sched. Name".Name;', [b'"Acc. Sched. Name"', b"Name"]),
    (b"TableRelation = System.Environment.Company.Name;", [b"System", b"Environment", b"Company", b"Name"]),
])
def test_old_target_normalisation(prop, want):
    v, src = _value(_field(prop))
    tr = next(n for n in rc.walk(v) if n.type == "simple_table_relation")
    assert [t for _, _, t in rc.normalise_old_target(tr)] == want


def test_old_target_rejects_expression_base():
    v, src = _value(_field(b"TableRelation = MakeCustomer().\"No.\";"))
    tr = next(n for n in rc.walk(v) if n.type == "simple_table_relation")
    with pytest.raises(rc.Unclassifiable):
        rc.normalise_old_target(tr)


def test_check_flags_todays_contract_breaks(tmp_path):
    (tmp_path / "a.al").write_bytes(_field(b"TableRelation = Customer;"))
    (tmp_path / "b.al").write_bytes(_field(b'AutoFormatExpression = Rec."Currency Code";'))
    findings = rc.check([tmp_path], rc.parser_for(None))
    kinds = sorted(f.kind for f in findings)
    assert "relation-shape" in kinds        # bare TableRelation is a leaf today
    assert "relation-outside" in kinds      # D2 is a relation today
```

Run: `python -m pytest tools/tests/test_relation_census.py -q`
Expected: FAIL, with the module missing.

- [ ] **Step 2: Implement.** Core code:

```python
"""B5 relation census: the TableRelation contract and the D1/D2/D3 delta (spec 2026-10-04 §5.5).

    python tools/relation_census.py check --root ./BC.History
    python tools/relation_census.py delta --root ./BC.History --base-lib BASE.dll [--manifest OUT.tsv]

Exit 0 clean, 1 finding, 2 cannot run (a census that cannot run never reports clean).
"""
from __future__ import annotations

import argparse, hashlib, sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.query_coverage import loader  # noqa: E402

RELATION_TYPES = {"table_relation_value", "preproc_conditional_table_relation",
                  "simple_table_relation", "qualified_name"}
D2_NAMES = {"autoformatexpression", "enabled", "styleexpr", "datacaptionexpression",
            "visible", "indentationcolumn", "editable", "showmandatory"}


class Unclassifiable(Exception):
    pass


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    start: int
    end: int
    detail: str


def parser_for(lib: Path | None):
    path = lib or loader.ensure_library(loader.REPO_ROOT)
    return loader.make_parser(loader.load_language(path))


def walk(n):
    st = [n]
    while st:
        n = st.pop()
        yield n
        st.extend(reversed(n.children))


def prop_name(p) -> str:
    nm = p.child_by_field_name("name")
    return nm.text.decode("utf-8", "replace").lower() if nm else ""


def segments(qn) -> list[tuple[int, int, bytes]]:
    return [(c.start_byte, c.end_byte, c.text) for c in qn.named_children]


def normalise_old_target(str_node) -> list[tuple[int, int, bytes]]:
    """Pre-B5 simple_table_relation -> ordered segments (spec §4.2, D3 normalisation)."""
    tables = str_node.children_by_field_name("table")
    out: list[tuple[int, int, bytes]] = []

    def norm(n):
        if n.type in ("identifier", "quoted_identifier", "keyword_identifier"):
            out.append((n.start_byte, n.end_byte, n.text))
        elif n.type == "member_expression":
            norm(n.child_by_field_name("object"))
            m = n.child_by_field_name("member") or n.child_by_field_name("property")
            if m is None:
                raise Unclassifiable(f"member_expression without member at {n.start_byte}")
            out.append((m.start_byte, m.end_byte, m.text))
        else:
            raise Unclassifiable(f"{n.type} at {n.start_byte}")

    for t in tables:
        norm(t)
    return out
```

  **The `member` field name.** Read `node-types.json` for `member_expression`'s fields before
  relying on `member`. Use `python tools/nodetypes.py show member_expression`, and keep only
  the field that actually exists.

  Then write `check_tree(path, tree, src) -> list[Finding]`, and
  `check(roots, parser) -> list[Finding]`, which reads each `*.al` file under the roots and
  calls `check_tree`. Together they implement the §5.5 `check` table:
  - **relation-shape:** every `property` named `tablerelation` with a value has value type
    `table_relation_value` or `preproc_conditional_property_value`. Recurse through that
    wrapper's `value` fields.
  - **relation-outside:** any node whose type is in `RELATION_TYPES` with no ancestor
    `property` named `tablerelation`.
  - **target:** run only once the grammar has `qualified_name`, which is when node-types
    contains it. Every `simple_table_relation` has exactly one `target` child, of type
    `qualified_name`, and no `table` field. Every segment is an `identifier` or
    `quoted_identifier` with `child_count == 0`.
  - **d2-host:** for a `property` named in `D2_NAMES`, compute its context key, look it up in
    `CONTEXT_HOSTS`, and require every host's row in `load_property_hosts()` for that name to
    have a delegate in this set: `ParseTextExpressionPropertyValue`,
    `ParseClientSideBooleanExpressionPropertyValue`, `ParseStyleExpressionPropertyValue`,
    `ParseIntegerExpressionPropertyValue`. A context key missing from `CONTEXT_HOSTS` is the
    finding `d2-unmapped`.
  - **has-error:** `root_node.has_error`, as the finding `has-error`.

  The context key is the type sequence of the nearest three named ancestors, e.g.
  `("field_declaration", "fields_body", "fields_section")` or `("page_field", ...)`.

  **Build `CONTEXT_HOSTS` from data.** Run `check` once over the four corpora with the map
  empty, collect every distinct `d2-unmapped` key, and map each one by hand to the compiler
  host kinds from spec §2.1. Commit the map with a comment per key naming the grammar context.
  A `modify` context maps to every host in its lookup chain (`LookupAnyControlProperty` /
  `LookupAnyActionProperty`).

  Then write `delta(roots, base_parser, cur_parser) -> (findings, manifest_rows)`:
  - For each file, check that the source sha256 is the same for both parses, and parse with
    both parsers.
  - Build each inventory: a dict from `(path, start_byte, end_byte)` to the `property` node.
    A key in one inventory and not the other is the finding `site-dropped`.
  - Compare each property's `value` subtree with its old version, using
    `str(node)` S-expressions. If they are equal, nothing is recorded. Otherwise call
    `classify(name, old_value, new_value)`, in which exactly one predicate must hold:
    - **D1:** the name is `tablerelation`; the old value is an `identifier` or
      `quoted_identifier` leaf; the new value is
      `table_relation_value(table_relation_expression(simple_table_relation target: qualified_name))`;
      and `segments(new qn)` has the leaf as its single segment, same span and text.
    - **D2:** the name is not `tablerelation`; the old value is `table_relation_value`; the new
      value is `property_expression`. The new dotted chain (the `member_expression` objects
      and members, a subscript taken as its base) has the same leaf spans as the old
      `normalise_old_target`.
    - **D3:** the name is `tablerelation`, and the old value type equals the new one. Pair
      the old and new `simple_table_relation` nodes in document order. For each pair,
      `normalise_old_target(old) == segments(new target)`. The two trees with every target
      subtree replaced by a placeholder are string-equal.
  - A difference matching no predicate is the finding `unclassified`; one matching two is
    `ambiguous`. `Unclassifiable` raised during D3 is the finding `unclassifiable`.
  - A manifest row is `path, start, end, sha256, name, class, old_type, new_type`.

  **`main`.** Build the argparse CLI, print a summary line like `has_error_sweep.py`, and
  return 0, 1 or 2. Return 2 on an unreadable root, a library that fails to load, or a source
  hash mismatch.

- [ ] **Step 3: Run the tests**

Run: `python -m pytest tools/tests/test_relation_census.py -q`
Expected: PASS against today's grammar.

- [ ] **Step 4: Today's corpus, as a baseline fact**

```bash
python tools/relation_census.py check --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0
```

Expected: exit 1, with about 36,118 `relation-shape` findings and 14,011 `relation-outside`
ones. These are today's defects, recorded in the commit message.

- [ ] **Step 5: Commit**

```bash
git add tools/relation_census.py tools/tests/test_relation_census.py
git commit -m "test(b5): relation census -- check and delta modes (spec §5.5)

Today: relation-shape <N>, relation-outside <M> (the D1/D2 defects).

[BC.History: 0 errors, 100% success]"
```

---

### Task 4: keying, `qualified_name`, the keyed value productions

**Files:**
- Modify: `src/scanner.c`:
  - the `TokenType` enum (`:14-31`);
  - the `IdentifierWord` enum (`:278-287`) and `read_identifier_word` (`:314-332`);
  - the recovery guard (`:556-567`);
  - the dispatch guard (`:950-951`);
  - the property-block guard and emission (`:1023-1060`).
- Modify: `grammar.js`:
  - `externals` (`:205-225`);
  - `property` (`:809-860`);
  - `_property_value` (`:1121`);
  - `_property_with_terminator_in_if` (`:940-962`);
  - `_property_whole_value_in_if` (`:985-1001`);
  - `_table_relation_split_value` (`:1063-1066`);
  - `table_relation_value` (`:1602-1606`);
  - `simple_table_relation` (`:1657-1660`);
  - `_namespaced_ref_table` (`:2239`), which is deleted if this task leaves it unused;
  - the `conflicts` entries naming relation rules (`:300-420`).
- Modify: `tools/check-field-types.py` (`:149-151`).
- Create:
  - `test/corpus/table_relation_keying_test.txt`
  - `test/corpus/table_relation_keying_negative_test.txt`
- Modify:
  - every existing fixture whose expected tree changes (22 files assert relation nodes);
  - `tools/deliberate-negatives.txt`;
  - `tools/config_oracle/tests/test_table_relation.py` and
    `test_property_value_conditional.py`, only where a test asserted a pre-B5 relation shape;
  - `tools/config_oracle/fixture-classes.tsv`, only if the quick tier asks for it.

**Interfaces:**
- Consumes:
  - Task 1's `keyword-allowed-identifiers.txt` and the decide-by-probe verdicts;
  - Task 2's G10 PASS;
  - Task 3's `relation_census.py check`.
- Produces:
  - the external `$._table_relation_property_name`, which is [17];
  - the node type `qualified_name`;
  - the field `simple_table_relation.target`;
  - the hidden rules `_table_relation_property_value`, `_table_relation_rooted`,
    `_table_relation_whole_conditional` and `_table_relation_keyed_split`.

- [ ] **Step 1: Write the failing positive fixture**,
  `test/corpus/table_relation_keying_test.txt`. Write each expected tree with field labels. It
  is generated in Step 6 and checked by hand there. The cases:
  - every row of spec §4.1;
  - bare, quoted, quoted-with-dot, dotted, `System.Environment.Company.Name`;
  - `where`, `if`/`else`;
  - lowercase and uppercase names;
  - `TableRelation /* c */ = A;`;
  - `TableRelation = Customer /* c */ ."No.";` (Review focus 5);
  - whole-value `#if` with both `;` placements, and nested;
  - the DC `else` + `#if` shape, verbatim from `CDCDataTranslation.Table.al:129-148`;
  - G10, with the tree recorded in Task 2;
  - `ValidateTableRelation = false;` and `TestTableRelation = false;` as generic boolean
    properties;
  - `AutoFormatExpression = Rec."Currency Code";` as `property_expression`;
  - `AutoFormatExpression = CustLedgEntry[6]."Currency Code";`.

Run: `./tools/ts-lock.sh tree-sitter test --file-name table_relation_keying_test.txt`
Expected: FAIL on the D1, D2, D3, G10 and whole-value cases.

- [ ] **Step 2: Scanner.**

```c
// enum TokenType -- append, never renumber
  TABLE_RELATION_PROPERTY_NAME = 17,  // `TableRelation` followed by = (B5)

// enum IdentifierWord -- append after WORD_NAMESPACES
  WORD_TABLE_RELATION,  // value grammar: TableRelationPropertyValueSyntax (B5)
```

  In `read_identifier_word`, after the `namespaces` line:

```c
  if (len == 13 && strcmp(buf, "tablerelation") == 0) return WORD_TABLE_RELATION;
```

  Add `&& valid_symbols[TABLE_RELATION_PROPERTY_NAME]` to the recovery guard. Add
  `|| valid_symbols[TABLE_RELATION_PROPERTY_NAME]` to the dispatch guard (`:951`) and to the
  property-block guard (`:1024`). In the emission chain, after the Namespaces branch:

```c
        } else if (word == WORD_TABLE_RELATION && valid_symbols[TABLE_RELATION_PROPERTY_NAME]) {
          lexer->result_symbol = TABLE_RELATION_PROPERTY_NAME;
```

  Extend the comment above the chain with one sentence: TableRelation is keyed because its
  value is the compiler's relation grammar (spec 2026-10-04 §2.1).

- [ ] **Step 3: Grammar.** Make all of these in one edit; partial states do not generate.

```javascript
// externals: append
    $._table_relation_property_name, // [17] `TableRelation` followed by = (B5)

// property: a fourth keyed arm after Namespaces. Drop optional() if Task 1 found
// `TableRelation = ;` rejected.
      seq(
        field('name', alias($._table_relation_property_name, $.property_name)),
        '=',
        optional(field('value', $._table_relation_property_value)),
        ';'
      ),

    // TableRelation's value is the compiler's relation grammar (ParseTableRelationPropertyValue:
    // optional if(...), ONE ParseQualifiedName target, optional where, optional else). A value
    // never starts with #if as a relation: a value-start #if is the whole-value wrapper, so
    // each input has one derivation (spec 2026-10-04 §3.2 item 4).
    _table_relation_head: $ => choice($.simple_table_relation, $.if_table_relation),
    _table_relation_property_value: $ => choice(
      alias($._table_relation_rooted, $.table_relation_value),
      alias($._table_relation_whole_conditional, $.preproc_conditional_property_value),
    ),
    _table_relation_rooted: $ => prec.right(5, seq(
      alias($._table_relation_head, $.table_relation_expression),
      optional($.preproc_conditional_table_relation),
    )),
    _table_relation_whole_conditional: $ => keyedValueConditional($,
      seq(field('value', $._table_relation_property_value), optional(';'))),
    _table_relation_keyed_split: $ => choice(
      seq(alias($._table_relation_head, $.table_relation_expression),
          $.preproc_conditional_table_relation),
      alias($._table_relation_open_if, $.table_relation_expression),
    ),

    simple_table_relation: $ => prec.right(20, seq(
      field('target', $.qualified_name),
      optional(prec(25, $.where_clause)),
    )),

    // The relation target, as alc's ParseQualifiedName reads it: identifier-token segments,
    // where an identifier token is IdentifierToken or one of the 101 IsKeywordAllowedIdentifier
    // keywords (tools/alc_facts/keyword-allowed-identifiers.txt). Segments carry no field:
    // which one is the table needs symbol resolution (spec 2026-10-04 §3.2 item 1).
    qualified_name: $ => prec.right(seq(
      $._qualified_name_segment,
      repeat(seq('.', $._qualified_name_segment)),
    )),
    _qualified_name_segment: $ => choice(
      $.identifier,
      $.quoted_identifier,
      alias($._keyword_allowed_identifier, $.identifier),
    ),
```

  **`_keyword_allowed_identifier`** is generated from the facts file by a module-level helper
  at the top of `grammar.js`:

```javascript
const KEYWORD_ALLOWED_IDENTIFIERS = require('fs')
  .readFileSync(require('path').join(__dirname, 'tools/alc_facts/keyword-allowed-identifiers.txt'), 'utf8')
  .split(/\r?\n/).filter(l => l && !l.startsWith('#'));
// ... in rules:
    _keyword_allowed_identifier: $ => choice(...KEYWORD_ALLOWED_IDENTIFIERS.map(w => kw(w))),
```

  If `tree-sitter generate` refuses `require('fs')`, use the fallback. Check that it refuses by
  running generate, not by assumption. The fallback inlines the 101 `kw('...')` calls,
  generated by
  `python -c "from tools.alc_facts.extract import load_keywords as k; print(', '.join(f\"kw('{w}')\" for w in k()))"`.
  A comment above the list then names the facts file, and Task 6 adds a pytest that compares
  the inlined list with `load_keywords()`.

  **The other edits, in the same step:**
  - `_property_value`: delete `$.table_relation_value,`.
  - `_property_with_terminator_in_if`: replace the
    `alias($._table_relation_split_value, $.table_relation_value)` value alternative with a
    keyed arm:

```javascript
      seq(
        field('name', alias($._table_relation_property_name, $.property_name)),
        '=',
        field('value', choice(
          alias($._table_relation_whole_conditional, $.preproc_conditional_property_value),
          alias($._table_relation_keyed_split, $.table_relation_value),
        )),
      ),
```

  - `_property_whole_value_in_if`: add the same keyed arm, with the whole conditional only.
  - Delete `_table_relation_split_value`, and the now-unused `table_relation_value` rule body.
    `table_relation_value` survives only as an alias name. Check with
    `grep -n "table_relation_value" grammar.js`: every remaining reference is an `alias(...,
    $.table_relation_value)` or a comment.
  - Delete `_namespaced_ref_table`, and its two `conflicts` entries, if no use is left.
    `_namespaced_ref_table_name` stays.
  - `table_relation_expression`: keep its `preproc_conditional_table_relation` alternative,
    because `if_table_relation.else_relation` needs it for the DC shape.

- [ ] **Step 4: Generate**

```bash
./tools/ts-lock.sh tree-sitter generate 2>&1 | tail -8
```

  **If the generator reports an unnecessary conflict,** delete that entry, and record its text
  for the commit message.

  **If it reports a new conflict:**
  - First record the exact edit that was tried (CLAUDE.md, "Two rules about verification").
  - Settle it with precedence on the keyed rules.
  - Declare a conflict only if precedence cannot, with a comment naming the two readings.

- [ ] **Step 5: Field contract.** In `tools/check-field-types.py`, replace the
  `simple_table_relation` / `table` entry with:

```python
    inv('simple_table_relation', 'target', False, set(), 'FIXED',
        "B5: one qualified_name target, as alc's ParseQualifiedName; was a 'table' field on "
        "every segment plus a member_expression escape",
        types={'qualified_name'}),
```

Run: `python tools/check-field-types.py`
Expected: exit 0.

- [ ] **Step 6: Run the new fixture, then rewrite the existing ones**

```bash
./tools/ts-lock.sh tree-sitter test --file-name table_relation_keying_test.txt
./tools/ts-lock.sh tree-sitter test 2>&1 | grep -E "✗|failure|^Total" | head -60
```

  The new fixture must pass. For every other failing case, read the actual tree and assign
  each hunk to D1, D2, D3, F1, F2 or F3. A hunk that fits none is a STOP: report it, do not
  rewrite it.

  Rewrite the expectations only after every hunk is assigned. Prefer editing by hand. If you
  use `-u`, use it per file, with `--file-name X`, and run `git diff --stat test/corpus`
  straight after. Restore any untargeted file with `git show HEAD:path > path`. Then read the
  whole diff of each targeted file, because `-u` strips field labels it did not have (trap 2).

  **The same rule for the oracle tests:**
  - `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_table_relation.py tools/config_oracle/tests/test_property_value_conditional.py -q`
  - A test that asserted a relation reading for a non-`TableRelation` value is rewritten to
    F3, with the reason in a comment.

- [ ] **Step 7: Prove the fixture can fail.** Rename one `target:` to `bogus:`, run Step 6's
  first command, see FAIL, then revert.

- [ ] **Step 8: Negative fixture**, `test/corpus/table_relation_keying_negative_test.txt`, with
  one case per Task 1 reject. Each expected tree is written by hand, as it really comes out,
  with the ERROR inside the value. A reject must never come out as a clean
  `property_expression` or a clean target.

  Add the file to `tools/deliberate-negatives.txt`, citing the Task 1 probe files. Then run:
  - `./tools/ts-lock.sh tree-sitter test --file-name table_relation_keying_negative_test.txt`
    (PASS);
  - `python tools/has_error_sweep.py --corpus-fixtures` (exit 0).

- [ ] **Step 9: Census and quick validation**

```bash
./tools/ts-lock.sh ./validate-grammar.sh
python tools/relation_census.py check --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0
python -m tools.config_oracle run --tier quick
```

Expected:
- `validate-grammar.sh` exits 0. Its case count equals Task 1's total, plus the cases added,
  minus nothing.
- `check` exits 0.
- The oracle quick tier exits 0. A new fixture record is classified with
  `evidence: alc_probe tools/alc_probe/cases/table-relation-keying/<file>.al`.

- [ ] **Step 10: Commit.** Run `./parse-al-parallel.sh ./BC.History/ .` for the count.

```bash
git add src/scanner.c grammar.js src/parser.c src/grammar.json src/node-types.json \
  tools/check-field-types.py tools/deliberate-negatives.txt test/corpus tools/config_oracle
git commit -m "fix(grammar): key TableRelation by name, one qualified_name target (B5, G10)

G10 (Task 2): <tree>. Conflicts removed: <list or none>.

[BC.History: 0 errors, 100% success]"
```

---

### Task 5: scanner-state audit, keyword containment, host fixtures

**Files:**
- Modify: `test/corpus/table_relation_keying_test.txt`, adding the host cases and the audit
  header.
- Create:
  - `test/corpus/table_relation_keyword_containment_test.txt`
  - `tools/tests/test_keyword_containment.py`

**Interfaces:**
- Consumes: Task 4's grammar.
- Produces: the audit result, recorded as the fixture header comment.

- [ ] **Step 1: The two-direction audit (§5.4)**

```bash
grep -n "ts_external_scanner_states" -A70 src/parser.c | head -100
```

  For every row, record:
  - (a) `property_name` without `_table_relation_property_name`;
  - (b) a keyed token without `property_name`.

  Map each such row to its grammar host, using `tree-sitter generate --report-states-for-rule
  property` or a debug parse. Every (a) host must be one where `TableRelation` cannot occur,
  e.g. `caption_value` sub-fields, with a debug parse as evidence. Every (b) row needs an
  explanation. Write the table into the fixture header.

  If a real field host lacks the keyed token, give it the keyed arm. Do not paper over it.

- [ ] **Step 2: Keyword containment (Review focus 1).** A behavioral proof over all 101
  words: no generic property value may parse differently from the pre-change library. Create
  `tools/tests/test_keyword_containment.py`:

```python
"""B5 Review focus 1: the 101 keyword-allowed segment tokens never leak into a generic
property value (the issue #27 class). Every generic placement must give the same tree as the
pre-B5 library."""
import os
from pathlib import Path
import pytest
from tools import relation_census as rc
from tools.alc_facts.extract import load_keywords

BASE = os.environ.get("B5_BASE_LIB")   # $SCRATCH/al_base.dll; the test skips without it
SITES = [
    b"table 50100 T\n{\n    fields { field(1; F; Code[20])\n    {\n        Description = %s;\n    }\n    }\n}\n",
    b"page 50100 P\n{\n    layout { area(Content) { field(F; Rec.F)\n    {\n        Visible = %s;\n"
    b"        Image = %s;\n        ApplicationArea = %s;\n    }\n    }\n    }\n}\n",
]


@pytest.mark.skipif(not BASE, reason="set B5_BASE_LIB to the pre-B5 library")
@pytest.mark.parametrize("word", load_keywords())
def test_generic_value_tree_unchanged(word):
    base, cur = rc.parser_for(Path(BASE)), rc.parser_for(None)
    w = word.capitalize().encode()
    for site in SITES:
        src = site.replace(b"%s", w)
        assert str(cur.parse(src).root_node) == str(base.parse(src).root_node), (word, src)
```

Run: `B5_BASE_LIB="$SCRATCH/al_base.dll" ./tools/ts-lock.sh python -m pytest tools/tests/test_keyword_containment.py -q`
Expected: 101 passed.

  Also write the containment fixture, so `tree-sitter test` pins the shape without the base
  library. Generic properties whose value is one of these words must stay `identifier` leaves:
  - `Visible = Table;`
  - `Image = Filter;`
  - `ApplicationArea = Assembly;`
  - `Description = Field;`
  - `CaptionClass = Order;`
  - `Editable = Type;`

  Run it. Also re-run the issue #27 fixture:
  `./tools/ts-lock.sh tree-sitter test -i "issue 27"`, or, if no case is named that, the
  fixture `grep -l "Type = Type::Alpha" test/corpus` finds.

  **A failure is a leak, and a STOP:** report the word and both trees.

- [ ] **Step 3: Host fixtures (§5.2, Review focus 3).** Add one case per host and form from the
  §5.2 table:

  | host | flat | whole-value `#if` | continued |
  |---|---|---|---|
  | table field | ✓ | ✓ | ✓ |
  | tableextension added field | ✓ | ✓ | ✓ |
  | tableextension `modify` | ✓ | ✓ | ✓ |
  | page field | ✓ | ✓ | ✓ |
  | pageextension `modify` | ✓ | ✓ | ✓ |
  | report request-page field | ✓ | | |
  | xmlport request-page field | ✓ | | |

  Also add a whole `TableRelation` property inside a field-body `#if`/`#else`.

  Every host case also goes into `tools/alc_probe/cases/table-relation-keying/` as
  `host-<name>.al` with `// expect: * accept`, and is run with `--check`. The fixture is not
  committed for a host alc rejects.

- [ ] **Step 4: The two production `else` + `#if` sites.** Find the second site:

```bash
python tools/relation_census.py check --root ./DC --manifest "$SCRATCH/dc.tsv"
grep -c preproc "$SCRATCH/dc.tsv"
```

  Use the `TableRelation` rows whose subtree contains `preproc_conditional_table_relation`.
  Pin both sites, verbatim, with exact parents and fields. The `#if` is under
  `if_table_relation`'s `else_relation`, never at the root.

- [ ] **Step 5: Run and commit**

```bash
./tools/ts-lock.sh tree-sitter test --file-name table_relation_keying_test.txt
./tools/ts-lock.sh tree-sitter test --file-name table_relation_keyword_containment_test.txt
python -m tools.alc_probe run tools/alc_probe/cases/table-relation-keying --check
git add test/corpus/table_relation_keying_test.txt test/corpus/table_relation_keyword_containment_test.txt \
  tools/tests/test_keyword_containment.py tools/alc_probe/cases/table-relation-keying
git commit -m "test(b5): scanner-state audit, keyword containment, host and DC fixtures

[BC.History: 0 errors, 100% success]"
```

---

### Task 6: the delta gate, mutations, incremental, oracle

**Files:**
- Create:
  - `tools/config_oracle/tests/test_table_relation_incremental.py`
  - `tools/tests/test_relation_query_captures.py`
- Modify: `tools/tests/test_relation_census.py`, adding the mutation tests.

**Interfaces:**
- Consumes:
  - Task 3's census and `$SCRATCH/al_base.dll`;
  - Task 4's grammar.

- [ ] **Step 1: The delta gate**

```bash
./tools/ts-lock.sh tree-sitter build -o "$SCRATCH/al_b5.dll"
python tools/relation_census.py delta --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0 \
  --base-lib "$SCRATCH/al_base.dll" --cur-lib "$SCRATCH/al_b5.dll" --manifest "$SCRATCH/b5-manifest.tsv"
cut -f6 "$SCRATCH/b5-manifest.tsv" | sort | uniq -c
```

Expected:
- exit 0;
- class totals of D1 36,118, D2 14,011, and D3 equal to the number of `simple_table_relation`
  nodes in the 25,714 `TableRelation` relation values;
- 0 `unclassified`, `ambiguous`, `unclassifiable` or `site-dropped` findings.

A D3 total that differs from the pre-change `simple_table_relation` count under
`TableRelation` is a STOP. Get that count from the Task 3 census of the base library.

- [ ] **Step 2: tree-harness agrees**

```bash
./tools/ts-lock.sh ./tools/tree-harness.sh verify ./BC.History .snapshots/baseline-b5 > "$SCRATCH/th.txt" 2>&1
grep "^=== CHANGED" "$SCRATCH/th.txt" | sed 's/^=== CHANGED: //' | sort > "$SCRATCH/th-files.txt"
grep "BC.History" "$SCRATCH/b5-manifest.tsv" | cut -f1 | sort -u > "$SCRATCH/mf-files.txt"
diff "$SCRATCH/th-files.txt" "$SCRATCH/mf-files.txt" && echo "file sets match"
```

Expected: `file sets match`, after normalising the path prefixes of the two files.

- [ ] **Step 3: Mutation proof (§5.5).** Add one pytest per mutation to
  `tools/tests/test_relation_census.py`. Each builds a mutated tree or source and asserts the
  expected finding kind. Each uses an in-memory fake, so no scratch build is needed:
  - **dropped property:** the current inventory with one site removed → `site-dropped`;
  - **reordered segments:** swap two segment entries in the new target → `unclassified`;
  - **`table` field instead of `target`:** run `check` on a pre-B5 tree parsed with
    `al_base.dll` → the `target` finding;
  - **non-leaf segment:** a fake `qualified_name` whose child has a child → `target`;
  - **conditional moved to the root:** a fake `table_relation_value` that starts with
    `preproc_conditional_table_relation` → `relation-shape`.

  The two family mutations need real scratch builds. Run each once, by hand, and record the
  result in the commit message:
  - comment out the emission line for `TABLE_RELATION_PROPERTY_NAME` in a scratch worktree,
    build, and run `check`: expect `relation-shape`;
  - restore `$.table_relation_value` in `_property_value` in a scratch worktree, build, and run
    `check`: expect `relation-outside`.

Run: `python -m pytest tools/tests/test_relation_census.py -q` (PASS).

- [ ] **Step 4: Incremental test**, `tools/config_oracle/tests/test_table_relation_incremental.py`.
  Copy `_edit` and the test function verbatim from `test_pair_list_incremental.py`, and use:

```python
HOST = b"table 50100 T\n{\n    fields { field(1; F; Code[20])\n    {\n        %s\n    }\n    }\n}\n"

EDITS = [
    (b"TableRelation = Customer;", b"TableRelationX = Customer;"),
    (b"TableRelationX = Customer;", b"TableRelation = Customer;"),
    (b"TableRelation = Rec.A;", b"Visible = Rec.A;"),
    (b"Visible = Rec.A;", b"TableRelation = Rec.A;"),
    (b"TableRelation = Customer;", b"tablerelation = Customer;"),
    (b"TableRelation = Customer;", b'TableRelation = Customer where("No." = const(\'A\'));'),
    (b"TableRelation = Customer;", b"TableRelation = System.Customer;"),
    (b"TableRelation = Customer;", b'TableRelation = Customer."No.";'),
    (b"TableRelation = Customer;", b"TableRelation =\n#if X\n Customer\n#else\n Vendor\n#endif\n;"),
    (b"TableRelation = Customer;", b"TableRelation  = Customer;"),
]
```

Run: `./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_table_relation_incremental.py -q`
Expected: PASS.

Prove it can fail: disable `tree.edit` the way B4 Task 4 Step 3 did, see FAIL, restore, and
re-run.

- [ ] **Step 5: Query capture test (§4.3).** Create
  `tools/tests/test_relation_query_captures.py`. It runs every `queries/*.scm` file over a
  D1, a D2 and a D3 site, and pins the capture names on each site's nodes, so that any future
  capture is written against the new shapes. It uses the API of
  `tools/query_coverage/inventory.py:45-46`:

```python
from pathlib import Path
import tree_sitter
from tools import relation_census as rc

SRC = (b'table 50101 Customer { fields { field(1; "No."; Code[20]) { } } }\n'
       b"table 50100 T\n{\n    fields {\n"
       b"        field(1; A; Code[20]) { TableRelation = Customer; }\n"                         # D1
       b'        field(2; B; Decimal) { AutoFormatExpression = Rec."Currency Code"; }\n'        # D2
       b'        field(3; C; Code[20]) { TableRelation = Customer."No." where("No." = const(\'A\')); }\n'  # D3
       b"    }\n}\n")


def _captures():
    parser = rc.parser_for(None)
    tree = parser.parse(SRC)
    out = set()
    for scm in sorted(Path("queries").glob("*.scm")):
        q = tree_sitter.Query(parser.language, scm.read_text(encoding="utf-8"))
        for name, nodes in tree_sitter.QueryCursor(q).captures(tree.root_node).items():
            out |= {(scm.name, name, n.start_byte, n.end_byte) for n in nodes}
    return out


def _span(text: bytes, after: bytes):
    i = SRC.index(after) + len(after)
    j = SRC.index(text, i)
    return j, j + len(text)


def _on(caps, span):
    return sorted((f, n) for f, n, s, e in caps if (s, e) == span)


def test_relation_segments_are_never_keyword_captures():
    caps = _captures()
    for text, after in [(b"Customer", b"TableRelation = "), (b'"No."', b"Customer.")]:
        assert not any("keyword" in n or n.startswith("type") for _, n in _on(caps, _span(text, after)))


PINNED = {
    # Filled in from the first run, after checking each entry against queries/highlights.scm.
    # The keys are (text, after); the values are the sorted (file, capture) lists.
}


def test_pinned_captures():
    caps = _captures()
    for (text, after), want in PINNED.items():
        assert _on(caps, _span(text, after)) == want
```

  Run the file once. Print `_on(...)` for these sites:
  - D1 `Customer`;
  - D2 `Rec` and `"Currency Code"`;
  - D3 `Customer` and `"No."`.

  Check every capture against `queries/highlights.scm`. A segment captured as a keyword or a
  type is a STOP. Then write the reviewed lists into `PINNED` as literals.

  **`PINNED` must not be committed empty.** Its emptiness is what the review step fills in.

Run: `python -m pytest tools/tests/test_relation_query_captures.py -q` (PASS).

- [ ] **Step 6: Oracle full tier and sweeps.** Run in the background, waiting with an `until`
  loop on the output file, never `tail -f`:

```bash
./tools/ts-lock.sh python -m tools.config_oracle run --tier full --root ./BC.History --root ./DC --root H:/Git/BC28.1 --root H:/Git/BCApps-29.0
for r in ./BC.History ./DC H:/Git/BC28.1 H:/Git/BCApps-29.0; do python tools/has_error_sweep.py --root "$r"; done
```

Expected:
- the oracle exits 0, with 0 discrepancies. Remove any `production-classes.tsv` entry it
  reports stale; a new unclassified record is a STOP;
- the sweeps show no new error file. BCApps keeps its 2 known files.

- [ ] **Step 7: Commit**

```bash
git add tools/tests/test_relation_census.py tools/config_oracle/tests/test_table_relation_incremental.py \
  tools/tests/test_relation_query_captures.py
# plus tools/config_oracle/production-classes.tsv if changed
git commit -m "test(b5): delta gate, census mutations, incremental parse

delta: D1 <n>, D2 <n>, D3 <n>, 0 findings. Scratch mutations: <results>.

[BC.History: 0 errors, 100% success]"
```

---

### Task 7: budget, WASM, docs, roadmap, cleanup

**Files:**
- Modify:
  - `CHANGELOG.md`
  - `CLAUDE.md`
  - `.claude/rules/scanner.md`
  - `docs/deferred-work.md`
  - `docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md`
  - `tree-sitter-al.wasm` and `tree-sitter-al.wasm.inputs.sha256`
  - `tools/query_coverage/baseline.json`, only if `qc` reports a new skipped hidden-rule field
    for the new hidden rules (B4 precedent)

- [ ] **Step 1: Size and performance**

```bash
./tools/metrics.sh --vs 6b15b9b
python -m tools.perf ab --lib-a "$SCRATCH/al_base.dll" --lib-b "$SCRATCH/al_b5.dll" --corpus dc --rounds 24
```

Expected:
- STATE_COUNT ≤ 17,231;
- the `ab` confidence interval contains 1.0, or the slowdown is within its stated resolution.

Over budget is a STOP. Report the numbers and `tree-sitter generate --report-states-for-rule -`.

- [ ] **Step 2: Full gates**

```bash
./tools/ts-lock.sh ./validate-grammar.sh --full
python tools/snip.py --census --root ./BC.History
python -m tools.query_coverage.qc run
python tools/traversal_census.py
./tools/ts-lock.sh python -m pytest tests/traversal -q && npm test
```

Expected: all exit 0, apart from the stale WASM, which Step 3 fixes. `qc` behaves like this:
- **New `fields|skipped|hidden-rule` entries** come from the new hidden rules, and nothing else
  changed: run `qc accept` and name them in the docs commit.
- **Any other regression** is a STOP.

The traversal census decides whether `qualified_name` needs a `traversal/policy.json` entry.
If it adds one, also run `cargo test --features traversal`.

- [ ] **Step 3: WASM**, as its own commit.

```bash
./tools/ts-lock.sh tree-sitter build --wasm -o tree-sitter-al.wasm
./tools/check-wasm-fresh.sh --update
./tools/check-wasm-fresh.sh
git add tree-sitter-al.wasm tree-sitter-al.wasm.inputs.sha256
git commit -m "build: rebuild tree-sitter-al.wasm for B5

[BC.History: 0 errors, 100% success]"
```

- [ ] **Step 4: Docs**, per spec §6:
  - **CHANGELOG `[Unreleased]` / `### Changed`:** one breaking entry covering D1, D2, D3 and
    G10, the cost (STATE_COUNT and `ab`), and the four-point migration note from §4.3.
  - **CLAUDE.md "Name-keyed properties":**
    - "three families" becomes four;
    - a `TableRelation` bullet citing `ParseTableRelationPropertyValue` and `ParseQualifiedName`;
    - a `TABLE_RELATION_PROPERTY_NAME` row in the token table;
    - the emission order: CalcFormula → ML → Namespaces → TableRelation → generic → decline.
  - **`.claude/rules/scanner.md`:**
    - the token row;
    - "Nine tokens" becomes "Ten tokens" in the dispatch section;
    - the emission order;
    - the three guards that list every keyed token.
  - **`docs/deferred-work.md`:** mark items 13 and 15 RESOLVED, with the Task 4 commit hash.
    Item 15's correction is that the root question was answered by the compiler's per-host
    dispatch.
  - **Roadmap:**
    - the B5 row gets a done note: STATE_COUNT, `ab`, and the delta totals D1/D2/D3;
    - decision 2 is recorded as superseded, with a pointer to spec §2.1;
    - a new row, **B5b: link-syntax leak**: `Visible = Flag = Rec.OtherFlag;` is a clean
      `link_value_list`. Key the compiler's TableFilter family (`SubPageLink`, `RunPageLink`,
      `LinkFields`, `DataItemTableFilter`, `ColumnFilter`) and `DataItemLink` by name, with
      the B5 method.

- [ ] **Step 5: Commit the docs**

```bash
git add CHANGELOG.md CLAUDE.md .claude/rules/scanner.md docs/deferred-work.md \
  docs/superpowers/plans/2026-09-28-roadmap-remaining-work.md
# plus tools/query_coverage/baseline.json if accepted in Step 2
git commit -m "docs: B5 done -- TableRelation keyed, qualified_name target, G10, B5b row

[BC.History: 0 errors, 100% success]"
```

- [ ] **Step 6: Cleanup.**
  - Delete `.snapshots/baseline-b5` with `P=.snapshots/baseline-b5; rm -rf "${P:?}"`.
  - Remove any scratch worktree left behind, with `git worktree list` and then
    `git worktree remove`.
  - List leftover processes with `./tools/session-cleanup.sh --procs`, and kill only the ones
    you started.
