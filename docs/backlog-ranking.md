# Backlog ranking (2026-11-08)

A ranking of every open item in [`deferred-work.md`](deferred-work.md) for the project goal: **the best parsed
AST for al-sem** ("I would prefer the parser doesn't get slower or bigger, but correctness is our goal"). Produced
after the v4.6.0 release by an independent read of each item's full body (Fable), with four read-only corpus greps
(items 28, 68, 69, 70: 0 production sites each). No builds, tests or alc probes were run for it, so every score is
a judgement from the item texts. Item numbers are `deferred-work.md` items; this file does not replace them.

**Scales (1-5).** P = value for the goal (5 = silent wrong tree al-sem would consume in real code; 1 = cosmetic or
audit-only); production impact counts heavily. D = effort and design uncertainty (5 = needs its own spec, recorded
failed attempts, or a grammar-wide conflict class). R = blast radius (5 = shared statement/expression machinery or
the scanner's core dispatch). Order: P descending, then D+R ascending, with the deviations stated below the table.

## Ranked table

| # | item | short title | P | D | R | reason |
|---|---|---|---|---|---|---|
| 1 | 43 | `; else` / `Bar #if X ; #endif else Baz` reads `else` as a call | 4 | 2 | 3 | Silent wrong tree on a VALID split input (X=0); 0 sites. The recorded blocker (reserving `else` changed 6 cells where `end`/`end else` were misread as calls) is probably gone since #41 killed that call reading (inferred from item 69, not measured). |
| 2 | 37 | Conditional value fragments / key `OptionMembers` by name (B13) | 3 | 3 | 3 | Valid AL ERRORs in 10 pinned shapes plus bare-`;` ML arms; option-members is the one list family with real sites; keying `OptionMembers` is a sixth instance of a done pattern and also closes 38, 65 and B7b-1e of 46. |
| 3 | 22 | `case_else_branch` has two shapes | 3 | 2 | 2 | Real sites (2 under `preproc_conditional_case`, 1,468 beside `case_body` in BC.History). A tree-shape decision (B10): a field, or pin both shapes; moving 1,468 nodes is the costly option. |
| 4 | 46 | Remaining list families B7b-1b..g | 3 | 4 | 3 | Thousands of GAP cells of valid AL; recipe exists (`strictConditionalList`, Host Conversion Procedure). Start with 1b parameter-list (90 cells) or 1e option-members (overlaps 37). 1b done 2026-11-08 (batch 2, GAP 90 -> 0). |
| 5 | 10 | Split `add*` headers open over `#endif` (EDocumentDE) | 3 | 5 | 4 | The one item with a REAL production file that ERRORs (BCApps `EDocumentServiceDE.PageExt.al`); partial forms measured +835..+2,270 states; needs configuration-aware parsing. |
| 6 | 64 | split-if-begin GAP, 582 cells; C2 recovery loses `procedure` | 3 | 5 | 4 | Largest unowned GAP family on alc-accepted input; "needs its own spec"; split-statement / version-count class. |
| 7 | 36 | Configuration-dependent property boundaries (B12) | 3 | 5 | 4 | One-reading guesses are wrong in some configuration; 0 sites; blocked on the F1 representation decision. |
| 8 | 56 | Case-pattern slot continuations (RC6) | 3 | 5 | 3 | `1 #if X + 1 #endif :` reads `+1` as a second pattern: 106 SILENT + 2,124 GAP cells; 0 sites; needs separator tracking and C1 lowering first. |
| 9 | 57 | B7b-2 crossing forms | 3 | 5 | 4 | Mostly visible ERRORs, but `Foo(1 #if X + 2 #else , 3 #endif)` parses CLEAN and WRONG; needs a new representation. |
| 10 | 24 | F0 traversal helper residuals | 2 | 2 | 1 | `shared` misreports a trailing comment on an `#endif` line; public API, "must be fixed before the next major"; mechanical in three runtimes plus doc/CHANGELOG. |
| 11 | 27 | `identifier` two shapes (`TableData` option member) | 2 | 2 | 2 | 6 real sites where an `identifier` has an anonymous child; a forbidden two-shape. |
| 12 | 71 | CLI version disagreement (^0.26.7 / 0.27.0 / 0.27.2) | 2 | 2 | 2 | Gate stability; move the generator deliberately with the tree harness proving identical trees. |
| 13 | 72 | `parser.c` 63.6 MiB vs 100 MB | 2 | 2 | 2 | A decision, not a fix; +6.9% in one minor. |
| 14 | 21 | MSVC build 2x slower | 2 | 2 | 2 | Speed only, Windows consumers; remaining work is CI build config. |
| 15 | 54 | B7b-2 ~4% on DC | 2 | 3 | 2 | Speed; partly addressed by D1; re-measure with `ab` first. |
| 16 | 29 | Four `TableRelation` `#if`-in-chain shapes ERROR | 2 | 3 | 2 | Visible, alc not probed, 0 sites; isolated. |
| 17 | 59 | Traversal helper has no region API | 2 | 3 | 1 | Useful only if al-sem uses the helper rather than the C shim. |
| 18 | 23 | Permissions list ending in an arm + split procedure ERRORs | 2 | 3 | 3 | Visible, 0 sites, not traced. |
| 19 | 50 | `;` group beside a split case end branch has no slot | 2 | 3 | 3 | Visible, 48 cells, 0 sites. |
| 20 | 69 | Bare `end` without `;` in both arms ERRORs | 2 | 3 | 4 | Visible, 12 cells, 0 sites; was silent before #41, now loud. Scanner token variant. |
| 21 | 63 | Incremental reparse differs from fresh (2 valid inputs) | 2 | 3 | 4 | Editors only: al-sem parses fresh through `al_shim_parse_utf8`. |
| 22 | 45 | Four variable-attribute group shapes ERROR | 2 | 3 | 4 | Visible, 0 sites; `VAR_ATTRIBUTE_OPEN` design decision. |
| 23 | 48 | Configuration-independent orphan `;` around empty groups | 2 | 3 | 5 | 18 SILENT cells, semantically empty, 0 sites; touches `_statement`. |
| 24 | 49 | B7b-3 cells deferred by host limitation | 2 | 4 | 1 | Mostly oracle lowering for split hosts. |
| 25 | 51 | `in` prefix arm with a continuation (shape 3) | 2 | 4 | 3 | Visible, 0 sites; a precedence change was measured and reverted. |
| 26 | 47 | Six case shapes alc accepts still ERROR | 2 | 4 | 3 | Visible, 0 sites, each needs an owner decision. |
| 27 | 68 | Split `end;` after statements in the FIRST arm ERRORs | 2 | 4 | 4 | Visible, 0 sites, alc not probed; version-count class. |
| 28 | 26 | Directive after code on the same line parses clean | 2 | 4 | 5 | Over-acceptance (AL0620), 0 sites; needs new scanner line state. |
| 29 | 58 | `in`'s right takes a non-list arm | 1 | 2 | 2 | Over-acceptance; costed (+209 states), D1 made room. |
| 30 | 65 | Comma-less group-then-member reads as option list | 1 | 2 | 2 | Over-acceptance; falls out of item 37. |
| 31 | 30 | Trailing comma in a link list accepted | 1 | 2 | 2 | Over-acceptance, 0 sites. |
| 32 | 28 | `Visible = Where;` ERRORs | 1 | 2 | 2 | 0 sites, alc not probed; probe first. |
| 33 | 70 | No working alc probe for `profileextension` | 1 | 2 | 1 | 0 qualified sites; a probe-rig question. |
| 34 | 6 | Doubled UTF-8 BOM, 3 bytes | 1 | 1 | 1 | One file outside the four corpora; one alc probe decides it. |
| 35 | 42 | 117 UNCHECKED matrix cells | 1 | 2 | 1 | Audit debt. |
| 36 | 60 | 231 property-value cells in no manifest | 1 | 2 | 1 | Audit debt. |
| 37 | 38 | All-comma `OptionMembers` run reads as permissions list | 1 | 1 | 1 | Invalid in every configuration; resolved by item 37. |
| 38 | 44 | B7b-1 over-acceptances | 1 | 4 | 4 | The oracle already flags each; "only if a consumer needs it". |
| 39 | 55 | Oracle does not check grouping in a region | 1 | 3 | 1 | Contract by design; "none open". |
| 40 | 52 | Quadratic consecutive-group runs | 1 | 4 | 4 | User-decided known limit; longest real run is 3. |
| 41 | 53 | Quadratic ternary-chain tails | 1 | 4 | 3 | Decided known limit. |
| — | 1 | Separator positions: B7a index | 2 | 5 | 4 | Not a work item: an index to the matrix and to items 36/37/38/44/45/46. |
| — | 2 | A rule existing ≠ shape covered | 1 | 1 | 1 | A principle, "resolved into item 1"; close. |

Deviations from pure order: 22 above 46/10/64 (real sites and cheap); 24 leads the P2 block (release-gating,
mechanical); 58 leads the P1 block (already costed).

## Cleanup suggested by the ranking

- Items 1 and 2 are an index and a principle, not work: rewrite 1 as a pointer paragraph, close 2.
- Items 38 and 65 are consequences of `OptionMembers` not being keyed: fold into item 37.
- Items 52, 53, 55 are recorded decisions: move to a "measured known limits" section.
- Items 42 and 60 are the same kind of audit debt: merge.
- Item 49 is mostly an oracle-lowering roadmap row: re-home its grammar parts to 48, 50, 64.
- Item 21's remaining actions are release-pipeline work.
- Item 6: probe and close either way. Item 44: ask al-sem once whether the oracle's flagging is enough.
- Item 63 belongs to the editor (D2) track, not the al-sem track.
- Item 43's recorded blocker should be re-verified before it is treated as still true.

## A gap found by the ranking

The B7a matrix's top-ranked SILENT family, **`integer-list`** (9 cells, representative
`occ:signed_integer_list:0.0.1.0.0@declaration_body#sep-after`), has no deferred item of its own. Its "6" in the
matrix is the number of production sites of the same shape class (`preproc_conditional_option_members/sep-after`),
not 6 confirmed wrong trees in production; that needs triage. Logged as item 73.

