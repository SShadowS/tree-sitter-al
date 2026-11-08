// A UTF-8 BOM (U+FEFF) at the start of the line between the two codeunits, far from offset 0:
// alc accepts it anywhere whitespace may stand, so it is whitespace, not a token.
// expect: * accept
// source: deferred item 6, recorded by batch1/probes 2026-11-08
codeunit 50100 "Bom One"
{
}
﻿codeunit 50101 "Bom Two"
{
}
