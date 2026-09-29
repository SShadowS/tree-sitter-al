// Fixture preproc_split_brace_and_case_test.txt#A report dataitem whose closing brace is inside a branch#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !CLEAN28 accept
// expect: CLEAN28 reject(AL0104)
report 50000 T
{
    dataset
    {
        dataitem(Outer; T2)
        {
            dataitem(Inner; T2)
            {
                column(A; ALbl)
                {
                }
#if not CLEAN28
                column(B; BLbl)
                {
                }
            }
#else
                column(C; CLbl)
                {
                }
#endif
            trigger OnPreDataItem()
            begin
                if not ShowIt then
                    CurrReport.Break();
            end;
        }
        dataitem(Next; T2)
        {
            DataItemTableView = sorting(N);
        }
    }
    var
        ALbl: Label 'a';
        BLbl: Label 'b';
        CLbl: Label 'c';
        ShowIt: Boolean;
}
table 50101 T2 { fields { field(1; N; Integer) { } } keys { key(PK; N) { } } }
