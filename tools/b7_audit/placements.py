"""Placement generator (spec 6): each registry row -> concrete #if-placement cells, each with its
intended configuration-validity vector.

A cell is built by rewriting the row's `plain` filling of the template's hole, so it stays
type-correct wherever the plain filling is. Cells are generated for the row's WITNESS host only
(spec 10: one host-parity witness per row). Placement symbols are X and Y (templates own TPL/TPL2).

Shapes are written literally below, one directive or content line per `\\n`. In content lines the
tokens A B C D E F G H L R are element/operand slots, `s`/`t` the separator/terminator, `op`/`op2`
the operators, `CLOSER` the statement end; any other token is literal text.

The intended vector of a shape is declared, never derived from its text: "all", "X" (valid only
with X defined), "notX", or chosen per host from the family tables. `well_formed` is the
independent syntactic model the tests hold every vector against.
"""
import re
from dataclasses import dataclass
from itertools import combinations

from tools.b7_audit.registry import HOLE

PLACEMENT_SYMBOLS = ("X", "Y")


@dataclass(frozen=True)
class Cell:
    id: str
    key: str
    host: str
    placement: str
    source: str
    symbols: tuple
    intended_valid: frozenset
    hole: tuple                    # byte range of the filled hole in source (utf-8)
    plain: str                     # the template filled with the row's plain filling
    check: tuple = ()              # the well-formedness model of the hole (see well_formed)


def assignments(symbols):
    """Every subset of `symbols` as a frozenset, sorted by size then names."""
    syms = sorted(set(symbols))
    out = [frozenset(c) for n in range(len(syms) + 1) for c in combinations(syms, n)]
    return sorted(out, key=lambda e: (len(e), sorted(e)))


# --- 6.1 separator placements (lists) ----------------------------------------------------------
# (id, shape, vector); vector "trail"/"holes"/"empty" is decided per family below.
LIST_SHAPES = [
    ("sep-after", "A s\n#if X\nB s\n#endif\nC", "all"),
    ("sep-before", "A\n#if X\ns B\n#endif\ns C", "all"),
    ("sep-before-end", "A\n#if X\ns B\n#endif", "all"),
    ("first-replace", "#if X\nA\n#else\nB\n#endif\ns C", "all"),
    ("lead-optional", "#if X\nA s\n#endif\nB", "all"),
    ("count-differs", "A\n#if X\ns B s C\n#else\ns D\n#endif", "all"),
    ("both-in-arm", "A\n#if X\ns B s\n#else\ns\n#endif\nC", "all"),
    ("sep-only", "A\n#if X\ns\n#else\ns\n#endif\nB", "all"),
    ("empty", "A s\n#if X\n#endif\nB", "all"),
    ("adjacent-indep", "A\n#if X\ns B\n#endif\n#if Y\ns C\n#endif", "all"),
    ("adjacent-compl", "A\n#if X\ns B\n#endif\n#if not X\ns C\n#endif", "all"),
    ("elif", "A\n#if X\ns B\n#elif Y\ns C\n#endif\ns D", "all"),
    ("nested", "A\n#if X\ns B\n#if Y\ns C\n#endif\n#endif\ns D", "all"),
    ("one-elem", "#if X\nA s B\n#else\nA\n#endif", "all"),
    ("empty-list", "#if X\nA s B\n#endif", "empty"),
    ("holes-lead", "#if X\ns\n#endif\nA s B", "holes"),
    ("holes-mid", "A s\n#if X\ns\n#endif\nB", "holes"),
    ("holes-trail", "A s B\n#if X\ns\n#endif", "trailsep"),
    ("trail", "A s\n#if X\nB\n#endif", "trail"),
]
# Shapes that move a different element into first position, skipped where the first is positional.
MOVES_FIRST = {"first-replace", "lead-optional"}

# Family facts (syntax only; alc judges semantics in Task 7).
HOLES = {"option-members"}                       # empty members allowed: option ordinals
TRAILING = HOLES                                 # a trailing separator is an empty member
EMPTY_OK = {"arguments", "parameter-list", "list-literal", "attribute-arguments"}
POSITIONAL_FIRST = {"caption-subfields", "label-attributes"}   # the caption text must stay first