## Execution batches

Worked in batches of independent items, each item in its own worktree (see the batch log at the end of this file).

Mechanics: each item runs in its own git worktree with `TREE_SITTER_LIBDIR` and `TS_LOCK_DIR` pointed inside it (the
CLI caches the compiled parser by grammar name, so without them parallel worktrees overwrite one another's `al.so`;
`TREE_SITTER_LIBDIR` was verified to redirect it), the corpora symlinked, and the B7a alc cache hard-linked (`cp -al`)
so a worktree's B7a run is warm. An independent reviewer per item tries to refute the implementer's report. Branches are
merged and the gates re-run on the combined tree by the controller, never by the agents.

### Batch 1 (2026-11-08)

| item | result | review | merged |
|---|---|---|---|
| 43 | `else` reserved in `code_names`: the flat orphan `else` (alc rejects) is an ERROR; the valid split form went from a silent wrong tree to an ERROR (owner accepted the trade) and is split out as item 74. STATE_COUNT +0. | approve-with-notes | yes |
| 37, 38 | `OptionMembers` keyed by name; conditional option lists parse (4,332 B7a records ERROR→clean, 0 the other way; option-members GAP 1,111→436). Flat values alc rejects change shape (listed in the CHANGELOG). STATE_COUNT +756 (+2.66%). Owner accepted on the evidence. | approve-with-notes | yes |
| 65 | Not resolved: the measured fix (+12 states) ERRORs a configuration alc accepts; reverted and recorded. | — | — |
| 73 | Triaged: 0 production sites hold the defective sequence; a fix would key `OptionOrdinalValues`. | — | — |
| 24 | `SplitInfo.shared` excludes the `#endif` line in Python, JS and Rust; docs and the 4.5.0 exports-map correction. | approve-with-notes | yes |
| 6 | alc accepts a doubled BOM; the grammar already treats U+FEFF as an extra. Closed, not a defect. | changes-needed (docs; fixed at merge) | yes |
| 28 | alc accepts `Visible = Where;`; done in batch 2. | as above | yes |
| 70 | alc accepts a qualified `profileextension` base; done in batch 2. | as above | yes |
| 44 | Asked al-sem (relayed by the owner via kraken coord, `q-20261108T212902-ba39458a`): it does not need these rejected. Recorded as a decided known limit. | — | yes |

### Batch 2 (2026-11-09)

| item | result | review | merged |
|---|---|---|---|
| 28 | `Where` at generic property value start is an `identifier` (`_value_start_keyword_name`, `prec(-1)` so `where(` stays a clause); `Visible = Where();` stays an ERROR, as alc rejects it (AL0322). STATE_COUNT +59. | approve-with-notes | yes |
| 70 | `profileextension`'s base takes a qualified name, as #36 did for the other kinds. STATE_COUNT +4. | approve-with-notes | yes |
| 27 | A `TableData` option member is a leaf `identifier` (one shared hidden rule; two inline aliases had renamed an anonymous token in 10,875 production files, measured with `perf delta` and dropped). The shape census flags 0 types. STATE_COUNT -5. | approve-with-notes | yes |
| 46b | Procedure parameter lists are a strict conditional list (new `preproc_conditional_parameters`); B7a parameter-list GAP 90 → 0. Over-accepts forms invalid in every configuration (item 44's limit). STATE_COUNT +89. | approve-with-notes | yes |

Combined: STATE_COUNT +147 (+0.5%), `parser.c` +1.2%; production trees unchanged in all four corpora.
