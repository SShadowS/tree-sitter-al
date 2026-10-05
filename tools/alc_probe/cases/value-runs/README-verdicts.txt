B11 value-run evidence, alc 18.0.41, runtime 15.0, recorded 2026-10-05.
24 promoted spec 2.1 probes (*-empty-prefix, *-seq-in-arms, *-seq-after): ACCEPT in every configuration, no drift.
One line per remaining case (decide-by-probe), per-configuration verdicts (X=0 means X undefined). Split and flat agree everywhere.
Effects (Task 1 brief, Step 3 table):
- every all-empty-<f> is REJECTED by alc except captionml and namespaces (accepted): the all-empty site still parses
  (structure, not validation); over-acceptance for the rejected families.
- bare-semi-arm-<f>: REJECTED (bare `;` arm active, X defined) for calcformula, caption, implementation, link,
  optionmembers, tablerelation; ACCEPTED in every configuration for captionml and namespaces (an empty ML/Namespaces
  value is valid). Record: the grammar still does not admit a bare `;` arm (spec 3); add a B13 note in Task 9 for those two.
- host tuples rejected (AL0124): action-area namespaces, assembly ml, assembly namespaces: no fixture for those tuples.
  Accepted: action-area generic (ToolTip) and ml (ToolTipML), assembly generic (Version).
- every b13-* shape is ACCEPTED when X is defined (X=0 leaves `N = ;`, rejected for call-f-paren, caption-locked,
  decimal-range, runobject; accepted for ml-pairs, namespaces-pairs, sorting-where): all remain B13 debt, none become negatives.
- the three boundary-* cases accept in every configuration (alc reads each configuration flat; the one-reading residue is ours).

- Symbol convention for impl-entire-run-separators.al: five symbols, V W X Y Z, in this order of the text: V,W are the leading/trailing
  separator groups' symbols (`#if W ,` leads, `#if V ,` trails), Y selects `IFoo = FooImpl`, X is the joining `,`, Z selects `IBar = BarImpl`.
  The only valid configuration is V=0 W=0 X=1 Y=1 Z=1.
- nested-empty-semi-arm-link.al is a DIFFERENT shape from the spec 5.1 one: a single group with an #else arm. The spec shape (first group
  = nested empty group then `;`, then a separate second group) is nested-empty-semi-arm-link-two-groups.al.
- nested-empty-semi-arm-<caption|captionml|namespaces>: the nested-empty-then-`;` arm for the other optional-core families (see rows).

