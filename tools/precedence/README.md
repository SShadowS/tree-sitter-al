# Operator-precedence probe rig

The acceptance instrument for every precedence and associativity relation in the AL
expression grammar. Findings live in **`docs/al-operator-precedence.md`**; this
directory is what re-derives them.

```
cases/            196 probe .al files, one construct each
alc-results.tsv   every compiler verdict, name<TAB>ACCEPT|REJECT<TAB>first error
probe.sh          compiler half — recompiles cases/ and rewrites the .tsv
render.py         parser half — renders each case as a parenthesised grouping
```

## Why it exists

Byte coverage cannot see a precedence misparse. Neither can the error count, the node
type census, or `tools/tree-harness.sh`. `a + b * c` grouped wrongly covers every byte
correctly, produces no `ERROR`, and changes no node type — which is exactly how three
of these shipped undetected until 2026-08-11 (`a171c19`, `d4e8433`, `168c5ec`).

The only ground truth is the compiler. This rig asks it.

## Running it

```bash
# compiler half — needs a directory of BC symbol packages (Base Application,
# System Application, System, Application, Business Foundation)
./tools/precedence/probe.sh /path/to/.alpackages /tmp/new-results.tsv
diff tools/precedence/alc-results.tsv /tmp/new-results.tsv

# parser half
./tools/ts-lock.sh python tools/precedence/render.py tools/precedence/cases
```

A clean `diff` means the compiler still answers as recorded. A changed row is either
a compiler change or a broken rig — check the controls first.

## The one thing that will mislead you

**A probe rig with missing symbols rejects everything and emits no diagnostics.** That
is indistinguishable from a real compile error, and it silently destroys the rig's
discriminating power: every probe "fails", so every relation appears confirmed in
whichever direction you were expecting.

`probe.sh` runs four control cases first and **refuses to continue** if they do not
come out as recorded:

| control | expected | why |
|---|---|---|
| `ctl_zero_direct` | REJECT | `1 div 0` — AL0370 fires at all |
| `ctl_zero_computed` | REJECT | `1 div (2 - 2)` — the folder evaluates |
| `ctl_nonzero` | ACCEPT | `1 div (2 - 1)` — it does not reject everything |
| `ctl_ovf` | REJECT | `2147483647 + 1` — AL0371 fires |

## Adding a probe

1. Write one construct into `cases/<name>.al`, with a `codeunit 50100 Probe`
   wrapper. One case per file — `al compile` compiles every `.al` in the project
   directory, so two cases in one run contaminate each other.
2. **Write the paired control that must flip.** A probe whose control does not flip
   is not measuring anything. This is not a formality: `AL0370` does not fold through
   `div`, and that dead instrument silently passed five probes before a control
   caught it. See `docs/al-operator-precedence.md` § "The three instruments".
3. Re-run `probe.sh` and commit the new `alc-results.tsv` row.
4. If the relation is one the grammar could get wrong, pin it in
   `test/corpus/operator_precedence_test.txt` as **shape**, not error count.

## Choosing an instrument

| you want to discriminate | use |
|---|---|
| a value difference in `+ - * mod` | `AL0370`, `1 div (E)` |
| a value difference where no zero is reachable | `AL0371` overflow |
| anything involving `div` in the folded subtree | **not** `AL0370` — it does not fold through `div` |
| `and` / `or` / `xor` grouping | `AL0175` operand-type message — nothing else can work, since every operand must be Boolean under any grouping |
| a value-neutral relation such as `-a * b` | `AL0173`/`AL0175` operand-type message |
