# B7b-1d: conditional label and caption tails (deferred item 46, row B7b-1d)

Date: 2026-11-10. Branch `batch6/item46d`. Parent: B7b-1 spec
(`2026-10-07-b7b-1-strict-conditional-lists-design.md`).

## 1. Scope

The comma-led attribute tail of a text value, with a `#if` group at any separator:

| B7a family | sites | keys | hosts |
|---|---|---|---|
| `label-attributes` | report `label_declaration` (`L = 'a', Locked = true;`) | `occ:label_declaration:3.0.0` | labels_body, preproc_conditional_labels |
| `label-attributes` | label variable (`L: Label 'a', Locked = true;`) | `occ:variable_declaration:0.0.4.*` | var_body, preproc_conditional_var, preproc_split_var_section_tail |
| `caption-subfields` | `caption_value` (`Caption = 'a', Locked = true;`) | `occ:caption_value:0.1.*` | property directly and every whole-value-arm route |

Placements converted, every one in the matrix for both families (B7a generator names): adjacent-compl, adjacent-indep,
both-in-arm, count-differs, elif, empty, sep-after, sep-before, sep-before-end, sep-only, nested, trail, holes-mid,
holes-trail. For labels also the text-bearing shapes: one-elem, empty-list, holes-lead (the text is positional, so a
group holding the text is a `#if` at the VALUE slot, not a separator). Caption's one-elem and empty-list already parse
as whole-value property groups and stay there; caption's holes-lead is a group holding only `,` before the text, valid
only inactive (see section 5).

alc's verdict per cell is the committed B7a evidence (`tools/alc_probe/cases/b7-audit/label-attributes__*`,
`caption-subfields__*`); a MIXED cell (holes-*, empty-list) has a configuration alc rejects, which stays invalid.

Two placements of neighbouring families flip as a side effect: `label-declaration / empty` (all 6 cells) and the Label arm's
9 of the 36 `var-declaration / empty` cells (`L: Label 'a' #if X #endif ;`, key `occ:variable_declaration:0.0.5`). The other 27 `var-declaration / empty` cells (TextConst arm, name list, regular variable) stay GAP; the witness
is re-seated on `occ:variable_declaration:1.0.4` (TextConst).

## 2. Why the generator fits, and where it does not

The tail is a strict list `item (, item)*` whose first item is the text: `strictListBody` with the first item fixed.
So the hosts keep `value ... , item ...` and take the generator's `_e`/`_t`/`_b`/`_r` for everything after the text
(`labelCommaTail`, `caption_value`). Items are heterogeneous (a `name = value` run of three nodes for a report label
and a caption sub-field), so an item is a `seq`, which the generator already allows (`atom($)` is any rule). The
tree-side `Family` of `conditional_lists.FAMILIES` is NOT used: it needs one item per node (its region check counts
nodes); these families register an ordinary `branch-select` contract with policy `strict-list` and the flat comparison
judges the spliced region.

The text-bearing `#if` groups (one-elem/empty-list/holes-lead, labels only): at the value slot, a group holding the
text (`_F_hw`, witnessed: some arm holds the text, the others `text tail`, `,` or nothing), or a text-less group
directly BEFORE the text (`_F_h`, arms `,` or nothing). A text-less group alone is not offered: the Label-variable arm
takes any `basic_type`, so `A: Integer #if X #endif ;` would become a text-less label (item 44 aside, that is a wrong
tree, measured as a new B7a SILENT). Both have the family's group kind, so `value` is on the group where the text sits
in an arm (field `value` on `preproc_conditional_report_label_attributes` / `preproc_conditional_label_attributes`).

## 3. Tree shape

On input that parsed before, the production corpora are byte-identical (main vs branch), but generated input is not:
a caption-shaped value with a trailing comma then an `#if` group changes shape (tree correction; breaking; flagged in
CHANGELOG [Unreleased], measured over 311,220 generated caption inputs plus every changed form across 11 hosts and six generic property names, 0 regressions):

| shape (`P` any generic property name; `G`/`G1`/`E` are groups, arms below) | main | branch |
|---|---|---|
| `P = 'a', G ;`, one group `G`, every arm empty or comments/`#region`/`#pragma` | `value: (option_member_list (option_member (string_literal)) (preproc_conditional_option_members ...))` when another member of the body follows the property; `value: (caption_value (string_literal))` + sibling `preproc_conditional_property_value` when the property is the last member | always `value: (caption_value (string_literal))` + sibling `preproc_conditional_property_value` |
| `P = 'a', G1 [E ...] ;`, `G1` arms empty or a lone `,` (at least one `,`), then 0..2 all-empty groups `E` (tail `,;` without `E`: same change) | `value: (option_member_list (option_member (string_literal)) (preproc_conditional_option_members ...))` for `G1`, every host | `value: (caption_value (string_literal) (preproc_conditional_caption_subfields ...))`, each `E` a sibling `preproc_conditional_property_value` |

