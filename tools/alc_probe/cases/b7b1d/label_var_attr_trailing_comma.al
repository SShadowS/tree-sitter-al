// B7b-1d: a Label variable's attribute then a lone trailing comma. alc rejects (AL0301), so the flat grammar has no such form.
// expect: * reject(AL0301)
// source: B7b-1d probe, measured with tools.alc_probe, 2026-11-10
codeunit 50100 C
{
    var
        L: Label 'a', Locked = true,;
}