# Extra elements, used in order and only where the family can take them (distinct, valid).
# Families absent here supply only the plain's own elements (fixed arity: arguments, subscript,
# parameter-list, split-call, type/attribute arguments; or no proven-valid extra: implements,
# implementation-list, order-by, move-modification).
_INTS = [str(n) for n in range(21, 25)]          # 21.. clear of every template's case values
POOLS = {
    "case-patterns": _INTS, "list-literal": _INTS, "integer-list": _INTS, "array-dimensions": ["4", "5"],
    "option-members": ["D", "E", "F", "G"],
    "var-names": ["X3", "X4", "X5"],
    "ml-pairs": ["ENU = 'a'", "DAN = 'b'", "DEU = 'c'", "FRA = 'd'"],
    "namespace-pairs": ["p = 'urn:a'", "q = 'urn:b'", "r = 'urn:c'", "t = 'urn:d'"],
    "caption-subfields": ["Locked = true", "Comment = 'c'", "MaxLength = 10"],
    "label-attributes": ["Locked = true", "Comment = 'c'", "MaxLength = 10"],
    "link-list": ["K = field(K)", "N = const(1)", "B = const(true)", "O = const(A)"],
    "where-filter": ["K = field(K)", "N = const(1)", "B = const(true)", "O = const(A)"],
    "key-fields": ["K", "N", "B", "O"], "sorting": ["K", "N", "B", "O"],   # table T's four fields
    "permissions": ["tabledata T = R", "tabledata T2 = R", "tabledata T3 = R", "codeunit P = X"],
}


def _ident(e):
    """The name an element is keyed by (a duplicate key is invalid): `K = ...` -> K."""
    m = re.match(r"\s*(?:tabledata|codeunit)?\s*([\w\"']+)", e)
    return m.group(1).lower() if m else e


def _declares(template, element):
    """Permissions may only name objects the template declares."""
    m = re.match(r"(tabledata|codeunit)\s+(\w+)", element)
    if not m:
        return True
    kind = "table" if m.group(1) == "tabledata" else "codeunit"
    return re.search(rf"^\s*{kind}\s+\d+\s+{m.group(2)}\b", template, re.M | re.I) is not None


def _extend(family, els, template):
    out = list(els)
    for cand in POOLS.get(family, []):
        if len(out) >= 4:
            break
        if _ident(cand) in {_ident(e) for e in out} or not _declares(template, cand):
            continue
        if family == "var-names" and re.search(rf"\b{cand}\b", template):
            continue
        out.append(cand)
    return out


# --- terminator and fixed-separator placements (constant reading: one element / two elements) --
TERM_SHAPES = [
    ("first-replace", "#if X\nE\n#else\nE\n#endif\nt", "all"),
    ("sep-only", "E\n#if X\nt\n#else\nt\n#endif", "all"),
    ("empty", "E\n#if X\n#endif\nt", "all"),
    ("adjacent-compl", "E\n#if X\nt\n#endif\n#if not X\nt\n#endif", "all"),
    ("elif", "E\n#if X\nt\n#elif Y\nt\n#else\nt\n#endif", "all"),
    ("nested", "E\n#if X\n#if Y\nt\n#else\nt\n#endif\n#else\nt\n#endif", "all"),
    ("trail", "E\n#if X\nt\n#endif", "X"),
]
FIXED_SHAPES = [
    ("first-replace", "#if X\nL\n#else\nL\n#endif\ns R", "all"),
    ("sep-only", "L\n#if X\ns\n#else\ns\n#endif\nR", "all"),
    ("empty", "L s\n#if X\n#endif\nR", "all"),
    ("adjacent-compl", "L\n#if X\ns\n#endif\n#if not X\ns\n#endif\nR", "all"),
    ("elif", "L\n#if X\ns\n#elif Y\ns\n#else\ns\n#endif\nR", "all"),
    ("nested", "L\n#if X\n#if Y\ns\n#else\ns\n#endif\n#else\ns\n#endif\nR", "all"),
    ("sep-before-end", "L\n#if X\ns R\n#endif", "X"),
    ("trail", "L s\n#if X\nR\n#endif", "X"),
]
_LIST_ONLY = sorted({p for p, _, _ in LIST_SHAPES} - {p for p, _, _ in TERM_SHAPES + FIXED_SHAPES})

