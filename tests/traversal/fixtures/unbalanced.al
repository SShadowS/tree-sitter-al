codeunit 50104 "Unbalanced"
{
    procedure P()
    begin
#if CLEAN25
        Message('never closed');
    end;
}
