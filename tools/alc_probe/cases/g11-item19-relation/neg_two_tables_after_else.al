// Negative control, active only with X defined.
// expect: !X accept
// expect: X reject(AL0104,AL0124)
// source: commit 824fcf4 control (`else Resource Customer` REJECT, AL0104, AL0124): X defined
// source: recorded by A2, 2026-09-29: X undefined (the arm is inactive, leaving a valid relation)
table 50101 Item { fields { field(1; "No."; Code[20]) { } } }
table 50102 Resource { fields { field(1; "No."; Code[20]) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } } }
table 50100 T
{
    fields
    {
        field(1; Type; Option) { OptionMembers = Item, Resource; }
        field(2; "No."; Code[20])
        {
            TableRelation = if (Type = const(Item)) Item
#if X
                else Resource Customer
#endif
                ;
        }
    }
}
