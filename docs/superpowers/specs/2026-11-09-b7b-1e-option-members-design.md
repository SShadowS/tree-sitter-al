# B7b-1e: conditional option-member lists (deferred item 46, row B7b-1e)

Date: 2026-11-09. Branch `batch5/item46e`. Parent: B7b-1 spec
(`2026-10-07-b7b-1-strict-conditional-lists-design.md`), item 37 (OptionMembers keyed by name, B13).

## 1. What is left of the family

After item 37 the B7a `option-members` family had 436 GAP cells (from 1,111):

| cells | key / host | what |
|---|---|---|
| 300 | `option_member_list:*`, `_option_member_list_empty_open`, `_option_members_comma_conditional` at `option_type` | a `#if` group in the member list of an `Option` TYPE (`X: Option A #if X , B #endif;`) |
| 135 | `_option_values_arm_t:*` at the property hosts | a `;`-group inside an arm of a whole-value OptionMembers group (`#if TPL A,B,C #if X ; #endif #else ... #endif`): the terminator debt every keyed `;`-after family shares (link family, ML, Namespaces) |
| 1 | `seed:value-runs__bare-semi-arm-optionmembers` | a bare `;` arm (`#if X ; #else A; #endif`); item 37 "still open" |

The option-type cells are the conversion. Production sites with a group in an option type: 0 (four corpora;
the six `preproc_conditional_option_members` production shapes are `IncludedPermissionSets`, item 73). Real
production option types (thousands, flat) must keep their trees.

## 2. Scope

In:
- Every B7a placement at `option_type` (sep-before, sep-after, sep-only, both-in-arm, first-replace, nested,
  adjacent, elif, empty, holes, lead-optional, one-elem, empty-list, count-differs), with comments and `#if not`.
- Every host of a type: variable, parameter, return type, interface procedure return type.
- The `not`-arm-before-comma-led-member shape recorded under item 46 (`#if X not #endif ,B`), at the option
  type. At the keyed property it already parses since item 37 (record it).

Out (recorded, not converted):
- The 135 terminator cells: a `;` group nested in a whole-value arm. Not a list separator; it is the
  keyed-family terminator debt (link family's identical placements are GAP too) and needs one design across
  the `;`-after families.
- The bare-`;` seed (item 37, still open).
- Item 65 (comma-less group-then-member at a GENERIC property, `Visible = #if X Foo #endif Ok;`): it reaches
  `option_member_list` through `_property_value`, which this change does not touch. Must stay as it is.
- Over-acceptance of forms invalid in every configuration (`A #if X B #endif C`): item 44's decided limit;
  the oracle refuses each configuration (`two members without a separator`).

## 3. Grammar

`option_type` stops using `option_member_list` (the generic property's rule) and gets its own list, aliased
to `option_member_list`: a run of members, `,` and groups with no two members adjacent (right-recursive
`_option_type_more`), groups `preproc_conditional_option_members` whose arms are the keyed OptionMembers
list run (`_option_values_rest`: members, blank slots, nested groups). Not `strictListBody`: blank ordinals
(`Option ,,A`) are valid, so `item (sep item)*` does not fit (item 37's reason).

The host can own a group after the type's last member: a parameter list group (B7b-1b), a var block or
pragma-only group before `begin`, an interface body sibling. Two rules keep the host's tree:

1. An all-empty group (directives only) is part of the type's list only when more of the list follows it
   (`_option_type_group_e` is never last). An empty trailing group therefore always belongs to the host, and
   the GLR tie between `preproc_pragma_only` and an empty `preproc_conditional_var_block`, which is decided by
   version order on main, is not perturbed by a third reading.
2. A witnessed group (some arm non-empty, `witnessConditional`) carries `prec.dynamic(-1)`: where the host
   reading also completes (an arm of nested empty groups), the host wins.

Conflicts: `[_option_type_members]`, `[_option_type_more]` (a `#if` or a keyword after a member: more of the
list or the host's next item), `[_option_type_group_w, _option_type_group_e]` (the two group forms until an
arm).

## 4. Tree shape

Unchanged node types: `option_member_list` > `option_member` | `preproc_conditional_option_members` (arms:
`option_member`, nested groups; `,` anonymous). A list that is only groups is still `option_member_list`.
`node-types.json` unchanged. No tree changes on input that parsed before (main vs branch over the four
corpora and the variant sweeps in the fixture file).

## 5. Witnesses and gates

- `test/corpus/b7_gap_option_members_test.txt`: the 15 option-type witnesses move to
  `test/corpus/strict_conditional_option_members_test.txt` (positive, the witness's variable declaration in a
  minimal codeunit); the seed witness stays.
- Probes: `tools/alc_probe/cases/b7b1e/` (hosts, empty group after the type, `not` arm, plus the two shapes
  still ERRORing: bare `Option` then a host group, a trailing all-empty group in a variable's type).
- Oracle: an option type's list emptied by its groups is removed (flat `Option` has no list).
- B7a: the option_type registry rows move to the two live keys; `run --only option-members`.
