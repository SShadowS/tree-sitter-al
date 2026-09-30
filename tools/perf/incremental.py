"""Fresh-parse against incremental-parse equivalence on sample edits, and their speed ratio.

For every edit: `old.edit(...)` with byte offsets AND points, `inc = parse(new, old)`,
`fresh = parse(new)`, and the two complete cursor-derived trees must be identical: every
node the cursor visits (named and anonymous), its type, named/missing/extra flags, field
name, byte span, point span and has_error. Any difference is a correctness defect (exit 1).

Each file gets every applicable edit kind once, each from the ORIGINAL tree
("independent"), then all of them again applied one after another, each incremental parse
reusing the previous incremental tree ("chain") -- the editor's usage pattern, where reused
subtrees carry scanner state from earlier edits.
"""
from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from pathlib import Path

from tools.perf import common, stats

SEED = 20260930
SAMPLE = 300
BOM = b"\xef\xbb\xbf"
# Per-corpus quotas: files with a split construct, other files with `#if`, BOM files,
# files with a `/*` (block comments are rare in AL: a uniform sample of 300 held one),
# then uniform random to fill the corpus's share.
QUOTAS = (("split", 20), ("if", 20), ("bom", 10), ("block_comment", 5))
DIRECTIVE = re.compile(rb"(?im)^[ \t]*#[ \t]*(if|elif|else|endif)\b[^\r\n]*")
IF_LINE = re.compile(rb"(?im)^[ \t]*#[ \t]*if\b[^\r\n]*")
ENDIF = re.compile(rb"(?i)#[ \t]*endif\b")
ELSE_LINE = re.compile(rb"(?im)^[ \t]*#[ \t]*else\b[^\r\n]*(\r?\n|$)")
KINDS = ("ident_insert", "ident_delete", "semicolon_delete", "semicolon_insert",
         "if_eol_space", "if_eol_formfeed", "endif_newline", "beginend_delete",
         "beginend_insert", "line_comment_insert", "block_comment_insert",
         "string_insert", "else_line_delete")


@dataclass(frozen=True)
class Edit:
    kind: str
    start: int        # byte offset
    old_end: int      # byte offset in the old source
    new: bytes        # replacement for src[start:old_end]

    def apply(self, src: bytes) -> bytes:
        return src[:self.start] + self.new + src[self.old_end:]


def point_at(src: bytes, offset: int):
    """tree-sitter's (row, column) for a byte offset: rows advance on `\\n` only (a `\\r`
    is an ordinary column), and the column counts BYTES, not characters."""
    row = src.count(b"\n", 0, offset)
    return row, offset - (src.rfind(b"\n", 0, offset) + 1)


def edit_args(src: bytes, e: Edit) -> dict:
    """Keyword arguments for Tree.edit(), computed from the old source and the edit."""
    new_end = e.start + len(e.new)
    return dict(start_byte=e.start, old_end_byte=e.old_end, new_end_byte=new_end,
                start_point=point_at(src, e.start), old_end_point=point_at(src, e.old_end),
                new_end_point=point_at(e.apply(src), new_end))


def rows(tree):
    """The complete cursor-derived tree, pre-order: one tuple per node the cursor visits."""
    c, out, depth = tree.walk(), [], 0
    while True:
        n = c.node
        out.append((depth, n.type, n.is_named, n.is_missing, n.is_extra, c.field_name,
                    n.start_byte, n.end_byte, tuple(n.start_point), tuple(n.end_point), n.has_error))
        if c.goto_first_child():
            depth += 1
            continue
        while not c.goto_next_sibling():
            if not c.goto_parent():
                return out
            depth -= 1


ROW_FIELDS = ("depth", "type", "named", "missing", "extra", "field", "start_byte", "end_byte",
              "start_point", "end_point", "has_error")


def diff(a, b):
    """None when identical, else {index, incremental, fresh} of the first differing row
    (a row missing on one side is None)."""
    for i in range(max(len(a), len(b))):
        x = a[i] if i < len(a) else None
        y = b[i] if i < len(b) else None
        if x != y:
            return {"index": i, "incremental": x and dict(zip(ROW_FIELDS, x)),
                    "fresh": y and dict(zip(ROW_FIELDS, y))}
    return None


# ---- edit sites -----------------------------------------------------------------------

