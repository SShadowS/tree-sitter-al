"""Seed inventory (spec 5): verbatim reproducers that must be in the matrix, and the production
shape walk.

A seed file is `tools/b7_audit/seeds/<name>.al`. Its leading `//` lines carry
  `// host: <rule>`      the construct the seed exercises (the Cell's host)
  `// valid: <patterns>` intended-valid configurations: `;`-separated assignments, each a `,`-separated
                         list of `SYM` / `!SYM` (unmentioned symbols are free), or `*` (all) or `none`
  `// source: ...`       where the shape came from (one or more)
Other header lines (the original alc `// expect:` verdicts, prose) are kept verbatim and ignored here.
A seed Cell covers the whole file: hole=(0, len), plain=None, check=().
"""
import re
from pathlib import Path

from tools.b7_audit.placements import Cell, assignments
from tools.config_oracle.directives import discover

SEEDS = Path(__file__).parent / "seeds"
LINK_NAMES = ("SubPageLink", "RunPageLink", "LinkFields", "DataItemTableFilter", "ColumnFilter", "DataItemLink")


def expand_valid(spec, symbols):
    """The full assignments (frozensets of defined symbols) a `// valid:` line selects."""
    spec = spec.strip()
    if spec == "none":
        return set()
    if spec == "*":
        return set(assignments(symbols))
    out = set()
    for pat in spec.split(";"):
        lits = []
        for tok in pat.split(","):
            tok = tok.strip()
            name = tok.lstrip("!")
            if name not in symbols:
                raise ValueError(f"valid pattern {pat!r} names {name!r}, not one of {list(symbols)}")
            lits.append((name, not tok.startswith("!")))
        out |= {a for a in assignments(symbols) if all((n in a) == want for n, want in lits)}
    return out


def _header(text):
    h = {}
    for line in text.splitlines():
        if not line.startswith("//"):
            break
        m = re.match(r"//\s*(host|valid)\s*:\s*(.*?)\s*$", line)
        if m:
            h[m.group(1)] = m.group(2)
    return h


def load(root=SEEDS):
    cells = []
    for p in sorted(Path(root).glob("*.al")):
        text = p.read_text(encoding="utf-8")
        h = _header(text)
        if "host" not in h or "valid" not in h:
            raise ValueError(f"{p.name}: `// host:` and `// valid:` are required")
        symbols = tuple(discover(text.encode("utf-8")).free_symbols)
        cells.append(Cell(id=f"seed:{p.stem}", key=f"seed:{p.stem}", host=h["host"], placement=f"seed:{p.stem}",
                          source=text, symbols=symbols,
                          intended_valid=frozenset(expand_valid(h["valid"], symbols)),
                          hole=(0, len(text.encode("utf-8"))), plain=None, check=()))
    return cells


def link_coverage(root=SEEDS):
    """{link property name: [seed keys whose code assigns it]} (comment lines ignored)."""
    out = {n: [] for n in LINK_NAMES}
    for c in load(root):
        code = "\n".join(l for l in c.source.splitlines() if not l.lstrip().startswith("//"))
        for n in LINK_NAMES:
            if re.search(rf"\b{n}\s*=", code, re.I):
                out[n].append(c.key)
    return out


# --- production walk ------------------------------------------------------------------------------
_HEADS = {"preproc_split_begin", "preproc_split_end"}          # scanner tokens, not groups
_GROUP = ("preproc_conditional", "preproc_split_", "preproc_operand_prefix", "preproc_fragmented",
          "preproc_guarded")
_DIRECTIVE_HEADS = {"preproc_if", "preproc_elif", "preproc_else", "preproc_endif"}
SEPARATORS = {",", ";", "..", "::", ":"}
OP_WORDS = ("and", "or", "xor")
_LEAD_OP = re.compile(r"(?:\+|-|\*|/|<=|>=|<>|<|>|=)|(?:and|or|xor)\b", re.I)
_TRAIL_OP = re.compile(r"(?:\+|-|\*|/|<|>|=)$|\b(?:and|or|xor)$", re.I)
_EDGE_TYPES = {"+", "-", "*", "/", "<", ">", "<=", ">=", "<>", "and", "or", "xor"}   # no "=": a property's `=` is not an edge


def _is_group(t):
    return t not in _HEADS and t.startswith(_GROUP)


