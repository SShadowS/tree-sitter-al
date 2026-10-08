"""Structural delta classifier for B7b-3 (spec docs/superpowers/specs/
2026-10-08-b7b-3-statement-terminators-design.md, section 7).

    python -m tools.perf delta --lib-a MAIN.dll --lib-b BRANCH.dll [--corpus all|LABEL ...] [--out OUT.json]

Every file is parsed by both libraries; where the complete cursor rows
(`incremental.rows`) differ, the old tree is rewritten by the section 7.2 edits, each
checked structurally, and must then equal the new tree row for row:

- E1 call-terminator-out: a `call_statement` loses its last child `;`, which becomes a
  child of the nearest approved owner (a statement container, or the enclosing case branch
  as its own `;`), right after the outermost ancestor that ended at that `;`. Those
  ancestors' ends are recomputed from their retained children.
- E2 split-call-terminator-out: the same for `preproc_split_call_statement`, ending at `)`.
- Extras between the callee (or `)`) and the `;` stay in their parent, or move to the
  `;`'s new parent immediately before it. Nothing else.
- E3 bare-name-wrap: an eligible name in an eligible slot gains a `call_statement` parent
  with its span and its field; its own edge becomes `function`.

Edits are tried greedily: E1/E2 innermost first (post-order), then E3 in source order. A
refused attempt is reported, and whatever rows still differ afterwards are listed as the
unexplained remainder (never dropped). Any change in a file whose old or new tree has an
error is unexplained outright, unless the file is in the reviewed list
`tools/perf/delta-reviewed.tsv` (corpus, path, sha256 of the source bytes, reason) with a
matching sha256 AND an error in its old or new tree (B7b-3 Task 4 ruling: spec 7.2 says such
files are reviewed individually). Exit 0 every change explained or reviewed, 1 otherwise,
2 cannot run.
Run under ./tools/ts-lock.sh.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import NamedTuple

from tools.perf import common, parity

# ---- frozen tables (spec section 7.2) ------------------------------------------------

CALLS = {"call_statement": "E1", "preproc_split_call_statement": "E2"}
# Statement positions: every (visible host, field) the grammar routes into one of these
# rules through hidden rules and `inline`s (`statement_positions()` walks src/grammar.json;
# tests/test_delta.py pins the tables below against it, so a grammar change that adds or
# drops a route fails there instead of passing or failing silently here).
STATEMENT_RULES = ("_statement", "_statement_inner", "_expression_statement")
# Hosts of `_statement`: the `;` of E1/E2 goes to the NEAREST ancestor of one of these types,
# or of a case branch type (spec 7.2: the enclosing case branch owns its `;`).
STATEMENT_HOSTS = frozenset({
    "statement_block", "preproc_conditional_statement", "preproc_fragmented_else_tail",
    "preproc_split_block_close_after_endif", "preproc_split_block_end_in_else",
    "preproc_split_code_block_end", "preproc_split_code_block_over_endif",
    "preproc_split_else_begin_over_endif", "preproc_split_if_begin_asymmetric",
    "preproc_split_if_begin_else", "preproc_split_if_then_begin",
    "preproc_split_if_then_begin_else_shared", "preproc_split_open_statement"})
CASE_OWNERS = frozenset({"case_branch", "preproc_split_case_branch", "preproc_split_case_end_branch",
                         "preproc_split_case_extended"})
OWNERS = STATEMENT_HOSTS | CASE_OWNERS
# E3 eligible (parent type, slot): every statement position; None is the unfielded child.
# Spec 7.2 also lists repeat_statement.body and case_else_branch.body: both hold a
# statement_block, never a statement, so they are not positions (the walk shows it).
E3_SLOTS = frozenset({
    *((h, None) for h in STATEMENT_HOSTS),
    ("if_statement", "then_branch"), ("if_statement", "else_branch"),
    ("preproc_split_if_statement", "then_branch"), ("preproc_split_if_statement", "else_branch"),
    ("preproc_split_if_else_statement", "then_branch"), ("preproc_split_if_else_statement", "else_branch"),
    ("preproc_split_open_statement", "then_branch"), ("preproc_split_open_statement", "continuation"),
    *((p, "body") for p in ("while_statement", "for_statement", "foreach_statement", "with_statement",
                            "asserterror_statement", *CASE_OWNERS)),
    ("preproc_guarded_statement", None), ("preproc_guarded_statement", "then_branch"),
})
# Positions the walk reports that are shown NOT to be statement slots, each with a reason.
NEVER_ELIGIBLE = {}


def statement_positions(grammar=None):
    """-> {(visible host, field or None, statement rule)} from src/grammar.json: every place
    the grammar routes into STATEMENT_RULES, through hidden (`_`) and `inline` rules (fields
    carried through them) and named aliases (which make their own host)."""
    g = grammar or json.loads((common.REPO / "src" / "grammar.json").read_text(encoding="utf-8"))
    rules, inline = g["rules"], set(g.get("inline", []))
    out, seen = set(), set()

    def go(x, host, field):
        t = x["type"]
        if t == "FIELD":
            go(x["content"], host, x["name"])
        elif t == "ALIAS":
            c = x["content"]
            if c["type"] != "SYMBOL":
                go(c, host, field)
            elif x["named"] and c["name"] in rules and c["name"] not in STATEMENT_RULES:
                visit(x["value"], c["name"])
        elif t == "SYMBOL":
            n = x["name"]
            if n in STATEMENT_RULES:
                out.add((host, field, n))
            elif n in rules and (n.startswith("_") or n in inline) and (host, field, n) not in seen:
                seen.add((host, field, n))
                go(rules[n], host, field)
        elif "members" in x:
            for m in x["members"]:
                go(m, host, field)
        elif "content" in x:
            go(x["content"], host, field)

    def visit(host, rule):
        if (host, rule) not in seen:
            seen.add((host, rule))
            go(rules[rule], host, None)
    for name in rules:
        if not name.startswith("_") and name not in inline:
            visit(name, name)
    return out


E3_NAMES = frozenset({"identifier", "quoted_identifier"})
# Keyword table, section 7.2: grammar.js `code_names` (and or xor div mod in not), the
# statement keywords, and true/false. `is`/`as` are names (B6), so they are absent.
KEYWORDS = frozenset(
    "and or xor div mod in not "
    "if then else begin end case of repeat until while do for to downto foreach with exit asserterror "
    "true false".split())
# Admitted by explicit whitelist, through the `_value_start_keyword_name` route.
VALUE_START_NAMES = frozenset({"order", "table"})
REMAINDER_CAP = 40


class Edit(NamedTuple):
    kind: str          # "E1" | "E2" | "E3"
    start_byte: int
    note: str


class Explanation(NamedTuple):
    edits: list
    unexplained: list


# ---- a mutable tree over rows --------------------------------------------------------

class Node:
    __slots__ = ("type", "grammar", "named", "missing", "extra", "field", "start", "end", "spoint",
                 "epoint", "err", "kids", "parent")

    def __init__(self, r, parent):
        (_, self.type, self.grammar, self.named, self.missing, self.extra, self.field, self.start,
         self.end, self.spoint, self.epoint, self.err) = r
        self.kids, self.parent = [], parent

    def key(self):
        return (self.type, self.grammar, self.start, self.end)

    def same(self, o):
        """Paired by (start, type, symbol): the end may have moved."""
        return o is not None and (self.type, self.grammar, self.start) == (o.type, o.grammar, o.start)


def build(rows):
    stack, root = [], None
    for r in rows:
        del stack[r[0]:]
        x = Node(r, stack[-1] if stack else None)
        if x.parent:
            x.parent.kids.append(x)
        else:
            root = x
        stack.append(x)
    return root


def walk(x):
    yield x
    for k in x.kids:
        yield from walk(k)


def postorder(x):
    for k in x.kids:
        yield from postorder(k)
    yield x


def to_rows(root):
    out = []

    def go(x, d):
        out.append((d, x.type, x.grammar, x.named, x.missing, x.extra, x.field, x.start, x.end,
                    x.spoint, x.epoint, x.err))
        for k in x.kids:
            go(k, d + 1)
    go(root, 0)
    return out


def index(root):
    ix = {}
    for x in walk(root):
        ix.setdefault(x.key(), []).append(x)
    return ix


# ---- the edits -----------------------------------------------------------------------

def _e1(c, new_ix):
    """Try E1/E2 on old node `c`. -> (Edit | None, refusal note | None)."""
    real = [k for k in c.kids if not k.extra]
    if not real or real[-1].type != ";" or real[-1].named:
        return None, None
    semi = real[-1]
    target = next(iter(new_ix.get(semi.key(), [])), None)
    if target is None or c.same(target.parent):
        return None, None                              # gone (remainder) or not moved
    kind, np_ = CALLS[c.type], target.parent
    owner, chain = c.parent, [c]
    while owner is not None and owner.type not in OWNERS:
        chain.append(owner)
        owner = owner.parent
    where = f"{kind} refused at {c.start}: `;` moved to {np_.type}@{np_.start}"
    if owner is None or not owner.same(np_):
        return None, f"{where}, nearest approved owner is {owner.type + '@' + str(owner.start) if owner else 'none'}"
    if any(x.end != semi.end for x in chain):
        return None, f"{where}, an ancestor below it does not end at the `;`"
    rest = real[:-1]
    if kind == "E1" and not (len(rest) == 1 and rest[0].field == "function"):
        return None, f"{where}, call children are not exactly `function`"
    if kind == "E2" and (not rest or rest[-1].type != ")"):
        return None, f"{where}, split call does not end at `)`"
    # Extras between the last retained child and the `;`: stay, or move before the `;`.
    # "Stay" is permitted by the spec but tree-sitter never produces it: a node's trailing
    # extras are pushed to its parent (ts_subtree_array_remove_trailing_extras).
    tail = c.kids[c.kids.index(rest[-1]) + 1:]
    moving = [e for e in tail if e.extra and any(owner.same(t.parent) for t in new_ix.get(e.key(), []))]
    for x in (semi, *moving):
        c.kids.remove(x)
    for x in chain:                                    # innermost first
        last = x.kids[-1]
        x.end, x.epoint = last.end, last.epoint
    at = owner.kids.index(chain[-1]) + 1
    owner.kids[at:at] = [*moving, semi]
    for x in (*moving, semi):
        x.parent = owner
    return Edit(kind, c.start, f"{c.type} `;` -> {owner.type}@{owner.start}"
                + (f" (+{len(moving)} extra)" if moving else "")), None


def _e3(nc, old_ix, src):
    """Try E3 for new call_statement `nc`. -> (Edit | None, refusal note | None)."""
    if len(nc.kids) != 1:
        return None, None
    f = nc.kids[0]
    if not (f.field == "function" and f.type in E3_NAMES and (f.start, f.end) == (nc.start, nc.end)):
        return None, None
    o = next(iter(old_ix.get(f.key(), [])), None)
    if o is None or o.parent is None or (o.parent.type == "call_statement" and o.field == "function"):
        return None, None
    text = src[o.start:o.end].decode("utf-8", "replace")
    where = f"E3 refused at {o.start}: {text!r} in {o.parent.type}.{o.field}"
    if (o.parent.type, o.field) not in E3_SLOTS:
        return None, f"{where}: slot not eligible"
    if o.type == "identifier" and text.lower() in KEYWORDS and text.lower() not in VALUE_START_NAMES:
        return None, f"{where}: keyword text"
    w = Node((0, "call_statement", "call_statement", True, False, False, o.field, o.start, o.end,
              o.spoint, o.epoint, o.err), o.parent)
    p = o.parent
    p.kids[p.kids.index(o)] = w
    w.kids, o.parent, o.field = [o], w, "function"
    return Edit("E3", o.start, f"{text} in {p.type}.{w.field}"), None


def explain_rows(old_rows, new_rows, src: bytes) -> Explanation:
    if old_rows == new_rows:
        return Explanation([], [])
    if old_rows[0][11] or new_rows[0][11]:
        return Explanation([], [f"has_error (old {old_rows[0][11]}, new {new_rows[0][11]}): no change is admitted"])
    old, new = build(old_rows), build(new_rows)
    edits, notes = [], []
    new_ix = index(new)
    for c in list(postorder(old)):
        if c.type in CALLS:
            e, why = _e1(c, new_ix)
            edits += [e] if e else []
            notes += [why] if why else []
    old_ix = index(old)
    for nc in walk(new):
        if nc.type == "call_statement":
            e, why = _e3(nc, old_ix, src)
            edits += [e] if e else []
            notes += [why] if why else []
    got = to_rows(old)
    if got == new_rows:
        return Explanation(edits, [])
    a, b = Counter(got), Counter(new_rows)
    diff = [f"- {r}" for r in sorted((a - b).elements(), key=lambda r: (r[7], r[0]))] + \
           [f"+ {r}" for r in sorted((b - a).elements(), key=lambda r: (r[7], r[0]))]
    if len(diff) > REMAINDER_CAP:
        diff = diff[:REMAINDER_CAP] + [f"... {len(diff) - REMAINDER_CAP} more differing rows"]
    if not diff:                                       # same rows, different order
        diff = ["rows equal as a multiset but differ in order"]
    return Explanation(edits, notes + diff)


def explain(old_tree, new_tree, src: bytes) -> Explanation:
    from tools.perf import incremental
    return explain_rows(incremental.rows(old_tree), incremental.rows(new_tree), src)


# ---- corpus driver (parity's pool) ---------------------------------------------------

def _chunk(job):
    """-> [{file, edits, unexplained}] for the changed files of one chunk (worker process)."""
    from tools.perf import incremental
    a, b, label, root, rels = job
    pa, pb = parity._parsers(a, b)
    out = []
    for r in rels:
        try:
            raw = (Path(root) / r).read_bytes()
            src = common.source(raw)
        except Exception as e:  # noqa: BLE001
            raise parity.ParityError(f"cannot read {label}:{r}: {e!r}") from e
        ra, rb = incremental.rows(pa.parse(src)), incremental.rows(pb.parse(src))
        if ra != rb:
            ex = explain_rows(ra, rb, src)
            out.append({"file": f"{label}:{r}", "edits": [e._asdict() for e in ex.edits],
                        "unexplained": ex.unexplained, "sha256": hashlib.sha256(raw).hexdigest(),
                        "has_error": [bool(ra[0][11]), bool(rb[0][11])]})
    return out


def run(lib_a, lib_b, labels, workers=None, roots=None):
    """-> {label: (files, [changed-file reports])}; raises like parity.run."""
    return parity.run(lib_a, lib_b, labels, workers, roots, chunk_fn=_chunk, pool=True)


REVIEWED = Path(__file__).with_name("delta-reviewed.tsv")
REVIEWED_HEADER = "corpus	path	sha256	reason"


def load_reviewed(path=REVIEWED):
    """-> {"label:path": (sha256, reason)}; a missing file is an empty list."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {}
    body = [l for l in lines if l.strip() and not l.startswith("#")]
    if not body or body[0] != REVIEWED_HEADER:
        raise ValueError(f"{path}: missing or wrong header line")
    out = {}
    for l in body[1:]:
        cols = l.split("	")
        if len(cols) != 4 or not all(c.strip() for c in cols):
            raise ValueError(f"{path}: a row needs corpus, path, sha256 and reason: {l!r}")
        out[f"{cols[0]}:{cols[1]}"] = (cols[2].lower(), cols[3])
    return out