def _boundary(src, off, lo, hi):
    """The first UTF-8 character boundary at or after `off` within [lo, hi], or None."""
    while off <= hi and off < len(src) and 0x80 <= src[off] < 0xC0:
        off += 1
    return off if lo <= off <= hi else None


def _nodes(tree):
    kinds = {"identifier": [], "comment": [], "multiline_comment": [], "string_literal": [],
             ";": [], "begin_keyword": [], "end_keyword": []}
    c = tree.walk()
    while True:
        n = c.node
        if n.type in kinds:
            kinds[n.type].append((n.start_byte, n.end_byte))
        if c.goto_first_child():
            continue
        while not c.goto_next_sibling():
            if not c.goto_parent():
                return kinds


def sites(src: bytes, tree, rng: random.Random):
    """One Edit per applicable kind, at a site chosen by `rng`. Deterministic given rng."""
    nodes, out = _nodes(tree), []
    pick = lambda xs: xs[rng.randrange(len(xs))] if xs else None  # noqa: E731

    def insert_inside(kind, spans, lead, trail, text=b"x"):
        spans = [(s, e) for s, e in spans if e - s >= lead + trail]
        span = pick(spans)
        if span:
            s, e = span
            off = _boundary(src, rng.randint(s + lead, e - trail), s + lead, e - trail)
            if off is not None:
                out.append(Edit(kind, off, off, text))

    ids = nodes["identifier"]
    span = pick(ids)
    if span:
        off = _boundary(src, (span[0] + span[1]) // 2, span[0], span[1])
        if off is not None:
            out.append(Edit("ident_insert", off, off, b"x"))
    span = pick([(s, e) for s, e in ids if e - s >= 2 and src[s] != 0x22])   # unquoted, >= 2 bytes
    if span:
        i = pick([i for i in range(*span) if src[i] < 0x80])                 # never split a UTF-8 char
        if i is not None:
            out.append(Edit("ident_delete", i, i + 1, b""))
    semi = pick(nodes[";"])
    if semi:
        out.append(Edit("semicolon_delete", semi[0], semi[1], b""))
    semi = pick(nodes[";"])
    if semi:
        out.append(Edit("semicolon_insert", semi[1], semi[1], b";"))
    for kind, text in (("if_eol_space", b" "), ("if_eol_formfeed", b"\f")):
        m = pick(list(IF_LINE.finditer(src)))
        if m:
            out.append(Edit(kind, m.end(), m.end(), text))   # `[^\r\n]*` ends before any \r
    m = pick(list(ENDIF.finditer(src)))
    if m:
        line_end = src.find(b"\n", m.end())
        eol = b"\n" if line_end < 0 else (b"\r\n" if src[line_end - 1:line_end] == b"\r" else b"\n")
        out.append(Edit("endif_newline", m.end(), m.end(), eol))
    directive_lines = {point_at(src, m.start())[0] for m in DIRECTIVE.finditer(src)}
    near = [(s, e) for s, e in nodes["begin_keyword"] + nodes["end_keyword"]
            if directive_lines & {point_at(src, s)[0] + d for d in (-1, 0, 1)}]
    span = pick(sorted(near))
    if span:
        out.append(Edit("beginend_delete", span[0], span[1], b""))
    m = pick(list(DIRECTIVE.finditer(src)))
    if m:
        nl = src.find(b"\n", m.end())
        at = len(src) if nl < 0 else nl + 1
        out.append(Edit("beginend_insert", at, at, pick([b"begin ", b"end; "])))
    insert_inside("line_comment_insert", nodes["comment"], 2, 0)
    insert_inside("block_comment_insert", nodes["multiline_comment"], 2, 2)
    insert_inside("string_insert", nodes["string_literal"], 1, 1)
    m = pick(list(ELSE_LINE.finditer(src)))
    if m:
        out.append(Edit("else_line_delete", m.start(), m.end(), b""))
    return out


# ---- the sample -----------------------------------------------------------------------

def _has_split(tree):
    c = tree.walk()
    while True:
        t = c.node.type
        if t.startswith("preproc_split") or t.startswith("preproc_fragmented"):
            return True
        if c.goto_first_child():
            continue
        while not c.goto_next_sibling():
            if not c.goto_parent():
                return False


def sample(files, labels, parser, seed=SEED, size=SAMPLE):
    """-> [(index into files, category)]: per corpus an equal share of `size`, filled by
    QUOTAS first. Candidates are shuffled with Random(f"{seed}:{label}:{category}")."""
    share, chosen = size // len(labels), []
    for label in labels:
        idx = [i for i, f in enumerate(files) if f[0] == label]
        taken = set()

        def take(cat, cands, n, test=None):
            cands = [i for i in cands if i not in taken]
            random.Random(f"{seed}:{label}:{cat}").shuffle(cands)
            for i in cands:
                if n <= 0:
                    return
                if test is None or test(i):
                    taken.add(i)
                    chosen.append((i, cat))
                    n -= 1

        with_if = [i for i in idx if IF_LINE.search(files[i][2])]
        take("split", with_if, dict(QUOTAS)["split"], lambda i: _has_split(parser.parse(files[i][2])))
        take("if", with_if, dict(QUOTAS)["if"])
        take("bom", [i for i in idx if files[i][2].startswith(BOM)], dict(QUOTAS)["bom"])
        take("block_comment", [i for i in idx if b"/*" in files[i][2]], dict(QUOTAS)["block_comment"])
        take("random", idx, share - len(taken))
    return chosen


# ---- the run --------------------------------------------------------------------------

def check(parser, fid, src, e, old_tree, mismatches, timings, mode):
    new = e.apply(src)
    old_tree.edit(**edit_args(src, e))
    t0 = time.perf_counter_ns()
    inc = parser.parse(new, old_tree)
    t1 = time.perf_counter_ns()
    fresh = parser.parse(new)
    t2 = time.perf_counter_ns()
    timings.append((t1 - t0, t2 - t1))
    d = diff(rows(inc), rows(fresh))
    if d:
        mismatches.append({"file": fid, "mode": mode, "kind": e.kind, "start": e.start,
                           "old_end": e.old_end, "new": e.new.decode("utf-8", "replace"),
                           "first_difference": d})
    return new, inc


def measure(labels, seed=SEED, size=SAMPLE, report_dir=None):
    files, _ = common.load(labels)
    parser = common.parser()
    chosen = sample(files, labels, parser, seed, size)
    mismatches, timings, per_kind = [], [], {k: 0 for k in KINDS}
    for n, (i, cat) in enumerate(chosen):
        label, rel, src = files[i]
        fid = f"{label}:{rel}"
        if n % 50 == 0:
            common.log(f"incremental: file {n + 1}/{len(chosen)}")
        tree = parser.parse(src)
        rng = random.Random(f"{seed}:{fid}")
        edits = sites(src, tree, rng)
        for e in edits:
            per_kind[e.kind] += 1
            check(parser, fid, src, e, tree.copy(), mismatches, timings, "independent")
        cur_src, cur_tree = src, tree                          # chain: reuse the incremental tree
        for kind in [e.kind for e in edits]:
            e = next((x for x in sites(cur_src, cur_tree, rng) if x.kind == kind), None)
            if e is not None:
                cur_src, cur_tree = check(parser, fid, cur_src, e, cur_tree, mismatches, timings, "chain")
    ratio = [inc / fresh for inc, fresh in timings if fresh]
    cats = {}
    for i, cat in chosen:
        cats[cat] = cats.get(cat, 0) + 1
    result = {
        "seed": seed, "sample_size": len(chosen), "categories": cats,
        "bom_files": sum(files[i][2].startswith(BOM) for i, _ in chosen),
        "crlf_files": sum(b"\r\n" in files[i][2] for i, _ in chosen),
        "files_with_if": sum(bool(IF_LINE.search(files[i][2])) for i, _ in chosen),
        "edits_per_kind_independent": per_kind, "edits_checked": len(timings),
        "mismatches": len(mismatches), "mismatch_details": mismatches[:50],
        "incremental_ms": stats.latency([a / 1e6 for a, _ in timings]),
        "fresh_ms": stats.latency([b / 1e6 for _, b in timings]),
        "speed_ratio_incremental_over_fresh": {"median": stats.median(ratio), "p95": stats.percentile(ratio, 95)},
        "sample": [{"file": f"{files[i][0]}:{files[i][1]}", "category": cat} for i, cat in chosen],
    }
    if mismatches and report_dir:
        d = Path(report_dir) / "incremental-mismatches"
        d.mkdir(parents=True, exist_ok=True)
        import json
        (d / "mismatches.json").write_text(json.dumps(mismatches, indent=1), encoding="utf-8")
    return result
