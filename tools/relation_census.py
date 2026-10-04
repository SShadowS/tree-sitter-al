"""B5 relation census: the TableRelation contract and the D1/D2/D3 delta (spec 2026-10-04 §5.5).

    python tools/relation_census.py check --root ./BC.History [--cur-lib DLL] [--manifest OUT.tsv]
    python tools/relation_census.py delta --root ./BC.History --base-lib BASE.dll [--cur-lib DLL] [--manifest OUT.tsv]

Exit 0 clean, 1 finding, 2 cannot run (a census that cannot run never reports clean).
"""
from __future__ import annotations

import argparse, hashlib, sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.alc_facts.extract import load_property_hosts  # noqa: E402
from tools import has_error_sweep  # noqa: E402
from tools.query_coverage import loader  # noqa: E402

RELATION_TYPES = {"table_relation_value", "preproc_conditional_table_relation",
                  "simple_table_relation", "qualified_name"}
D2_NAMES = {"autoformatexpression", "enabled", "styleexpr", "datacaptionexpression",
            "visible", "indentationcolumn", "editable", "showmandatory"}
EXPR_DELEGATES = {"ParseTextExpressionPropertyValue", "ParseClientSideBooleanExpressionPropertyValue",
                  "ParseStyleExpressionPropertyValue", "ParseIntegerExpressionPropertyValue"}
SHAPE_OK = {"table_relation_value", "preproc_conditional_property_value"}

# Tree-context key (types of the nearest three named ancestors of a D2 property, skipping the
# generic `declaration_body` and any `preproc_*` wrapper) -> compiler host kinds (spec §2.1).
# Built from data: `check` with this map empty, every distinct `d2-unmapped` key over the four
# corpora, each mapped by hand against tools/alc_facts/property-hosts.tsv.
# Lookup chains, decompiled ObjectParser.cs (alc 18.0.41.62505), first match wins:
# LookupAnyControlProperty (line 9482) = PageField ?? PageGroup ?? PagePart ?? PageArea
# LookupAnyActionProperty  (line 9287) = PageAction ?? PageActionRef ?? PageActionGroup ?? PageActionArea
_CTRL_CHAIN = ("PageField", "PageGroup", "PagePart", "PageArea")
_ACT_CHAIN = ("PageAction", "PageActionRef", "PageActionGroup", "PageActionArea")
CONTEXT_HOSTS: dict[tuple[str, ...], tuple[str, ...]] = {
    # table field
    ("field_declaration", "fields_body", "fields_section"): ("Field",),
    ("report_column", "report_body", "report_dataitem"): ("ReportColumn",),  # report column
    ("report_column", "dataset_mod_body", "add_dataset_modification"): ("ReportColumn",),  # reportextension add column
    # page field in a group / repeater / cuegroup / layout area / add* modification
    ("page_field", "layout_container_body", "group_section"): ("PageField",),
    ("page_field", "layout_container_body", "repeater_section"): ("PageField",),
    ("page_field", "layout_container_body", "cuegroup_section"): ("PageField",),
    ("page_field", "layout_body", "area_section"): ("PageField",),
    ("page_field", "layout_body", "addafter_modification"): ("PageField",),
    ("page_field", "layout_body", "addbefore_modification"): ("PageField",),
    ("page_field", "layout_body", "addlast_modification"): ("PageField",),
    # page action (area / group / actions section / add* modification)
    ("action_declaration", "action_group_body", "action_group_section"): ("PageAction",),
    ("action_declaration", "action_body", "action_area_section"): ("PageAction",),
    ("action_declaration", "action_body", "addafter_action_modification"): ("PageAction",),
    ("action_declaration", "action_body", "addlast_action_modification"): ("PageAction",),
    ("fileuploadaction_declaration", "action_body", "action_area_section"): ("PageFileUploadAction",),
    # page group: properties sit in the group/repeater body
    ("layout_container_body", "group_section", "layout_container_body"): ("PageGroup",),
    ("layout_container_body", "group_section", "layout_body"): ("PageGroup",),
    ("layout_container_body", "repeater_section", "layout_body"): ("PageGroup",),  # repeater is a group
    # page action group
    ("action_group_body", "action_group_section", "action_group_body"): ("PageActionGroup",),
    ("action_group_body", "action_group_section", "action_body"): ("PageActionGroup",),
    # page part
    ("part_section", "layout_body", "area_section"): ("PagePart",),
    ("part_section", "layout_body", "addafter_modification"): ("PagePart",),
    # page object properties
    ("page_declaration", "source_file"): ("Page",),
    # `modify`: the lookup chain, field first; the first host with a row for the name decides (check_tree)
    ("modify_modification", "layout_body", "layout_section"): _CTRL_CHAIN,
    ("modify_action_modification", "action_body", "actions_section"): _ACT_CHAIN,
}


