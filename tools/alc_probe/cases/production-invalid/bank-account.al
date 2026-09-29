// Source bcapps-29.0:src/Layers/FR/BaseApp/Bank/BankAccount/BankAccount.Table.al
// source: milestone-2 results doc, "Resolve sweep" (four-way probe); recorded by A4, 2026-09-29
// expect: * accept
// expect: CLEANSCHEMA31 reject(AL0104,AL0198)
// A field opened inside `#if not CLEANSCHEMA31` whose `#if CLEAN28 ... #else` arm carries
// a trigger, its `}` after the outer `#endif`. The file's third symbol, CLEAN27, guards
// only a pragma, as here.
table 50100 T
{
    fields
    {
        field(1; A; Integer) { }
#if not CLEAN27
#pragma warning disable AS0086
#endif
        field(2; B; Integer) { }
#if not CLEAN27
#pragma warning restore AS0086
#endif
#if not CLEANSCHEMA31
        field(10851; C; Text[5])
        {
            Caption = 'C';
#if CLEAN28
            ObsoleteState = Removed;
            ObsoleteTag = '31.0';
#else
            ObsoleteState = Pending;
            ObsoleteTag = '28.0';

            trigger OnValidate()
            begin
                C := 'x';
            end;
#endif
        }
        field(10853; D; Boolean)
        {
            Caption = 'D';
#endif
        }
        field(10854; E; Code[6]) { }
    }
}
