// expect: * accept
// source: docs/deferred-work.md item 17, commit 04af3f6: alc four-way ACCEPT (assembly)
dotnet
{
    assembly(mscorlib)
    {
        Version =
#if X
            '4.0.0.0';
#else
            '2.0.0.0';
#endif
        Culture = 'neutral';
        PublicKeyToken = 'b77a5c561934e089';
        type(System.DateTime; MyDateTime) { }
    }
}
