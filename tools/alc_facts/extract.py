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
                           encoding="utf-8", errors="replace", check=True)
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


ADD = re.compile(r'instance\.Add\("([A-Z0-9_]+)", new (?:Enum)?PropertyTypeInfo\(PropertyKind\.\w+, "\w+", '
                 r'"[^"]*", "([^"]*)", ')
DEF = re.compile(r"ParseFunc (parseFunc\d*) = delegate\(.*?return p\.(Parse\w+PropertyValue)\(", re.S)
INLINE = re.compile(r"p\.(Parse\w+PropertyValue)\(")


def hosts_from(object_parser: str) -> list[tuple[str, str, str, str]]:
    # parseFuncN is re-declared in every method: resolve to the nearest preceding definition.
    defs = [(m.start(), m.group(1), m.group(2)) for m in DEF.finditer(object_parser)]
    rows = []
    for m in ADD.finditer(object_parser):
        name, value_kind = m.group(1), m.group(2)
        end = object_parser.index("));", m.end())
        rest = object_parser[m.end():end]
        host = re.findall(r'isRequired: (?:false|true), \w+, "(\w+)"', rest)
        f = re.match(r"(parseFunc\d*),", rest)
        if f:
            cands = [d for pos, n, d in defs if n == f.group(1) and pos < m.start()]
            delegate = cands[-1] if cands else None
        else:
            inline = INLINE.search(rest) if rest.startswith("delegate(") else None
            delegate = inline.group(1) if inline else None
        if not host or not delegate:
            raise SystemExit(f"unparsed row {name}: {rest[:160]}")
        # The string is the host SET sharing this registration, joined by '_' (the same
        # "Field_PageField" string sits in GetFieldProperties and GetPageFieldProperties).
        rows.extend((name, h, value_kind, delegate) for h in host[0].split("_"))
    n = object_parser.count('instance.Add("')
    if len({(r[0], r[2], r[3]) for r in rows}) == 0 or sum(1 for _ in ADD.finditer(object_parser)) != n:
        raise SystemExit(f"matched {sum(1 for _ in ADD.finditer(object_parser))} of {n} instance.Add calls")
    return sorted(set(rows))


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