# --- 6.2 continuation placements ---------------------------------------------------------------
CONT_SHAPES = [
    ("suffix", "E\n#if X\nop F\n#endif", "all"),
    ("suffix-else", "E\n#if X\nop F\n#else\nop2 G\n#endif", "all"),
    ("op-only", "E\n#if X\nop\n#endif\nF", "X"),
    ("prefix", "E op\n#if X\nF op\n#endif\nG", "all"),
    ("whole-operand", "E op\n#if X\nF\n#else\nG\n#endif", "all"),
    ("first", "#if X\nE op\n#endif\nF", "all"),
    ("first-only", "#if X\nE\n#else\nF\n#endif", "all"),
    ("chain", "E op2 F\n#if X\nop G\n#endif\nop2 H", "all"),
    ("consecutive", "E\n#if X\nop F\n#endif\n#if Y\nop G\n#endif", "all"),
    ("nested", "E\n#if X\nop F\n#if Y\nop G\n#endif\n#endif", "all"),
    ("unary-paren", "E op\n#if X\n( F op G )\n#else\nG\n#endif", "all"),
    ("unary-minus", "E op\n#if X\n- F\n#else\nG\n#endif", "all"),
    ("unary-not", "E op\n#if X\nnot F\n#else\nG\n#endif", "all"),
    ("signed", "E op\n#if X\n-1\n#else\nF\n#endif", "all"),
    ("semi-in-arms", "E\n#if X\nop F CLOSER Bar();\n#else\nCLOSER\n#endif", "all"),
]
# Operator families with typed operands (spec 6.2): slot type -> family -> (op, op2, operands F G H,
# shapes the family supports). The slot type is read from the row's plain expression (_slot_type).
_ALL_BIN = {"suffix", "suffix-else", "op-only", "prefix", "whole-operand", "first", "first-only",
            "consecutive", "nested", "semi-in-arms"}
OPERATORS = {
    "Integer": {"arithmetic": ("+", "*", ("2", "3", "4"), _ALL_BIN | {"chain", "unary-paren", "unary-minus", "signed"})},
    "Text": {"arithmetic": ("+", None, ("'b'", "'c'", "'d'"), _ALL_BIN - {"suffix-else"})},
    "Boolean": {
        "logical": ("and", "or", ("true", "false", "Ok"), _ALL_BIN | {"chain", "unary-paren", "unary-not"}),
        "comparison": ("=", "<>", ("true", "false", "Ok"), _ALL_BIN | {"unary-paren", "unary-not"}),
        # a list operand alone would stand in the Boolean slot: no suffix-else, first, first-only
        "membership": ("in", None, ("[true, false]", "[true]", "[false]"),
                       _ALL_BIN - {"suffix-else", "first", "first-only"}),
    },
}
FAMILIES = ("arithmetic", "comparison", "logical", "membership", "type-test")
STATEMENT_END_FAMILIES = {"assignment", "exit-value", "call"}   # item 39: the expression may end the statement


def _slot_type(plain, template):
    """Literals by their form; a bare variable by its declaration in the template."""
    p = plain.strip()
    if p in ("true", "false") or p.startswith("not "):
        return "Boolean"
    if re.fullmatch(r"-?\d+", p):
        return "Integer"
    if re.fullmatch(r"'[^']*'", p):
        return "Text"
    m = re.fullmatch(r"\w+", p) and re.search(rf"\b{p}\s*:\s*(Boolean|Integer|Text)\b", template)
    return m.group(1) if m else None


# --- rendering ---------------------------------------------------------------------------------
_SLOTS = set("ABCDEFGHLR")


def _render(shape, slots, comments=False):
    out = []
    for line in shape.split("\n"):
        if line.startswith("#"):
            out.append(line)
            continue
        toks = []
        for tok in line.split(" "):
            if tok in ("s", "t") and comments:
                toks.append("/* c */")
            toks.append(slots.get(tok, tok) if (tok in _SLOTS or tok in slots) else tok)
        text = " ".join(t for t in toks if t != "")
        out.append(text + (" // c" if comments and text else ""))
    return "\n".join(out)


def _flip(shape):
    """Polarity: every `#if X` becomes `#if not X` and back; the vector is read with X flipped."""
    return re.sub(r"^#if (not )?X$", lambda m: "#if X" if m.group(1) else "#if not X", shape, flags=re.M)


def _pred(vector):
    return {"all": lambda e: True, "X": lambda e: "X" in e, "notX": lambda e: "X" not in e}[vector]


def _intended(shape, vector, tsyms, polar=False):
    psyms = [s for s in PLACEMENT_SYMBOLS if re.search(rf"^#(?:el)?if .*\b{s}\b", shape, re.M)]
    p = _pred(vector)
    ok = [e for e in assignments(psyms) if p(e ^ {"X"} if polar else e)]
    return psyms, frozenset(e | t for e in ok for t in assignments(tsyms))