Both hold at the direct property, inside a `#if` around the whole property and inside a whole-value arm. Arm forms measured:
`#if`, `#if`/`#else`, `#if`/`#elif`[/`#else`]; nested groups do not change. Not changed: a verbatim text, two or more
all-empty groups, other arm content (`,\n,`, `B`, `'b'`, ...), keyed names (`CaptionML`, `OptionMembers`, `TableRelation`,
`CalcFormula`, `SubPageLink`). alc: the first row accepts every configuration; the second accepts the configuration with
the `,`-arm inactive and rejects the `,`-active one (AL0107), and its `,;`-tail variant is rejected in every configuration
(probes `tools/alc_probe/cases/b7b1d/caption_trailing_comma_*.al`). The oracle reports a discrepancy on main for the valid
configurations and passes the new tree; on the second row's rejected configuration the branch reports a discrepancy
(flat `'a',,;` is `option_member_list`), which is why that row is pinned in pytest, not the corpus.

`A: Integer #if X 'a', Locked = true #endif ;`: the text-bearing value-slot group is offered on any `basic_type`
(section 2 excludes only the text-less form), so this over-acceptance parses with a label-attribute group; X=0 (flat
`A: Integer;`) gets a `discrepancy`. Recorded as deferred item 88.

New nodes (only):

- `preproc_conditional_caption_subfields`: arms hold `,`, `property_name`, `=`, a value, nested groups. Child of `caption_value`.
- `preproc_conditional_label_attributes`: arms hold `,`, `label_attribute`, `value:` text, nested groups. Child of `variable_declaration`.
- `preproc_conditional_report_label_attributes`: arms hold `,`, the attribute triples (`comment_keyword = comment:`, `locked_keyword = locked:`, `maxlength_keyword = maxlength:`), `value:` text, nested groups. Child of `label_declaration`.

Node-types change: `label_declaration.value` becomes optional (the text can sit in a group; flagged with the breaking
shapes above); the three group kinds are new; the host children lists gain the group.

**Unwrap.** Flat `Caption = 'a';` is a bare `string_literal`. A configuration whose sub-field groups select nothing gives
the oracle a `caption_value` with one child: the rewrite `caption-value-unwrap` replaces it by the text (`engine._lower_ordinary`).

## 4. Conflicts and dynamic precedence

Label hosts: none. Caption: a string then `#if` is a real fork (a sub-field group, or the value with a sibling
`preproc_conditional_property_value`, an expression tail, an option member), decided by the arm content, so GLR.

The caption's own rules: a witnessed group (never all-empty, `witnessConditional`) with `prec.dynamic(-1)`; an all-empty
group is the list's only when more of the list follows it (`emptyNeverLast` in `strictConditionalList`), so a trailing
empty group stays the property's sibling (`Caption = 'a' #if X #endif ;` keeps main's tree; `Caption = 'a', #if X #endif ;`
is a sibling group too, the shape change of section 3). `caption_value` is no longer `prec.right`: a right associativity on
the reduce silently removes the reduce at `'a', • #if` (generator: no conflict reported), killing the sibling reading. The
whole `caption_value` carries `prec.dynamic(1)`, so a caption reading beats `option_member_list` when both complete
(`'a', #if X #endif ;`, `'a', #if X , #endif ;`).

Conflicts: `[_property_value, caption_value, option_member, _literal_value]`, the three-symbol verbatim one,
`[_caption_subfields_w_g, _caption_subfields_e_g]`, `[_caption_subfields_t]`, `[_caption_subfields_e]`, `[caption_value]`.
`perf ab` was NOT run: the host stayed overloaded and the owner skipped it for this batch. The speed measurement
`docs/agent-brief-rules.md` asks for when a change adds a `conflicts` entry or a `prec.dynamic` is still owed. One 8-round DC
screen on -O2 builds at load 2-3 during review (not a gate): time A/B median 0.995, CI 0.967-1.020, no slowdown visible,
below that run's resolution.

## 5. Out (recorded)

- Caption holes-lead (`Caption = #if X , #endif 'a', Locked = true;`, 72 MIXED cells: X=0 valid, X=1 rejected): needs a
  group before the text inside `caption_value`, at a value slot shared with the whole-value groups, for a shape that is
  only valid when the group is inactive. Deferred item 86.
- A `;` inside a tail arm (`'a' #if X , Locked = true; #else ; #endif`, alc accepts both configurations): the keyed-family
  terminator debt, not a separator placement. Deferred item 87 for the caption; the label hosts' counterparts are the
  existing `label-declaration` / `var-declaration` GAP families. Stays an ERROR on both.
- Over-acceptance of forms invalid in every configuration (`'a' #if X Locked = true #endif`, no separator): item 44.
- `A: Integer #if X 'a', Locked = true #endif ;` (X=0 valid, flat `A: Integer;`) parses with a label group on a bare
  `basic_type`, tree differs from flat: item 88.

## 6. Gates and pins

`test/corpus/strict_conditional_label_caption_tails_test.txt` (witnesses converted, preservation and shape-change cases;
one case per placement for the caption (14) and the report label (17); the label variable has only sep-before-end, nested,
trail, holes-trail, one-elem, empty and two trailing-comma cases (8), its other placements are pinned by the B7a cell
assertions alone). Oracle: contracts + `caption-value-unwrap`; `traversal/policy.json`. B7a: equiv registry rows for
the new census keys (arm separators, the `,` after a head group, a value-slot group's arms); a full `run`; cell
assertion rows (`assertions.tsv`, `strict_list_assertions --family tail`, a hole-text model). Trees: full harness
verify (all four corpora unchanged), `perf delta`.