def reviewed_ok(c, reviewed):
    """None when the unexplained file `c` is a reviewed exception, else why not."""
    entry = reviewed.get(c["file"])
    if entry is None:
        return "not in delta-reviewed.tsv"
    if entry[0] != c.get("sha256"):
        return f"delta-reviewed.tsv sha256 {entry[0][:12]} != source {str(c.get('sha256'))[:12]}"
    if not any(c.get("has_error") or ()):
        return "delta-reviewed.tsv lists it, but neither tree has an error"
    return None


def report(out, path=None, file=None, reviewed=None):
    file = file or sys.stdout
    reviewed = load_reviewed() if reviewed is None else reviewed
    summary = {}
    for label, (n, changed) in out.items():
        kinds = Counter(e["kind"] for c in changed for e in c["edits"])
        bad, ok = [], []
        for c in changed:
            if c["unexplained"]:
                why = reviewed_ok(c, reviewed)
                (ok if why is None else bad).append(c)
                c["review"] = why or "reviewed: " + reviewed[c["file"]][1]
        summary[label] = {"files": n, "changed": len(changed), "unexplained": len(bad), "reviewed": len(ok),
                          "edits": dict(kinds)}
        print(f"delta: {label}: {n} files, {len(changed)} changed, {len(bad)} unexplained, {len(ok)} reviewed, "
              "edits " + (", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) or "0"), file=file)
        for c in ok:
            print(f"  reviewed {c['file']}", file=file)
        for c in bad:
            print(f"  {c['file']}  ({c['review']})", file=file)
            for u in c["unexplained"][:5]:
                print(f"    {u}", file=file)
    if path:
        Path(path).write_text(json.dumps({"summary": summary, "files": {l: c for l, (_, c) in out.items()}},
                                         indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"delta: wrote {path}", file=file)
    return 1 if any(s["unexplained"] for s in summary.values()) else 0


def main(lib_a, lib_b, corpus, workers=None, out=None):
    labels = common.LABELS if not corpus or "all" in corpus else tuple(corpus)
    try:
        return report(run(lib_a, lib_b, labels, workers), out)
    except (FileNotFoundError, parity.ParityError) as e:
        print(f"delta: cannot run: {e}", file=sys.stderr)
        return 2