# --- top-level splitting (strings, quoted identifiers, brackets, comments respected) ------------
def strip_comments(text):
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"":
            j = text.find(c, i + 1)
            j = n - 1 if j < 0 else j
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            out.append(" ")
            i = n if j < 0 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def split_top(text, sep):
    parts, depth, cur, quote = [], 0, [], None
    for c in text:
        if quote:
            quote = None if c == quote else quote
        elif c in "'\"":
            quote = c
        elif c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        elif c == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(c)
    parts.append("".join(cur))
    return parts


def _norm(s):
    return re.sub(r"\s+", "", s)


def well_formed_list(text, sep, holes=False, empty=False, elements=None):
    """A list: tokens split on top-level `sep`, no empty token unless the host allows holes, each
    token one element (when `elements` is given), an empty list only where the host allows it."""
    text = strip_comments(text)
    if not text.strip():
        return empty
    toks = [t.strip() for t in split_top(text, sep)]
    if not holes and "" in toks:
        return False
    known = None if elements is None else {_norm(e) for e in elements}
    return all(t == "" or known is None or _norm(t) in known for t in toks)


_TOKEN = re.compile(r"\s*(?:(?P<num>\d+(?:\.\d+)?)|(?P<str>'(?:[^']|'')*')|(?P<id>\"[^\"]*\"|[A-Za-z_]\w*)"
                    r"|(?P<op><>|<=|>=|\.\.|[-+*/=<>()\[\],.]))")
_BIN = {"+", "-", "*", "/", "=", "<>", "<", ">", "<=", ">=", "div", "mod", "and", "or", "xor", "in"}


def well_formed_expr(text):
    """expr := term (binop term)*; term := ('-'|'not')* primary; primary := literal | name(.name)* |
    '(' expr ')' | '[' expr (',' expr)* ']'."""
    toks, pos, text = [], 0, strip_comments(text).strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            return False
        toks.append(m.group(m.lastgroup).lower() if m.lastgroup == "id" else m.group(m.lastgroup))
        pos = m.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
    i = 0

    def expr():
        nonlocal i
        if not term():
            return False
        while i < len(toks) and toks[i] in _BIN:
            i += 1
            if not term():
                return False
        return True

    def term():
        nonlocal i
        while i < len(toks) and toks[i] in ("-", "not"):
            i += 1
        if i >= len(toks):
            return False
        t = toks[i]
        i += 1
        if t in ("(", "["):
            close = ")" if t == "(" else "]"
            if not expr():
                return False
            while close == "]" and i < len(toks) and toks[i] == ",":
                i += 1
                if not expr():
                    return False
            if i >= len(toks) or toks[i] != close:
                return False
            i += 1
            return True
        if t in _BIN or t in (")", "]", ",", ".", ".."):
            return False
        while i + 1 < len(toks) and toks[i] == "." and re.match(r"[\w\"]", toks[i + 1]):
            i += 2
        return True

    return bool(toks) and expr() and i == len(toks)


def well_formed(cell, text):
    """The independent syntactic model of a cell's hole (`text` = one configuration's flat hole)."""
    kind, *a = cell.check
    if kind == "list":
        sep, lead, tail, holes, empty, elements = a
        t = strip_comments(text).strip()
        for edge, cut in ((lead, lambda t: t[len(sep):] if t.startswith(sep) else None),
                          (tail, lambda t: t[:-len(sep)] if t.endswith(sep) else None)):
            if edge:
                t = cut(t)
                if t is None:
                    return False
                t = t.strip()
        return well_formed_list(t, sep, holes, empty, elements)
    if kind == "exact":                       # terminator / fixed separator: one constant reading
        return _norm(strip_comments(text)) == _norm(a[0])
    if kind == "expr":
        return well_formed_expr(text)
    if kind == "expr-stmt":                   # semi-in-arms: expr CLOSER [Bar();]
        closer = a[0].strip()
        t = _norm(strip_comments(text))
        for tail in (_norm(closer) + "Bar();", _norm(closer)):
            if t.endswith(tail) and well_formed_expr(t[:-len(tail)]):
                return True
        return False
    raise ValueError(kind)


# --- link-name variants (controller ruling) ----------------------------------------------------
LINK_NAMES = ("SubPageLink", "RunPageLink", "LinkFields", "DataItemTableFilter", "ColumnFilter", "DataItemLink")
_PROPERTY_HOSTS = None


