"""The word `end` in every name position: `has_error` must equal main's (abc77b25, before state review C3).

Since C3 `end` is a grammar token (`end_keyword`), not an external one. Where it is never a name, two
mechanisms make it an ERROR: the reserved set `statement_names` at a statement start, and the scanner's
MALFORMED_DIRECTIVE clause in every state that offers BEGIN_KEYWORD but not CONTINUE_AS_IDENTIFIER (a var
section's next declaration, a procedure's return-value name, ...). That clause is safe only while
`end_keyword` is valid in none of those states; `test_end_never_valid_where_the_scanner_rejects_it` reads
that property from src/parser.c, and the matrix below is the behaviour it protects. A row clean on one
side only is a regression either way: clean here and ERROR on main reads code alc accepts as broken; ERROR
on main and clean here accepts code alc rejects (AL0519; `procedure T() End: Integer` was one, found by
this matrix).

EXPECTED is main's `has_error` per spelling `end`, `End`, `END`, `"End"` (E = ERROR, . = clean, - = not
generated). Several clean rows are over-acceptances main shares (a parameter named End, alc AL0104);
the matrix pins sameness with main, not correctness, except the rows in DIFFERS_FROM_MAIN. The spec of the probe rows:
docs/superpowers specs, state review C3, section 5."""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SPELL = {"lower": "end", "title": "End", "upper": "END", "quoted": '"End"'}


def cu(members, name="P"):
    return f"codeunit 50100 {name}\n{{\n{members}\n}}\n"


def proc(stmts="A := 1;", vars_="", params="", ret="", name="T"):
    v = f"    var\n        A: Integer;\n        R: Codeunit P;\n        L: List of [Integer];\n{vars_}"
    return f"    procedure {name}({params}){ret}\n{v}    begin\n        {stmts}\n    end;\n"


def table(fields, rest=""):
    return f"table 50100 T\n{{\n    fields\n    {{\n{fields}\n    }}\n{rest}}}\n"


