# alc_probe: the four-way (2^n-way) compile matrix

Runs `al compile` over `#if`-split AL cases and says whether the compiler accepts each
configuration. It automates the rule in `docs/deferred-work.md`, "The instrument these
items depend on": alc does not parse inactive branches, so a `#if` probe means nothing
until it has been compiled split and flat, with each symbol defined and undefined.

```bash
python -m tools.alc_probe run tools/alc_probe/cases --check          # the recorded verdicts
python -m tools.alc_probe run my_probe.al                            # ad hoc: print what alc says
python -m tools.alc_probe run tools/alc_probe/cases --json out.json  # full results + compiler identity
```

For every assignment of the symbols in the case's `#if`/`#elif` conditions (found by
`tools/config_oracle/directives.discover`), and for every runtime the case lists, the
case is compiled twice:

- **split**: the file as written, `preprocessorSymbols` set to the assignment;
- **flat**: `directives.resolve(...).masked` for that assignment (directive lines and
  inactive arms blanked), with no symbols.

Each compile is a fresh project directory with absolute paths, and no
`application`/`dependencies` keys. The compile core, `core.py`, is shared with
`tools/config_oracle/probe_alc.py`. Compiles run the exact executable the identity
names; the identity records `al --version`, that executable (for a dotnet tool, a
launcher shim) and the sha256 of every `Microsoft.Dynamics.Nav.CodeAnalysis.dll` of
that version.

## Verdicts

A verdict is judged by whether the `.app` was written and by **where** each error is
located, never by its number:

| verdict | meaning |
|---|---|
| `ACCEPT` | the `.app` was written |
| `REJECT` | no `.app`, and at least one error located in a `.al` file: `...\Test.al(7,15): error AL1073` |
| `BROKEN` | no `.app`, and every error located in `app.json` (`...\app.json(1,175): error AL1043`) or unlocated (`error AL1021`, `error AL1028`); or no errors at all; or `al` could not be run. Never counted as a REJECT |
| `MISMATCH` | split and flat disagree, in verdict or in a rejection's `.al`-located codes: alc chose different arms than our resolver |

AL1021 is printed, unlocated, on every run, successful ones included. AL1073 (a
procedure named like a declared trigger) is in the AL1xxx range but located in the
source, so it is a REJECT (`cases/alc-classification/`).

**Cases must be self-contained.** A reference to a Base/System Application object
without symbol packages fails with a `.al`-located AL0185, which is a REJECT by every
rule, and the controls cannot catch it because they reference nothing.

Every run first compiles a valid and a garbage control for each runtime the cases use.
If the valid control is not ACCEPT, the garbage control is not REJECT, or any compile
is BROKEN, the run gives no verdicts and exits 2.

## Case header

The leading `//` lines of a case file. Other `//` lines there are prose.

```al
// Valid only with S31 undefined: the field's `{` opens inside the #if.
// expect: * accept
// expect: S31 reject(AL0104,AL0198)
// expect-mismatch: !S31 C28
// runtime: 15.0 17.0 18.0
// source: docs/bc29-parse-gaps.md family D, commit 5b809bc
```

- `expect: <assignment> <accept | reject(ALxxxx,...)>`: the expected **split** verdict.
  `<assignment>` is `*` (every assignment) or symbols that must all hold, `SYM` defined
  and `!SYM` undefined. The **last** matching line wins, so put `*` first. A `reject`
  must list its codes, comma-separated with no spaces, and `--check` fails unless the
  `.al`-located codes are exactly that set: a control that starts rejecting for another
  reason is drift, not a pass.
- `expect-mismatch: <assignment>`: flat and split are expected to disagree there. Without
  it a MISMATCH fails the run; with it, agreement fails `--check`.
- `runtime:` one or more runtimes, space or comma separated; default `15.0`. Every
  assignment runs once per runtime, against the same expectation.
- `source:` where the recorded verdict came from (a doc section or a commit). A verdict
  or code first recorded by this tool says `recorded by A2, <date>`.

Under `--check` every assignment must be covered by an `expect:` and at least one
`source:` is required. A symbol in the header that no condition uses, a malformed
verdict or code list, an unknown `expect*`/`runtime*`/`source*` key, or a directive
layout the resolver refuses is a malformed case.

Cases are identified by their resolved path; they are displayed relative to the common
root of all the cases in the run, so `a/x.al` and `b/x.al` are two cases. Naming the
same file twice is an error.

**Never edit an expectation to match a new run.** A difference means the old probe or
this tool is wrong, and someone has to find out which.

## Exit codes

| code | meaning |
|---|---|
| 0 | every row matched (with `--check`), or the run completed with no unexpected MISMATCH |
| 1 | an unexpected MISMATCH (always), or a verdict/code differing from its `expect:` (`--check`) |
| 2 | broken environment (controls, a BROKEN compile, `al` missing, a crash), a malformed case, a path that does not exist or holds no `.al`, or the same case named twice |

## Tests

`tools/config_oracle/tests/test_alc_probe.py`, run in CI. The fast tests fake `al` with
diagnostic lines captured from alc 18.0.41; the `slow` ones
(`python -m pytest tools/config_oracle/tests/test_alc_probe.py -m slow`) need the real
compiler and skip without it.