def _host_kinds():
    global _PROPERTY_HOSTS
    if _PROPERTY_HOSTS is None:
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "alc_facts" / "property-hosts.tsv"
        kinds = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            name, kind = line.split("\t")[:2]
            kinds.setdefault(name, set()).add(kind)
        _PROPERTY_HOSTS = kinds
    return _PROPERTY_HOSTS


def _link_variants(row):
    """[(suffix, template)] -- one per link name valid in the witness template's container."""
    if row.family != "link-list":
        return [("", row.template)]
    used = sorted(set(re.findall(rf"\b({'|'.join(LINK_NAMES)})\s*=", row.template)))
    if len(used) != 1:
        return [("", row.template)]
    kinds = _host_kinds()
    obj = re.search(r"^(page|report|query|xmlport)\s+\d+", row.template, re.M | re.I)
    prefix = {"page": "Page", "report": "Report", "query": "Query", "xmlport": "XmlPort"}[obj.group(1).lower()] if obj else ""
    container = {k for k in kinds.get(used[0].upper(), set()) if k.startswith(prefix)}
    out = []
    for name in LINK_NAMES:
        if container and container <= kinds.get(name.upper(), set()):
            out.append((f"@{name}", re.sub(rf"\b{used[0]}(\s*=)", rf"{name}\1", row.template)))
    return out


# --- row -> cells ------------------------------------------------------------------------------
def _template_symbols(template):
    """Every symbol the template's own #if/#elif lines test (TPL, TPL2, TPL3, ...)."""
    conds = re.findall(r"^\s*#(?:el)?if\b(.*)$", template, re.M)
    return sorted({w for c in conds for w in re.findall(r"[A-Za-z_]\w*", c)} - {"not", "and", "or"})


def _plan(row):
    """-> (specs, skipped): specs = [(placement, shape, vector, slots, check, polar, comments)]."""
    skipped, specs = [], []
    if row.role in ("na", "lexical", "qualifier") or row.equiv:
        why = f"role {row.role}" + (f": {row.reason}" if row.reason else "")
        return [], [("*", "equiv row: " + row.equiv if row.equiv else why)]
    if set(_template_symbols(row.template)) & set(PLACEMENT_SYMBOLS):
        return [], [("*", "template uses a placement symbol (X or Y)")]
    if row.role in ("list-separator", "edge-separator"):
        return _plan_list(row)
    if row.role in ("terminator", "fixed-separator"):
        return _plan_exact(row)
    if row.role == "continuation":
        return _plan_cont(row)
    return [], [("*", f"unknown role {row.role}")]


def _variants(pid, shape, vector, slots, check, specs):
    """Spec 6.1's `comments` and `polarity` rows: every separator placement also with comments at
    every boundary, and with `#if not X`."""
    specs.append((pid, shape, vector, slots, check, False, False))
    specs.append((pid + "+comments", shape, vector, slots, check, False, True))
    specs.append((pid + "+not", _flip(shape), vector, slots, check, True, False))


def _plan_list(row):
    plain, fam, specs, skipped = row.plain.strip(), row.family, [], []
    sep = "," if len(split_top(plain, ",")) > 1 else ";" if len(split_top(plain, ";")) > 1 else None
    if sep is None:
        return [], [("*", "no top-level separator in plain")]
    if plain == sep:
        return [], [("*", "token-only hole")]
    toks = [t.strip() for t in split_top(plain, sep)]
    lead = toks[0] == "" and len(toks) > 1
    toks = toks[1:] if lead else toks
    tail = len(toks) > 1 and toks[-1] == ""
    toks = toks[:-1] if tail else toks
    els = [t for t in toks if t]
    if len(els) != len(toks):
        return [], [("*", "plain has an inner hole")]
    els = _extend(fam, els, row.template)
    slots = dict(zip("ABCD", els), s=sep)
    holes, empty = fam in HOLES, fam in EMPTY_OK and not (lead or tail)
    check = ("list", sep, lead, tail, holes, empty, tuple(els))
    for pid, shape, vector in LIST_SHAPES:
        need = len({c for c in shape if c in "ABCD"})
        if need > len(els):
            skipped.append((pid, f"family supplies {len(els)} elements, needs {need}"))
            continue
        if pid in MOVES_FIRST and fam in POSITIONAL_FIRST:
            skipped.append((pid, "first element is positional"))
            continue
        if pid == "empty-list" and (lead or tail):
            skipped.append((pid, "fragment with edge separators cannot be emptied"))
            continue
        vector = {"holes": "all" if holes else "notX", "empty": "all" if empty else "X",
                  "trail": "all" if fam in TRAILING else "X",
                  "trailsep": "all" if fam in TRAILING else "notX"}.get(vector, vector)
        # the plain's edge separators (a fragment of a longer list) stay literal in every arm
        _variants(pid, ("s\n" if lead else "") + shape + ("\ns" if tail else ""), vector, slots, check, specs)
    return specs, skipped