ROWS = {
    # declarations
    "var_first": lambda e: cu(f"    procedure T()\n    var\n        {e}: Integer;\n    begin\n    end;\n"),
    "var_second": lambda e: cu(proc(vars_=f"        {e}: Integer;\n")),
    "var_namelist": lambda e: cu(f"    procedure T()\n    var\n        A, {e}: Integer;\n    begin\n    end;\n"),
    "var_attribute": lambda e: cu(f"    procedure T()\n    var\n        [NonDebuggable]\n        {e}: Text;\n    begin\n    end;\n"),
    "var_label": lambda e: cu(proc(vars_=f"        {e}: Label 'x';\n")),
    "global_var": lambda e: cu(f"    var\n        {e}: Integer;\n\n" + proc()),
    "global_var_second": lambda e: cu(f"    var\n        A: Integer;\n        {e}: Integer;\n\n    procedure T()\n    begin\n    end;\n"),
    "protected_var": lambda e: cu(f"    protected var\n        {e}: Integer;\n\n    procedure T()\n    begin\n    end;\n"),
    "param_first": lambda e: cu(proc(params=f"{e}: Integer")),
    "param_second": lambda e: cu(proc(params=f"B: Integer; {e}: Integer")),
    "param_var": lambda e: cu(proc(params=f"var {e}: Integer")),
    "return_name": lambda e: cu(proc(ret=f" {e}: Integer")),
    "return_name_no_var": lambda e: cu(f"    procedure T() {e}: Integer\n    begin\n    end;\n"),
    "return_name_local": lambda e: cu(f"    local procedure T() {e}: Integer\n    begin\n    end;\n"),
    "return_name_after_attribute": lambda e: cu(f"    [TryFunction]\n    procedure T() {e}: Boolean\n    begin\n    end;\n"),
    "return_name_interface": lambda e: f"interface I\n{{\n    procedure T() {e}: Integer;\n}}\n",
    "trigger_return_name": lambda e: cu(f"    trigger OnRun() {e}: Integer\n    begin\n    end;\n"),
    "event_subscriber_param": lambda e: cu(f"    [EventSubscriber(ObjectType::Codeunit, Codeunit::P, 'OnFoo', '', false, false)]\n    local procedure S({e}: Integer)\n    begin\n    end;\n"),
    "event_publisher_param": lambda e: cu(f"    [IntegrationEvent(false, false)]\n    local procedure OnFoo(A: Integer; {e}: Integer)\n    begin\n    end;\n"),
    "procedure_name": lambda e: cu(proc(name=e)),
    "trigger_name": lambda e: cu(f"    trigger {e}()\n    begin\n    end;\n"),
    "event_name": lambda e: cu(f"    [IntegrationEvent(false, false)]\n    procedure {e}()\n    begin\n    end;\n"),
    "table_field": lambda e: table(f"        field(1; {e}; Integer) {{ }}"),
    "table_key": lambda e: table("        field(1; A; Integer) { }", f"    keys\n    {{\n        key({e}; A) {{ }}\n    }}\n"),
    "table_key_field": lambda e: table("        field(1; A; Integer) { }", f"    keys\n    {{\n        key(PK; A, {e}) {{ }}\n    }}\n"),
    "fieldgroup": lambda e: table("        field(1; A; Integer) { }", f"    fieldgroups\n    {{\n        fieldgroup({e}; A, {e}) {{ }}\n    }}\n"),
    "enum_value": lambda e: f"enum 50100 E\n{{\n    value(0; {e}) {{ }}\n    value(1; B) {{ }}\n}}\n",
    "enum_name": lambda e: f"enum 50100 {e}\n{{\n    value(0; A) {{ }}\n}}\n",
    "obj_codeunit": lambda e: f"codeunit 50100 {e}\n{{\n}}\n",
    "obj_table": lambda e: f"table 50100 {e}\n{{\n    fields\n    {{\n        field(1; A; Integer) {{ }}\n    }}\n}}\n",
    "obj_page": lambda e: f"page 50100 {e}\n{{\n}}\n",
    "obj_report": lambda e: f"report 50100 {e}\n{{\n}}\n",
    "obj_query": lambda e: f"query 50100 {e}\n{{\n    elements\n    {{\n        dataitem(C; Customer) {{ }}\n    }}\n}}\n",
    "obj_xmlport": lambda e: f"xmlport 50100 {e}\n{{\n}}\n",
    "obj_interface": lambda e: f"interface {e}\n{{\n}}\n",
    "obj_permissionset": lambda e: f"permissionset 50100 {e}\n{{\n}}\n",
    "obj_tableextension": lambda e: f"tableextension 50100 {e} extends Customer\n{{\n}}\n",
    "obj_pageextension": lambda e: f'pageextension 50100 {e} extends "Customer Card"\n{{\n}}\n',
    "obj_reportextension": lambda e: f'reportextension 50100 {e} extends "Customer - List"\n{{\n}}\n',
    "obj_enumextension": lambda e: f'enumextension 50100 {e} extends "Sales Line Type"\n{{\n}}\n',
    "obj_profile": lambda e: f'profile {e}\n{{\n    RoleCenter = "Business Manager Role Center";\n}}\n',
    "obj_controladdin": lambda e: f"controladdin {e}\n{{\n}}\n",
    "obj_entitlement": lambda e: f"entitlement {e}\n{{\n}}\n",
    "report_dataitem_column": lambda e: f'report 50100 R\n{{\n    dataset\n    {{\n        dataitem({e}; Customer)\n        {{\n            column({e}; "No.") {{ }}\n        }}\n    }}\n}}\n',
    "page_controls_actions": lambda e: f'page 50100 P\n{{\n    layout\n    {{\n        area(Content)\n        {{\n            group({e})\n            {{\n                field({e}; Rec."No.") {{ }}\n            }}\n        }}\n    }}\n    actions\n    {{\n        area(Processing)\n        {{\n            action({e}) {{ }}\n        }}\n    }}\n}}\n',
    "query_dataitem_column": lambda e: f'query 50100 Q\n{{\n    elements\n    {{\n        dataitem({e}; Customer)\n        {{\n            column({e}; "No.") {{ }}\n        }}\n    }}\n}}\n',
    "xmlport_elements": lambda e: f'xmlport 50100 X\n{{\n    schema\n    {{\n        textelement({e})\n        {{\n            tableelement({e}; Customer)\n            {{\n                fieldelement({e}; {e}."No.") {{ }}\n            }}\n        }}\n    }}\n}}\n',
    # code
    "stmt_call": lambda e: cu(proc(stmts=f"{e};")),
    "stmt_call_parens": lambda e: cu(proc(stmts=f"{e}();")),
    "stmt_assign": lambda e: cu(proc(stmts=f"{e} := 1;")),
    "stmt_compound_assign": lambda e: cu(proc(stmts=f"{e} += 1;")),
    "expr_value": lambda e: cu(proc(stmts=f"A := {e};")),
    "expr_binary": lambda e: cu(proc(stmts=f"A := 1 + {e};")),
    "expr_condition": lambda e: cu(proc(stmts=f"if {e} then A := 1;")),
    "argument": lambda e: cu(proc(stmts=f"T({e});", params="X: Integer")),
    "argument_second": lambda e: cu(proc(stmts=f"Message('%1', {e});")),
    "member_call": lambda e: cu(proc(stmts=f"R.{e}();")),
    "member_bare_call": lambda e: cu(proc(stmts=f"R.{e};")),
    "member_assign": lambda e: cu(proc(stmts=f"R.{e} := 1;")),
    "member_value": lambda e: cu(proc(stmts=f"A := R.{e};")),
    "enum_qualified": lambda e: cu(proc(stmts=f"A := MyEnum::{e};")),
    "database_qualified": lambda e: cu(proc(stmts=f"A := Database::{e};")),
    "rec_field": lambda e: table(f"        field(1; A; Integer)\n        {{\n            trigger OnValidate()\n            begin\n                A := Rec.{e};\n                A := xRec.{e};\n                Rec.{e} := 1;\n            end;\n        }}"),
    "case_pattern": lambda e: cu(proc(stmts=f"case A of\n            {e}:\n                A := 1;\n        end;")),
    "case_range": lambda e: cu(proc(stmts=f"case A of\n            1..{e}:\n                A := 1;\n        end;")),
    "in_list": lambda e: cu(proc(stmts=f"if A in [{e}, 1] then A := 1;")),
    "for_var": lambda e: cu(proc(stmts=f"for {e} := 1 to 2 do A := 1;")),
    "foreach_var": lambda e: cu(proc(stmts=f"foreach {e} in L do A := 1;")),
    "with_var": lambda e: cu(proc(stmts=f"with {e} do A := 1;")),
    "property_value": lambda e: table(f"        field(1; A; Option)\n        {{\n            OptionMembers = Start,{e};\n            InitValue = {e};\n        }}"),
    "property_value_if_arm": lambda e: table(f"        field(1; A; Option)\n        {{\n            OptionMembers =\n#if X\n                {e},\n#endif\n                Start;\n        }}"),
    # directly before the block's own end (the spelling is the block end's)
    "before_end_if_then": lambda e: cu(f"    procedure T()\n    var\n        A: Integer;\n    begin\n        if A = 1 then\n    {e};\n"),
    "before_end_else": lambda e: cu(f"    procedure T()\n    var\n        A: Integer;\n    begin\n        if A = 1 then A := 2 else\n    {e};\n"),
    "before_end_while": lambda e: cu(f"    procedure T()\n    var\n        A: Integer;\n    begin\n        while A = 1 do\n    {e};\n"),
    "before_end_case_branch": lambda e: cu(f"    procedure T()\n    var\n        A: Integer;\n    begin\n        case A of\n            1:\n        {e};\n    {e};\n"),
    "before_end_repeat": lambda e: cu(f"    procedure T()\n    var\n        A: Integer;\n    begin\n        repeat\n    {e};\n"),
    # the block end itself, in each spelling
    "block_end_spelling": lambda e: cu(f"    procedure T()\n    var\n        A: Integer;\n    begin\n        begin\n            A := 1;\n        {e};\n    {e};\n"),
    # a statement inside the arm of a guarded statement (see DIFFERS_FROM_MAIN)
    "guard_arm_end_statement": lambda e: cu(f"    procedure T()\n    var\n        A: Integer;\n        C: Boolean;\n    begin\n#if X\n        T();\n        {e};\n        if C then\n#endif\n        A := 1;\n    end;\n"),
}

