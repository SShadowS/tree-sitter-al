// Fixture b7b3_case_separator_negative_test.txt#B7b-3 case known over-acceptance: an empty group then a semicolon after a terminated branch (a doubled semicolon in every configuration; deferred-work item 44 decided limit, admitted by item 47's sibling empty_statement)#0
// expect: * reject(AL0104,AL0224)
// source: deferred item 47 fix round: `1: Bar; #if X #endif ;` is `1: Bar;;` in every configuration
codeunit 50100 Demo
{
    procedure Run(I: Integer)
    begin
        case I of
            1:
                Bar();
#if X
#endif
            ;
        end;
    end;

    procedure Bar()
    begin
    end;
}