def _plan_exact(row):
    plain, specs, skipped = row.plain.strip(), [], []
    if row.role == "terminator":
        if not plain.endswith(";"):
            return [], [("*", "terminator plain does not end in ';'")]
        elem = plain[:-1].strip()
        slots, shapes = {"E": elem, "t": ";"}, TERM_SHAPES
    else:
        sep = next((s for s in (";", ",", ":") if len(split_top(plain, s)) == 2), None)
        if sep is None:
            return [], [("*", "no single top-level separator in plain")]
        left, right = (p.strip() for p in split_top(plain, sep))
        elem = left
        slots, shapes = {"L": left, "R": right, "s": sep}, FIXED_SHAPES
    for pid in _LIST_ONLY:
        skipped.append((pid, f"{row.role} site holds a fixed number of elements"
                              f" ({'one' if row.role == 'terminator' else 'two'})"))
    for pid, shape, vector in shapes:
        if pid == "first-replace" and not elem:
            skipped.append((pid, "token-only hole"))
            continue
        if pid in ("sep-before-end", "trail") and row.role == "fixed-separator" and not slots["R"]:
            skipped.append((pid, "no right element in the hole"))
            continue
        _variants(pid, shape, vector, slots, ("exact", plain), specs)
    return specs, skipped


def _plan_cont(row):
    specs, skipped = [], []
    i = row.template.index(HOLE) + len(HOLE)
    if re.match(r"\s*[-+*/]?:=", row.template[i:]):
        return [], [("*", "assignment target takes no operator continuation")]
    j = row.template.find(";", i)
    closer = row.template[i:j + 1] if j >= 0 else ""
    stmt_end = (row.family in STATEMENT_END_FAMILIES and closer.strip() in (";", ");")
                and "procedure Bar()" in row.template)
    if not stmt_end:
        skipped.append(("semi-in-arms", "host is not a statement whose expression may end it"
                        if row.family not in STATEMENT_END_FAMILIES else "statement end or Bar() not in template"))
    typ = _slot_type(row.plain, row.template)
    if typ is None:
        return [], skipped + [("*", f"slot type of plain {row.plain.strip()!r} not derivable; no operator family types it")]
    fams = OPERATORS[typ]
    for fam in FAMILIES:
        if fam not in fams:
            skipped.append((f"*/{fam}", f"operands of {fam} do not type in a {typ} slot"))
    for fam, (op, op2, operands, supports) in fams.items():
        slots = dict(E=row.plain.strip(), op=op, **dict(zip("FGH", operands)))
        if op2:
            slots["op2"] = op2
        for pid, shape, vector in CONT_SHAPES:
            if pid == "semi-in-arms" and not stmt_end:
                continue
            if pid not in supports:
                skipped.append((f"{pid}/{fam}", f"{fam} in a {typ} slot cannot take {pid}"))
                continue
            check = ("expr-stmt", closer) if pid == "semi-in-arms" else ("expr",)
            specs.append((f"{pid}/{fam}", shape, vector, dict(slots, CLOSER=closer.strip()), check, False, False))
    return specs, skipped


def skipped_for(row):
    return _plan(row)[1]


def cells_for(row):
    specs, _ = _plan(row)
    out = []
    for suffix, template in _link_variants(row) if specs else []:
        tsyms = _template_symbols(template)
        pre, post = template.split(HOLE)
        for pid, shape, vector, slots, check, polar, comments in specs:
            filler = "\n" + _render(shape, slots, comments) + "\n"
            if check[0] == "expr-stmt":       # the hole swallows the statement end
                post_c = post[post.index(";") + 1:]
            else:
                post_c = post
            source = pre + filler + post_c
            a = len(pre.encode())
            psyms, valid = _intended(shape, vector, tsyms, polar)
            placement = pid + suffix
            out.append(Cell(f"{row.key}@{row.witness}#{placement}", row.key, row.witness, placement, source,
                            tuple(sorted(set(tsyms) | set(psyms))), valid, (a, a + len(filler.encode())),
                            pre + row.plain + post, check))
    return out
