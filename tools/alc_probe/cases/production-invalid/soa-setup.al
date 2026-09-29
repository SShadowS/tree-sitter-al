// Source bcapps-29.0:src/Apps/W1/SalesOrderAgent/app/src/Setup/SOASetup.Table.al
// source: milestone-2 results doc, "Resolve sweep" (four-way probe); recorded by A4, 2026-09-29
// expect: * accept
// expect: CLEANSCHEMA28 reject(AL0104,AL0198)
// A field opened inside `#if not CLEANSCHEMA28`, a nested `#if not CLEAN28 ... #else`
// before the outer `#endif`, its `}` after it.
table 50100 T
{
    fields
    {
        field(1; ID; Integer) { }
#if not CLEANSCHEMA28
        field(2; B; Guid)
        {
            ObsoleteReason = 'x';
#if not CLEAN28
            ObsoleteState = Pending;
            ObsoleteTag = '28.0';
#else
            ObsoleteState = Removed;
            ObsoleteTag = '31.0';
#endif
#endif
        }
        field(3; C; Guid) { }
    }
}
