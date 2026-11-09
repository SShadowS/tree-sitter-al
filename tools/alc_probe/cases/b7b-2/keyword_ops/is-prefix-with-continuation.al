// Item 51 shape 3, is variant: a typed is prefix arm with a continuation before its keyword, `F is #if X IBar and G is #endif IFoo`
// expect: * accept
// source: batch 4 item 51, 2026-11-09
interface IFoo { }
interface IBar { }
codeunit 50103 Impl implements IFoo, IBar { }
codeunit 50101 P
{
    procedure Q()
    var
        B: Boolean; Ok: Boolean;
        F: Interface IFoo; G: Interface IBar;
    begin
        B := F is
#if X
        IBar and G is
#endif
        IFoo;
    end;
}
