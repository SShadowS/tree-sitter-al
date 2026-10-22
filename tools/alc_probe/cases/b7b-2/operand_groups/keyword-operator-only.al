// B7b-2 Phase C (Task 10): the B3 operator-only form with `as` and `in`, the operand typed after #endif
// Fixture b7b2_operand_group_test.txt#B7b-2 operand group: operator-only form with a keyword operator#0
// expect: X accept
// expect: !X reject(AL0111)
// source: B7b-2 Phase C (Task 10), 2026-10-21
interface IFoo { }
codeunit 50101 P
{
    procedure Q()
    var
        I: Interface IFoo; I2: Interface IFoo; B: Boolean; Ok: Boolean;
    begin
        I2 := I
#if X
            as
#endif
            IFoo as IFoo;
        B := Ok
#if X
            in
#else
            in
#endif
            [true];
    end;
}
