#if CONDITION
#pragma warning disable AL0432
codeunit 50100 "Test Impl" implements Interface1, Interface2
#pragma warning restore AL0432
#else
codeunit 50100 "Test Impl" implements Interface2
#endif
{
    Access = Internal;

    procedure TestMethod()
    begin
    end;
}
