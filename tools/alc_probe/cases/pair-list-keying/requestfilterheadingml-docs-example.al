// Microsoft Learn's RequestFilterHeadingML example, one pair, with a trailing comment.
// source: learn.microsoft.com .../devenv-requestfilterheadingml-property
// expect: * accept
table 50101 T { fields { field(1; F; Integer) { } } }
report 50100 R
{
    dataset { dataitem(D; T) { RequestFilterHeadingML = DAN='Kundeliste'; // Customer list
    } }
}
