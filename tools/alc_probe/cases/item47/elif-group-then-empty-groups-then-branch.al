// expect: * accept
// source: deferred item 47 fix round: an empty #elif group, then two empty groups, before a branch (main made the first a sibling group, now all are the split branch's pattern groups)
codeunit 50100 Demo
{
    procedure Run(I: Integer)
    begin
        case I of
#if Y
#elif Z
#endif
#if W
#endif
#if X
#endif
            6:
                F();
        end;
    end;

    procedure F()
    begin
    end;
}
