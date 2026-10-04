// TextConst Locked = true.
// source: docs/superpowers/specs/2026-10-01-pair-list-property-keying-design.md §2.3
// expect: * reject(AL0104,AL0219)
codeunit 50100 C
{
    var
        T: TextConst ENU='a', Locked = true;
}
