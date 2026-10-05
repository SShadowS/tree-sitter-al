# B5b link-family compiler evidence, alc 18.0.41.62505 (recorded by B5b Task 1, 2026-10-05).
# Source: docs/superpowers/specs/2026-10-05-link-keying-design.md 5.1/5.2. Check: python -m tools.alc_probe run tools/alc_probe/cases/link-keying --check
#
# DECIDE-BY-PROBE VERDICTS (file: verdict). Reject codes are .al-located codes.
decide-chartpart-subpagelink.al: * reject(AL0171)
decide-const-biginteger.al: * accept
decide-const-date.al: * accept
decide-const-datetime-nonzero.al: * reject(AL0257)
decide-const-datetime.al: * accept
decide-const-decimal.al: * accept
decide-const-neg-biginteger.al: * accept
decide-const-neg-comment-integer.al: * accept
decide-const-neg-decimal.al: * accept
decide-const-neg-integer.al: * accept
decide-const-neg-space-decimal.al: * accept
decide-const-neg-space-integer.al: * accept
decide-const-negative-date.al: * reject(AL0104,AL0434)
decide-const-plus-decimal.al: * reject(AL0104)
decide-const-plus-integer.al: * reject(AL0104)
decide-const-time.al: * accept
decide-empty-value-querydataitemlink.al: * reject(AL0171)
decide-empty-value-reportdataitemlink.al: * reject(AL0171)
decide-empty-value-tablefilter.al: * reject(AL0104,AL0107,AL0292)
decide-enabled-status-const.al: * reject(AL0118)
decide-filter-parenthesized.al: * accept
decide-runpagelink-action-area.al: * reject(AL0104,AL0114,AL0124,AL0198)
decide-trailing-comma.al: * reject(AL0104,AL0107,AL0292)
#
# CROSS-DELEGATE NEGATIVES (neg-*): every one is rejected by alc; pinned as it parses in test/corpus.
neg-const-no-parens.al: * reject(AL0104)
neg-dataitemlink-const-query.al: * reject(AL0104,AL0107)
neg-dataitemlink-const-report.al: * reject(AL0104,AL0107)
neg-missing-equals.al: * reject(AL0104)
neg-runpagelink-dotted.al: * reject(AL0104,AL0292)
#
# HOST x PROPERTY TUPLES (flat probe; placements only for accepted rows).
ACCEPTED (7 placements each: flat, semi-after, semi-arms, mixed, list-internal, comment, body-if): page-action-runpagelink, page-part-subpagelink, pageext-addafter-action-runpagelink, pageext-addafter-part-subpagelink, query-column-columnfilter, query-dataitem-dataitemlink, query-dataitem-tablefilter-dataitemtablefilter, query-filter-columnfilter, report-dataitem-dataitemlink, report-requestpage-part-subpagelink, reportext-dataitem-dataitemlink, xmlport-requestpage-part-subpagelink, xmlport-tableelement-linkfields
REJECTED (no fixture, no placement variants): page-systempart-subpagelink reject(AL0171), pageext-modify-action-runpagelink reject(AL0255), pageext-modify-part-subpagelink reject(AL0246), report-requestpage-action-runpagelink reject(AL0255), report-requestpage-systempart-subpagelink reject(AL0171), xmlport-requestpage-action-runpagelink reject(AL0255), xmlport-requestpage-systempart-subpagelink reject(AL0171)
#
# NOTES
# - Empty value: EVERY delegate rejects it (TableFilter AL0107; report and query DataItemLink AL0171). No optional() on the keyed value, no ;-only arms.
# - const: accepted = 1.5, -1, -1.5, 1L, -1L, '- 1', '- 1.5', '-/*c*/1' (space or comment between sign and magnitude), a date (20240101D), a time (120000T), 0DT.
#   Rejected = unary plus (+1, +1.5: AL0104 syntax), a negative date (-20240101D: AL0104,AL0434), 20240101DT (AL0257, a RANGE error: it lexes as a datetime literal, only 0DT is valid).
# - filter((1|2)&3): ACCEPTED -> deferred-work item (filter_value grammar), no grammar change in B5b.
# - chartpart with SubPageLink: REJECTED (AL0171, the value is invalid for a chartpart) -> no deferred item.
# - RunPageLink on an action area: REJECTED (AL0124 among others) -> the AL0124 assumption of 3.2 item 4 holds, no _property_whole_value_in_if arm.
# - Enabled = Status = const(Open): rejected, but SEMANTICALLY (AL0118: the names const and Open do not exist), never AL0104. alc parses it as an expression.
# - Trailing comma A = field(B),; : REJECTED (AL0104,AL0107,AL0292) -> deferred-work item for B7.
# - Host x property tuples rejected: systempart SubPageLink (AL0171, no table to link against), pageext modify RunPageLink (AL0255) and SubPageLink (AL0246),
#   request-page action RunPageLink on report and xmlport (AL0255).
# - G11 shapes (delegate-valid pairs, page part / report data item / query data item): nested, nested-after, nested-mixed, empty-prefix, exhaustive-elif-not accept in every
#   assignment. independent-no-else: X&!Y, !X&Y, X&Y accept, !X&!Y rejects. empty-arm-beside-terminated: !X accepts, X rejects (empty value).
# - Visible = Flag = Rec.Flag on a page field (leak-visible-flag-equals-amount.al) is accepted.
