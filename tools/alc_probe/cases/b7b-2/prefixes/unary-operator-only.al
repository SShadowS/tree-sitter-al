// B7b-2 final review (Important 1): a group whose only arm content is a unary operator: `I := #if X - #endif 1;`, `B := Ok and #if Y not #endif Ok;`, `if #if Z not #endif Ok then;`, and an action's `Visible = #if W not #endif Ok;` (page 50102). alc accepts every configuration; the parser ERRORed on the first three and read the fourth as a comma-less option list, until item 61's fix (docs/deferred-work.md item 61; test/corpus/b7b2_unary_op_only_test.txt)
// expect: * accept
// source: B7b-2 final whole-branch review, 2026-10-21 (reviewer probe scratchpad alc/unary-op-only.al; the `if` statement added in the fix round), alc 18.0.41 four-way probe; the page added by item 61's fix, 2026-10-25
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer; B: Boolean; Ok: Boolean;
    begin
        I :=
#if X
        -
#endif
        1;
        B := Ok and
#if Y
        not
#endif
        Ok;
        if
#if Z
        not
#endif
        Ok then;
    end;
}
page 50102 PG
{
    actions
    {
        area(Processing)
        {
            action(A2)
            {
                Visible =
#if W
                    not
#endif
                    Ok;
                trigger OnAction()
                begin
                end;
            }
        }
    }
    var
        Ok: Boolean;
}
