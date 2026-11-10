// B7b-1d: an attribute then a lone trailing comma on a report label. alc rejects (AL0301), so the flat grammar has no such form.
// expect: * reject(AL0301)
// source: B7b-1d probe, measured with tools.alc_probe, 2026-11-10
report 50100 R
{
    labels
    {
        L1 = 'a', Locked = true,;
    }
}
