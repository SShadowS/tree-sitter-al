# AL operator precedence and associativity, measured

**Instrument:** `al compile` / alc **18.0.37.11445**, against real BC **28.0.46665.47126**
symbol packages (`Microsoft_Application`, `Base Application`, `System Application`,
`System`, `Business Foundation`).
**Measured:** 2026-08-11. **196 probe compiles**, one `.al` at a time.
**Rig:** `tools/precedence/` — `probe.sh` (compiler half), `render.py` (parser half),
`cases/` (every probe), `alc-results.tsv` (every verdict).

Nothing here is documentation-derived or recalled. Every relation below was put to
the compiler and the compiler's answer is recorded with the probe that produced it.

## The ladder

AL is Pascal-derived. Tightest to loosest:

| level | operators | assoc |
|---|---|---|
| 1 | `.` `[]` `()` (postfix) | left |
| 2 | `not` `-` `+` (unary) | right |
| 3 | `*` `/` `div` `mod` | left |
| 4 | `+` `-` (also string concatenation) | left |
| 5 | `in` `is` `as` | left |
| 6 | `and` | left |
| 7 | `or` `xor` | left |
| 8 | `=` `<>` `<` `>` `<=` `>=` | left |
| 9 | `..` — list-literal element / case pattern only | left |
| 10 | `? :` | right |

**The comparison operators are the LOOSEST binary operators, not the tightest.**
`a = b and c` means `a = (b and c)`. This is why Business Central code writes
`if (a = b) and (c = d) then` with parentheses that look redundant and are
load-bearing. It is the single most consequential fact in this document.

**AL has no `^` operator.** `i := 2 ^ 3;` is `AL0183: Unexpected character '^'`.

## The three instruments

Measuring a *grouping* with a compiler that will not print you a parse tree needs a
probe whose accept/reject or error text differs by grouping. Three work here.

### 1. `AL0370: Division by constant zero`

alc constant-folds, so `i := 1 div (E);` discriminates by the **value** of `E`.

**It does not fold through `div`.** `i := 8 div (2 div 4);` is `8 div 0` and compiles
clean. It does fold through `+`, `-`, `*` and `mod`. This was found by a paired
control, after it had silently passed five probes that would otherwise have read as
clean confirmations. **Any probe built on this instrument needs a parenthesised
control that must flip.**

### 2. `AL0371: The operation overflows at compile time`

A second value instrument, for relations where no zero is reachable — decimal
division never yields zero from non-zero operands, so `/` associativity needs this
one.

### 3. `AL0175` / `AL0173` operand-type messages

> `Operator 'and' cannot be applied to operands of type 'Integer' and 'Boolean'`

Names **which** operator received the mismatched pair **and in which order**. This is
the only instrument that can work for `and`/`or`/`xor`: accept/reject cannot
discriminate their grouping, because every operand must be Boolean under *every*
grouping, so a type error appears either way. It is also what makes value-neutral
relations observable — `-a * b` and `-(a * b)` are numerically identical, but the
compiler will tell you which operand the minus took.

### Rejected as instruments

All of these look like they should work and silently do not:

| candidate | why not |
|---|---|
| constant array index out of bounds | not checked; `arr: array[7]` accepts `arr[9]` |
| array dimension from an expression | `array[1+2*3]` is a syntax error |
| `Text[n]` overflow | `t: Text[3]; t := 'abcd';` accepted |
| ternary constant folding | not folded; `1 div (true ? 0 : 1)` accepted |
| duplicate `case` labels | AL0402 compares literals, does not fold `(true or false)` |
| overlapping `case` ranges | not detected |

## Measured relations

Each row names a probe in `tools/precedence/cases/`. "alc says" is the reading the
verdict forces.

### Multiplicative versus additive — `*` `/` `div` `mod` bind tighter