# main (abc77b25), per spelling lower / title / upper / quoted
EXPECTED = {
    "argument": "....", "argument_second": "....",
    "before_end_case_branch": "EEE-", "before_end_else": "EEE-", "before_end_if_then": "EEE-",
    "before_end_repeat": "EEE-", "before_end_while": "EEE-", "block_end_spelling": "...-",
    "case_pattern": "EEE.", "case_range": "....", "database_qualified": "....",
    "enum_name": "....", "enum_qualified": "....", "enum_value": "....", "event_name": "....",
    "event_publisher_param": "....", "event_subscriber_param": "....",
    "expr_binary": "....", "expr_condition": "....", "expr_value": "....", "fieldgroup": "....",
    "for_var": "....", "foreach_var": "....", "global_var": "....", "global_var_second": "....",
    "in_list": "....", "member_assign": "....", "member_bare_call": "....", "member_call": "....",
    "member_value": "....",
    "obj_codeunit": "....", "obj_controladdin": "....", "obj_entitlement": "....",
    "obj_enumextension": "....", "obj_interface": "....", "obj_page": "....",
    "obj_pageextension": "....", "obj_permissionset": "....", "obj_profile": "....",
    "obj_query": "....", "obj_report": "....", "obj_reportextension": "....", "obj_table": "....",
    "obj_tableextension": "....", "obj_xmlport": "....",
    "page_controls_actions": "....", "param_first": "....", "param_second": "....",
    "param_var": "....", "procedure_name": "....", "property_value": "....",
    "property_value_if_arm": "....", "protected_var": "....", "query_dataitem_column": "....",
    "rec_field": "....", "report_dataitem_column": "....",
    "return_name": "EEE.", "return_name_after_attribute": "EEE.", "return_name_interface": "EEE.",
    "return_name_local": "EEE.", "return_name_no_var": "EEE.",
    "stmt_assign": "EEE.", "stmt_call": "EEE.", "stmt_call_parens": "EEE.",
    "stmt_compound_assign": "EEE.",
    "table_field": "....", "table_key": "....", "table_key_field": "....", "trigger_name": "....",
    "trigger_return_name": "EEE.",
    "var_attribute": "EEE.", "var_first": "EEE.", "var_label": "EEE.", "var_namelist": "....",
    "var_second": "EEE.", "with_var": "....", "xmlport_elements": "....",
}

