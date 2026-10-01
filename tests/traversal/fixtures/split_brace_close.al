pageextension 50100 "Probe Ext" extends "Customer Card"
{
    layout
    {
        addlast(General)
        {
            field(A; Rec.Name) { }
#if CLEAN25
            field(B; Rec.Address) { }
        }
#else
            field(C; Rec.City) { }
        }
#endif
    }
}