| probe | alc verdict | alc says |
|---|---|---|
| `1 div (1 + 2 * 0)` | ACCEPT (=1) | `1 + (2*0)` |
| `1 div ((1 + 2) * 0)` | REJECT AL0370 | control flips |
| `1 div (4 - 2 * 2)` | REJECT AL0370 (=0) | `4 - (2*2)` |
| `1 div (5 - 8 mod 3)` | ACCEPT (=3) | `5 - (8 mod 3)` |
| `1 div (6 mod 2 + 1)` | ACCEPT (=1) | `(6 mod 2) + 1` |
| `1 / (2 - 4 / 2)` | REJECT AL0370 (=0) | `2 - (4/2)` |
| `1 + b * 2` | `'*' Boolean and Integer` | `1 + (b*2)` |
| `1 * b + 2` | `'*' Integer and Boolean` | `(1*b) + 2` |
| `1 ± b div 2` | `'div' Boolean and Integer` | `1 ± (b div 2)` |
| `1 ± b mod 2` | `'mod' Boolean and Integer` | `1 ± (b mod 2)` |
| `1 ± b / 2` | `'/' Boolean and Integer` | `1 ± (b/2)` |

### Associativity — everything binary is left-associative

| probe | alc verdict | alc says |
|---|---|---|
| `1 div (8 - 4 - 4)` | REJECT AL0370 (=0) | `(8-4)-4` |
| `1 / 1e-19 / 1e-19` | REJECT AL0371 | `(1/x)/x` |
| `2147483647 + 1 - 1` | REJECT AL0371 | `(a+1)-1` |
| `8 - b - 4` | `'-' Integer and Boolean` | `(8-b)-4` |
| `8 * b * 4`, `8 / b / 4`, `8 div b div 4`, `8 mod b mod 4` | `Integer and Boolean` | left |
| `8 * b div 4`, `8 / b div 4`, `8 div b mod 4`, `8 mod b * 4` | `Integer and Boolean` | left, one level |
| `'a' + b + 'c'` | `'+' Char and Boolean` | `('a'+b)+'c'` |
| `true and 1 and true` | `'and' Boolean and Integer` | `(true and 1) and true` |
| `1 = 1 = true` | ACCEPT | `(1=1)=true` |
| `true = 1 < 2` | `'=' Boolean and Integer` | `(true=1)<2` |

### Comparison versus arithmetic — arithmetic binds tighter

`1 + 1 = 2`, `2 * 3 = 6`, `1 = 1 + 1`, `'a' + 'b' = 'ab'`, `1 + 1 < 3` — all ACCEPT.
Under the inverse grouping each becomes `1 + (1 = 2)`-shaped and fails AL0175. So
`a + b = c` does compare the sum.

### Comparison versus the logical operators — **logical binds tighter**

| probe | alc verdict | alc says |
|---|---|---|
| `1 = 1 and 2 = 2` | `'and' Integer and Integer` | `1 = (1 and 2) = 2` |
| `1 < 2 and 3 < 4` | `'and' Integer and Integer` | `1 < (2 and 3) < 4` |
| `1 < 2 or 3 < 4` | `'or' Integer and Integer` | `1 < (2 or 3) < 4` |
| `1 <> 2 xor 3 <> 4` | `'xor' Integer and Integer` | `1 <> (2 xor 3) <> 4` |
| `1 = 1 and true` | `'and' Integer and Boolean` | `1 = (1 and true)` |
| `true and 1 = 1` | `'and' Boolean and Integer` | `(true and 1) = 1` |
| `(1 = 1) and (2 = 2)` | ACCEPT | control |

`'Integer' and 'Integer'` is producible only by `1 and 2`, and the parenthesised
control compiles, so the rig discriminates rather than rejecting everything.

**The two readings are not equivalent.** With `A`, `B`, `C` all Boolean and all
`false`, `A = B and C` is **true** under the compiler and **false** under the
comparison-tighter reading.

