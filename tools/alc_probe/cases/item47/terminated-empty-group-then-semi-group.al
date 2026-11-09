// Fixture item_47_case_empty_group_test.txt#Item 47: an empty group then a semicolon group after a terminated branch (alc accepts Y=0)#0
// expect: !Y accept
// expect: Y reject(AL0104,AL0111,AL0224)
// source: deferred item 47, an empty group then a `;` group after a TERMINATED branch (shape 6's neighbour; ERRORed on main)
codeunit 50100 Demo
{
    procedure Run(I: Integer)
    begin
        case I of
            1:
                A();
#if X
#endif
#if Y
            ;
#endif
            2:
                B();
        end;
    end;

    procedure A()
    begin
    end;

    procedure B()
    begin
    end;
}
