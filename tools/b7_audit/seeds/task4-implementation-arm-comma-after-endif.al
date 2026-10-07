// host: preproc_conditional_impl_values
// valid: X
// source: B7a Task 4 incidental (a `,`-led Implementation arm followed by `, X` after #endif; the parser ERRORs, alc accepted at Task 4 probe, re-measured by Task 6: valid only with X, the !X rejection is AL0596 a missing interface entry, semantic)
interface IFoo { procedure Bar(); }
interface IBar { procedure Bar(); }
interface IBaz { procedure Bar(); }
codeunit 50101 Impl implements IFoo, IBar, IBaz { procedure Bar() begin end; }
table 50100 T { fields { field(1; K; Integer) { } } }
enum 50102 E implements IFoo, IBar, IBaz
{
    value(0; V0)
    {
        Implementation = IFoo = Impl
#if X
            , IBar = Impl
#endif
            , IBaz = Impl;
    }
}
