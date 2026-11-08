// expect: * accept
// source: issue #34, enumextension extends <number>
enum 50105 "Base Enum"
{
    Extensible = true;
    value(0; A) { }
}
enumextension 50106 "Repro Enum Ext" extends 50105
{
    value(50100; B) { }
}
