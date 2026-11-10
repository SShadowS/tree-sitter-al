// B7b-1d: a report label's value followed by a lone comma. alc accepts (the label tail's optional item, as a Label variable's).
// expect: * accept
// source: B7b-1d probe, measured with tools.alc_probe, 2026-11-10
report 50100 R
{
    labels
    {
        L1 = 'a',;
    }
}
