﻿// The file opens with TWO UTF-8 BOMs (bytes EF BB BF EF BB BF), the shape of
// DO.Support/BC/BaseApp/Test/Tests-VAT/ERMVATServCharge.Codeunit.al. alc reads the second one as
// whitespace, not as a token.
// expect: * accept
// source: deferred item 6, recorded by batch1/probes 2026-11-08
codeunit 50100 "Doubled Bom"
{
    procedure P()
    begin
    end;
}