class Unclassifiable(Exception):
    pass


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    start: int
    end: int
    detail: str


class DeltaResult(NamedTuple):
    findings: list
    rows: list
    d3_old_relations: int  # simple_table_relation nodes under TableRelation in the BASE parse


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


_LEAVES = ("identifier", "quoted_identifier", "keyword_identifier")


def normalise_old_target(str_node) -> list[tuple[int, int, bytes]]:
    """Pre-B5 simple_table_relation -> ordered segments (spec §4.2, D3 normalisation)."""
    out: list[tuple[int, int, bytes]] = []

    def norm(n):
        if n.type in _LEAVES:
            out.append((n.start_byte, n.end_byte, n.text))
        elif n.type == "member_expression":
            norm(n.child_by_field_name("object"))
            m = n.child_by_field_name("member")
            if m is None:
                raise Unclassifiable(f"member_expression without member at {n.start_byte}")
            out.append((m.start_byte, m.end_byte, m.text))
        else:
            raise Unclassifiable(f"{n.type} at {n.start_byte}")

    for t in str_node.children_by_field_name("table"):
        norm(t)
    return out


def _chain(n) -> list[tuple[int, int]]:
    """Dotted chain leaf spans; a subscript is taken as its base (D2)."""
    if n.type in _LEAVES:
        return [(n.start_byte, n.end_byte)]
    if n.type == "member_expression":
        m = n.child_by_field_name("member")
        return _chain(n.child_by_field_name("object")) + [(m.start_byte, m.end_byte)]
    if n.type == "subscript_expression":
        return _chain(n.child_by_field_name("object") or n.named_children[0])
    raise Unclassifiable(f"{n.type} at {n.start_byte}")


def _context_key(p) -> tuple[str, ...]:
    out, a = [], p.parent
    while a is not None and len(out) < 3:
        if a.is_named and a.type != "declaration_body" and not a.type.startswith("preproc_"):
            out.append(a.type)
        a = a.parent
    return tuple(out)


def _dotted(v) -> bool:
    """A D2 property is of interest only when its value is a dotted chain: a relation today,
    any value holding a member_expression after B5 (`Visible = false` is no D2 site)."""
    return v.type == "table_relation_value" or any(x.type == "member_expression" for x in walk(v))


def _outside(n) -> bool:
    """True when no ancestor is a TableRelation property, nor itself a relation node: a site is
    reported once, at its outermost relation node."""
    a = n.parent
    while a is not None:
        if (a.type == "property" and prop_name(a) == "tablerelation") or a.type in RELATION_TYPES:
            return False
        a = a.parent
    return True


def _shape_ok(v) -> bool:
    if v.type == "table_relation_value":
        return True
    if v.type == "preproc_conditional_property_value":
        subs = v.children_by_field_name("value")
        return all(_shape_ok(s) for s in subs)
    return False


_HOSTS_BY_NAME: dict[str, dict[str, set[str]]] | None = None


def _host_rows():
    global _HOSTS_BY_NAME
    if _HOSTS_BY_NAME is None:
        d: dict[str, dict[str, set[str]]] = {}
        for name, host, _vk, delegate in load_property_hosts():
            d.setdefault(name, {}).setdefault(host, set()).add(delegate)
        _HOSTS_BY_NAME = d
    return _HOSTS_BY_NAME


