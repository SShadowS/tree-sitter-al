# B6 audit record (Task 6)

Branch `fix/b6-expression-statement` at `9dbf281`, measured 2026-10-06. Baselines:
`.snapshots/baseline-b6-{bc,dc,bc28,bcapps}`. Libraries built with clang-cl (the default).

## Step 1: incremental contract

`tools/config_oracle/tests/test_expression_statement_incremental.py`, 13 edits across the
statement/expression fork, the torn `#if` continuation and the `and(C)` reserved word.

```
./tools/ts-lock.sh python -m pytest tools/config_oracle/tests/test_expression_statement_incremental.py -q
13 passed
```

## Step 2: the `prec(-1)` audit

Comparison grammar: in `_expression_statement` the `prec(-1, …)` layer was removed and the
`reserved('code_names', choice(...))` body kept unchanged; `[$._expression_statement, $._expression]`
was added to `conflicts`. Generate then demanded one more entry, which was added as named:

```
Unresolved conflict ... preproc_if identifier • preproc_open
  1: (_expression_statement identifier)   2: (_single_pattern identifier)
  Add a conflict for these rules: `_expression_statement`, `_single_pattern`
```

With both entries generate succeeded. STATE_COUNT 23,215 (HEAD 23,213), LARGE_STATE_COUNT
7,450 (HEAD 7,448).

Verify loop against the same baselines:

| corpus | HEAD (`prec(-1)`) | conflict build |
|---|---|---|
| bc | VERIFIED | 381 files changed, 5,590 hunks |
| dc | VERIFIED | 10 files changed, 2,019 hunks |
| bc28 | VERIFIED | 405 files changed, 6,062 hunks |
| bcapps | 2 files changed | 979 files changed, 15,228 hunks |

Fixture suite: HEAD 2241/2241; conflict build 2240/2241, failing
`End as variable name in various contexts` (`test/corpus/end_identifier_edge_cases_test.txt`).

**Verdict: the trees are NOT identical. `prec(-1)` is load-bearing; the spec's expectation
(it only resolves an ambiguity no valid input needs) is wrong.** The difference is one
mechanism. A statement needs no separator before the next one in the block, and a
`list_literal` can start a statement, so at `X • [` both readings survive: the subscript
`X[1] := 2;` and the two statements `X` + `[1] := 2;`. Without the precedence GLR keeps the
split. Example (DC, `CDCAdvPOApprovalTest.Codeunit.al`, line 90):

```
<  (assignment_statement [89, 8] - [89, 52]
<    left: (subscript_expression [89, 8] - [89, 20]
>  (identifier [89, 8] - [89, 17])
>  (assignment_statement [89, 17] - [89, 52]
>    left: (list_literal [89, 17] - [89, 20]
```

Classification rule, applied to every diff hunk (`NNN[,NNN]{a,c,d}NNN` header up to the
next header or `=== CHANGED`): a hunk is the subscript split when a `<` line contains
`subscript_expression` and a `>` line contains `list_literal`; otherwise it "involves ERROR"
when any of its lines contains `ERROR`; otherwise it is "other". Counts: bc 5,448 of 5,590, dc 2,019 of 2,019, bc28 5,912 of
6,062 and bcapps 14,735 of 15,228 are this subscript split. The remaining bc/bc28 hunks, and
467 in bcapps, are its consequence on the enclosing node: the end of a `for`/`if` whose body
was `X[i] := …` moves to the end of the lone `X` (`for_statement [57, 8] - [58, 51]` becomes
`[57, 8] - [58, 24]`). 26 bcapps hunks involve ERROR nodes: 36 old ERROR lines, 68 new. The
failing fixture is the same split (`EndArray[1] := …`).

The comment above the rule names only `begin X • -`. The `[` case is the larger one. The
comment should name both. That is a follow-up and is not changed here.

Restored with `git show HEAD:grammar.js > grammar.js` and `tree-sitter generate`: `git diff grammar.js src/`
empty, STATE_COUNT back to 23,213, dc VERIFIED again, fixture suite 2241/2241.

## Step 3: BCApps hunk review

