// host: ml_value_list
// valid: !X,!Z; !X,Z
// seed-source: tools/alc_probe/cases/value-runs/tooltipml-after-t-action-area.al (verdicts measured by alc, as recorded in its expect lines)
// Fixture property_value_run_test.txt#B11: ToolTipML `;`-after run ending in a terminated group at the action-area host: the property ends at the group, a conditional action and an action follow (ruling 1)#0
// B11 controller ruling 1 at the action-area host (_property_whole_value_in_if): a ToolTipML `;`-after run ending in a terminated group, then a conditional action and an action.
// source: docs/superpowers/specs/2026-10-05-property-value-runs-design.md 3.2
// expect: * accept
// expect: X reject(AL0104)
page 50100 P { PageType = RoleCenter; actions { area(Embedding) {
ToolTipML =
#if X
ENU='a'
#endif
#if not X
ENU='b';
#else
ENU='c';
#endif
#if Z
action(B) { RunObject = page P; }
#endif
action(A) { RunObject = page P; } } } }