def check_tree(path: str, tree, src: bytes, *, target_check: bool | None = None,
               rows: list | None = None) -> list[Finding]:
    """Per-file core of `check`. target_check None = on iff the language has `qualified_name`."""
    if target_check is None:
        target_check = tree.language.id_for_node_kind("qualified_name", True) is not None
    out: list[Finding] = []
    sha = hashlib.sha256(src).hexdigest()
    root = tree.root_node

    def add(kind, n, detail=""):
        out.append(Finding(kind, path, n.start_byte, n.end_byte, detail))

    if root.has_error:
        add("has-error", root)
    for n in walk(root):
        t = n.type
        if t == "property":
            name = prop_name(n)
            v = n.child_by_field_name("value")
            hosts: tuple[str, ...] = ()
            if name == "tablerelation":
                if v is not None and not _shape_ok(v):
                    add("relation-shape", n, v.type)
            elif name in D2_NAMES and v is not None and _dotted(v):
                key = _context_key(n)
                mapped = CONTEXT_HOSTS.get(key)
                if mapped is None:
                    add("d2-unmapped", n, repr(key))
                else:
                    hosts = mapped
                    per = _host_rows().get(name.upper(), {})
                    seen = [h for h in mapped if h in per][:1]  # chains are first-match: the first host with a row decides
                    if not seen:
                        add("d2-host", n, f"{name} has no row on any of {mapped}")
                    for h in seen:
                        if not per[h] <= EXPR_DELEGATES:
                            add("d2-host", n, f"{name} on {h}: {sorted(per[h])}")
            if rows is not None and (name == "tablerelation" or (name in D2_NAMES and v is not None and _dotted(v))):
                rows.append((path, n.start_byte, n.end_byte, sha, name,
                             v.type if v is not None else "", ",".join(hosts)))
        if t in RELATION_TYPES and _outside(n):
            add("relation-outside", n, t)
        if target_check and t == "simple_table_relation":
            tg = n.children_by_field_name("target")
            if len(tg) != 1 or tg[0].type != "qualified_name" or n.children_by_field_name("table"):
                add("target", n, "need exactly one qualified_name target and no table field")
            else:
                for seg in tg[0].named_children:
                    if seg.type not in ("identifier", "quoted_identifier") or seg.child_count:
                        add("target", seg, f"segment {seg.type} children={seg.child_count}")
    return out


def _al_files(roots):
    for r in roots:
        r = Path(r)
        if not r.is_dir():
            raise FileNotFoundError(f"root not a directory: {r}")
        files = sorted(p for p in r.rglob("*") if p.suffix.lower() == ".al" and p.is_file())
        if not files:
            raise FileNotFoundError(f"root holds no .al files: {r}")
        yield from files


def _read(f: Path) -> bytes:
    """The parse buffer, exactly as has_error_sweep builds it (UTF-16 BOM decoded, UTF-8 BOM
    stripped); node offsets and hashes refer to THIS buffer."""
    return has_error_sweep.decode_al(f.read_bytes()).encode("utf-8", "surrogateescape")


def check(roots, parser, *, rows: list | None = None, target_check: bool | None = None) -> list[Finding]:
    out: list[Finding] = []
    for f in _al_files(roots):
        src = _read(f)
        out.extend(check_tree(str(f), parser.parse(src), src, target_check=target_check, rows=rows))
    return out


# --- delta -----------------------------------------------------------------------------

def _sexp(n, fields) -> str:
    """Named-node S-expression with field names, spans and MISSING marks; a
    simple_table_relation's target children collapse to one placeholder: pass ("table",) for an
    OLD tree and ("target",) for a NEW one, so a stray field of the other kind stays visible."""
    parts, placed = [], False
    cur = n.walk()
    if cur.goto_first_child():
        while True:
            c = cur.node
            if c.is_named:
                fn = cur.field_name
                if n.type == "simple_table_relation" and fn in fields:
                    if not placed:
                        parts.append("T")
                        placed = True
                else:
                    parts.append((fn + ":" if fn else "") + _sexp(c, fields))
            if not cur.goto_next_sibling():
                break
    miss = "!" if n.is_missing else ""
    return f"({n.type}{miss}@{n.start_byte}-{n.end_byte}{''.join(' ' + p for p in parts)})"


def _strs(v):
    return [n for n in walk(v) if n.type == "simple_table_relation"]


def _d1(name, o, n):
    if name != "tablerelation" or o.type not in ("identifier", "quoted_identifier"):
        return False
    if n.type != "table_relation_value" or n.named_child_count != 1:
        return False
    e = n.named_children[0]
    if e.type != "table_relation_expression" or e.named_child_count != 1:
        return False
    s = e.named_children[0]
    if s.type != "simple_table_relation":
        return False
    tg = s.children_by_field_name("target")
    if len(tg) != 1 or tg[0].type != "qualified_name" or s.named_child_count != 1:
        return False
    return segments(tg[0]) == [(o.start_byte, o.end_byte, o.text)]


def _d2(name, o, n):
    if name == "tablerelation" or o.type != "table_relation_value" or n.type != "property_expression":
        return False
    olds = _strs(o)
    if len(olds) != 1:
        return False
    try:
        old_chain = [s for t in olds[0].children_by_field_name("table") for s in _chain(t)]
        x = n
        while x.type == "property_expression" and x.named_child_count == 1:
            x = x.named_children[0]
        return old_chain == _chain(x)
    except Unclassifiable:
        return False


