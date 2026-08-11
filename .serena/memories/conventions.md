# Conventions

`CLAUDE.md` and `.claude/rules/contextual-keywords.md` carry the full keyword and
property architecture. This memory records only the traps behind those rules.

## Anonymous token visibility — the mechanism behind most defects

`kw(word)` builds a `token(PATTERN)`. **tree-sitter renders anonymous *pattern* tokens
as hidden `aux_sym_*` symbols (`.visible = false`)**, unlike anonymous *string* tokens
such as `";"`, which are visible.

Consequences that have each produced a live defect:

- A named rule whose entire body is a single token **collapses into that token**, so the
  token's visibility decides the node's shape. Bare `kw('x')` → childless leaf;
  `alias(kw('x'), 'x')` → one anonymous child typed `"x"`.
- A bare `kw()` sitting directly in a `seq` produces **no node at all** — the bytes are
  lexed and dropped, and the CST is not lossless over the source. This is what made
  `begin … end` inside every `#if` block vanish.
- A `choice()` mixing `alias`ed and bare alternatives gives **one node type two shapes**,
  decided by which word the source used. Invisible to every gate: the bytes are covered
  either way, so it is not a byte gap. `object_type_keyword` and `keyword_identifier`
  are the live instances.

Therefore: **read a keyword's text from the node itself, never by descending into a
child.** That stays correct for the two external tokens, which cannot take a child.

## `kwCases()` is load-bearing — never "simplify" to `kw()`

`kw()` compiles to a case-*insensitive* regex and would claim every permutation,
stealing spellings AL uses as identifiers. Real AL declares `eNuM: Decimal;`, and `eNuM`
is deliberately absent from `enum_keyword`'s whitelist.

The `kwCases()` rules are **exactly the object-declaration keywords** — codeunit,
controladdin, dotnet, enum, enumextension, pagecustomization, pageextension,
permissionset, permissionsetextension, profileextension, reportextension, tableextension,
xmlport. Membership is a stronger check than the count because it is falsifiable by
inspection. A new entry that is not an object-declaration keyword is almost certainly
wrong (`view_keyword` was miscounted in once).

## Identifier character class lives in three places

`grammar.js`'s `identifier` token, the scanner's tables in `src/unicode_id.h`, and a
hand-written literal in `dotnet_assembly_name`. The first two share
`tools/gen-unicode-id-table.py`, which hard-codes its target sets and **fails loudly**
when `grammar.js` moves without it — that generator is the drift detector. The third
shares no generator and is a drift hazard by construction; it is safe only while no
scanner token consults it.

Target is what alc accepts: C# identifier rules. `Nl` starts; `Mn Mc Pc Cf` continue.
alc accepts `Cf` mid-identifier including U+FEFF, U+200B/C/D, U+00AD, U+2060, U+061C.
Astral and `No` are accepted deliberately though alc rejects them — parse structure,
don't validate.

## Scanner

- **Nothing matches a keyword against the live lexer.** A scan that returns false
  discards every advance and is not re-entered at the same position; a walking matcher
  leaves its matched prefix consumed on failure. That shape caused three separate live
  defects and the tool (`read_keyword_ci`) was deleted. Read each word ONCE into a
  buffer via `read_word_ci`, `mark_end`, then classify.
- Two different `#` conventions coexist: `peek_directive_ci_skip_extras` takes bare
  directive words and consumes the `#` itself; the `PREPROC_OPEN`/`CLOSE` dispatch
  advances past `#` manually. Do not mix them.
- Every lookahead must step over everything `grammar.js` declares as `extras`, comments
  included. Keep `TRANSPARENT_DIRECTIVES` in sync with the `extras` array.

## Expression grammar

AL is Pascal-derived. Measured ladder, tightest to loosest, all left-associative:
postfix > unary (`not - +`) > `* / div mod` > `+ -` > `in is` > `and` > `or xor` >
`= <> < > <= >=` > `..` > `? :`. **Comparisons bind LOOSER than `and`/`or`/`xor`** —
the opposite of C-family intuition, and getting it wrong is silent.

`..` is **not** an expression operator: it is admitted only in `_single_pattern` and
`_list_element`. Every other position is a *syntax* error in alc, not a type error.

## Optional separators absorb misparses

`repeat(seq(X, optional(SEP)))` lets two adjacent `X` stand with no separator, so a
wrong parse is accepted as an extra element instead of erroring. Confirmed live in
`_case_pattern_item`; ~9 more comma sites share the shape. Suspect this whenever a
misparse produces a clean error count.
