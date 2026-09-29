// Valid only with S31 undefined: the field's `{` opens inside the #if.
// expect: * accept
// expect: S31 reject(AL0104,AL0198)
// source: docs/bc29-parse-gaps.md family D (undefined ACCEPT, S31 REJECT with AL0104, AL0198), commit 5b809bc
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
#if not S31
        field(2; B; Integer)
        {
            Caption = 'X';
#endif
        }
        field(3; C; Integer) { }
    }
}
