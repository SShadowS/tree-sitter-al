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
         "attribute-arguments": "preproc_conditional_attribute_args", "var-names": "preproc_conditional_var_names",
         "parameter-list": "preproc_conditional_parameters",
         "ml-pairs": "preproc_conditional_ml_pairs", "namespace-pairs": "preproc_conditional_namespace_pairs"}
# Families whose item is several tokens (`A: Integer`): every token run between separators and directives is
# ONE named item of this kind (B7b-1b). An attribute bundle would be a sibling, so `[` is refused.
ITEM = {"parameter-list": "parameter", "ml-pairs": "ml_value_pair", "namespace-pairs": "namespace_pair"}
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


# B7b-1d heterogeneous tails: the group per host rule and each attribute name's fragment (a sub-field,
# the report label's keyword pair, or a label_attribute node), in the host's own flat shape.
_CAP = {n: f"(property_name) ({v})" for n, v in (("locked", "boolean"), ("comment", "string_literal"), ("maxlength", "integer"))}
_RPT = {"locked": "(locked_keyword) (boolean)", "comment": "(comment_keyword) (string_literal)",
        "maxlength": "(maxlength_keyword) (integer)"}
_VAR = {"locked": "(label_attribute)", "comment": "(label_attribute)", "maxlength": "(label_attribute)"}
TAILS = {"caption_value": ("preproc_conditional_caption_subfields", _CAP),
         "label_declaration": ("preproc_conditional_report_label_attributes", _RPT),
         "variable_declaration": ("preproc_conditional_label_attributes", _VAR)}


def model(hole, group, item=None, names=None):
    """-> pattern text of the list's named children: atoms (or `item` runs) and exact groups, in source order.
    `names` (B7b-1d): lowercase attribute name -> its fragment; the `= value` after a name is consumed."""
    stack = [[]]
    in_item = False
    skip = 0                               # tokens left to skip after an attribute name (`=`, value)
    for m in TOK.finditer(hole):
        t = m.group(0)
        if t.startswith("//") or t.startswith("/*"):
            continue
        if skip:
            skip -= 1
            continue
        if t in ",;":
            in_item = False
            continue
        if names is not None and t.lower() in names:
            stack[-1].append(names[t.lower()])
            skip = 2
            continue
        d = m.group(1)
        if names is not None and d is None and not t.startswith(("'", '"')) and not t.isdigit():
            continue                       # a terminator cell's hole names the label before the text
        if item is not None and d is None:
            if t == "[":
                raise ValueError(f"attribute in {hole!r}: not modelled")
            if not in_item:
                stack[-1].append(f"({item})")
                in_item = True
            continue
        in_item = False
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
    ap.add_argument("--ids", type=Path, help="cells outside the B7b-1 manifest, one id per line (with --family)")
    ap.add_argument("--family", choices=sorted(GROUP) + ["tail"], help="`tail`: a B7b-1d label/caption tail (TAILS)")
    a = ap.parse_args(argv)
    by_id = {e.cell.id: e for e in evidence.universe()}
    parser = loader.make_parser(loader.load_language(a.lib))
    if a.ids:
        todo = [(cid, a.family) for cid in a.ids.read_text(encoding="utf-8").split()]
    elif a.header_ids:
        todo = [(cid, None) for cid in a.header_ids.read_text(encoding="utf-8").split()]
    else:
        todo = [(m.cell_id, m.family) for m in manifest.load()[1] if m.disposition == "admitted"]
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
        elif family == "tail":
            host = c.key.split(":")[1]
            pat = f"({host} {model(hole, TAILS[host][0], names=TAILS[host][1])})"
            reason = ("B7b-1d (deferred item 46): the hole's text, attributes and conditional groups in source order, "
                      f"each group a {TAILS[host][0]} owning exactly its arm items; model built from the hole text, not the parser")
        else:
            pat = f"({c.key.split(':')[1]} {model(hole, GROUP[family], ITEM.get(family))})"
            reason = MANIFEST_REASON.format(group=GROUP[family])
            if a.ids:
                reason = reason.replace("B7b-1 strict list (Task 13)", "B7b-1b strict list (deferred item 46)")
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
