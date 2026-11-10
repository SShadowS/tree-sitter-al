// expect: Q !R accept
// expect: Q R accept
// expect: !Q !R reject(AL0149)
// expect: !Q R reject(AL0149)
// source: deferred item 100 (from batch 6's item 81 review, probe rv3/m26): an empty #if group alone before the ; in a relation arm
table 50101 Item { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50102 Resource { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50103 Customer { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50104 Vendor { fields { field(1; "No."; Code[20]) { } field(2; A; Integer) { } } }
table 50100 T
{
 fields
 {
  field(2; B; Integer) { }
  field(1; A; Integer)
  {
TableRelation =
Item
#if Q
#if R
#endif
;
#else
else Customer
#if R
;
#else
;
#endif
#endif
  }
 }
}
