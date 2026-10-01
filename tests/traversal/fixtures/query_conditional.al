query 50100 "Probe Query"
{
    elements
    {
        dataitem(Item; Item)
        {
            column(No; "No.") { }
#if CLEAN25
            column(Description; Description) { }
#else
            column(Desc2; "Description 2") { }
#endif
        }
    }
}