def _d3(name, o, n):
    if name != "tablerelation" or o.type != n.type:
        return False
    os_, ns = _strs(o), _strs(n)
    if len(os_) != len(ns):
        return False
    for a, b in zip(os_, ns):
        tg = b.children_by_field_name("target")
        if len(tg) != 1 or normalise_old_target(a) != segments(tg[0]):
            return False
    return _sexp(o, ("table",)) == _sexp(n, ("target",))


def classify(name: str, old_value, new_value) -> str:
    name = name.lower()
    hits = []
    if _d1(name, old_value, new_value):
        hits.append("D1")
    if _d2(name, old_value, new_value):
        hits.append("D2")
    if _d3(name, old_value, new_value):  # may raise Unclassifiable
        hits.append("D3")
    if len(hits) == 1:
        return hits[0]
    raise Unclassifiable("ambiguous: " + "+".join(hits) if hits else "unclassified")


def _inventory(path, tree):
    return {(path, p.start_byte, p.end_byte): p for p in walk(tree.root_node) if p.type == "property"}


def delta(roots, base_parser, cur_parser) -> DeltaResult:
    findings: list[Finding] = []
    rows: list = []
    d3_old = 0
    for f in _al_files(roots):
        src, path = _read(f), str(f)
        sha = hashlib.sha256(src).hexdigest()
        if hashlib.sha256(_read(f)).hexdigest() != sha:
            raise RuntimeError(f"source hash changed while reading {path}")
        bt, ct = base_parser.parse(src), cur_parser.parse(src)
        if ct.root_node.has_error and not bt.root_node.has_error:
            findings.append(Finding("has-error-new", path, 0, len(src), "base clean, current has_error"))
        bi, ci = _inventory(path, bt), _inventory(path, ct)
        for k in bi.keys() ^ ci.keys():
            findings.append(Finding("site-dropped", path, k[1], k[2],
                                    "base only" if k in bi else "current only"))
        for k in bi.keys() & ci.keys():
            bp, cp = bi[k], ci[k]
            name = prop_name(bp)
            bv, cv = bp.child_by_field_name("value"), cp.child_by_field_name("value")
            if name == "tablerelation" and bv is not None:
                d3_old += len(_strs(bv))
            if bv is None or cv is None:
                if (bv is None) != (cv is None):
                    findings.append(Finding("unclassified", path, k[1], k[2], "value presence differs"))
                continue
            if str(bv) == str(cv):
                continue
            try:
                cls = classify(name, bv, cv)
            except Unclassifiable as e:
                msg = str(e)
                kind = "ambiguous" if msg.startswith("ambiguous") else (
                    "unclassified" if msg == "unclassified" else "unclassifiable")
                findings.append(Finding(kind, path, k[1], k[2], f"{name}: {bv.type} -> {cv.type}; {msg}"))
                continue
            rows.append((path, k[1], k[2], sha, name, cls, bv.type, cv.type))
    return DeltaResult(findings, rows, d3_old)


# --- CLI -------------------------------------------------------------------------------

def _write_tsv(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write("\t".join(str(c) for c in r) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("check", "delta"))
    ap.add_argument("--root", action="append", default=[], type=Path)
    ap.add_argument("--base-lib", type=Path)
    ap.add_argument("--cur-lib", type=Path)
    ap.add_argument("--manifest", type=Path)
    a = ap.parse_args(argv)
    try:
        if not a.root:
            raise RuntimeError("no --root")
        cur = parser_for(a.cur_lib)
        if a.mode == "check":
            rows: list = []
            findings = check(a.root, cur, rows=rows)
            res_rows = rows
            extra = ""
        else:
            if not a.base_lib:
                raise RuntimeError("delta needs --base-lib")
            res = delta(a.root, parser_for(a.base_lib), cur)
            findings, res_rows = res.findings, res.rows
            extra = f" d3_old_relations={res.d3_old_relations} classes={dict(Counter(r[5] for r in res_rows))}"
        if a.manifest:
            _write_tsv(a.manifest, res_rows)
    except Exception as e:  # cannot run is never clean
        print(f"relation_census: cannot run: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    by = Counter(f.kind for f in findings)
    shown: Counter = Counter()
    for f in findings:  # first 30 of each kind: the common kinds number in the tens of thousands
        shown[f.kind] += 1
        if shown[f.kind] > 30:
            continue
        print(f"{f.kind}\t{f.path}:{f.start}-{f.end}\t{f.detail}")
    print(f"relation_census {a.mode}: findings={len(findings)} {dict(sorted(by.items()))}{extra}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
