// Fixture split_table_field_open_test.txt#Field body opened inside %23if, closed after %23endif (one valid configuration)#0
// source: alc 18.0.41, first probed in the A3 review (2026-09-29); recorded by A3 fix 1, 2026-09-29
// expect: !C28 !S31 accept
// expect: !C28 S31 reject(AL0104,AL0162,AL0198)
// expect: C28 !S31 accept
// expect: C28 S31 reject(AL0104,AL0162,AL0198)
// Compiles ONLY with S31 undefined: defined, alc rejects it (AL0104). The tree is that one reading.
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
#if not S31
        field(2; B; Integer) { }
        field(3; C; Integer)
        {
            Caption = 'X';
#if C28
            ObsoleteState = Pending;
#endif
#endif
            trigger OnValidate()
            begin
            end;
        }
        field(4; D; Integer) { }
    }
}
