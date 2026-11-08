// expect: * accept
// source: issue #41/#42: `End` as a value must keep parsing
table 50000 EndValues
{
    fields
    {
        field(1; Kind; Option)
        {
            OptionMembers = End,Start;
            InitValue = End;
        }
        field(2; Other; Option)
        {
            OptionMembers = End,Start;
            ValuesAllowed = End;
        }
        field(3; Code; Code[20])
        {
            TableRelation = EndValues.Code where(Kind = const(End));
        }
        field(4; Cnt; Integer)
        {
            FieldClass = FlowField;
            CalcFormula = count(EndValues where(Kind = filter(End)));
        }
    }
}

page 50000 EndPage
{
    SourceTable = EndValues;
    SourceTableView = where(Kind = const(End));

    actions
    {
        area(Processing)
        {
            action(Open)
            {
                RunObject = page EndPage;
                RunPageLink = Kind = const(End);
            }
        }
    }
}
