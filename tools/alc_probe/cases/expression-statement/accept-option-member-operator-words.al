// B6 (code_names reserved set): every operator word is an option member, first position included
// source: recorded by B6 task 5, 2026-10-06; the option_member arms beside the reserved set
// expect: * accept
table 50100 T { fields { field(1; div; Integer) { } field(2; K; Option) { OptionMembers = and,or,is,div; } field(3; L; Option) { OptionMembers = not,in,mod,xor; } } }
