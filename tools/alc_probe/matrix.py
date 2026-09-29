"""Four-way (2^n-way) alc matrix over `#if`-split AL cases.

    python -m tools.alc_probe run <case.al|dir>... [--check] [--json OUT]

For every assignment of the symbols named in the case's `#if`/`#elif` conditions,
and for every runtime the case lists, the case is compiled twice: SPLIT (the file
as written, `preprocessorSymbols` set to the assignment) and FLAT (the oracle
resolver's text for that configuration, directives blanked, no symbols). A
flat/split disagreement, in verdict or in a rejection's error codes, is MISMATCH:
alc chose different arms than tools/config_oracle/directives.py. The header format
and the exit codes are in tools/alc_probe/README.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import traceback
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
_VERDICT = re.compile(r"(?i)(accept)$|(reject)\((AL\d{4}(?:,AL\d{4})*)\)$")


class CaseError(Exception):
    """A malformed case, or a path that names no case. Exit 2."""


@dataclass(frozen=True)
class Expected:
    kind: str                  # ACCEPT | REJECT
    codes: tuple = ()          # a REJECT's exact set of .al-located error codes

    def __str__(self) -> str:
        return "accept" if self.kind == core.ACCEPT else f"reject({','.join(self.codes)})"


@dataclass
class Rule:
    literals: tuple                   # () means `*`; else (("SYM", True), ("SYM", False)) for SYM / !SYM
    expected: Expected | None = None  # None for expect-mismatch lines

    def matches(self, env: frozenset) -> bool:
        return all((name in env) == want for name, want in self.literals)


@dataclass
class Case:
    path: Path                 # resolved: the case's identity
    name: str                  # for display only
    source: str
    runtimes: tuple = (core.DEFAULT_RUNTIME,)
    sources: list = field(default_factory=list)
    expects: list = field(default_factory=list)
    mismatches: list = field(default_factory=list)
    symbols: tuple = ()
    envs: list = field(default_factory=list)

    def expected(self, env: frozenset) -> Expected | None:
        hits = [r.expected for r in self.expects if r.matches(env)]
        return hits[-1] if hits else None           # the last matching line wins

    def mismatch_expected(self, env: frozenset) -> bool:
        return any(r.matches(env) for r in self.mismatches)


def _literals(spec: list, line: str) -> tuple:
    if spec == ["*"]:
        return ()
    if not spec or not all(_LITERAL.match(t) for t in spec):
        raise CaseError(f"bad assignment in {line!r}: use `*` or symbols like `A !B`")
    return tuple((t.lstrip("!"), not t.startswith("!")) for t in spec)


def _expected(word: str, line: str) -> Expected:
    m = _VERDICT.match(word)
    if not m:
        raise CaseError(f"bad verdict in {line!r}: `accept` or `reject(AL0104,...)`, the codes required")
    if m.group(1):
        return Expected(core.ACCEPT)
    codes = m.group(3).upper().split(",")
    if len(set(codes)) != len(codes):
        raise CaseError(f"duplicate code in {line!r}")
    return Expected(core.REJECT, tuple(sorted(codes)))


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
            rts = value.replace(",", " ").split()
            if not rts or not all(_RUNTIME.match(r) for r in rts) or len(set(rts)) != len(rts):
                raise CaseError(f"bad runtime list {value!r}")
            case.runtimes = tuple(rts)
        elif key == "expect":
            words = value.split()
            if len(words) < 2:
                raise CaseError(f"bad expect line {s!r}: `<* | SYM !SYM ...> <accept | reject(ALxxxx,...)>`")
            case.expects.append(Rule(_literals(words[:-1], s), _expected(words[-1], s)))
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
    """(resolved path, display name) for every case. Names are relative to the common root."""
    found = []
    for arg in paths:
        p = Path(arg)
        if p.is_dir():
            files = sorted(p.rglob("*.al"))
            if not files:
                raise CaseError(f"{arg}: no .al files")
            found += files
        elif p.is_file():
            found.append(p)
        else:
            raise CaseError(f"{arg}: no such file or directory")
    resolved = [f.resolve() for f in found]
    dupes = sorted({str(r) for r in resolved if resolved.count(r) > 1})
    if dupes:
        raise CaseError(f"the same case named twice: {dupes}")
    root = Path(os.path.commonpath([r.parent for r in resolved]))
    return [(r, r.relative_to(root).as_posix()) for r in resolved]


def flat_text(case: Case, env: frozenset) -> str:
    try:
        return resolve(case.source.encode("utf-8"), env).masked.decode("utf-8")
    except ResolveError as e:
        raise CaseError(f"{case.name}: resolver refused {config_id(env, case.symbols)}: {e}") from e


def _fmt(v: core.Verdict) -> str:
    codes = v.codes if v.kind == core.BROKEN else v.source_codes   # BROKEN is explained by the rest
    return v.kind + (f"({','.join(codes)})" if codes else "")


def _vd(v: core.Verdict) -> dict:
    return {"verdict": v.kind, "codes": list(v.codes), "source_codes": list(v.source_codes),
            **({"detail": v.detail} if v.detail else {})}


def _differ(split: core.Verdict, flat: core.Verdict) -> bool:
    return split.kind != flat.kind or (split.kind == core.REJECT and split.source_codes != flat.source_codes)


def _meets(v: core.Verdict, exp: Expected | None) -> bool:
    return exp is not None and v.kind == exp.kind and (v.kind != core.REJECT or v.source_codes == exp.codes)


def run(paths: list, *, check: bool, json_out: str | None, runner: core.Runner, al: str, jobs: int) -> int:
    report: dict = {"check": check}

    def finish(code: int) -> int:
        report["exit"] = code
        if json_out:
            Path(json_out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return code

    ident = core.compiler_identity(al, runner)
    report["compiler"] = ident.as_dict()
    print(f"compiler: {ident.version or '?'}  {ident.path or '?'}")
    for p, h in ident.code_analysis:
        print(f"  {h}  {p}")
    if ident.error:
        print(f"BROKEN environment: {ident.error}", file=sys.stderr)
        return finish(EXIT_ENV)
    al = ident.path                                 # compile with exactly the executable identified

    try:
        cases = [parse_case(p, n, p.read_text(encoding="utf-8"), check=check) for p, n in collect(paths)]
        flats = {(c.path, env): flat_text(c, env) for c in cases for env in c.envs}
    except CaseError as e:
        print(f"malformed case: {e}", file=sys.stderr)
        return finish(EXIT_ENV)

    with tempfile.TemporaryDirectory(prefix="alc-matrix-") as tmp, ThreadPoolExecutor(max_workers=jobs) as pool:
        def compile_all(items, tag):
            # items: (key, source, symbols, runtime); each compile gets its own directory
            return dict(zip([k for k, *_ in items], pool.map(
                lambda i_it: core.compile_project(Path(tmp) / f"{tag}{i_it[0]:05d}", i_it[1][1], i_it[1][2],
                                                  runtime=i_it[1][3], al=al, runner=runner), enumerate(items))))

        runtimes = sorted({rt for c in cases for rt in c.runtimes})
        controls = compile_all([((rt, want), src, [], rt) for rt in runtimes
                                for want, src in ((core.ACCEPT, core.VALID_CONTROL), (core.REJECT, core.GARBAGE_CONTROL))], "c")
        report["controls"] = [{"runtime": rt, "expect": want, **_vd(v)} for (rt, want), v in controls.items()]
        bad = [(k, v) for k, v in controls.items() if v.kind != k[1]]
        for (rt, want), v in controls.items():
            print(f"{'ok  ' if v.kind == want else 'FAIL'} control runtime={rt} expect={want} got={_fmt(v)} {v.detail}")
        if bad:
            print("BROKEN environment: a control did not behave; no verdicts given", file=sys.stderr)
            return finish(EXIT_ENV)

        results = compile_all([((c.path, env, rt, kind), text, sorted(env) if kind == "split" else [], rt)
                               for c in cases for env in c.envs for rt in c.runtimes
                               for kind, text in (("split", c.source), ("flat", flats[(c.path, env)]))], "k")

    broken = [(k, v) for k, v in results.items() if v.kind == core.BROKEN]
    if broken:
        names = {c.path: c.name for c in cases}
        for (path, env, rt, kind), v in broken:
            print(f"BROKEN {names[path]} {kind} runtime={rt} symbols={sorted(env)} {_fmt(v)} {v.detail}",
                  file=sys.stderr)
        report["broken"] = [{"case": names[p], "symbols": sorted(e), "runtime": rt, "kind": k, **_vd(v)}
                            for (p, e, rt, k), v in broken]
        print("BROKEN environment: no verdicts given", file=sys.stderr)
        return finish(EXIT_ENV)

    drift = mismatches = 0
    report["cases"] = []
    for c in cases:
        rows = []
        for env in c.envs:
            for rt in c.runtimes:
                split, flat = results[(c.path, env, rt, "split")], results[(c.path, env, rt, "flat")]
                exp, mm_ok = c.expected(env), c.mismatch_expected(env)
                mismatch = _differ(split, flat)
                if mismatch and not mm_ok:
                    status = "MISMATCH"
                    mismatches += 1
                elif check and (not _meets(split, exp) or (mm_ok and not mismatch)):
                    status = "DIFF"
                    drift += 1
                else:
                    status = "ok"
                cid = config_id(env, c.symbols)
                print(f"{status:8} {c.name:52} {cid:24} rt={rt:5} split={_fmt(split):28} flat={_fmt(flat):28} "
                      f"expect={exp or '-'}{' +mismatch' if mm_ok else ''}")
                rows.append({"config": cid, "symbols": sorted(env), "runtime": rt, "split": _vd(split),
                             "flat": _vd(flat), "expect": str(exp) if exp else None,
                             "mismatch_expected": mm_ok, "status": status})
        report["cases"].append({"case": c.name, "path": str(c.path), "runtimes": list(c.runtimes),
                                "source": c.sources, "symbols": list(c.symbols), "results": rows})
    n = sum(len(c.envs) * len(c.runtimes) for c in cases)
    print(f"{len(cases)} cases, {n} assignment-runtime pairs, {2 * n} compiles; "
          f"{mismatches} unexpected MISMATCH, {drift} drifted from expect")
    return finish(EXIT_FAIL if mismatches or drift else EXIT_OK)


def main(argv: list | None = None, *, runner: core.Runner = core.default_runner, al: str = "al") -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.alc_probe")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="compile every case split and flat under every symbol assignment")
    r.add_argument("paths", nargs="+", help="case files or directories (searched for *.al)")
    r.add_argument("--check", action="store_true", help="exit 1 when a verdict differs from its `// expect:`")
    r.add_argument("--json", dest="json_out", help="write the full results, with the compiler identity, here")
    r.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args(argv)
    try:
        return run(args.paths, check=args.check, json_out=args.json_out, runner=runner, al=al, jobs=args.jobs)
    except Exception:                               # a crash is an environment problem, never "drift" (1)
        traceback.print_exc()
        print("BROKEN environment: the run crashed; no verdicts given", file=sys.stderr)
        return EXIT_ENV
