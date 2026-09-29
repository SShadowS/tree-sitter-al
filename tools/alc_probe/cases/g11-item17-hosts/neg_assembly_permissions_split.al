// expect: * reject(AL0124)
// source: docs/deferred-work.md item 17 and commit 04af3f6: Permissions at the host REJECT (AL0124), flat and split
table 50101 TT { fields { field(1; A; Integer) { } } }

dotnet
{
    assembly(mscorlib)
    {
        Permissions =
#if X
                    tabledata TT = R;
#else
                    tabledata TT = RM;
#endif
        Version = '4.0.0.0';
        Culture = 'neutral';
        PublicKeyToken = 'b77a5c561934e089';
        type(System.DateTime; MyDateTime) { }
    }
}