```
./tools/ts-lock.sh ./tools/tree-harness.sh verify H:/Git/BCApps-29.0 .snapshots/baseline-b6-bcapps
tree-harness: 2 file(s) changed
```

bc, dc, bc28 VERIFIED in the same session. Old trees were read from the snapshot
(`trees.gz`, in `manifest.tsv` order).

`EDocumentServiceDE.PageExt.al`: the whole file is `(ERROR [7, 0] - [78, 1])` in the old
tree. The one hunk adds `(identifier [73, 52] - [73, 54])`, the `in` of
`IsParameterVisible := Rec."Document Format" in [...]`, inside the old
`(ERROR [71, 4] - [77, 36])`. The `in` token now sits under the reserved set and surfaces as
an identifier inside the error.

`ERMPurchaseReportsIII.Codeunit.al`: line 2201 lacks the `end;` of
`VerifyValueEntryItemLedgerEntry`, so the old tree reads every later procedure (2202-2703)
as statements of that one code block, with ERROR nodes throughout (first at
`[2201, 50] - [2201, 72]`). alc rejects this file. All 45 hunks lie in that region:

- 26 hunks contain an old ERROR node on their `<` side.
- 19 hunks are attribute pairs (`[RequestPageHandler]` / `[Scope('OnPrem')]` and similar),
  which the old tree read as `subscript_expression (list_literal) [call]` statements. The new
  tree wraps each in an ERROR. Each has an old ERROR on the next source line, inside the
  swallowed header of the procedure the attributes belong to. This is the narrowing working:
  a subscript is not an invocation statement.

No changed node is a valid procedure outside an old ERROR region. **Pass.**

| file | hunk | source lines | nearest old ERROR | relation |
|---|---|---|---|---|
| EDocumentServiceDE | 201a202 | 74-74 | [71, 4] - [77, 36] | inside ancestor ERROR [71, 4] - [77, 36] |
| ERMPurchaseReportsIII | 10911,10913c10911,10913 | 2204-2204 | [2203, 20] - [2203, 21] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11189,11204c11189,11212 | 2245-2245 | [2244, 115] - [2244, 121] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11213,11215c11221,11223 | 2247-2247 | [2246, 31] - [2246, 32] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11333,11345c11341,11357 | 2266-2267 | [2265, 89] - [2265, 95] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11347,11349c11359,11361 | 2268-2268 | [2267, 25] - [2267, 26] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11353,11355c11365,11367 | 2269-2269 | [2268, 22] - [2268, 23] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11568,11570c11580,11582 | 2298-2298 | [2297, 166] - [2297, 167] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11619,11625c11631,11635 | 2305-2306 | [2304, 128] - [2304, 135] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11701,11707c11711,11716 | 2322-2322 | [2321, 131] - [2321, 138] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11709,11711c11718,11720 | 2322-2322 | [2321, 174] - [2321, 175] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11714,11720c11723,11727 | 2322-2322 | [2321, 221] - [2321, 228] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11723,11729c11730,11734 | 2322-2322 | [2321, 280] - [2321, 287] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11867,11873c11872,11877 | 2351-2351 | [2350, 133] - [2350, 140] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11875,11877c11879,11881 | 2351-2351 | [2350, 176] - [2350, 177] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11880,11886c11884,11888 | 2351-2351 | [2350, 223] - [2350, 230] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 11889,11895c11891,11895 | 2351-2351 | [2350, 282] - [2350, 289] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 12375,12379c12375,12379 | 2432-2433 | [2431, 107] - [2431, 113] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 12381,12383c12381,12383 | 2434-2434 | [2433, 22] - [2433, 23] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 12386,12389c12386,12391 | 2435-2435 | [2434, 16] - [2434, 22] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 12500,12502c12502,12504 | 2454-2454 | [2453, 14] - [2453, 15] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 12553,12561c12555,12562 | 2462-2463 | [2461, 87] - [2461, 94] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 12563,12565c12564,12566 | 2464-2464 | [2463, 25] - [2463, 26] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 12569,12571c12570,12572 | 2465-2465 | [2464, 22] - [2464, 23] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 12678,12684c12679,12686 | 2481-2482 | [2482, 42] - [2482, 74] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 12711,12717c12713,12720 | 2489-2490 | [2490, 48] - [2490, 84] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 12764,12770c12767,12774 | 2500-2501 | [2501, 36] - [2501, 42] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 12783,12789c12787,12794 | 2507-2508 | [2508, 34] - [2508, 56] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 12809,12815c12814,12821 | 2514-2515 | [2515, 41] - [2515, 66] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 12827,12830c12833,12835 | 2516-2516 | [2515, 99] - [2515, 100] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 12843,12849c12848,12855 | 2522-2523 | [2523, 48] - [2523, 84] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 12877,12883c12883,12890 | 2529-2530 | [2530, 51] - [2530, 90] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 12911,12917c12918,12925 | 2536-2537 | [2537, 35] - [2537, 74] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 12945,12951c12953,12960 | 2543-2544 | [2544, 37] - [2544, 78] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 12987,12993c12996,13003 | 2551-2552 | [2552, 30] - [2552, 64] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 13081,13087c13091,13098 | 2569-2570 | [2570, 46] - [2570, 80] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 13170,13176c13181,13188 | 2587-2588 | [2588, 22] - [2588, 50] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 13204,13210c13216,13223 | 2594-2595 | [2595, 49] - [2595, 90] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 13238,13244c13251,13258 | 2601-2602 | [2602, 56] - [2602, 92] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 13289,13295c13303,13310 | 2611-2612 | [2612, 64] - [2612, 100] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 13306,13308c13321,13323 | 2615-2615 | [2614, 20] - [2614, 21] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 13312,13314c13327,13329 | 2616-2616 | [2615, 22] - [2615, 23] | old ERROR inside hunk |
| ERMPurchaseReportsIII | 13863,13869c13878,13885 | 2676-2677 | [2677, 37] - [2677, 43] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 13889,13895c13905,13912 | 2683-2684 | [2684, 36] - [2684, 76] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 13931,13937c13948,13955 | 2691-2692 | [2692, 54] - [2692, 96] | attribute pair; next ERROR on the following source line |
| ERMPurchaseReportsIII | 13965,13971c13983,13990 | 2698-2699 | [2699, 68] - [2699, 108] | attribute pair; next ERROR on the following source line |