all-empty-calcformula.al: reject(AL0104,AL0107,AL0176) in all 2 configurations
all-empty-caption.al: reject(AL0219) in all 2 configurations
all-empty-captionml.al: accept in all 2 configurations
all-empty-implementation.al: reject(AL0153,AL0596) in all 2 configurations
all-empty-link.al: reject(AL0104,AL0107,AL0292) in all 2 configurations
all-empty-namespaces.al: accept in all 2 configurations
all-empty-optionmembers.al: reject(AL0153) in all 2 configurations
all-empty-tablerelation.al: reject(AL0107) in all 2 configurations
b13-call-f-paren.al: accept [X=1]; reject(AL0104,AL0224) [X=0]
b13-caption-locked.al: accept [X=1]; reject(AL0219) [X=0]
b13-decimal-range.al: accept [X=1]; reject(AL0114) [X=0]
b13-ml-pairs-comma.al: accept in all 2 configurations
b13-namespaces-pairs-comma.al: accept in all 2 configurations
b13-runobject-page-p.al: accept [X=1]; reject(AL0198) [X=0]
b13-sorting-where.al: accept in all 2 configurations
bare-semi-arm-calcformula.al: accept [X=0]; reject(AL0104,AL0107,AL0176) [X=1]
bare-semi-arm-caption.al: accept [X=0]; reject(AL0219) [X=1]
bare-semi-arm-captionml.al: accept in all 2 configurations
bare-semi-arm-implementation.al: accept [X=0]; reject(AL0153,AL0596) [X=1]
bare-semi-arm-link.al: accept [X=0]; reject(AL0104,AL0107,AL0292) [X=1]
bare-semi-arm-namespaces.al: accept in all 2 configurations
bare-semi-arm-optionmembers.al: accept [X=0]; reject(AL0153) [X=1]
bare-semi-arm-tablerelation.al: accept [X=0]; reject(AL0107) [X=1]
boundary-complementary-three.al: accept in all 4 configurations
boundary-mixed-after.al: accept in all 2 configurations
boundary-visible-caption.al: accept in all 2 configurations
generic-elif-run-inside.al: accept [X=0 Y=0 | X=1 Y=0 | X=1 Y=1]; reject(AL0104,AL0198) [X=0 Y=1]
generic-empty-after-last-inside.al: accept in all 4 configurations
generic-empty-between-groups-inside.al: accept in all 4 configurations
generic-nested-empty-prefix.al: accept in all 4 configurations
generic-terminated-then-property.al: accept in all 4 configurations
generic-three-group-run-inside.al: accept [X=0 Y=0 Z=1 | X=0 Y=1 Z=0 | X=1 Y=0 Z=0]; reject(AL0104,AL0198) [X=0 Y=1 Z=1 | X=1 Y=0 Z=1 | X=1 Y=1 Z=0 | X=1 Y=1 Z=1]; reject(AL0104,AL0219) [X=0 Y=0 Z=0]
generic-trailing-semi-after-terminated-run.al: accept in all 2 configurations
host-action-area-generic-run-inside.al: accept in all 2 configurations
host-action-area-ml-run-inside.al: accept in all 2 configurations
host-action-area-namespaces-run-inside.al: reject(AL0124) in all 2 configurations
host-assembly-generic-run-inside.al: accept in all 2 configurations
host-assembly-ml-run-inside.al: reject(AL0124) in all 2 configurations
host-assembly-namespaces-run-inside.al: reject(AL0124) in all 2 configurations
impl-comma-concat.al: accept in all 4 configurations
impl-entire-run-separators.al: accept [V=0 W=0 X=1 Y=1 Z=1]; reject(AL0104) [V=0 W=0 X=0 Y=1 Z=1]; reject(AL0104,AL0107) [V=0 W=1 X=0 Y=1 Z=1]; reject(AL0104,AL0107,AL0301) [V=1 W=1 X=0 Y=1 Z=1]; reject(AL0104,AL0301) [V=1 W=0 X=0 Y=1 Z=1]; reject(AL0107) x12; reject(AL0107,AL0301) x8; reject(AL0153,AL0596) [V=0 W=0 X=0 Y=0 Z=0]; reject(AL0301) [V=0 W=0 X=1 Y=1 Z=0 | V=1 W=0 X=0 Y=0 Z=1 | V=1 W=0 X=0 Y=1 Z=0 | V=1 W=0 X=1 Y=1 Z=1]; reject(AL0596) [V=0 W=0 X=0 Y=0 Z=1 | V=0 W=0 X=0 Y=1 Z=0]
link-comma-concat.al: accept in all 4 configurations
link-entire-run-separators.al: accept [W=0 X=0 Y=0 Z=1 | W=0 X=0 Y=1 Z=0]; reject(AL0104,AL0107,AL0198,AL0224,AL0292) [W=1 X=1 Y=1 Z=1]; reject(AL0104,AL0107,AL0224,AL0292) [W=0 X=1 Y=1 Z=1]; reject(AL0104,AL0107,AL0292) x10; reject(AL0104,AL0124,AL0198,AL0224) [W=1 X=0 Y=1 Z=1]; reject(AL0104,AL0124,AL0224) [W=0 X=0 Y=1 Z=1]
link-nested-joining-comma.al: accept [X=0 Y=0 | X=0 Y=1 | X=1 Y=1]; reject(AL0104,AL0124,AL0224) [X=1 Y=0]
link-trailing-semi-after-terminated-run.al: accept in all 2 configurations
nested-empty-semi-arm-caption.al: accept [X=0 Y=0 | X=0 Y=1]; reject(AL0219) [X=1 Y=0 | X=1 Y=1]
nested-empty-semi-arm-captionml.al: accept in all 4 configurations
nested-empty-semi-arm-link-two-groups.al: accept [X=0 Y=0 | X=0 Y=1]; reject(AL0171) [X=1 Y=0 | X=1 Y=1]
nested-empty-semi-arm-link.al: accept [X=0 Y=0 | X=0 Y=1]; reject(AL0171) [X=1 Y=0 | X=1 Y=1]
nested-empty-semi-arm-namespaces.al: accept in all 4 configurations
optionmembers-blank-slots-only.al: reject(AL0153) in all 4 configurations
optionmembers-blank-slots.al: accept in all 8 configurations
optionmembers-comma-concat.al: accept in all 4 configurations
optionmembers-entire-run.al: accept in all 4 configurations
optionmembers-selects-nothing.al: accept [X=0 Y=1 | X=1 Y=0 | X=1 Y=1]; reject(AL0153) [X=0 Y=0]
calcformula-after-t-suffix-empty.al: accept [X=0 Z=0 | X=0 Z=1]; reject(AL0104,AL0124) [X=1 Z=0 | X=1 Z=1]  (B11 Task 6, controller ruling 1)
captionml-after-t-suffix-empty.al: accept [X=0 Z=0 | X=0 Z=1]; reject(AL0104) [X=1 Z=0 | X=1 Z=1]  (B11 Task 6, controller ruling 1)
tooltipml-after-t-action-area.al: accept [X=0 Z=0 | X=0 Z=1]; reject(AL0104) [X=1 Z=0 | X=1 Z=1]  (B11 Task 6 fix round 1, ruling 1 at the action-area host)
b13-optionmembers-comma-free.al: accept in all 2 configurations
b13-ml-conditional-terminator.al: accept in all 4 configurations
