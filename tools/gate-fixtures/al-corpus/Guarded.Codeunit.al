codeunit 50101 "Selftest Guarded"
{
    procedure Run()
    begin
#if CLEAN25
        Message('new');
#else
        Message('old');
#endif
    end;
}