# Rows that differ from main ON PURPOSE (not main's has_error). guard_arm_end_statement: `End;` as a
# statement in a preproc guard arm (`#if X F(); End; if C then #endif A := 1;`) was clean on main, a call
# named End; alc 18.0.41 rejects X=1 (AL0104, AL0198) and accepts X=0
# (tools/alc_probe/cases/issue40-42/end-statement-in-guard-arm.al). Since C3 it is an ERROR: correct.
# Review of C3, finding F2; main's flags were "...." (quoted stays a clean call).
DIFFERS_FROM_MAIN = {"guard_arm_end_statement": "EEE."}
EXPECTED.update(DIFFERS_FROM_MAIN)

CASES = [(row, sp, flags[i] == "E")
         for row, flags in EXPECTED.items()
         for i, sp in enumerate(SPELL) if flags[i] != "-"]


def test_matrix_is_complete():
    assert set(EXPECTED) == set(ROWS)


@pytest.mark.parametrize("row,spelling,error", CASES, ids=[f"{r}-{s}" for r, s, _ in CASES])
def test_end_name_position_matches_main(al_parser, row, spelling, error):
    src = ROWS[row](SPELL[spelling]).encode()
    assert al_parser.parse(src).root_node.has_error is error


def test_end_never_valid_where_the_scanner_rejects_it(al_language):
    """The property the scanner's `end` clause rests on, read from the generated tables: no parse state
    whose external lex state offers begin_keyword without continue_as_identifier (and without
    preproc_split_end) has end_keyword as a valid lookahead."""
    src = (REPO / "src" / "parser.c").read_text(encoding="utf-8")
    table = re.search(r"ts_external_scanner_states\[\d+\]\[EXTERNAL_TOKEN_COUNT\] = \{(.*?)\n\};", src, re.S)
    rows = {int(i): set(re.findall(r"\[ts_external_token_(\w+)\] = true", body))
            for i, body in re.findall(r"\[(\d+)\] = \{(.*?)\n  \}", table.group(1), re.S)}
    full = max(len(s) for s in rows.values())
    clause = {i for i, s in rows.items()
              if "begin_keyword" in s and "continue_as_identifier" not in s
              and "preproc_split_end" not in s and len(s) < full}   # the all-valid row is recovery
    assert clause, "no external row matches the clause: the table parse is broken"
    modes = re.findall(r"\[(\d+)\] = \{\.lex_state = \d+(?:, \.external_lex_state = (\d+))?", src)
    states = [int(st) for st, ext in modes if ext and int(ext) in clause]
    assert states
    bad = [s for s in states if "end_keyword" in set(al_language.lookahead_iterator(s).names())]
    assert not bad, f"end_keyword is valid in states {bad[:20]} of external rows {sorted(clause)}"