(Source lines are 1-based; ERROR ranges are tree-sitter's 0-based rows.)

## Step 4: performance

OLD library: main `48d04e2`. Its `src/` equals this branch's base `43b157d`:

```
$ git diff --stat 48d04e2 43b157d -- src/; echo "exit=$?"
exit=0
```

(no output before `exit=0`: no file differs). It was checked out as a
throwaway worktree in the scratchpad and built with
`./tools/ts-lock.sh tree-sitter build --output old.dll <worktree>`. NEW: the same command on
this checkout. Both clang-cl; the worktree was removed afterwards.

`python -m tools.perf ab --lib-a old.dll --lib-b new.dll --corpus dc --rounds 24` refused to
time, three runs out of three: `148 files parse differently`. The only row difference
(measured over the 43 differing files outside `.dependencies`) is the `grammar_name` of the
anonymous `in` token: `in` on main, `identifier` on this branch, 114 rows. Type, spans,
fields and `has_error` agree. This comes from Task 5's `_in_token` under the `code_names`
reserved set. tree-harness does not see it because it compares the displayed tree.

The 43-file figure came from this script (`rowdiff.py`, run from the repo root with
`PYTHONPATH=. python rowdiff.py <dir holding old.dll and new.dll>`). Python's `glob` skips
dot-directories, so `.dependencies` is not covered, which is why it reports 43 and not 148.
Output: `files 43 row-count-differs 0` and `114 (('grammar_name',), 'in', 'in', 'identifier')`.

```python
import sys, json, collections, glob
from pathlib import Path
from tools.query_coverage import loader
from tools.perf import incremental
S = sys.argv[1]
pa = loader.make_parser(loader.load_language(Path(S + '/old.dll')))
pb = loader.make_parser(loader.load_language(Path(S + '/new.dll')))
kinds = collections.Counter(); nfiles = 0; other = 0
for f in glob.glob('DC/**/*.al', recursive=True):
    src = open(f, 'rb').read()
    ra, rb = incremental.rows(pa.parse(src)), incremental.rows(pb.parse(src))
    if ra == rb: continue
    nfiles += 1
    if len(ra) != len(rb): other += 1; continue
    for x, y in zip(ra, rb):
        if x != y:
            diff = tuple(incremental.ROW_FIELDS[i] for i in range(len(x)) if x[i] != y[i])
            kinds[(diff, x[1], x[2], y[2])] += 1
print('files', nfiles, 'row-count-differs', other)
for k, v in kinds.most_common(): print(v, k)
```

To time anyway, `ab` was run through this wrapper (`ab_mask_in.py`). It replaces
`ab.trees_identical` with the same comparison over `tools.perf.incremental.rows`, which has
these fields per node: depth, type, grammar_name, named, missing, extra, field, start_byte,
end_byte, start_point, end_point, has_error. The one exception: `grammar_name` is set to
`None` on rows whose type is `in` and that are anonymous. Every other field of every row is
compared as before.

```python
"""Run `python -m tools.perf ab` with ONE relaxation of its tree-identity check: the
grammar_name of the anonymous `in` token is ignored (B6 Task 5 backs it with `_in_token`,
reported as `identifier`; type, spans, fields and everything else are still compared)."""
import sys
from tools.perf import ab, incremental

def rows_masked(tree):
    return [r[:2] + (None,) + r[3:] if (r[1] == 'in' and not r[3]) else r
            for r in incremental.rows(tree)]

def trees_identical(pa, pb, files):
    return [f"{l}:{rel}" for l, rel, src in files if rows_masked(pa.parse(src)) != rows_masked(pb.parse(src))]

ab.trees_identical = trees_identical
from tools.perf.__main__ import main
sys.exit(main(['ab'] + sys.argv[1:]))
```

Run three times from the repo root, N = 1, 2, 3:

```
PYTHONPATH=. python ab_mask_in.py --lib-a old.dll --lib-b new.dll --corpus dc --rounds 24 --out abmN
```

The tree check passed on all 1,352 files. Everything else (pinning to CPU 2, ABBA order,
warm-up, bootstrap CI) is `ab` unchanged.
The machine was busy in all three runs: outside-CPU mean 8.7-10.1 cores, over `ab`'s 4.5
threshold.

| run | old median, s | new median, s | time old / time new | within-run 95% CI |
|---|---|---|---|---|
| 1 | 0.789 | 0.775 | 1.017 | 1.011-1.038 |
| 2 | 0.790 | 0.773 | 1.019 | 1.013-1.038 |
| 3 | 0.794 | 0.774 | 1.014 | 0.991-1.045 |

The new library is about 1.4-1.9% faster on DC. Three runs agree on the direction. The
LARGE_STATE_COUNT +66 from Task 5 (7,382 to 7,448) does not show up as a slowdown here.

Synthetic file (scratchpad, not committed): 5,000 copies of
`X := 1\n#if A\n  + 2\n#else\n  - 3\n#endif\n  ;\n` in one procedure, 210,073 bytes.
`./tools/ts-lock.sh tree-sitter parse -q -t --lib-path <lib> --lang-name al <file>`,
interleaved:

| run | old, ms | new, ms | old / new |
|---|---|---|---|
| 1 | 142.95 | 35.34 | 4.05 |
| 2 | 140.80 | 34.75 | 4.05 |
| 3 | 157.89 | 33.98 | 4.65 |

Both libraries build byte-identical trees for this file (5,000 `assignment_statement`, no
ERROR or MISSING). On this input the narrowed library took about a quarter of the time.
**Not investigated: do not quote the ~4x as established.** It is three single-shot CLI
timings on one synthetic input, not pinned and not `ab`. No cause was measured. One
possibility is that GLR no longer keeps a statement reading of each torn continuation alive,
but that is a guess.
