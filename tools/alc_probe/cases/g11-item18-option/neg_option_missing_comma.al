// Negative control: no comma between the members.
// expect: * reject
// source: commit 6fed757 control (`B C;` REJECT, AL0104); this is the probe18.py form of it, `A B;`
table 50100 T
{
    fields
    {
        field(1; F; Option)
        {
            OptionMembers =
                A B;
        }
    }
}