def _content(text):
    """The node's text without directive lines and comments, stripped."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    lines = [re.sub(r"//.*$", "", l) for l in text.splitlines() if not l.lstrip().startswith("#")]
    return " ".join(lines).strip()


def _near(node, attr):
    n = getattr(node, attr)
    while n is not None and (n.is_extra or n.type.startswith(("preproc_define", "preproc_undef", "preproc_region",
                                                              "preproc_endregion", "pragma"))):
        n = getattr(n, attr)
    return n


def _edge(n):
    return n is not None and (n.type in SEPARATORS or n.type in _EDGE_TYPES or n.type.lower() in _EDGE_TYPES
                              or n.type.endswith("_expression"))


_UNIT_HOSTS = ("preproc_conditional_statement", "preproc_fragmented_else_tail", "preproc_guarded_statement",
               "preproc_conditional_permissions", "preproc_split_permissions_property")


# Split hosts whose arms hold statements, so a `;` at a group's end ends a statement (`end;` closing a split
# `begin`, BC.History CustContUpdate.Codeunit.al:144). The other split hosts (field, key, declaration, report
# dataitem header, ...) join values with `;`. A split node spans past its `#endif`, so its last child is the `;` of
# the statement it completes (CRMSetupDefaults.Codeunit.al:2257: a case branch whose `#if` arm holds one pattern
# and `,`; the node ends at the branch's `exit(...);`). Task 6 deferred minor: 58 such sites were counted sep-after.
_SPLIT_STATEMENT_PREFIXES = ("preproc_split_procedure", "preproc_split_if_", "preproc_split_case_",
                             "preproc_split_code_block_", "preproc_split_block_", "preproc_split_else_begin",
                             "preproc_split_complete_body")


def _terminates(host):
    """Hosts whose trailing `;` ends the last unit (Permissions' `;` ends the property, the list joins
    with `,`); in link, impl-values, option-members, table-relation and where hosts it stays a separator."""
    return (host in _UNIT_HOSTS or (host.startswith("preproc_split_") and "statement" in host)
            or host.startswith(_SPLIT_STATEMENT_PREFIXES))


def classify(node):
    """The placement class of a preproc group, or None when it is not next to a separator or
    expression edge. sep-before/sep-after/sep-both: a separator inside the group at its start/end;
    suffix/prefix: an operator inside at its start/end; trail/lead-optional: nothing of the kind
    inside, a separator sibling before/after; other: only an expression-edge sibling."""
    body = _content(node.text.decode("utf-8", "replace"))
    kids = [c for c in node.children if not c.is_extra and c.type not in _DIRECTIVE_HEADS]
    lead = bool(kids) and kids[0].type in SEPARATORS
    trail = bool(kids) and kids[-1].type in SEPARATORS
    # a `;` that ends the group's last unit (a statement, a permission list) ends it; it joins nothing
    terminated = trail and kids[-1].type == ";" and _terminates(node.type)
    if terminated:
        trail = False
    prev, nxt = _near(node, "prev_sibling"), _near(node, "next_sibling")
    if terminated and not lead:
        return "terminated-unit"
    if lead and trail:
        return "sep-both"
    if lead:
        return "sep-before"
    if trail:
        return "sep-after"
    if _LEAD_OP.match(body):
        return "suffix"
    if _TRAIL_OP.search(body):
        return "prefix"
    if prev is not None and prev.type in SEPARATORS:
        return "trail"
    if nxt is not None and nxt.type in SEPARATORS:
        return "lead-optional"
    if _edge(prev) or _edge(nxt):
        return "other"
    return None


def _groups(root):
    cur = root.walk()
    while True:
        if cur.node.is_named and _is_group(cur.node.type):
            yield cur.node
        if cur.goto_first_child() or cur.goto_next_sibling():
            continue
        while cur.goto_parent():
            if cur.goto_next_sibling():
                break
        else:
            return


def walk(roots, parser=None, per_class_examples=3):
    """(counts {(host, class): n}, examples {(host, class): [file:line, ...]}) over every .al under
    the roots that holds an `#if` (a file without one cannot hold a group)."""
    if parser is None:
        from tools.query_coverage import loader
        parser = loader.make_parser(loader.load_language(loader.ensure_library(loader.REPO_ROOT)))
    from tools.has_error_sweep import decode_al
    counts, examples = {}, {}
    for root in roots:
        for p in sorted(x for x in Path(root).rglob("*") if x.suffix.lower() == ".al" and x.is_file()):
            data = decode_al(p.read_bytes()).encode("utf-8", "surrogateescape")
            if b"#if" not in data.lower():
                continue
            for node in _groups(parser.parse(data).root_node):
                cls = classify(node)
                if cls is None:
                    continue
                k = (node.type, cls)
                counts[k] = counts.get(k, 0) + 1
                ex = examples.setdefault(k, [])
                if len(ex) < per_class_examples:
                    ex.append(f"{p.as_posix()}:{node.start_point[0] + 1}")
    return counts, examples


def production_shapes(roots, parser=None):
    return walk(roots, parser)[0]


ROOTS = {"BC.History": "BC.History", "DC": "DC", "BC28.1": "H:/Git/BC28.1", "BCApps-29.0": "H:/Git/BCApps-29.0"}
SHAPES_JSON = Path(__file__).parent / "production_shapes.json"


def main(argv=None):
    """python -m tools.b7_audit.seeds [EXAMPLES.json]: walk the four corpora, write production_shapes.json
    (counts only, sorted, LF) and, when a path is given, the example locations (not committed)."""
    import json
    import sys
    argv = sys.argv[1:] if argv is None else argv
    repo = Path(__file__).resolve().parents[2]
    roots = [(repo / p if not Path(p).is_absolute() and ":" not in p else Path(p)) for p in ROOTS.values()]
    counts, examples = walk(roots)
    rows = [{"host": h, "class": c, "count": n} for (h, c), n in sorted(counts.items())]
    SHAPES_JSON.write_text(json.dumps({"roots": list(ROOTS), "shapes": rows}, indent=1) + "\n",
                           encoding="utf-8", newline="\n")
    if argv:
        Path(argv[0]).write_text(json.dumps({f"{h}|{c}": v for (h, c), v in sorted(examples.items())}, indent=1) + "\n",
                                 encoding="utf-8", newline="\n")
    print(f"{len(rows)} (host, class) pairs, {sum(counts.values())} sites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
