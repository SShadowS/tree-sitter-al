enum 50100 "Probe Kind" implements "IProbe", "IOther"
{
    Extensible = true;
    DefaultImplementation = "IProbe" = "Probe Default",
#if CLEAN25
        "IOther" = "Other New"
#else
        "IOther" = "Other Old"
#endif
        ;

    value(0; None) { }
}
