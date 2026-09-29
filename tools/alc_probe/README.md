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
`tools/config_oracle/directives.discover`), the case is compiled twice:

- **split**: the file as written, `preprocessorSymbols` set to the assignment;
- **flat**: `directives.resolve(...).masked` for that assignment (directive lines and
  inactive arms blanked), with no symbols.

Each compile is a fresh project directory with absolute paths, runtime 15.0 unless the
case says otherwise, and no `application`/`dependencies` keys. The compile core,
`core.py`, is shared with `tools/config_oracle/probe_alc.py`.

## Verdicts

| verdict | meaning |
|---|---|
| `ACCEPT` | the `.app` was written |
| `REJECT` | no `.app`, and at least one source diagnostic (an `ALxxxx` outside AL1xxx) |
| `BROKEN` | no `.app` and no source diagnostic, or `al` could not be run. Never counted as a REJECT |
| `MISMATCH` | split and flat disagree: alc chose different arms than our resolver |

AL1xxx is the project/manifest/package range: AL1021 is printed on every run, even
successful ones, and a broken project answers with AL1001, AL1017, AL1022, AL1039,
AL1040, AL1043 or AL1053 (measured with alc 18.0.41), not with an empty log.

Every run first compiles a valid and a garbage control for each runtime the cases use.
If the valid control is not ACCEPT, the garbage control is not REJECT, or any compile
is BROKEN, the run gives no verdicts and exits 2.

## Case header

The leading `//` lines of a case file. Other `//` lines there are prose.

```al
// Valid only with S31 undefined: the field's `{` opens inside the #if.
// expect: * accept
// expect: S31 reject
// expect-mismatch: !S31 C28
// runtime: 17.0
// source: docs/bc29-parse-gaps.md family D, commit 5b809bc
```

- `expect: <assignment> <accept|reject>`: the expected **split** verdict. `<assignment>` is
  `*` (every assignment) or symbols that must all hold, `SYM` defined and `!SYM`
  undefined. The **last** matching line wins, so put `*` first.
- `expect-mismatch: <assignment>`: flat and split are expected to disagree there. Without
  it a MISMATCH fails `--check`; with it, agreement fails `--check`.
- `runtime:` defaults to `15.0`.
- `source:` where the recorded verdict came from (a doc section or a commit). A verdict
  first recorded by this tool says `source: recorded by A2, <date>` or similar.

Under `--check` every assignment must be covered by an `expect:` and at least one
`source:` is required. A symbol in the header that no condition uses, an unknown
`expect*`/`runtime*`/`source*` key, or a directive layout the resolver refuses is a
malformed case.

**Never edit an expectation to match a new run.** A difference means the old probe or
this tool is wrong, and someone has to find out which.

## Exit codes

| code | meaning |
|---|---|
| 0 | with `--check`: everything matches; without it: the run completed |
| 1 | `--check` only: a verdict differs from its `expect:`, or an unexpected MISMATCH |
| 2 | broken environment (controls, a BROKEN compile, `al` missing), a malformed case, or no cases found |

## Tests

`tools/config_oracle/tests/test_alc_probe.py`. The fast tests fake `al`; the `slow` ones
(`python -m pytest tools/config_oracle/tests/test_alc_probe.py -m slow`) need the real
compiler and skip without it.