### `and` versus `or` versus `xor` — `and` > `or` = `xor`

| probe | alc verdict | alc says |
|---|---|---|
| `true or 1 and true` | `'and' Integer and Boolean` | `true or (1 and true)` |
| `true and 1 or true` | `'and' Boolean and Integer` | `(true and 1) or true` |
| `true xor 1 and true` | `'and' Integer and Boolean` | `true xor (1 and true)` |
| `true or 1 xor true` | `'or' Boolean and Integer` | `(true or 1) xor true` |
| `true xor 1 or true` | `'xor' Boolean and Integer` | `(true xor 1) or true` |

### Unary — binds tighter than `*`, looser than postfix

| probe | alc verdict | alc says |
|---|---|---|
| `-b * 2` | `'-' on 'Boolean'` | `(-b) * 2` |
| `-b div 2`, `-b mod 2` | `'-' on 'Boolean'` | `(-b) op 2` |
| `-(b * 2)` | `'*' Boolean and Integer` | control |
| `(-b) * 2` | `'-' on 'Boolean'` | control |
| `not 2 * true` | `'not' on 'Integer'` | `(not 2) * true` |
| `1 div (-2 + 2)` | REJECT AL0370 (=0) | `(-2) + 2` |
| `-arr[1]` (`arr: array[10] of Boolean`) | `'-' on 'Boolean'` | `-(arr[1])` |
| `-BoolFn()` | `'-' on 'Boolean'` | `-(BoolFn())` |
| `not iarr[1]` (`iarr: array of Integer`) | `'not' on 'Integer'` | `not (iarr[1])` |
| `not barr[1]` (Boolean array) | ACCEPT | control |

The operand type reported is the **element/return** type, so the unary applied to the
postfix *result*; had the unary bound tighter the operand would have been the array
or the function.

### `in`, `is`, `as` — one level, tighter than `and`, looser than `+`

| probe | alc verdict | alc says |
|---|---|---|
| `1 + 1 in [2]` | ACCEPT | `(1+1) in [2]` |
| `1 and 1 in [1]` | `'and' Integer and Boolean` | `1 and (1 in [1])` |
| `1 or 1 in [1]` | `'or' Integer and Boolean` | `1 or (1 in [1])` |
| `true = 1 in [1]` | ACCEPT | `true = (1 in [1])` |
| `1 and x is IProbeB` | `'and' Integer and Boolean` | `1 and (x is I)` |
| `1 and x as IProbeB` | `'and' Integer and **'Interface IProbeB'**` | `1 and (x as I)` |
| `x as IProbeB is IProbeB` | ACCEPT | `(x as I) is I` |
| `true = x as IProbeB is IProbeB` | ACCEPT | both tighter than `=` |

The `as` row is the decisive one: the `and`'s right operand carries the type produced
**by the cast** (`Interface IProbeB`), not `x`'s declared type (`Interface IProbeA`),
so the `as` bound first.

### `..` — not an expression operator at all

`..` is admissible in exactly **two** syntactic positions. Everywhere else it is a
**syntax** error, not a type error, which means the form has no reading in AL at all:

| probe | alc verdict |
|---|---|
| `b := 1 in [1 .. 5];` | **ACCEPT** |
| `case i of 1 .. 5:` | **ACCEPT** |
| `i := 1 .. 5;` | AL0104 Syntax error, `'end'` expected |
| `Q(1 .. 5);` | AL0104 Syntax error, `','` expected |
| `b := 1 in 1 .. 5;` | AL0104 Syntax error, `'['` expected |
| `i := (1 .. 5);` | AL0104 Syntax error, `')'` expected |
| `if 1 .. 5 then;` | AL0104 Syntax error, `'then'` expected |
| `b := arr[1 .. 5];` | AL0104 Syntax error, `','` expected |
| `exit(1 .. 5);` | AL0104 Syntax error, `')'` expected |
| `b := 1 in [1 + (1 .. 4)];` | AL0104 Syntax error, `')'` expected |

