"""B7b-1 helper: the assertion rows of `assertions.tsv` that close the strict-list cells (B7b-1 Task 13).

Each row is built from an independent model of the cell's hole text, never from the parser: the list's items and
`#if` groups in source order, every group exact (`preproc_conditional_<family>!`) and owning exactly its arm items,
the host non-exact. Separators and comments are skipped. A row's `holds` column is its truth on LIB.

    python -m tools.b7_audit.strict_list_assertions LIB                    # the manifest's admitted cells (1404)
    python -m tools.b7_audit.strict_list_assertions LIB --header-ids FILE  # header cells, one cell id per line

`--header-ids` is for the cells outside the manifest that the shared field_list change turned clean (the 18 key /
fieldgroup / addlast header cells, Task 6); their hole is `Name ; <field list>` and only the part after the fixed `;`
is modelled. Rows go to stdout (TSV, assertions.tsv columns), rows that do not hold on LIB to stderr. Merge by hand,
then `python -m tools.b7_audit assert --refresh`.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

GROUP = {"implements": "preproc_conditional_implements", "key-fields": "preproc_conditional_field_list_items",
         "sorting": "preproc_conditional_sorting_fields", "order-by": "preproc_conditional_order_by_fields",
         "move-modification": "preproc_conditional_move_elements",
         "array-dimensions": "preproc_conditional_array_dimensions",
         "attribute-arguments": "preproc_conditional_attribute_args", "var-names": "preproc_conditional_var_names"}
TOK = re.compile(r'//[^\n]*|/\*.*?\*/|#\s*(if|elif|else|endif)\b[^\n]*|"[^"]*"|\'[^\']*\'|\d+|[A-Za-z_]\w*|[,;]|\S',
                 re.S)
ATOM = re.compile(r'"[^"]*"|\'[^\']*\'|\d+|[A-Za-z_]\w*')
MANIFEST_REASON = ("B7b-1 strict list (Task 13): the hole's items and conditional groups in source order, each group a "
                   "{group} owning exactly its arm items; model built from the hole text, not the parser")
HEADER_REASON = ("B7b-1 Task 13 (out of the manifest; Task 6 side effect): after the fixed `;` the field list holds the "
                 "group and the items in source order; model built from the hole text, not the parser")


def atom(t):
    if t.startswith('"'):
        return "quoted_identifier"
    if t.startswith("'"):
        return "string_literal"
    if t.isdigit():
        return "integer"
    if t.lower() in ("true", "false"):
        return "boolean"
    return "identifier"


def model(hole, group):
    """-> pattern text of the list's named children: atoms and exact groups, in source order."""
    stack = [[]]
    for m in TOK.finditer(hole):
        t = m.group(0)
        if t.startswith("//") or t.startswith("/*") or t in ",;":
            continue
        d = m.group(1)
        if d == "if":
            stack.append(["(preproc_if)"])
        elif d in ("elif", "else"):
            stack[-1].append(f"(preproc_{d})")
        elif d == "endif":
            kids = stack.pop() + ["(preproc_endif)"]
            stack[-1].append(f"({group}! " + " ".join(kids) + ")")
        elif ATOM.fullmatch(t):
            stack[-1].append(f"({atom(t)})")
        else:
            raise ValueError(f"unexpected token {t!r} in {hole!r}")
    if len(stack) != 1:
        raise ValueError(f"unbalanced #if in {hole!r}")
    return " ".join(stack[0])


def main(argv=None):
    from tools.b7_audit import evidence, judge, manifest
    from tools.query_coverage import loader
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lib", type=Path)
    ap.add_argument("--header-ids", type=Path)
    a = ap.parse_args(argv)
    by_id = {e.cell.id: e for e in evidence.universe()}
    parser = loader.make_parser(loader.load_language(a.lib))
    if a.header_ids:
        todo = [(cid, None) for cid in a.header_ids.read_text(encoding="utf-8").split()]
    else:
        todo = [(m.cell_id, m.family) for m in manifest.load() if m.disposition == "admitted"]
    bad = 0
    for cid, family in todo:
        c = by_id[cid].cell
        src = c.source.encode("utf-8")
        hole = src[c.hole[0]:c.hole[1]].decode("utf-8")
        if family is None:
            name, sep, rest = hole.partition(";")
            if not sep or "#" in name:
                raise ValueError(f"{cid}: not a `Name ; <list>` header hole: {hole!r}")
            pat, reason = f"(field_list {model(rest, GROUP['key-fields'])})", HEADER_REASON
        else:
            pat = f"({c.key.split(':')[1]} {model(hole, GROUP[family])})"
            reason = MANIFEST_REASON.format(group=GROUP[family])
        holds = judge.check_assertion(parser.parse(src).root_node, judge.Assertion(cid, pat, (), ""))
        if not holds:
            bad += 1
            print(f"NOT HOLDING {cid}\n  {pat}\n  hole={hole!r}", file=sys.stderr)
        fp = ",".join(judge.fingerprints(hashlib.sha256(src).hexdigest()))
        print("\t".join((cid, pat, fp, reason, "true" if holds else "false")))
    print(f"{len(todo)} rows, {bad} not holding", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
