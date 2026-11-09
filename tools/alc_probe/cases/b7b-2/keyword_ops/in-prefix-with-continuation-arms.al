// Item 51 shape 3: continuations in every arm of a typed in prefix, an `in` item among them
// expect: * accept
// source: batch 4 item 51, 2026-11-09
codeunit 50101 P
{
    procedure Q()
    var
        I: Integer; B: Boolean; Ok: Boolean;
    begin
        B := Ok in
#if X
        [true] in [false] and Ok in
#else
        [true] or Ok xor (I = 2) in
#endif
        [false];
    end;
}