Where it *is* admissible, its operands extend maximally — it is the outermost thing
in the element or pattern:

| probe | alc verdict | alc says |
|---|---|---|
| `1 in [1 + 1 .. 4]` | ACCEPT | `(1+1) .. 4` |
| `1 in [1 * 2 .. 4]` | ACCEPT | `(1*2) .. 4` |
| `1 in [1 .. 2 = 2]` | `'..' Integer and Boolean` | `1 .. (2=2)` |
| `1 in [1 = 1 .. 2]` | `'..' Boolean and Integer` | `(1=1) .. 2` |

**A corpus census cannot establish this.** Counting where `range_expression` nodes
*are* shows only where the grammar currently puts them; a position AL accepts but the
grammar rejects would produce an `ERROR` and no range node at all, so it would be
invisible to the count. The syntax-error probes above are what turn the corpus
observation into a statement about the language.

`filter(...)` is not an exception — it has its own `filter_value` rule and never
produced a `range_expression`.

### Ternary — loosest

| probe | alc verdict | alc says |
|---|---|---|
| `1 + true ? 2 : 3` | `'+' Integer and Boolean` | `(1+true) ? 2 : 3` |
| `true and true ? 1 : 2` | ACCEPT | `(true and true) ? 1 : 2` |
| `1 = 1 ? 1 : 2` | ACCEPT | `(1=1) ? 1 : 2` |
| `1 in [1] ? 1 : 2` | ACCEPT | `(1 in [1]) ? 1 : 2` |
| `b := true ? 1 : 2 = 2` | AL0122, identical to the control `true ? 1 : (2=2)` | else-branch extends right |

The last row needs its control to read correctly: `b := true ? 1 : (2 = 2);` produces
the *same* AL0122 message, which is what identifies the unparenthesised form as the
same grouping rather than as `(true ? 1 : 2) = 2`.

## What this found in tree-sitter-al

Three relations were wrong, and every one of the misparses was **silent** — full byte
coverage, no `ERROR` node, no node type changed, and `BC.History` parsing 0 errors on
both sides of every fix.

| relation | grammar had | sites | fixed in |
|---|---|---|---|
| `..` versus `+ - *` | `..` tighter (prec 8) | 4, all meaning-changing | `a171c19` |
| unary versus `*` | tied at 7, right-assoc won | 629 in 193 files | `d4e8433` |
| comparison versus `and`/`or`/`xor` | inverted | 3 | `168c5ec` |

The before/after `(parent, field, child)` edge census recorded **13,339,003 fielded
edges on both sides with `node_types: 0 changed`** — 636 trees rewritten with no node
type changing count at all. That is why no existing gate saw them, and why
`test/corpus/operator_precedence_test.txt` asserts **shape** rather than error count.

## Re-running

```bash
# compiler half — needs a directory of BC symbol packages
./tools/precedence/probe.sh /path/to/.alpackages /tmp/new-results.tsv
diff tools/precedence/alc-results.tsv /tmp/new-results.tsv

# parser half
./tools/ts-lock.sh python tools/precedence/render.py tools/precedence/cases
```

`probe.sh` refuses to run if its four control cases do not come out as recorded. A rig
with missing symbols rejects *everything* and emits no diagnostics, which is
indistinguishable from a real compile error — the control gate is what stops that
from being read as a result.

## Still unmeasured

Small and stated rather than assumed:

- **`..` versus the logical operators and `?:`.** A range of Booleans is meaningless,
  so no probe types correctly. `..` is below comparison and comparison is below the
  logical operators, so the ladder position is implied but not measured.
- **Unary `+` specifically.** Every unary probe used `-` or `not`; `+` shares the
  rule and the level, and is assumed to share the precedence.
- **`assignment as expression`** (`asserterror x := 1` and similar) against the rest
  of the ladder.
