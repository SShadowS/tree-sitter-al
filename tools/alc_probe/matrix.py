"""Four-way (2^n-way) alc matrix over `#if`-split AL cases.

    python -m tools.alc_probe run <case.al|dir>... [--check] [--json OUT]

For every assignment of the symbols named in the case's `#if`/`#elif` conditions,
the case is compiled twice: SPLIT (the file as written, `preprocessorSymbols` set
to the assignment) and FLAT (the oracle resolver's text for that configuration,
directives blanked, no symbols). A flat/split disagreement is MISMATCH: alc chose
different arms than tools/config_oracle/directives.py. The header format and the
exit codes are in tools/alc_probe/README.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from tools.alc_probe import core
from tools.config_oracle.directives import ResolveError, config_id, configurations, discover, resolve

EXIT_OK, EXIT_FAIL, EXIT_ENV = 0, 1, 2

_KEY = re.compile(r"//\s*(expect-mismatch|expect|runtime|source)\s*:\s*(.*?)\s*$")
_NEAR_KEY = re.compile(r"//\s*(expect|runtime|source)[\w-]*\s*:", re.I)
_RUNTIME = re.compile(r"\d+\.\d+$")
_LITERAL = re.compile(r"!?[A-Za-z_][A-Za-z0-9_]*$")


class CaseError(Exception):
    """A malformed case (header or directives). Exit 2."""


@dataclass
class Rule:
    literals: tuple            # () means `*`; else (("SYM", True), ("SYM", False)) for SYM / !SYM
    verdict: str | None = None  # ACCEPT/REJECT for expect lines, None for expect-mismatch

    def matches(self, env: frozenset) -> bool:
        return all((name in env) == want for name, want in self.literals)


@dataclass
class Case:
    path: Path
    name: str
    source: str
    runtime: str = core.DEFAULT_RUNTIME
    sources: list = field(default_factory=list)
    expects: list = field(default_factory=list)
    mismatches: list = field(default_factory=list)
    symbols: tuple = ()
    envs: list = field(default_factory=list)

    def expected(self, env: frozenset) -> str | None:
        hits = [r.verdict for r in self.expects if r.matches(env)]
        return hits[-1] if hits else None           # the last matching line wins

    def mismatch_expected(self, env: frozenset) -> bool:
        return any(r.matches(env) for r in self.mismatches)


def _literals(spec: list, line: str) -> tuple:
    if spec == ["*"]:
        return ()
    if not spec or not all(_LITERAL.match(t) for t in spec):
        raise CaseError(f"bad assignment in {line!r}: use `*` or symbols like `A !B`")
    return tuple((t.lstrip("!"), not t.startswith("!")) for t in spec)


def parse_case(path: Path, name: str, text: str, *, check: bool) -> Case:
    case = Case(path, name, text)
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("//"):
            break                                  # the header is the leading run of // lines
        m = _KEY.fullmatch(s)
        if not m:
            if _NEAR_KEY.match(s):
                raise CaseError(f"unknown header key in {s!r}")
            continue                               # prose
        key, value = m.group(1), m.group(2)
        if key == "source":
            if not value:
                raise CaseError("empty `// source:`")
            case.sources.append(value)
        elif key == "runtime":
            if not _RUNTIME.match(value):
                raise CaseError(f"bad runtime {value!r}")
            case.runtime = value
        elif key == "expect":
            words = value.split()
            if len(words) < 2 or words[-1].lower() not in ("accept", "reject"):
                raise CaseError(f"bad expect line {s!r}: `<* | SYM !SYM ...> <accept|reject>`")
            case.expects.append(Rule(_literals(words[:-1], s), words[-1].upper()))
        else:
            case.mismatches.append(Rule(_literals(value.split(), s)))
    try:
        disc = discover(text.encode("utf-8"))
    except ResolveError as e:
        raise CaseError(f"directives do not resolve: {e}") from e
    case.symbols = disc.free_symbols
    case.envs = configurations(disc)
    for rule in case.expects + case.mismatches:
        unknown = [n for n, _ in rule.literals if n not in case.symbols]
        if unknown:
            raise CaseError(f"header names {unknown}, but the case's conditions use only {list(case.symbols)}")
    if check:
        if not case.sources:
            raise CaseError("no `// source:` line")
        missing = [config_id(env, case.symbols) for env in case.envs if case.expected(env) is None]
        if missing:
            raise CaseError(f"no `// expect:` covers {missing}")
    return case


def collect(paths: list) -> list:
    """(path, display name) for every .al under each argument, in a stable order."""
    found = []
    for arg in paths:
        p = Path(arg)
        if p.is_dir():
            found += [(f, f.relative_to(p).as_posix()) for f in sorted(p.rglob("*.al"))]
        elif p.is_file():
            found.append((p, p.name))
    return found


def flat_text(case: Case, env: frozenset) -> str:
    try:
        return resolve(case.source.encode("utf-8"), env).masked.decode("utf-8")
    except ResolveError as e:
        raise CaseError(f"{case.name}: resolver refused {config_id(env, case.symbols)}: {e}") from e


def _fmt(v: core.Verdict) -> str:
    codes = v.codes if v.kind == core.BROKEN else v.syntax_codes   # a BROKEN verdict is explained by its AL1xxx codes
    return v.kind + (f"({','.join(codes)})" if codes else "")


def _vd(v: core.Verdict) -> dict:
    return {"verdict": v.kind, "codes": list(v.codes), **({"detail": v.detail} if v.detail else {})}


def run(paths: list, *, check: bool, json_out: str | None, runner: core.Runner, al: str, jobs: int) -> int:
    report: dict = {"check": check}

    def finish(code: int) -> int:
        report["exit"] = code
        if json_out:
            Path(json_out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return code

    ident = core.compiler_identity(al, runner)
    report["compiler"] = ident.as_dict()
    print(f"compiler: {ident.version or '?'}  {ident.path or '?'}  sha256={ident.sha256 or '?'}")
    if ident.error:
        print(f"BROKEN environment: {ident.error}", file=sys.stderr)
        return finish(EXIT_ENV)

    files = collect(paths)
    if not files:
        print(f"no cases found under {paths}", file=sys.stderr)
        return finish(EXIT_ENV)
    try:
        cases = [parse_case(p, n, p.read_text(encoding="utf-8"), check=check) for p, n in files]
        flats = {(c.name, env): flat_text(c, env) for c in cases for env in c.envs}
    except CaseError as e:
        print(f"malformed case: {e}", file=sys.stderr)
        return finish(EXIT_ENV)

    with tempfile.TemporaryDirectory(prefix="alc-matrix-") as tmp, ThreadPoolExecutor(max_workers=jobs) as pool:
        def compile_all(items, tag):
            # items: (key, source, symbols, runtime); each compile gets its own directory
            return dict(zip([k for k, *_ in items], pool.map(
                lambda i_it: core.compile_project(Path(tmp) / f"{tag}{i_it[0]:05d}", i_it[1][1], i_it[1][2],
                                                  runtime=i_it[1][3], al=al, runner=runner), enumerate(items))))

        runtimes = sorted({c.runtime for c in cases})
        controls = compile_all([((rt, want), src, [], rt) for rt in runtimes
                                for want, src in ((core.ACCEPT, core.VALID_CONTROL), (core.REJECT, core.GARBAGE_CONTROL))], "c")
        report["controls"] = [{"runtime": rt, "expect": want, **_vd(v)} for (rt, want), v in controls.items()]
        bad = [(k, v) for k, v in controls.items() if v.kind != k[1]]
        for (rt, want), v in controls.items():
            print(f"{'ok  ' if v.kind == want else 'FAIL'} control runtime={rt} expect={want} got={_fmt(v)} {v.detail}")
        if bad:
            print("BROKEN environment: a control did not behave; no verdicts given", file=sys.stderr)
            return finish(EXIT_ENV)

        results = compile_all([((c.name, env, kind), text, sorted(env) if kind == "split" else [], c.runtime)
                               for c in cases for env in c.envs
                               for kind, text in (("split", c.source), ("flat", flats[(c.name, env)]))], "k")

    broken = [(k, v) for k, v in results.items() if v.kind == core.BROKEN]
    if broken:
        for (name, env, kind), v in broken:
            print(f"BROKEN {name} {kind} symbols={sorted(env)} {v.detail} {','.join(v.codes)}", file=sys.stderr)
        report["broken"] = [{"case": n, "symbols": sorted(e), "kind": k, **_vd(v)} for (n, e, k), v in broken]
        print("BROKEN environment: no verdicts given", file=sys.stderr)
        return finish(EXIT_ENV)

    failures = 0
    report["cases"] = []
    for c in cases:
        rows = []
        for env in c.envs:
            split, flat = results[(c.name, env, "split")], results[(c.name, env, "flat")]
            exp, mm_ok = c.expected(env), c.mismatch_expected(env)
            mismatch = split.kind != flat.kind
            if mismatch and not mm_ok:
                status = "MISMATCH"
            elif check and (split.kind != exp or (mm_ok and not mismatch)):
                status = "DIFF"
            else:
                status = "ok"
            failures += check and status != "ok"
            cid = config_id(env, c.symbols)
            print(f"{status:8} {c.name:52} {cid:24} split={_fmt(split):28} flat={_fmt(flat):28} "
                  f"expect={(exp or '-').lower()}{' +mismatch' if mm_ok else ''}")
            rows.append({"config": cid, "symbols": sorted(env), "split": _vd(split), "flat": _vd(flat),
                         "expect": exp, "mismatch_expected": mm_ok, "status": status})
        report["cases"].append({"case": c.name, "runtime": c.runtime, "source": c.sources,
                                "symbols": list(c.symbols), "results": rows})
    n = sum(len(c.envs) for c in cases)
    print(f"{len(cases)} cases, {n} assignments, {2 * n} compiles; {failures} failing")
    return finish(EXIT_FAIL if failures else EXIT_OK)


def main(argv: list | None = None, *, runner: core.Runner = core.default_runner, al: str = "al") -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.alc_probe")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="compile every case split and flat under every symbol assignment")
    r.add_argument("paths", nargs="+", help="case files or directories (searched for *.al)")
    r.add_argument("--check", action="store_true", help="exit 1 when a verdict differs from its `// expect:`")
    r.add_argument("--json", dest="json_out", help="write the full results, with the compiler identity, here")
    r.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args(argv)
    return run(args.paths, check=args.check, json_out=args.json_out, runner=runner, al=al, jobs=args.jobs)
