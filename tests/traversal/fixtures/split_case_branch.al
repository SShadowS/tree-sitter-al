codeunit 50100 Probe
{
    procedure P(K: Integer)
    begin
        case K of
#if CLEAN25
            3,
#endif
            1, 2:
                Message('x');
        end;
    end;
}
