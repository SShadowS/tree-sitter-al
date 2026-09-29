// Fixture preproc_split_brace_and_case_test.txt#A report dataitem opened inside a branch and closed after %23endif#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !CLEAN28 accept
// expect: CLEAN28 reject(AL0198)
report 50000 T
{
    dataset
    {
        dataitem(Outer; T2)
        {
#if not CLEAN28
            dataitem("Integer"; T2)
            {
                DataItemTableView = sorting(N);
#endif
                dataitem(Total2; T2)
                {
                    DataItemTableView = sorting(N);
                }
            }
        }
    }
}
table 50101 T2 { fields { field(1; N; Integer) { } } keys { key(PK; N) { } } }
