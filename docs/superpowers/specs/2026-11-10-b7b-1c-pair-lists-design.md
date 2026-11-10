# B7b-1c: conditional ML and Namespaces pair lists (deferred item 46, row B7b-1c)

Date: 2026-11-10. Branch `batch6/item46c`. Parent: B7b-1 spec
(`2026-10-07-b7b-1-strict-conditional-lists-design.md`).

## 1. What the family is

`ml-pairs` (GAP 825) and `namespace-pairs` (GAP 288) in the B7a matrix: a `#if` group at a `,` of an
`ENU = 'a', DAN = 'b'` list. Hosts: the keyed `CaptionML` family and `Namespaces` property values (scanner-keyed,
B4), a TextConst variable's list (`variable_declaration`).

The GAP cells split into two owners:

| cells | key | what | here |
|---|---|---|---|
| ML 465, NS 153 | `occ:ml_value_list:0.1.0.0`, `occ:namespace_value_list:0.1.0.0` (list-separator role) | a group at a pair separator | converted |
| ML 360, NS 135 | `occ:_ml_arm_t:*`, `occ:_namespaces_arm_t:*` (terminator role) | a `;` group inside a whole-value arm: `#if TPL ENU='a' #if X ; #else ; #endif #else ENU='b'; #endif` | not converted; see 5 |

`list-literal` (GAP 388, OVERACCEPT 4) needs a whole-value ownership table first (`[1, #if X ...`, whose groups an
expression region also claims). That table does not fall out of a property-value list change. Left, recorded in item 46.

## 2. Grammar

`ml_value_list` and `namespace_value_list` become `strictListBody` hosts: `strictConditionalList('ml_pairs',
ml_value_pair, ',', -1)` and `'namespace_pairs'`, group nodes `preproc_conditional_ml_pairs` and
`preproc_conditional_namespace_pairs`, arms pairs and `,` (unfielded, as `parameters`).

A generic property's value `FooML = ENU = 'x', DAN = 'y';` keeps a flat list (`_ml_value_list_flat`, aliased
`ml_value_list`): a group at a generic value is `_property_value`'s own conditional, and giving it a list group
reading would touch every property. alc rejects a pair list at a name that is not one of the 13 (AL0219,
`tools/alc_probe/cases/b7b1c/generic_pair_list.al`), so the flat rule's separators are `na` cells.

**Whole value against list.** A group that is the whole value (arms are complete lists, no comma at an arm edge,
nothing beside it) is the keyed family's whole-value group, unchanged: the list group carries `prec.dynamic(-1)`, so
where both readings complete the whole-value and sequence readings and the decorations (an empty group before or
after the value) win. A group is a list group when a comma stands at an arm's edge or a pair stands beside it.
The tie-break only works while the parser still holds both readings: from 9 consecutive empty groups after the value the
no-list reading is gone before dynamic precedence decides, and the first n-8 groups become list groups (section 3,
deferred item 91).

Conflicts added (ML; the same again for Namespaces): `[_ml_pairs_t]`, `[_ml_pairs_e]` (after a pair or group a `#if`
is more of the list or the value's trailing decoration), `[ml_value_list, _ml_pairs_r]` (an arm that is a complete
list reads as a whole-value arm or a list-group arm until `#endif`),
`[_ml_tail_lead, _ml_after_lead, _empty_value_conditional, preproc_conditional_ml_pairs]`,
`[_empty_value_conditional, preproc_conditional_ml_pairs]`,
`[_ml_after_lead, _empty_value_conditional, preproc_conditional_ml_pairs]` (the directive-only forms).

## 3. Tree shape

Flat input and every existing whole-value shape keep their trees up to the threshold below: the four corpora are
byte-identical against the pre-change snapshots and the fixture suite is unchanged except the witnesses. New nodes
where a group sits in the list (previously ERROR): `ml_value_list` / `namespace_value_list` > pairs |
`preproc_conditional_*_pairs`.

**One tree-shape change on valid input (item 91):** 9 or more consecutive empty groups after a keyed value parsed clean
before with every group a sibling `preproc_conditional_property_value`; now the first n-8 are list groups, and a
whole-value group before such a run is one too. alc accepts it
(`tools/alc_probe/cases/b7b1c/many_empty_groups_after_value.al`); 0 production sites; breaking under the CHANGELOG rule;
pinned at n=8 and n=9 in `test/corpus/strict_conditional_pair_lists_test.txt`.

`node-types.json`: the two lists gain the group as a child, two new node types. Field-free.

## 4. Oracle and audit

- `conditional_lists.FAMILIES`: `ml_pairs`, `namespace_pairs`, hosts the list nodes; `contracts.py`, `policy.json`
  entries. An emptied keyed value is a property with no value (flat-valid: `list-value-empty`); an emptied TextConst
  flat-parses as `T: TextConst;` (`type_specification`), so the oracle rewrites the split `basic_type` to it
  (`textconst-list-removed`; `test_b7b1c_pair_lists.py`).
- B7a: the `,` key moved from `0.1.0.0` to `1.0.0` (alias rows); group-arm separators `_ml_pairs_*`,
  `_namespace_pairs_*`; `_ml_value_list_flat` an `na` row. Witnesses that pass became
  `test/corpus/strict_conditional_pair_lists_test.txt`; `b7_gap_*` keep the five terminator placements each.

## 5. Left: the terminator cells

`occ:_ml_arm_t:*` / `occ:_namespaces_arm_t:*`: a value followed by a `;` group inside a whole-value arm (and at the
property level, `ENU='a' #if X ; #else ; #endif`, which ERRORs too). Role `terminator`, not a list separator, the same
debt as the keyed families' `_option_values_arm_t` / `_table_relation_arm_t` cells (B7b-1e section 2). Recorded as
item 90, not done here.
