#include "tree_sitter/parser.h"

#if defined(__GNUC__) || defined(__clang__)
#pragma GCC diagnostic ignored "-Wmissing-field-initializers"
#endif

#ifdef _MSC_VER
#pragma optimize("", off)
#elif defined(__clang__)
#pragma clang optimize off
#elif defined(__GNUC__)
#pragma GCC optimize ("O0")
#endif

#define LANGUAGE_VERSION 14
#define STATE_COUNT 1159
#define LARGE_STATE_COUNT 2
#define SYMBOL_COUNT 342
#define ALIAS_COUNT 9
#define TOKEN_COUNT 171
#define EXTERNAL_TOKEN_COUNT 0
#define FIELD_COUNT 58
#define MAX_ALIAS_SEQUENCE_LENGTH 12
#define PRODUCTION_ID_COUNT 85

enum ts_symbol_identifiers {
  anon_sym_table = 1,
  anon_sym_LBRACE = 2,
  anon_sym_RBRACE = 3,
  anon_sym_codeunit = 4,
  anon_sym_Install = 5,
  anon_sym_Upgrade = 6,
  anon_sym_Test = 7,
  anon_sym_FlowField = 8,
  anon_sym_FlowFilter = 9,
  anon_sym_Normal = 10,
  anon_sym_COMMA = 11,
  anon_sym_Temporary = 12,
  anon_sym_External = 13,
  anon_sym_System = 14,
  anon_sym_TableType = 15,
  anon_sym_EQ = 16,
  anon_sym_SEMI = 17,
  anon_sym_CustomerContent = 18,
  anon_sym_EndUserIdentifiableInformation = 19,
  anon_sym_AccountData = 20,
  anon_sym_EndUserPseudonymousIdentifiers = 21,
  anon_sym_OrganizationIdentifiableInformation = 22,
  anon_sym_SystemMetadata = 23,
  anon_sym_ToBeClassified = 24,
  anon_sym_trigger = 25,
  anon_sym_OnRun = 26,
  anon_sym_LPAREN_RPAREN = 27,
  anon_sym_Permissions = 28,
  sym_permission_type = 29,
  anon_sym_OnInsert = 30,
  anon_sym_OnModify = 31,
  anon_sym_OnDelete = 32,
  anon_sym_OnRename = 33,
  anon_sym_OnValidate = 34,
  anon_sym_OnAfterGetRecord = 35,
  anon_sym_OnAfterInsertEvent = 36,
  anon_sym_OnAfterModifyEvent = 37,
  anon_sym_OnAfterDeleteEvent = 38,
  anon_sym_OnBeforeInsertEvent = 39,
  anon_sym_OnBeforeModifyEvent = 40,
  anon_sym_OnBeforeDeleteEvent = 41,
  anon_sym_DOT = 42,
  anon_sym_TableNo = 43,
  anon_sym_Subtype = 44,
  anon_sym_SingleInstance = 45,
  anon_sym_DrillDownPageId = 46,
  anon_sym_LookupPageId = 47,
  anon_sym_TableRelation = 48,
  anon_sym_FieldClass = 49,
  anon_sym_CalcFormula = 50,
  anon_sym_BlankZero = 51,
  anon_sym_Editable = 52,
  anon_sym_OptionMembers = 53,
  anon_sym_OptionCaption = 54,
  anon_sym_DataClassification = 55,
  anon_sym_Caption = 56,
  anon_sym_tabledata = 57,
  anon_sym_DecimalPlaces = 58,
  anon_sym_COLON = 59,
  anon_sym_var = 60,
  anon_sym_List = 61,
  anon_sym_of = 62,
  anon_sym_LBRACK = 63,
  anon_sym_RBRACK = 64,
  anon_sym_Dictionary = 65,
  anon_sym_Integer = 66,
  anon_sym_BigInteger = 67,
  anon_sym_Decimal = 68,
  anon_sym_Byte = 69,
  anon_sym_Char = 70,
  anon_sym_Date = 71,
  anon_sym_Time = 72,
  anon_sym_DateTime = 73,
  anon_sym_Duration = 74,
  anon_sym_DateFormula = 75,
  anon_sym_Boolean = 76,
  anon_sym_Option = 77,
  anon_sym_Guid = 78,
  anon_sym_RecordId = 79,
  anon_sym_Variant = 80,
  anon_sym_Dialog = 81,
  anon_sym_Action = 82,
  anon_sym_Blob = 83,
  anon_sym_FilterPageBuilder = 84,
  anon_sym_JsonToken = 85,
  anon_sym_JsonValue = 86,
  anon_sym_JsonArray = 87,
  anon_sym_JsonObject = 88,
  anon_sym_Media = 89,
  anon_sym_MediaSet = 90,
  anon_sym_OStream = 91,
  anon_sym_InStream = 92,
  anon_sym_OutStream = 93,
  anon_sym_SecretText = 94,
  anon_sym_Label = 95,
  anon_sym_Text = 96,
  anon_sym_Code = 97,
  anon_sym_Record = 98,
  anon_sym_Codeunit = 99,
  anon_sym_Query = 100,
  anon_sym_DotNet = 101,
  anon_sym_array = 102,
  anon_sym_fields = 103,
  anon_sym_field = 104,
  anon_sym_LPAREN = 105,
  anon_sym_RPAREN = 106,
  anon_sym_where = 107,
  anon_sym_if = 108,
  anon_sym_else = 109,
  anon_sym_const = 110,
  anon_sym_filter = 111,
  anon_sym_lookup = 112,
  anon_sym_count = 113,
  anon_sym_sum = 114,
  anon_sym_average = 115,
  anon_sym_min = 116,
  anon_sym_max = 117,
  anon_sym_CONST = 118,
  anon_sym_FILTER = 119,
  anon_sym_FIELD = 120,
  anon_sym_UPPERLIMIT = 121,
  anon_sym_LT_GT = 122,
  anon_sym_LT_EQ = 123,
  anon_sym_GT_EQ = 124,
  anon_sym_LT = 125,
  anon_sym_GT = 126,
  anon_sym_IN = 127,
  anon_sym_OnLookup = 128,
  anon_sym_OnAssistEdit = 129,
  anon_sym_OnDrillDown = 130,
  anon_sym_keys = 131,
  anon_sym_key = 132,
  sym_procedure_modifier = 133,
  anon_sym_procedure = 134,
  anon_sym_PLUS = 135,
  anon_sym_DASH = 136,
  anon_sym_STAR = 137,
  anon_sym_SLASH = 138,
  sym_identifier = 139,
  anon_sym_DQUOTE = 140,
  aux_sym__quoted_identifier_token1 = 141,
  aux_sym__quoted_identifier_token2 = 142,
  aux_sym__quoted_identifier_token3 = 143,
  sym_integer = 144,
  sym_string_literal = 145,
  anon_sym_Clustered = 146,
  anon_sym_true = 147,
  anon_sym_false = 148,
  sym_temporary = 149,
  anon_sym_Enum = 150,
  anon_sym_begin = 151,
  anon_sym_end = 152,
  anon_sym_repeat = 153,
  anon_sym_until = 154,
  anon_sym_COLON_EQ = 155,
  anon_sym_COLON_COLON = 156,
  anon_sym_Get = 157,
  anon_sym_FindSet = 158,
  anon_sym_Insert = 159,
  anon_sym_Modify = 160,
  anon_sym_Delete = 161,
  anon_sym_SetRange = 162,
  anon_sym_SetFilter = 163,
  anon_sym_Reset = 164,
  anon_sym_then = 165,
  anon_sym_FindFirst = 166,
  anon_sym_FindLast = 167,
  anon_sym_Next = 168,
  anon_sym_case = 169,
  anon_sym_exit = 170,
  sym_source_file = 171,
  sym__object = 172,
  sym_function_call = 173,
  sym_object_id = 174,
  sym_object_name = 175,
  sym_table_declaration = 176,
  sym_codeunit_declaration = 177,
  sym_table_no_value = 178,
  sym_subtype_value = 179,
  sym_single_instance_value = 180,
  sym_page_id_value = 181,
  sym_permissions_value = 182,
  sym_field_class_value = 183,
  sym_calc_formula_value = 184,
  sym_blank_zero_value = 185,
  sym_editable_value = 186,
  sym_option_members_value = 187,
  sym_option_caption_value = 188,
  sym_table_type_value = 189,
  sym_table_type_property = 190,
  sym_data_classification_value = 191,
  sym__codeunit_element = 192,
  sym_onrun_trigger = 193,
  sym__table_element = 194,
  sym_permissions_property = 195,
  sym_oninsert_trigger = 196,
  sym_onmodify_trigger = 197,
  sym_ondelete_trigger = 198,
  sym_onrename_trigger = 199,
  sym_onvalidate_trigger = 200,
  sym_onaftergetrecord_trigger = 201,
  sym_onafterinsertevent_trigger = 202,
  sym_onaftermodifyevent_trigger = 203,
  sym_onafterdeleteevent_trigger = 204,
  sym_onbeforeinsertevent_trigger = 205,
  sym_onbeforemodifyevent_trigger = 206,
  sym_onbeforedeleteevent_trigger = 207,
  sym_member_access = 208,
  sym_method_call = 209,
  sym_property_list = 210,
  sym_property = 211,
  sym_caption_property = 212,
  sym_data_classification_property = 213,
  sym_tabledata_permission_list = 214,
  sym_tabledata_permission = 215,
  sym__table_identifier = 216,
  sym_drilldown_pageid_property = 217,
  sym_lookup_pageid_property = 218,
  sym_decimal_places_property = 219,
  sym_var_section = 220,
  sym_variable_declaration = 221,
  sym_type_specification = 222,
  sym_list_type = 223,
  sym_dictionary_type = 224,
  sym_basic_type = 225,
  sym_text_type = 226,
  sym_code_type = 227,
  sym_record_type = 228,
  sym__table_reference = 229,
  sym_codeunit_type = 230,
  sym_query_type = 231,
  sym_query_type_value = 232,
  sym_dotnet_type = 233,
  sym_array_type = 234,
  sym_fields = 235,
  sym_field_declaration = 236,
  sym_table_relation_property = 237,
  sym_table_relation_value = 238,
  sym__simple_table_relation = 239,
  sym__field_reference = 240,
  sym__condition_field_reference = 241,
  sym_conditional_table_relation = 242,
  sym__table_relation_body = 243,
  sym_table_relation_condition = 244,
  sym_field_class_property = 245,
  sym_calc_formula_property = 246,
  sym__calc_formula_expression = 247,
  sym_lookup_formula = 248,
  sym_lookup_where_conditions = 249,
  sym_lookup_where_condition = 250,
  sym_count_formula = 251,
  sym_sum_formula = 252,
  sym_average_formula = 253,
  sym_min_formula = 254,
  sym_max_formula = 255,
  sym_field_reference = 256,
  sym_where_clause = 257,
  sym_where_conditions = 258,
  sym_where_condition = 259,
  sym_filter_conditions = 260,
  sym_filter_condition = 261,
  sym_filter_operator = 262,
  sym_blank_zero_property = 263,
  sym_editable_property = 264,
  sym_option_members_property = 265,
  sym_option_member = 266,
  sym_option_caption_property = 267,
  sym_field_trigger_declaration = 268,
  sym_keys = 269,
  sym_key_declaration = 270,
  sym_key_field = 271,
  sym_key_field_list = 272,
  sym_attribute_list = 273,
  sym_attribute = 274,
  sym_attribute_arguments = 275,
  sym_expression_list = 276,
  sym_return_value = 277,
  sym__procedure_return_specification = 278,
  sym_return_type = 279,
  sym__procedure_name = 280,
  sym_procedure = 281,
  sym_comparison_operator = 282,
  sym_arithmetic_operator = 283,
  sym_parameter_list = 284,
  sym_modifier = 285,
  sym_parameter = 286,
  sym__quoted_identifier = 287,
  sym_clustered_property = 288,
  sym_boolean = 289,
  sym_data_type = 290,
  sym_code_block = 291,
  sym__statement = 292,
  sym_repeat_statement = 293,
  sym_assignment_statement = 294,
  sym__assignable_expression = 295,
  sym_argument_list = 296,
  sym__primary_expression = 297,
  sym_enum_member_access = 298,
  sym__expression = 299,
  sym_procedure_call = 300,
  sym_get_method = 301,
  sym_find_set_method = 302,
  sym_insert_statement = 303,
  sym_modify_statement = 304,
  sym_delete_statement = 305,
  sym_set_range_statement = 306,
  sym_set_filter_statement = 307,
  sym_reset_statement = 308,
  sym_binary_expression = 309,
  sym_if_statement = 310,
  sym_get_statement = 311,
  sym_find_set_statement = 312,
  sym_find_first_statement = 313,
  sym_find_last_statement = 314,
  sym_next_statement = 315,
  sym_case_statement = 316,
  sym_case_clause = 317,
  sym_value_set = 318,
  sym_else_clause = 319,
  sym_exit_statement = 320,
  aux_sym_source_file_repeat1 = 321,
  aux_sym_table_declaration_repeat1 = 322,
  aux_sym_codeunit_declaration_repeat1 = 323,
  aux_sym_option_members_value_repeat1 = 324,
  aux_sym_property_list_repeat1 = 325,
  aux_sym_var_section_repeat1 = 326,
  aux_sym_fields_repeat1 = 327,
  aux_sym_field_declaration_repeat1 = 328,
  aux_sym_lookup_where_conditions_repeat1 = 329,
  aux_sym_where_conditions_repeat1 = 330,
  aux_sym_filter_conditions_repeat1 = 331,
  aux_sym_keys_repeat1 = 332,
  aux_sym_key_declaration_repeat1 = 333,
  aux_sym_key_field_list_repeat1 = 334,
  aux_sym_attribute_list_repeat1 = 335,
  aux_sym_expression_list_repeat1 = 336,
  aux_sym_parameter_list_repeat1 = 337,
  aux_sym__quoted_identifier_repeat1 = 338,
  aux_sym_code_block_repeat1 = 339,
  aux_sym_set_filter_statement_repeat1 = 340,
  aux_sym_case_statement_repeat1 = 341,
  alias_sym_const = 342,
  alias_sym_field = 343,
  alias_sym_field_ref = 344,
  alias_sym_member = 345,
  alias_sym_method_name = 346,
  alias_sym_name = 347,
  alias_sym_record = 348,
  alias_sym_table = 349,
  alias_sym_table_reference = 350,
};

static const char * const ts_symbol_names[] = {
  [ts_builtin_sym_end] = "end",
  [anon_sym_table] = "table",
  [anon_sym_LBRACE] = "{",
  [anon_sym_RBRACE] = "}",
  [anon_sym_codeunit] = "codeunit",
  [anon_sym_Install] = "Install",
  [anon_sym_Upgrade] = "Upgrade",
  [anon_sym_Test] = "Test",
  [anon_sym_FlowField] = "FlowField",
  [anon_sym_FlowFilter] = "FlowFilter",
  [anon_sym_Normal] = "Normal",
  [anon_sym_COMMA] = ",",
  [anon_sym_Temporary] = "Temporary",
  [anon_sym_External] = "External",
  [anon_sym_System] = "System",
  [anon_sym_TableType] = "TableType",
  [anon_sym_EQ] = "=",
  [anon_sym_SEMI] = ";",
  [anon_sym_CustomerContent] = "CustomerContent",
  [anon_sym_EndUserIdentifiableInformation] = "EndUserIdentifiableInformation",
  [anon_sym_AccountData] = "AccountData",
  [anon_sym_EndUserPseudonymousIdentifiers] = "EndUserPseudonymousIdentifiers",
  [anon_sym_OrganizationIdentifiableInformation] = "OrganizationIdentifiableInformation",
  [anon_sym_SystemMetadata] = "SystemMetadata",
  [anon_sym_ToBeClassified] = "ToBeClassified",
  [anon_sym_trigger] = "trigger",
  [anon_sym_OnRun] = "OnRun",
  [anon_sym_LPAREN_RPAREN] = "()",
  [anon_sym_Permissions] = "Permissions",
  [sym_permission_type] = "permission_type",
  [anon_sym_OnInsert] = "OnInsert",
  [anon_sym_OnModify] = "OnModify",
  [anon_sym_OnDelete] = "OnDelete",
  [anon_sym_OnRename] = "OnRename",
  [anon_sym_OnValidate] = "OnValidate",
  [anon_sym_OnAfterGetRecord] = "OnAfterGetRecord",
  [anon_sym_OnAfterInsertEvent] = "OnAfterInsertEvent",
  [anon_sym_OnAfterModifyEvent] = "OnAfterModifyEvent",
  [anon_sym_OnAfterDeleteEvent] = "OnAfterDeleteEvent",
  [anon_sym_OnBeforeInsertEvent] = "OnBeforeInsertEvent",
  [anon_sym_OnBeforeModifyEvent] = "OnBeforeModifyEvent",
  [anon_sym_OnBeforeDeleteEvent] = "OnBeforeDeleteEvent",
  [anon_sym_DOT] = ".",
  [anon_sym_TableNo] = "TableNo",
  [anon_sym_Subtype] = "Subtype",
  [anon_sym_SingleInstance] = "SingleInstance",
  [anon_sym_DrillDownPageId] = "DrillDownPageId",
  [anon_sym_LookupPageId] = "LookupPageId",
  [anon_sym_TableRelation] = "TableRelation",
  [anon_sym_FieldClass] = "FieldClass",
  [anon_sym_CalcFormula] = "CalcFormula",
  [anon_sym_BlankZero] = "BlankZero",
  [anon_sym_Editable] = "Editable",
  [anon_sym_OptionMembers] = "OptionMembers",
  [anon_sym_OptionCaption] = "OptionCaption",
  [anon_sym_DataClassification] = "DataClassification",
  [anon_sym_Caption] = "Caption",
  [anon_sym_tabledata] = "tabledata",
  [anon_sym_DecimalPlaces] = "DecimalPlaces",
  [anon_sym_COLON] = ":",
  [anon_sym_var] = "var",
  [anon_sym_List] = "List",
  [anon_sym_of] = "of",
  [anon_sym_LBRACK] = "[",
  [anon_sym_RBRACK] = "]",
  [anon_sym_Dictionary] = "Dictionary",
  [anon_sym_Integer] = "Integer",
  [anon_sym_BigInteger] = "BigInteger",
  [anon_sym_Decimal] = "Decimal",
  [anon_sym_Byte] = "Byte",
  [anon_sym_Char] = "Char",
  [anon_sym_Date] = "Date",
  [anon_sym_Time] = "Time",
  [anon_sym_DateTime] = "DateTime",
  [anon_sym_Duration] = "Duration",
  [anon_sym_DateFormula] = "DateFormula",
  [anon_sym_Boolean] = "Boolean",
  [anon_sym_Option] = "Option",
  [anon_sym_Guid] = "Guid",
  [anon_sym_RecordId] = "RecordId",
  [anon_sym_Variant] = "Variant",
  [anon_sym_Dialog] = "Dialog",
  [anon_sym_Action] = "Action",
  [anon_sym_Blob] = "Blob",
  [anon_sym_FilterPageBuilder] = "FilterPageBuilder",
  [anon_sym_JsonToken] = "JsonToken",
  [anon_sym_JsonValue] = "JsonValue",
  [anon_sym_JsonArray] = "JsonArray",
  [anon_sym_JsonObject] = "JsonObject",
  [anon_sym_Media] = "Media",
  [anon_sym_MediaSet] = "MediaSet",
  [anon_sym_OStream] = "OStream",
  [anon_sym_InStream] = "InStream",
  [anon_sym_OutStream] = "OutStream",
  [anon_sym_SecretText] = "SecretText",
  [anon_sym_Label] = "Label",
  [anon_sym_Text] = "Text",
  [anon_sym_Code] = "Code",
  [anon_sym_Record] = "Record",
  [anon_sym_Codeunit] = "Codeunit",
  [anon_sym_Query] = "Query",
  [anon_sym_DotNet] = "DotNet",
  [anon_sym_array] = "array",
  [anon_sym_fields] = "fields",
  [anon_sym_field] = "field",
  [anon_sym_LPAREN] = "(",
  [anon_sym_RPAREN] = ")",
  [anon_sym_where] = "where",
  [anon_sym_if] = "if",
  [anon_sym_else] = "else",
  [anon_sym_const] = "const",
  [anon_sym_filter] = "filter",
  [anon_sym_lookup] = "lookup",
  [anon_sym_count] = "count",
  [anon_sym_sum] = "sum",
  [anon_sym_average] = "average",
  [anon_sym_min] = "min",
  [anon_sym_max] = "max",
  [anon_sym_CONST] = "CONST",
  [anon_sym_FILTER] = "FILTER",
  [anon_sym_FIELD] = "FIELD",
  [anon_sym_UPPERLIMIT] = "UPPERLIMIT",
  [anon_sym_LT_GT] = "<>",
  [anon_sym_LT_EQ] = "<=",
  [anon_sym_GT_EQ] = ">=",
  [anon_sym_LT] = "<",
  [anon_sym_GT] = ">",
  [anon_sym_IN] = "IN",
  [anon_sym_OnLookup] = "OnLookup",
  [anon_sym_OnAssistEdit] = "OnAssistEdit",
  [anon_sym_OnDrillDown] = "OnDrillDown",
  [anon_sym_keys] = "keys",
  [anon_sym_key] = "key",
  [sym_procedure_modifier] = "procedure_modifier",
  [anon_sym_procedure] = "procedure",
  [anon_sym_PLUS] = "+",
  [anon_sym_DASH] = "-",
  [anon_sym_STAR] = "*",
  [anon_sym_SLASH] = "/",
  [sym_identifier] = "identifier",
  [anon_sym_DQUOTE] = "\"",
  [aux_sym__quoted_identifier_token1] = "_quoted_identifier_token1",
  [aux_sym__quoted_identifier_token2] = "_quoted_identifier_token2",
  [aux_sym__quoted_identifier_token3] = "_quoted_identifier_token3",
  [sym_integer] = "integer",
  [sym_string_literal] = "string_literal",
  [anon_sym_Clustered] = "Clustered",
  [anon_sym_true] = "true",
  [anon_sym_false] = "false",
  [sym_temporary] = "temporary",
  [anon_sym_Enum] = "Enum",
  [anon_sym_begin] = "begin",
  [anon_sym_end] = "end",
  [anon_sym_repeat] = "repeat",
  [anon_sym_until] = "until",
  [anon_sym_COLON_EQ] = ":=",
  [anon_sym_COLON_COLON] = "::",
  [anon_sym_Get] = "Get",
  [anon_sym_FindSet] = "FindSet",
  [anon_sym_Insert] = "Insert",
  [anon_sym_Modify] = "Modify",
  [anon_sym_Delete] = "Delete",
  [anon_sym_SetRange] = "SetRange",
  [anon_sym_SetFilter] = "SetFilter",
  [anon_sym_Reset] = "Reset",
  [anon_sym_then] = "then",
  [anon_sym_FindFirst] = "FindFirst",
  [anon_sym_FindLast] = "FindLast",
  [anon_sym_Next] = "Next",
  [anon_sym_case] = "case",
  [anon_sym_exit] = "exit",
  [sym_source_file] = "source_file",
  [sym__object] = "_object",
  [sym_function_call] = "function_call",
  [sym_object_id] = "object_id",
  [sym_object_name] = "object_name",
  [sym_table_declaration] = "table_declaration",
  [sym_codeunit_declaration] = "codeunit_declaration",
  [sym_table_no_value] = "table_no_value",
  [sym_subtype_value] = "subtype_value",
  [sym_single_instance_value] = "single_instance_value",
  [sym_page_id_value] = "page_id_value",
  [sym_permissions_value] = "permissions_value",
  [sym_field_class_value] = "field_class_value",
  [sym_calc_formula_value] = "calc_formula_value",
  [sym_blank_zero_value] = "blank_zero_value",
  [sym_editable_value] = "editable_value",
  [sym_option_members_value] = "option_members_value",
  [sym_option_caption_value] = "option_caption_value",
  [sym_table_type_value] = "table_type_value",
  [sym_table_type_property] = "table_type_property",
  [sym_data_classification_value] = "data_classification_value",
  [sym__codeunit_element] = "_codeunit_element",
  [sym_onrun_trigger] = "onrun_trigger",
  [sym__table_element] = "_table_element",
  [sym_permissions_property] = "permissions_property",
  [sym_oninsert_trigger] = "oninsert_trigger",
  [sym_onmodify_trigger] = "onmodify_trigger",
  [sym_ondelete_trigger] = "ondelete_trigger",
  [sym_onrename_trigger] = "onrename_trigger",
  [sym_onvalidate_trigger] = "onvalidate_trigger",
  [sym_onaftergetrecord_trigger] = "onaftergetrecord_trigger",
  [sym_onafterinsertevent_trigger] = "onafterinsertevent_trigger",
  [sym_onaftermodifyevent_trigger] = "onaftermodifyevent_trigger",
  [sym_onafterdeleteevent_trigger] = "onafterdeleteevent_trigger",
  [sym_onbeforeinsertevent_trigger] = "onbeforeinsertevent_trigger",
  [sym_onbeforemodifyevent_trigger] = "onbeforemodifyevent_trigger",
  [sym_onbeforedeleteevent_trigger] = "onbeforedeleteevent_trigger",
  [sym_member_access] = "member_access",
  [sym_method_call] = "method_call",
  [sym_property_list] = "property_list",
  [sym_property] = "property",
  [sym_caption_property] = "caption_property",
  [sym_data_classification_property] = "data_classification_property",
  [sym_tabledata_permission_list] = "tabledata_permission_list",
  [sym_tabledata_permission] = "tabledata_permission",
  [sym__table_identifier] = "_table_identifier",
  [sym_drilldown_pageid_property] = "drilldown_pageid_property",
  [sym_lookup_pageid_property] = "lookup_pageid_property",
  [sym_decimal_places_property] = "decimal_places_property",
  [sym_var_section] = "var_section",
  [sym_variable_declaration] = "variable_declaration",
  [sym_type_specification] = "type_specification",
  [sym_list_type] = "list_type",
  [sym_dictionary_type] = "dictionary_type",
  [sym_basic_type] = "basic_type",
  [sym_text_type] = "text_type",
  [sym_code_type] = "type",
  [sym_record_type] = "record_type",
  [sym__table_reference] = "_table_reference",
  [sym_codeunit_type] = "codeunit_type",
  [sym_query_type] = "query_type",
  [sym_query_type_value] = "query_type_value",
  [sym_dotnet_type] = "dotnet_type",
  [sym_array_type] = "array_type",
  [sym_fields] = "fields",
  [sym_field_declaration] = "field_declaration",
  [sym_table_relation_property] = "table_relation_property",
  [sym_table_relation_value] = "table_relation_value",
  [sym__simple_table_relation] = "_simple_table_relation",
  [sym__field_reference] = "_field_reference",
  [sym__condition_field_reference] = "_condition_field_reference",
  [sym_conditional_table_relation] = "conditional_table_relation",
  [sym__table_relation_body] = "_table_relation_body",
  [sym_table_relation_condition] = "table_relation_condition",
  [sym_field_class_property] = "field_class_property",
  [sym_calc_formula_property] = "calc_formula_property",
  [sym__calc_formula_expression] = "_calc_formula_expression",
  [sym_lookup_formula] = "lookup_formula",
  [sym_lookup_where_conditions] = "lookup_where_conditions",
  [sym_lookup_where_condition] = "lookup_where_condition",
  [sym_count_formula] = "count_formula",
  [sym_sum_formula] = "sum_formula",
  [sym_average_formula] = "average_formula",
  [sym_min_formula] = "min_formula",
  [sym_max_formula] = "max_formula",
  [sym_field_reference] = "field_reference",
  [sym_where_clause] = "where_clause",
  [sym_where_conditions] = "where_conditions",
  [sym_where_condition] = "where_condition",
  [sym_filter_conditions] = "filter_conditions",
  [sym_filter_condition] = "filter_condition",
  [sym_filter_operator] = "filter_operator",
  [sym_blank_zero_property] = "blank_zero_property",
  [sym_editable_property] = "editable_property",
  [sym_option_members_property] = "option_members_property",
  [sym_option_member] = "option_member",
  [sym_option_caption_property] = "option_caption_property",
  [sym_field_trigger_declaration] = "field_trigger_declaration",
  [sym_keys] = "keys",
  [sym_key_declaration] = "key_declaration",
  [sym_key_field] = "key_field",
  [sym_key_field_list] = "key_field_list",
  [sym_attribute_list] = "attribute_list",
  [sym_attribute] = "attribute",
  [sym_attribute_arguments] = "attribute_arguments",
  [sym_expression_list] = "expression_list",
  [sym_return_value] = "return_value",
  [sym__procedure_return_specification] = "_procedure_return_specification",
  [sym_return_type] = "return_type",
  [sym__procedure_name] = "_procedure_name",
  [sym_procedure] = "procedure",
  [sym_comparison_operator] = "comparison_operator",
  [sym_arithmetic_operator] = "arithmetic_operator",
  [sym_parameter_list] = "parameter_list",
  [sym_modifier] = "modifier",
  [sym_parameter] = "parameter",
  [sym__quoted_identifier] = "_quoted_identifier",
  [sym_clustered_property] = "clustered_property",
  [sym_boolean] = "boolean",
  [sym_data_type] = "data_type",
  [sym_code_block] = "code_block",
  [sym__statement] = "_statement",
  [sym_repeat_statement] = "repeat_statement",
  [sym_assignment_statement] = "assignment_statement",
  [sym__assignable_expression] = "_assignable_expression",
  [sym_argument_list] = "argument_list",
  [sym__primary_expression] = "_primary_expression",
  [sym_enum_member_access] = "enum_member_access",
  [sym__expression] = "_expression",
  [sym_procedure_call] = "procedure_call",
  [sym_get_method] = "get_method",
  [sym_find_set_method] = "find_set_method",
  [sym_insert_statement] = "insert_statement",
  [sym_modify_statement] = "modify_statement",
  [sym_delete_statement] = "delete_statement",
  [sym_set_range_statement] = "set_range_statement",
  [sym_set_filter_statement] = "set_filter_statement",
  [sym_reset_statement] = "reset_statement",
  [sym_binary_expression] = "binary_expression",
  [sym_if_statement] = "if_statement",
  [sym_get_statement] = "get_statement",
  [sym_find_set_statement] = "find_set_statement",
  [sym_find_first_statement] = "find_first_statement",
  [sym_find_last_statement] = "find_last_statement",
  [sym_next_statement] = "next_statement",
  [sym_case_statement] = "case_statement",
  [sym_case_clause] = "case_clause",
  [sym_value_set] = "value_set",
  [sym_else_clause] = "else_clause",
  [sym_exit_statement] = "exit_statement",
  [aux_sym_source_file_repeat1] = "source_file_repeat1",
  [aux_sym_table_declaration_repeat1] = "table_declaration_repeat1",
  [aux_sym_codeunit_declaration_repeat1] = "codeunit_declaration_repeat1",
  [aux_sym_option_members_value_repeat1] = "option_members_value_repeat1",
  [aux_sym_property_list_repeat1] = "property_list_repeat1",
  [aux_sym_var_section_repeat1] = "var_section_repeat1",
  [aux_sym_fields_repeat1] = "fields_repeat1",
  [aux_sym_field_declaration_repeat1] = "field_declaration_repeat1",
  [aux_sym_lookup_where_conditions_repeat1] = "lookup_where_conditions_repeat1",
  [aux_sym_where_conditions_repeat1] = "where_conditions_repeat1",
  [aux_sym_filter_conditions_repeat1] = "filter_conditions_repeat1",
  [aux_sym_keys_repeat1] = "keys_repeat1",
  [aux_sym_key_declaration_repeat1] = "key_declaration_repeat1",
  [aux_sym_key_field_list_repeat1] = "key_field_list_repeat1",
  [aux_sym_attribute_list_repeat1] = "attribute_list_repeat1",
  [aux_sym_expression_list_repeat1] = "expression_list_repeat1",
  [aux_sym_parameter_list_repeat1] = "parameter_list_repeat1",
  [aux_sym__quoted_identifier_repeat1] = "_quoted_identifier_repeat1",
  [aux_sym_code_block_repeat1] = "code_block_repeat1",
  [aux_sym_set_filter_statement_repeat1] = "set_filter_statement_repeat1",
  [aux_sym_case_statement_repeat1] = "case_statement_repeat1",
  [alias_sym_const] = "const",
  [alias_sym_field] = "field",
  [alias_sym_field_ref] = "field_ref",
  [alias_sym_member] = "member",
  [alias_sym_method_name] = "method_name",
  [alias_sym_name] = "name",
  [alias_sym_record] = "record",
  [alias_sym_table] = "table",
  [alias_sym_table_reference] = "table_reference",
};

static const TSSymbol ts_symbol_map[] = {
  [ts_builtin_sym_end] = ts_builtin_sym_end,
  [anon_sym_table] = anon_sym_table,
  [anon_sym_LBRACE] = anon_sym_LBRACE,
  [anon_sym_RBRACE] = anon_sym_RBRACE,
  [anon_sym_codeunit] = anon_sym_codeunit,
  [anon_sym_Install] = anon_sym_Install,
  [anon_sym_Upgrade] = anon_sym_Upgrade,
  [anon_sym_Test] = anon_sym_Test,
  [anon_sym_FlowField] = anon_sym_FlowField,
  [anon_sym_FlowFilter] = anon_sym_FlowFilter,
  [anon_sym_Normal] = anon_sym_Normal,
  [anon_sym_COMMA] = anon_sym_COMMA,
  [anon_sym_Temporary] = anon_sym_Temporary,
  [anon_sym_External] = anon_sym_External,
  [anon_sym_System] = anon_sym_System,
  [anon_sym_TableType] = anon_sym_TableType,
  [anon_sym_EQ] = anon_sym_EQ,
  [anon_sym_SEMI] = anon_sym_SEMI,
  [anon_sym_CustomerContent] = anon_sym_CustomerContent,
  [anon_sym_EndUserIdentifiableInformation] = anon_sym_EndUserIdentifiableInformation,
  [anon_sym_AccountData] = anon_sym_AccountData,
  [anon_sym_EndUserPseudonymousIdentifiers] = anon_sym_EndUserPseudonymousIdentifiers,
  [anon_sym_OrganizationIdentifiableInformation] = anon_sym_OrganizationIdentifiableInformation,
  [anon_sym_SystemMetadata] = anon_sym_SystemMetadata,
  [anon_sym_ToBeClassified] = anon_sym_ToBeClassified,
  [anon_sym_trigger] = anon_sym_trigger,
  [anon_sym_OnRun] = anon_sym_OnRun,
  [anon_sym_LPAREN_RPAREN] = anon_sym_LPAREN_RPAREN,
  [anon_sym_Permissions] = anon_sym_Permissions,
  [sym_permission_type] = sym_permission_type,
  [anon_sym_OnInsert] = anon_sym_OnInsert,
  [anon_sym_OnModify] = anon_sym_OnModify,
  [anon_sym_OnDelete] = anon_sym_OnDelete,
  [anon_sym_OnRename] = anon_sym_OnRename,
  [anon_sym_OnValidate] = anon_sym_OnValidate,
  [anon_sym_OnAfterGetRecord] = anon_sym_OnAfterGetRecord,
  [anon_sym_OnAfterInsertEvent] = anon_sym_OnAfterInsertEvent,
  [anon_sym_OnAfterModifyEvent] = anon_sym_OnAfterModifyEvent,
  [anon_sym_OnAfterDeleteEvent] = anon_sym_OnAfterDeleteEvent,
  [anon_sym_OnBeforeInsertEvent] = anon_sym_OnBeforeInsertEvent,
  [anon_sym_OnBeforeModifyEvent] = anon_sym_OnBeforeModifyEvent,
  [anon_sym_OnBeforeDeleteEvent] = anon_sym_OnBeforeDeleteEvent,
  [anon_sym_DOT] = anon_sym_DOT,
  [anon_sym_TableNo] = anon_sym_TableNo,
  [anon_sym_Subtype] = anon_sym_Subtype,
  [anon_sym_SingleInstance] = anon_sym_SingleInstance,
  [anon_sym_DrillDownPageId] = anon_sym_DrillDownPageId,
  [anon_sym_LookupPageId] = anon_sym_LookupPageId,
  [anon_sym_TableRelation] = anon_sym_TableRelation,
  [anon_sym_FieldClass] = anon_sym_FieldClass,
  [anon_sym_CalcFormula] = anon_sym_CalcFormula,
  [anon_sym_BlankZero] = anon_sym_BlankZero,
  [anon_sym_Editable] = anon_sym_Editable,
  [anon_sym_OptionMembers] = anon_sym_OptionMembers,
  [anon_sym_OptionCaption] = anon_sym_OptionCaption,
  [anon_sym_DataClassification] = anon_sym_DataClassification,
  [anon_sym_Caption] = anon_sym_Caption,
  [anon_sym_tabledata] = anon_sym_tabledata,
  [anon_sym_DecimalPlaces] = anon_sym_DecimalPlaces,
  [anon_sym_COLON] = anon_sym_COLON,
  [anon_sym_var] = anon_sym_var,
  [anon_sym_List] = anon_sym_List,
  [anon_sym_of] = anon_sym_of,
  [anon_sym_LBRACK] = anon_sym_LBRACK,
  [anon_sym_RBRACK] = anon_sym_RBRACK,
  [anon_sym_Dictionary] = anon_sym_Dictionary,
  [anon_sym_Integer] = anon_sym_Integer,
  [anon_sym_BigInteger] = anon_sym_BigInteger,
  [anon_sym_Decimal] = anon_sym_Decimal,
  [anon_sym_Byte] = anon_sym_Byte,
  [anon_sym_Char] = anon_sym_Char,
  [anon_sym_Date] = anon_sym_Date,
  [anon_sym_Time] = anon_sym_Time,
  [anon_sym_DateTime] = anon_sym_DateTime,
  [anon_sym_Duration] = anon_sym_Duration,
  [anon_sym_DateFormula] = anon_sym_DateFormula,
  [anon_sym_Boolean] = anon_sym_Boolean,
  [anon_sym_Option] = anon_sym_Option,
  [anon_sym_Guid] = anon_sym_Guid,
  [anon_sym_RecordId] = anon_sym_RecordId,
  [anon_sym_Variant] = anon_sym_Variant,
  [anon_sym_Dialog] = anon_sym_Dialog,
  [anon_sym_Action] = anon_sym_Action,
  [anon_sym_Blob] = anon_sym_Blob,
  [anon_sym_FilterPageBuilder] = anon_sym_FilterPageBuilder,
  [anon_sym_JsonToken] = anon_sym_JsonToken,
  [anon_sym_JsonValue] = anon_sym_JsonValue,
  [anon_sym_JsonArray] = anon_sym_JsonArray,
  [anon_sym_JsonObject] = anon_sym_JsonObject,
  [anon_sym_Media] = anon_sym_Media,
  [anon_sym_MediaSet] = anon_sym_MediaSet,
  [anon_sym_OStream] = anon_sym_OStream,
  [anon_sym_InStream] = anon_sym_InStream,
  [anon_sym_OutStream] = anon_sym_OutStream,
  [anon_sym_SecretText] = anon_sym_SecretText,
  [anon_sym_Label] = anon_sym_Label,
  [anon_sym_Text] = anon_sym_Text,
  [anon_sym_Code] = anon_sym_Code,
  [anon_sym_Record] = anon_sym_Record,
  [anon_sym_Codeunit] = anon_sym_Codeunit,
  [anon_sym_Query] = anon_sym_Query,
  [anon_sym_DotNet] = anon_sym_DotNet,
  [anon_sym_array] = anon_sym_array,
  [anon_sym_fields] = anon_sym_fields,
  [anon_sym_field] = anon_sym_field,
  [anon_sym_LPAREN] = anon_sym_LPAREN,
  [anon_sym_RPAREN] = anon_sym_RPAREN,
  [anon_sym_where] = anon_sym_where,
  [anon_sym_if] = anon_sym_if,
  [anon_sym_else] = anon_sym_else,
  [anon_sym_const] = anon_sym_const,
  [anon_sym_filter] = anon_sym_filter,
  [anon_sym_lookup] = anon_sym_lookup,
  [anon_sym_count] = anon_sym_count,
  [anon_sym_sum] = anon_sym_sum,
  [anon_sym_average] = anon_sym_average,
  [anon_sym_min] = anon_sym_min,
  [anon_sym_max] = anon_sym_max,
  [anon_sym_CONST] = anon_sym_CONST,
  [anon_sym_FILTER] = anon_sym_FILTER,
  [anon_sym_FIELD] = anon_sym_FIELD,
  [anon_sym_UPPERLIMIT] = anon_sym_UPPERLIMIT,
  [anon_sym_LT_GT] = anon_sym_LT_GT,
  [anon_sym_LT_EQ] = anon_sym_LT_EQ,
  [anon_sym_GT_EQ] = anon_sym_GT_EQ,
  [anon_sym_LT] = anon_sym_LT,
  [anon_sym_GT] = anon_sym_GT,
  [anon_sym_IN] = anon_sym_IN,
  [anon_sym_OnLookup] = anon_sym_OnLookup,
  [anon_sym_OnAssistEdit] = anon_sym_OnAssistEdit,
  [anon_sym_OnDrillDown] = anon_sym_OnDrillDown,
  [anon_sym_keys] = anon_sym_keys,
  [anon_sym_key] = anon_sym_key,
  [sym_procedure_modifier] = sym_procedure_modifier,
  [anon_sym_procedure] = anon_sym_procedure,
  [anon_sym_PLUS] = anon_sym_PLUS,
  [anon_sym_DASH] = anon_sym_DASH,
  [anon_sym_STAR] = anon_sym_STAR,
  [anon_sym_SLASH] = anon_sym_SLASH,
  [sym_identifier] = sym_identifier,
  [anon_sym_DQUOTE] = anon_sym_DQUOTE,
  [aux_sym__quoted_identifier_token1] = aux_sym__quoted_identifier_token1,
  [aux_sym__quoted_identifier_token2] = aux_sym__quoted_identifier_token2,
  [aux_sym__quoted_identifier_token3] = aux_sym__quoted_identifier_token3,
  [sym_integer] = sym_integer,
  [sym_string_literal] = sym_string_literal,
  [anon_sym_Clustered] = anon_sym_Clustered,
  [anon_sym_true] = anon_sym_true,
  [anon_sym_false] = anon_sym_false,
  [sym_temporary] = sym_temporary,
  [anon_sym_Enum] = anon_sym_Enum,
  [anon_sym_begin] = anon_sym_begin,
  [anon_sym_end] = anon_sym_end,
  [anon_sym_repeat] = anon_sym_repeat,
  [anon_sym_until] = anon_sym_until,
  [anon_sym_COLON_EQ] = anon_sym_COLON_EQ,
  [anon_sym_COLON_COLON] = anon_sym_COLON_COLON,
  [anon_sym_Get] = anon_sym_Get,
  [anon_sym_FindSet] = anon_sym_FindSet,
  [anon_sym_Insert] = anon_sym_Insert,
  [anon_sym_Modify] = anon_sym_Modify,
  [anon_sym_Delete] = anon_sym_Delete,
  [anon_sym_SetRange] = anon_sym_SetRange,
  [anon_sym_SetFilter] = anon_sym_SetFilter,
  [anon_sym_Reset] = anon_sym_Reset,
  [anon_sym_then] = anon_sym_then,
  [anon_sym_FindFirst] = anon_sym_FindFirst,
  [anon_sym_FindLast] = anon_sym_FindLast,
  [anon_sym_Next] = anon_sym_Next,
  [anon_sym_case] = anon_sym_case,
  [anon_sym_exit] = anon_sym_exit,
  [sym_source_file] = sym_source_file,
  [sym__object] = sym__object,
  [sym_function_call] = sym_function_call,
  [sym_object_id] = sym_object_id,
  [sym_object_name] = sym_object_name,
  [sym_table_declaration] = sym_table_declaration,
  [sym_codeunit_declaration] = sym_codeunit_declaration,
  [sym_table_no_value] = sym_table_no_value,
  [sym_subtype_value] = sym_subtype_value,
  [sym_single_instance_value] = sym_single_instance_value,
  [sym_page_id_value] = sym_page_id_value,
  [sym_permissions_value] = sym_permissions_value,
  [sym_field_class_value] = sym_field_class_value,
  [sym_calc_formula_value] = sym_calc_formula_value,
  [sym_blank_zero_value] = sym_blank_zero_value,
  [sym_editable_value] = sym_editable_value,
  [sym_option_members_value] = sym_option_members_value,
  [sym_option_caption_value] = sym_option_caption_value,
  [sym_table_type_value] = sym_table_type_value,
  [sym_table_type_property] = sym_table_type_property,
  [sym_data_classification_value] = sym_data_classification_value,
  [sym__codeunit_element] = sym__codeunit_element,
  [sym_onrun_trigger] = sym_onrun_trigger,
  [sym__table_element] = sym__table_element,
  [sym_permissions_property] = sym_permissions_property,
  [sym_oninsert_trigger] = sym_oninsert_trigger,
  [sym_onmodify_trigger] = sym_onmodify_trigger,
  [sym_ondelete_trigger] = sym_ondelete_trigger,
  [sym_onrename_trigger] = sym_onrename_trigger,
  [sym_onvalidate_trigger] = sym_onvalidate_trigger,
  [sym_onaftergetrecord_trigger] = sym_onaftergetrecord_trigger,
  [sym_onafterinsertevent_trigger] = sym_onafterinsertevent_trigger,
  [sym_onaftermodifyevent_trigger] = sym_onaftermodifyevent_trigger,
  [sym_onafterdeleteevent_trigger] = sym_onafterdeleteevent_trigger,
  [sym_onbeforeinsertevent_trigger] = sym_onbeforeinsertevent_trigger,
  [sym_onbeforemodifyevent_trigger] = sym_onbeforemodifyevent_trigger,
  [sym_onbeforedeleteevent_trigger] = sym_onbeforedeleteevent_trigger,
  [sym_member_access] = sym_member_access,
  [sym_method_call] = sym_method_call,
  [sym_property_list] = sym_property_list,
  [sym_property] = sym_property,
  [sym_caption_property] = sym_caption_property,
  [sym_data_classification_property] = sym_data_classification_property,
  [sym_tabledata_permission_list] = sym_tabledata_permission_list,
  [sym_tabledata_permission] = sym_tabledata_permission,
  [sym__table_identifier] = sym__table_identifier,
  [sym_drilldown_pageid_property] = sym_drilldown_pageid_property,
  [sym_lookup_pageid_property] = sym_lookup_pageid_property,
  [sym_decimal_places_property] = sym_decimal_places_property,
  [sym_var_section] = sym_var_section,
  [sym_variable_declaration] = sym_variable_declaration,
  [sym_type_specification] = sym_type_specification,
  [sym_list_type] = sym_list_type,
  [sym_dictionary_type] = sym_dictionary_type,
  [sym_basic_type] = sym_basic_type,
  [sym_text_type] = sym_text_type,
  [sym_code_type] = sym_code_type,
  [sym_record_type] = sym_record_type,
  [sym__table_reference] = sym__table_reference,
  [sym_codeunit_type] = sym_codeunit_type,
  [sym_query_type] = sym_query_type,
  [sym_query_type_value] = sym_query_type_value,
  [sym_dotnet_type] = sym_dotnet_type,
  [sym_array_type] = sym_array_type,
  [sym_fields] = sym_fields,
  [sym_field_declaration] = sym_field_declaration,
  [sym_table_relation_property] = sym_table_relation_property,
  [sym_table_relation_value] = sym_table_relation_value,
  [sym__simple_table_relation] = sym__simple_table_relation,
  [sym__field_reference] = sym__field_reference,
  [sym__condition_field_reference] = sym__condition_field_reference,
  [sym_conditional_table_relation] = sym_conditional_table_relation,
  [sym__table_relation_body] = sym__table_relation_body,
  [sym_table_relation_condition] = sym_table_relation_condition,
  [sym_field_class_property] = sym_field_class_property,
  [sym_calc_formula_property] = sym_calc_formula_property,
  [sym__calc_formula_expression] = sym__calc_formula_expression,
  [sym_lookup_formula] = sym_lookup_formula,
  [sym_lookup_where_conditions] = sym_lookup_where_conditions,
  [sym_lookup_where_condition] = sym_lookup_where_condition,
  [sym_count_formula] = sym_count_formula,
  [sym_sum_formula] = sym_sum_formula,
  [sym_average_formula] = sym_average_formula,
  [sym_min_formula] = sym_min_formula,
  [sym_max_formula] = sym_max_formula,
  [sym_field_reference] = sym_field_reference,
  [sym_where_clause] = sym_where_clause,
  [sym_where_conditions] = sym_where_conditions,
  [sym_where_condition] = sym_where_condition,
  [sym_filter_conditions] = sym_filter_conditions,
  [sym_filter_condition] = sym_filter_condition,
  [sym_filter_operator] = sym_filter_operator,
  [sym_blank_zero_property] = sym_blank_zero_property,
  [sym_editable_property] = sym_editable_property,
  [sym_option_members_property] = sym_option_members_property,
  [sym_option_member] = sym_option_member,
  [sym_option_caption_property] = sym_option_caption_property,
  [sym_field_trigger_declaration] = sym_field_trigger_declaration,
  [sym_keys] = sym_keys,
  [sym_key_declaration] = sym_key_declaration,
  [sym_key_field] = sym_key_field,
  [sym_key_field_list] = sym_key_field_list,
  [sym_attribute_list] = sym_attribute_list,
  [sym_attribute] = sym_attribute,
  [sym_attribute_arguments] = sym_attribute_arguments,
  [sym_expression_list] = sym_expression_list,
  [sym_return_value] = sym_return_value,
  [sym__procedure_return_specification] = sym__procedure_return_specification,
  [sym_return_type] = sym_return_type,
  [sym__procedure_name] = sym__procedure_name,
  [sym_procedure] = sym_procedure,
  [sym_comparison_operator] = sym_comparison_operator,
  [sym_arithmetic_operator] = sym_arithmetic_operator,
  [sym_parameter_list] = sym_parameter_list,
  [sym_modifier] = sym_modifier,
  [sym_parameter] = sym_parameter,
  [sym__quoted_identifier] = sym__quoted_identifier,
  [sym_clustered_property] = sym_clustered_property,
  [sym_boolean] = sym_boolean,
  [sym_data_type] = sym_data_type,
  [sym_code_block] = sym_code_block,
  [sym__statement] = sym__statement,
  [sym_repeat_statement] = sym_repeat_statement,
  [sym_assignment_statement] = sym_assignment_statement,
  [sym__assignable_expression] = sym__assignable_expression,
  [sym_argument_list] = sym_argument_list,
  [sym__primary_expression] = sym__primary_expression,
  [sym_enum_member_access] = sym_enum_member_access,
  [sym__expression] = sym__expression,
  [sym_procedure_call] = sym_procedure_call,
  [sym_get_method] = sym_get_method,
  [sym_find_set_method] = sym_find_set_method,
  [sym_insert_statement] = sym_insert_statement,
  [sym_modify_statement] = sym_modify_statement,
  [sym_delete_statement] = sym_delete_statement,
  [sym_set_range_statement] = sym_set_range_statement,
  [sym_set_filter_statement] = sym_set_filter_statement,
  [sym_reset_statement] = sym_reset_statement,
  [sym_binary_expression] = sym_binary_expression,
  [sym_if_statement] = sym_if_statement,
  [sym_get_statement] = sym_get_statement,
  [sym_find_set_statement] = sym_find_set_statement,
  [sym_find_first_statement] = sym_find_first_statement,
  [sym_find_last_statement] = sym_find_last_statement,
  [sym_next_statement] = sym_next_statement,
  [sym_case_statement] = sym_case_statement,
  [sym_case_clause] = sym_case_clause,
  [sym_value_set] = sym_value_set,
  [sym_else_clause] = sym_else_clause,
  [sym_exit_statement] = sym_exit_statement,
  [aux_sym_source_file_repeat1] = aux_sym_source_file_repeat1,
  [aux_sym_table_declaration_repeat1] = aux_sym_table_declaration_repeat1,
  [aux_sym_codeunit_declaration_repeat1] = aux_sym_codeunit_declaration_repeat1,
  [aux_sym_option_members_value_repeat1] = aux_sym_option_members_value_repeat1,
  [aux_sym_property_list_repeat1] = aux_sym_property_list_repeat1,
  [aux_sym_var_section_repeat1] = aux_sym_var_section_repeat1,
  [aux_sym_fields_repeat1] = aux_sym_fields_repeat1,
  [aux_sym_field_declaration_repeat1] = aux_sym_field_declaration_repeat1,
  [aux_sym_lookup_where_conditions_repeat1] = aux_sym_lookup_where_conditions_repeat1,
  [aux_sym_where_conditions_repeat1] = aux_sym_where_conditions_repeat1,
  [aux_sym_filter_conditions_repeat1] = aux_sym_filter_conditions_repeat1,
  [aux_sym_keys_repeat1] = aux_sym_keys_repeat1,
  [aux_sym_key_declaration_repeat1] = aux_sym_key_declaration_repeat1,
  [aux_sym_key_field_list_repeat1] = aux_sym_key_field_list_repeat1,
  [aux_sym_attribute_list_repeat1] = aux_sym_attribute_list_repeat1,
  [aux_sym_expression_list_repeat1] = aux_sym_expression_list_repeat1,
  [aux_sym_parameter_list_repeat1] = aux_sym_parameter_list_repeat1,
  [aux_sym__quoted_identifier_repeat1] = aux_sym__quoted_identifier_repeat1,
  [aux_sym_code_block_repeat1] = aux_sym_code_block_repeat1,
  [aux_sym_set_filter_statement_repeat1] = aux_sym_set_filter_statement_repeat1,
  [aux_sym_case_statement_repeat1] = aux_sym_case_statement_repeat1,
  [alias_sym_const] = alias_sym_const,
  [alias_sym_field] = alias_sym_field,
  [alias_sym_field_ref] = alias_sym_field_ref,
  [alias_sym_member] = alias_sym_member,
  [alias_sym_method_name] = alias_sym_method_name,
  [alias_sym_name] = alias_sym_name,
  [alias_sym_record] = alias_sym_record,
  [alias_sym_table] = alias_sym_table,
  [alias_sym_table_reference] = alias_sym_table_reference,
};

static const TSSymbolMetadata ts_symbol_metadata[] = {
  [ts_builtin_sym_end] = {
    .visible = false,
    .named = true,
  },
  [anon_sym_table] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LBRACE] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_RBRACE] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_codeunit] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Install] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Upgrade] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Test] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_FlowField] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_FlowFilter] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Normal] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_COMMA] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Temporary] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_External] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_System] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_TableType] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_EQ] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_SEMI] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_CustomerContent] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_EndUserIdentifiableInformation] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_AccountData] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_EndUserPseudonymousIdentifiers] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OrganizationIdentifiableInformation] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_SystemMetadata] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_ToBeClassified] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_trigger] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnRun] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LPAREN_RPAREN] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Permissions] = {
    .visible = true,
    .named = false,
  },
  [sym_permission_type] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_OnInsert] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnModify] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnDelete] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnRename] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnValidate] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnAfterGetRecord] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnAfterInsertEvent] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnAfterModifyEvent] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnAfterDeleteEvent] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnBeforeInsertEvent] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnBeforeModifyEvent] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnBeforeDeleteEvent] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_DOT] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_TableNo] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Subtype] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_SingleInstance] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_DrillDownPageId] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LookupPageId] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_TableRelation] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_FieldClass] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_CalcFormula] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_BlankZero] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Editable] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OptionMembers] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OptionCaption] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_DataClassification] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Caption] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_tabledata] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_DecimalPlaces] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_COLON] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_var] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_List] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_of] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LBRACK] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_RBRACK] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Dictionary] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Integer] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_BigInteger] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Decimal] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Byte] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Char] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Date] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Time] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_DateTime] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Duration] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_DateFormula] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Boolean] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Option] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Guid] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_RecordId] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Variant] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Dialog] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Action] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Blob] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_FilterPageBuilder] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_JsonToken] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_JsonValue] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_JsonArray] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_JsonObject] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Media] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_MediaSet] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OStream] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_InStream] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OutStream] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_SecretText] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Label] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Text] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Code] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Record] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Codeunit] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Query] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_DotNet] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_array] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_fields] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_field] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LPAREN] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_RPAREN] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_where] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_if] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_else] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_const] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_filter] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_lookup] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_count] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_sum] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_average] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_min] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_max] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_CONST] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_FILTER] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_FIELD] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_UPPERLIMIT] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LT_GT] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LT_EQ] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_GT_EQ] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_LT] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_GT] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_IN] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnLookup] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnAssistEdit] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_OnDrillDown] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_keys] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_key] = {
    .visible = true,
    .named = false,
  },
  [sym_procedure_modifier] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_procedure] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_PLUS] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_DASH] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_STAR] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_SLASH] = {
    .visible = true,
    .named = false,
  },
  [sym_identifier] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_DQUOTE] = {
    .visible = true,
    .named = false,
  },
  [aux_sym__quoted_identifier_token1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym__quoted_identifier_token2] = {
    .visible = false,
    .named = false,
  },
  [aux_sym__quoted_identifier_token3] = {
    .visible = false,
    .named = false,
  },
  [sym_integer] = {
    .visible = true,
    .named = true,
  },
  [sym_string_literal] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_Clustered] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_true] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_false] = {
    .visible = true,
    .named = false,
  },
  [sym_temporary] = {
    .visible = true,
    .named = true,
  },
  [anon_sym_Enum] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_begin] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_end] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_repeat] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_until] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_COLON_EQ] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_COLON_COLON] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Get] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_FindSet] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Insert] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Modify] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Delete] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_SetRange] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_SetFilter] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Reset] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_then] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_FindFirst] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_FindLast] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_Next] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_case] = {
    .visible = true,
    .named = false,
  },
  [anon_sym_exit] = {
    .visible = true,
    .named = false,
  },
  [sym_source_file] = {
    .visible = true,
    .named = true,
  },
  [sym__object] = {
    .visible = false,
    .named = true,
  },
  [sym_function_call] = {
    .visible = true,
    .named = true,
  },
  [sym_object_id] = {
    .visible = true,
    .named = true,
  },
  [sym_object_name] = {
    .visible = true,
    .named = true,
  },
  [sym_table_declaration] = {
    .visible = true,
    .named = true,
  },
  [sym_codeunit_declaration] = {
    .visible = true,
    .named = true,
  },
  [sym_table_no_value] = {
    .visible = true,
    .named = true,
  },
  [sym_subtype_value] = {
    .visible = true,
    .named = true,
  },
  [sym_single_instance_value] = {
    .visible = true,
    .named = true,
  },
  [sym_page_id_value] = {
    .visible = true,
    .named = true,
  },
  [sym_permissions_value] = {
    .visible = true,
    .named = true,
  },
  [sym_field_class_value] = {
    .visible = true,
    .named = true,
  },
  [sym_calc_formula_value] = {
    .visible = true,
    .named = true,
  },
  [sym_blank_zero_value] = {
    .visible = true,
    .named = true,
  },
  [sym_editable_value] = {
    .visible = true,
    .named = true,
  },
  [sym_option_members_value] = {
    .visible = true,
    .named = true,
  },
  [sym_option_caption_value] = {
    .visible = true,
    .named = true,
  },
  [sym_table_type_value] = {
    .visible = true,
    .named = true,
  },
  [sym_table_type_property] = {
    .visible = true,
    .named = true,
  },
  [sym_data_classification_value] = {
    .visible = true,
    .named = true,
  },
  [sym__codeunit_element] = {
    .visible = false,
    .named = true,
  },
  [sym_onrun_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym__table_element] = {
    .visible = false,
    .named = true,
  },
  [sym_permissions_property] = {
    .visible = true,
    .named = true,
  },
  [sym_oninsert_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onmodify_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_ondelete_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onrename_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onvalidate_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onaftergetrecord_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onafterinsertevent_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onaftermodifyevent_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onafterdeleteevent_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onbeforeinsertevent_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onbeforemodifyevent_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_onbeforedeleteevent_trigger] = {
    .visible = true,
    .named = true,
  },
  [sym_member_access] = {
    .visible = true,
    .named = true,
  },
  [sym_method_call] = {
    .visible = true,
    .named = true,
  },
  [sym_property_list] = {
    .visible = true,
    .named = true,
  },
  [sym_property] = {
    .visible = true,
    .named = true,
  },
  [sym_caption_property] = {
    .visible = true,
    .named = true,
  },
  [sym_data_classification_property] = {
    .visible = true,
    .named = true,
  },
  [sym_tabledata_permission_list] = {
    .visible = true,
    .named = true,
  },
  [sym_tabledata_permission] = {
    .visible = true,
    .named = true,
  },
  [sym__table_identifier] = {
    .visible = false,
    .named = true,
  },
  [sym_drilldown_pageid_property] = {
    .visible = true,
    .named = true,
  },
  [sym_lookup_pageid_property] = {
    .visible = true,
    .named = true,
  },
  [sym_decimal_places_property] = {
    .visible = true,
    .named = true,
  },
  [sym_var_section] = {
    .visible = true,
    .named = true,
  },
  [sym_variable_declaration] = {
    .visible = true,
    .named = true,
  },
  [sym_type_specification] = {
    .visible = true,
    .named = true,
  },
  [sym_list_type] = {
    .visible = true,
    .named = true,
  },
  [sym_dictionary_type] = {
    .visible = true,
    .named = true,
  },
  [sym_basic_type] = {
    .visible = true,
    .named = true,
  },
  [sym_text_type] = {
    .visible = true,
    .named = true,
  },
  [sym_code_type] = {
    .visible = true,
    .named = true,
  },
  [sym_record_type] = {
    .visible = true,
    .named = true,
  },
  [sym__table_reference] = {
    .visible = false,
    .named = true,
  },
  [sym_codeunit_type] = {
    .visible = true,
    .named = true,
  },
  [sym_query_type] = {
    .visible = true,
    .named = true,
  },
  [sym_query_type_value] = {
    .visible = true,
    .named = true,
  },
  [sym_dotnet_type] = {
    .visible = true,
    .named = true,
  },
  [sym_array_type] = {
    .visible = true,
    .named = true,
  },
  [sym_fields] = {
    .visible = true,
    .named = true,
  },
  [sym_field_declaration] = {
    .visible = true,
    .named = true,
  },
  [sym_table_relation_property] = {
    .visible = true,
    .named = true,
  },
  [sym_table_relation_value] = {
    .visible = true,
    .named = true,
  },
  [sym__simple_table_relation] = {
    .visible = false,
    .named = true,
  },
  [sym__field_reference] = {
    .visible = false,
    .named = true,
  },
  [sym__condition_field_reference] = {
    .visible = false,
    .named = true,
  },
  [sym_conditional_table_relation] = {
    .visible = true,
    .named = true,
  },
  [sym__table_relation_body] = {
    .visible = false,
    .named = true,
  },
  [sym_table_relation_condition] = {
    .visible = true,
    .named = true,
  },
  [sym_field_class_property] = {
    .visible = true,
    .named = true,
  },
  [sym_calc_formula_property] = {
    .visible = true,
    .named = true,
  },
  [sym__calc_formula_expression] = {
    .visible = false,
    .named = true,
  },
  [sym_lookup_formula] = {
    .visible = true,
    .named = true,
  },
  [sym_lookup_where_conditions] = {
    .visible = true,
    .named = true,
  },
  [sym_lookup_where_condition] = {
    .visible = true,
    .named = true,
  },
  [sym_count_formula] = {
    .visible = true,
    .named = true,
  },
  [sym_sum_formula] = {
    .visible = true,
    .named = true,
  },
  [sym_average_formula] = {
    .visible = true,
    .named = true,
  },
  [sym_min_formula] = {
    .visible = true,
    .named = true,
  },
  [sym_max_formula] = {
    .visible = true,
    .named = true,
  },
  [sym_field_reference] = {
    .visible = true,
    .named = true,
  },
  [sym_where_clause] = {
    .visible = true,
    .named = true,
  },
  [sym_where_conditions] = {
    .visible = true,
    .named = true,
  },
  [sym_where_condition] = {
    .visible = true,
    .named = true,
  },
  [sym_filter_conditions] = {
    .visible = true,
    .named = true,
  },
  [sym_filter_condition] = {
    .visible = true,
    .named = true,
  },
  [sym_filter_operator] = {
    .visible = true,
    .named = true,
  },
  [sym_blank_zero_property] = {
    .visible = true,
    .named = true,
  },
  [sym_editable_property] = {
    .visible = true,
    .named = true,
  },
  [sym_option_members_property] = {
    .visible = true,
    .named = true,
  },
  [sym_option_member] = {
    .visible = true,
    .named = true,
  },
  [sym_option_caption_property] = {
    .visible = true,
    .named = true,
  },
  [sym_field_trigger_declaration] = {
    .visible = true,
    .named = true,
  },
  [sym_keys] = {
    .visible = true,
    .named = true,
  },
  [sym_key_declaration] = {
    .visible = true,
    .named = true,
  },
  [sym_key_field] = {
    .visible = true,
    .named = true,
  },
  [sym_key_field_list] = {
    .visible = true,
    .named = true,
  },
  [sym_attribute_list] = {
    .visible = true,
    .named = true,
  },
  [sym_attribute] = {
    .visible = true,
    .named = true,
  },
  [sym_attribute_arguments] = {
    .visible = true,
    .named = true,
  },
  [sym_expression_list] = {
    .visible = true,
    .named = true,
  },
  [sym_return_value] = {
    .visible = true,
    .named = true,
  },
  [sym__procedure_return_specification] = {
    .visible = false,
    .named = true,
  },
  [sym_return_type] = {
    .visible = true,
    .named = true,
  },
  [sym__procedure_name] = {
    .visible = false,
    .named = true,
  },
  [sym_procedure] = {
    .visible = true,
    .named = true,
  },
  [sym_comparison_operator] = {
    .visible = true,
    .named = true,
  },
  [sym_arithmetic_operator] = {
    .visible = true,
    .named = true,
  },
  [sym_parameter_list] = {
    .visible = true,
    .named = true,
  },
  [sym_modifier] = {
    .visible = true,
    .named = true,
  },
  [sym_parameter] = {
    .visible = true,
    .named = true,
  },
  [sym__quoted_identifier] = {
    .visible = false,
    .named = true,
  },
  [sym_clustered_property] = {
    .visible = true,
    .named = true,
  },
  [sym_boolean] = {
    .visible = true,
    .named = true,
  },
  [sym_data_type] = {
    .visible = true,
    .named = true,
  },
  [sym_code_block] = {
    .visible = true,
    .named = true,
  },
  [sym__statement] = {
    .visible = false,
    .named = true,
  },
  [sym_repeat_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_assignment_statement] = {
    .visible = true,
    .named = true,
  },
  [sym__assignable_expression] = {
    .visible = false,
    .named = true,
  },
  [sym_argument_list] = {
    .visible = true,
    .named = true,
  },
  [sym__primary_expression] = {
    .visible = false,
    .named = true,
  },
  [sym_enum_member_access] = {
    .visible = true,
    .named = true,
  },
  [sym__expression] = {
    .visible = false,
    .named = true,
  },
  [sym_procedure_call] = {
    .visible = true,
    .named = true,
  },
  [sym_get_method] = {
    .visible = true,
    .named = true,
  },
  [sym_find_set_method] = {
    .visible = true,
    .named = true,
  },
  [sym_insert_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_modify_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_delete_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_set_range_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_set_filter_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_reset_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_binary_expression] = {
    .visible = true,
    .named = true,
  },
  [sym_if_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_get_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_find_set_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_find_first_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_find_last_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_next_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_case_statement] = {
    .visible = true,
    .named = true,
  },
  [sym_case_clause] = {
    .visible = true,
    .named = true,
  },
  [sym_value_set] = {
    .visible = true,
    .named = true,
  },
  [sym_else_clause] = {
    .visible = true,
    .named = true,
  },
  [sym_exit_statement] = {
    .visible = true,
    .named = true,
  },
  [aux_sym_source_file_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_table_declaration_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_codeunit_declaration_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_option_members_value_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_property_list_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_var_section_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_fields_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_field_declaration_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_lookup_where_conditions_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_where_conditions_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_filter_conditions_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_keys_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_key_declaration_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_key_field_list_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_attribute_list_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_expression_list_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_parameter_list_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym__quoted_identifier_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_code_block_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_set_filter_statement_repeat1] = {
    .visible = false,
    .named = false,
  },
  [aux_sym_case_statement_repeat1] = {
    .visible = false,
    .named = false,
  },
  [alias_sym_const] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_field] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_field_ref] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_member] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_method_name] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_name] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_record] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_table] = {
    .visible = true,
    .named = true,
  },
  [alias_sym_table_reference] = {
    .visible = true,
    .named = true,
  },
};

enum ts_field_identifiers {
  field_arguments = 1,
  field_attribute_name = 2,
  field_base_type = 3,
  field_call = 4,
  field_condition = 5,
  field_const = 6,
  field_decimals = 7,
  field_else_branch = 8,
  field_enum_type = 9,
  field_enum_value = 10,
  field_expression = 11,
  field_field = 12,
  field_field_name = 13,
  field_fields = 14,
  field_filter = 15,
  field_filter_expression = 16,
  field_forward_order = 17,
  field_from_value = 18,
  field_function_name = 19,
  field_id = 20,
  field_left = 21,
  field_length = 22,
  field_lock_record = 23,
  field_member = 24,
  field_method = 25,
  field_modifier = 26,
  field_name = 27,
  field_object = 28,
  field_object_id = 29,
  field_object_name = 30,
  field_operator = 31,
  field_parameter = 32,
  field_parameter_name = 33,
  field_parameter_type = 34,
  field_permission = 35,
  field_precision = 36,
  field_property_name = 37,
  field_property_value = 38,
  field_record = 39,
  field_reference = 40,
  field_return_type = 41,
  field_return_value = 42,
  field_right = 43,
  field_run_trigger = 44,
  field_scale = 45,
  field_size = 46,
  field_steps = 47,
  field_system_id = 48,
  field_table = 49,
  field_table_name = 50,
  field_target = 51,
  field_temporary = 52,
  field_then_branch = 53,
  field_to_value = 54,
  field_trigger_name = 55,
  field_type = 56,
  field_value = 57,
  field_value_set = 58,
};

static const char * const ts_field_names[] = {
  [0] = NULL,
  [field_arguments] = "arguments",
  [field_attribute_name] = "attribute_name",
  [field_base_type] = "base_type",
  [field_call] = "call",
  [field_condition] = "condition",
  [field_const] = "const",
  [field_decimals] = "decimals",
  [field_else_branch] = "else_branch",
  [field_enum_type] = "enum_type",
  [field_enum_value] = "enum_value",
  [field_expression] = "expression",
  [field_field] = "field",
  [field_field_name] = "field_name",
  [field_fields] = "fields",
  [field_filter] = "filter",
  [field_filter_expression] = "filter_expression",
  [field_forward_order] = "forward_order",
  [field_from_value] = "from_value",
  [field_function_name] = "function_name",
  [field_id] = "id",
  [field_left] = "left",
  [field_length] = "length",
  [field_lock_record] = "lock_record",
  [field_member] = "member",
  [field_method] = "method",
  [field_modifier] = "modifier",
  [field_name] = "name",
  [field_object] = "object",
  [field_object_id] = "object_id",
  [field_object_name] = "object_name",
  [field_operator] = "operator",
  [field_parameter] = "parameter",
  [field_parameter_name] = "parameter_name",
  [field_parameter_type] = "parameter_type",
  [field_permission] = "permission",
  [field_precision] = "precision",
  [field_property_name] = "property_name",
  [field_property_value] = "property_value",
  [field_record] = "record",
  [field_reference] = "reference",
  [field_return_type] = "return_type",
  [field_return_value] = "return_value",
  [field_right] = "right",
  [field_run_trigger] = "run_trigger",
  [field_scale] = "scale",
  [field_size] = "size",
  [field_steps] = "steps",
  [field_system_id] = "system_id",
  [field_table] = "table",
  [field_table_name] = "table_name",
  [field_target] = "target",
  [field_temporary] = "temporary",
  [field_then_branch] = "then_branch",
  [field_to_value] = "to_value",
  [field_trigger_name] = "trigger_name",
  [field_type] = "type",
  [field_value] = "value",
  [field_value_set] = "value_set",
};

static const TSFieldMapSlice ts_field_map_slices[PRODUCTION_ID_COUNT] = {
  [1] = {.index = 0, .length = 1},
  [2] = {.index = 1, .length = 2},
  [4] = {.index = 3, .length = 1},
  [5] = {.index = 4, .length = 2},
  [6] = {.index = 6, .length = 1},
  [7] = {.index = 7, .length = 1},
  [8] = {.index = 8, .length = 2},
  [9] = {.index = 10, .length = 2},
  [10] = {.index = 12, .length = 1},
  [11] = {.index = 13, .length = 1},
  [12] = {.index = 14, .length = 1},
  [13] = {.index = 15, .length = 2},
  [14] = {.index = 17, .length = 3},
  [15] = {.index = 20, .length = 2},
  [16] = {.index = 22, .length = 2},
  [17] = {.index = 24, .length = 3},
  [18] = {.index = 27, .length = 2},
  [19] = {.index = 29, .length = 1},
  [20] = {.index = 30, .length = 2},
  [21] = {.index = 32, .length = 2},
  [22] = {.index = 34, .length = 1},
  [23] = {.index = 35, .length = 1},
  [24] = {.index = 36, .length = 1},
  [25] = {.index = 37, .length = 2},
  [26] = {.index = 39, .length = 1},
  [27] = {.index = 40, .length = 3},
  [28] = {.index = 43, .length = 3},
  [29] = {.index = 46, .length = 2},
  [30] = {.index = 48, .length = 1},
  [31] = {.index = 49, .length = 3},
  [32] = {.index = 52, .length = 2},
  [33] = {.index = 54, .length = 2},
  [34] = {.index = 56, .length = 2},
  [35] = {.index = 58, .length = 2},
  [36] = {.index = 60, .length = 2},
  [37] = {.index = 62, .length = 2},
  [38] = {.index = 64, .length = 1},
  [39] = {.index = 65, .length = 2},
  [40] = {.index = 67, .length = 3},
  [41] = {.index = 70, .length = 2},
  [42] = {.index = 72, .length = 3},
  [43] = {.index = 75, .length = 2},
  [45] = {.index = 77, .length = 1},
  [46] = {.index = 77, .length = 1},
  [47] = {.index = 78, .length = 1},
  [48] = {.index = 79, .length = 1},
  [49] = {.index = 80, .length = 1},
  [50] = {.index = 81, .length = 3},
  [51] = {.index = 84, .length = 3},
  [52] = {.index = 87, .length = 2},
  [53] = {.index = 89, .length = 3},
  [54] = {.index = 92, .length = 2},
  [55] = {.index = 94, .length = 2},
  [56] = {.index = 96, .length = 2},
  [57] = {.index = 98, .length = 1},
  [58] = {.index = 99, .length = 1},
  [59] = {.index = 100, .length = 3},
  [60] = {.index = 103, .length = 3},
  [61] = {.index = 106, .length = 5},
  [62] = {.index = 111, .length = 5},
  [63] = {.index = 116, .length = 6},
  [64] = {.index = 122, .length = 5},
  [65] = {.index = 127, .length = 3},
  [66] = {.index = 130, .length = 3},
  [67] = {.index = 133, .length = 3},
  [68] = {.index = 136, .length = 3},
  [69] = {.index = 139, .length = 2},
  [70] = {.index = 141, .length = 1},
  [71] = {.index = 142, .length = 4},
  [72] = {.index = 146, .length = 2},
  [73] = {.index = 148, .length = 1},
  [74] = {.index = 149, .length = 2},
  [75] = {.index = 149, .length = 2},
  [76] = {.index = 149, .length = 2},
  [77] = {.index = 149, .length = 2},
  [78] = {.index = 151, .length = 4},
  [79] = {.index = 155, .length = 2},
  [80] = {.index = 157, .length = 3},
  [81] = {.index = 160, .length = 8},
  [82] = {.index = 168, .length = 1},
  [83] = {.index = 169, .length = 2},
  [84] = {.index = 171, .length = 11},
};

static const TSFieldMapEntry ts_field_map_entries[] = {
  [0] =
    {field_name, 0},
  [1] =
    {field_object_id, 1},
    {field_object_name, 2},
  [3] =
    {field_attribute_name, 1},
  [4] =
    {field_property_name, 0},
    {field_property_value, 2},
  [6] =
    {field_call, 0},
  [7] =
    {field_reference, 1},
  [8] =
    {field_name, 0},
    {field_type, 2},
  [10] =
    {field_arguments, 1},
    {field_function_name, 0},
  [12] =
    {field_arguments, 1},
  [13] =
    {field_return_value, 0},
  [14] =
    {field_name, 1},
  [15] =
    {field_permission, 3},
    {field_table_name, 1},
  [17] =
    {field_name, 0},
    {field_temporary, 3},
    {field_type, 2},
  [20] =
    {field_member, 2},
    {field_object, 0},
  [22] =
    {field_enum_type, 0},
    {field_enum_value, 2},
  [24] =
    {field_left, 0},
    {field_operator, 1},
    {field_right, 2},
  [27] =
    {field_modifier, 0},
    {field_name, 2},
  [29] =
    {field_return_type, 1},
  [30] =
    {field_name, 1},
    {field_return_type, 4, .inherited = true},
  [32] =
    {field_parameter_name, 0},
    {field_parameter_type, 2},
  [34] =
    {field_name, 2},
  [35] =
    {field_target, 2},
  [36] =
    {field_table, 2},
  [37] =
    {field_left, 0},
    {field_right, 2},
  [39] =
    {field_length, 2},
  [40] =
    {field_arguments, 3},
    {field_method, 2},
    {field_object, 0},
  [43] =
    {field_modifier, 0},
    {field_name, 2},
    {field_return_type, 5, .inherited = true},
  [46] =
    {field_name, 1},
    {field_return_type, 5, .inherited = true},
  [48] =
    {field_return_type, 2},
  [49] =
    {field_modifier, 0},
    {field_parameter_name, 1},
    {field_parameter_type, 3},
  [52] =
    {field_modifier, 1},
    {field_name, 3},
  [54] =
    {field_name, 2},
    {field_return_type, 5, .inherited = true},
  [56] =
    {field_const, 2},
    {field_field, 0},
  [58] =
    {field_field, 2},
    {field_table, 0},
  [60] =
    {field_condition, 1},
    {field_then_branch, 3},
  [62] =
    {field_arguments, 3},
    {field_record, 0},
  [64] =
    {field_condition, 3},
  [65] =
    {field_fields, 4},
    {field_name, 2},
  [67] =
    {field_modifier, 0},
    {field_name, 2},
    {field_return_type, 6, .inherited = true},
  [70] =
    {field_name, 1},
    {field_return_type, 6, .inherited = true},
  [72] =
    {field_modifier, 1},
    {field_name, 3},
    {field_return_type, 6, .inherited = true},
  [75] =
    {field_name, 2},
    {field_return_type, 6, .inherited = true},
  [77] =
    {field_record, 0},
  [78] =
    {field_expression, 1},
  [79] =
    {field_size, 2},
  [80] =
    {field_base_type, 0},
  [81] =
    {field_modifier, 0},
    {field_name, 2},
    {field_return_type, 7, .inherited = true},
  [84] =
    {field_modifier, 1},
    {field_name, 3},
    {field_return_type, 7, .inherited = true},
  [87] =
    {field_name, 2},
    {field_return_type, 7, .inherited = true},
  [89] =
    {field_condition, 1},
    {field_else_branch, 5},
    {field_then_branch, 3},
  [92] =
    {field_forward_order, 4},
    {field_record, 0},
  [94] =
    {field_record, 0},
    {field_run_trigger, 4},
  [96] =
    {field_record, 0},
    {field_steps, 4},
  [98] =
    {field_value_set, 0},
  [99] =
    {field_enum_type, 1},
  [100] =
    {field_id, 2},
    {field_name, 4},
    {field_type, 6},
  [103] =
    {field_modifier, 1},
    {field_name, 3},
    {field_return_type, 8, .inherited = true},
  [106] =
    {field_field, 0},
    {field_field, 2},
    {field_field, 3},
    {field_field, 4},
    {field_field, 5},
  [111] =
    {field_const, 2},
    {field_const, 3},
    {field_const, 4},
    {field_const, 5},
    {field_field, 0},
  [116] =
    {field_field, 0},
    {field_filter, 2},
    {field_filter, 3},
    {field_filter, 4},
    {field_filter, 5},
    {field_filter, 6},
  [122] =
    {field_field, 0},
    {field_value, 2},
    {field_value, 3},
    {field_value, 4},
    {field_value, 5},
  [127] =
    {field_forward_order, 4},
    {field_lock_record, 6},
    {field_record, 0},
  [130] =
    {field_record, 0},
    {field_run_trigger, 4},
    {field_system_id, 6},
  [133] =
    {field_field_name, 4},
    {field_from_value, 6},
    {field_record, 0},
  [136] =
    {field_field_name, 4},
    {field_filter_expression, 6},
    {field_record, 0},
  [139] =
    {field_base_type, 0},
    {field_size, 2},
  [141] =
    {field_parameter, 1},
  [142] =
    {field_field_name, 4},
    {field_filter_expression, 6},
    {field_parameter, 7, .inherited = true},
    {field_record, 0},
  [146] =
    {field_parameter, 0, .inherited = true},
    {field_parameter, 1, .inherited = true},
  [148] =
    {field_value, 2},
  [149] =
    {field_field, 0},
    {field_value, 4},
  [151] =
    {field_field_name, 4},
    {field_from_value, 6},
    {field_record, 0},
    {field_to_value, 8},
  [155] =
    {field_decimals, 4},
    {field_size, 2},
  [157] =
    {field_base_type, 0},
    {field_decimals, 4},
    {field_size, 2},
  [160] =
    {field_field, 0},
    {field_value, 2},
    {field_value, 3},
    {field_value, 4},
    {field_value, 5},
    {field_value, 6},
    {field_value, 7},
    {field_value, 8},
  [168] =
    {field_trigger_name, 1},
  [169] =
    {field_precision, 2},
    {field_scale, 4},
  [171] =
    {field_field, 0},
    {field_value, 2},
    {field_value, 3},
    {field_value, 4},
    {field_value, 5},
    {field_value, 6},
    {field_value, 7},
    {field_value, 8},
    {field_value, 9},
    {field_value, 10},
    {field_value, 11},
};

static const TSSymbol ts_alias_sequences[PRODUCTION_ID_COUNT][MAX_ALIAS_SEQUENCE_LENGTH] = {
  [0] = {0},
  [1] = {
    [0] = alias_sym_name,
  },
  [3] = {
    [0] = alias_sym_name,
  },
  [15] = {
    [2] = alias_sym_member,
  },
  [21] = {
    [0] = alias_sym_name,
    [2] = sym_code_type,
  },
  [24] = {
    [2] = alias_sym_table_reference,
  },
  [27] = {
    [2] = alias_sym_method_name,
  },
  [31] = {
    [1] = alias_sym_name,
    [3] = sym_code_type,
  },
  [35] = {
    [0] = alias_sym_table,
    [2] = alias_sym_field,
  },
  [37] = {
    [0] = alias_sym_record,
  },
  [39] = {
    [2] = alias_sym_name,
  },
  [44] = {
    [0] = sym_identifier,
  },
  [45] = {
    [0] = alias_sym_record,
  },
  [54] = {
    [0] = alias_sym_record,
  },
  [59] = {
    [4] = alias_sym_name,
  },
  [65] = {
    [0] = alias_sym_record,
  },
  [74] = {
    [4] = alias_sym_field_ref,
  },
  [75] = {
    [2] = alias_sym_const,
  },
  [76] = {
    [0] = sym_identifier,
    [4] = alias_sym_field_ref,
  },
  [77] = {
    [0] = sym_identifier,
  },
};

static const uint16_t ts_non_terminal_alias_map[] = {
  sym_basic_type, 2,
    sym_basic_type,
    sym_code_type,
  sym_text_type, 2,
    sym_text_type,
    sym_code_type,
  sym_record_type, 2,
    sym_record_type,
    sym_code_type,
  sym__table_reference, 2,
    sym__table_reference,
    alias_sym_table_reference,
  sym_array_type, 2,
    sym_array_type,
    sym_code_type,
  sym__field_reference, 2,
    sym__field_reference,
    sym_identifier,
  sym__condition_field_reference, 2,
    sym__condition_field_reference,
    alias_sym_field_ref,
  sym__quoted_identifier, 7,
    sym__quoted_identifier,
    alias_sym_field,
    alias_sym_member,
    alias_sym_method_name,
    alias_sym_name,
    alias_sym_table,
    sym_identifier,
  0,
};

static const TSStateId ts_primary_state_ids[STATE_COUNT] = {
  [0] = 0,
  [1] = 1,
  [2] = 2,
  [3] = 3,
  [4] = 4,
  [5] = 5,
  [6] = 6,
  [7] = 7,
  [8] = 8,
  [9] = 4,
  [10] = 4,
  [11] = 11,
  [12] = 12,
  [13] = 13,
  [14] = 14,
  [15] = 11,
  [16] = 12,
  [17] = 14,
  [18] = 11,
  [19] = 11,
  [20] = 20,
  [21] = 21,
  [22] = 21,
  [23] = 20,
  [24] = 12,
  [25] = 21,
  [26] = 20,
  [27] = 21,
  [28] = 20,
  [29] = 21,
  [30] = 20,
  [31] = 20,
  [32] = 13,
  [33] = 12,
  [34] = 21,
  [35] = 13,
  [36] = 13,
  [37] = 37,
  [38] = 37,
  [39] = 37,
  [40] = 37,
  [41] = 41,
  [42] = 42,
  [43] = 43,
  [44] = 44,
  [45] = 45,
  [46] = 46,
  [47] = 47,
  [48] = 48,
  [49] = 49,
  [50] = 50,
  [51] = 49,
  [52] = 52,
  [53] = 48,
  [54] = 50,
  [55] = 55,
  [56] = 56,
  [57] = 57,
  [58] = 58,
  [59] = 59,
  [60] = 60,
  [61] = 61,
  [62] = 62,
  [63] = 63,
  [64] = 64,
  [65] = 64,
  [66] = 50,
  [67] = 67,
  [68] = 68,
  [69] = 49,
  [70] = 48,
  [71] = 50,
  [72] = 49,
  [73] = 48,
  [74] = 63,
  [75] = 64,
  [76] = 76,
  [77] = 64,
  [78] = 47,
  [79] = 79,
  [80] = 76,
  [81] = 81,
  [82] = 52,
  [83] = 83,
  [84] = 84,
  [85] = 57,
  [86] = 86,
  [87] = 58,
  [88] = 88,
  [89] = 47,
  [90] = 79,
  [91] = 63,
  [92] = 81,
  [93] = 52,
  [94] = 94,
  [95] = 84,
  [96] = 96,
  [97] = 55,
  [98] = 57,
  [99] = 58,
  [100] = 88,
  [101] = 88,
  [102] = 88,
  [103] = 55,
  [104] = 76,
  [105] = 84,
  [106] = 57,
  [107] = 58,
  [108] = 47,
  [109] = 63,
  [110] = 81,
  [111] = 52,
  [112] = 112,
  [113] = 79,
  [114] = 84,
  [115] = 115,
  [116] = 47,
  [117] = 79,
  [118] = 76,
  [119] = 81,
  [120] = 55,
  [121] = 121,
  [122] = 121,
  [123] = 123,
  [124] = 124,
  [125] = 121,
  [126] = 126,
  [127] = 121,
  [128] = 128,
  [129] = 129,
  [130] = 128,
  [131] = 128,
  [132] = 128,
  [133] = 133,
  [134] = 128,
  [135] = 135,
  [136] = 136,
  [137] = 137,
  [138] = 138,
  [139] = 139,
  [140] = 140,
  [141] = 139,
  [142] = 142,
  [143] = 143,
  [144] = 138,
  [145] = 140,
  [146] = 146,
  [147] = 147,
  [148] = 148,
  [149] = 137,
  [150] = 140,
  [151] = 147,
  [152] = 138,
  [153] = 137,
  [154] = 154,
  [155] = 137,
  [156] = 138,
  [157] = 147,
  [158] = 139,
  [159] = 137,
  [160] = 138,
  [161] = 147,
  [162] = 154,
  [163] = 146,
  [164] = 138,
  [165] = 146,
  [166] = 140,
  [167] = 146,
  [168] = 154,
  [169] = 154,
  [170] = 139,
  [171] = 171,
  [172] = 172,
  [173] = 173,
  [174] = 64,
  [175] = 175,
  [176] = 176,
  [177] = 177,
  [178] = 178,
  [179] = 179,
  [180] = 180,
  [181] = 181,
  [182] = 182,
  [183] = 183,
  [184] = 184,
  [185] = 185,
  [186] = 186,
  [187] = 187,
  [188] = 188,
  [189] = 189,
  [190] = 190,
  [191] = 191,
  [192] = 192,
  [193] = 193,
  [194] = 194,
  [195] = 195,
  [196] = 196,
  [197] = 197,
  [198] = 198,
  [199] = 199,
  [200] = 200,
  [201] = 201,
  [202] = 202,
  [203] = 203,
  [204] = 204,
  [205] = 205,
  [206] = 206,
  [207] = 79,
  [208] = 208,
  [209] = 209,
  [210] = 210,
  [211] = 211,
  [212] = 212,
  [213] = 213,
  [214] = 214,
  [215] = 215,
  [216] = 216,
  [217] = 217,
  [218] = 218,
  [219] = 219,
  [220] = 220,
  [221] = 221,
  [222] = 222,
  [223] = 223,
  [224] = 224,
  [225] = 225,
  [226] = 226,
  [227] = 227,
  [228] = 228,
  [229] = 229,
  [230] = 230,
  [231] = 231,
  [232] = 232,
  [233] = 233,
  [234] = 60,
  [235] = 235,
  [236] = 236,
  [237] = 68,
  [238] = 59,
  [239] = 239,
  [240] = 240,
  [241] = 241,
  [242] = 242,
  [243] = 243,
  [244] = 67,
  [245] = 190,
  [246] = 246,
  [247] = 247,
  [248] = 60,
  [249] = 249,
  [250] = 250,
  [251] = 251,
  [252] = 252,
  [253] = 253,
  [254] = 254,
  [255] = 59,
  [256] = 256,
  [257] = 67,
  [258] = 258,
  [259] = 259,
  [260] = 260,
  [261] = 261,
  [262] = 262,
  [263] = 263,
  [264] = 264,
  [265] = 265,
  [266] = 266,
  [267] = 267,
  [268] = 268,
  [269] = 269,
  [270] = 270,
  [271] = 271,
  [272] = 272,
  [273] = 273,
  [274] = 274,
  [275] = 275,
  [276] = 276,
  [277] = 277,
  [278] = 278,
  [279] = 279,
  [280] = 280,
  [281] = 281,
  [282] = 282,
  [283] = 283,
  [284] = 249,
  [285] = 250,
  [286] = 251,
  [287] = 252,
  [288] = 254,
  [289] = 289,
  [290] = 259,
  [291] = 260,
  [292] = 262,
  [293] = 263,
  [294] = 264,
  [295] = 265,
  [296] = 266,
  [297] = 267,
  [298] = 268,
  [299] = 269,
  [300] = 270,
  [301] = 271,
  [302] = 272,
  [303] = 273,
  [304] = 274,
  [305] = 275,
  [306] = 276,
  [307] = 277,
  [308] = 278,
  [309] = 279,
  [310] = 280,
  [311] = 281,
  [312] = 282,
  [313] = 283,
  [314] = 190,
  [315] = 190,
  [316] = 316,
  [317] = 68,
  [318] = 81,
  [319] = 259,
  [320] = 320,
  [321] = 260,
  [322] = 262,
  [323] = 263,
  [324] = 324,
  [325] = 265,
  [326] = 266,
  [327] = 267,
  [328] = 268,
  [329] = 269,
  [330] = 270,
  [331] = 271,
  [332] = 272,
  [333] = 273,
  [334] = 274,
  [335] = 275,
  [336] = 276,
  [337] = 277,
  [338] = 278,
  [339] = 279,
  [340] = 280,
  [341] = 281,
  [342] = 282,
  [343] = 283,
  [344] = 84,
  [345] = 48,
  [346] = 271,
  [347] = 272,
  [348] = 348,
  [349] = 349,
  [350] = 273,
  [351] = 274,
  [352] = 275,
  [353] = 276,
  [354] = 277,
  [355] = 278,
  [356] = 279,
  [357] = 280,
  [358] = 281,
  [359] = 282,
  [360] = 360,
  [361] = 262,
  [362] = 283,
  [363] = 60,
  [364] = 68,
  [365] = 59,
  [366] = 67,
  [367] = 263,
  [368] = 264,
  [369] = 265,
  [370] = 249,
  [371] = 266,
  [372] = 250,
  [373] = 251,
  [374] = 252,
  [375] = 267,
  [376] = 268,
  [377] = 254,
  [378] = 269,
  [379] = 270,
  [380] = 259,
  [381] = 381,
  [382] = 249,
  [383] = 250,
  [384] = 251,
  [385] = 252,
  [386] = 60,
  [387] = 68,
  [388] = 59,
  [389] = 67,
  [390] = 324,
  [391] = 324,
  [392] = 324,
  [393] = 324,
  [394] = 254,
  [395] = 260,
  [396] = 264,
  [397] = 397,
  [398] = 398,
  [399] = 399,
  [400] = 400,
  [401] = 401,
  [402] = 402,
  [403] = 403,
  [404] = 348,
  [405] = 405,
  [406] = 64,
  [407] = 48,
  [408] = 408,
  [409] = 409,
  [410] = 410,
  [411] = 411,
  [412] = 412,
  [413] = 412,
  [414] = 414,
  [415] = 415,
  [416] = 416,
  [417] = 415,
  [418] = 418,
  [419] = 416,
  [420] = 418,
  [421] = 415,
  [422] = 418,
  [423] = 64,
  [424] = 416,
  [425] = 415,
  [426] = 418,
  [427] = 64,
  [428] = 416,
  [429] = 418,
  [430] = 64,
  [431] = 431,
  [432] = 432,
  [433] = 433,
  [434] = 432,
  [435] = 433,
  [436] = 432,
  [437] = 433,
  [438] = 433,
  [439] = 412,
  [440] = 432,
  [441] = 412,
  [442] = 442,
  [443] = 57,
  [444] = 55,
  [445] = 60,
  [446] = 59,
  [447] = 442,
  [448] = 63,
  [449] = 442,
  [450] = 52,
  [451] = 58,
  [452] = 442,
  [453] = 68,
  [454] = 454,
  [455] = 455,
  [456] = 456,
  [457] = 67,
  [458] = 458,
  [459] = 459,
  [460] = 460,
  [461] = 133,
  [462] = 136,
  [463] = 463,
  [464] = 464,
  [465] = 465,
  [466] = 466,
  [467] = 467,
  [468] = 468,
  [469] = 469,
  [470] = 470,
  [471] = 471,
  [472] = 472,
  [473] = 473,
  [474] = 474,
  [475] = 475,
  [476] = 476,
  [477] = 477,
  [478] = 478,
  [479] = 479,
  [480] = 480,
  [481] = 481,
  [482] = 482,
  [483] = 483,
  [484] = 484,
  [485] = 485,
  [486] = 486,
  [487] = 487,
  [488] = 488,
  [489] = 171,
  [490] = 172,
  [491] = 491,
  [492] = 492,
  [493] = 493,
  [494] = 494,
  [495] = 495,
  [496] = 496,
  [497] = 497,
  [498] = 498,
  [499] = 499,
  [500] = 500,
  [501] = 501,
  [502] = 502,
  [503] = 503,
  [504] = 504,
  [505] = 505,
  [506] = 506,
  [507] = 507,
  [508] = 508,
  [509] = 509,
  [510] = 510,
  [511] = 511,
  [512] = 512,
  [513] = 513,
  [514] = 514,
  [515] = 515,
  [516] = 516,
  [517] = 516,
  [518] = 518,
  [519] = 519,
  [520] = 520,
  [521] = 521,
  [522] = 522,
  [523] = 523,
  [524] = 516,
  [525] = 525,
  [526] = 526,
  [527] = 516,
  [528] = 516,
  [529] = 529,
  [530] = 530,
  [531] = 531,
  [532] = 532,
  [533] = 533,
  [534] = 534,
  [535] = 535,
  [536] = 536,
  [537] = 537,
  [538] = 538,
  [539] = 539,
  [540] = 540,
  [541] = 541,
  [542] = 542,
  [543] = 543,
  [544] = 544,
  [545] = 545,
  [546] = 546,
  [547] = 547,
  [548] = 548,
  [549] = 536,
  [550] = 542,
  [551] = 543,
  [552] = 544,
  [553] = 133,
  [554] = 136,
  [555] = 555,
  [556] = 556,
  [557] = 557,
  [558] = 558,
  [559] = 532,
  [560] = 560,
  [561] = 561,
  [562] = 536,
  [563] = 542,
  [564] = 543,
  [565] = 544,
  [566] = 566,
  [567] = 567,
  [568] = 568,
  [569] = 569,
  [570] = 570,
  [571] = 571,
  [572] = 572,
  [573] = 573,
  [574] = 574,
  [575] = 536,
  [576] = 542,
  [577] = 543,
  [578] = 544,
  [579] = 579,
  [580] = 580,
  [581] = 581,
  [582] = 582,
  [583] = 583,
  [584] = 584,
  [585] = 585,
  [586] = 586,
  [587] = 532,
  [588] = 588,
  [589] = 589,
  [590] = 590,
  [591] = 532,
  [592] = 592,
  [593] = 593,
  [594] = 532,
  [595] = 595,
  [596] = 596,
  [597] = 597,
  [598] = 598,
  [599] = 599,
  [600] = 600,
  [601] = 601,
  [602] = 602,
  [603] = 603,
  [604] = 604,
  [605] = 605,
  [606] = 606,
  [607] = 607,
  [608] = 608,
  [609] = 609,
  [610] = 610,
  [611] = 611,
  [612] = 612,
  [613] = 613,
  [614] = 614,
  [615] = 615,
  [616] = 616,
  [617] = 617,
  [618] = 618,
  [619] = 619,
  [620] = 620,
  [621] = 621,
  [622] = 622,
  [623] = 620,
  [624] = 624,
  [625] = 625,
  [626] = 616,
  [627] = 627,
  [628] = 628,
  [629] = 629,
  [630] = 630,
  [631] = 631,
  [632] = 632,
  [633] = 613,
  [634] = 632,
  [635] = 616,
  [636] = 636,
  [637] = 637,
  [638] = 638,
  [639] = 620,
  [640] = 640,
  [641] = 641,
  [642] = 616,
  [643] = 643,
  [644] = 644,
  [645] = 645,
  [646] = 632,
  [647] = 647,
  [648] = 620,
  [649] = 649,
  [650] = 613,
  [651] = 651,
  [652] = 652,
  [653] = 653,
  [654] = 654,
  [655] = 637,
  [656] = 644,
  [657] = 657,
  [658] = 641,
  [659] = 659,
  [660] = 660,
  [661] = 661,
  [662] = 620,
  [663] = 613,
  [664] = 664,
  [665] = 665,
  [666] = 666,
  [667] = 667,
  [668] = 637,
  [669] = 644,
  [670] = 657,
  [671] = 641,
  [672] = 672,
  [673] = 673,
  [674] = 620,
  [675] = 675,
  [676] = 676,
  [677] = 677,
  [678] = 678,
  [679] = 637,
  [680] = 644,
  [681] = 657,
  [682] = 641,
  [683] = 657,
  [684] = 620,
  [685] = 620,
  [686] = 686,
  [687] = 687,
  [688] = 688,
  [689] = 689,
  [690] = 690,
  [691] = 620,
  [692] = 692,
  [693] = 693,
  [694] = 616,
  [695] = 695,
  [696] = 696,
  [697] = 697,
  [698] = 698,
  [699] = 673,
  [700] = 631,
  [701] = 640,
  [702] = 702,
  [703] = 631,
  [704] = 640,
  [705] = 632,
  [706] = 631,
  [707] = 640,
  [708] = 673,
  [709] = 709,
  [710] = 710,
  [711] = 711,
  [712] = 712,
  [713] = 713,
  [714] = 714,
  [715] = 715,
  [716] = 716,
  [717] = 717,
  [718] = 718,
  [719] = 719,
  [720] = 720,
  [721] = 721,
  [722] = 722,
  [723] = 723,
  [724] = 724,
  [725] = 725,
  [726] = 726,
  [727] = 727,
  [728] = 728,
  [729] = 729,
  [730] = 730,
  [731] = 731,
  [732] = 732,
  [733] = 733,
  [734] = 734,
  [735] = 735,
  [736] = 736,
  [737] = 737,
  [738] = 738,
  [739] = 739,
  [740] = 740,
  [741] = 171,
  [742] = 172,
  [743] = 743,
  [744] = 744,
  [745] = 745,
  [746] = 746,
  [747] = 747,
  [748] = 748,
  [749] = 749,
  [750] = 750,
  [751] = 751,
  [752] = 752,
  [753] = 753,
  [754] = 754,
  [755] = 755,
  [756] = 756,
  [757] = 757,
  [758] = 758,
  [759] = 759,
  [760] = 760,
  [761] = 761,
  [762] = 762,
  [763] = 763,
  [764] = 764,
  [765] = 765,
  [766] = 766,
  [767] = 767,
  [768] = 768,
  [769] = 769,
  [770] = 770,
  [771] = 771,
  [772] = 772,
  [773] = 773,
  [774] = 774,
  [775] = 775,
  [776] = 776,
  [777] = 777,
  [778] = 773,
  [779] = 779,
  [780] = 780,
  [781] = 781,
  [782] = 744,
  [783] = 783,
  [784] = 759,
  [785] = 760,
  [786] = 786,
  [787] = 787,
  [788] = 788,
  [789] = 789,
  [790] = 790,
  [791] = 791,
  [792] = 792,
  [793] = 773,
  [794] = 794,
  [795] = 744,
  [796] = 796,
  [797] = 759,
  [798] = 760,
  [799] = 786,
  [800] = 800,
  [801] = 801,
  [802] = 802,
  [803] = 803,
  [804] = 804,
  [805] = 805,
  [806] = 773,
  [807] = 807,
  [808] = 744,
  [809] = 809,
  [810] = 759,
  [811] = 760,
  [812] = 786,
  [813] = 813,
  [814] = 786,
  [815] = 815,
  [816] = 816,
  [817] = 817,
  [818] = 818,
  [819] = 789,
  [820] = 820,
  [821] = 821,
  [822] = 822,
  [823] = 823,
  [824] = 824,
  [825] = 825,
  [826] = 826,
  [827] = 827,
  [828] = 828,
  [829] = 789,
  [830] = 830,
  [831] = 831,
  [832] = 832,
  [833] = 833,
  [834] = 834,
  [835] = 835,
  [836] = 836,
  [837] = 837,
  [838] = 838,
  [839] = 839,
  [840] = 840,
  [841] = 841,
  [842] = 842,
  [843] = 843,
  [844] = 844,
  [845] = 845,
  [846] = 846,
  [847] = 847,
  [848] = 848,
  [849] = 849,
  [850] = 850,
  [851] = 851,
  [852] = 852,
  [853] = 853,
  [854] = 854,
  [855] = 855,
  [856] = 856,
  [857] = 857,
  [858] = 858,
  [859] = 859,
  [860] = 860,
  [861] = 861,
  [862] = 862,
  [863] = 863,
  [864] = 864,
  [865] = 865,
  [866] = 866,
  [867] = 867,
  [868] = 868,
  [869] = 869,
  [870] = 870,
  [871] = 871,
  [872] = 872,
  [873] = 873,
  [874] = 874,
  [875] = 875,
  [876] = 876,
  [877] = 877,
  [878] = 878,
  [879] = 879,
  [880] = 880,
  [881] = 881,
  [882] = 882,
  [883] = 883,
  [884] = 884,
  [885] = 885,
  [886] = 830,
  [887] = 887,
  [888] = 888,
  [889] = 889,
  [890] = 890,
  [891] = 891,
  [892] = 892,
  [893] = 893,
  [894] = 894,
  [895] = 895,
  [896] = 896,
  [897] = 897,
  [898] = 898,
  [899] = 899,
  [900] = 900,
  [901] = 901,
  [902] = 902,
  [903] = 903,
  [904] = 904,
  [905] = 905,
  [906] = 906,
  [907] = 907,
  [908] = 908,
  [909] = 909,
  [910] = 910,
  [911] = 911,
  [912] = 912,
  [913] = 913,
  [914] = 914,
  [915] = 915,
  [916] = 916,
  [917] = 917,
  [918] = 918,
  [919] = 919,
  [920] = 920,
  [921] = 921,
  [922] = 922,
  [923] = 923,
  [924] = 924,
  [925] = 925,
  [926] = 926,
  [927] = 927,
  [928] = 928,
  [929] = 836,
  [930] = 930,
  [931] = 931,
  [932] = 932,
  [933] = 933,
  [934] = 934,
  [935] = 935,
  [936] = 936,
  [937] = 937,
  [938] = 938,
  [939] = 939,
  [940] = 940,
  [941] = 941,
  [942] = 942,
  [943] = 943,
  [944] = 944,
  [945] = 945,
  [946] = 946,
  [947] = 947,
  [948] = 948,
  [949] = 949,
  [950] = 950,
  [951] = 951,
  [952] = 882,
  [953] = 884,
  [954] = 891,
  [955] = 896,
  [956] = 956,
  [957] = 957,
  [958] = 958,
  [959] = 959,
  [960] = 960,
  [961] = 961,
  [962] = 962,
  [963] = 963,
  [964] = 964,
  [965] = 965,
  [966] = 966,
  [967] = 967,
  [968] = 968,
  [969] = 925,
  [970] = 970,
  [971] = 971,
  [972] = 972,
  [973] = 836,
  [974] = 974,
  [975] = 975,
  [976] = 976,
  [977] = 977,
  [978] = 978,
  [979] = 979,
  [980] = 980,
  [981] = 981,
  [982] = 982,
  [983] = 983,
  [984] = 984,
  [985] = 985,
  [986] = 945,
  [987] = 946,
  [988] = 947,
  [989] = 989,
  [990] = 990,
  [991] = 991,
  [992] = 992,
  [993] = 882,
  [994] = 884,
  [995] = 891,
  [996] = 896,
  [997] = 956,
  [998] = 957,
  [999] = 999,
  [1000] = 1000,
  [1001] = 1001,
  [1002] = 961,
  [1003] = 1003,
  [1004] = 1004,
  [1005] = 1005,
  [1006] = 1006,
  [1007] = 1007,
  [1008] = 1008,
  [1009] = 1009,
  [1010] = 836,
  [1011] = 1011,
  [1012] = 1012,
  [1013] = 1013,
  [1014] = 1014,
  [1015] = 1015,
  [1016] = 1016,
  [1017] = 1017,
  [1018] = 1018,
  [1019] = 1019,
  [1020] = 1020,
  [1021] = 1021,
  [1022] = 945,
  [1023] = 946,
  [1024] = 947,
  [1025] = 1025,
  [1026] = 1026,
  [1027] = 1027,
  [1028] = 1028,
  [1029] = 882,
  [1030] = 884,
  [1031] = 891,
  [1032] = 896,
  [1033] = 956,
  [1034] = 957,
  [1035] = 1035,
  [1036] = 1036,
  [1037] = 1037,
  [1038] = 961,
  [1039] = 945,
  [1040] = 1040,
  [1041] = 956,
  [1042] = 957,
  [1043] = 946,
  [1044] = 1044,
  [1045] = 836,
  [1046] = 947,
  [1047] = 1047,
  [1048] = 1048,
  [1049] = 1049,
  [1050] = 1050,
  [1051] = 1051,
  [1052] = 1052,
  [1053] = 1053,
  [1054] = 979,
  [1055] = 1055,
  [1056] = 1056,
  [1057] = 1057,
  [1058] = 1058,
  [1059] = 1059,
  [1060] = 1060,
  [1061] = 897,
  [1062] = 912,
  [1063] = 915,
  [1064] = 918,
  [1065] = 923,
  [1066] = 924,
  [1067] = 930,
  [1068] = 936,
  [1069] = 1069,
  [1070] = 1070,
  [1071] = 1071,
  [1072] = 1072,
  [1073] = 974,
  [1074] = 1074,
  [1075] = 1075,
  [1076] = 1076,
  [1077] = 1077,
  [1078] = 979,
  [1079] = 1079,
  [1080] = 1080,
  [1081] = 1081,
  [1082] = 1082,
  [1083] = 1083,
  [1084] = 897,
  [1085] = 912,
  [1086] = 915,
  [1087] = 918,
  [1088] = 923,
  [1089] = 924,
  [1090] = 930,
  [1091] = 936,
  [1092] = 1092,
  [1093] = 1093,
  [1094] = 1094,
  [1095] = 1095,
  [1096] = 974,
  [1097] = 1097,
  [1098] = 1098,
  [1099] = 1099,
  [1100] = 979,
  [1101] = 1101,
  [1102] = 1102,
  [1103] = 1103,
  [1104] = 1104,
  [1105] = 897,
  [1106] = 912,
  [1107] = 915,
  [1108] = 918,
  [1109] = 923,
  [1110] = 924,
  [1111] = 930,
  [1112] = 936,
  [1113] = 1113,
  [1114] = 1114,
  [1115] = 1115,
  [1116] = 1116,
  [1117] = 974,
  [1118] = 1118,
  [1119] = 1119,
  [1120] = 1120,
  [1121] = 961,
  [1122] = 943,
  [1123] = 1123,
  [1124] = 1124,
  [1125] = 1125,
  [1126] = 1126,
  [1127] = 1127,
  [1128] = 885,
  [1129] = 925,
  [1130] = 943,
  [1131] = 1131,
  [1132] = 1132,
  [1133] = 1133,
  [1134] = 1134,
  [1135] = 885,
  [1136] = 830,
  [1137] = 1137,
  [1138] = 1138,
  [1139] = 1139,
  [1140] = 885,
  [1141] = 830,
  [1142] = 1142,
  [1143] = 1143,
  [1144] = 1144,
  [1145] = 1145,
  [1146] = 1146,
  [1147] = 1147,
  [1148] = 1148,
  [1149] = 1149,
  [1150] = 1150,
  [1151] = 1151,
  [1152] = 921,
  [1153] = 922,
  [1154] = 921,
  [1155] = 922,
  [1156] = 921,
  [1157] = 922,
  [1158] = 1158,
};

static TSCharacterRange sym_permission_type_character_set_1[] = {
  {'D', 'D'}, {'I', 'I'}, {'M', 'M'}, {'R', 'R'}, {'X', 'X'}, {'d', 'd'}, {'i', 'i'}, {'m', 'm'},
  {'r', 'r'}, {'x', 'x'},
};

static bool ts_lex(TSLexer *lexer, TSStateId state) {
  START_LEXER();
  eof = lexer->eof(lexer);
  switch (state) {
    case 0:
      if (eof) ADVANCE(890);
      ADVANCE_MAP(
        '"', 1453,
        '\'', 15,
        '(', 1062,
        ')', 1063,
        '*', 1102,
        '+', 1100,
        ',', 902,
        '-', 1101,
        '.', 948,
        '/', 1103,
        ':', 971,
        ';', 910,
        '<', 1086,
        '=', 909,
        '>', 1087,
        'A', 190,
        'B', 404,
        'C', 76,
        'D', 925,
        'E', 206,
        'F', 56,
        'G', 286,
        'I', 924,
        'J', 728,
        'L', 100,
        'M', 930,
        'N', 246,
        'O', 87,
        'P', 339,
        'Q', 851,
        'R', 928,
        'S', 275,
        'T', 114,
        'U', 77,
        'V', 118,
        '[', 977,
        '\\', 888,
        ']', 978,
        'a', 684,
        'b', 283,
        'c', 117,
        'e', 508,
        'f', 101,
        'i', 931,
        'k', 248,
        'l', 605,
        'm', 926,
        'o', 374,
        'p', 686,
        'r', 929,
        's', 842,
        't', 161,
        'u', 570,
        'v', 120,
        'w', 403,
        '{', 893,
        '}', 894,
        'X', 935,
        'd', 935,
        'x', 935,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(0);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      END_STATE();
    case 1:
      if (lookahead == '\n') SKIP(1);
      if (lookahead == '"') ADVANCE(1453);
      if (lookahead == '.') ADVANCE(1454);
      if (lookahead == '\\') ADVANCE(888);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(1455);
      if (lookahead != 0) ADVANCE(1454);
      END_STATE();
    case 2:
      ADVANCE_MAP(
        '"', 1453,
        '\'', 15,
        '(', 1062,
        ')', 1063,
        '*', 1102,
        '+', 1100,
        ',', 902,
        '-', 1101,
        '.', 948,
        '/', 1103,
        ':', 970,
        ';', 910,
        '<', 24,
        '=', 909,
        'c', 1141,
        'e', 1328,
        'f', 1155,
        'i', 1246,
        'r', 1204,
        't', 1389,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(2);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 3:
      if (lookahead == '"') ADVANCE(1453);
      if (lookahead == '\'') ADVANCE(15);
      if (lookahead == '(') ADVANCE(1062);
      if (lookahead == ')') ADVANCE(1063);
      if (lookahead == 'f') ADVANCE(1155);
      if (lookahead == 't') ADVANCE(1389);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(3);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 4:
      ADVANCE_MAP(
        '"', 1453,
        '\'', 15,
        '(', 1062,
        '*', 1102,
        '+', 1100,
        '-', 1101,
        '.', 948,
        '/', 1103,
        ':', 22,
        '<', 24,
        '=', 909,
        'b', 1219,
        'c', 1141,
        'e', 1445,
        'f', 1155,
        'i', 1246,
        'r', 1204,
        't', 1389,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(4);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 5:
      ADVANCE_MAP(
        '"', 1453,
        '\'', 15,
        '(', 1062,
        '*', 1102,
        '+', 1100,
        '-', 1101,
        '.', 948,
        '/', 1103,
        ':', 21,
        ';', 910,
        '<', 24,
        '=', 909,
        'c', 1141,
        'e', 1305,
        'f', 1155,
        'i', 1246,
        'r', 1204,
        't', 1389,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(5);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 6:
      ADVANCE_MAP(
        '"', 1453,
        '\'', 15,
        '(', 1062,
        '*', 1102,
        '+', 1100,
        '-', 1101,
        '.', 948,
        '/', 1103,
        ':', 21,
        ';', 910,
        '<', 24,
        '=', 909,
        'c', 1141,
        'e', 1307,
        'f', 1155,
        'i', 1246,
        'r', 1204,
        't', 1389,
        'u', 1332,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(6);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 7:
      ADVANCE_MAP(
        '"', 1453,
        '\'', 15,
        '(', 1062,
        '*', 1102,
        '+', 1100,
        '-', 1101,
        '.', 948,
        '/', 1103,
        ':', 21,
        ';', 910,
        '<', 24,
        '=', 909,
        'c', 1141,
        'e', 1445,
        'f', 1155,
        'i', 1246,
        'r', 1204,
        't', 1389,
        'u', 1332,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(7);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 8:
      if (lookahead == '"') ADVANCE(1453);
      if (lookahead == '\'') ADVANCE(15);
      if (lookahead == '(') ADVANCE(1062);
      if (lookahead == ';') ADVANCE(910);
      if (lookahead == 'e') ADVANCE(1306);
      if (lookahead == 'f') ADVANCE(1155);
      if (lookahead == 't') ADVANCE(1389);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(8);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 9:
      ADVANCE_MAP(
        '"', 1453,
        '\'', 15,
        '(', 1062,
        'c', 1141,
        'e', 1445,
        'f', 1155,
        'i', 1246,
        'r', 1204,
        't', 1389,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(9);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 10:
      if (lookahead == '"') ADVANCE(1453);
      if (lookahead == '\'') ADVANCE(15);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(10);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 11:
      if (lookahead == '"') ADVANCE(1453);
      if (lookahead == 'F') ADVANCE(1110);
      if (lookahead == 'U') ADVANCE(1122);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(11);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 12:
      if (lookahead == '"') ADVANCE(1453);
      if (lookahead == 'F') ADVANCE(1110);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(12);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 13:
      if (lookahead == '"') ADVANCE(1453);
      if (lookahead == 'i') ADVANCE(1246);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(13);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 14:
      if (lookahead == '\'') ADVANCE(15);
      if (lookahead == 'c') ADVANCE(651);
      if (lookahead == 'f') ADVANCE(458);
      if (lookahead == 'k') ADVANCE(307);
      if (lookahead == '{') ADVANCE(893);
      if (lookahead == '}') ADVANCE(894);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(14);
      if (set_contains(sym_permission_type_character_set_1, 10, lookahead)) ADVANCE(935);
      END_STATE();
    case 15:
      if (lookahead == '\'') ADVANCE(1458);
      if (lookahead == '\\') ADVANCE(887);
      if (lookahead != 0) ADVANCE(15);
      END_STATE();
    case 16:
      ADVANCE_MAP(
        '(', 1062,
        ')', 1063,
        '*', 1102,
        '+', 1100,
        ',', 902,
        '-', 1101,
        '.', 948,
        '/', 1103,
        ':', 970,
        '<', 24,
        '=', 909,
        'A', 1175,
        'B', 1260,
        'C', 1258,
        'D', 1161,
        'F', 1262,
        'G', 1432,
        'I', 1317,
        'J', 1393,
        'L', 1135,
        'M', 1214,
        'O', 1128,
        'Q', 1433,
        'R', 1216,
        'S', 1218,
        'T', 1197,
        'V', 1142,
        ']', 978,
        'a', 1373,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(16);
      if (('E' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 17:
      ADVANCE_MAP(
        '(', 20,
        'A', 1175,
        'B', 1260,
        'C', 1259,
        'D', 1162,
        'F', 1262,
        'G', 1432,
        'I', 1317,
        'J', 1393,
        'L', 1136,
        'M', 1214,
        'O', 1128,
        'R', 1216,
        'S', 1218,
        'T', 1197,
        'V', 1142,
        'a', 1373,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(17);
      if (('E' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 18:
      ADVANCE_MAP(
        ')', 1063,
        '*', 1102,
        '+', 1100,
        ',', 902,
        '-', 1101,
        '.', 948,
        '/', 1103,
        ':', 970,
        ';', 910,
        '<', 24,
        '=', 909,
        'B', 501,
        'C', 99,
        'D', 149,
        'E', 207,
        'F', 435,
        'L', 619,
        'N', 614,
        'O', 667,
        'P', 339,
        'S', 409,
        'T', 115,
        '[', 977,
        'e', 567,
        'f', 430,
        'k', 306,
        'l', 621,
        'o', 374,
        'p', 686,
        't', 167,
        'v', 120,
        '}', 894,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(18);
      END_STATE();
    case 19:
      if (lookahead == ')') ADVANCE(1063);
      if (lookahead == 'v') ADVANCE(1160);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(19);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 20:
      if (lookahead == ')') ADVANCE(921);
      END_STATE();
    case 21:
      if (lookahead == ':') ADVANCE(1476);
      END_STATE();
    case 22:
      if (lookahead == ':') ADVANCE(1476);
      if (lookahead == '=') ADVANCE(1475);
      END_STATE();
    case 23:
      if (lookahead == ':') ADVANCE(969);
      if (lookahead == ';') ADVANCE(910);
      if (lookahead == 'b') ADVANCE(1219);
      if (lookahead == 'v') ADVANCE(1160);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(23);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 24:
      if (lookahead == '>') ADVANCE(1083);
      END_STATE();
    case 25:
      ADVANCE_MAP(
        'A', 384,
        'B', 280,
        'D', 348,
        'I', 598,
        'L', 643,
        'M', 645,
        'R', 293,
        'V', 123,
      );
      END_STATE();
    case 26:
      if (lookahead == 'A') ADVANCE(703);
      if (lookahead == 'O') ADVANCE(177);
      if (lookahead == 'T') ADVANCE(615);
      if (lookahead == 'V') ADVANCE(137);
      END_STATE();
    case 27:
      ADVANCE_MAP(
        'B', 1261,
        'C', 1357,
        'D', 1166,
        'E', 1327,
        'G', 1432,
        'I', 1335,
        'O', 1360,
        'R', 1245,
        'T', 1197,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(27);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 28:
      if (lookahead == 'B') ADVANCE(370);
      END_STATE();
    case 29:
      if (lookahead == 'B') ADVANCE(849);
      END_STATE();
    case 30:
      if (lookahead == 'C') ADVANCE(488);
      END_STATE();
    case 31:
      if (lookahead == 'C') ADVANCE(652);
      END_STATE();
    case 32:
      ADVANCE_MAP(
        'C', 1170,
        'D', 1159,
        'L', 1352,
        'P', 1237,
        'T', 1147,
        '[', 977,
        'f', 1280,
        'k', 1221,
        'l', 1345,
        'p', 1386,
        't', 1380,
        'v', 1160,
        '}', 894,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(32);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 33:
      if (lookahead == 'C') ADVANCE(121);
      if (lookahead == 'M') ADVANCE(303);
      END_STATE();
    case 34:
      if (lookahead == 'C') ADVANCE(490);
      END_STATE();
    case 35:
      if (lookahead == 'C') ADVANCE(515);
      END_STATE();
    case 36:
      if (lookahead == 'D') ADVANCE(1080);
      END_STATE();
    case 37:
      if (lookahead == 'D') ADVANCE(612);
      END_STATE();
    case 38:
      if (lookahead == 'D') ADVANCE(366);
      if (lookahead == 'G') ADVANCE(334);
      if (lookahead == 'I') ADVANCE(600);
      if (lookahead == 'M') ADVANCE(647);
      END_STATE();
    case 39:
      if (lookahead == 'D') ADVANCE(642);
      END_STATE();
    case 40:
      if (lookahead == 'D') ADVANCE(147);
      END_STATE();
    case 41:
      if (lookahead == 'D') ADVANCE(368);
      if (lookahead == 'I') ADVANCE(602);
      if (lookahead == 'M') ADVANCE(654);
      END_STATE();
    case 42:
      if (lookahead == 'E') ADVANCE(68);
      if (lookahead == 'L') ADVANCE(94);
      END_STATE();
    case 43:
      if (lookahead == 'E') ADVANCE(84);
      END_STATE();
    case 44:
      if (lookahead == 'E') ADVANCE(858);
      END_STATE();
    case 45:
      if (lookahead == 'E') ADVANCE(83);
      END_STATE();
    case 46:
      if (lookahead == 'E') ADVANCE(236);
      END_STATE();
    case 47:
      if (lookahead == 'E') ADVANCE(859);
      END_STATE();
    case 48:
      if (lookahead == 'E') ADVANCE(860);
      END_STATE();
    case 49:
      if (lookahead == 'E') ADVANCE(861);
      END_STATE();
    case 50:
      if (lookahead == 'E') ADVANCE(862);
      END_STATE();
    case 51:
      if (lookahead == 'E') ADVANCE(863);
      END_STATE();
    case 52:
      if (lookahead == 'F') ADVANCE(425);
      if (lookahead == 'L') ADVANCE(158);
      if (lookahead == 'S') ADVANCE(325);
      END_STATE();
    case 53:
      if (lookahead == 'F') ADVANCE(455);
      END_STATE();
    case 54:
      if (lookahead == 'F') ADVANCE(646);
      END_STATE();
    case 55:
      if (lookahead == 'F') ADVANCE(423);
      if (lookahead == 'R') ADVANCE(151);
      END_STATE();
    case 56:
      if (lookahead == 'I') ADVANCE(42);
      if (lookahead == 'i') ADVANCE(285);
      if (lookahead == 'l') ADVANCE(606);
      END_STATE();
    case 57:
      if (lookahead == 'I') ADVANCE(70);
      END_STATE();
    case 58:
      if (lookahead == 'I') ADVANCE(92);
      END_STATE();
    case 59:
      if (lookahead == 'I') ADVANCE(218);
      END_STATE();
    case 60:
      if (lookahead == 'I') ADVANCE(597);
      END_STATE();
    case 61:
      if (lookahead == 'I') ADVANCE(220);
      END_STATE();
    case 62:
      if (lookahead == 'I') ADVANCE(587);
      END_STATE();
    case 63:
      if (lookahead == 'I') ADVANCE(591);
      END_STATE();
    case 64:
      if (lookahead == 'I') ADVANCE(232);
      if (lookahead == 'P') ADVANCE(743);
      END_STATE();
    case 65:
      if (lookahead == 'I') ADVANCE(242);
      END_STATE();
    case 66:
      if (lookahead == 'I') ADVANCE(603);
      END_STATE();
    case 67:
      if (lookahead == 'I') ADVANCE(244);
      END_STATE();
    case 68:
      if (lookahead == 'L') ADVANCE(36);
      END_STATE();
    case 69:
      if (lookahead == 'L') ADVANCE(57);
      END_STATE();
    case 70:
      if (lookahead == 'M') ADVANCE(58);
      END_STATE();
    case 71:
      if (lookahead == 'M') ADVANCE(333);
      END_STATE();
    case 72:
      if (lookahead == 'N') ADVANCE(1088);
      if (lookahead == 'n') ADVANCE(89);
      END_STATE();
    case 73:
      if (lookahead == 'N') ADVANCE(86);
      END_STATE();
    case 74:
      if (lookahead == 'N') ADVANCE(608);
      if (lookahead == 'R') ADVANCE(316);
      if (lookahead == 'T') ADVANCE(883);
      END_STATE();
    case 75:
      if (lookahead == 'N') ADVANCE(320);
      END_STATE();
    case 76:
      if (lookahead == 'O') ADVANCE(73);
      if (lookahead == 'a') ADVANCE(479);
      if (lookahead == 'h') ADVANCE(122);
      if (lookahead == 'l') ADVANCE(852);
      if (lookahead == 'o') ADVANCE(224);
      if (lookahead == 'u') ADVANCE(731);
      END_STATE();
    case 77:
      if (lookahead == 'P') ADVANCE(78);
      if (lookahead == 'p') ADVANCE(392);
      END_STATE();
    case 78:
      if (lookahead == 'P') ADVANCE(43);
      END_STATE();
    case 79:
      if (lookahead == 'P') ADVANCE(155);
      END_STATE();
    case 80:
      if (lookahead == 'P') ADVANCE(494);
      END_STATE();
    case 81:
      if (lookahead == 'P') ADVANCE(156);
      END_STATE();
    case 82:
      if (lookahead == 'P') ADVANCE(159);
      END_STATE();
    case 83:
      if (lookahead == 'R') ADVANCE(1078);
      END_STATE();
    case 84:
      if (lookahead == 'R') ADVANCE(69);
      END_STATE();
    case 85:
      if (lookahead == 'R') ADVANCE(289);
      END_STATE();
    case 86:
      if (lookahead == 'S') ADVANCE(91);
      END_STATE();
    case 87:
      if (lookahead == 'S') ADVANCE(797);
      if (lookahead == 'n') ADVANCE(25);
      if (lookahead == 'p') ADVANCE(824);
      if (lookahead == 'r') ADVANCE(390);
      if (lookahead == 'u') ADVANCE(789);
      END_STATE();
    case 88:
      if (lookahead == 'S') ADVANCE(797);
      if (lookahead == 'p') ADVANCE(836);
      if (lookahead == 'r') ADVANCE(390);
      if (lookahead == 'u') ADVANCE(789);
      END_STATE();
    case 89:
      if (lookahead == 'S') ADVANCE(814);
      if (lookahead == 's') ADVANCE(305);
      if (lookahead == 't') ADVANCE(294);
      END_STATE();
    case 90:
      if (lookahead == 'S') ADVANCE(817);
      END_STATE();
    case 91:
      if (lookahead == 'T') ADVANCE(1077);
      END_STATE();
    case 92:
      if (lookahead == 'T') ADVANCE(1081);
      END_STATE();
    case 93:
      if (lookahead == 'T') ADVANCE(336);
      END_STATE();
    case 94:
      if (lookahead == 'T') ADVANCE(45);
      END_STATE();
    case 95:
      if (lookahead == 'T') ADVANCE(883);
      END_STATE();
    case 96:
      if (lookahead == 'U') ADVANCE(748);
      END_STATE();
    case 97:
      if (lookahead == 'Z') ADVANCE(335);
      END_STATE();
    case 98:
      if (lookahead == '[') ADVANCE(977);
      if (lookahead == 'l') ADVANCE(1345);
      if (lookahead == 'p') ADVANCE(1386);
      if (lookahead == 't') ADVANCE(1380);
      if (lookahead == 'v') ADVANCE(1160);
      if (lookahead == '}') ADVANCE(894);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(98);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 99:
      if (lookahead == 'a') ADVANCE(479);
      if (lookahead == 'l') ADVANCE(852);
      END_STATE();
    case 100:
      if (lookahead == 'a') ADVANCE(178);
      if (lookahead == 'i') ADVANCE(732);
      if (lookahead == 'o') ADVANCE(607);
      END_STATE();
    case 101:
      if (lookahead == 'a') ADVANCE(510);
      if (lookahead == 'i') ADVANCE(341);
      END_STATE();
    case 102:
      if (lookahead == 'a') ADVANCE(30);
      END_STATE();
    case 103:
      if (lookahead == 'a') ADVANCE(30);
      if (lookahead == 'e') ADVANCE(993);
      END_STATE();
    case 104:
      if (lookahead == 'a') ADVANCE(1031);
      END_STATE();
    case 105:
      if (lookahead == 'a') ADVANCE(967);
      END_STATE();
    case 106:
      if (lookahead == 'a') ADVANCE(913);
      END_STATE();
    case 107:
      if (lookahead == 'a') ADVANCE(958);
      END_STATE();
    case 108:
      if (lookahead == 'a') ADVANCE(1001);
      END_STATE();
    case 109:
      if (lookahead == 'a') ADVANCE(916);
      END_STATE();
    case 110:
      if (lookahead == 'a') ADVANCE(757);
      if (lookahead == 'e') ADVANCE(203);
      if (lookahead == 'i') ADVANCE(116);
      if (lookahead == 'o') ADVANCE(788);
      if (lookahead == 'r') ADVANCE(457);
      if (lookahead == 'u') ADVANCE(679);
      END_STATE();
    case 111:
      if (lookahead == 'a') ADVANCE(867);
      if (lookahead == 'i') ADVANCE(547);
      END_STATE();
    case 112:
      if (lookahead == 'a') ADVANCE(566);
      END_STATE();
    case 113:
      if (lookahead == 'a') ADVANCE(566);
      if (lookahead == 'o') ADVANCE(176);
      END_STATE();
    case 114:
      if (lookahead == 'a') ADVANCE(181);
      if (lookahead == 'e') ADVANCE(529);
      if (lookahead == 'i') ADVANCE(533);
      if (lookahead == 'o') ADVANCE(28);
      END_STATE();
    case 115:
      if (lookahead == 'a') ADVANCE(181);
      if (lookahead == 'e') ADVANCE(528);
      END_STATE();
    case 116:
      if (lookahead == 'a') ADVANCE(486);
      if (lookahead == 'c') ADVANCE(828);
      END_STATE();
    case 117:
      if (lookahead == 'a') ADVANCE(733);
      if (lookahead == 'o') ADVANCE(227);
      END_STATE();
    case 118:
      if (lookahead == 'a') ADVANCE(713);
      END_STATE();
    case 119:
      if (lookahead == 'a') ADVANCE(872);
      END_STATE();
    case 120:
      if (lookahead == 'a') ADVANCE(668);
      END_STATE();
    case 121:
      if (lookahead == 'a') ADVANCE(666);
      END_STATE();
    case 122:
      if (lookahead == 'a') ADVANCE(669);
      END_STATE();
    case 123:
      if (lookahead == 'a') ADVANCE(506);
      END_STATE();
    case 124:
      if (lookahead == 'a') ADVANCE(875);
      END_STATE();
    case 125:
      if (lookahead == 'a') ADVANCE(472);
      END_STATE();
    case 126:
      if (lookahead == 'a') ADVANCE(745);
      END_STATE();
    case 127:
      if (lookahead == 'a') ADVANCE(574);
      END_STATE();
    case 128:
      if (lookahead == 'a') ADVANCE(393);
      END_STATE();
    case 129:
      if (lookahead == 'a') ADVANCE(524);
      END_STATE();
    case 130:
      if (lookahead == 'a') ADVANCE(525);
      END_STATE();
    case 131:
      if (lookahead == 'a') ADVANCE(489);
      END_STATE();
    case 132:
      if (lookahead == 'a') ADVANCE(474);
      END_STATE();
    case 133:
      if (lookahead == 'a') ADVANCE(526);
      END_STATE();
    case 134:
      if (lookahead == 'a') ADVANCE(554);
      END_STATE();
    case 135:
      if (lookahead == 'a') ADVANCE(237);
      END_STATE();
    case 136:
      if (lookahead == 'a') ADVANCE(475);
      END_STATE();
    case 137:
      if (lookahead == 'a') ADVANCE(485);
      END_STATE();
    case 138:
      if (lookahead == 'a') ADVANCE(477);
      END_STATE();
    case 139:
      if (lookahead == 'a') ADVANCE(478);
      END_STATE();
    case 140:
      if (lookahead == 'a') ADVANCE(481);
      END_STATE();
    case 141:
      if (lookahead == 'a') ADVANCE(769);
      END_STATE();
    case 142:
      if (lookahead == 'a') ADVANCE(590);
      END_STATE();
    case 143:
      if (lookahead == 'a') ADVANCE(689);
      END_STATE();
    case 144:
      if (lookahead == 'a') ADVANCE(691);
      END_STATE();
    case 145:
      if (lookahead == 'a') ADVANCE(693);
      END_STATE();
    case 146:
      if (lookahead == 'a') ADVANCE(801);
      END_STATE();
    case 147:
      if (lookahead == 'a') ADVANCE(803);
      END_STATE();
    case 148:
      if (lookahead == 'a') ADVANCE(805);
      END_STATE();
    case 149:
      if (lookahead == 'a') ADVANCE(806);
      if (lookahead == 'e') ADVANCE(204);
      if (lookahead == 'r') ADVANCE(457);
      END_STATE();
    case 150:
      if (lookahead == 'a') ADVANCE(231);
      END_STATE();
    case 151:
      if (lookahead == 'a') ADVANCE(588);
      END_STATE();
    case 152:
      if (lookahead == 'a') ADVANCE(197);
      END_STATE();
    case 153:
      if (lookahead == 'a') ADVANCE(730);
      END_STATE();
    case 154:
      if (lookahead == 'a') ADVANCE(537);
      END_STATE();
    case 155:
      if (lookahead == 'a') ADVANCE(395);
      END_STATE();
    case 156:
      if (lookahead == 'a') ADVANCE(396);
      END_STATE();
    case 157:
      if (lookahead == 'a') ADVANCE(578);
      END_STATE();
    case 158:
      if (lookahead == 'a') ADVANCE(739);
      END_STATE();
    case 159:
      if (lookahead == 'a') ADVANCE(397);
      END_STATE();
    case 160:
      if (lookahead == 'a') ADVANCE(808);
      END_STATE();
    case 161:
      if (lookahead == 'a') ADVANCE(182);
      if (lookahead == 'e') ADVANCE(544);
      if (lookahead == 'h') ADVANCE(291);
      if (lookahead == 'r') ADVANCE(414);
      END_STATE();
    case 162:
      if (lookahead == 'a') ADVANCE(747);
      END_STATE();
    case 163:
      if (lookahead == 'a') ADVANCE(183);
      END_STATE();
    case 164:
      if (lookahead == 'a') ADVANCE(184);
      END_STATE();
    case 165:
      if (lookahead == 'a') ADVANCE(185);
      if (lookahead == 'e') ADVANCE(529);
      if (lookahead == 'i') ADVANCE(533);
      if (lookahead == 'o') ADVANCE(28);
      END_STATE();
    case 166:
      if (lookahead == 'a') ADVANCE(186);
      if (lookahead == 'e') ADVANCE(544);
      if (lookahead == 'h') ADVANCE(291);
      if (lookahead == 'r') ADVANCE(413);
      END_STATE();
    case 167:
      if (lookahead == 'a') ADVANCE(187);
      if (lookahead == 'h') ADVANCE(291);
      if (lookahead == 'r') ADVANCE(413);
      END_STATE();
    case 168:
      if (lookahead == 'a') ADVANCE(829);
      END_STATE();
    case 169:
      if (lookahead == 'a') ADVANCE(830);
      END_STATE();
    case 170:
      if (lookahead == 'a') ADVANCE(832);
      END_STATE();
    case 171:
      if (lookahead == 'a') ADVANCE(833);
      END_STATE();
    case 172:
      if (lookahead == 'a') ADVANCE(834);
      END_STATE();
    case 173:
      if (lookahead == 'a') ADVANCE(835);
      END_STATE();
    case 174:
      if (lookahead == 'a') ADVANCE(665);
      if (lookahead == 'h') ADVANCE(122);
      if (lookahead == 'o') ADVANCE(241);
      if (lookahead == 'u') ADVANCE(731);
      END_STATE();
    case 175:
      if (lookahead == 'a') ADVANCE(189);
      END_STATE();
    case 176:
      if (lookahead == 'b') ADVANCE(1018);
      END_STATE();
    case 177:
      if (lookahead == 'b') ADVANCE(465);
      END_STATE();
    case 178:
      if (lookahead == 'b') ADVANCE(292);
      END_STATE();
    case 179:
      if (lookahead == 'b') ADVANCE(791);
      END_STATE();
    case 180:
      if (lookahead == 'b') ADVANCE(1219);
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(180);
      if (('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 181:
      if (lookahead == 'b') ADVANCE(493);
      END_STATE();
    case 182:
      if (lookahead == 'b') ADVANCE(496);
      END_STATE();
    case 183:
      if (lookahead == 'b') ADVANCE(502);
      END_STATE();
    case 184:
      if (lookahead == 'b') ADVANCE(509);
      END_STATE();
    case 185:
      if (lookahead == 'b') ADVANCE(503);
      END_STATE();
    case 186:
      if (lookahead == 'b') ADVANCE(504);
      END_STATE();
    case 187:
      if (lookahead == 'b') ADVANCE(505);
      END_STATE();
    case 188:
      if (lookahead == 'b') ADVANCE(330);
      END_STATE();
    case 189:
      if (lookahead == 'b') ADVANCE(520);
      END_STATE();
    case 190:
      if (lookahead == 'c') ADVANCE(193);
      END_STATE();
    case 191:
      if (lookahead == 'c') ADVANCE(54);
      END_STATE();
    case 192:
      if (lookahead == 'c') ADVANCE(456);
      if (lookahead == 'l') ADVANCE(344);
      END_STATE();
    case 193:
      if (lookahead == 'c') ADVANCE(616);
      if (lookahead == 't') ADVANCE(433);
      END_STATE();
    case 194:
      if (lookahead == 'c') ADVANCE(625);
      if (lookahead == 's') ADVANCE(313);
      END_STATE();
    case 195:
      if (lookahead == 'c') ADVANCE(297);
      END_STATE();
    case 196:
      if (lookahead == 'c') ADVANCE(778);
      END_STATE();
    case 197:
      if (lookahead == 'c') ADVANCE(299);
      END_STATE();
    case 198:
      if (lookahead == 'c') ADVANCE(273);
      END_STATE();
    case 199:
      if (lookahead == 'c') ADVANCE(125);
      END_STATE();
    case 200:
      if (lookahead == 'c') ADVANCE(125);
      if (lookahead == 'o') ADVANCE(468);
      END_STATE();
    case 201:
      if (lookahead == 'c') ADVANCE(714);
      if (lookahead == 't') ADVANCE(55);
      END_STATE();
    case 202:
      if (lookahead == 'c') ADVANCE(639);
      END_STATE();
    case 203:
      if (lookahead == 'c') ADVANCE(459);
      if (lookahead == 'l') ADVANCE(344);
      END_STATE();
    case 204:
      if (lookahead == 'c') ADVANCE(460);
      END_STATE();
    case 205:
      if (lookahead == 'c') ADVANCE(171);
      END_STATE();
    case 206:
      if (lookahead == 'd') ADVANCE(421);
      if (lookahead == 'n') ADVANCE(209);
      if (lookahead == 'x') ADVANCE(816);
      END_STATE();
    case 207:
      if (lookahead == 'd') ADVANCE(421);
      if (lookahead == 'x') ADVANCE(816);
      END_STATE();
    case 208:
      if (lookahead == 'd') ADVANCE(96);
      END_STATE();
    case 209:
      if (lookahead == 'd') ADVANCE(96);
      if (lookahead == 'u') ADVANCE(522);
      END_STATE();
    case 210:
      if (lookahead == 'd') ADVANCE(1469);
      END_STATE();
    case 211:
      if (lookahead == 'd') ADVANCE(52);
      END_STATE();
    case 212:
      if (lookahead == 'd') ADVANCE(1008);
      END_STATE();
    case 213:
      if (lookahead == 'd') ADVANCE(1061);
      END_STATE();
    case 214:
      if (lookahead == 'd') ADVANCE(1049);
      END_STATE();
    case 215:
      if (lookahead == 'd') ADVANCE(1010);
      END_STATE();
    case 216:
      if (lookahead == 'd') ADVANCE(1459);
      END_STATE();
    case 217:
      if (lookahead == 'd') ADVANCE(899);
      END_STATE();
    case 218:
      if (lookahead == 'd') ADVANCE(954);
      END_STATE();
    case 219:
      if (lookahead == 'd') ADVANCE(917);
      END_STATE();
    case 220:
      if (lookahead == 'd') ADVANCE(952);
      END_STATE();
    case 221:
      if (lookahead == 'd') ADVANCE(941);
      END_STATE();
    case 222:
      if (lookahead == 'd') ADVANCE(1060);
      END_STATE();
    case 223:
      if (lookahead == 'd') ADVANCE(416);
      END_STATE();
    case 224:
      if (lookahead == 'd') ADVANCE(250);
      END_STATE();
    case 225:
      if (lookahead == 'd') ADVANCE(408);
      END_STATE();
    case 226:
      if (lookahead == 'd') ADVANCE(856);
      END_STATE();
    case 227:
      if (lookahead == 'd') ADVANCE(290);
      if (lookahead == 'n') ADVANCE(737);
      if (lookahead == 'u') ADVANCE(575);
      END_STATE();
    case 228:
      if (lookahead == 'd') ADVANCE(290);
      if (lookahead == 'u') ADVANCE(575);
      END_STATE();
    case 229:
      if (lookahead == 'd') ADVANCE(722);
      END_STATE();
    case 230:
      if (lookahead == 'd') ADVANCE(160);
      END_STATE();
    case 231:
      if (lookahead == 'd') ADVANCE(261);
      END_STATE();
    case 232:
      if (lookahead == 'd') ADVANCE(351);
      END_STATE();
    case 233:
      if (lookahead == 'd') ADVANCE(432);
      END_STATE();
    case 234:
      if (lookahead == 'd') ADVANCE(146);
      END_STATE();
    case 235:
      if (lookahead == 'd') ADVANCE(436);
      END_STATE();
    case 236:
      if (lookahead == 'd') ADVANCE(428);
      END_STATE();
    case 237:
      if (lookahead == 'd') ADVANCE(148);
      END_STATE();
    case 238:
      if (lookahead == 'd') ADVANCE(635);
      END_STATE();
    case 239:
      if (lookahead == 'd') ADVANCE(331);
      END_STATE();
    case 240:
      if (lookahead == 'd') ADVANCE(34);
      END_STATE();
    case 241:
      if (lookahead == 'd') ADVANCE(365);
      END_STATE();
    case 242:
      if (lookahead == 'd') ADVANCE(363);
      END_STATE();
    case 243:
      if (lookahead == 'd') ADVANCE(462);
      END_STATE();
    case 244:
      if (lookahead == 'd') ADVANCE(373);
      END_STATE();
    case 245:
      if (lookahead == 'e') ADVANCE(868);
      END_STATE();
    case 246:
      if (lookahead == 'e') ADVANCE(868);
      if (lookahead == 'o') ADVANCE(685);
      END_STATE();
    case 247:
      if (lookahead == 'e') ADVANCE(194);
      END_STATE();
    case 248:
      if (lookahead == 'e') ADVANCE(870);
      END_STATE();
    case 249:
      if (lookahead == 'e') ADVANCE(988);
      END_STATE();
    case 250:
      if (lookahead == 'e') ADVANCE(1046);
      END_STATE();
    case 251:
      if (lookahead == 'e') ADVANCE(995);
      END_STATE();
    case 252:
      if (lookahead == 'e') ADVANCE(1489);
      END_STATE();
    case 253:
      if (lookahead == 'e') ADVANCE(1067);
      END_STATE();
    case 254:
      if (lookahead == 'e') ADVANCE(1460);
      END_STATE();
    case 255:
      if (lookahead == 'e') ADVANCE(74);
      END_STATE();
    case 256:
      if (lookahead == 'e') ADVANCE(1462);
      END_STATE();
    case 257:
      if (lookahead == 'e') ADVANCE(892);
      END_STATE();
    case 258:
      if (lookahead == 'e') ADVANCE(1064);
      END_STATE();
    case 259:
      if (lookahead == 'e') ADVANCE(1481);
      END_STATE();
    case 260:
      if (lookahead == 'e') ADVANCE(950);
      END_STATE();
    case 261:
      if (lookahead == 'e') ADVANCE(897);
      END_STATE();
    case 262:
      if (lookahead == 'e') ADVANCE(1074);
      END_STATE();
    case 263:
      if (lookahead == 'e') ADVANCE(997);
      END_STATE();
    case 264:
      if (lookahead == 'e') ADVANCE(960);
      END_STATE();
    case 265:
      if (lookahead == 'e') ADVANCE(41);
      END_STATE();
    case 266:
      if (lookahead == 'e') ADVANCE(938);
      END_STATE();
    case 267:
      if (lookahead == 'e') ADVANCE(939);
      END_STATE();
    case 268:
      if (lookahead == 'e') ADVANCE(1482);
      END_STATE();
    case 269:
      if (lookahead == 'e') ADVANCE(1024);
      END_STATE();
    case 270:
      if (lookahead == 'e') ADVANCE(907);
      END_STATE();
    case 271:
      if (lookahead == 'e') ADVANCE(1098);
      END_STATE();
    case 272:
      if (lookahead == 'e') ADVANCE(940);
      END_STATE();
    case 273:
      if (lookahead == 'e') ADVANCE(951);
      END_STATE();
    case 274:
      if (lookahead == 'e') ADVANCE(891);
      END_STATE();
    case 275:
      if (lookahead == 'e') ADVANCE(201);
      if (lookahead == 'i') ADVANCE(568);
      if (lookahead == 'u') ADVANCE(179);
      if (lookahead == 'y') ADVANCE(744);
      END_STATE();
    case 276:
      if (lookahead == 'e') ADVANCE(201);
      if (lookahead == 'y') ADVANCE(749);
      END_STATE();
    case 277:
      if (lookahead == 'e') ADVANCE(223);
      if (lookahead == 'o') ADVANCE(225);
      END_STATE();
    case 278:
      if (lookahead == 'e') ADVANCE(29);
      END_STATE();
    case 279:
      if (lookahead == 'e') ADVANCE(60);
      END_STATE();
    case 280:
      if (lookahead == 'e') ADVANCE(378);
      END_STATE();
    case 281:
      if (lookahead == 'e') ADVANCE(44);
      END_STATE();
    case 282:
      if (lookahead == 'e') ADVANCE(196);
      END_STATE();
    case 283:
      if (lookahead == 'e') ADVANCE(391);
      END_STATE();
    case 284:
      if (lookahead == 'e') ADVANCE(483);
      END_STATE();
    case 285:
      if (lookahead == 'e') ADVANCE(483);
      if (lookahead == 'l') ADVANCE(818);
      if (lookahead == 'n') ADVANCE(211);
      END_STATE();
    case 286:
      if (lookahead == 'e') ADVANCE(758);
      if (lookahead == 'u') ADVANCE(412);
      END_STATE();
    case 287:
      if (lookahead == 'e') ADVANCE(59);
      END_STATE();
    case 288:
      if (lookahead == 'e') ADVANCE(95);
      END_STATE();
    case 289:
      if (lookahead == 'e') ADVANCE(202);
      END_STATE();
    case 290:
      if (lookahead == 'e') ADVANCE(857);
      END_STATE();
    case 291:
      if (lookahead == 'e') ADVANCE(549);
      END_STATE();
    case 292:
      if (lookahead == 'e') ADVANCE(471);
      END_STATE();
    case 293:
      if (lookahead == 'e') ADVANCE(573);
      if (lookahead == 'u') ADVANCE(550);
      END_STATE();
    case 294:
      if (lookahead == 'e') ADVANCE(399);
      END_STATE();
    case 295:
      if (lookahead == 'e') ADVANCE(523);
      END_STATE();
    case 296:
      if (lookahead == 'e') ADVANCE(681);
      END_STATE();
    case 297:
      if (lookahead == 'e') ADVANCE(226);
      END_STATE();
    case 298:
      if (lookahead == 'e') ADVANCE(694);
      END_STATE();
    case 299:
      if (lookahead == 'e') ADVANCE(725);
      END_STATE();
    case 300:
      if (lookahead == 'e') ADVANCE(848);
      END_STATE();
    case 301:
      if (lookahead == 'e') ADVANCE(696);
      END_STATE();
    case 302:
      if (lookahead == 'e') ADVANCE(216);
      END_STATE();
    case 303:
      if (lookahead == 'e') ADVANCE(531);
      END_STATE();
    case 304:
      if (lookahead == 'e') ADVANCE(129);
      END_STATE();
    case 305:
      if (lookahead == 'e') ADVANCE(704);
      if (lookahead == 't') ADVANCE(131);
      END_STATE();
    case 306:
      if (lookahead == 'e') ADVANCE(881);
      END_STATE();
    case 307:
      if (lookahead == 'e') ADVANCE(879);
      END_STATE();
    case 308:
      if (lookahead == 'e') ADVANCE(680);
      END_STATE();
    case 309:
      if (lookahead == 'e') ADVANCE(130);
      END_STATE();
    case 310:
      if (lookahead == 'e') ADVANCE(530);
      END_STATE();
    case 311:
      if (lookahead == 'e') ADVANCE(527);
      END_STATE();
    case 312:
      if (lookahead == 'e') ADVANCE(670);
      END_STATE();
    case 313:
      if (lookahead == 'e') ADVANCE(764);
      END_STATE();
    case 314:
      if (lookahead == 'e') ADVANCE(219);
      END_STATE();
    case 315:
      if (lookahead == 'e') ADVANCE(671);
      END_STATE();
    case 316:
      if (lookahead == 'e') ADVANCE(519);
      END_STATE();
    case 317:
      if (lookahead == 'e') ADVANCE(133);
      END_STATE();
    case 318:
      if (lookahead == 'e') ADVANCE(672);
      END_STATE();
    case 319:
      if (lookahead == 'e') ADVANCE(557);
      END_STATE();
    case 320:
      if (lookahead == 'e') ADVANCE(767);
      END_STATE();
    case 321:
      if (lookahead == 'e') ADVANCE(673);
      END_STATE();
    case 322:
      if (lookahead == 'e') ADVANCE(792);
      END_STATE();
    case 323:
      if (lookahead == 'e') ADVANCE(674);
      END_STATE();
    case 324:
      if (lookahead == 'e') ADVANCE(682);
      END_STATE();
    case 325:
      if (lookahead == 'e') ADVANCE(770);
      END_STATE();
    case 326:
      if (lookahead == 'e') ADVANCE(675);
      END_STATE();
    case 327:
      if (lookahead == 'e') ADVANCE(676);
      END_STATE();
    case 328:
      if (lookahead == 'e') ADVANCE(774);
      END_STATE();
    case 329:
      if (lookahead == 'e') ADVANCE(677);
      END_STATE();
    case 330:
      if (lookahead == 'e') ADVANCE(695);
      END_STATE();
    case 331:
      if (lookahead == 'e') ADVANCE(678);
      END_STATE();
    case 332:
      if (lookahead == 'e') ADVANCE(697);
      END_STATE();
    case 333:
      if (lookahead == 'e') ADVANCE(802);
      END_STATE();
    case 334:
      if (lookahead == 'e') ADVANCE(794);
      END_STATE();
    case 335:
      if (lookahead == 'e') ADVANCE(700);
      END_STATE();
    case 336:
      if (lookahead == 'e') ADVANCE(869);
      END_STATE();
    case 337:
      if (lookahead == 'e') ADVANCE(141);
      END_STATE();
    case 338:
      if (lookahead == 'e') ADVANCE(62);
      END_STATE();
    case 339:
      if (lookahead == 'e') ADVANCE(687);
      END_STATE();
    case 340:
      if (lookahead == 'e') ADVANCE(134);
      END_STATE();
    case 341:
      if (lookahead == 'e') ADVANCE(484);
      if (lookahead == 'l') ADVANCE(819);
      END_STATE();
    case 342:
      if (lookahead == 'e') ADVANCE(61);
      END_STATE();
    case 343:
      if (lookahead == 'e') ADVANCE(708);
      END_STATE();
    case 344:
      if (lookahead == 'e') ADVANCE(804);
      END_STATE();
    case 345:
      if (lookahead == 'e') ADVANCE(487);
      if (lookahead == 'l') ADVANCE(823);
      END_STATE();
    case 346:
      if (lookahead == 'e') ADVANCE(705);
      END_STATE();
    case 347:
      if (lookahead == 'e') ADVANCE(711);
      END_STATE();
    case 348:
      if (lookahead == 'e') ADVANCE(514);
      if (lookahead == 'r') ADVANCE(422);
      END_STATE();
    case 349:
      if (lookahead == 'e') ADVANCE(807);
      END_STATE();
    case 350:
      if (lookahead == 'e') ADVANCE(495);
      END_STATE();
    case 351:
      if (lookahead == 'e') ADVANCE(579);
      END_STATE();
    case 352:
      if (lookahead == 'e') ADVANCE(497);
      if (lookahead == 'l') ADVANCE(819);
      END_STATE();
    case 353:
      if (lookahead == 'e') ADVANCE(709);
      END_STATE();
    case 354:
      if (lookahead == 'e') ADVANCE(580);
      END_STATE();
    case 355:
      if (lookahead == 'e') ADVANCE(581);
      END_STATE();
    case 356:
      if (lookahead == 'e') ADVANCE(809);
      END_STATE();
    case 357:
      if (lookahead == 'e') ADVANCE(582);
      END_STATE();
    case 358:
      if (lookahead == 'e') ADVANCE(583);
      END_STATE();
    case 359:
      if (lookahead == 'e') ADVANCE(584);
      END_STATE();
    case 360:
      if (lookahead == 'e') ADVANCE(585);
      END_STATE();
    case 361:
      if (lookahead == 'e') ADVANCE(586);
      END_STATE();
    case 362:
      if (lookahead == 'e') ADVANCE(234);
      END_STATE();
    case 363:
      if (lookahead == 'e') ADVANCE(599);
      END_STATE();
    case 364:
      if (lookahead == 'e') ADVANCE(401);
      END_STATE();
    case 365:
      if (lookahead == 'e') ADVANCE(846);
      END_STATE();
    case 366:
      if (lookahead == 'e') ADVANCE(516);
      END_STATE();
    case 367:
      if (lookahead == 'e') ADVANCE(839);
      END_STATE();
    case 368:
      if (lookahead == 'e') ADVANCE(518);
      END_STATE();
    case 369:
      if (lookahead == 'e') ADVANCE(49);
      END_STATE();
    case 370:
      if (lookahead == 'e') ADVANCE(35);
      END_STATE();
    case 371:
      if (lookahead == 'e') ADVANCE(719);
      END_STATE();
    case 372:
      if (lookahead == 'e') ADVANCE(66);
      END_STATE();
    case 373:
      if (lookahead == 'e') ADVANCE(604);
      END_STATE();
    case 374:
      if (lookahead == 'f') ADVANCE(976);
      END_STATE();
    case 375:
      if (lookahead == 'f') ADVANCE(873);
      END_STATE();
    case 376:
      if (lookahead == 'f') ADVANCE(874);
      END_STATE();
    case 377:
      if (lookahead == 'f') ADVANCE(884);
      END_STATE();
    case 378:
      if (lookahead == 'f') ADVANCE(649);
      END_STATE();
    case 379:
      if (lookahead == 'f') ADVANCE(411);
      END_STATE();
    case 380:
      if (lookahead == 'f') ADVANCE(429);
      END_STATE();
    case 381:
      if (lookahead == 'f') ADVANCE(454);
      END_STATE();
    case 382:
      if (lookahead == 'f') ADVANCE(461);
      END_STATE();
    case 383:
      if (lookahead == 'f') ADVANCE(648);
      END_STATE();
    case 384:
      if (lookahead == 'f') ADVANCE(821);
      if (lookahead == 's') ADVANCE(734);
      END_STATE();
    case 385:
      if (lookahead == 'f') ADVANCE(885);
      END_STATE();
    case 386:
      if (lookahead == 'f') ADVANCE(655);
      END_STATE();
    case 387:
      if (lookahead == 'f') ADVANCE(463);
      END_STATE();
    case 388:
      if (lookahead == 'g') ADVANCE(63);
      END_STATE();
    case 389:
      if (lookahead == 'g') ADVANCE(1014);
      END_STATE();
    case 390:
      if (lookahead == 'g') ADVANCE(127);
      END_STATE();
    case 391:
      if (lookahead == 'g') ADVANCE(419);
      END_STATE();
    case 392:
      if (lookahead == 'g') ADVANCE(690);
      END_STATE();
    case 393:
      if (lookahead == 'g') ADVANCE(262);
      END_STATE();
    case 394:
      if (lookahead == 'g') ADVANCE(268);
      END_STATE();
    case 395:
      if (lookahead == 'g') ADVANCE(278);
      END_STATE();
    case 396:
      if (lookahead == 'g') ADVANCE(287);
      END_STATE();
    case 397:
      if (lookahead == 'g') ADVANCE(342);
      END_STATE();
    case 398:
      if (lookahead == 'g') ADVANCE(500);
      END_STATE();
    case 399:
      if (lookahead == 'g') ADVANCE(318);
      END_STATE();
    case 400:
      if (lookahead == 'g') ADVANCE(323);
      END_STATE();
    case 401:
      if (lookahead == 'g') ADVANCE(327);
      END_STATE();
    case 402:
      if (lookahead == 'g') ADVANCE(400);
      END_STATE();
    case 403:
      if (lookahead == 'h') ADVANCE(346);
      END_STATE();
    case 404:
      if (lookahead == 'i') ADVANCE(388);
      if (lookahead == 'l') ADVANCE(113);
      if (lookahead == 'o') ADVANCE(611);
      if (lookahead == 'y') ADVANCE(795);
      END_STATE();
    case 405:
      if (lookahead == 'i') ADVANCE(388);
      if (lookahead == 'l') ADVANCE(618);
      if (lookahead == 'o') ADVANCE(611);
      if (lookahead == 'y') ADVANCE(795);
      END_STATE();
    case 406:
      if (lookahead == 'i') ADVANCE(886);
      END_STATE();
    case 407:
      if (lookahead == 'i') ADVANCE(512);
      END_STATE();
    case 408:
      if (lookahead == 'i') ADVANCE(375);
      END_STATE();
    case 409:
      if (lookahead == 'i') ADVANCE(568);
      if (lookahead == 'u') ADVANCE(179);
      if (lookahead == 'y') ADVANCE(750);
      END_STATE();
    case 410:
      if (lookahead == 'i') ADVANCE(379);
      END_STATE();
    case 411:
      if (lookahead == 'i') ADVANCE(205);
      END_STATE();
    case 412:
      if (lookahead == 'i') ADVANCE(212);
      END_STATE();
    case 413:
      if (lookahead == 'i') ADVANCE(402);
      END_STATE();
    case 414:
      if (lookahead == 'i') ADVANCE(402);
      if (lookahead == 'u') ADVANCE(254);
      END_STATE();
    case 415:
      if (lookahead == 'i') ADVANCE(729);
      END_STATE();
    case 416:
      if (lookahead == 'i') ADVANCE(104);
      END_STATE();
    case 417:
      if (lookahead == 'i') ADVANCE(473);
      END_STATE();
    case 418:
      if (lookahead == 'i') ADVANCE(157);
      END_STATE();
    case 419:
      if (lookahead == 'i') ADVANCE(551);
      END_STATE();
    case 420:
      if (lookahead == 'i') ADVANCE(230);
      END_STATE();
    case 421:
      if (lookahead == 'i') ADVANCE(796);
      END_STATE();
    case 422:
      if (lookahead == 'i') ADVANCE(513);
      END_STATE();
    case 423:
      if (lookahead == 'i') ADVANCE(517);
      END_STATE();
    case 424:
      if (lookahead == 'i') ADVANCE(763);
      END_STATE();
    case 425:
      if (lookahead == 'i') ADVANCE(717);
      END_STATE();
    case 426:
      if (lookahead == 'i') ADVANCE(772);
      END_STATE();
    case 427:
      if (lookahead == 'i') ADVANCE(776);
      END_STATE();
    case 428:
      if (lookahead == 'i') ADVANCE(780);
      END_STATE();
    case 429:
      if (lookahead == 'i') ADVANCE(314);
      END_STATE();
    case 430:
      if (lookahead == 'i') ADVANCE(350);
      END_STATE();
    case 431:
      if (lookahead == 'i') ADVANCE(536);
      END_STATE();
    case 432:
      if (lookahead == 'i') ADVANCE(376);
      END_STATE();
    case 433:
      if (lookahead == 'i') ADVANCE(623);
      END_STATE();
    case 434:
      if (lookahead == 'i') ADVANCE(380);
      END_STATE();
    case 435:
      if (lookahead == 'i') ADVANCE(284);
      END_STATE();
    case 436:
      if (lookahead == 'i') ADVANCE(377);
      END_STATE();
    case 437:
      if (lookahead == 'i') ADVANCE(626);
      END_STATE();
    case 438:
      if (lookahead == 'i') ADVANCE(382);
      END_STATE();
    case 439:
      if (lookahead == 'i') ADVANCE(627);
      END_STATE();
    case 440:
      if (lookahead == 'i') ADVANCE(381);
      END_STATE();
    case 441:
      if (lookahead == 'i') ADVANCE(492);
      END_STATE();
    case 442:
      if (lookahead == 'i') ADVANCE(629);
      END_STATE();
    case 443:
      if (lookahead == 'i') ADVANCE(740);
      END_STATE();
    case 444:
      if (lookahead == 'i') ADVANCE(630);
      END_STATE();
    case 445:
      if (lookahead == 'i') ADVANCE(631);
      END_STATE();
    case 446:
      if (lookahead == 'i') ADVANCE(632);
      END_STATE();
    case 447:
      if (lookahead == 'i') ADVANCE(633);
      END_STATE();
    case 448:
      if (lookahead == 'i') ADVANCE(634);
      END_STATE();
    case 449:
      if (lookahead == 'i') ADVANCE(636);
      END_STATE();
    case 450:
      if (lookahead == 'i') ADVANCE(637);
      END_STATE();
    case 451:
      if (lookahead == 'i') ADVANCE(638);
      END_STATE();
    case 452:
      if (lookahead == 'i') ADVANCE(640);
      END_STATE();
    case 453:
      if (lookahead == 'i') ADVANCE(641);
      END_STATE();
    case 454:
      if (lookahead == 'i') ADVANCE(332);
      END_STATE();
    case 455:
      if (lookahead == 'i') ADVANCE(345);
      END_STATE();
    case 456:
      if (lookahead == 'i') ADVANCE(539);
      END_STATE();
    case 457:
      if (lookahead == 'i') ADVANCE(482);
      END_STATE();
    case 458:
      if (lookahead == 'i') ADVANCE(352);
      END_STATE();
    case 459:
      if (lookahead == 'i') ADVANCE(540);
      END_STATE();
    case 460:
      if (lookahead == 'i') ADVANCE(541);
      END_STATE();
    case 461:
      if (lookahead == 'i') ADVANCE(164);
      END_STATE();
    case 462:
      if (lookahead == 'i') ADVANCE(385);
      END_STATE();
    case 463:
      if (lookahead == 'i') ADVANCE(175);
      END_STATE();
    case 464:
      if (lookahead == 'i') ADVANCE(387);
      END_STATE();
    case 465:
      if (lookahead == 'j') ADVANCE(282);
      END_STATE();
    case 466:
      if (lookahead == 'k') ADVANCE(97);
      END_STATE();
    case 467:
      if (lookahead == 'k') ADVANCE(843);
      END_STATE();
    case 468:
      if (lookahead == 'k') ADVANCE(844);
      END_STATE();
    case 469:
      if (lookahead == 'k') ADVANCE(845);
      END_STATE();
    case 470:
      if (lookahead == 'k') ADVANCE(319);
      END_STATE();
    case 471:
      if (lookahead == 'l') ADVANCE(1042);
      END_STATE();
    case 472:
      if (lookahead == 'l') ADVANCE(1096);
      END_STATE();
    case 473:
      if (lookahead == 'l') ADVANCE(1473);
      END_STATE();
    case 474:
      if (lookahead == 'l') ADVANCE(901);
      END_STATE();
    case 475:
      if (lookahead == 'l') ADVANCE(986);
      END_STATE();
    case 476:
      if (lookahead == 'l') ADVANCE(896);
      END_STATE();
    case 477:
      if (lookahead == 'l') ADVANCE(904);
      END_STATE();
    case 478:
      if (lookahead == 'l') ADVANCE(985);
      END_STATE();
    case 479:
      if (lookahead == 'l') ADVANCE(191);
      if (lookahead == 'p') ADVANCE(827);
      END_STATE();
    case 480:
      if (lookahead == 'l') ADVANCE(37);
      END_STATE();
    case 481:
      if (lookahead == 'l') ADVANCE(80);
      END_STATE();
    case 482:
      if (lookahead == 'l') ADVANCE(480);
      END_STATE();
    case 483:
      if (lookahead == 'l') ADVANCE(240);
      END_STATE();
    case 484:
      if (lookahead == 'l') ADVANCE(213);
      END_STATE();
    case 485:
      if (lookahead == 'l') ADVANCE(850);
      END_STATE();
    case 486:
      if (lookahead == 'l') ADVANCE(622);
      END_STATE();
    case 487:
      if (lookahead == 'l') ADVANCE(217);
      END_STATE();
    case 488:
      if (lookahead == 'l') ADVANCE(126);
      END_STATE();
    case 489:
      if (lookahead == 'l') ADVANCE(476);
      END_STATE();
    case 490:
      if (lookahead == 'l') ADVANCE(153);
      END_STATE();
    case 491:
      if (lookahead == 'l') ADVANCE(340);
      END_STATE();
    case 492:
      if (lookahead == 'l') ADVANCE(239);
      END_STATE();
    case 493:
      if (lookahead == 'l') ADVANCE(255);
      END_STATE();
    case 494:
      if (lookahead == 'l') ADVANCE(152);
      END_STATE();
    case 495:
      if (lookahead == 'l') ADVANCE(229);
      END_STATE();
    case 496:
      if (lookahead == 'l') ADVANCE(257);
      END_STATE();
    case 497:
      if (lookahead == 'l') ADVANCE(222);
      END_STATE();
    case 498:
      if (lookahead == 'l') ADVANCE(107);
      END_STATE();
    case 499:
      if (lookahead == 'l') ADVANCE(108);
      END_STATE();
    case 500:
      if (lookahead == 'l') ADVANCE(279);
      END_STATE();
    case 501:
      if (lookahead == 'l') ADVANCE(112);
      END_STATE();
    case 502:
      if (lookahead == 'l') ADVANCE(264);
      END_STATE();
    case 503:
      if (lookahead == 'l') ADVANCE(288);
      END_STATE();
    case 504:
      if (lookahead == 'l') ADVANCE(274);
      END_STATE();
    case 505:
      if (lookahead == 'l') ADVANCE(362);
      END_STATE();
    case 506:
      if (lookahead == 'l') ADVANCE(420);
      END_STATE();
    case 507:
      if (lookahead == 'l') ADVANCE(735);
      END_STATE();
    case 508:
      if (lookahead == 'l') ADVANCE(735);
      if (lookahead == 'n') ADVANCE(210);
      if (lookahead == 'x') ADVANCE(424);
      END_STATE();
    case 509:
      if (lookahead == 'l') ADVANCE(338);
      END_STATE();
    case 510:
      if (lookahead == 'l') ADVANCE(738);
      END_STATE();
    case 511:
      if (lookahead == 'l') ADVANCE(39);
      END_STATE();
    case 512:
      if (lookahead == 'l') ADVANCE(818);
      if (lookahead == 'n') ADVANCE(211);
      END_STATE();
    case 513:
      if (lookahead == 'l') ADVANCE(511);
      END_STATE();
    case 514:
      if (lookahead == 'l') ADVANCE(349);
      END_STATE();
    case 515:
      if (lookahead == 'l') ADVANCE(162);
      END_STATE();
    case 516:
      if (lookahead == 'l') ADVANCE(356);
      END_STATE();
    case 517:
      if (lookahead == 'l') ADVANCE(822);
      END_STATE();
    case 518:
      if (lookahead == 'l') ADVANCE(367);
      END_STATE();
    case 519:
      if (lookahead == 'l') ADVANCE(170);
      END_STATE();
    case 520:
      if (lookahead == 'l') ADVANCE(372);
      END_STATE();
    case 521:
      if (lookahead == 'm') ADVANCE(1073);
      END_STATE();
    case 522:
      if (lookahead == 'm') ADVANCE(1465);
      END_STATE();
    case 523:
      if (lookahead == 'm') ADVANCE(906);
      END_STATE();
    case 524:
      if (lookahead == 'm') ADVANCE(1034);
      END_STATE();
    case 525:
      if (lookahead == 'm') ADVANCE(1036);
      END_STATE();
    case 526:
      if (lookahead == 'm') ADVANCE(1038);
      END_STATE();
    case 527:
      if (lookahead == 'm') ADVANCE(905);
      END_STATE();
    case 528:
      if (lookahead == 'm') ADVANCE(662);
      END_STATE();
    case 529:
      if (lookahead == 'm') ADVANCE(662);
      if (lookahead == 's') ADVANCE(761);
      if (lookahead == 'x') ADVANCE(762);
      END_STATE();
    case 530:
      if (lookahead == 'm') ADVANCE(71);
      END_STATE();
    case 531:
      if (lookahead == 'm') ADVANCE(188);
      END_STATE();
    case 532:
      if (lookahead == 'm') ADVANCE(415);
      END_STATE();
    case 533:
      if (lookahead == 'm') ADVANCE(251);
      END_STATE();
    case 534:
      if (lookahead == 'm') ADVANCE(854);
      END_STATE();
    case 535:
      if (lookahead == 'm') ADVANCE(624);
      END_STATE();
    case 536:
      if (lookahead == 'm') ADVANCE(263);
      END_STATE();
    case 537:
      if (lookahead == 'm') ADVANCE(267);
      END_STATE();
    case 538:
      if (lookahead == 'm') ADVANCE(132);
      END_STATE();
    case 539:
      if (lookahead == 'm') ADVANCE(136);
      END_STATE();
    case 540:
      if (lookahead == 'm') ADVANCE(139);
      END_STATE();
    case 541:
      if (lookahead == 'm') ADVANCE(140);
      END_STATE();
    case 542:
      if (lookahead == 'm') ADVANCE(324);
      END_STATE();
    case 543:
      if (lookahead == 'm') ADVANCE(855);
      END_STATE();
    case 544:
      if (lookahead == 'm') ADVANCE(663);
      END_STATE();
    case 545:
      if (lookahead == 'm') ADVANCE(172);
      END_STATE();
    case 546:
      if (lookahead == 'm') ADVANCE(173);
      END_STATE();
    case 547:
      if (lookahead == 'n') ADVANCE(1075);
      END_STATE();
    case 548:
      if (lookahead == 'n') ADVANCE(26);
      END_STATE();
    case 549:
      if (lookahead == 'n') ADVANCE(1485);
      END_STATE();
    case 550:
      if (lookahead == 'n') ADVANCE(920);
      END_STATE();
    case 551:
      if (lookahead == 'n') ADVANCE(1467);
      END_STATE();
    case 552:
      if (lookahead == 'n') ADVANCE(1016);
      END_STATE();
    case 553:
      if (lookahead == 'n') ADVANCE(1006);
      END_STATE();
    case 554:
      if (lookahead == 'n') ADVANCE(1003);
      END_STATE();
    case 555:
      if (lookahead == 'n') ADVANCE(965);
      END_STATE();
    case 556:
      if (lookahead == 'n') ADVANCE(999);
      END_STATE();
    case 557:
      if (lookahead == 'n') ADVANCE(1022);
      END_STATE();
    case 558:
      if (lookahead == 'n') ADVANCE(1091);
      END_STATE();
    case 559:
      if (lookahead == 'n') ADVANCE(962);
      END_STATE();
    case 560:
      if (lookahead == 'n') ADVANCE(956);
      END_STATE();
    case 561:
      if (lookahead == 'n') ADVANCE(963);
      END_STATE();
    case 562:
      if (lookahead == 'n') ADVANCE(912);
      END_STATE();
    case 563:
      if (lookahead == 'n') ADVANCE(915);
      END_STATE();
    case 564:
      if (lookahead == 'n') ADVANCE(1005);
      END_STATE();
    case 565:
      if (lookahead == 'n') ADVANCE(33);
      END_STATE();
    case 566:
      if (lookahead == 'n') ADVANCE(466);
      END_STATE();
    case 567:
      if (lookahead == 'n') ADVANCE(210);
      END_STATE();
    case 568:
      if (lookahead == 'n') ADVANCE(398);
      END_STATE();
    case 569:
      if (lookahead == 'n') ADVANCE(67);
      END_STATE();
    case 570:
      if (lookahead == 'n') ADVANCE(798);
      END_STATE();
    case 571:
      if (lookahead == 'n') ADVANCE(724);
      END_STATE();
    case 572:
      if (lookahead == 'n') ADVANCE(880);
      END_STATE();
    case 573:
      if (lookahead == 'n') ADVANCE(154);
      END_STATE();
    case 574:
      if (lookahead == 'n') ADVANCE(406);
      END_STATE();
    case 575:
      if (lookahead == 'n') ADVANCE(766);
      END_STATE();
    case 576:
      if (lookahead == 'n') ADVANCE(208);
      END_STATE();
    case 577:
      if (lookahead == 'n') ADVANCE(793);
      END_STATE();
    case 578:
      if (lookahead == 'n') ADVANCE(771);
      END_STATE();
    case 579:
      if (lookahead == 'n') ADVANCE(813);
      END_STATE();
    case 580:
      if (lookahead == 'n') ADVANCE(781);
      END_STATE();
    case 581:
      if (lookahead == 'n') ADVANCE(782);
      END_STATE();
    case 582:
      if (lookahead == 'n') ADVANCE(783);
      END_STATE();
    case 583:
      if (lookahead == 'n') ADVANCE(784);
      END_STATE();
    case 584:
      if (lookahead == 'n') ADVANCE(785);
      END_STATE();
    case 585:
      if (lookahead == 'n') ADVANCE(786);
      END_STATE();
    case 586:
      if (lookahead == 'n') ADVANCE(787);
      END_STATE();
    case 587:
      if (lookahead == 'n') ADVANCE(383);
      END_STATE();
    case 588:
      if (lookahead == 'n') ADVANCE(394);
      END_STATE();
    case 589:
      if (lookahead == 'n') ADVANCE(426);
      END_STATE();
    case 590:
      if (lookahead == 'n') ADVANCE(198);
      END_STATE();
    case 591:
      if (lookahead == 'n') ADVANCE(826);
      END_STATE();
    case 592:
      if (lookahead == 'n') ADVANCE(427);
      END_STATE();
    case 593:
      if (lookahead == 'n') ADVANCE(737);
      END_STATE();
    case 594:
      if (lookahead == 'n') ADVANCE(145);
      END_STATE();
    case 595:
      if (lookahead == 'n') ADVANCE(825);
      END_STATE();
    case 596:
      if (lookahead == 'n') ADVANCE(138);
      END_STATE();
    case 597:
      if (lookahead == 'n') ADVANCE(742);
      END_STATE();
    case 598:
      if (lookahead == 'n') ADVANCE(751);
      END_STATE();
    case 599:
      if (lookahead == 'n') ADVANCE(815);
      END_STATE();
    case 600:
      if (lookahead == 'n') ADVANCE(752);
      END_STATE();
    case 601:
      if (lookahead == 'n') ADVANCE(82);
      END_STATE();
    case 602:
      if (lookahead == 'n') ADVANCE(756);
      END_STATE();
    case 603:
      if (lookahead == 'n') ADVANCE(386);
      END_STATE();
    case 604:
      if (lookahead == 'n') ADVANCE(841);
      END_STATE();
    case 605:
      if (lookahead == 'o') ADVANCE(200);
      END_STATE();
    case 606:
      if (lookahead == 'o') ADVANCE(864);
      END_STATE();
    case 607:
      if (lookahead == 'o') ADVANCE(467);
      END_STATE();
    case 608:
      if (lookahead == 'o') ADVANCE(949);
      END_STATE();
    case 609:
      if (lookahead == 'o') ADVANCE(959);
      END_STATE();
    case 610:
      if (lookahead == 'o') ADVANCE(228);
      END_STATE();
    case 611:
      if (lookahead == 'o') ADVANCE(491);
      END_STATE();
    case 612:
      if (lookahead == 'o') ADVANCE(865);
      END_STATE();
    case 613:
      if (lookahead == 'o') ADVANCE(195);
      END_STATE();
    case 614:
      if (lookahead == 'o') ADVANCE(685);
      END_STATE();
    case 615:
      if (lookahead == 'o') ADVANCE(470);
      END_STATE();
    case 616:
      if (lookahead == 'o') ADVANCE(853);
      END_STATE();
    case 617:
      if (lookahead == 'o') ADVANCE(548);
      END_STATE();
    case 618:
      if (lookahead == 'o') ADVANCE(176);
      END_STATE();
    case 619:
      if (lookahead == 'o') ADVANCE(607);
      END_STATE();
    case 620:
      if (lookahead == 'o') ADVANCE(542);
      END_STATE();
    case 621:
      if (lookahead == 'o') ADVANCE(199);
      END_STATE();
    case 622:
      if (lookahead == 'o') ADVANCE(389);
      END_STATE();
    case 623:
      if (lookahead == 'o') ADVANCE(552);
      END_STATE();
    case 624:
      if (lookahead == 'o') ADVANCE(847);
      END_STATE();
    case 625:
      if (lookahead == 'o') ADVANCE(688);
      END_STATE();
    case 626:
      if (lookahead == 'o') ADVANCE(553);
      END_STATE();
    case 627:
      if (lookahead == 'o') ADVANCE(555);
      END_STATE();
    case 628:
      if (lookahead == 'o') ADVANCE(715);
      END_STATE();
    case 629:
      if (lookahead == 'o') ADVANCE(594);
      END_STATE();
    case 630:
      if (lookahead == 'o') ADVANCE(556);
      END_STATE();
    case 631:
      if (lookahead == 'o') ADVANCE(571);
      END_STATE();
    case 632:
      if (lookahead == 'o') ADVANCE(569);
      END_STATE();
    case 633:
      if (lookahead == 'o') ADVANCE(559);
      END_STATE();
    case 634:
      if (lookahead == 'o') ADVANCE(560);
      END_STATE();
    case 635:
      if (lookahead == 'o') ADVANCE(572);
      END_STATE();
    case 636:
      if (lookahead == 'o') ADVANCE(561);
      END_STATE();
    case 637:
      if (lookahead == 'o') ADVANCE(562);
      END_STATE();
    case 638:
      if (lookahead == 'o') ADVANCE(563);
      END_STATE();
    case 639:
      if (lookahead == 'o') ADVANCE(702);
      END_STATE();
    case 640:
      if (lookahead == 'o') ADVANCE(564);
      END_STATE();
    case 641:
      if (lookahead == 'o') ADVANCE(565);
      END_STATE();
    case 642:
      if (lookahead == 'o') ADVANCE(866);
      END_STATE();
    case 643:
      if (lookahead == 'o') ADVANCE(644);
      END_STATE();
    case 644:
      if (lookahead == 'o') ADVANCE(469);
      END_STATE();
    case 645:
      if (lookahead == 'o') ADVANCE(233);
      END_STATE();
    case 646:
      if (lookahead == 'o') ADVANCE(692);
      END_STATE();
    case 647:
      if (lookahead == 'o') ADVANCE(235);
      END_STATE();
    case 648:
      if (lookahead == 'o') ADVANCE(698);
      END_STATE();
    case 649:
      if (lookahead == 'o') ADVANCE(710);
      END_STATE();
    case 650:
      if (lookahead == 'o') ADVANCE(716);
      END_STATE();
    case 651:
      if (lookahead == 'o') ADVANCE(593);
      END_STATE();
    case 652:
      if (lookahead == 'o') ADVANCE(595);
      END_STATE();
    case 653:
      if (lookahead == 'o') ADVANCE(718);
      END_STATE();
    case 654:
      if (lookahead == 'o') ADVANCE(243);
      END_STATE();
    case 655:
      if (lookahead == 'o') ADVANCE(720);
      END_STATE();
    case 656:
      if (lookahead == 'p') ADVANCE(1071);
      END_STATE();
    case 657:
      if (lookahead == 'p') ADVANCE(1089);
      END_STATE();
    case 658:
      if (lookahead == 'p') ADVANCE(392);
      END_STATE();
    case 659:
      if (lookahead == 'p') ADVANCE(337);
      END_STATE();
    case 660:
      if (lookahead == 'p') ADVANCE(260);
      END_STATE();
    case 661:
      if (lookahead == 'p') ADVANCE(270);
      END_STATE();
    case 662:
      if (lookahead == 'p') ADVANCE(628);
      END_STATE();
    case 663:
      if (lookahead == 'p') ADVANCE(650);
      END_STATE();
    case 664:
      if (lookahead == 'p') ADVANCE(81);
      END_STATE();
    case 665:
      if (lookahead == 'p') ADVANCE(827);
      END_STATE();
    case 666:
      if (lookahead == 'p') ADVANCE(831);
      END_STATE();
    case 667:
      if (lookahead == 'p') ADVANCE(837);
      END_STATE();
    case 668:
      if (lookahead == 'r') ADVANCE(972);
      END_STATE();
    case 669:
      if (lookahead == 'r') ADVANCE(990);
      END_STATE();
    case 670:
      if (lookahead == 'r') ADVANCE(1070);
      END_STATE();
    case 671:
      if (lookahead == 'r') ADVANCE(64);
      END_STATE();
    case 672:
      if (lookahead == 'r') ADVANCE(981);
      END_STATE();
    case 673:
      if (lookahead == 'r') ADVANCE(38);
      END_STATE();
    case 674:
      if (lookahead == 'r') ADVANCE(918);
      END_STATE();
    case 675:
      if (lookahead == 'r') ADVANCE(1483);
      END_STATE();
    case 676:
      if (lookahead == 'r') ADVANCE(983);
      END_STATE();
    case 677:
      if (lookahead == 'r') ADVANCE(900);
      END_STATE();
    case 678:
      if (lookahead == 'r') ADVANCE(1020);
      END_STATE();
    case 679:
      if (lookahead == 'r') ADVANCE(168);
      END_STATE();
    case 680:
      if (lookahead == 'r') ADVANCE(79);
      END_STATE();
    case 681:
      if (lookahead == 'r') ADVANCE(871);
      END_STATE();
    case 682:
      if (lookahead == 'r') ADVANCE(31);
      END_STATE();
    case 683:
      if (lookahead == 'r') ADVANCE(119);
      END_STATE();
    case 684:
      if (lookahead == 'r') ADVANCE(683);
      if (lookahead == 'v') ADVANCE(298);
      END_STATE();
    case 685:
      if (lookahead == 'r') ADVANCE(538);
      END_STATE();
    case 686:
      if (lookahead == 'r') ADVANCE(613);
      END_STATE();
    case 687:
      if (lookahead == 'r') ADVANCE(532);
      END_STATE();
    case 688:
      if (lookahead == 'r') ADVANCE(214);
      END_STATE();
    case 689:
      if (lookahead == 'r') ADVANCE(876);
      END_STATE();
    case 690:
      if (lookahead == 'r') ADVANCE(150);
      END_STATE();
    case 691:
      if (lookahead == 'r') ADVANCE(877);
      END_STATE();
    case 692:
      if (lookahead == 'r') ADVANCE(534);
      END_STATE();
    case 693:
      if (lookahead == 'r') ADVANCE(878);
      END_STATE();
    case 694:
      if (lookahead == 'r') ADVANCE(128);
      END_STATE();
    case 695:
      if (lookahead == 'r') ADVANCE(726);
      END_STATE();
    case 696:
      if (lookahead == 'r') ADVANCE(596);
      END_STATE();
    case 697:
      if (lookahead == 'r') ADVANCE(727);
      END_STATE();
    case 698:
      if (lookahead == 'r') ADVANCE(545);
      END_STATE();
    case 699:
      if (lookahead == 'r') ADVANCE(124);
      END_STATE();
    case 700:
      if (lookahead == 'r') ADVANCE(609);
      END_STATE();
    case 701:
      if (lookahead == 'r') ADVANCE(304);
      END_STATE();
    case 702:
      if (lookahead == 'r') ADVANCE(221);
      END_STATE();
    case 703:
      if (lookahead == 'r') ADVANCE(699);
      END_STATE();
    case 704:
      if (lookahead == 'r') ADVANCE(768);
      END_STATE();
    case 705:
      if (lookahead == 'r') ADVANCE(258);
      END_STATE();
    case 706:
      if (lookahead == 'r') ADVANCE(309);
      END_STATE();
    case 707:
      if (lookahead == 'r') ADVANCE(317);
      END_STATE();
    case 708:
      if (lookahead == 'r') ADVANCE(775);
      END_STATE();
    case 709:
      if (lookahead == 'r') ADVANCE(302);
      END_STATE();
    case 710:
      if (lookahead == 'r') ADVANCE(265);
      END_STATE();
    case 711:
      if (lookahead == 'r') ADVANCE(838);
      END_STATE();
    case 712:
      if (lookahead == 'r') ADVANCE(271);
      END_STATE();
    case 713:
      if (lookahead == 'r') ADVANCE(418);
      END_STATE();
    case 714:
      if (lookahead == 'r') ADVANCE(322);
      END_STATE();
    case 715:
      if (lookahead == 'r') ADVANCE(143);
      END_STATE();
    case 716:
      if (lookahead == 'r') ADVANCE(144);
      END_STATE();
    case 717:
      if (lookahead == 'r') ADVANCE(741);
      END_STATE();
    case 718:
      if (lookahead == 'r') ADVANCE(543);
      END_STATE();
    case 719:
      if (lookahead == 'r') ADVANCE(840);
      END_STATE();
    case 720:
      if (lookahead == 'r') ADVANCE(546);
      END_STATE();
    case 721:
      if (lookahead == 's') ADVANCE(1092);
      END_STATE();
    case 722:
      if (lookahead == 's') ADVANCE(1058);
      END_STATE();
    case 723:
      if (lookahead == 's') ADVANCE(957);
      END_STATE();
    case 724:
      if (lookahead == 's') ADVANCE(922);
      END_STATE();
    case 725:
      if (lookahead == 's') ADVANCE(968);
      END_STATE();
    case 726:
      if (lookahead == 's') ADVANCE(961);
      END_STATE();
    case 727:
      if (lookahead == 's') ADVANCE(914);
      END_STATE();
    case 728:
      if (lookahead == 's') ADVANCE(617);
      END_STATE();
    case 729:
      if (lookahead == 's') ADVANCE(754);
      END_STATE();
    case 730:
      if (lookahead == 's') ADVANCE(723);
      END_STATE();
    case 731:
      if (lookahead == 's') ADVANCE(799);
      END_STATE();
    case 732:
      if (lookahead == 's') ADVANCE(759);
      END_STATE();
    case 733:
      if (lookahead == 's') ADVANCE(252);
      END_STATE();
    case 734:
      if (lookahead == 's') ADVANCE(443);
      END_STATE();
    case 735:
      if (lookahead == 's') ADVANCE(253);
      END_STATE();
    case 736:
      if (lookahead == 's') ADVANCE(410);
      END_STATE();
    case 737:
      if (lookahead == 's') ADVANCE(765);
      END_STATE();
    case 738:
      if (lookahead == 's') ADVANCE(256);
      END_STATE();
    case 739:
      if (lookahead == 's') ADVANCE(773);
      END_STATE();
    case 740:
      if (lookahead == 's') ADVANCE(790);
      END_STATE();
    case 741:
      if (lookahead == 's') ADVANCE(777);
      END_STATE();
    case 742:
      if (lookahead == 's') ADVANCE(812);
      END_STATE();
    case 743:
      if (lookahead == 's') ADVANCE(300);
      END_STATE();
    case 744:
      if (lookahead == 's') ADVANCE(800);
      END_STATE();
    case 745:
      if (lookahead == 's') ADVANCE(736);
      END_STATE();
    case 746:
      if (lookahead == 's') ADVANCE(434);
      END_STATE();
    case 747:
      if (lookahead == 's') ADVANCE(746);
      END_STATE();
    case 748:
      if (lookahead == 's') ADVANCE(315);
      END_STATE();
    case 749:
      if (lookahead == 's') ADVANCE(810);
      END_STATE();
    case 750:
      if (lookahead == 's') ADVANCE(811);
      END_STATE();
    case 751:
      if (lookahead == 's') ADVANCE(343);
      END_STATE();
    case 752:
      if (lookahead == 's') ADVANCE(347);
      END_STATE();
    case 753:
      if (lookahead == 's') ADVANCE(820);
      END_STATE();
    case 754:
      if (lookahead == 's') ADVANCE(445);
      END_STATE();
    case 755:
      if (lookahead == 's') ADVANCE(65);
      END_STATE();
    case 756:
      if (lookahead == 's') ADVANCE(371);
      END_STATE();
    case 757:
      if (lookahead == 't') ADVANCE(103);
      END_STATE();
    case 758:
      if (lookahead == 't') ADVANCE(1477);
      END_STATE();
    case 759:
      if (lookahead == 't') ADVANCE(974);
      END_STATE();
    case 760:
      if (lookahead == 't') ADVANCE(1488);
      END_STATE();
    case 761:
      if (lookahead == 't') ADVANCE(898);
      END_STATE();
    case 762:
      if (lookahead == 't') ADVANCE(1044);
      END_STATE();
    case 763:
      if (lookahead == 't') ADVANCE(1491);
      END_STATE();
    case 764:
      if (lookahead == 't') ADVANCE(1484);
      END_STATE();
    case 765:
      if (lookahead == 't') ADVANCE(1069);
      END_STATE();
    case 766:
      if (lookahead == 't') ADVANCE(1072);
      END_STATE();
    case 767:
      if (lookahead == 't') ADVANCE(1054);
      END_STATE();
    case 768:
      if (lookahead == 't') ADVANCE(1479);
      END_STATE();
    case 769:
      if (lookahead == 't') ADVANCE(1471);
      END_STATE();
    case 770:
      if (lookahead == 't') ADVANCE(1478);
      END_STATE();
    case 771:
      if (lookahead == 't') ADVANCE(1012);
      END_STATE();
    case 772:
      if (lookahead == 't') ADVANCE(1050);
      END_STATE();
    case 773:
      if (lookahead == 't') ADVANCE(1487);
      END_STATE();
    case 774:
      if (lookahead == 't') ADVANCE(1032);
      END_STATE();
    case 775:
      if (lookahead == 't') ADVANCE(936);
      END_STATE();
    case 776:
      if (lookahead == 't') ADVANCE(895);
      END_STATE();
    case 777:
      if (lookahead == 't') ADVANCE(1486);
      END_STATE();
    case 778:
      if (lookahead == 't') ADVANCE(1028);
      END_STATE();
    case 779:
      if (lookahead == 't') ADVANCE(1040);
      END_STATE();
    case 780:
      if (lookahead == 't') ADVANCE(1090);
      END_STATE();
    case 781:
      if (lookahead == 't') ADVANCE(911);
      END_STATE();
    case 782:
      if (lookahead == 't') ADVANCE(944);
      END_STATE();
    case 783:
      if (lookahead == 't') ADVANCE(942);
      END_STATE();
    case 784:
      if (lookahead == 't') ADVANCE(943);
      END_STATE();
    case 785:
      if (lookahead == 't') ADVANCE(947);
      END_STATE();
    case 786:
      if (lookahead == 't') ADVANCE(945);
      END_STATE();
    case 787:
      if (lookahead == 't') ADVANCE(946);
      END_STATE();
    case 788:
      if (lookahead == 't') ADVANCE(75);
      END_STATE();
    case 789:
      if (lookahead == 't') ADVANCE(90);
      END_STATE();
    case 790:
      if (lookahead == 't') ADVANCE(46);
      END_STATE();
    case 791:
      if (lookahead == 't') ADVANCE(882);
      END_STATE();
    case 792:
      if (lookahead == 't') ADVANCE(93);
      END_STATE();
    case 793:
      if (lookahead == 't') ADVANCE(40);
      END_STATE();
    case 794:
      if (lookahead == 't') ADVANCE(85);
      END_STATE();
    case 795:
      if (lookahead == 't') ADVANCE(249);
      END_STATE();
    case 796:
      if (lookahead == 't') ADVANCE(163);
      END_STATE();
    case 797:
      if (lookahead == 't') ADVANCE(701);
      END_STATE();
    case 798:
      if (lookahead == 't') ADVANCE(417);
      END_STATE();
    case 799:
      if (lookahead == 't') ADVANCE(620);
      END_STATE();
    case 800:
      if (lookahead == 't') ADVANCE(295);
      END_STATE();
    case 801:
      if (lookahead == 't') ADVANCE(105);
      END_STATE();
    case 802:
      if (lookahead == 't') ADVANCE(135);
      END_STATE();
    case 803:
      if (lookahead == 't') ADVANCE(106);
      END_STATE();
    case 804:
      if (lookahead == 't') ADVANCE(259);
      END_STATE();
    case 805:
      if (lookahead == 't') ADVANCE(109);
      END_STATE();
    case 806:
      if (lookahead == 't') ADVANCE(102);
      END_STATE();
    case 807:
      if (lookahead == 't') ADVANCE(266);
      END_STATE();
    case 808:
      if (lookahead == 't') ADVANCE(272);
      END_STATE();
    case 809:
      if (lookahead == 't') ADVANCE(281);
      END_STATE();
    case 810:
      if (lookahead == 't') ADVANCE(310);
      END_STATE();
    case 811:
      if (lookahead == 't') ADVANCE(311);
      END_STATE();
    case 812:
      if (lookahead == 't') ADVANCE(142);
      END_STATE();
    case 813:
      if (lookahead == 't') ADVANCE(438);
      END_STATE();
    case 814:
      if (lookahead == 't') ADVANCE(706);
      END_STATE();
    case 815:
      if (lookahead == 't') ADVANCE(440);
      END_STATE();
    case 816:
      if (lookahead == 't') ADVANCE(301);
      END_STATE();
    case 817:
      if (lookahead == 't') ADVANCE(707);
      END_STATE();
    case 818:
      if (lookahead == 't') ADVANCE(308);
      END_STATE();
    case 819:
      if (lookahead == 't') ADVANCE(312);
      END_STATE();
    case 820:
      if (lookahead == 't') ADVANCE(353);
      END_STATE();
    case 821:
      if (lookahead == 't') ADVANCE(321);
      END_STATE();
    case 822:
      if (lookahead == 't') ADVANCE(326);
      END_STATE();
    case 823:
      if (lookahead == 't') ADVANCE(329);
      END_STATE();
    case 824:
      if (lookahead == 't') ADVANCE(437);
      END_STATE();
    case 825:
      if (lookahead == 't') ADVANCE(354);
      END_STATE();
    case 826:
      if (lookahead == 't') ADVANCE(364);
      END_STATE();
    case 827:
      if (lookahead == 't') ADVANCE(439);
      END_STATE();
    case 828:
      if (lookahead == 't') ADVANCE(442);
      END_STATE();
    case 829:
      if (lookahead == 't') ADVANCE(444);
      END_STATE();
    case 830:
      if (lookahead == 't') ADVANCE(446);
      END_STATE();
    case 831:
      if (lookahead == 't') ADVANCE(447);
      END_STATE();
    case 832:
      if (lookahead == 't') ADVANCE(448);
      END_STATE();
    case 833:
      if (lookahead == 't') ADVANCE(449);
      END_STATE();
    case 834:
      if (lookahead == 't') ADVANCE(450);
      END_STATE();
    case 835:
      if (lookahead == 't') ADVANCE(451);
      END_STATE();
    case 836:
      if (lookahead == 't') ADVANCE(452);
      END_STATE();
    case 837:
      if (lookahead == 't') ADVANCE(453);
      END_STATE();
    case 838:
      if (lookahead == 't') ADVANCE(47);
      END_STATE();
    case 839:
      if (lookahead == 't') ADVANCE(369);
      END_STATE();
    case 840:
      if (lookahead == 't') ADVANCE(50);
      END_STATE();
    case 841:
      if (lookahead == 't') ADVANCE(464);
      END_STATE();
    case 842:
      if (lookahead == 'u') ADVANCE(521);
      END_STATE();
    case 843:
      if (lookahead == 'u') ADVANCE(664);
      END_STATE();
    case 844:
      if (lookahead == 'u') ADVANCE(656);
      END_STATE();
    case 845:
      if (lookahead == 'u') ADVANCE(657);
      END_STATE();
    case 846:
      if (lookahead == 'u') ADVANCE(589);
      END_STATE();
    case 847:
      if (lookahead == 'u') ADVANCE(755);
      END_STATE();
    case 848:
      if (lookahead == 'u') ADVANCE(238);
      END_STATE();
    case 849:
      if (lookahead == 'u') ADVANCE(441);
      END_STATE();
    case 850:
      if (lookahead == 'u') ADVANCE(269);
      END_STATE();
    case 851:
      if (lookahead == 'u') ADVANCE(296);
      END_STATE();
    case 852:
      if (lookahead == 'u') ADVANCE(753);
      END_STATE();
    case 853:
      if (lookahead == 'u') ADVANCE(577);
      END_STATE();
    case 854:
      if (lookahead == 'u') ADVANCE(498);
      END_STATE();
    case 855:
      if (lookahead == 'u') ADVANCE(499);
      END_STATE();
    case 856:
      if (lookahead == 'u') ADVANCE(712);
      END_STATE();
    case 857:
      if (lookahead == 'u') ADVANCE(592);
      END_STATE();
    case 858:
      if (lookahead == 'v') ADVANCE(355);
      END_STATE();
    case 859:
      if (lookahead == 'v') ADVANCE(357);
      END_STATE();
    case 860:
      if (lookahead == 'v') ADVANCE(358);
      END_STATE();
    case 861:
      if (lookahead == 'v') ADVANCE(359);
      END_STATE();
    case 862:
      if (lookahead == 'v') ADVANCE(360);
      END_STATE();
    case 863:
      if (lookahead == 'v') ADVANCE(361);
      END_STATE();
    case 864:
      if (lookahead == 'w') ADVANCE(53);
      END_STATE();
    case 865:
      if (lookahead == 'w') ADVANCE(601);
      END_STATE();
    case 866:
      if (lookahead == 'w') ADVANCE(558);
      END_STATE();
    case 867:
      if (lookahead == 'x') ADVANCE(1076);
      END_STATE();
    case 868:
      if (lookahead == 'x') ADVANCE(760);
      END_STATE();
    case 869:
      if (lookahead == 'x') ADVANCE(779);
      END_STATE();
    case 870:
      if (lookahead == 'y') ADVANCE(1095);
      END_STATE();
    case 871:
      if (lookahead == 'y') ADVANCE(1052);
      END_STATE();
    case 872:
      if (lookahead == 'y') ADVANCE(1056);
      END_STATE();
    case 873:
      if (lookahead == 'y') ADVANCE(1480);
      END_STATE();
    case 874:
      if (lookahead == 'y') ADVANCE(937);
      END_STATE();
    case 875:
      if (lookahead == 'y') ADVANCE(1026);
      END_STATE();
    case 876:
      if (lookahead == 'y') ADVANCE(903);
      END_STATE();
    case 877:
      if (lookahead == 'y') ADVANCE(1464);
      END_STATE();
    case 878:
      if (lookahead == 'y') ADVANCE(979);
      END_STATE();
    case 879:
      if (lookahead == 'y') ADVANCE(1094);
      END_STATE();
    case 880:
      if (lookahead == 'y') ADVANCE(535);
      END_STATE();
    case 881:
      if (lookahead == 'y') ADVANCE(721);
      END_STATE();
    case 882:
      if (lookahead == 'y') ADVANCE(660);
      END_STATE();
    case 883:
      if (lookahead == 'y') ADVANCE(661);
      END_STATE();
    case 884:
      if (lookahead == 'y') ADVANCE(48);
      END_STATE();
    case 885:
      if (lookahead == 'y') ADVANCE(51);
      END_STATE();
    case 886:
      if (lookahead == 'z') ADVANCE(169);
      END_STATE();
    case 887:
      if (lookahead == '"' ||
          lookahead == '\'' ||
          lookahead == '\\') ADVANCE(15);
      END_STATE();
    case 888:
      if (lookahead == '"' ||
          lookahead == '\'' ||
          lookahead == '\\') ADVANCE(1456);
      END_STATE();
    case 889:
      if (eof) ADVANCE(890);
      ADVANCE_MAP(
        '(', 1062,
        ')', 1063,
        '*', 1102,
        '+', 1100,
        ',', 902,
        '-', 1101,
        '.', 948,
        '/', 1103,
        ':', 971,
        ';', 910,
        '<', 1086,
        '=', 909,
        '>', 1087,
        'A', 190,
        'B', 405,
        'C', 174,
        'D', 110,
        'E', 576,
        'F', 407,
        'G', 286,
        'I', 72,
        'J', 728,
        'L', 100,
        'M', 277,
        'N', 245,
        'O', 88,
        'P', 339,
        'Q', 851,
        'R', 247,
        'S', 276,
        'T', 165,
        'U', 658,
        'V', 118,
        '[', 977,
        ']', 978,
        'a', 684,
        'b', 283,
        'c', 610,
        'e', 507,
        'f', 430,
        'k', 306,
        'l', 605,
        'm', 111,
        'o', 374,
        'p', 686,
        's', 842,
        't', 166,
        'v', 120,
        'w', 403,
        '{', 893,
        '}', 894,
      );
      if (('\t' <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') SKIP(889);
      END_STATE();
    case 890:
      ACCEPT_TOKEN(ts_builtin_sym_end);
      END_STATE();
    case 891:
      ACCEPT_TOKEN(anon_sym_table);
      END_STATE();
    case 892:
      ACCEPT_TOKEN(anon_sym_table);
      if (lookahead == 'd') ADVANCE(146);
      END_STATE();
    case 893:
      ACCEPT_TOKEN(anon_sym_LBRACE);
      END_STATE();
    case 894:
      ACCEPT_TOKEN(anon_sym_RBRACE);
      END_STATE();
    case 895:
      ACCEPT_TOKEN(anon_sym_codeunit);
      END_STATE();
    case 896:
      ACCEPT_TOKEN(anon_sym_Install);
      END_STATE();
    case 897:
      ACCEPT_TOKEN(anon_sym_Upgrade);
      END_STATE();
    case 898:
      ACCEPT_TOKEN(anon_sym_Test);
      END_STATE();
    case 899:
      ACCEPT_TOKEN(anon_sym_FlowField);
      END_STATE();
    case 900:
      ACCEPT_TOKEN(anon_sym_FlowFilter);
      END_STATE();
    case 901:
      ACCEPT_TOKEN(anon_sym_Normal);
      END_STATE();
    case 902:
      ACCEPT_TOKEN(anon_sym_COMMA);
      END_STATE();
    case 903:
      ACCEPT_TOKEN(anon_sym_Temporary);
      END_STATE();
    case 904:
      ACCEPT_TOKEN(anon_sym_External);
      END_STATE();
    case 905:
      ACCEPT_TOKEN(anon_sym_System);
      END_STATE();
    case 906:
      ACCEPT_TOKEN(anon_sym_System);
      if (lookahead == 'M') ADVANCE(333);
      END_STATE();
    case 907:
      ACCEPT_TOKEN(anon_sym_TableType);
      END_STATE();
    case 908:
      ACCEPT_TOKEN(anon_sym_TableType);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 909:
      ACCEPT_TOKEN(anon_sym_EQ);
      END_STATE();
    case 910:
      ACCEPT_TOKEN(anon_sym_SEMI);
      END_STATE();
    case 911:
      ACCEPT_TOKEN(anon_sym_CustomerContent);
      END_STATE();
    case 912:
      ACCEPT_TOKEN(anon_sym_EndUserIdentifiableInformation);
      END_STATE();
    case 913:
      ACCEPT_TOKEN(anon_sym_AccountData);
      END_STATE();
    case 914:
      ACCEPT_TOKEN(anon_sym_EndUserPseudonymousIdentifiers);
      END_STATE();
    case 915:
      ACCEPT_TOKEN(anon_sym_OrganizationIdentifiableInformation);
      END_STATE();
    case 916:
      ACCEPT_TOKEN(anon_sym_SystemMetadata);
      END_STATE();
    case 917:
      ACCEPT_TOKEN(anon_sym_ToBeClassified);
      END_STATE();
    case 918:
      ACCEPT_TOKEN(anon_sym_trigger);
      END_STATE();
    case 919:
      ACCEPT_TOKEN(anon_sym_trigger);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 920:
      ACCEPT_TOKEN(anon_sym_OnRun);
      END_STATE();
    case 921:
      ACCEPT_TOKEN(anon_sym_LPAREN_RPAREN);
      END_STATE();
    case 922:
      ACCEPT_TOKEN(anon_sym_Permissions);
      END_STATE();
    case 923:
      ACCEPT_TOKEN(anon_sym_Permissions);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 924:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'N', 1088,
        'n', 89,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'i', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 925:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'a', 757,
        'e', 192,
        'i', 927,
        'o', 788,
        'r', 932,
        'u', 679,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'm', 935,
        'x', 935,
      );
      END_STATE();
    case 926:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'a', 867,
        'i', 934,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 927:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'a', 486,
        'c', 828,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'i', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 928:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'e', 194,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'i', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 929:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'e', 659,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'i', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 930:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'e', 223,
        'o', 225,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'i', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 931:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'f', 1065,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'i', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 932:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'i', 933,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 933:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'l', 480,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'i', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 934:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'n', 1075,
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'i', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 935:
      ACCEPT_TOKEN(sym_permission_type);
      ADVANCE_MAP(
        'D', 935,
        'I', 935,
        'M', 935,
        'R', 935,
        'X', 935,
        'd', 935,
        'i', 935,
        'm', 935,
        'r', 935,
        'x', 935,
      );
      END_STATE();
    case 936:
      ACCEPT_TOKEN(anon_sym_OnInsert);
      END_STATE();
    case 937:
      ACCEPT_TOKEN(anon_sym_OnModify);
      END_STATE();
    case 938:
      ACCEPT_TOKEN(anon_sym_OnDelete);
      END_STATE();
    case 939:
      ACCEPT_TOKEN(anon_sym_OnRename);
      END_STATE();
    case 940:
      ACCEPT_TOKEN(anon_sym_OnValidate);
      END_STATE();
    case 941:
      ACCEPT_TOKEN(anon_sym_OnAfterGetRecord);
      END_STATE();
    case 942:
      ACCEPT_TOKEN(anon_sym_OnAfterInsertEvent);
      END_STATE();
    case 943:
      ACCEPT_TOKEN(anon_sym_OnAfterModifyEvent);
      END_STATE();
    case 944:
      ACCEPT_TOKEN(anon_sym_OnAfterDeleteEvent);
      END_STATE();
    case 945:
      ACCEPT_TOKEN(anon_sym_OnBeforeInsertEvent);
      END_STATE();
    case 946:
      ACCEPT_TOKEN(anon_sym_OnBeforeModifyEvent);
      END_STATE();
    case 947:
      ACCEPT_TOKEN(anon_sym_OnBeforeDeleteEvent);
      END_STATE();
    case 948:
      ACCEPT_TOKEN(anon_sym_DOT);
      END_STATE();
    case 949:
      ACCEPT_TOKEN(anon_sym_TableNo);
      END_STATE();
    case 950:
      ACCEPT_TOKEN(anon_sym_Subtype);
      END_STATE();
    case 951:
      ACCEPT_TOKEN(anon_sym_SingleInstance);
      END_STATE();
    case 952:
      ACCEPT_TOKEN(anon_sym_DrillDownPageId);
      END_STATE();
    case 953:
      ACCEPT_TOKEN(anon_sym_DrillDownPageId);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 954:
      ACCEPT_TOKEN(anon_sym_LookupPageId);
      END_STATE();
    case 955:
      ACCEPT_TOKEN(anon_sym_LookupPageId);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 956:
      ACCEPT_TOKEN(anon_sym_TableRelation);
      END_STATE();
    case 957:
      ACCEPT_TOKEN(anon_sym_FieldClass);
      END_STATE();
    case 958:
      ACCEPT_TOKEN(anon_sym_CalcFormula);
      END_STATE();
    case 959:
      ACCEPT_TOKEN(anon_sym_BlankZero);
      END_STATE();
    case 960:
      ACCEPT_TOKEN(anon_sym_Editable);
      END_STATE();
    case 961:
      ACCEPT_TOKEN(anon_sym_OptionMembers);
      END_STATE();
    case 962:
      ACCEPT_TOKEN(anon_sym_OptionCaption);
      END_STATE();
    case 963:
      ACCEPT_TOKEN(anon_sym_DataClassification);
      END_STATE();
    case 964:
      ACCEPT_TOKEN(anon_sym_DataClassification);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 965:
      ACCEPT_TOKEN(anon_sym_Caption);
      END_STATE();
    case 966:
      ACCEPT_TOKEN(anon_sym_Caption);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 967:
      ACCEPT_TOKEN(anon_sym_tabledata);
      END_STATE();
    case 968:
      ACCEPT_TOKEN(anon_sym_DecimalPlaces);
      END_STATE();
    case 969:
      ACCEPT_TOKEN(anon_sym_COLON);
      END_STATE();
    case 970:
      ACCEPT_TOKEN(anon_sym_COLON);
      if (lookahead == ':') ADVANCE(1476);
      END_STATE();
    case 971:
      ACCEPT_TOKEN(anon_sym_COLON);
      if (lookahead == ':') ADVANCE(1476);
      if (lookahead == '=') ADVANCE(1475);
      END_STATE();
    case 972:
      ACCEPT_TOKEN(anon_sym_var);
      END_STATE();
    case 973:
      ACCEPT_TOKEN(anon_sym_var);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 974:
      ACCEPT_TOKEN(anon_sym_List);
      END_STATE();
    case 975:
      ACCEPT_TOKEN(anon_sym_List);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 976:
      ACCEPT_TOKEN(anon_sym_of);
      END_STATE();
    case 977:
      ACCEPT_TOKEN(anon_sym_LBRACK);
      END_STATE();
    case 978:
      ACCEPT_TOKEN(anon_sym_RBRACK);
      END_STATE();
    case 979:
      ACCEPT_TOKEN(anon_sym_Dictionary);
      END_STATE();
    case 980:
      ACCEPT_TOKEN(anon_sym_Dictionary);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 981:
      ACCEPT_TOKEN(anon_sym_Integer);
      END_STATE();
    case 982:
      ACCEPT_TOKEN(anon_sym_Integer);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 983:
      ACCEPT_TOKEN(anon_sym_BigInteger);
      END_STATE();
    case 984:
      ACCEPT_TOKEN(anon_sym_BigInteger);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 985:
      ACCEPT_TOKEN(anon_sym_Decimal);
      END_STATE();
    case 986:
      ACCEPT_TOKEN(anon_sym_Decimal);
      if (lookahead == 'P') ADVANCE(494);
      END_STATE();
    case 987:
      ACCEPT_TOKEN(anon_sym_Decimal);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 988:
      ACCEPT_TOKEN(anon_sym_Byte);
      END_STATE();
    case 989:
      ACCEPT_TOKEN(anon_sym_Byte);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 990:
      ACCEPT_TOKEN(anon_sym_Char);
      END_STATE();
    case 991:
      ACCEPT_TOKEN(anon_sym_Char);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 992:
      ACCEPT_TOKEN(anon_sym_Date);
      if (lookahead == 'F') ADVANCE(1351);
      if (lookahead == 'T') ADVANCE(1281);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 993:
      ACCEPT_TOKEN(anon_sym_Date);
      if (lookahead == 'F') ADVANCE(653);
      if (lookahead == 'T') ADVANCE(431);
      END_STATE();
    case 994:
      ACCEPT_TOKEN(anon_sym_Date);
      if (lookahead == 'T') ADVANCE(1281);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 995:
      ACCEPT_TOKEN(anon_sym_Time);
      END_STATE();
    case 996:
      ACCEPT_TOKEN(anon_sym_Time);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 997:
      ACCEPT_TOKEN(anon_sym_DateTime);
      END_STATE();
    case 998:
      ACCEPT_TOKEN(anon_sym_DateTime);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 999:
      ACCEPT_TOKEN(anon_sym_Duration);
      END_STATE();
    case 1000:
      ACCEPT_TOKEN(anon_sym_Duration);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1001:
      ACCEPT_TOKEN(anon_sym_DateFormula);
      END_STATE();
    case 1002:
      ACCEPT_TOKEN(anon_sym_DateFormula);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1003:
      ACCEPT_TOKEN(anon_sym_Boolean);
      END_STATE();
    case 1004:
      ACCEPT_TOKEN(anon_sym_Boolean);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1005:
      ACCEPT_TOKEN(anon_sym_Option);
      END_STATE();
    case 1006:
      ACCEPT_TOKEN(anon_sym_Option);
      if (lookahead == 'C') ADVANCE(121);
      if (lookahead == 'M') ADVANCE(303);
      END_STATE();
    case 1007:
      ACCEPT_TOKEN(anon_sym_Option);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1008:
      ACCEPT_TOKEN(anon_sym_Guid);
      END_STATE();
    case 1009:
      ACCEPT_TOKEN(anon_sym_Guid);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1010:
      ACCEPT_TOKEN(anon_sym_RecordId);
      END_STATE();
    case 1011:
      ACCEPT_TOKEN(anon_sym_RecordId);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1012:
      ACCEPT_TOKEN(anon_sym_Variant);
      END_STATE();
    case 1013:
      ACCEPT_TOKEN(anon_sym_Variant);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1014:
      ACCEPT_TOKEN(anon_sym_Dialog);
      END_STATE();
    case 1015:
      ACCEPT_TOKEN(anon_sym_Dialog);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1016:
      ACCEPT_TOKEN(anon_sym_Action);
      END_STATE();
    case 1017:
      ACCEPT_TOKEN(anon_sym_Action);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1018:
      ACCEPT_TOKEN(anon_sym_Blob);
      END_STATE();
    case 1019:
      ACCEPT_TOKEN(anon_sym_Blob);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1020:
      ACCEPT_TOKEN(anon_sym_FilterPageBuilder);
      END_STATE();
    case 1021:
      ACCEPT_TOKEN(anon_sym_FilterPageBuilder);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1022:
      ACCEPT_TOKEN(anon_sym_JsonToken);
      END_STATE();
    case 1023:
      ACCEPT_TOKEN(anon_sym_JsonToken);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1024:
      ACCEPT_TOKEN(anon_sym_JsonValue);
      END_STATE();
    case 1025:
      ACCEPT_TOKEN(anon_sym_JsonValue);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1026:
      ACCEPT_TOKEN(anon_sym_JsonArray);
      END_STATE();
    case 1027:
      ACCEPT_TOKEN(anon_sym_JsonArray);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1028:
      ACCEPT_TOKEN(anon_sym_JsonObject);
      END_STATE();
    case 1029:
      ACCEPT_TOKEN(anon_sym_JsonObject);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1030:
      ACCEPT_TOKEN(anon_sym_Media);
      if (lookahead == 'S') ADVANCE(1232);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1031:
      ACCEPT_TOKEN(anon_sym_Media);
      if (lookahead == 'S') ADVANCE(328);
      END_STATE();
    case 1032:
      ACCEPT_TOKEN(anon_sym_MediaSet);
      END_STATE();
    case 1033:
      ACCEPT_TOKEN(anon_sym_MediaSet);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1034:
      ACCEPT_TOKEN(anon_sym_OStream);
      END_STATE();
    case 1035:
      ACCEPT_TOKEN(anon_sym_OStream);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1036:
      ACCEPT_TOKEN(anon_sym_InStream);
      END_STATE();
    case 1037:
      ACCEPT_TOKEN(anon_sym_InStream);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1038:
      ACCEPT_TOKEN(anon_sym_OutStream);
      END_STATE();
    case 1039:
      ACCEPT_TOKEN(anon_sym_OutStream);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1040:
      ACCEPT_TOKEN(anon_sym_SecretText);
      END_STATE();
    case 1041:
      ACCEPT_TOKEN(anon_sym_SecretText);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1042:
      ACCEPT_TOKEN(anon_sym_Label);
      END_STATE();
    case 1043:
      ACCEPT_TOKEN(anon_sym_Label);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1044:
      ACCEPT_TOKEN(anon_sym_Text);
      END_STATE();
    case 1045:
      ACCEPT_TOKEN(anon_sym_Text);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1046:
      ACCEPT_TOKEN(anon_sym_Code);
      if (lookahead == 'u') ADVANCE(589);
      END_STATE();
    case 1047:
      ACCEPT_TOKEN(anon_sym_Code);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1048:
      ACCEPT_TOKEN(anon_sym_Record);
      if (lookahead == 'I') ADVANCE(1186);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1049:
      ACCEPT_TOKEN(anon_sym_Record);
      if (lookahead == 'I') ADVANCE(215);
      END_STATE();
    case 1050:
      ACCEPT_TOKEN(anon_sym_Codeunit);
      END_STATE();
    case 1051:
      ACCEPT_TOKEN(anon_sym_Codeunit);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1052:
      ACCEPT_TOKEN(anon_sym_Query);
      END_STATE();
    case 1053:
      ACCEPT_TOKEN(anon_sym_Query);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1054:
      ACCEPT_TOKEN(anon_sym_DotNet);
      END_STATE();
    case 1055:
      ACCEPT_TOKEN(anon_sym_DotNet);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1056:
      ACCEPT_TOKEN(anon_sym_array);
      END_STATE();
    case 1057:
      ACCEPT_TOKEN(anon_sym_array);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1058:
      ACCEPT_TOKEN(anon_sym_fields);
      END_STATE();
    case 1059:
      ACCEPT_TOKEN(anon_sym_fields);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1060:
      ACCEPT_TOKEN(anon_sym_field);
      END_STATE();
    case 1061:
      ACCEPT_TOKEN(anon_sym_field);
      if (lookahead == 's') ADVANCE(1058);
      END_STATE();
    case 1062:
      ACCEPT_TOKEN(anon_sym_LPAREN);
      END_STATE();
    case 1063:
      ACCEPT_TOKEN(anon_sym_RPAREN);
      END_STATE();
    case 1064:
      ACCEPT_TOKEN(anon_sym_where);
      END_STATE();
    case 1065:
      ACCEPT_TOKEN(anon_sym_if);
      END_STATE();
    case 1066:
      ACCEPT_TOKEN(anon_sym_if);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1067:
      ACCEPT_TOKEN(anon_sym_else);
      END_STATE();
    case 1068:
      ACCEPT_TOKEN(anon_sym_else);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1069:
      ACCEPT_TOKEN(anon_sym_const);
      END_STATE();
    case 1070:
      ACCEPT_TOKEN(anon_sym_filter);
      END_STATE();
    case 1071:
      ACCEPT_TOKEN(anon_sym_lookup);
      END_STATE();
    case 1072:
      ACCEPT_TOKEN(anon_sym_count);
      END_STATE();
    case 1073:
      ACCEPT_TOKEN(anon_sym_sum);
      END_STATE();
    case 1074:
      ACCEPT_TOKEN(anon_sym_average);
      END_STATE();
    case 1075:
      ACCEPT_TOKEN(anon_sym_min);
      END_STATE();
    case 1076:
      ACCEPT_TOKEN(anon_sym_max);
      END_STATE();
    case 1077:
      ACCEPT_TOKEN(anon_sym_CONST);
      END_STATE();
    case 1078:
      ACCEPT_TOKEN(anon_sym_FILTER);
      END_STATE();
    case 1079:
      ACCEPT_TOKEN(anon_sym_FILTER);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1080:
      ACCEPT_TOKEN(anon_sym_FIELD);
      END_STATE();
    case 1081:
      ACCEPT_TOKEN(anon_sym_UPPERLIMIT);
      END_STATE();
    case 1082:
      ACCEPT_TOKEN(anon_sym_UPPERLIMIT);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1083:
      ACCEPT_TOKEN(anon_sym_LT_GT);
      END_STATE();
    case 1084:
      ACCEPT_TOKEN(anon_sym_LT_EQ);
      END_STATE();
    case 1085:
      ACCEPT_TOKEN(anon_sym_GT_EQ);
      END_STATE();
    case 1086:
      ACCEPT_TOKEN(anon_sym_LT);
      if (lookahead == '=') ADVANCE(1084);
      if (lookahead == '>') ADVANCE(1083);
      END_STATE();
    case 1087:
      ACCEPT_TOKEN(anon_sym_GT);
      if (lookahead == '=') ADVANCE(1085);
      END_STATE();
    case 1088:
      ACCEPT_TOKEN(anon_sym_IN);
      END_STATE();
    case 1089:
      ACCEPT_TOKEN(anon_sym_OnLookup);
      END_STATE();
    case 1090:
      ACCEPT_TOKEN(anon_sym_OnAssistEdit);
      END_STATE();
    case 1091:
      ACCEPT_TOKEN(anon_sym_OnDrillDown);
      END_STATE();
    case 1092:
      ACCEPT_TOKEN(anon_sym_keys);
      END_STATE();
    case 1093:
      ACCEPT_TOKEN(anon_sym_keys);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1094:
      ACCEPT_TOKEN(anon_sym_key);
      END_STATE();
    case 1095:
      ACCEPT_TOKEN(anon_sym_key);
      if (lookahead == 's') ADVANCE(1092);
      END_STATE();
    case 1096:
      ACCEPT_TOKEN(sym_procedure_modifier);
      END_STATE();
    case 1097:
      ACCEPT_TOKEN(sym_procedure_modifier);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1098:
      ACCEPT_TOKEN(anon_sym_procedure);
      END_STATE();
    case 1099:
      ACCEPT_TOKEN(anon_sym_procedure);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1100:
      ACCEPT_TOKEN(anon_sym_PLUS);
      END_STATE();
    case 1101:
      ACCEPT_TOKEN(anon_sym_DASH);
      END_STATE();
    case 1102:
      ACCEPT_TOKEN(anon_sym_STAR);
      END_STATE();
    case 1103:
      ACCEPT_TOKEN(anon_sym_SLASH);
      END_STATE();
    case 1104:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'A') ADVANCE(1383);
      if (lookahead == 'O') ADVANCE(1172);
      if (lookahead == 'T') ADVANCE(1337);
      if (lookahead == 'V') ADVANCE(1151);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('B' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1105:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'B') ADVANCE(1440);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1106:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'C') ADVANCE(1299);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1107:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'D') ADVANCE(1338);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1108:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'E') ADVANCE(1127);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1109:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'E') ADVANCE(1126);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1110:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'I') ADVANCE(1117);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1111:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'I') ADVANCE(1119);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1112:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'I') ADVANCE(1334);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1113:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'I') ADVANCE(1131);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1114:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'I') ADVANCE(1186);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1115:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'I') ADVANCE(1188);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1116:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'I') ADVANCE(1189);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1117:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'L') ADVANCE(1134);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1118:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'L') ADVANCE(1111);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1119:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'M') ADVANCE(1113);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1120:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'N') ADVANCE(1224);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1121:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'P') ADVANCE(1108);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1122:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'P') ADVANCE(1121);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1123:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'P') ADVANCE(1163);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1124:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'P') ADVANCE(1165);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1125:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'P') ADVANCE(1167);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1126:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'R') ADVANCE(1079);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1127:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'R') ADVANCE(1118);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1128:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'S') ADVANCE(1418);
      if (lookahead == 'p') ADVANCE(1422);
      if (lookahead == 'u') ADVANCE(1403);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1129:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'S') ADVANCE(1426);
      if (lookahead == 't') ADVANCE(1213);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1130:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'S') ADVANCE(1428);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1131:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'T') ADVANCE(1082);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1132:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'T') ADVANCE(1451);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1133:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'T') ADVANCE(1240);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1134:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'T') ADVANCE(1109);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1135:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1173);
      if (lookahead == 'i') ADVANCE(1394);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1136:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1173);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1137:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1030);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1138:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1002);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1139:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1106);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1140:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1447);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1141:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1398);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1142:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1377);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1143:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1294);
      if (lookahead == 'c') ADVANCE(1425);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1144:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1294);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1145:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1308);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1146:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1448);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1147:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1174);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1148:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1363);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1149:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1290);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1150:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1309);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1151:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1302);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1152:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1310);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1153:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1331);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1154:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1321);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1155:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1303);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1156:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1376);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1157:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1293);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1158:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1414);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1159:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1420);
      if (lookahead == 'r') ADVANCE(1277);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1160:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1369);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1161:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1417);
      if (lookahead == 'e') ADVANCE(1176);
      if (lookahead == 'i') ADVANCE(1143);
      if (lookahead == 'o') ADVANCE(1402);
      if (lookahead == 'u') ADVANCE(1371);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1162:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1417);
      if (lookahead == 'e') ADVANCE(1176);
      if (lookahead == 'i') ADVANCE(1144);
      if (lookahead == 'u') ADVANCE(1371);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1163:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1251);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1164:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1396);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1165:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1252);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1166:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1421);
      if (lookahead == 'e') ADVANCE(1176);
      if (lookahead == 'u') ADVANCE(1371);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1167:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1256);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1168:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1427);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1169:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1430);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1170:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'a') ADVANCE(1361);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('b' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1171:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'b') ADVANCE(1019);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1172:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'b') ADVANCE(1286);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1173:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'b') ADVANCE(1220);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1174:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'b') ADVANCE(1300);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1175:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'c') ADVANCE(1415);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1176:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'c') ADVANCE(1263);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1177:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'c') ADVANCE(1348);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1178:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'c') ADVANCE(1411);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1179:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'c') ADVANCE(1157);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1180:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'c') ADVANCE(1228);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1181:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'c') ADVANCE(1384);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1182:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'c') ADVANCE(1356);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1183:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'c') ADVANCE(1169);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1184:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1009);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1185:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1048);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1186:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1011);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1187:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1470);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1188:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(955);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1189:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(953);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1190:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1114);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1191:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1266);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1192:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1217);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1193:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1391);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1194:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1441);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1195:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1208);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1196:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'd') ADVANCE(1235);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1197:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1443);
      if (lookahead == 'i') ADVANCE(1314);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1198:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(989);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1199:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(992);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1200:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(996);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1201:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(998);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1202:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1025);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1203:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1105);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1204:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1358);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1205:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1490);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1206:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1461);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1207:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1463);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1208:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1047);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1209:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1068);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1210:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(994);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1211:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(908);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1212:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1099);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1213:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1253);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1214:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1191);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1215:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1132);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1216:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1177);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1217:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1435);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1218:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1181);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1219:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1250);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1220:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1289);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1221:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1450);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1222:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1364);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1223:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1145);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1224:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1406);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1225:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1150);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1226:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1365);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1227:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1407);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1228:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1194);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1229:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1323);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1230:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1366);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1231:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1152);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1232:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1410);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1233:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1295);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1234:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1367);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1235:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1368);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1236:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1158);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1237:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1379);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1238:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1370);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1239:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1178);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1240:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1444);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1241:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1115);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1242:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1154);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1243:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1116);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1244:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1254);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1245:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'e') ADVANCE(1182);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1246:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'f') ADVANCE(1066);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1247:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'f') ADVANCE(1271);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1248:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1112);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1249:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1015);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1250:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1278);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1251:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1203);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1252:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1241);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1253:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1230);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1254:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1234);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1255:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1238);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1256:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1243);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1257:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'g') ADVANCE(1255);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1258:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'h') ADVANCE(1148);
      if (lookahead == 'o') ADVANCE(1192);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1259:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'h') ADVANCE(1148);
      if (lookahead == 'o') ADVANCE(1195);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1260:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1248);
      if (lookahead == 'l') ADVANCE(1341);
      if (lookahead == 'o') ADVANCE(1340);
      if (lookahead == 'y') ADVANCE(1416);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1261:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1248);
      if (lookahead == 'l') ADVANCE(1341);
      if (lookahead == 'o') ADVANCE(1340);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1262:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1304);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1263:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1313);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1264:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1247);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1265:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1184);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1266:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1137);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1267:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1395);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1268:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1153);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1269:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1257);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1270:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1344);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1271:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1183);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1272:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1347);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1273:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1349);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1274:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1301);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1275:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1291);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1276:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1409);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1277:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1298);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1278:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1324);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1279:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1413);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1280:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1233);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1281:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1316);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1282:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1350);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1283:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1353);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1284:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1354);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1285:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'i') ADVANCE(1355);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1286:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'j') ADVANCE(1239);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1287:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'k') ADVANCE(1434);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1288:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'k') ADVANCE(1229);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1289:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1043);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1290:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(987);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1291:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1474);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1292:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1107);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1293:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1097);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1294:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1343);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1295:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1193);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1296:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1242);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1297:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1138);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1298:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1292);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1299:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1164);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1300:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1215);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1301:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1196);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1302:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1438);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1303:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1399);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1304:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1423);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1305:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1400);
      if (lookahead == 'n') ADVANCE(1187);
      if (lookahead == 'x') ADVANCE(1279);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1306:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1400);
      if (lookahead == 'n') ADVANCE(1187);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1307:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'l') ADVANCE(1400);
      if (lookahead == 'x') ADVANCE(1279);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1308:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'm') ADVANCE(1035);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1309:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'm') ADVANCE(1037);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1310:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'm') ADVANCE(1039);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1311:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'm') ADVANCE(1466);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1312:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'm') ADVANCE(1436);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1313:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'm') ADVANCE(1149);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1314:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'm') ADVANCE(1200);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1315:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'm') ADVANCE(1267);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1316:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'm') ADVANCE(1201);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1317:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1129);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1318:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1104);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1319:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1017);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1320:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1007);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1321:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1004);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1322:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1000);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1323:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1023);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1324:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1468);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1325:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(966);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1326:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(964);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1327:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1437);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1328:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1187);
      if (lookahead == 'x') ADVANCE(1279);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1329:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1276);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1330:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1392);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1331:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1408);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1332:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1424);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1333:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1156);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1334:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1431);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1335:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1419);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1336:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'n') ADVANCE(1125);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1337:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1288);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1338:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1442);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1339:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1318);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1340:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1296);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1341:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1171);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1342:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1287);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1343:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1249);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1344:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1319);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1345:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1179);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1346:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1180);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1347:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1320);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1348:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1374);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1349:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1333);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1350:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1322);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1351:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1375);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1352:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1342);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1353:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1325);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1354:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1330);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1355:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1326);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1356:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1378);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1357:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'o') ADVANCE(1195);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1358:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'p') ADVANCE(1236);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1359:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'p') ADVANCE(1211);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1360:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'p') ADVANCE(1422);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1361:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'p') ADVANCE(1429);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1362:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'p') ADVANCE(1124);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1363:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(991);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1364:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1446);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1365:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1123);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1366:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(982);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1367:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(984);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1368:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1021);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1369:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(973);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1370:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(919);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1371:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1168);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1372:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1140);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1373:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1372);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1374:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1185);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1375:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1312);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1376:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1449);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1377:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1268);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1378:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1190);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1379:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1315);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1380:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1269);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1381:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1146);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1382:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1223);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1383:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1381);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1384:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1227);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1385:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1225);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1386:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1346);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1387:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1231);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1388:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1212);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1389:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'r') ADVANCE(1439);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1390:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1093);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1391:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1059);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1392:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(923);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1393:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1339);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1394:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1404);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1395:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1401);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1396:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1397);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1397:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1264);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1398:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1205);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1399:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1207);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1400:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1209);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1401:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 's') ADVANCE(1284);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1402:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1120);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1403:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1130);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1404:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(975);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1405:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1045);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1406:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1055);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1407:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1133);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1408:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1013);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1409:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1051);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1410:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1033);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1411:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1029);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1412:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1041);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1413:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1492);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1414:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1472);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1415:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1270);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1416:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1198);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1417:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1199);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1418:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1382);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1419:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1213);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1420:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1139);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1421:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1210);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1422:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1272);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1423:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1226);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1424:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1275);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1425:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1273);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1426:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1385);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1427:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1282);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1428:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1387);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1429:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1283);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1430:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1285);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1431:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 't') ADVANCE(1244);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1432:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1265);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1433:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1222);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1434:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1362);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1435:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1329);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1436:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1297);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1437:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1311);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1438:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1202);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1439:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1206);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1440:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1274);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1441:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'u') ADVANCE(1388);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1442:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'w') ADVANCE(1336);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1443:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'x') ADVANCE(1405);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1444:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'x') ADVANCE(1412);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1445:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'x') ADVANCE(1279);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1446:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'y') ADVANCE(1053);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1447:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'y') ADVANCE(1057);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1448:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'y') ADVANCE(1027);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1449:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'y') ADVANCE(980);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1450:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'y') ADVANCE(1390);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1451:
      ACCEPT_TOKEN(sym_identifier);
      if (lookahead == 'y') ADVANCE(1359);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1452:
      ACCEPT_TOKEN(sym_identifier);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1453:
      ACCEPT_TOKEN(anon_sym_DQUOTE);
      END_STATE();
    case 1454:
      ACCEPT_TOKEN(aux_sym__quoted_identifier_token1);
      END_STATE();
    case 1455:
      ACCEPT_TOKEN(aux_sym__quoted_identifier_token1);
      if (lookahead == '.') ADVANCE(1454);
      if (lookahead == '\t' ||
          (0x0b <= lookahead && lookahead <= '\r') ||
          lookahead == ' ') ADVANCE(1455);
      if (lookahead != 0 &&
          (lookahead < '\t' || '\r' < lookahead) &&
          lookahead != '"' &&
          lookahead != '\\') ADVANCE(1454);
      END_STATE();
    case 1456:
      ACCEPT_TOKEN(aux_sym__quoted_identifier_token2);
      END_STATE();
    case 1457:
      ACCEPT_TOKEN(sym_integer);
      if (('0' <= lookahead && lookahead <= '9')) ADVANCE(1457);
      END_STATE();
    case 1458:
      ACCEPT_TOKEN(sym_string_literal);
      END_STATE();
    case 1459:
      ACCEPT_TOKEN(anon_sym_Clustered);
      END_STATE();
    case 1460:
      ACCEPT_TOKEN(anon_sym_true);
      END_STATE();
    case 1461:
      ACCEPT_TOKEN(anon_sym_true);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1462:
      ACCEPT_TOKEN(anon_sym_false);
      END_STATE();
    case 1463:
      ACCEPT_TOKEN(anon_sym_false);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1464:
      ACCEPT_TOKEN(sym_temporary);
      END_STATE();
    case 1465:
      ACCEPT_TOKEN(anon_sym_Enum);
      END_STATE();
    case 1466:
      ACCEPT_TOKEN(anon_sym_Enum);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1467:
      ACCEPT_TOKEN(anon_sym_begin);
      END_STATE();
    case 1468:
      ACCEPT_TOKEN(anon_sym_begin);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1469:
      ACCEPT_TOKEN(anon_sym_end);
      END_STATE();
    case 1470:
      ACCEPT_TOKEN(anon_sym_end);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1471:
      ACCEPT_TOKEN(anon_sym_repeat);
      END_STATE();
    case 1472:
      ACCEPT_TOKEN(anon_sym_repeat);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1473:
      ACCEPT_TOKEN(anon_sym_until);
      END_STATE();
    case 1474:
      ACCEPT_TOKEN(anon_sym_until);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1475:
      ACCEPT_TOKEN(anon_sym_COLON_EQ);
      END_STATE();
    case 1476:
      ACCEPT_TOKEN(anon_sym_COLON_COLON);
      END_STATE();
    case 1477:
      ACCEPT_TOKEN(anon_sym_Get);
      END_STATE();
    case 1478:
      ACCEPT_TOKEN(anon_sym_FindSet);
      END_STATE();
    case 1479:
      ACCEPT_TOKEN(anon_sym_Insert);
      END_STATE();
    case 1480:
      ACCEPT_TOKEN(anon_sym_Modify);
      END_STATE();
    case 1481:
      ACCEPT_TOKEN(anon_sym_Delete);
      END_STATE();
    case 1482:
      ACCEPT_TOKEN(anon_sym_SetRange);
      END_STATE();
    case 1483:
      ACCEPT_TOKEN(anon_sym_SetFilter);
      END_STATE();
    case 1484:
      ACCEPT_TOKEN(anon_sym_Reset);
      END_STATE();
    case 1485:
      ACCEPT_TOKEN(anon_sym_then);
      END_STATE();
    case 1486:
      ACCEPT_TOKEN(anon_sym_FindFirst);
      END_STATE();
    case 1487:
      ACCEPT_TOKEN(anon_sym_FindLast);
      END_STATE();
    case 1488:
      ACCEPT_TOKEN(anon_sym_Next);
      END_STATE();
    case 1489:
      ACCEPT_TOKEN(anon_sym_case);
      END_STATE();
    case 1490:
      ACCEPT_TOKEN(anon_sym_case);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    case 1491:
      ACCEPT_TOKEN(anon_sym_exit);
      END_STATE();
    case 1492:
      ACCEPT_TOKEN(anon_sym_exit);
      if (('0' <= lookahead && lookahead <= '9') ||
          ('A' <= lookahead && lookahead <= 'Z') ||
          lookahead == '_' ||
          ('a' <= lookahead && lookahead <= 'z')) ADVANCE(1452);
      END_STATE();
    default:
      return false;
  }
}

static const TSLexMode ts_lex_modes[STATE_COUNT] = {
  [0] = {.lex_state = 0},
  [1] = {.lex_state = 889},
  [2] = {.lex_state = 16},
  [3] = {.lex_state = 16},
  [4] = {.lex_state = 889},
  [5] = {.lex_state = 889},
  [6] = {.lex_state = 889},
  [7] = {.lex_state = 889},
  [8] = {.lex_state = 889},
  [9] = {.lex_state = 889},
  [10] = {.lex_state = 889},
  [11] = {.lex_state = 4},
  [12] = {.lex_state = 4},
  [13] = {.lex_state = 7},
  [14] = {.lex_state = 2},
  [15] = {.lex_state = 4},
  [16] = {.lex_state = 4},
  [17] = {.lex_state = 7},
  [18] = {.lex_state = 4},
  [19] = {.lex_state = 4},
  [20] = {.lex_state = 2},
  [21] = {.lex_state = 2},
  [22] = {.lex_state = 2},
  [23] = {.lex_state = 2},
  [24] = {.lex_state = 4},
  [25] = {.lex_state = 2},
  [26] = {.lex_state = 2},
  [27] = {.lex_state = 2},
  [28] = {.lex_state = 2},
  [29] = {.lex_state = 2},
  [30] = {.lex_state = 2},
  [31] = {.lex_state = 2},
  [32] = {.lex_state = 7},
  [33] = {.lex_state = 4},
  [34] = {.lex_state = 2},
  [35] = {.lex_state = 7},
  [36] = {.lex_state = 7},
  [37] = {.lex_state = 9},
  [38] = {.lex_state = 9},
  [39] = {.lex_state = 9},
  [40] = {.lex_state = 9},
  [41] = {.lex_state = 889},
  [42] = {.lex_state = 889},
  [43] = {.lex_state = 889},
  [44] = {.lex_state = 17},
  [45] = {.lex_state = 17},
  [46] = {.lex_state = 18},
  [47] = {.lex_state = 889},
  [48] = {.lex_state = 5},
  [49] = {.lex_state = 5},
  [50] = {.lex_state = 5},
  [51] = {.lex_state = 6},
  [52] = {.lex_state = 2},
  [53] = {.lex_state = 6},
  [54] = {.lex_state = 6},
  [55] = {.lex_state = 2},
  [56] = {.lex_state = 18},
  [57] = {.lex_state = 2},
  [58] = {.lex_state = 2},
  [59] = {.lex_state = 18},
  [60] = {.lex_state = 18},
  [61] = {.lex_state = 18},
  [62] = {.lex_state = 18},
  [63] = {.lex_state = 2},
  [64] = {.lex_state = 6},
  [65] = {.lex_state = 5},
  [66] = {.lex_state = 2},
  [67] = {.lex_state = 18},
  [68] = {.lex_state = 18},
  [69] = {.lex_state = 2},
  [70] = {.lex_state = 2},
  [71] = {.lex_state = 7},
  [72] = {.lex_state = 7},
  [73] = {.lex_state = 7},
  [74] = {.lex_state = 5},
  [75] = {.lex_state = 2},
  [76] = {.lex_state = 5},
  [77] = {.lex_state = 7},
  [78] = {.lex_state = 5},
  [79] = {.lex_state = 5},
  [80] = {.lex_state = 6},
  [81] = {.lex_state = 5},
  [82] = {.lex_state = 5},
  [83] = {.lex_state = 18},
  [84] = {.lex_state = 5},
  [85] = {.lex_state = 5},
  [86] = {.lex_state = 18},
  [87] = {.lex_state = 5},
  [88] = {.lex_state = 8},
  [89] = {.lex_state = 6},
  [90] = {.lex_state = 6},
  [91] = {.lex_state = 6},
  [92] = {.lex_state = 6},
  [93] = {.lex_state = 6},
  [94] = {.lex_state = 18},
  [95] = {.lex_state = 6},
  [96] = {.lex_state = 18},
  [97] = {.lex_state = 6},
  [98] = {.lex_state = 6},
  [99] = {.lex_state = 6},
  [100] = {.lex_state = 8},
  [101] = {.lex_state = 8},
  [102] = {.lex_state = 8},
  [103] = {.lex_state = 5},
  [104] = {.lex_state = 2},
  [105] = {.lex_state = 2},
  [106] = {.lex_state = 7},
  [107] = {.lex_state = 7},
  [108] = {.lex_state = 7},
  [109] = {.lex_state = 7},
  [110] = {.lex_state = 7},
  [111] = {.lex_state = 7},
  [112] = {.lex_state = 8},
  [113] = {.lex_state = 7},
  [114] = {.lex_state = 7},
  [115] = {.lex_state = 18},
  [116] = {.lex_state = 2},
  [117] = {.lex_state = 2},
  [118] = {.lex_state = 7},
  [119] = {.lex_state = 2},
  [120] = {.lex_state = 7},
  [121] = {.lex_state = 3},
  [122] = {.lex_state = 3},
  [123] = {.lex_state = 18},
  [124] = {.lex_state = 18},
  [125] = {.lex_state = 3},
  [126] = {.lex_state = 18},
  [127] = {.lex_state = 3},
  [128] = {.lex_state = 3},
  [129] = {.lex_state = 27},
  [130] = {.lex_state = 3},
  [131] = {.lex_state = 3},
  [132] = {.lex_state = 3},
  [133] = {.lex_state = 32},
  [134] = {.lex_state = 3},
  [135] = {.lex_state = 3},
  [136] = {.lex_state = 32},
  [137] = {.lex_state = 3},
  [138] = {.lex_state = 3},
  [139] = {.lex_state = 3},
  [140] = {.lex_state = 3},
  [141] = {.lex_state = 3},
  [142] = {.lex_state = 3},
  [143] = {.lex_state = 3},
  [144] = {.lex_state = 3},
  [145] = {.lex_state = 3},
  [146] = {.lex_state = 3},
  [147] = {.lex_state = 3},
  [148] = {.lex_state = 18},
  [149] = {.lex_state = 3},
  [150] = {.lex_state = 3},
  [151] = {.lex_state = 3},
  [152] = {.lex_state = 3},
  [153] = {.lex_state = 3},
  [154] = {.lex_state = 3},
  [155] = {.lex_state = 3},
  [156] = {.lex_state = 3},
  [157] = {.lex_state = 3},
  [158] = {.lex_state = 3},
  [159] = {.lex_state = 3},
  [160] = {.lex_state = 3},
  [161] = {.lex_state = 3},
  [162] = {.lex_state = 3},
  [163] = {.lex_state = 3},
  [164] = {.lex_state = 3},
  [165] = {.lex_state = 3},
  [166] = {.lex_state = 3},
  [167] = {.lex_state = 3},
  [168] = {.lex_state = 3},
  [169] = {.lex_state = 3},
  [170] = {.lex_state = 3},
  [171] = {.lex_state = 32},
  [172] = {.lex_state = 32},
  [173] = {.lex_state = 889},
  [174] = {.lex_state = 889},
  [175] = {.lex_state = 889},
  [176] = {.lex_state = 889},
  [177] = {.lex_state = 889},
  [178] = {.lex_state = 889},
  [179] = {.lex_state = 0},
  [180] = {.lex_state = 0},
  [181] = {.lex_state = 889},
  [182] = {.lex_state = 889},
  [183] = {.lex_state = 889},
  [184] = {.lex_state = 889},
  [185] = {.lex_state = 889},
  [186] = {.lex_state = 889},
  [187] = {.lex_state = 889},
  [188] = {.lex_state = 889},
  [189] = {.lex_state = 889},
  [190] = {.lex_state = 5},
  [191] = {.lex_state = 889},
  [192] = {.lex_state = 889},
  [193] = {.lex_state = 889},
  [194] = {.lex_state = 889},
  [195] = {.lex_state = 889},
  [196] = {.lex_state = 889},
  [197] = {.lex_state = 889},
  [198] = {.lex_state = 889},
  [199] = {.lex_state = 889},
  [200] = {.lex_state = 889},
  [201] = {.lex_state = 889},
  [202] = {.lex_state = 889},
  [203] = {.lex_state = 889},
  [204] = {.lex_state = 889},
  [205] = {.lex_state = 889},
  [206] = {.lex_state = 889},
  [207] = {.lex_state = 18},
  [208] = {.lex_state = 889},
  [209] = {.lex_state = 889},
  [210] = {.lex_state = 889},
  [211] = {.lex_state = 889},
  [212] = {.lex_state = 889},
  [213] = {.lex_state = 889},
  [214] = {.lex_state = 889},
  [215] = {.lex_state = 889},
  [216] = {.lex_state = 889},
  [217] = {.lex_state = 889},
  [218] = {.lex_state = 889},
  [219] = {.lex_state = 889},
  [220] = {.lex_state = 889},
  [221] = {.lex_state = 889},
  [222] = {.lex_state = 889},
  [223] = {.lex_state = 889},
  [224] = {.lex_state = 889},
  [225] = {.lex_state = 889},
  [226] = {.lex_state = 889},
  [227] = {.lex_state = 889},
  [228] = {.lex_state = 889},
  [229] = {.lex_state = 889},
  [230] = {.lex_state = 889},
  [231] = {.lex_state = 889},
  [232] = {.lex_state = 889},
  [233] = {.lex_state = 889},
  [234] = {.lex_state = 5},
  [235] = {.lex_state = 889},
  [236] = {.lex_state = 889},
  [237] = {.lex_state = 5},
  [238] = {.lex_state = 5},
  [239] = {.lex_state = 889},
  [240] = {.lex_state = 889},
  [241] = {.lex_state = 889},
  [242] = {.lex_state = 889},
  [243] = {.lex_state = 889},
  [244] = {.lex_state = 5},
  [245] = {.lex_state = 6},
  [246] = {.lex_state = 889},
  [247] = {.lex_state = 889},
  [248] = {.lex_state = 6},
  [249] = {.lex_state = 5},
  [250] = {.lex_state = 5},
  [251] = {.lex_state = 5},
  [252] = {.lex_state = 5},
  [253] = {.lex_state = 889},
  [254] = {.lex_state = 5},
  [255] = {.lex_state = 6},
  [256] = {.lex_state = 0},
  [257] = {.lex_state = 6},
  [258] = {.lex_state = 889},
  [259] = {.lex_state = 5},
  [260] = {.lex_state = 5},
  [261] = {.lex_state = 889},
  [262] = {.lex_state = 5},
  [263] = {.lex_state = 5},
  [264] = {.lex_state = 5},
  [265] = {.lex_state = 5},
  [266] = {.lex_state = 5},
  [267] = {.lex_state = 5},
  [268] = {.lex_state = 5},
  [269] = {.lex_state = 5},
  [270] = {.lex_state = 5},
  [271] = {.lex_state = 5},
  [272] = {.lex_state = 5},
  [273] = {.lex_state = 5},
  [274] = {.lex_state = 5},
  [275] = {.lex_state = 5},
  [276] = {.lex_state = 5},
  [277] = {.lex_state = 5},
  [278] = {.lex_state = 5},
  [279] = {.lex_state = 5},
  [280] = {.lex_state = 5},
  [281] = {.lex_state = 5},
  [282] = {.lex_state = 5},
  [283] = {.lex_state = 5},
  [284] = {.lex_state = 6},
  [285] = {.lex_state = 6},
  [286] = {.lex_state = 6},
  [287] = {.lex_state = 6},
  [288] = {.lex_state = 6},
  [289] = {.lex_state = 0},
  [290] = {.lex_state = 6},
  [291] = {.lex_state = 6},
  [292] = {.lex_state = 6},
  [293] = {.lex_state = 6},
  [294] = {.lex_state = 6},
  [295] = {.lex_state = 6},
  [296] = {.lex_state = 6},
  [297] = {.lex_state = 6},
  [298] = {.lex_state = 6},
  [299] = {.lex_state = 6},
  [300] = {.lex_state = 6},
  [301] = {.lex_state = 6},
  [302] = {.lex_state = 6},
  [303] = {.lex_state = 6},
  [304] = {.lex_state = 6},
  [305] = {.lex_state = 6},
  [306] = {.lex_state = 6},
  [307] = {.lex_state = 6},
  [308] = {.lex_state = 6},
  [309] = {.lex_state = 6},
  [310] = {.lex_state = 6},
  [311] = {.lex_state = 6},
  [312] = {.lex_state = 6},
  [313] = {.lex_state = 6},
  [314] = {.lex_state = 5},
  [315] = {.lex_state = 6},
  [316] = {.lex_state = 889},
  [317] = {.lex_state = 6},
  [318] = {.lex_state = 18},
  [319] = {.lex_state = 7},
  [320] = {.lex_state = 16},
  [321] = {.lex_state = 7},
  [322] = {.lex_state = 7},
  [323] = {.lex_state = 7},
  [324] = {.lex_state = 889},
  [325] = {.lex_state = 7},
  [326] = {.lex_state = 7},
  [327] = {.lex_state = 7},
  [328] = {.lex_state = 7},
  [329] = {.lex_state = 7},
  [330] = {.lex_state = 7},
  [331] = {.lex_state = 7},
  [332] = {.lex_state = 7},
  [333] = {.lex_state = 7},
  [334] = {.lex_state = 7},
  [335] = {.lex_state = 7},
  [336] = {.lex_state = 7},
  [337] = {.lex_state = 7},
  [338] = {.lex_state = 7},
  [339] = {.lex_state = 7},
  [340] = {.lex_state = 7},
  [341] = {.lex_state = 7},
  [342] = {.lex_state = 7},
  [343] = {.lex_state = 7},
  [344] = {.lex_state = 18},
  [345] = {.lex_state = 16},
  [346] = {.lex_state = 2},
  [347] = {.lex_state = 2},
  [348] = {.lex_state = 16},
  [349] = {.lex_state = 889},
  [350] = {.lex_state = 2},
  [351] = {.lex_state = 2},
  [352] = {.lex_state = 2},
  [353] = {.lex_state = 2},
  [354] = {.lex_state = 2},
  [355] = {.lex_state = 2},
  [356] = {.lex_state = 2},
  [357] = {.lex_state = 2},
  [358] = {.lex_state = 2},
  [359] = {.lex_state = 2},
  [360] = {.lex_state = 889},
  [361] = {.lex_state = 2},
  [362] = {.lex_state = 2},
  [363] = {.lex_state = 2},
  [364] = {.lex_state = 2},
  [365] = {.lex_state = 2},
  [366] = {.lex_state = 2},
  [367] = {.lex_state = 2},
  [368] = {.lex_state = 2},
  [369] = {.lex_state = 2},
  [370] = {.lex_state = 7},
  [371] = {.lex_state = 2},
  [372] = {.lex_state = 7},
  [373] = {.lex_state = 7},
  [374] = {.lex_state = 7},
  [375] = {.lex_state = 2},
  [376] = {.lex_state = 2},
  [377] = {.lex_state = 7},
  [378] = {.lex_state = 2},
  [379] = {.lex_state = 2},
  [380] = {.lex_state = 2},
  [381] = {.lex_state = 16},
  [382] = {.lex_state = 2},
  [383] = {.lex_state = 2},
  [384] = {.lex_state = 2},
  [385] = {.lex_state = 2},
  [386] = {.lex_state = 7},
  [387] = {.lex_state = 7},
  [388] = {.lex_state = 7},
  [389] = {.lex_state = 7},
  [390] = {.lex_state = 889},
  [391] = {.lex_state = 889},
  [392] = {.lex_state = 889},
  [393] = {.lex_state = 889},
  [394] = {.lex_state = 2},
  [395] = {.lex_state = 2},
  [396] = {.lex_state = 7},
  [397] = {.lex_state = 18},
  [398] = {.lex_state = 18},
  [399] = {.lex_state = 889},
  [400] = {.lex_state = 18},
  [401] = {.lex_state = 18},
  [402] = {.lex_state = 18},
  [403] = {.lex_state = 18},
  [404] = {.lex_state = 889},
  [405] = {.lex_state = 18},
  [406] = {.lex_state = 889},
  [407] = {.lex_state = 889},
  [408] = {.lex_state = 0},
  [409] = {.lex_state = 18},
  [410] = {.lex_state = 18},
  [411] = {.lex_state = 18},
  [412] = {.lex_state = 889},
  [413] = {.lex_state = 889},
  [414] = {.lex_state = 889},
  [415] = {.lex_state = 4},
  [416] = {.lex_state = 889},
  [417] = {.lex_state = 4},
  [418] = {.lex_state = 889},
  [419] = {.lex_state = 889},
  [420] = {.lex_state = 889},
  [421] = {.lex_state = 4},
  [422] = {.lex_state = 889},
  [423] = {.lex_state = 4},
  [424] = {.lex_state = 889},
  [425] = {.lex_state = 4},
  [426] = {.lex_state = 889},
  [427] = {.lex_state = 4},
  [428] = {.lex_state = 889},
  [429] = {.lex_state = 889},
  [430] = {.lex_state = 4},
  [431] = {.lex_state = 889},
  [432] = {.lex_state = 889},
  [433] = {.lex_state = 889},
  [434] = {.lex_state = 889},
  [435] = {.lex_state = 889},
  [436] = {.lex_state = 889},
  [437] = {.lex_state = 889},
  [438] = {.lex_state = 889},
  [439] = {.lex_state = 889},
  [440] = {.lex_state = 889},
  [441] = {.lex_state = 889},
  [442] = {.lex_state = 889},
  [443] = {.lex_state = 889},
  [444] = {.lex_state = 889},
  [445] = {.lex_state = 8},
  [446] = {.lex_state = 8},
  [447] = {.lex_state = 889},
  [448] = {.lex_state = 889},
  [449] = {.lex_state = 889},
  [450] = {.lex_state = 889},
  [451] = {.lex_state = 889},
  [452] = {.lex_state = 889},
  [453] = {.lex_state = 8},
  [454] = {.lex_state = 4},
  [455] = {.lex_state = 8},
  [456] = {.lex_state = 23},
  [457] = {.lex_state = 8},
  [458] = {.lex_state = 23},
  [459] = {.lex_state = 13},
  [460] = {.lex_state = 23},
  [461] = {.lex_state = 98},
  [462] = {.lex_state = 98},
  [463] = {.lex_state = 23},
  [464] = {.lex_state = 23},
  [465] = {.lex_state = 13},
  [466] = {.lex_state = 23},
  [467] = {.lex_state = 23},
  [468] = {.lex_state = 13},
  [469] = {.lex_state = 13},
  [470] = {.lex_state = 23},
  [471] = {.lex_state = 23},
  [472] = {.lex_state = 889},
  [473] = {.lex_state = 0},
  [474] = {.lex_state = 889},
  [475] = {.lex_state = 23},
  [476] = {.lex_state = 23},
  [477] = {.lex_state = 889},
  [478] = {.lex_state = 23},
  [479] = {.lex_state = 23},
  [480] = {.lex_state = 0},
  [481] = {.lex_state = 889},
  [482] = {.lex_state = 23},
  [483] = {.lex_state = 23},
  [484] = {.lex_state = 23},
  [485] = {.lex_state = 0},
  [486] = {.lex_state = 0},
  [487] = {.lex_state = 0},
  [488] = {.lex_state = 889},
  [489] = {.lex_state = 98},
  [490] = {.lex_state = 98},
  [491] = {.lex_state = 889},
  [492] = {.lex_state = 0},
  [493] = {.lex_state = 0},
  [494] = {.lex_state = 0},
  [495] = {.lex_state = 0},
  [496] = {.lex_state = 0},
  [497] = {.lex_state = 0},
  [498] = {.lex_state = 3},
  [499] = {.lex_state = 0},
  [500] = {.lex_state = 3},
  [501] = {.lex_state = 0},
  [502] = {.lex_state = 19},
  [503] = {.lex_state = 10},
  [504] = {.lex_state = 0},
  [505] = {.lex_state = 10},
  [506] = {.lex_state = 10},
  [507] = {.lex_state = 10},
  [508] = {.lex_state = 19},
  [509] = {.lex_state = 19},
  [510] = {.lex_state = 10},
  [511] = {.lex_state = 19},
  [512] = {.lex_state = 10},
  [513] = {.lex_state = 10},
  [514] = {.lex_state = 11},
  [515] = {.lex_state = 18},
  [516] = {.lex_state = 1},
  [517] = {.lex_state = 1},
  [518] = {.lex_state = 1},
  [519] = {.lex_state = 10},
  [520] = {.lex_state = 10},
  [521] = {.lex_state = 10},
  [522] = {.lex_state = 10},
  [523] = {.lex_state = 10},
  [524] = {.lex_state = 1},
  [525] = {.lex_state = 0},
  [526] = {.lex_state = 10},
  [527] = {.lex_state = 1},
  [528] = {.lex_state = 1},
  [529] = {.lex_state = 0},
  [530] = {.lex_state = 10},
  [531] = {.lex_state = 10},
  [532] = {.lex_state = 1},
  [533] = {.lex_state = 0},
  [534] = {.lex_state = 10},
  [535] = {.lex_state = 889},
  [536] = {.lex_state = 0},
  [537] = {.lex_state = 0},
  [538] = {.lex_state = 0},
  [539] = {.lex_state = 16},
  [540] = {.lex_state = 0},
  [541] = {.lex_state = 0},
  [542] = {.lex_state = 0},
  [543] = {.lex_state = 0},
  [544] = {.lex_state = 0},
  [545] = {.lex_state = 10},
  [546] = {.lex_state = 0},
  [547] = {.lex_state = 10},
  [548] = {.lex_state = 10},
  [549] = {.lex_state = 0},
  [550] = {.lex_state = 0},
  [551] = {.lex_state = 0},
  [552] = {.lex_state = 0},
  [553] = {.lex_state = 180},
  [554] = {.lex_state = 180},
  [555] = {.lex_state = 0},
  [556] = {.lex_state = 14},
  [557] = {.lex_state = 14},
  [558] = {.lex_state = 10},
  [559] = {.lex_state = 1},
  [560] = {.lex_state = 0},
  [561] = {.lex_state = 0},
  [562] = {.lex_state = 0},
  [563] = {.lex_state = 0},
  [564] = {.lex_state = 0},
  [565] = {.lex_state = 0},
  [566] = {.lex_state = 10},
  [567] = {.lex_state = 0},
  [568] = {.lex_state = 12},
  [569] = {.lex_state = 10},
  [570] = {.lex_state = 10},
  [571] = {.lex_state = 10},
  [572] = {.lex_state = 0},
  [573] = {.lex_state = 0},
  [574] = {.lex_state = 0},
  [575] = {.lex_state = 0},
  [576] = {.lex_state = 0},
  [577] = {.lex_state = 0},
  [578] = {.lex_state = 0},
  [579] = {.lex_state = 10},
  [580] = {.lex_state = 10},
  [581] = {.lex_state = 10},
  [582] = {.lex_state = 10},
  [583] = {.lex_state = 14},
  [584] = {.lex_state = 19},
  [585] = {.lex_state = 14},
  [586] = {.lex_state = 0},
  [587] = {.lex_state = 1},
  [588] = {.lex_state = 0},
  [589] = {.lex_state = 0},
  [590] = {.lex_state = 10},
  [591] = {.lex_state = 1},
  [592] = {.lex_state = 14},
  [593] = {.lex_state = 0},
  [594] = {.lex_state = 1},
  [595] = {.lex_state = 14},
  [596] = {.lex_state = 18},
  [597] = {.lex_state = 10},
  [598] = {.lex_state = 889},
  [599] = {.lex_state = 0},
  [600] = {.lex_state = 0},
  [601] = {.lex_state = 0},
  [602] = {.lex_state = 10},
  [603] = {.lex_state = 0},
  [604] = {.lex_state = 0},
  [605] = {.lex_state = 0},
  [606] = {.lex_state = 0},
  [607] = {.lex_state = 14},
  [608] = {.lex_state = 10},
  [609] = {.lex_state = 10},
  [610] = {.lex_state = 0},
  [611] = {.lex_state = 10},
  [612] = {.lex_state = 889},
  [613] = {.lex_state = 0},
  [614] = {.lex_state = 0},
  [615] = {.lex_state = 0},
  [616] = {.lex_state = 0},
  [617] = {.lex_state = 10},
  [618] = {.lex_state = 0},
  [619] = {.lex_state = 889},
  [620] = {.lex_state = 10},
  [621] = {.lex_state = 0},
  [622] = {.lex_state = 0},
  [623] = {.lex_state = 10},
  [624] = {.lex_state = 0},
  [625] = {.lex_state = 0},
  [626] = {.lex_state = 0},
  [627] = {.lex_state = 0},
  [628] = {.lex_state = 0},
  [629] = {.lex_state = 0},
  [630] = {.lex_state = 0},
  [631] = {.lex_state = 10},
  [632] = {.lex_state = 0},
  [633] = {.lex_state = 0},
  [634] = {.lex_state = 0},
  [635] = {.lex_state = 0},
  [636] = {.lex_state = 18},
  [637] = {.lex_state = 0},
  [638] = {.lex_state = 889},
  [639] = {.lex_state = 10},
  [640] = {.lex_state = 10},
  [641] = {.lex_state = 10},
  [642] = {.lex_state = 0},
  [643] = {.lex_state = 0},
  [644] = {.lex_state = 0},
  [645] = {.lex_state = 0},
  [646] = {.lex_state = 0},
  [647] = {.lex_state = 0},
  [648] = {.lex_state = 10},
  [649] = {.lex_state = 0},
  [650] = {.lex_state = 0},
  [651] = {.lex_state = 0},
  [652] = {.lex_state = 0},
  [653] = {.lex_state = 0},
  [654] = {.lex_state = 0},
  [655] = {.lex_state = 0},
  [656] = {.lex_state = 0},
  [657] = {.lex_state = 10},
  [658] = {.lex_state = 10},
  [659] = {.lex_state = 16},
  [660] = {.lex_state = 0},
  [661] = {.lex_state = 0},
  [662] = {.lex_state = 10},
  [663] = {.lex_state = 0},
  [664] = {.lex_state = 10},
  [665] = {.lex_state = 0},
  [666] = {.lex_state = 0},
  [667] = {.lex_state = 0},
  [668] = {.lex_state = 0},
  [669] = {.lex_state = 0},
  [670] = {.lex_state = 10},
  [671] = {.lex_state = 10},
  [672] = {.lex_state = 889},
  [673] = {.lex_state = 10},
  [674] = {.lex_state = 10},
  [675] = {.lex_state = 0},
  [676] = {.lex_state = 0},
  [677] = {.lex_state = 10},
  [678] = {.lex_state = 10},
  [679] = {.lex_state = 0},
  [680] = {.lex_state = 0},
  [681] = {.lex_state = 10},
  [682] = {.lex_state = 10},
  [683] = {.lex_state = 10},
  [684] = {.lex_state = 10},
  [685] = {.lex_state = 10},
  [686] = {.lex_state = 14},
  [687] = {.lex_state = 0},
  [688] = {.lex_state = 0},
  [689] = {.lex_state = 0},
  [690] = {.lex_state = 0},
  [691] = {.lex_state = 10},
  [692] = {.lex_state = 0},
  [693] = {.lex_state = 0},
  [694] = {.lex_state = 0},
  [695] = {.lex_state = 14},
  [696] = {.lex_state = 0},
  [697] = {.lex_state = 10},
  [698] = {.lex_state = 0},
  [699] = {.lex_state = 10},
  [700] = {.lex_state = 10},
  [701] = {.lex_state = 10},
  [702] = {.lex_state = 889},
  [703] = {.lex_state = 10},
  [704] = {.lex_state = 10},
  [705] = {.lex_state = 0},
  [706] = {.lex_state = 10},
  [707] = {.lex_state = 10},
  [708] = {.lex_state = 10},
  [709] = {.lex_state = 14},
  [710] = {.lex_state = 0},
  [711] = {.lex_state = 0},
  [712] = {.lex_state = 0},
  [713] = {.lex_state = 0},
  [714] = {.lex_state = 0},
  [715] = {.lex_state = 0},
  [716] = {.lex_state = 0},
  [717] = {.lex_state = 0},
  [718] = {.lex_state = 0},
  [719] = {.lex_state = 0},
  [720] = {.lex_state = 0},
  [721] = {.lex_state = 0},
  [722] = {.lex_state = 0},
  [723] = {.lex_state = 0},
  [724] = {.lex_state = 0},
  [725] = {.lex_state = 0},
  [726] = {.lex_state = 0},
  [727] = {.lex_state = 0},
  [728] = {.lex_state = 0},
  [729] = {.lex_state = 0},
  [730] = {.lex_state = 0},
  [731] = {.lex_state = 0},
  [732] = {.lex_state = 0},
  [733] = {.lex_state = 0},
  [734] = {.lex_state = 0},
  [735] = {.lex_state = 0},
  [736] = {.lex_state = 0},
  [737] = {.lex_state = 0},
  [738] = {.lex_state = 0},
  [739] = {.lex_state = 0},
  [740] = {.lex_state = 0},
  [741] = {.lex_state = 180},
  [742] = {.lex_state = 180},
  [743] = {.lex_state = 10},
  [744] = {.lex_state = 0},
  [745] = {.lex_state = 0},
  [746] = {.lex_state = 10},
  [747] = {.lex_state = 0},
  [748] = {.lex_state = 0},
  [749] = {.lex_state = 0},
  [750] = {.lex_state = 0},
  [751] = {.lex_state = 0},
  [752] = {.lex_state = 0},
  [753] = {.lex_state = 0},
  [754] = {.lex_state = 0},
  [755] = {.lex_state = 0},
  [756] = {.lex_state = 0},
  [757] = {.lex_state = 0},
  [758] = {.lex_state = 0},
  [759] = {.lex_state = 0},
  [760] = {.lex_state = 0},
  [761] = {.lex_state = 0},
  [762] = {.lex_state = 0},
  [763] = {.lex_state = 0},
  [764] = {.lex_state = 0},
  [765] = {.lex_state = 0},
  [766] = {.lex_state = 0},
  [767] = {.lex_state = 0},
  [768] = {.lex_state = 0},
  [769] = {.lex_state = 0},
  [770] = {.lex_state = 0},
  [771] = {.lex_state = 0},
  [772] = {.lex_state = 0},
  [773] = {.lex_state = 0},
  [774] = {.lex_state = 0},
  [775] = {.lex_state = 0},
  [776] = {.lex_state = 0},
  [777] = {.lex_state = 0},
  [778] = {.lex_state = 0},
  [779] = {.lex_state = 0},
  [780] = {.lex_state = 0},
  [781] = {.lex_state = 14},
  [782] = {.lex_state = 0},
  [783] = {.lex_state = 14},
  [784] = {.lex_state = 0},
  [785] = {.lex_state = 0},
  [786] = {.lex_state = 0},
  [787] = {.lex_state = 0},
  [788] = {.lex_state = 10},
  [789] = {.lex_state = 0},
  [790] = {.lex_state = 18},
  [791] = {.lex_state = 0},
  [792] = {.lex_state = 10},
  [793] = {.lex_state = 0},
  [794] = {.lex_state = 0},
  [795] = {.lex_state = 0},
  [796] = {.lex_state = 14},
  [797] = {.lex_state = 0},
  [798] = {.lex_state = 0},
  [799] = {.lex_state = 0},
  [800] = {.lex_state = 0},
  [801] = {.lex_state = 0},
  [802] = {.lex_state = 0},
  [803] = {.lex_state = 0},
  [804] = {.lex_state = 10},
  [805] = {.lex_state = 0},
  [806] = {.lex_state = 0},
  [807] = {.lex_state = 0},
  [808] = {.lex_state = 0},
  [809] = {.lex_state = 0},
  [810] = {.lex_state = 0},
  [811] = {.lex_state = 0},
  [812] = {.lex_state = 0},
  [813] = {.lex_state = 0},
  [814] = {.lex_state = 0},
  [815] = {.lex_state = 16},
  [816] = {.lex_state = 16},
  [817] = {.lex_state = 0},
  [818] = {.lex_state = 14},
  [819] = {.lex_state = 0},
  [820] = {.lex_state = 0},
  [821] = {.lex_state = 0},
  [822] = {.lex_state = 0},
  [823] = {.lex_state = 14},
  [824] = {.lex_state = 0},
  [825] = {.lex_state = 0},
  [826] = {.lex_state = 0},
  [827] = {.lex_state = 0},
  [828] = {.lex_state = 0},
  [829] = {.lex_state = 0},
  [830] = {.lex_state = 0},
  [831] = {.lex_state = 0},
  [832] = {.lex_state = 16},
  [833] = {.lex_state = 17},
  [834] = {.lex_state = 0},
  [835] = {.lex_state = 0},
  [836] = {.lex_state = 10},
  [837] = {.lex_state = 10},
  [838] = {.lex_state = 0},
  [839] = {.lex_state = 0},
  [840] = {.lex_state = 0},
  [841] = {.lex_state = 0},
  [842] = {.lex_state = 0},
  [843] = {.lex_state = 0},
  [844] = {.lex_state = 0},
  [845] = {.lex_state = 0},
  [846] = {.lex_state = 0},
  [847] = {.lex_state = 0},
  [848] = {.lex_state = 0},
  [849] = {.lex_state = 0},
  [850] = {.lex_state = 16},
  [851] = {.lex_state = 0},
  [852] = {.lex_state = 16},
  [853] = {.lex_state = 0},
  [854] = {.lex_state = 0},
  [855] = {.lex_state = 17},
  [856] = {.lex_state = 0},
  [857] = {.lex_state = 0},
  [858] = {.lex_state = 0},
  [859] = {.lex_state = 0},
  [860] = {.lex_state = 16},
  [861] = {.lex_state = 0},
  [862] = {.lex_state = 0},
  [863] = {.lex_state = 17},
  [864] = {.lex_state = 0},
  [865] = {.lex_state = 0},
  [866] = {.lex_state = 0},
  [867] = {.lex_state = 0},
  [868] = {.lex_state = 17},
  [869] = {.lex_state = 0},
  [870] = {.lex_state = 0},
  [871] = {.lex_state = 0},
  [872] = {.lex_state = 0},
  [873] = {.lex_state = 0},
  [874] = {.lex_state = 0},
  [875] = {.lex_state = 0},
  [876] = {.lex_state = 0},
  [877] = {.lex_state = 0},
  [878] = {.lex_state = 0},
  [879] = {.lex_state = 0},
  [880] = {.lex_state = 0},
  [881] = {.lex_state = 0},
  [882] = {.lex_state = 0},
  [883] = {.lex_state = 889},
  [884] = {.lex_state = 0},
  [885] = {.lex_state = 0},
  [886] = {.lex_state = 0},
  [887] = {.lex_state = 0},
  [888] = {.lex_state = 0},
  [889] = {.lex_state = 0},
  [890] = {.lex_state = 0},
  [891] = {.lex_state = 0},
  [892] = {.lex_state = 0},
  [893] = {.lex_state = 0},
  [894] = {.lex_state = 0},
  [895] = {.lex_state = 0},
  [896] = {.lex_state = 0},
  [897] = {.lex_state = 0},
  [898] = {.lex_state = 0},
  [899] = {.lex_state = 0},
  [900] = {.lex_state = 0},
  [901] = {.lex_state = 0},
  [902] = {.lex_state = 0},
  [903] = {.lex_state = 0},
  [904] = {.lex_state = 16},
  [905] = {.lex_state = 10},
  [906] = {.lex_state = 0},
  [907] = {.lex_state = 0},
  [908] = {.lex_state = 0},
  [909] = {.lex_state = 0},
  [910] = {.lex_state = 0},
  [911] = {.lex_state = 0},
  [912] = {.lex_state = 0},
  [913] = {.lex_state = 17},
  [914] = {.lex_state = 0},
  [915] = {.lex_state = 0},
  [916] = {.lex_state = 17},
  [917] = {.lex_state = 17},
  [918] = {.lex_state = 0},
  [919] = {.lex_state = 17},
  [920] = {.lex_state = 17},
  [921] = {.lex_state = 0},
  [922] = {.lex_state = 0},
  [923] = {.lex_state = 0},
  [924] = {.lex_state = 0},
  [925] = {.lex_state = 0},
  [926] = {.lex_state = 0},
  [927] = {.lex_state = 0},
  [928] = {.lex_state = 0},
  [929] = {.lex_state = 10},
  [930] = {.lex_state = 0},
  [931] = {.lex_state = 0},
  [932] = {.lex_state = 0},
  [933] = {.lex_state = 0},
  [934] = {.lex_state = 0},
  [935] = {.lex_state = 0},
  [936] = {.lex_state = 0},
  [937] = {.lex_state = 0},
  [938] = {.lex_state = 0},
  [939] = {.lex_state = 0},
  [940] = {.lex_state = 0},
  [941] = {.lex_state = 0},
  [942] = {.lex_state = 0},
  [943] = {.lex_state = 16},
  [944] = {.lex_state = 0},
  [945] = {.lex_state = 0},
  [946] = {.lex_state = 0},
  [947] = {.lex_state = 0},
  [948] = {.lex_state = 0},
  [949] = {.lex_state = 0},
  [950] = {.lex_state = 0},
  [951] = {.lex_state = 0},
  [952] = {.lex_state = 0},
  [953] = {.lex_state = 0},
  [954] = {.lex_state = 0},
  [955] = {.lex_state = 0},
  [956] = {.lex_state = 0},
  [957] = {.lex_state = 0},
  [958] = {.lex_state = 0},
  [959] = {.lex_state = 0},
  [960] = {.lex_state = 0},
  [961] = {.lex_state = 0},
  [962] = {.lex_state = 10},
  [963] = {.lex_state = 0},
  [964] = {.lex_state = 0},
  [965] = {.lex_state = 0},
  [966] = {.lex_state = 0},
  [967] = {.lex_state = 0},
  [968] = {.lex_state = 0},
  [969] = {.lex_state = 0},
  [970] = {.lex_state = 0},
  [971] = {.lex_state = 0},
  [972] = {.lex_state = 0},
  [973] = {.lex_state = 10},
  [974] = {.lex_state = 0},
  [975] = {.lex_state = 0},
  [976] = {.lex_state = 0},
  [977] = {.lex_state = 0},
  [978] = {.lex_state = 0},
  [979] = {.lex_state = 4},
  [980] = {.lex_state = 0},
  [981] = {.lex_state = 0},
  [982] = {.lex_state = 0},
  [983] = {.lex_state = 0},
  [984] = {.lex_state = 0},
  [985] = {.lex_state = 0},
  [986] = {.lex_state = 0},
  [987] = {.lex_state = 0},
  [988] = {.lex_state = 0},
  [989] = {.lex_state = 0},
  [990] = {.lex_state = 0},
  [991] = {.lex_state = 0},
  [992] = {.lex_state = 0},
  [993] = {.lex_state = 0},
  [994] = {.lex_state = 0},
  [995] = {.lex_state = 0},
  [996] = {.lex_state = 0},
  [997] = {.lex_state = 0},
  [998] = {.lex_state = 0},
  [999] = {.lex_state = 0},
  [1000] = {.lex_state = 0},
  [1001] = {.lex_state = 0},
  [1002] = {.lex_state = 0},
  [1003] = {.lex_state = 0},
  [1004] = {.lex_state = 0},
  [1005] = {.lex_state = 0},
  [1006] = {.lex_state = 0},
  [1007] = {.lex_state = 0},
  [1008] = {.lex_state = 17},
  [1009] = {.lex_state = 10},
  [1010] = {.lex_state = 10},
  [1011] = {.lex_state = 0},
  [1012] = {.lex_state = 0},
  [1013] = {.lex_state = 0},
  [1014] = {.lex_state = 17},
  [1015] = {.lex_state = 0},
  [1016] = {.lex_state = 0},
  [1017] = {.lex_state = 0},
  [1018] = {.lex_state = 0},
  [1019] = {.lex_state = 0},
  [1020] = {.lex_state = 0},
  [1021] = {.lex_state = 0},
  [1022] = {.lex_state = 0},
  [1023] = {.lex_state = 0},
  [1024] = {.lex_state = 0},
  [1025] = {.lex_state = 0},
  [1026] = {.lex_state = 0},
  [1027] = {.lex_state = 0},
  [1028] = {.lex_state = 0},
  [1029] = {.lex_state = 0},
  [1030] = {.lex_state = 0},
  [1031] = {.lex_state = 0},
  [1032] = {.lex_state = 0},
  [1033] = {.lex_state = 0},
  [1034] = {.lex_state = 0},
  [1035] = {.lex_state = 0},
  [1036] = {.lex_state = 0},
  [1037] = {.lex_state = 0},
  [1038] = {.lex_state = 0},
  [1039] = {.lex_state = 0},
  [1040] = {.lex_state = 0},
  [1041] = {.lex_state = 0},
  [1042] = {.lex_state = 0},
  [1043] = {.lex_state = 0},
  [1044] = {.lex_state = 10},
  [1045] = {.lex_state = 10},
  [1046] = {.lex_state = 0},
  [1047] = {.lex_state = 0},
  [1048] = {.lex_state = 0},
  [1049] = {.lex_state = 0},
  [1050] = {.lex_state = 0},
  [1051] = {.lex_state = 0},
  [1052] = {.lex_state = 16},
  [1053] = {.lex_state = 0},
  [1054] = {.lex_state = 4},
  [1055] = {.lex_state = 0},
  [1056] = {.lex_state = 0},
  [1057] = {.lex_state = 0},
  [1058] = {.lex_state = 0},
  [1059] = {.lex_state = 0},
  [1060] = {.lex_state = 0},
  [1061] = {.lex_state = 0},
  [1062] = {.lex_state = 0},
  [1063] = {.lex_state = 0},
  [1064] = {.lex_state = 0},
  [1065] = {.lex_state = 0},
  [1066] = {.lex_state = 0},
  [1067] = {.lex_state = 0},
  [1068] = {.lex_state = 0},
  [1069] = {.lex_state = 0},
  [1070] = {.lex_state = 0},
  [1071] = {.lex_state = 0},
  [1072] = {.lex_state = 0},
  [1073] = {.lex_state = 0},
  [1074] = {.lex_state = 0},
  [1075] = {.lex_state = 0},
  [1076] = {.lex_state = 0},
  [1077] = {.lex_state = 0},
  [1078] = {.lex_state = 4},
  [1079] = {.lex_state = 0},
  [1080] = {.lex_state = 0},
  [1081] = {.lex_state = 0},
  [1082] = {.lex_state = 0},
  [1083] = {.lex_state = 0},
  [1084] = {.lex_state = 0},
  [1085] = {.lex_state = 0},
  [1086] = {.lex_state = 0},
  [1087] = {.lex_state = 0},
  [1088] = {.lex_state = 0},
  [1089] = {.lex_state = 0},
  [1090] = {.lex_state = 0},
  [1091] = {.lex_state = 0},
  [1092] = {.lex_state = 0},
  [1093] = {.lex_state = 0},
  [1094] = {.lex_state = 0},
  [1095] = {.lex_state = 0},
  [1096] = {.lex_state = 0},
  [1097] = {.lex_state = 0},
  [1098] = {.lex_state = 0},
  [1099] = {.lex_state = 0},
  [1100] = {.lex_state = 4},
  [1101] = {.lex_state = 0},
  [1102] = {.lex_state = 0},
  [1103] = {.lex_state = 0},
  [1104] = {.lex_state = 0},
  [1105] = {.lex_state = 0},
  [1106] = {.lex_state = 0},
  [1107] = {.lex_state = 0},
  [1108] = {.lex_state = 0},
  [1109] = {.lex_state = 0},
  [1110] = {.lex_state = 0},
  [1111] = {.lex_state = 0},
  [1112] = {.lex_state = 0},
  [1113] = {.lex_state = 0},
  [1114] = {.lex_state = 0},
  [1115] = {.lex_state = 0},
  [1116] = {.lex_state = 0},
  [1117] = {.lex_state = 0},
  [1118] = {.lex_state = 0},
  [1119] = {.lex_state = 0},
  [1120] = {.lex_state = 0},
  [1121] = {.lex_state = 0},
  [1122] = {.lex_state = 16},
  [1123] = {.lex_state = 0},
  [1124] = {.lex_state = 0},
  [1125] = {.lex_state = 0},
  [1126] = {.lex_state = 0},
  [1127] = {.lex_state = 0},
  [1128] = {.lex_state = 0},
  [1129] = {.lex_state = 0},
  [1130] = {.lex_state = 16},
  [1131] = {.lex_state = 17},
  [1132] = {.lex_state = 0},
  [1133] = {.lex_state = 0},
  [1134] = {.lex_state = 0},
  [1135] = {.lex_state = 0},
  [1136] = {.lex_state = 0},
  [1137] = {.lex_state = 0},
  [1138] = {.lex_state = 0},
  [1139] = {.lex_state = 0},
  [1140] = {.lex_state = 0},
  [1141] = {.lex_state = 0},
  [1142] = {.lex_state = 17},
  [1143] = {.lex_state = 0},
  [1144] = {.lex_state = 0},
  [1145] = {.lex_state = 0},
  [1146] = {.lex_state = 0},
  [1147] = {.lex_state = 0},
  [1148] = {.lex_state = 10},
  [1149] = {.lex_state = 17},
  [1150] = {.lex_state = 0},
  [1151] = {.lex_state = 0},
  [1152] = {.lex_state = 0},
  [1153] = {.lex_state = 0},
  [1154] = {.lex_state = 0},
  [1155] = {.lex_state = 0},
  [1156] = {.lex_state = 0},
  [1157] = {.lex_state = 0},
  [1158] = {.lex_state = 14},
};

static const uint16_t ts_parse_table[LARGE_STATE_COUNT][SYMBOL_COUNT] = {
  [0] = {
    [ts_builtin_sym_end] = ACTIONS(1),
    [anon_sym_table] = ACTIONS(1),
    [anon_sym_LBRACE] = ACTIONS(1),
    [anon_sym_RBRACE] = ACTIONS(1),
    [anon_sym_codeunit] = ACTIONS(1),
    [anon_sym_Install] = ACTIONS(1),
    [anon_sym_Upgrade] = ACTIONS(1),
    [anon_sym_Test] = ACTIONS(1),
    [anon_sym_FlowField] = ACTIONS(1),
    [anon_sym_FlowFilter] = ACTIONS(1),
    [anon_sym_Normal] = ACTIONS(1),
    [anon_sym_COMMA] = ACTIONS(1),
    [anon_sym_Temporary] = ACTIONS(1),
    [anon_sym_External] = ACTIONS(1),
    [anon_sym_System] = ACTIONS(1),
    [anon_sym_TableType] = ACTIONS(1),
    [anon_sym_EQ] = ACTIONS(1),
    [anon_sym_SEMI] = ACTIONS(1),
    [anon_sym_CustomerContent] = ACTIONS(1),
    [anon_sym_EndUserIdentifiableInformation] = ACTIONS(1),
    [anon_sym_AccountData] = ACTIONS(1),
    [anon_sym_EndUserPseudonymousIdentifiers] = ACTIONS(1),
    [anon_sym_OrganizationIdentifiableInformation] = ACTIONS(1),
    [anon_sym_SystemMetadata] = ACTIONS(1),
    [anon_sym_ToBeClassified] = ACTIONS(1),
    [anon_sym_trigger] = ACTIONS(1),
    [anon_sym_OnRun] = ACTIONS(1),
    [anon_sym_Permissions] = ACTIONS(1),
    [sym_permission_type] = ACTIONS(1),
    [anon_sym_OnInsert] = ACTIONS(1),
    [anon_sym_OnModify] = ACTIONS(1),
    [anon_sym_OnDelete] = ACTIONS(1),
    [anon_sym_OnRename] = ACTIONS(1),
    [anon_sym_OnValidate] = ACTIONS(1),
    [anon_sym_OnAfterGetRecord] = ACTIONS(1),
    [anon_sym_OnAfterInsertEvent] = ACTIONS(1),
    [anon_sym_OnAfterModifyEvent] = ACTIONS(1),
    [anon_sym_OnAfterDeleteEvent] = ACTIONS(1),
    [anon_sym_OnBeforeInsertEvent] = ACTIONS(1),
    [anon_sym_OnBeforeModifyEvent] = ACTIONS(1),
    [anon_sym_OnBeforeDeleteEvent] = ACTIONS(1),
    [anon_sym_DOT] = ACTIONS(1),
    [anon_sym_TableNo] = ACTIONS(1),
    [anon_sym_Subtype] = ACTIONS(1),
    [anon_sym_SingleInstance] = ACTIONS(1),
    [anon_sym_DrillDownPageId] = ACTIONS(1),
    [anon_sym_LookupPageId] = ACTIONS(1),
    [anon_sym_TableRelation] = ACTIONS(1),
    [anon_sym_FieldClass] = ACTIONS(1),
    [anon_sym_CalcFormula] = ACTIONS(1),
    [anon_sym_BlankZero] = ACTIONS(1),
    [anon_sym_Editable] = ACTIONS(1),
    [anon_sym_OptionMembers] = ACTIONS(1),
    [anon_sym_OptionCaption] = ACTIONS(1),
    [anon_sym_DataClassification] = ACTIONS(1),
    [anon_sym_Caption] = ACTIONS(1),
    [anon_sym_tabledata] = ACTIONS(1),
    [anon_sym_DecimalPlaces] = ACTIONS(1),
    [anon_sym_COLON] = ACTIONS(1),
    [anon_sym_var] = ACTIONS(1),
    [anon_sym_List] = ACTIONS(1),
    [anon_sym_of] = ACTIONS(1),
    [anon_sym_LBRACK] = ACTIONS(1),
    [anon_sym_RBRACK] = ACTIONS(1),
    [anon_sym_Dictionary] = ACTIONS(1),
    [anon_sym_Integer] = ACTIONS(1),
    [anon_sym_BigInteger] = ACTIONS(1),
    [anon_sym_Decimal] = ACTIONS(1),
    [anon_sym_Byte] = ACTIONS(1),
    [anon_sym_Char] = ACTIONS(1),
    [anon_sym_Date] = ACTIONS(1),
    [anon_sym_Time] = ACTIONS(1),
    [anon_sym_DateTime] = ACTIONS(1),
    [anon_sym_Duration] = ACTIONS(1),
    [anon_sym_DateFormula] = ACTIONS(1),
    [anon_sym_Boolean] = ACTIONS(1),
    [anon_sym_Option] = ACTIONS(1),
    [anon_sym_Guid] = ACTIONS(1),
    [anon_sym_RecordId] = ACTIONS(1),
    [anon_sym_Variant] = ACTIONS(1),
    [anon_sym_Dialog] = ACTIONS(1),
    [anon_sym_Action] = ACTIONS(1),
    [anon_sym_Blob] = ACTIONS(1),
    [anon_sym_FilterPageBuilder] = ACTIONS(1),
    [anon_sym_JsonToken] = ACTIONS(1),
    [anon_sym_JsonValue] = ACTIONS(1),
    [anon_sym_JsonArray] = ACTIONS(1),
    [anon_sym_JsonObject] = ACTIONS(1),
    [anon_sym_Media] = ACTIONS(1),
    [anon_sym_MediaSet] = ACTIONS(1),
    [anon_sym_OStream] = ACTIONS(1),
    [anon_sym_InStream] = ACTIONS(1),
    [anon_sym_OutStream] = ACTIONS(1),
    [anon_sym_SecretText] = ACTIONS(1),
    [anon_sym_Label] = ACTIONS(1),
    [anon_sym_Text] = ACTIONS(1),
    [anon_sym_Code] = ACTIONS(1),
    [anon_sym_Record] = ACTIONS(1),
    [anon_sym_Codeunit] = ACTIONS(1),
    [anon_sym_Query] = ACTIONS(1),
    [anon_sym_DotNet] = ACTIONS(1),
    [anon_sym_array] = ACTIONS(1),
    [anon_sym_fields] = ACTIONS(1),
    [anon_sym_field] = ACTIONS(1),
    [anon_sym_LPAREN] = ACTIONS(1),
    [anon_sym_RPAREN] = ACTIONS(1),
    [anon_sym_where] = ACTIONS(1),
    [anon_sym_if] = ACTIONS(1),
    [anon_sym_else] = ACTIONS(1),
    [anon_sym_const] = ACTIONS(1),
    [anon_sym_filter] = ACTIONS(1),
    [anon_sym_lookup] = ACTIONS(1),
    [anon_sym_count] = ACTIONS(1),
    [anon_sym_sum] = ACTIONS(1),
    [anon_sym_average] = ACTIONS(1),
    [anon_sym_min] = ACTIONS(1),
    [anon_sym_max] = ACTIONS(1),
    [anon_sym_CONST] = ACTIONS(1),
    [anon_sym_FILTER] = ACTIONS(1),
    [anon_sym_FIELD] = ACTIONS(1),
    [anon_sym_UPPERLIMIT] = ACTIONS(1),
    [anon_sym_LT_GT] = ACTIONS(1),
    [anon_sym_LT_EQ] = ACTIONS(1),
    [anon_sym_GT_EQ] = ACTIONS(1),
    [anon_sym_LT] = ACTIONS(1),
    [anon_sym_GT] = ACTIONS(1),
    [anon_sym_IN] = ACTIONS(1),
    [anon_sym_OnLookup] = ACTIONS(1),
    [anon_sym_OnAssistEdit] = ACTIONS(1),
    [anon_sym_OnDrillDown] = ACTIONS(1),
    [anon_sym_keys] = ACTIONS(1),
    [anon_sym_key] = ACTIONS(1),
    [sym_procedure_modifier] = ACTIONS(1),
    [anon_sym_procedure] = ACTIONS(1),
    [anon_sym_PLUS] = ACTIONS(1),
    [anon_sym_DASH] = ACTIONS(1),
    [anon_sym_STAR] = ACTIONS(1),
    [anon_sym_SLASH] = ACTIONS(1),
    [anon_sym_DQUOTE] = ACTIONS(1),
    [aux_sym__quoted_identifier_token2] = ACTIONS(1),
    [aux_sym__quoted_identifier_token3] = ACTIONS(1),
    [sym_integer] = ACTIONS(1),
    [sym_string_literal] = ACTIONS(1),
    [anon_sym_Clustered] = ACTIONS(1),
    [anon_sym_true] = ACTIONS(1),
    [anon_sym_false] = ACTIONS(1),
    [sym_temporary] = ACTIONS(1),
    [anon_sym_Enum] = ACTIONS(1),
    [anon_sym_begin] = ACTIONS(1),
    [anon_sym_end] = ACTIONS(1),
    [anon_sym_repeat] = ACTIONS(1),
    [anon_sym_until] = ACTIONS(1),
    [anon_sym_COLON_EQ] = ACTIONS(1),
    [anon_sym_COLON_COLON] = ACTIONS(1),
    [anon_sym_Get] = ACTIONS(1),
    [anon_sym_FindSet] = ACTIONS(1),
    [anon_sym_Insert] = ACTIONS(1),
    [anon_sym_Modify] = ACTIONS(1),
    [anon_sym_Delete] = ACTIONS(1),
    [anon_sym_SetRange] = ACTIONS(1),
    [anon_sym_SetFilter] = ACTIONS(1),
    [anon_sym_Reset] = ACTIONS(1),
    [anon_sym_then] = ACTIONS(1),
    [anon_sym_FindFirst] = ACTIONS(1),
    [anon_sym_FindLast] = ACTIONS(1),
    [anon_sym_Next] = ACTIONS(1),
    [anon_sym_case] = ACTIONS(1),
    [anon_sym_exit] = ACTIONS(1),
  },
  [1] = {
    [sym_source_file] = STATE(1040),
    [sym__object] = STATE(491),
    [sym_table_declaration] = STATE(491),
    [sym_codeunit_declaration] = STATE(491),
    [aux_sym_source_file_repeat1] = STATE(491),
    [ts_builtin_sym_end] = ACTIONS(3),
    [anon_sym_table] = ACTIONS(5),
    [anon_sym_codeunit] = ACTIONS(7),
  },
};

static const uint16_t ts_small_parse_table[] = {
  [0] = 12,
    ACTIONS(9), 1,
      anon_sym_List,
    ACTIONS(11), 1,
      anon_sym_Dictionary,
    ACTIONS(15), 1,
      anon_sym_Text,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(19), 1,
      anon_sym_Codeunit,
    ACTIONS(21), 1,
      anon_sym_Query,
    ACTIONS(23), 1,
      anon_sym_DotNet,
    ACTIONS(25), 1,
      anon_sym_array,
    ACTIONS(27), 1,
      sym_identifier,
    STATE(801), 1,
      sym_return_type,
    STATE(800), 9,
      sym_list_type,
      sym_dictionary_type,
      sym_basic_type,
      sym_text_type,
      sym_record_type,
      sym_codeunit_type,
      sym_query_type,
      sym_dotnet_type,
      sym_array_type,
    ACTIONS(13), 30,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Date,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_Media,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [74] = 12,
    ACTIONS(9), 1,
      anon_sym_List,
    ACTIONS(11), 1,
      anon_sym_Dictionary,
    ACTIONS(15), 1,
      anon_sym_Text,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(19), 1,
      anon_sym_Codeunit,
    ACTIONS(21), 1,
      anon_sym_Query,
    ACTIONS(23), 1,
      anon_sym_DotNet,
    ACTIONS(25), 1,
      anon_sym_array,
    ACTIONS(27), 1,
      sym_identifier,
    STATE(719), 1,
      sym_return_type,
    STATE(800), 9,
      sym_list_type,
      sym_dictionary_type,
      sym_basic_type,
      sym_text_type,
      sym_record_type,
      sym_codeunit_type,
      sym_query_type,
      sym_dotnet_type,
      sym_array_type,
    ACTIONS(13), 30,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Date,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_Media,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [148] = 12,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(29), 1,
      anon_sym_List,
    ACTIONS(31), 1,
      anon_sym_Dictionary,
    ACTIONS(35), 1,
      anon_sym_Text,
    ACTIONS(37), 1,
      anon_sym_Codeunit,
    ACTIONS(39), 1,
      anon_sym_Query,
    ACTIONS(41), 1,
      anon_sym_DotNet,
    ACTIONS(43), 1,
      anon_sym_array,
    STATE(819), 1,
      sym_type_specification,
    ACTIONS(13), 2,
      anon_sym_Date,
      anon_sym_Media,
    STATE(486), 9,
      sym_list_type,
      sym_dictionary_type,
      sym_basic_type,
      sym_text_type,
      sym_record_type,
      sym_codeunit_type,
      sym_query_type,
      sym_dotnet_type,
      sym_array_type,
    ACTIONS(33), 28,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [221] = 12,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(29), 1,
      anon_sym_List,
    ACTIONS(31), 1,
      anon_sym_Dictionary,
    ACTIONS(35), 1,
      anon_sym_Text,
    ACTIONS(37), 1,
      anon_sym_Codeunit,
    ACTIONS(39), 1,
      anon_sym_Query,
    ACTIONS(41), 1,
      anon_sym_DotNet,
    ACTIONS(43), 1,
      anon_sym_array,
    STATE(1035), 1,
      sym_type_specification,
    ACTIONS(13), 2,
      anon_sym_Date,
      anon_sym_Media,
    STATE(486), 9,
      sym_list_type,
      sym_dictionary_type,
      sym_basic_type,
      sym_text_type,
      sym_record_type,
      sym_codeunit_type,
      sym_query_type,
      sym_dotnet_type,
      sym_array_type,
    ACTIONS(33), 28,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [294] = 12,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(29), 1,
      anon_sym_List,
    ACTIONS(31), 1,
      anon_sym_Dictionary,
    ACTIONS(35), 1,
      anon_sym_Text,
    ACTIONS(37), 1,
      anon_sym_Codeunit,
    ACTIONS(39), 1,
      anon_sym_Query,
    ACTIONS(41), 1,
      anon_sym_DotNet,
    ACTIONS(43), 1,
      anon_sym_array,
    STATE(898), 1,
      sym_type_specification,
    ACTIONS(13), 2,
      anon_sym_Date,
      anon_sym_Media,
    STATE(486), 9,
      sym_list_type,
      sym_dictionary_type,
      sym_basic_type,
      sym_text_type,
      sym_record_type,
      sym_codeunit_type,
      sym_query_type,
      sym_dotnet_type,
      sym_array_type,
    ACTIONS(33), 28,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [367] = 12,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(29), 1,
      anon_sym_List,
    ACTIONS(31), 1,
      anon_sym_Dictionary,
    ACTIONS(35), 1,
      anon_sym_Text,
    ACTIONS(37), 1,
      anon_sym_Codeunit,
    ACTIONS(39), 1,
      anon_sym_Query,
    ACTIONS(41), 1,
      anon_sym_DotNet,
    ACTIONS(43), 1,
      anon_sym_array,
    STATE(487), 1,
      sym_type_specification,
    ACTIONS(13), 2,
      anon_sym_Date,
      anon_sym_Media,
    STATE(486), 9,
      sym_list_type,
      sym_dictionary_type,
      sym_basic_type,
      sym_text_type,
      sym_record_type,
      sym_codeunit_type,
      sym_query_type,
      sym_dotnet_type,
      sym_array_type,
    ACTIONS(33), 28,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [440] = 12,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(29), 1,
      anon_sym_List,
    ACTIONS(31), 1,
      anon_sym_Dictionary,
    ACTIONS(35), 1,
      anon_sym_Text,
    ACTIONS(37), 1,
      anon_sym_Codeunit,
    ACTIONS(39), 1,
      anon_sym_Query,
    ACTIONS(41), 1,
      anon_sym_DotNet,
    ACTIONS(43), 1,
      anon_sym_array,
    STATE(1048), 1,
      sym_type_specification,
    ACTIONS(13), 2,
      anon_sym_Date,
      anon_sym_Media,
    STATE(486), 9,
      sym_list_type,
      sym_dictionary_type,
      sym_basic_type,
      sym_text_type,
      sym_record_type,
      sym_codeunit_type,
      sym_query_type,
      sym_dotnet_type,
      sym_array_type,
    ACTIONS(33), 28,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [513] = 12,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(29), 1,
      anon_sym_List,
    ACTIONS(31), 1,
      anon_sym_Dictionary,
    ACTIONS(35), 1,
      anon_sym_Text,
    ACTIONS(37), 1,
      anon_sym_Codeunit,
    ACTIONS(39), 1,
      anon_sym_Query,
    ACTIONS(41), 1,
      anon_sym_DotNet,
    ACTIONS(43), 1,
      anon_sym_array,
    STATE(829), 1,
      sym_type_specification,
    ACTIONS(13), 2,
      anon_sym_Date,
      anon_sym_Media,
    STATE(486), 9,
      sym_list_type,
      sym_dictionary_type,
      sym_basic_type,
      sym_text_type,
      sym_record_type,
      sym_codeunit_type,
      sym_query_type,
      sym_dotnet_type,
      sym_array_type,
    ACTIONS(33), 28,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [586] = 12,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(29), 1,
      anon_sym_List,
    ACTIONS(31), 1,
      anon_sym_Dictionary,
    ACTIONS(35), 1,
      anon_sym_Text,
    ACTIONS(37), 1,
      anon_sym_Codeunit,
    ACTIONS(39), 1,
      anon_sym_Query,
    ACTIONS(41), 1,
      anon_sym_DotNet,
    ACTIONS(43), 1,
      anon_sym_array,
    STATE(789), 1,
      sym_type_specification,
    ACTIONS(13), 2,
      anon_sym_Date,
      anon_sym_Media,
    STATE(486), 9,
      sym_list_type,
      sym_dictionary_type,
      sym_basic_type,
      sym_text_type,
      sym_record_type,
      sym_codeunit_type,
      sym_query_type,
      sym_dotnet_type,
      sym_array_type,
    ACTIONS(33), 28,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [659] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(47), 1,
      anon_sym_if,
    ACTIONS(49), 1,
      sym_identifier,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(57), 1,
      anon_sym_begin,
    ACTIONS(59), 1,
      anon_sym_repeat,
    ACTIONS(61), 1,
      anon_sym_case,
    ACTIONS(63), 1,
      anon_sym_exit,
    STATE(286), 1,
      sym_get_method,
    STATE(287), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1100), 1,
      sym__assignable_expression,
    ACTIONS(53), 2,
      sym_integer,
      sym_string_literal,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(80), 2,
      sym_function_call,
      sym_method_call,
    STATE(301), 2,
      sym_code_block,
      sym__statement,
    STATE(452), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(285), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [739] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(65), 1,
      anon_sym_if,
    ACTIONS(67), 1,
      sym_identifier,
    ACTIONS(71), 1,
      anon_sym_begin,
    ACTIONS(73), 1,
      anon_sym_repeat,
    ACTIONS(75), 1,
      anon_sym_case,
    ACTIONS(77), 1,
      anon_sym_exit,
    STATE(251), 1,
      sym_get_method,
    STATE(252), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1078), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(69), 2,
      sym_integer,
      sym_string_literal,
    STATE(76), 2,
      sym_function_call,
      sym_method_call,
    STATE(190), 2,
      sym_code_block,
      sym__statement,
    STATE(442), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(250), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [819] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(79), 1,
      anon_sym_if,
    ACTIONS(81), 1,
      sym_identifier,
    ACTIONS(85), 1,
      anon_sym_repeat,
    ACTIONS(87), 1,
      anon_sym_until,
    ACTIONS(89), 1,
      anon_sym_case,
    ACTIONS(91), 1,
      anon_sym_exit,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(83), 2,
      sym_integer,
      sym_string_literal,
    STATE(17), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [899] = 18,
    ACTIONS(93), 1,
      anon_sym_LPAREN,
    ACTIONS(96), 1,
      anon_sym_if,
    ACTIONS(99), 1,
      sym_identifier,
    ACTIONS(102), 1,
      anon_sym_DQUOTE,
    ACTIONS(111), 1,
      anon_sym_end,
    ACTIONS(113), 1,
      anon_sym_repeat,
    ACTIONS(116), 1,
      anon_sym_case,
    ACTIONS(119), 1,
      anon_sym_exit,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(105), 2,
      sym_integer,
      sym_string_literal,
    ACTIONS(108), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(14), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [979] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(128), 1,
      anon_sym_begin,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(346), 2,
      sym_code_block,
      sym__statement,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1059] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(47), 1,
      anon_sym_if,
    ACTIONS(49), 1,
      sym_identifier,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(57), 1,
      anon_sym_begin,
    ACTIONS(59), 1,
      anon_sym_repeat,
    ACTIONS(61), 1,
      anon_sym_case,
    ACTIONS(63), 1,
      anon_sym_exit,
    STATE(286), 1,
      sym_get_method,
    STATE(287), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1100), 1,
      sym__assignable_expression,
    ACTIONS(53), 2,
      sym_integer,
      sym_string_literal,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(80), 2,
      sym_function_call,
      sym_method_call,
    STATE(245), 2,
      sym_code_block,
      sym__statement,
    STATE(452), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(285), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1139] = 18,
    ACTIONS(93), 1,
      anon_sym_LPAREN,
    ACTIONS(102), 1,
      anon_sym_DQUOTE,
    ACTIONS(111), 1,
      anon_sym_until,
    ACTIONS(136), 1,
      anon_sym_if,
    ACTIONS(139), 1,
      sym_identifier,
    ACTIONS(145), 1,
      anon_sym_repeat,
    ACTIONS(148), 1,
      anon_sym_case,
    ACTIONS(151), 1,
      anon_sym_exit,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(108), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(142), 2,
      sym_integer,
      sym_string_literal,
    STATE(17), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1219] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(79), 1,
      anon_sym_if,
    ACTIONS(81), 1,
      sym_identifier,
    ACTIONS(85), 1,
      anon_sym_repeat,
    ACTIONS(89), 1,
      anon_sym_case,
    ACTIONS(91), 1,
      anon_sym_exit,
    ACTIONS(154), 1,
      anon_sym_begin,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(83), 2,
      sym_integer,
      sym_string_literal,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(331), 2,
      sym_code_block,
      sym__statement,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1299] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(65), 1,
      anon_sym_if,
    ACTIONS(67), 1,
      sym_identifier,
    ACTIONS(71), 1,
      anon_sym_begin,
    ACTIONS(73), 1,
      anon_sym_repeat,
    ACTIONS(75), 1,
      anon_sym_case,
    ACTIONS(77), 1,
      anon_sym_exit,
    STATE(251), 1,
      sym_get_method,
    STATE(252), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1078), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(69), 2,
      sym_integer,
      sym_string_literal,
    STATE(76), 2,
      sym_function_call,
      sym_method_call,
    STATE(271), 2,
      sym_code_block,
      sym__statement,
    STATE(442), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(250), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1379] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(156), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(14), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1459] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(158), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(20), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1539] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(160), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(23), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1619] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(162), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(14), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1699] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(47), 1,
      anon_sym_if,
    ACTIONS(49), 1,
      sym_identifier,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(57), 1,
      anon_sym_begin,
    ACTIONS(59), 1,
      anon_sym_repeat,
    ACTIONS(61), 1,
      anon_sym_case,
    ACTIONS(63), 1,
      anon_sym_exit,
    STATE(286), 1,
      sym_get_method,
    STATE(287), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1100), 1,
      sym__assignable_expression,
    ACTIONS(53), 2,
      sym_integer,
      sym_string_literal,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(80), 2,
      sym_function_call,
      sym_method_call,
    STATE(315), 2,
      sym_code_block,
      sym__statement,
    STATE(452), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(285), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1779] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(164), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(26), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1859] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(166), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(14), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [1939] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(168), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(28), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2019] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(170), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(14), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2099] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(172), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(30), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2179] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(174), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(14), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2259] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(176), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(14), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2339] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(79), 1,
      anon_sym_if,
    ACTIONS(81), 1,
      sym_identifier,
    ACTIONS(85), 1,
      anon_sym_repeat,
    ACTIONS(89), 1,
      anon_sym_case,
    ACTIONS(91), 1,
      anon_sym_exit,
    ACTIONS(178), 1,
      anon_sym_until,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(83), 2,
      sym_integer,
      sym_string_literal,
    STATE(17), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2419] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(65), 1,
      anon_sym_if,
    ACTIONS(67), 1,
      sym_identifier,
    ACTIONS(71), 1,
      anon_sym_begin,
    ACTIONS(73), 1,
      anon_sym_repeat,
    ACTIONS(75), 1,
      anon_sym_case,
    ACTIONS(77), 1,
      anon_sym_exit,
    STATE(251), 1,
      sym_get_method,
    STATE(252), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1078), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(69), 2,
      sym_integer,
      sym_string_literal,
    STATE(76), 2,
      sym_function_call,
      sym_method_call,
    STATE(314), 2,
      sym_code_block,
      sym__statement,
    STATE(442), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(250), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2499] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(122), 1,
      anon_sym_if,
    ACTIONS(124), 1,
      sym_identifier,
    ACTIONS(130), 1,
      anon_sym_repeat,
    ACTIONS(132), 1,
      anon_sym_case,
    ACTIONS(134), 1,
      anon_sym_exit,
    ACTIONS(180), 1,
      anon_sym_end,
    STATE(384), 1,
      sym_get_method,
    STATE(385), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(979), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(126), 2,
      sym_integer,
      sym_string_literal,
    STATE(31), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(104), 2,
      sym_function_call,
      sym_method_call,
    STATE(447), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(383), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2579] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(79), 1,
      anon_sym_if,
    ACTIONS(81), 1,
      sym_identifier,
    ACTIONS(85), 1,
      anon_sym_repeat,
    ACTIONS(89), 1,
      anon_sym_case,
    ACTIONS(91), 1,
      anon_sym_exit,
    ACTIONS(182), 1,
      anon_sym_until,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(83), 2,
      sym_integer,
      sym_string_literal,
    STATE(17), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2659] = 18,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(79), 1,
      anon_sym_if,
    ACTIONS(81), 1,
      sym_identifier,
    ACTIONS(85), 1,
      anon_sym_repeat,
    ACTIONS(89), 1,
      anon_sym_case,
    ACTIONS(91), 1,
      anon_sym_exit,
    ACTIONS(184), 1,
      anon_sym_until,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(83), 2,
      sym_integer,
      sym_string_literal,
    STATE(17), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2739] = 17,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(79), 1,
      anon_sym_if,
    ACTIONS(81), 1,
      sym_identifier,
    ACTIONS(85), 1,
      anon_sym_repeat,
    ACTIONS(89), 1,
      anon_sym_case,
    ACTIONS(91), 1,
      anon_sym_exit,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(83), 2,
      sym_integer,
      sym_string_literal,
    STATE(36), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2816] = 17,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(79), 1,
      anon_sym_if,
    ACTIONS(81), 1,
      sym_identifier,
    ACTIONS(85), 1,
      anon_sym_repeat,
    ACTIONS(89), 1,
      anon_sym_case,
    ACTIONS(91), 1,
      anon_sym_exit,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(83), 2,
      sym_integer,
      sym_string_literal,
    STATE(13), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2893] = 17,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(79), 1,
      anon_sym_if,
    ACTIONS(81), 1,
      sym_identifier,
    ACTIONS(85), 1,
      anon_sym_repeat,
    ACTIONS(89), 1,
      anon_sym_case,
    ACTIONS(91), 1,
      anon_sym_exit,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(83), 2,
      sym_integer,
      sym_string_literal,
    STATE(32), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [2970] = 17,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(79), 1,
      anon_sym_if,
    ACTIONS(81), 1,
      sym_identifier,
    ACTIONS(85), 1,
      anon_sym_repeat,
    ACTIONS(89), 1,
      anon_sym_case,
    ACTIONS(91), 1,
      anon_sym_exit,
    STATE(373), 1,
      sym_get_method,
    STATE(374), 1,
      sym_find_set_method,
    STATE(454), 1,
      sym_member_access,
    STATE(1054), 1,
      sym__assignable_expression,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(83), 2,
      sym_integer,
      sym_string_literal,
    STATE(35), 2,
      sym__statement,
      aux_sym_code_block_repeat1,
    STATE(118), 2,
      sym_function_call,
      sym_method_call,
    STATE(449), 6,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
    STATE(372), 17,
      sym_repeat_statement,
      sym_assignment_statement,
      sym_procedure_call,
      sym_insert_statement,
      sym_modify_statement,
      sym_delete_statement,
      sym_set_range_statement,
      sym_set_filter_statement,
      sym_reset_statement,
      sym_if_statement,
      sym_get_statement,
      sym_find_set_statement,
      sym_find_first_statement,
      sym_find_last_statement,
      sym_next_statement,
      sym_case_statement,
      sym_exit_statement,
  [3047] = 17,
    ACTIONS(186), 1,
      anon_sym_RBRACE,
    ACTIONS(188), 1,
      anon_sym_TableType,
    ACTIONS(191), 1,
      anon_sym_trigger,
    ACTIONS(194), 1,
      anon_sym_Permissions,
    ACTIONS(197), 1,
      anon_sym_DrillDownPageId,
    ACTIONS(200), 1,
      anon_sym_LookupPageId,
    ACTIONS(203), 1,
      anon_sym_DataClassification,
    ACTIONS(206), 1,
      anon_sym_Caption,
    ACTIONS(209), 1,
      anon_sym_var,
    ACTIONS(212), 1,
      anon_sym_LBRACK,
    ACTIONS(215), 1,
      anon_sym_fields,
    ACTIONS(218), 1,
      anon_sym_keys,
    ACTIONS(221), 1,
      sym_procedure_modifier,
    ACTIONS(224), 1,
      anon_sym_procedure,
    STATE(809), 1,
      sym_attribute_list,
    STATE(529), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
    STATE(41), 24,
      sym_table_type_property,
      sym__table_element,
      sym_permissions_property,
      sym_oninsert_trigger,
      sym_onmodify_trigger,
      sym_ondelete_trigger,
      sym_onrename_trigger,
      sym_onvalidate_trigger,
      sym_onaftergetrecord_trigger,
      sym_onafterinsertevent_trigger,
      sym_onaftermodifyevent_trigger,
      sym_onafterdeleteevent_trigger,
      sym_onbeforeinsertevent_trigger,
      sym_onbeforemodifyevent_trigger,
      sym_onbeforedeleteevent_trigger,
      sym_caption_property,
      sym_data_classification_property,
      sym_drilldown_pageid_property,
      sym_lookup_pageid_property,
      sym_var_section,
      sym_fields,
      sym_keys,
      sym_procedure,
      aux_sym_table_declaration_repeat1,
  [3123] = 17,
    ACTIONS(227), 1,
      anon_sym_RBRACE,
    ACTIONS(229), 1,
      anon_sym_TableType,
    ACTIONS(231), 1,
      anon_sym_trigger,
    ACTIONS(233), 1,
      anon_sym_Permissions,
    ACTIONS(235), 1,
      anon_sym_DrillDownPageId,
    ACTIONS(237), 1,
      anon_sym_LookupPageId,
    ACTIONS(239), 1,
      anon_sym_DataClassification,
    ACTIONS(241), 1,
      anon_sym_Caption,
    ACTIONS(243), 1,
      anon_sym_var,
    ACTIONS(245), 1,
      anon_sym_LBRACK,
    ACTIONS(247), 1,
      anon_sym_fields,
    ACTIONS(249), 1,
      anon_sym_keys,
    ACTIONS(251), 1,
      sym_procedure_modifier,
    ACTIONS(253), 1,
      anon_sym_procedure,
    STATE(809), 1,
      sym_attribute_list,
    STATE(529), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
    STATE(43), 24,
      sym_table_type_property,
      sym__table_element,
      sym_permissions_property,
      sym_oninsert_trigger,
      sym_onmodify_trigger,
      sym_ondelete_trigger,
      sym_onrename_trigger,
      sym_onvalidate_trigger,
      sym_onaftergetrecord_trigger,
      sym_onafterinsertevent_trigger,
      sym_onaftermodifyevent_trigger,
      sym_onafterdeleteevent_trigger,
      sym_onbeforeinsertevent_trigger,
      sym_onbeforemodifyevent_trigger,
      sym_onbeforedeleteevent_trigger,
      sym_caption_property,
      sym_data_classification_property,
      sym_drilldown_pageid_property,
      sym_lookup_pageid_property,
      sym_var_section,
      sym_fields,
      sym_keys,
      sym_procedure,
      aux_sym_table_declaration_repeat1,
  [3199] = 17,
    ACTIONS(229), 1,
      anon_sym_TableType,
    ACTIONS(231), 1,
      anon_sym_trigger,
    ACTIONS(233), 1,
      anon_sym_Permissions,
    ACTIONS(235), 1,
      anon_sym_DrillDownPageId,
    ACTIONS(237), 1,
      anon_sym_LookupPageId,
    ACTIONS(239), 1,
      anon_sym_DataClassification,
    ACTIONS(241), 1,
      anon_sym_Caption,
    ACTIONS(243), 1,
      anon_sym_var,
    ACTIONS(245), 1,
      anon_sym_LBRACK,
    ACTIONS(247), 1,
      anon_sym_fields,
    ACTIONS(249), 1,
      anon_sym_keys,
    ACTIONS(251), 1,
      sym_procedure_modifier,
    ACTIONS(253), 1,
      anon_sym_procedure,
    ACTIONS(255), 1,
      anon_sym_RBRACE,
    STATE(809), 1,
      sym_attribute_list,
    STATE(529), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
    STATE(41), 24,
      sym_table_type_property,
      sym__table_element,
      sym_permissions_property,
      sym_oninsert_trigger,
      sym_onmodify_trigger,
      sym_ondelete_trigger,
      sym_onrename_trigger,
      sym_onvalidate_trigger,
      sym_onaftergetrecord_trigger,
      sym_onafterinsertevent_trigger,
      sym_onaftermodifyevent_trigger,
      sym_onafterdeleteevent_trigger,
      sym_onbeforeinsertevent_trigger,
      sym_onbeforemodifyevent_trigger,
      sym_onbeforedeleteevent_trigger,
      sym_caption_property,
      sym_data_classification_property,
      sym_drilldown_pageid_property,
      sym_lookup_pageid_property,
      sym_var_section,
      sym_fields,
      sym_keys,
      sym_procedure,
      aux_sym_table_declaration_repeat1,
  [3275] = 7,
    ACTIONS(15), 1,
      anon_sym_Text,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(25), 1,
      anon_sym_array,
    ACTIONS(257), 1,
      anon_sym_Code,
    ACTIONS(259), 1,
      sym_identifier,
    STATE(805), 5,
      sym_basic_type,
      sym_text_type,
      sym_code_type,
      sym_record_type,
      sym_array_type,
    ACTIONS(13), 30,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Date,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_Media,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [3330] = 7,
    ACTIONS(15), 1,
      anon_sym_Text,
    ACTIONS(17), 1,
      anon_sym_Record,
    ACTIONS(25), 1,
      anon_sym_array,
    ACTIONS(257), 1,
      anon_sym_Code,
    ACTIONS(261), 1,
      sym_identifier,
    STATE(725), 5,
      sym_basic_type,
      sym_text_type,
      sym_code_type,
      sym_record_type,
      sym_array_type,
    ACTIONS(13), 30,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Decimal,
      anon_sym_Byte,
      anon_sym_Char,
      anon_sym_Date,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_DateFormula,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Variant,
      anon_sym_Dialog,
      anon_sym_Action,
      anon_sym_Blob,
      anon_sym_FilterPageBuilder,
      anon_sym_JsonToken,
      anon_sym_JsonValue,
      anon_sym_JsonArray,
      anon_sym_JsonObject,
      anon_sym_Media,
      anon_sym_MediaSet,
      anon_sym_OStream,
      anon_sym_InStream,
      anon_sym_OutStream,
      anon_sym_SecretText,
      anon_sym_Label,
  [3385] = 24,
    ACTIONS(245), 1,
      anon_sym_LBRACK,
    ACTIONS(251), 1,
      sym_procedure_modifier,
    ACTIONS(253), 1,
      anon_sym_procedure,
    ACTIONS(263), 1,
      anon_sym_RBRACE,
    ACTIONS(265), 1,
      anon_sym_trigger,
    ACTIONS(267), 1,
      anon_sym_Permissions,
    ACTIONS(269), 1,
      anon_sym_TableNo,
    ACTIONS(271), 1,
      anon_sym_Subtype,
    ACTIONS(273), 1,
      anon_sym_SingleInstance,
    ACTIONS(277), 1,
      anon_sym_TableRelation,
    ACTIONS(279), 1,
      anon_sym_FieldClass,
    ACTIONS(281), 1,
      anon_sym_CalcFormula,
    ACTIONS(283), 1,
      anon_sym_BlankZero,
    ACTIONS(285), 1,
      anon_sym_Editable,
    ACTIONS(287), 1,
      anon_sym_OptionMembers,
    ACTIONS(289), 1,
      anon_sym_OptionCaption,
    ACTIONS(291), 1,
      anon_sym_DataClassification,
    ACTIONS(293), 1,
      anon_sym_var,
    STATE(256), 1,
      sym_property_list,
    STATE(809), 1,
      sym_attribute_list,
    ACTIONS(275), 2,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
    STATE(83), 2,
      sym_property,
      aux_sym_property_list_repeat1,
    STATE(529), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
    STATE(289), 5,
      sym__codeunit_element,
      sym_onrun_trigger,
      sym_var_section,
      sym_procedure,
      aux_sym_codeunit_declaration_repeat1,
  [3465] = 2,
    ACTIONS(297), 3,
      anon_sym_COLON,
      anon_sym_LT,
      anon_sym_GT,
    ACTIONS(295), 26,
      anon_sym_LBRACE,
      anon_sym_COMMA,
      anon_sym_Temporary,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_var,
      anon_sym_of,
      anon_sym_RBRACK,
      anon_sym_LPAREN,
      anon_sym_RPAREN,
      anon_sym_where,
      anon_sym_else,
      anon_sym_LT_GT,
      anon_sym_LT_EQ,
      anon_sym_GT_EQ,
      anon_sym_IN,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      sym_temporary,
      anon_sym_begin,
      anon_sym_COLON_EQ,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [3499] = 3,
    STATE(164), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(301), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(299), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [3530] = 7,
    ACTIONS(307), 1,
      anon_sym_DOT,
    ACTIONS(313), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(164), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
    ACTIONS(305), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(309), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [3569] = 7,
    ACTIONS(307), 1,
      anon_sym_DOT,
    ACTIONS(313), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(164), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
    ACTIONS(315), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(317), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [3608] = 7,
    ACTIONS(319), 1,
      anon_sym_DOT,
    ACTIONS(321), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(160), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
    ACTIONS(305), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(309), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [3647] = 2,
    ACTIONS(325), 9,
      anon_sym_COLON,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(323), 15,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [3676] = 3,
    STATE(160), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(301), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(299), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [3707] = 7,
    ACTIONS(319), 1,
      anon_sym_DOT,
    ACTIONS(321), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(160), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
    ACTIONS(315), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(317), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [3746] = 2,
    ACTIONS(329), 9,
      anon_sym_COLON,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(327), 15,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [3775] = 13,
    ACTIONS(331), 1,
      anon_sym_RBRACE,
    ACTIONS(333), 1,
      anon_sym_trigger,
    ACTIONS(336), 1,
      anon_sym_TableRelation,
    ACTIONS(339), 1,
      anon_sym_FieldClass,
    ACTIONS(342), 1,
      anon_sym_CalcFormula,
    ACTIONS(345), 1,
      anon_sym_BlankZero,
    ACTIONS(348), 1,
      anon_sym_Editable,
    ACTIONS(351), 1,
      anon_sym_OptionMembers,
    ACTIONS(354), 1,
      anon_sym_OptionCaption,
    ACTIONS(357), 1,
      anon_sym_DataClassification,
    ACTIONS(360), 1,
      anon_sym_Caption,
    ACTIONS(363), 1,
      anon_sym_DecimalPlaces,
    STATE(56), 12,
      sym_caption_property,
      sym_data_classification_property,
      sym_decimal_places_property,
      sym_table_relation_property,
      sym_field_class_property,
      sym_calc_formula_property,
      sym_blank_zero_property,
      sym_editable_property,
      sym_option_members_property,
      sym_option_caption_property,
      sym_field_trigger_declaration,
      aux_sym_field_declaration_repeat1,
  [3826] = 2,
    ACTIONS(368), 9,
      anon_sym_COLON,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(366), 15,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [3855] = 2,
    ACTIONS(372), 9,
      anon_sym_COLON,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(370), 15,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [3884] = 2,
    ACTIONS(376), 1,
      anon_sym_SEMI,
    ACTIONS(374), 23,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
      anon_sym_end,
  [3913] = 2,
    ACTIONS(380), 1,
      anon_sym_SEMI,
    ACTIONS(378), 23,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
      anon_sym_end,
  [3942] = 13,
    ACTIONS(239), 1,
      anon_sym_DataClassification,
    ACTIONS(241), 1,
      anon_sym_Caption,
    ACTIONS(382), 1,
      anon_sym_RBRACE,
    ACTIONS(384), 1,
      anon_sym_trigger,
    ACTIONS(386), 1,
      anon_sym_TableRelation,
    ACTIONS(388), 1,
      anon_sym_FieldClass,
    ACTIONS(390), 1,
      anon_sym_CalcFormula,
    ACTIONS(392), 1,
      anon_sym_BlankZero,
    ACTIONS(394), 1,
      anon_sym_Editable,
    ACTIONS(396), 1,
      anon_sym_OptionMembers,
    ACTIONS(398), 1,
      anon_sym_OptionCaption,
    ACTIONS(400), 1,
      anon_sym_DecimalPlaces,
    STATE(56), 12,
      sym_caption_property,
      sym_data_classification_property,
      sym_decimal_places_property,
      sym_table_relation_property,
      sym_field_class_property,
      sym_calc_formula_property,
      sym_blank_zero_property,
      sym_editable_property,
      sym_option_members_property,
      sym_option_caption_property,
      sym_field_trigger_declaration,
      aux_sym_field_declaration_repeat1,
  [3993] = 13,
    ACTIONS(239), 1,
      anon_sym_DataClassification,
    ACTIONS(241), 1,
      anon_sym_Caption,
    ACTIONS(384), 1,
      anon_sym_trigger,
    ACTIONS(386), 1,
      anon_sym_TableRelation,
    ACTIONS(388), 1,
      anon_sym_FieldClass,
    ACTIONS(390), 1,
      anon_sym_CalcFormula,
    ACTIONS(392), 1,
      anon_sym_BlankZero,
    ACTIONS(394), 1,
      anon_sym_Editable,
    ACTIONS(396), 1,
      anon_sym_OptionMembers,
    ACTIONS(398), 1,
      anon_sym_OptionCaption,
    ACTIONS(400), 1,
      anon_sym_DecimalPlaces,
    ACTIONS(402), 1,
      anon_sym_RBRACE,
    STATE(61), 12,
      sym_caption_property,
      sym_data_classification_property,
      sym_decimal_places_property,
      sym_table_relation_property,
      sym_field_class_property,
      sym_calc_formula_property,
      sym_blank_zero_property,
      sym_editable_property,
      sym_option_members_property,
      sym_option_caption_property,
      sym_field_trigger_declaration,
      aux_sym_field_declaration_repeat1,
  [4044] = 2,
    ACTIONS(406), 9,
      anon_sym_COLON,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(404), 15,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4073] = 3,
    STATE(98), 1,
      sym_argument_list,
    ACTIONS(410), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(408), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4103] = 3,
    STATE(85), 1,
      sym_argument_list,
    ACTIONS(410), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(408), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4133] = 7,
    ACTIONS(412), 1,
      anon_sym_DOT,
    ACTIONS(414), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(156), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
    ACTIONS(315), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(317), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [4171] = 1,
    ACTIONS(416), 23,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
      anon_sym_end,
  [4197] = 1,
    ACTIONS(374), 23,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
      anon_sym_end,
  [4223] = 7,
    ACTIONS(412), 1,
      anon_sym_DOT,
    ACTIONS(414), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(156), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
    ACTIONS(305), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(309), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [4261] = 3,
    STATE(156), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(301), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(299), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4291] = 7,
    ACTIONS(418), 1,
      anon_sym_DOT,
    ACTIONS(420), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(152), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
    ACTIONS(315), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(317), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [4329] = 7,
    ACTIONS(418), 1,
      anon_sym_DOT,
    ACTIONS(420), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(152), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
    ACTIONS(305), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(309), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [4367] = 3,
    STATE(152), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(301), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(299), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4397] = 2,
    ACTIONS(406), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(404), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4424] = 3,
    STATE(57), 1,
      sym_argument_list,
    ACTIONS(410), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(408), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4453] = 3,
    ACTIONS(424), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(422), 8,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
    ACTIONS(426), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [4482] = 3,
    STATE(106), 1,
      sym_argument_list,
    ACTIONS(410), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(408), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4511] = 2,
    ACTIONS(297), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(295), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4538] = 2,
    ACTIONS(430), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(428), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4565] = 3,
    ACTIONS(424), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(422), 8,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
    ACTIONS(426), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [4594] = 2,
    ACTIONS(434), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(432), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4621] = 2,
    ACTIONS(325), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(323), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4648] = 15,
    ACTIONS(267), 1,
      anon_sym_Permissions,
    ACTIONS(269), 1,
      anon_sym_TableNo,
    ACTIONS(271), 1,
      anon_sym_Subtype,
    ACTIONS(273), 1,
      anon_sym_SingleInstance,
    ACTIONS(277), 1,
      anon_sym_TableRelation,
    ACTIONS(279), 1,
      anon_sym_FieldClass,
    ACTIONS(281), 1,
      anon_sym_CalcFormula,
    ACTIONS(283), 1,
      anon_sym_BlankZero,
    ACTIONS(285), 1,
      anon_sym_Editable,
    ACTIONS(287), 1,
      anon_sym_OptionMembers,
    ACTIONS(289), 1,
      anon_sym_OptionCaption,
    ACTIONS(291), 1,
      anon_sym_DataClassification,
    ACTIONS(275), 2,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
    STATE(86), 2,
      sym_property,
      aux_sym_property_list_repeat1,
    ACTIONS(436), 6,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_var,
      anon_sym_LBRACK,
      sym_procedure_modifier,
      anon_sym_procedure,
  [4701] = 2,
    ACTIONS(440), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(438), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4728] = 2,
    ACTIONS(368), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(366), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4755] = 15,
    ACTIONS(444), 1,
      anon_sym_Permissions,
    ACTIONS(447), 1,
      anon_sym_TableNo,
    ACTIONS(450), 1,
      anon_sym_Subtype,
    ACTIONS(453), 1,
      anon_sym_SingleInstance,
    ACTIONS(459), 1,
      anon_sym_TableRelation,
    ACTIONS(462), 1,
      anon_sym_FieldClass,
    ACTIONS(465), 1,
      anon_sym_CalcFormula,
    ACTIONS(468), 1,
      anon_sym_BlankZero,
    ACTIONS(471), 1,
      anon_sym_Editable,
    ACTIONS(474), 1,
      anon_sym_OptionMembers,
    ACTIONS(477), 1,
      anon_sym_OptionCaption,
    ACTIONS(480), 1,
      anon_sym_DataClassification,
    ACTIONS(456), 2,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
    STATE(86), 2,
      sym_property,
      aux_sym_property_list_repeat1,
    ACTIONS(442), 6,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_var,
      anon_sym_LBRACK,
      sym_procedure_modifier,
      anon_sym_procedure,
  [4808] = 2,
    ACTIONS(372), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(370), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4835] = 11,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(483), 1,
      anon_sym_else,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(489), 1,
      anon_sym_end,
    STATE(896), 1,
      sym_else_clause,
    STATE(1052), 1,
      sym_value_set,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(487), 2,
      sym_integer,
      sym_string_literal,
    STATE(112), 2,
      sym_case_clause,
      aux_sym_case_statement_repeat1,
    STATE(381), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [4880] = 2,
    ACTIONS(297), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(295), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4907] = 2,
    ACTIONS(430), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(428), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4934] = 2,
    ACTIONS(406), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(404), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4961] = 2,
    ACTIONS(434), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(432), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [4988] = 2,
    ACTIONS(325), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(323), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5015] = 1,
    ACTIONS(491), 22,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [5040] = 2,
    ACTIONS(440), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(438), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5067] = 1,
    ACTIONS(493), 22,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [5092] = 2,
    ACTIONS(329), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(327), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5119] = 2,
    ACTIONS(368), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(366), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5146] = 2,
    ACTIONS(372), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(370), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5173] = 11,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(483), 1,
      anon_sym_else,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(495), 1,
      anon_sym_end,
    STATE(955), 1,
      sym_else_clause,
    STATE(1052), 1,
      sym_value_set,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(487), 2,
      sym_integer,
      sym_string_literal,
    STATE(112), 2,
      sym_case_clause,
      aux_sym_case_statement_repeat1,
    STATE(381), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [5218] = 11,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(483), 1,
      anon_sym_else,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(497), 1,
      anon_sym_end,
    STATE(996), 1,
      sym_else_clause,
    STATE(1052), 1,
      sym_value_set,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(487), 2,
      sym_integer,
      sym_string_literal,
    STATE(112), 2,
      sym_case_clause,
      aux_sym_case_statement_repeat1,
    STATE(381), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [5263] = 11,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(483), 1,
      anon_sym_else,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(499), 1,
      anon_sym_end,
    STATE(1032), 1,
      sym_else_clause,
    STATE(1052), 1,
      sym_value_set,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(487), 2,
      sym_integer,
      sym_string_literal,
    STATE(112), 2,
      sym_case_clause,
      aux_sym_case_statement_repeat1,
    STATE(381), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [5308] = 2,
    ACTIONS(329), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(327), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5335] = 3,
    ACTIONS(424), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(422), 8,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
    ACTIONS(426), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [5363] = 2,
    ACTIONS(440), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(438), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5389] = 2,
    ACTIONS(368), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(366), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5415] = 2,
    ACTIONS(372), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(370), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5441] = 2,
    ACTIONS(297), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(295), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5467] = 2,
    ACTIONS(406), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(404), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5493] = 2,
    ACTIONS(434), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(432), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5519] = 2,
    ACTIONS(325), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(323), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5545] = 9,
    ACTIONS(501), 1,
      anon_sym_LPAREN,
    ACTIONS(506), 1,
      sym_identifier,
    ACTIONS(509), 1,
      anon_sym_DQUOTE,
    STATE(1052), 1,
      sym_value_set,
    ACTIONS(504), 2,
      anon_sym_else,
      anon_sym_end,
    ACTIONS(512), 2,
      sym_integer,
      sym_string_literal,
    ACTIONS(515), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(112), 2,
      sym_case_clause,
      aux_sym_case_statement_repeat1,
    STATE(381), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [5585] = 2,
    ACTIONS(430), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(428), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5611] = 2,
    ACTIONS(440), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(438), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5637] = 1,
    ACTIONS(518), 21,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_TableNo,
      anon_sym_Subtype,
      anon_sym_SingleInstance,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_var,
      anon_sym_LBRACK,
      sym_procedure_modifier,
      anon_sym_procedure,
      anon_sym_Clustered,
  [5661] = 2,
    ACTIONS(297), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(295), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5687] = 2,
    ACTIONS(430), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(428), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5713] = 3,
    ACTIONS(424), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(422), 8,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
    ACTIONS(426), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [5741] = 2,
    ACTIONS(434), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(432), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5767] = 2,
    ACTIONS(329), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
    ACTIONS(327), 13,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_LPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
      anon_sym_COLON_COLON,
  [5793] = 8,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    STATE(1052), 1,
      sym_value_set,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(487), 2,
      sym_integer,
      sym_string_literal,
    STATE(102), 2,
      sym_case_clause,
      aux_sym_case_statement_repeat1,
    STATE(381), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [5829] = 8,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    STATE(1052), 1,
      sym_value_set,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(487), 2,
      sym_integer,
      sym_string_literal,
    STATE(88), 2,
      sym_case_clause,
      aux_sym_case_statement_repeat1,
    STATE(381), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [5865] = 16,
    ACTIONS(267), 1,
      anon_sym_Permissions,
    ACTIONS(269), 1,
      anon_sym_TableNo,
    ACTIONS(271), 1,
      anon_sym_Subtype,
    ACTIONS(273), 1,
      anon_sym_SingleInstance,
    ACTIONS(277), 1,
      anon_sym_TableRelation,
    ACTIONS(279), 1,
      anon_sym_FieldClass,
    ACTIONS(281), 1,
      anon_sym_CalcFormula,
    ACTIONS(283), 1,
      anon_sym_BlankZero,
    ACTIONS(285), 1,
      anon_sym_Editable,
    ACTIONS(287), 1,
      anon_sym_OptionMembers,
    ACTIONS(289), 1,
      anon_sym_OptionCaption,
    ACTIONS(291), 1,
      anon_sym_DataClassification,
    ACTIONS(520), 1,
      anon_sym_RBRACE,
    ACTIONS(522), 1,
      anon_sym_Clustered,
    ACTIONS(275), 2,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
    STATE(124), 3,
      sym_property,
      sym_clustered_property,
      aux_sym_key_declaration_repeat1,
  [5917] = 16,
    ACTIONS(524), 1,
      anon_sym_RBRACE,
    ACTIONS(526), 1,
      anon_sym_Permissions,
    ACTIONS(529), 1,
      anon_sym_TableNo,
    ACTIONS(532), 1,
      anon_sym_Subtype,
    ACTIONS(535), 1,
      anon_sym_SingleInstance,
    ACTIONS(541), 1,
      anon_sym_TableRelation,
    ACTIONS(544), 1,
      anon_sym_FieldClass,
    ACTIONS(547), 1,
      anon_sym_CalcFormula,
    ACTIONS(550), 1,
      anon_sym_BlankZero,
    ACTIONS(553), 1,
      anon_sym_Editable,
    ACTIONS(556), 1,
      anon_sym_OptionMembers,
    ACTIONS(559), 1,
      anon_sym_OptionCaption,
    ACTIONS(562), 1,
      anon_sym_DataClassification,
    ACTIONS(565), 1,
      anon_sym_Clustered,
    ACTIONS(538), 2,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
    STATE(124), 3,
      sym_property,
      sym_clustered_property,
      aux_sym_key_declaration_repeat1,
  [5969] = 8,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    STATE(1052), 1,
      sym_value_set,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(487), 2,
      sym_integer,
      sym_string_literal,
    STATE(100), 2,
      sym_case_clause,
      aux_sym_case_statement_repeat1,
    STATE(381), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6005] = 16,
    ACTIONS(267), 1,
      anon_sym_Permissions,
    ACTIONS(269), 1,
      anon_sym_TableNo,
    ACTIONS(271), 1,
      anon_sym_Subtype,
    ACTIONS(273), 1,
      anon_sym_SingleInstance,
    ACTIONS(277), 1,
      anon_sym_TableRelation,
    ACTIONS(279), 1,
      anon_sym_FieldClass,
    ACTIONS(281), 1,
      anon_sym_CalcFormula,
    ACTIONS(283), 1,
      anon_sym_BlankZero,
    ACTIONS(285), 1,
      anon_sym_Editable,
    ACTIONS(287), 1,
      anon_sym_OptionMembers,
    ACTIONS(289), 1,
      anon_sym_OptionCaption,
    ACTIONS(291), 1,
      anon_sym_DataClassification,
    ACTIONS(522), 1,
      anon_sym_Clustered,
    ACTIONS(568), 1,
      anon_sym_RBRACE,
    ACTIONS(275), 2,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
    STATE(123), 3,
      sym_property,
      sym_clustered_property,
      aux_sym_key_declaration_repeat1,
  [6057] = 8,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    STATE(1052), 1,
      sym_value_set,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(487), 2,
      sym_integer,
      sym_string_literal,
    STATE(101), 2,
      sym_case_clause,
      aux_sym_case_statement_repeat1,
    STATE(381), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6093] = 7,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(570), 1,
      anon_sym_RPAREN,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(572), 2,
      sym_integer,
      sym_string_literal,
    STATE(391), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6125] = 7,
    ACTIONS(576), 1,
      anon_sym_Decimal,
    ACTIONS(578), 1,
      anon_sym_Text,
    ACTIONS(580), 1,
      anon_sym_Code,
    ACTIONS(582), 1,
      sym_identifier,
    ACTIONS(584), 1,
      anon_sym_Enum,
    STATE(906), 1,
      sym_data_type,
    ACTIONS(574), 11,
      anon_sym_Integer,
      anon_sym_BigInteger,
      anon_sym_Date,
      anon_sym_Time,
      anon_sym_DateTime,
      anon_sym_Duration,
      anon_sym_Boolean,
      anon_sym_Option,
      anon_sym_Guid,
      anon_sym_RecordId,
      anon_sym_Blob,
  [6157] = 7,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(586), 1,
      anon_sym_RPAREN,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(588), 2,
      sym_integer,
      sym_string_literal,
    STATE(324), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6189] = 7,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(590), 1,
      anon_sym_RPAREN,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(592), 2,
      sym_integer,
      sym_string_literal,
    STATE(390), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6221] = 7,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(594), 1,
      anon_sym_RPAREN,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(596), 2,
      sym_integer,
      sym_string_literal,
    STATE(393), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6253] = 4,
    ACTIONS(602), 1,
      sym_identifier,
    ACTIONS(598), 2,
      anon_sym_RBRACE,
      anon_sym_LBRACK,
    STATE(136), 2,
      sym_variable_declaration,
      aux_sym_var_section_repeat1,
    ACTIONS(600), 12,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [6279] = 7,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(604), 1,
      anon_sym_RPAREN,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(606), 2,
      sym_integer,
      sym_string_literal,
    STATE(392), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6311] = 7,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    STATE(1071), 1,
      sym_expression_list,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(608), 2,
      sym_integer,
      sym_string_literal,
    STATE(349), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6343] = 4,
    ACTIONS(614), 1,
      sym_identifier,
    ACTIONS(610), 2,
      anon_sym_RBRACE,
      anon_sym_LBRACK,
    STATE(136), 2,
      sym_variable_declaration,
      aux_sym_var_section_repeat1,
    ACTIONS(612), 12,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [6369] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(617), 2,
      sym_integer,
      sym_string_literal,
    STATE(429), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6398] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(619), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(621), 2,
      sym_integer,
      sym_string_literal,
    STATE(407), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6427] = 6,
    ACTIONS(623), 1,
      anon_sym_LPAREN,
    ACTIONS(625), 1,
      sym_identifier,
    ACTIONS(627), 1,
      anon_sym_DQUOTE,
    ACTIONS(629), 2,
      sym_integer,
      sym_string_literal,
    ACTIONS(631), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(69), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6456] = 6,
    ACTIONS(633), 1,
      anon_sym_LPAREN,
    ACTIONS(635), 1,
      sym_identifier,
    ACTIONS(637), 1,
      anon_sym_DQUOTE,
    ACTIONS(639), 2,
      sym_integer,
      sym_string_literal,
    ACTIONS(641), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(54), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6485] = 6,
    ACTIONS(633), 1,
      anon_sym_LPAREN,
    ACTIONS(637), 1,
      anon_sym_DQUOTE,
    ACTIONS(643), 1,
      sym_identifier,
    ACTIONS(641), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(645), 2,
      sym_integer,
      sym_string_literal,
    STATE(51), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6514] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(647), 2,
      sym_integer,
      sym_string_literal,
    STATE(320), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6543] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(649), 2,
      sym_integer,
      sym_string_literal,
    STATE(399), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6572] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(651), 2,
      sym_integer,
      sym_string_literal,
    STATE(345), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6601] = 6,
    ACTIONS(653), 1,
      anon_sym_LPAREN,
    ACTIONS(655), 1,
      sym_identifier,
    ACTIONS(657), 1,
      anon_sym_DQUOTE,
    ACTIONS(659), 2,
      sym_integer,
      sym_string_literal,
    ACTIONS(661), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(71), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6630] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(619), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(663), 2,
      sym_integer,
      sym_string_literal,
    STATE(436), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6659] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(665), 2,
      sym_integer,
      sym_string_literal,
    STATE(416), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6688] = 1,
    ACTIONS(667), 16,
      anon_sym_RBRACE,
      anon_sym_Permissions,
      anon_sym_TableNo,
      anon_sym_Subtype,
      anon_sym_SingleInstance,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Clustered,
  [6707] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(669), 2,
      sym_integer,
      sym_string_literal,
    STATE(418), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6736] = 6,
    ACTIONS(671), 1,
      anon_sym_LPAREN,
    ACTIONS(673), 1,
      sym_identifier,
    ACTIONS(675), 1,
      anon_sym_DQUOTE,
    ACTIONS(677), 2,
      sym_integer,
      sym_string_literal,
    ACTIONS(679), 2,
      anon_sym_true,
      anon_sym_false,
    STATE(50), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6765] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(681), 2,
      sym_integer,
      sym_string_literal,
    STATE(419), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6794] = 6,
    ACTIONS(653), 1,
      anon_sym_LPAREN,
    ACTIONS(657), 1,
      anon_sym_DQUOTE,
    ACTIONS(683), 1,
      sym_identifier,
    ACTIONS(661), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(685), 2,
      sym_integer,
      sym_string_literal,
    STATE(73), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6823] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(687), 2,
      sym_integer,
      sym_string_literal,
    STATE(420), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6852] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(619), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(689), 2,
      sym_integer,
      sym_string_literal,
    STATE(413), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6881] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(691), 2,
      sym_integer,
      sym_string_literal,
    STATE(422), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6910] = 6,
    ACTIONS(623), 1,
      anon_sym_LPAREN,
    ACTIONS(627), 1,
      anon_sym_DQUOTE,
    ACTIONS(693), 1,
      sym_identifier,
    ACTIONS(631), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(695), 2,
      sym_integer,
      sym_string_literal,
    STATE(70), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6939] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(697), 2,
      sym_integer,
      sym_string_literal,
    STATE(424), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6968] = 6,
    ACTIONS(671), 1,
      anon_sym_LPAREN,
    ACTIONS(675), 1,
      anon_sym_DQUOTE,
    ACTIONS(699), 1,
      sym_identifier,
    ACTIONS(679), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(701), 2,
      sym_integer,
      sym_string_literal,
    STATE(49), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [6997] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(703), 2,
      sym_integer,
      sym_string_literal,
    STATE(426), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7026] = 6,
    ACTIONS(633), 1,
      anon_sym_LPAREN,
    ACTIONS(637), 1,
      anon_sym_DQUOTE,
    ACTIONS(705), 1,
      sym_identifier,
    ACTIONS(641), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(707), 2,
      sym_integer,
      sym_string_literal,
    STATE(53), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7055] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(485), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(709), 2,
      sym_integer,
      sym_string_literal,
    STATE(428), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7084] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(619), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(711), 2,
      sym_integer,
      sym_string_literal,
    STATE(439), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7113] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(619), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(713), 2,
      sym_integer,
      sym_string_literal,
    STATE(432), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7142] = 6,
    ACTIONS(671), 1,
      anon_sym_LPAREN,
    ACTIONS(675), 1,
      anon_sym_DQUOTE,
    ACTIONS(715), 1,
      sym_identifier,
    ACTIONS(679), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(717), 2,
      sym_integer,
      sym_string_literal,
    STATE(48), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7171] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(619), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(719), 2,
      sym_integer,
      sym_string_literal,
    STATE(434), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7200] = 6,
    ACTIONS(623), 1,
      anon_sym_LPAREN,
    ACTIONS(627), 1,
      anon_sym_DQUOTE,
    ACTIONS(721), 1,
      sym_identifier,
    ACTIONS(631), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(723), 2,
      sym_integer,
      sym_string_literal,
    STATE(66), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7229] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(619), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(725), 2,
      sym_integer,
      sym_string_literal,
    STATE(440), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7258] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(619), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(727), 2,
      sym_integer,
      sym_string_literal,
    STATE(412), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7287] = 6,
    ACTIONS(45), 1,
      anon_sym_LPAREN,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(619), 1,
      sym_identifier,
    ACTIONS(55), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(729), 2,
      sym_integer,
      sym_string_literal,
    STATE(441), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7316] = 6,
    ACTIONS(653), 1,
      anon_sym_LPAREN,
    ACTIONS(657), 1,
      anon_sym_DQUOTE,
    ACTIONS(731), 1,
      sym_identifier,
    ACTIONS(661), 2,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(733), 2,
      sym_integer,
      sym_string_literal,
    STATE(72), 9,
      sym_function_call,
      sym_member_access,
      sym_method_call,
      sym__quoted_identifier,
      sym_boolean,
      sym__primary_expression,
      sym_enum_member_access,
      sym__expression,
      sym_binary_expression,
  [7345] = 2,
    ACTIONS(735), 2,
      anon_sym_RBRACE,
      anon_sym_LBRACK,
    ACTIONS(737), 13,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
      sym_identifier,
  [7365] = 2,
    ACTIONS(739), 2,
      anon_sym_RBRACE,
      anon_sym_LBRACK,
    ACTIONS(741), 13,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
      sym_identifier,
  [7385] = 1,
    ACTIONS(743), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7402] = 4,
    ACTIONS(410), 1,
      anon_sym_COLON,
    ACTIONS(745), 1,
      anon_sym_LPAREN,
    STATE(57), 1,
      sym_argument_list,
    ACTIONS(408), 11,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_EQ,
      anon_sym_COLON_COLON,
  [7425] = 1,
    ACTIONS(747), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7442] = 1,
    ACTIONS(749), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7459] = 1,
    ACTIONS(751), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7476] = 1,
    ACTIONS(753), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7493] = 9,
    ACTIONS(245), 1,
      anon_sym_LBRACK,
    ACTIONS(251), 1,
      sym_procedure_modifier,
    ACTIONS(253), 1,
      anon_sym_procedure,
    ACTIONS(265), 1,
      anon_sym_trigger,
    ACTIONS(293), 1,
      anon_sym_var,
    ACTIONS(755), 1,
      anon_sym_RBRACE,
    STATE(809), 1,
      sym_attribute_list,
    STATE(529), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
    STATE(180), 5,
      sym__codeunit_element,
      sym_onrun_trigger,
      sym_var_section,
      sym_procedure,
      aux_sym_codeunit_declaration_repeat1,
  [7526] = 9,
    ACTIONS(757), 1,
      anon_sym_RBRACE,
    ACTIONS(759), 1,
      anon_sym_trigger,
    ACTIONS(762), 1,
      anon_sym_var,
    ACTIONS(765), 1,
      anon_sym_LBRACK,
    ACTIONS(768), 1,
      sym_procedure_modifier,
    ACTIONS(771), 1,
      anon_sym_procedure,
    STATE(809), 1,
      sym_attribute_list,
    STATE(529), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
    STATE(180), 5,
      sym__codeunit_element,
      sym_onrun_trigger,
      sym_var_section,
      sym_procedure,
      aux_sym_codeunit_declaration_repeat1,
  [7559] = 1,
    ACTIONS(774), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7576] = 1,
    ACTIONS(776), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7593] = 1,
    ACTIONS(778), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7610] = 1,
    ACTIONS(780), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7627] = 1,
    ACTIONS(782), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7644] = 1,
    ACTIONS(780), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7661] = 1,
    ACTIONS(784), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7678] = 1,
    ACTIONS(786), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7695] = 1,
    ACTIONS(788), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7712] = 3,
    ACTIONS(794), 1,
      anon_sym_else,
    ACTIONS(790), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(792), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [7733] = 1,
    ACTIONS(796), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7750] = 1,
    ACTIONS(798), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7767] = 1,
    ACTIONS(800), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7784] = 1,
    ACTIONS(802), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7801] = 1,
    ACTIONS(804), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7818] = 1,
    ACTIONS(802), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7835] = 1,
    ACTIONS(806), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7852] = 1,
    ACTIONS(808), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7869] = 1,
    ACTIONS(810), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7886] = 1,
    ACTIONS(806), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7903] = 1,
    ACTIONS(812), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7920] = 1,
    ACTIONS(814), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7937] = 1,
    ACTIONS(816), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7954] = 1,
    ACTIONS(818), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7971] = 1,
    ACTIONS(820), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [7988] = 1,
    ACTIONS(818), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8005] = 2,
    ACTIONS(430), 1,
      anon_sym_COLON,
    ACTIONS(428), 13,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [8024] = 1,
    ACTIONS(822), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8041] = 1,
    ACTIONS(824), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8058] = 1,
    ACTIONS(826), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8075] = 1,
    ACTIONS(822), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8092] = 1,
    ACTIONS(828), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8109] = 1,
    ACTIONS(830), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8126] = 1,
    ACTIONS(832), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8143] = 1,
    ACTIONS(834), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8160] = 1,
    ACTIONS(832), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8177] = 1,
    ACTIONS(836), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8194] = 1,
    ACTIONS(838), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8211] = 1,
    ACTIONS(840), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8228] = 1,
    ACTIONS(836), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8245] = 1,
    ACTIONS(842), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8262] = 1,
    ACTIONS(844), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8279] = 1,
    ACTIONS(846), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8296] = 1,
    ACTIONS(848), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8313] = 1,
    ACTIONS(844), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8330] = 1,
    ACTIONS(850), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8347] = 1,
    ACTIONS(852), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8364] = 1,
    ACTIONS(854), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8381] = 1,
    ACTIONS(856), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8398] = 1,
    ACTIONS(858), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8415] = 1,
    ACTIONS(860), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8432] = 1,
    ACTIONS(862), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8449] = 1,
    ACTIONS(864), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8466] = 3,
    ACTIONS(866), 1,
      anon_sym_SEMI,
    ACTIONS(378), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(868), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8487] = 1,
    ACTIONS(870), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8504] = 1,
    ACTIONS(872), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8521] = 2,
    ACTIONS(374), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8540] = 3,
    ACTIONS(876), 1,
      anon_sym_SEMI,
    ACTIONS(374), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8561] = 1,
    ACTIONS(878), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8578] = 1,
    ACTIONS(880), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8595] = 1,
    ACTIONS(882), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8612] = 1,
    ACTIONS(884), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8629] = 1,
    ACTIONS(886), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8646] = 2,
    ACTIONS(416), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(888), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8665] = 3,
    ACTIONS(890), 1,
      anon_sym_else,
    ACTIONS(790), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(792), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [8686] = 1,
    ACTIONS(892), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8703] = 1,
    ACTIONS(894), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8720] = 3,
    ACTIONS(896), 1,
      anon_sym_SEMI,
    ACTIONS(378), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(868), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [8741] = 3,
    ACTIONS(900), 1,
      anon_sym_LPAREN,
    ACTIONS(898), 4,
      anon_sym_SEMI,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(902), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8762] = 3,
    ACTIONS(904), 1,
      anon_sym_SEMI,
    ACTIONS(906), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(908), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8783] = 2,
    ACTIONS(910), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(912), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8802] = 2,
    ACTIONS(914), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(916), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8821] = 8,
    ACTIONS(918), 1,
      anon_sym_lookup,
    ACTIONS(920), 1,
      anon_sym_count,
    ACTIONS(922), 1,
      anon_sym_sum,
    ACTIONS(924), 1,
      anon_sym_average,
    ACTIONS(926), 1,
      anon_sym_min,
    ACTIONS(928), 1,
      anon_sym_max,
    STATE(844), 1,
      sym_calc_formula_value,
    STATE(899), 7,
      sym__calc_formula_expression,
      sym_lookup_formula,
      sym_count_formula,
      sym_sum_formula,
      sym_average_formula,
      sym_min_formula,
      sym_max_formula,
  [8852] = 2,
    ACTIONS(930), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(932), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8871] = 3,
    ACTIONS(934), 1,
      anon_sym_SEMI,
    ACTIONS(374), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [8892] = 9,
    ACTIONS(245), 1,
      anon_sym_LBRACK,
    ACTIONS(251), 1,
      sym_procedure_modifier,
    ACTIONS(253), 1,
      anon_sym_procedure,
    ACTIONS(265), 1,
      anon_sym_trigger,
    ACTIONS(293), 1,
      anon_sym_var,
    ACTIONS(936), 1,
      anon_sym_RBRACE,
    STATE(809), 1,
      sym_attribute_list,
    STATE(529), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
    STATE(179), 5,
      sym__codeunit_element,
      sym_onrun_trigger,
      sym_var_section,
      sym_procedure,
      aux_sym_codeunit_declaration_repeat1,
  [8925] = 2,
    ACTIONS(416), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(888), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [8944] = 1,
    ACTIONS(938), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [8961] = 2,
    ACTIONS(940), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(942), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8980] = 2,
    ACTIONS(944), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(946), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [8999] = 1,
    ACTIONS(948), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [9016] = 2,
    ACTIONS(950), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(952), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9035] = 2,
    ACTIONS(954), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(956), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9054] = 2,
    ACTIONS(958), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(960), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9073] = 2,
    ACTIONS(962), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(964), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9092] = 2,
    ACTIONS(966), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(968), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9111] = 2,
    ACTIONS(970), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(972), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9130] = 2,
    ACTIONS(974), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(976), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9149] = 2,
    ACTIONS(978), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(980), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9168] = 2,
    ACTIONS(982), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(984), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9187] = 2,
    ACTIONS(986), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(988), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9206] = 2,
    ACTIONS(990), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(992), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9225] = 2,
    ACTIONS(994), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(996), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9244] = 2,
    ACTIONS(998), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1000), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9263] = 2,
    ACTIONS(1002), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1004), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9282] = 2,
    ACTIONS(1006), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1008), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9301] = 2,
    ACTIONS(1010), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1012), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9320] = 2,
    ACTIONS(1014), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1016), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9339] = 2,
    ACTIONS(1018), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1020), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9358] = 2,
    ACTIONS(1022), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1024), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9377] = 2,
    ACTIONS(1026), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1028), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9396] = 2,
    ACTIONS(1030), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1032), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9415] = 2,
    ACTIONS(1034), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1036), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [9434] = 3,
    ACTIONS(1038), 1,
      anon_sym_LPAREN,
    ACTIONS(898), 4,
      anon_sym_SEMI,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(902), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9455] = 3,
    ACTIONS(1040), 1,
      anon_sym_SEMI,
    ACTIONS(906), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(908), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9476] = 2,
    ACTIONS(910), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(912), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9495] = 2,
    ACTIONS(914), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(916), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9514] = 2,
    ACTIONS(930), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(932), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9533] = 9,
    ACTIONS(245), 1,
      anon_sym_LBRACK,
    ACTIONS(251), 1,
      sym_procedure_modifier,
    ACTIONS(253), 1,
      anon_sym_procedure,
    ACTIONS(265), 1,
      anon_sym_trigger,
    ACTIONS(293), 1,
      anon_sym_var,
    ACTIONS(936), 1,
      anon_sym_RBRACE,
    STATE(809), 1,
      sym_attribute_list,
    STATE(529), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
    STATE(180), 5,
      sym__codeunit_element,
      sym_onrun_trigger,
      sym_var_section,
      sym_procedure,
      aux_sym_codeunit_declaration_repeat1,
  [9566] = 2,
    ACTIONS(940), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(942), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9585] = 2,
    ACTIONS(944), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(946), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9604] = 2,
    ACTIONS(950), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(952), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9623] = 2,
    ACTIONS(954), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(956), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9642] = 2,
    ACTIONS(958), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(960), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9661] = 2,
    ACTIONS(962), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(964), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9680] = 2,
    ACTIONS(966), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(968), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9699] = 2,
    ACTIONS(970), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(972), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9718] = 2,
    ACTIONS(974), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(976), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9737] = 2,
    ACTIONS(978), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(980), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9756] = 2,
    ACTIONS(982), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(984), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9775] = 2,
    ACTIONS(986), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(988), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9794] = 2,
    ACTIONS(990), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(992), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9813] = 2,
    ACTIONS(994), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(996), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9832] = 2,
    ACTIONS(998), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1000), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9851] = 2,
    ACTIONS(1002), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1004), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9870] = 2,
    ACTIONS(1006), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1008), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9889] = 2,
    ACTIONS(1010), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1012), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9908] = 2,
    ACTIONS(1014), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1016), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9927] = 2,
    ACTIONS(1018), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1020), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9946] = 2,
    ACTIONS(1022), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1024), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9965] = 2,
    ACTIONS(1026), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1028), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [9984] = 2,
    ACTIONS(1030), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1032), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10003] = 2,
    ACTIONS(1034), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1036), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10022] = 3,
    ACTIONS(1042), 1,
      anon_sym_else,
    ACTIONS(790), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(792), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10043] = 3,
    ACTIONS(1044), 1,
      anon_sym_else,
    ACTIONS(790), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(792), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10064] = 1,
    ACTIONS(1046), 14,
      anon_sym_RBRACE,
      anon_sym_TableType,
      anon_sym_trigger,
      anon_sym_Permissions,
      anon_sym_DrillDownPageId,
      anon_sym_LookupPageId,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_var,
      anon_sym_LBRACK,
      anon_sym_fields,
      anon_sym_keys,
      sym_procedure_modifier,
      anon_sym_procedure,
  [10081] = 2,
    ACTIONS(374), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 9,
      anon_sym_if,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10100] = 2,
    ACTIONS(434), 1,
      anon_sym_COLON,
    ACTIONS(432), 12,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [10118] = 2,
    ACTIONS(940), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(942), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10136] = 7,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1052), 1,
      anon_sym_COLON,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    ACTIONS(1048), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [10164] = 2,
    ACTIONS(944), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(946), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10182] = 2,
    ACTIONS(950), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(952), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10200] = 2,
    ACTIONS(954), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(956), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10218] = 8,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1058), 1,
      anon_sym_RPAREN,
    STATE(616), 1,
      aux_sym_expression_list_repeat1,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [10248] = 2,
    ACTIONS(962), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(964), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10266] = 2,
    ACTIONS(966), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(968), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10284] = 2,
    ACTIONS(970), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(972), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10302] = 2,
    ACTIONS(974), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(976), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10320] = 2,
    ACTIONS(978), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(980), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10338] = 2,
    ACTIONS(982), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(984), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10356] = 2,
    ACTIONS(986), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(988), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10374] = 2,
    ACTIONS(990), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(992), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10392] = 2,
    ACTIONS(994), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(996), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10410] = 2,
    ACTIONS(998), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1000), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10428] = 2,
    ACTIONS(1002), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1004), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10446] = 2,
    ACTIONS(1006), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1008), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10464] = 2,
    ACTIONS(1010), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1012), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10482] = 2,
    ACTIONS(1014), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1016), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10500] = 2,
    ACTIONS(1018), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1020), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10518] = 2,
    ACTIONS(1022), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1024), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10536] = 2,
    ACTIONS(1026), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1028), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10554] = 2,
    ACTIONS(1030), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1032), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10572] = 2,
    ACTIONS(1034), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1036), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [10590] = 2,
    ACTIONS(440), 1,
      anon_sym_COLON,
    ACTIONS(438), 12,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [10608] = 3,
    ACTIONS(301), 1,
      anon_sym_COLON,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(299), 10,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
  [10628] = 2,
    ACTIONS(986), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(988), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10646] = 2,
    ACTIONS(990), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(992), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10664] = 4,
    ACTIONS(745), 1,
      anon_sym_LPAREN,
    ACTIONS(1062), 1,
      anon_sym_COLON,
    STATE(63), 1,
      sym_argument_list,
    ACTIONS(1060), 10,
      anon_sym_COMMA,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_RPAREN,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
  [10686] = 8,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1064), 1,
      anon_sym_RPAREN,
    STATE(615), 1,
      aux_sym_expression_list_repeat1,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [10716] = 2,
    ACTIONS(994), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(996), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10734] = 2,
    ACTIONS(998), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1000), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10752] = 2,
    ACTIONS(1002), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1004), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10770] = 2,
    ACTIONS(1006), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1008), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10788] = 2,
    ACTIONS(1010), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1012), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10806] = 2,
    ACTIONS(1014), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1016), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10824] = 2,
    ACTIONS(1018), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1020), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10842] = 2,
    ACTIONS(1022), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1024), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10860] = 2,
    ACTIONS(1026), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1028), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10878] = 2,
    ACTIONS(1030), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1032), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10896] = 7,
    ACTIONS(918), 1,
      anon_sym_lookup,
    ACTIONS(920), 1,
      anon_sym_count,
    ACTIONS(922), 1,
      anon_sym_sum,
    ACTIONS(924), 1,
      anon_sym_average,
    ACTIONS(926), 1,
      anon_sym_min,
    ACTIONS(928), 1,
      anon_sym_max,
    STATE(853), 7,
      sym__calc_formula_expression,
      sym_lookup_formula,
      sym_count_formula,
      sym_sum_formula,
      sym_average_formula,
      sym_min_formula,
      sym_max_formula,
  [10924] = 2,
    ACTIONS(950), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(952), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10942] = 2,
    ACTIONS(1034), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1036), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10960] = 3,
    ACTIONS(1066), 1,
      anon_sym_SEMI,
    ACTIONS(378), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(868), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10980] = 2,
    ACTIONS(374), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [10998] = 3,
    ACTIONS(1068), 1,
      anon_sym_SEMI,
    ACTIONS(374), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11018] = 2,
    ACTIONS(416), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(888), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11036] = 2,
    ACTIONS(954), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(956), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11054] = 2,
    ACTIONS(958), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(960), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11072] = 2,
    ACTIONS(962), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(964), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11090] = 3,
    ACTIONS(1070), 1,
      anon_sym_LPAREN,
    ACTIONS(898), 4,
      anon_sym_SEMI,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(902), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11110] = 2,
    ACTIONS(966), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(968), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11128] = 3,
    ACTIONS(1072), 1,
      anon_sym_SEMI,
    ACTIONS(906), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(908), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11148] = 2,
    ACTIONS(910), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(912), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11166] = 2,
    ACTIONS(914), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(916), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11184] = 2,
    ACTIONS(970), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(972), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11202] = 2,
    ACTIONS(974), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(976), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11220] = 2,
    ACTIONS(930), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(932), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11238] = 2,
    ACTIONS(978), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(980), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11256] = 2,
    ACTIONS(982), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(984), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11274] = 2,
    ACTIONS(940), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(942), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11292] = 8,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1074), 1,
      anon_sym_COLON,
    STATE(659), 1,
      aux_sym_expression_list_repeat1,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [11322] = 3,
    ACTIONS(1076), 1,
      anon_sym_LPAREN,
    ACTIONS(898), 4,
      anon_sym_SEMI,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(902), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11342] = 3,
    ACTIONS(1078), 1,
      anon_sym_SEMI,
    ACTIONS(906), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(908), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11362] = 2,
    ACTIONS(910), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(912), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11380] = 2,
    ACTIONS(914), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(916), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11398] = 3,
    ACTIONS(1080), 1,
      anon_sym_SEMI,
    ACTIONS(378), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(868), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11418] = 2,
    ACTIONS(374), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11436] = 3,
    ACTIONS(1082), 1,
      anon_sym_SEMI,
    ACTIONS(374), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11456] = 2,
    ACTIONS(416), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(888), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11474] = 8,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1084), 1,
      anon_sym_RPAREN,
    STATE(635), 1,
      aux_sym_expression_list_repeat1,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [11504] = 8,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1086), 1,
      anon_sym_RPAREN,
    STATE(694), 1,
      aux_sym_expression_list_repeat1,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [11534] = 8,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1088), 1,
      anon_sym_RPAREN,
    STATE(626), 1,
      aux_sym_expression_list_repeat1,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [11564] = 8,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1090), 1,
      anon_sym_RPAREN,
    STATE(642), 1,
      aux_sym_expression_list_repeat1,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [11594] = 2,
    ACTIONS(930), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(932), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11612] = 2,
    ACTIONS(944), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(946), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
      anon_sym_repeat,
      anon_sym_case,
      anon_sym_exit,
  [11630] = 2,
    ACTIONS(958), 5,
      anon_sym_SEMI,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(960), 8,
      anon_sym_if,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_repeat,
      anon_sym_until,
      anon_sym_case,
      anon_sym_exit,
  [11648] = 1,
    ACTIONS(1092), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11663] = 1,
    ACTIONS(1094), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11678] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    ACTIONS(1096), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [11703] = 1,
    ACTIONS(1098), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11718] = 1,
    ACTIONS(1100), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11733] = 1,
    ACTIONS(1102), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11748] = 1,
    ACTIONS(1104), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11763] = 3,
    ACTIONS(1106), 1,
      anon_sym_LPAREN,
    STATE(448), 1,
      sym_argument_list,
    ACTIONS(1060), 10,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [11782] = 1,
    ACTIONS(1108), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11797] = 3,
    ACTIONS(1106), 1,
      anon_sym_LPAREN,
    STATE(443), 1,
      sym_argument_list,
    ACTIONS(408), 10,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [11816] = 2,
    STATE(138), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(299), 10,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [11833] = 12,
    ACTIONS(1110), 1,
      anon_sym_OnInsert,
    ACTIONS(1112), 1,
      anon_sym_OnModify,
    ACTIONS(1114), 1,
      anon_sym_OnDelete,
    ACTIONS(1116), 1,
      anon_sym_OnRename,
    ACTIONS(1118), 1,
      anon_sym_OnValidate,
    ACTIONS(1120), 1,
      anon_sym_OnAfterGetRecord,
    ACTIONS(1122), 1,
      anon_sym_OnAfterInsertEvent,
    ACTIONS(1124), 1,
      anon_sym_OnAfterModifyEvent,
    ACTIONS(1126), 1,
      anon_sym_OnAfterDeleteEvent,
    ACTIONS(1128), 1,
      anon_sym_OnBeforeInsertEvent,
    ACTIONS(1130), 1,
      anon_sym_OnBeforeModifyEvent,
    ACTIONS(1132), 1,
      anon_sym_OnBeforeDeleteEvent,
  [11870] = 1,
    ACTIONS(1134), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11885] = 1,
    ACTIONS(1136), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11900] = 1,
    ACTIONS(1138), 12,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_TableRelation,
      anon_sym_FieldClass,
      anon_sym_CalcFormula,
      anon_sym_BlankZero,
      anon_sym_Editable,
      anon_sym_OptionMembers,
      anon_sym_OptionCaption,
      anon_sym_DataClassification,
      anon_sym_Caption,
      anon_sym_DecimalPlaces,
  [11915] = 6,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1140), 1,
      anon_sym_DOT,
    ACTIONS(1142), 1,
      anon_sym_of,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(138), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [11939] = 6,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1140), 1,
      anon_sym_DOT,
    ACTIONS(1144), 1,
      anon_sym_of,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(138), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [11963] = 1,
    ACTIONS(1146), 11,
      anon_sym_COMMA,
      anon_sym_Temporary,
      anon_sym_SEMI,
      anon_sym_DOT,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      anon_sym_where,
      anon_sym_else,
      sym_temporary,
      anon_sym_begin,
  [11977] = 5,
    ACTIONS(745), 1,
      anon_sym_LPAREN,
    ACTIONS(1148), 1,
      anon_sym_DOT,
    ACTIONS(1150), 1,
      anon_sym_COLON_EQ,
    STATE(63), 1,
      sym_argument_list,
    ACTIONS(1060), 7,
      anon_sym_EQ,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
  [11999] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1152), 1,
      anon_sym_RPAREN,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12023] = 5,
    ACTIONS(1150), 1,
      anon_sym_COLON_EQ,
    ACTIONS(1154), 1,
      anon_sym_DOT,
    ACTIONS(1156), 1,
      anon_sym_LPAREN,
    STATE(109), 1,
      sym_argument_list,
    ACTIONS(1060), 7,
      anon_sym_EQ,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
  [12045] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1158), 1,
      anon_sym_RPAREN,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12069] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1160), 1,
      anon_sym_RPAREN,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12093] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1162), 1,
      anon_sym_RPAREN,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12117] = 5,
    ACTIONS(1150), 1,
      anon_sym_COLON_EQ,
    ACTIONS(1164), 1,
      anon_sym_DOT,
    ACTIONS(1166), 1,
      anon_sym_LPAREN,
    STATE(74), 1,
      sym_argument_list,
    ACTIONS(1060), 7,
      anon_sym_EQ,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
  [12139] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1168), 1,
      anon_sym_RPAREN,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12163] = 3,
    ACTIONS(1156), 1,
      anon_sym_LPAREN,
    STATE(106), 1,
      sym_argument_list,
    ACTIONS(408), 9,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_EQ,
      anon_sym_COLON_COLON,
  [12181] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1170), 1,
      anon_sym_RPAREN,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12205] = 5,
    ACTIONS(1150), 1,
      anon_sym_COLON_EQ,
    ACTIONS(1172), 1,
      anon_sym_DOT,
    ACTIONS(1174), 1,
      anon_sym_LPAREN,
    STATE(91), 1,
      sym_argument_list,
    ACTIONS(1060), 7,
      anon_sym_EQ,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
  [12227] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1176), 1,
      anon_sym_RPAREN,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12251] = 3,
    ACTIONS(1166), 1,
      anon_sym_LPAREN,
    STATE(85), 1,
      sym_argument_list,
    ACTIONS(408), 9,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_EQ,
      anon_sym_COLON_COLON,
  [12269] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1178), 1,
      anon_sym_RPAREN,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12293] = 6,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1180), 1,
      anon_sym_RPAREN,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12317] = 3,
    ACTIONS(1174), 1,
      anon_sym_LPAREN,
    STATE(98), 1,
      sym_argument_list,
    ACTIONS(408), 9,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_EQ,
      anon_sym_COLON_COLON,
  [12335] = 2,
    ACTIONS(1184), 2,
      anon_sym_LT,
      anon_sym_GT,
    ACTIONS(1182), 9,
      anon_sym_EQ,
      anon_sym_SEMI,
      anon_sym_RPAREN,
      anon_sym_where,
      anon_sym_else,
      anon_sym_LT_GT,
      anon_sym_LT_EQ,
      anon_sym_GT_EQ,
      anon_sym_IN,
  [12351] = 6,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1140), 1,
      anon_sym_DOT,
    ACTIONS(1186), 1,
      anon_sym_then,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(138), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12375] = 11,
    ACTIONS(1188), 1,
      anon_sym_Get,
    ACTIONS(1190), 1,
      anon_sym_FindSet,
    ACTIONS(1192), 1,
      anon_sym_Insert,
    ACTIONS(1194), 1,
      anon_sym_Modify,
    ACTIONS(1196), 1,
      anon_sym_Delete,
    ACTIONS(1198), 1,
      anon_sym_SetRange,
    ACTIONS(1200), 1,
      anon_sym_SetFilter,
    ACTIONS(1202), 1,
      anon_sym_Reset,
    ACTIONS(1204), 1,
      anon_sym_FindFirst,
    ACTIONS(1206), 1,
      anon_sym_FindLast,
    ACTIONS(1208), 1,
      anon_sym_Next,
  [12409] = 6,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1140), 1,
      anon_sym_DOT,
    ACTIONS(1210), 1,
      anon_sym_then,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(138), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12433] = 11,
    ACTIONS(1212), 1,
      anon_sym_Get,
    ACTIONS(1214), 1,
      anon_sym_FindSet,
    ACTIONS(1216), 1,
      anon_sym_Insert,
    ACTIONS(1218), 1,
      anon_sym_Modify,
    ACTIONS(1220), 1,
      anon_sym_Delete,
    ACTIONS(1222), 1,
      anon_sym_SetRange,
    ACTIONS(1224), 1,
      anon_sym_SetFilter,
    ACTIONS(1226), 1,
      anon_sym_Reset,
    ACTIONS(1228), 1,
      anon_sym_FindFirst,
    ACTIONS(1230), 1,
      anon_sym_FindLast,
    ACTIONS(1232), 1,
      anon_sym_Next,
  [12467] = 6,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1140), 1,
      anon_sym_DOT,
    ACTIONS(1234), 1,
      anon_sym_then,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(138), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12491] = 11,
    ACTIONS(1236), 1,
      anon_sym_Get,
    ACTIONS(1238), 1,
      anon_sym_FindSet,
    ACTIONS(1240), 1,
      anon_sym_Insert,
    ACTIONS(1242), 1,
      anon_sym_Modify,
    ACTIONS(1244), 1,
      anon_sym_Delete,
    ACTIONS(1246), 1,
      anon_sym_SetRange,
    ACTIONS(1248), 1,
      anon_sym_SetFilter,
    ACTIONS(1250), 1,
      anon_sym_Reset,
    ACTIONS(1252), 1,
      anon_sym_FindFirst,
    ACTIONS(1254), 1,
      anon_sym_FindLast,
    ACTIONS(1256), 1,
      anon_sym_Next,
  [12525] = 11,
    ACTIONS(1258), 1,
      anon_sym_Get,
    ACTIONS(1260), 1,
      anon_sym_FindSet,
    ACTIONS(1262), 1,
      anon_sym_Insert,
    ACTIONS(1264), 1,
      anon_sym_Modify,
    ACTIONS(1266), 1,
      anon_sym_Delete,
    ACTIONS(1268), 1,
      anon_sym_SetRange,
    ACTIONS(1270), 1,
      anon_sym_SetFilter,
    ACTIONS(1272), 1,
      anon_sym_Reset,
    ACTIONS(1274), 1,
      anon_sym_FindFirst,
    ACTIONS(1276), 1,
      anon_sym_FindLast,
    ACTIONS(1278), 1,
      anon_sym_Next,
  [12559] = 6,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1140), 1,
      anon_sym_DOT,
    ACTIONS(1280), 1,
      anon_sym_of,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(138), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12583] = 6,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1140), 1,
      anon_sym_DOT,
    ACTIONS(1282), 1,
      anon_sym_then,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(138), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12607] = 6,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1140), 1,
      anon_sym_DOT,
    ACTIONS(1284), 1,
      anon_sym_of,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(138), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12631] = 5,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1286), 1,
      anon_sym_DOT,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12652] = 1,
    ACTIONS(366), 10,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [12665] = 1,
    ACTIONS(327), 10,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [12678] = 3,
    ACTIONS(1288), 1,
      anon_sym_SEMI,
    ACTIONS(378), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(868), 5,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
  [12695] = 3,
    ACTIONS(1290), 1,
      anon_sym_SEMI,
    ACTIONS(374), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 5,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
  [12712] = 5,
    ACTIONS(1050), 1,
      anon_sym_DOT,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12733] = 1,
    ACTIONS(404), 10,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [12746] = 5,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1292), 1,
      anon_sym_DOT,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12767] = 1,
    ACTIONS(323), 10,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [12780] = 1,
    ACTIONS(370), 10,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_of,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
      anon_sym_then,
  [12793] = 5,
    ACTIONS(1054), 1,
      anon_sym_COLON_COLON,
    ACTIONS(1294), 1,
      anon_sym_DOT,
    ACTIONS(303), 2,
      anon_sym_EQ,
      anon_sym_LT_GT,
    STATE(144), 2,
      sym_comparison_operator,
      sym_arithmetic_operator,
    ACTIONS(311), 4,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
  [12814] = 2,
    ACTIONS(374), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(874), 5,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
  [12828] = 2,
    ACTIONS(1150), 1,
      anon_sym_COLON_EQ,
    ACTIONS(422), 8,
      anon_sym_EQ,
      anon_sym_DOT,
      anon_sym_LT_GT,
      anon_sym_PLUS,
      anon_sym_DASH,
      anon_sym_STAR,
      anon_sym_SLASH,
      anon_sym_COLON_COLON,
  [12842] = 2,
    ACTIONS(1296), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(1298), 5,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
  [12856] = 9,
    ACTIONS(1300), 1,
      anon_sym_SEMI,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    STATE(175), 1,
      sym_code_block,
    STATE(567), 1,
      sym__procedure_return_specification,
    STATE(791), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [12884] = 2,
    ACTIONS(416), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
    ACTIONS(888), 5,
      anon_sym_else,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
      anon_sym_end,
  [12898] = 9,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    ACTIONS(1310), 1,
      anon_sym_SEMI,
    STATE(187), 1,
      sym_code_block,
    STATE(599), 1,
      sym__procedure_return_specification,
    STATE(727), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [12926] = 7,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1312), 1,
      anon_sym_if,
    ACTIONS(1314), 1,
      sym_identifier,
    ACTIONS(1316), 1,
      sym_integer,
    STATE(414), 1,
      sym__quoted_identifier,
    STATE(535), 1,
      sym__table_reference,
    STATE(779), 3,
      sym__simple_table_relation,
      sym_conditional_table_relation,
      sym__table_relation_body,
  [12950] = 9,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    ACTIONS(1318), 1,
      anon_sym_SEMI,
    STATE(176), 1,
      sym_code_block,
    STATE(560), 1,
      sym__procedure_return_specification,
    STATE(794), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [12978] = 4,
    ACTIONS(1320), 1,
      sym_identifier,
    ACTIONS(598), 2,
      anon_sym_RBRACE,
      anon_sym_LBRACK,
    STATE(462), 2,
      sym_variable_declaration,
      aux_sym_var_section_repeat1,
    ACTIONS(600), 4,
      anon_sym_trigger,
      anon_sym_var,
      sym_procedure_modifier,
      anon_sym_procedure,
  [12996] = 4,
    ACTIONS(1322), 1,
      sym_identifier,
    ACTIONS(610), 2,
      anon_sym_RBRACE,
      anon_sym_LBRACK,
    STATE(462), 2,
      sym_variable_declaration,
      aux_sym_var_section_repeat1,
    ACTIONS(612), 4,
      anon_sym_trigger,
      anon_sym_var,
      sym_procedure_modifier,
      anon_sym_procedure,
  [13014] = 9,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    ACTIONS(1325), 1,
      anon_sym_SEMI,
    STATE(201), 1,
      sym_code_block,
    STATE(589), 1,
      sym__procedure_return_specification,
    STATE(751), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13042] = 9,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    ACTIONS(1327), 1,
      anon_sym_SEMI,
    STATE(316), 1,
      sym_code_block,
    STATE(573), 1,
      sym__procedure_return_specification,
    STATE(753), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13070] = 7,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1312), 1,
      anon_sym_if,
    ACTIONS(1314), 1,
      sym_identifier,
    ACTIONS(1316), 1,
      sym_integer,
    STATE(414), 1,
      sym__quoted_identifier,
    STATE(535), 1,
      sym__table_reference,
    STATE(737), 3,
      sym__simple_table_relation,
      sym_conditional_table_relation,
      sym__table_relation_body,
  [13094] = 9,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    ACTIONS(1329), 1,
      anon_sym_SEMI,
    STATE(188), 1,
      sym_code_block,
    STATE(555), 1,
      sym__procedure_return_specification,
    STATE(731), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13122] = 9,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    ACTIONS(1331), 1,
      anon_sym_SEMI,
    STATE(178), 1,
      sym_code_block,
    STATE(540), 1,
      sym__procedure_return_specification,
    STATE(822), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13150] = 8,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1312), 1,
      anon_sym_if,
    ACTIONS(1314), 1,
      sym_identifier,
    ACTIONS(1316), 1,
      sym_integer,
    STATE(414), 1,
      sym__quoted_identifier,
    STATE(535), 1,
      sym__table_reference,
    STATE(989), 1,
      sym_table_relation_value,
    STATE(875), 2,
      sym__simple_table_relation,
      sym_conditional_table_relation,
  [13176] = 8,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1312), 1,
      anon_sym_if,
    ACTIONS(1314), 1,
      sym_identifier,
    ACTIONS(1316), 1,
      sym_integer,
    STATE(414), 1,
      sym__quoted_identifier,
    STATE(535), 1,
      sym__table_reference,
    STATE(844), 1,
      sym_table_relation_value,
    STATE(875), 2,
      sym__simple_table_relation,
      sym_conditional_table_relation,
  [13202] = 9,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    ACTIONS(1333), 1,
      anon_sym_SEMI,
    STATE(181), 1,
      sym_code_block,
    STATE(541), 1,
      sym__procedure_return_specification,
    STATE(715), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13230] = 8,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    STATE(213), 1,
      sym_code_block,
    STATE(546), 1,
      sym__procedure_return_specification,
    STATE(774), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13255] = 2,
    STATE(844), 1,
      sym_data_classification_value,
    ACTIONS(1335), 7,
      anon_sym_CustomerContent,
      anon_sym_EndUserIdentifiableInformation,
      anon_sym_AccountData,
      anon_sym_EndUserPseudonymousIdentifiers,
      anon_sym_OrganizationIdentifiableInformation,
      anon_sym_SystemMetadata,
      anon_sym_ToBeClassified,
  [13268] = 2,
    ACTIONS(1339), 1,
      anon_sym_Temporary,
    ACTIONS(1337), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13281] = 3,
    STATE(935), 1,
      sym_filter_operator,
    ACTIONS(1343), 2,
      anon_sym_LT,
      anon_sym_GT,
    ACTIONS(1341), 5,
      anon_sym_EQ,
      anon_sym_LT_GT,
      anon_sym_LT_EQ,
      anon_sym_GT_EQ,
      anon_sym_IN,
  [13296] = 8,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    STATE(183), 1,
      sym_code_block,
    STATE(588), 1,
      sym__procedure_return_specification,
    STATE(721), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13321] = 8,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    STATE(188), 1,
      sym_code_block,
    STATE(572), 1,
      sym__procedure_return_specification,
    STATE(731), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13346] = 3,
    STATE(621), 1,
      sym_filter_operator,
    ACTIONS(1343), 2,
      anon_sym_LT,
      anon_sym_GT,
    ACTIONS(1341), 5,
      anon_sym_EQ,
      anon_sym_LT_GT,
      anon_sym_LT_EQ,
      anon_sym_GT_EQ,
      anon_sym_IN,
  [13361] = 8,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    STATE(201), 1,
      sym_code_block,
    STATE(574), 1,
      sym__procedure_return_specification,
    STATE(751), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13386] = 8,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    STATE(203), 1,
      sym_code_block,
    STATE(603), 1,
      sym__procedure_return_specification,
    STATE(755), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13411] = 2,
    ACTIONS(1347), 1,
      anon_sym_LBRACK,
    ACTIONS(1345), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13424] = 2,
    STATE(991), 1,
      sym_data_classification_value,
    ACTIONS(1335), 7,
      anon_sym_CustomerContent,
      anon_sym_EndUserIdentifiableInformation,
      anon_sym_AccountData,
      anon_sym_EndUserPseudonymousIdentifiers,
      anon_sym_OrganizationIdentifiableInformation,
      anon_sym_SystemMetadata,
      anon_sym_ToBeClassified,
  [13437] = 8,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    STATE(176), 1,
      sym_code_block,
    STATE(537), 1,
      sym__procedure_return_specification,
    STATE(794), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13462] = 8,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    STATE(193), 1,
      sym_code_block,
    STATE(538), 1,
      sym__procedure_return_specification,
    STATE(747), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13487] = 8,
    ACTIONS(1302), 1,
      anon_sym_COLON,
    ACTIONS(1304), 1,
      anon_sym_var,
    ACTIONS(1306), 1,
      sym_identifier,
    ACTIONS(1308), 1,
      anon_sym_begin,
    STATE(181), 1,
      sym_code_block,
    STATE(533), 1,
      sym__procedure_return_specification,
    STATE(715), 1,
      sym_var_section,
    STATE(852), 1,
      sym_return_value,
  [13512] = 1,
    ACTIONS(1349), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13522] = 1,
    ACTIONS(1351), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13532] = 1,
    ACTIONS(1353), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13542] = 4,
    ACTIONS(1355), 1,
      ts_builtin_sym_end,
    ACTIONS(1357), 1,
      anon_sym_table,
    ACTIONS(1360), 1,
      anon_sym_codeunit,
    STATE(488), 4,
      sym__object,
      sym_table_declaration,
      sym_codeunit_declaration,
      aux_sym_source_file_repeat1,
  [13558] = 2,
    ACTIONS(735), 2,
      anon_sym_RBRACE,
      anon_sym_LBRACK,
    ACTIONS(737), 5,
      anon_sym_trigger,
      anon_sym_var,
      sym_procedure_modifier,
      anon_sym_procedure,
      sym_identifier,
  [13570] = 2,
    ACTIONS(739), 2,
      anon_sym_RBRACE,
      anon_sym_LBRACK,
    ACTIONS(741), 5,
      anon_sym_trigger,
      anon_sym_var,
      sym_procedure_modifier,
      anon_sym_procedure,
      sym_identifier,
  [13582] = 4,
    ACTIONS(5), 1,
      anon_sym_table,
    ACTIONS(7), 1,
      anon_sym_codeunit,
    ACTIONS(1363), 1,
      ts_builtin_sym_end,
    STATE(488), 4,
      sym__object,
      sym_table_declaration,
      sym_codeunit_declaration,
      aux_sym_source_file_repeat1,
  [13598] = 1,
    ACTIONS(1365), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13608] = 1,
    ACTIONS(1367), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13618] = 1,
    ACTIONS(1369), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13628] = 1,
    ACTIONS(1371), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13638] = 1,
    ACTIONS(1373), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13648] = 1,
    ACTIONS(1375), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13658] = 2,
    ACTIONS(1379), 3,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(1377), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
  [13670] = 1,
    ACTIONS(1381), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13680] = 2,
    ACTIONS(1385), 3,
      sym_identifier,
      anon_sym_true,
      anon_sym_false,
    ACTIONS(1383), 4,
      anon_sym_LPAREN,
      anon_sym_DQUOTE,
      sym_integer,
      sym_string_literal,
  [13692] = 1,
    ACTIONS(1387), 7,
      anon_sym_COMMA,
      anon_sym_SEMI,
      anon_sym_var,
      anon_sym_RBRACK,
      anon_sym_RPAREN,
      sym_temporary,
      anon_sym_begin,
  [13702] = 6,
    ACTIONS(1389), 1,
      anon_sym_var,
    ACTIONS(1391), 1,
      anon_sym_RPAREN,
    ACTIONS(1393), 1,
      sym_identifier,
    STATE(618), 1,
      sym_parameter,
    STATE(835), 1,
      sym_parameter_list,
    STATE(837), 1,
      sym_modifier,
  [13721] = 6,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1395), 1,
      sym_identifier,
    STATE(431), 1,
      sym__quoted_identifier,
    STATE(693), 1,
      sym_where_condition,
    STATE(873), 1,
      sym__field_reference,
    STATE(874), 1,
      sym_where_conditions,
  [13740] = 1,
    ACTIONS(1397), 6,
      anon_sym_RBRACE,
      anon_sym_trigger,
      anon_sym_var,
      anon_sym_LBRACK,
      sym_procedure_modifier,
      anon_sym_procedure,
  [13749] = 6,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1399), 1,
      sym_identifier,
    STATE(625), 1,
      sym_lookup_where_condition,
    STATE(758), 1,
      sym__quoted_identifier,
    STATE(870), 1,
      sym__condition_field_reference,
    STATE(871), 1,
      sym_lookup_where_conditions,
  [13768] = 6,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1401), 1,
      sym_identifier,
    ACTIONS(1403), 1,
      sym_string_literal,
    STATE(676), 1,
      sym_option_member,
    STATE(769), 1,
      sym__quoted_identifier,
    STATE(844), 1,
      sym_option_members_value,
  [13787] = 6,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1395), 1,
      sym_identifier,
    STATE(431), 1,
      sym__quoted_identifier,
    STATE(477), 1,
      sym__field_reference,
    STATE(689), 1,
      sym_filter_condition,
    STATE(1077), 1,
      sym_filter_conditions,
  [13806] = 6,
    ACTIONS(1389), 1,
      anon_sym_var,
    ACTIONS(1393), 1,
      sym_identifier,
    ACTIONS(1405), 1,
      anon_sym_RPAREN,
    STATE(618), 1,
      sym_parameter,
    STATE(837), 1,
      sym_modifier,
    STATE(872), 1,
      sym_parameter_list,
  [13825] = 6,
    ACTIONS(1389), 1,
      anon_sym_var,
    ACTIONS(1393), 1,
      sym_identifier,
    ACTIONS(1407), 1,
      anon_sym_RPAREN,
    STATE(618), 1,
      sym_parameter,
    STATE(837), 1,
      sym_modifier,
    STATE(846), 1,
      sym_parameter_list,
  [13844] = 6,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1395), 1,
      sym_identifier,
    STATE(431), 1,
      sym__quoted_identifier,
    STATE(477), 1,
      sym__field_reference,
    STATE(689), 1,
      sym_filter_condition,
    STATE(864), 1,
      sym_filter_conditions,
  [13863] = 6,
    ACTIONS(1389), 1,
      anon_sym_var,
    ACTIONS(1393), 1,
      sym_identifier,
    ACTIONS(1409), 1,
      anon_sym_RPAREN,
    STATE(618), 1,
      sym_parameter,
    STATE(837), 1,
      sym_modifier,
    STATE(1053), 1,
      sym_parameter_list,
  [13882] = 5,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1399), 1,
      sym_identifier,
    STATE(758), 1,
      sym__quoted_identifier,
    STATE(807), 1,
      sym_lookup_where_condition,
    STATE(870), 1,
      sym__condition_field_reference,
  [13898] = 5,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1395), 1,
      sym_identifier,
    STATE(431), 1,
      sym__quoted_identifier,
    STATE(813), 1,
      sym_where_condition,
    STATE(873), 1,
      sym__field_reference,
  [13914] = 5,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1411), 1,
      anon_sym_FILTER,
    ACTIONS(1413), 1,
      anon_sym_UPPERLIMIT,
    ACTIONS(1415), 1,
      sym_identifier,
    STATE(1015), 1,
      sym__quoted_identifier,
  [13930] = 2,
    STATE(880), 1,
      sym_table_type_value,
    ACTIONS(1417), 4,
      anon_sym_Normal,
      anon_sym_Temporary,
      anon_sym_External,
      anon_sym_System,
  [13940] = 4,
    ACTIONS(1419), 1,
      anon_sym_DQUOTE,
    ACTIONS(1421), 1,
      aux_sym__quoted_identifier_token1,
    STATE(518), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1423), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [13954] = 4,
    ACTIONS(1421), 1,
      aux_sym__quoted_identifier_token1,
    ACTIONS(1425), 1,
      anon_sym_DQUOTE,
    STATE(518), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1423), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [13968] = 4,
    ACTIONS(1427), 1,
      anon_sym_DQUOTE,
    ACTIONS(1429), 1,
      aux_sym__quoted_identifier_token1,
    STATE(518), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1432), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [13982] = 5,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1395), 1,
      sym_identifier,
    STATE(431), 1,
      sym__quoted_identifier,
    STATE(876), 1,
      sym__field_reference,
    STATE(877), 1,
      sym_table_relation_condition,
  [13998] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    STATE(414), 1,
      sym__quoted_identifier,
    STATE(653), 1,
      sym__table_reference,
    ACTIONS(1316), 2,
      sym_identifier,
      sym_integer,
  [14012] = 5,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1435), 1,
      sym_identifier,
    STATE(690), 1,
      sym_key_field,
    STATE(714), 1,
      sym__quoted_identifier,
    STATE(851), 1,
      sym_key_field_list,
  [14028] = 5,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1395), 1,
      sym_identifier,
    STATE(431), 1,
      sym__quoted_identifier,
    STATE(477), 1,
      sym__field_reference,
    STATE(757), 1,
      sym_filter_condition,
  [14044] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    STATE(414), 1,
      sym__quoted_identifier,
    STATE(473), 1,
      sym__table_reference,
    ACTIONS(1316), 2,
      sym_identifier,
      sym_integer,
  [14058] = 4,
    ACTIONS(1421), 1,
      aux_sym__quoted_identifier_token1,
    ACTIONS(1437), 1,
      anon_sym_DQUOTE,
    STATE(518), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1423), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [14072] = 3,
    ACTIONS(1439), 1,
      anon_sym_LBRACK,
    ACTIONS(1442), 2,
      sym_procedure_modifier,
      anon_sym_procedure,
    STATE(525), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
  [14084] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    STATE(495), 1,
      sym__quoted_identifier,
    STATE(496), 1,
      sym_query_type_value,
    ACTIONS(1444), 2,
      sym_identifier,
      sym_integer,
  [14098] = 4,
    ACTIONS(1421), 1,
      aux_sym__quoted_identifier_token1,
    ACTIONS(1446), 1,
      anon_sym_DQUOTE,
    STATE(518), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1423), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [14112] = 4,
    ACTIONS(1421), 1,
      aux_sym__quoted_identifier_token1,
    ACTIONS(1448), 1,
      anon_sym_DQUOTE,
    STATE(518), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1423), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [14126] = 3,
    ACTIONS(245), 1,
      anon_sym_LBRACK,
    ACTIONS(1450), 2,
      sym_procedure_modifier,
      anon_sym_procedure,
    STATE(525), 2,
      sym_attribute,
      aux_sym_attribute_list_repeat1,
  [14138] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    STATE(844), 1,
      sym_page_id_value,
    STATE(861), 1,
      sym__quoted_identifier,
    ACTIONS(1452), 2,
      sym_identifier,
      sym_integer,
  [14152] = 5,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1401), 1,
      sym_identifier,
    ACTIONS(1454), 1,
      sym_string_literal,
    STATE(698), 1,
      sym_option_member,
    STATE(769), 1,
      sym__quoted_identifier,
  [14168] = 3,
    ACTIONS(1456), 1,
      aux_sym__quoted_identifier_token1,
    STATE(524), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1458), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [14179] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(194), 1,
      sym_code_block,
    STATE(745), 1,
      sym_var_section,
  [14192] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1395), 1,
      sym_identifier,
    STATE(431), 1,
      sym__quoted_identifier,
    STATE(651), 1,
      sym__field_reference,
  [14205] = 3,
    ACTIONS(1466), 1,
      anon_sym_DOT,
    ACTIONS(1468), 1,
      anon_sym_where,
    ACTIONS(1464), 2,
      anon_sym_SEMI,
      anon_sym_else,
  [14216] = 3,
    ACTIONS(1470), 1,
      anon_sym_RPAREN,
    STATE(759), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14227] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(184), 1,
      sym_code_block,
    STATE(717), 1,
      sym_var_section,
  [14240] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(210), 1,
      sym_code_block,
    STATE(770), 1,
      sym_var_section,
  [14253] = 3,
    ACTIONS(1474), 1,
      anon_sym_COMMA,
    STATE(539), 1,
      aux_sym_expression_list_repeat1,
    ACTIONS(1048), 2,
      anon_sym_COLON,
      anon_sym_RPAREN,
  [14264] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(189), 1,
      sym_code_block,
    STATE(734), 1,
      sym_var_section,
  [14277] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(196), 1,
      sym_code_block,
    STATE(748), 1,
      sym_var_section,
  [14290] = 3,
    ACTIONS(1477), 1,
      anon_sym_RPAREN,
    STATE(760), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14301] = 3,
    ACTIONS(1479), 1,
      anon_sym_RPAREN,
    STATE(882), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14312] = 3,
    ACTIONS(1481), 1,
      anon_sym_RPAREN,
    STATE(884), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14323] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1483), 1,
      sym_identifier,
    STATE(761), 1,
      sym_field_reference,
    STATE(883), 1,
      sym__quoted_identifier,
  [14336] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(224), 1,
      sym_code_block,
    STATE(803), 1,
      sym_var_section,
  [14349] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1485), 1,
      sym_identifier,
    STATE(1049), 1,
      sym_object_name,
    STATE(1059), 1,
      sym__quoted_identifier,
  [14362] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1487), 1,
      sym_identifier,
    STATE(965), 2,
      sym__table_identifier,
      sym__quoted_identifier,
  [14373] = 3,
    ACTIONS(1489), 1,
      anon_sym_RPAREN,
    STATE(784), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14384] = 3,
    ACTIONS(1491), 1,
      anon_sym_RPAREN,
    STATE(785), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14395] = 3,
    ACTIONS(1493), 1,
      anon_sym_RPAREN,
    STATE(952), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14406] = 3,
    ACTIONS(1495), 1,
      anon_sym_RPAREN,
    STATE(953), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14417] = 3,
    ACTIONS(600), 1,
      anon_sym_begin,
    ACTIONS(1497), 1,
      sym_identifier,
    STATE(554), 2,
      sym_variable_declaration,
      aux_sym_var_section_repeat1,
  [14428] = 3,
    ACTIONS(612), 1,
      anon_sym_begin,
    ACTIONS(1499), 1,
      sym_identifier,
    STATE(554), 2,
      sym_variable_declaration,
      aux_sym_var_section_repeat1,
  [14439] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(206), 1,
      sym_code_block,
    STATE(756), 1,
      sym_var_section,
  [14452] = 3,
    ACTIONS(1502), 1,
      anon_sym_RBRACE,
    ACTIONS(1504), 1,
      anon_sym_field,
    STATE(583), 2,
      sym_field_declaration,
      aux_sym_fields_repeat1,
  [14463] = 3,
    ACTIONS(1506), 1,
      anon_sym_RBRACE,
    ACTIONS(1508), 1,
      anon_sym_key,
    STATE(607), 2,
      sym_key_declaration,
      aux_sym_keys_repeat1,
  [14474] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1483), 1,
      sym_identifier,
    STATE(654), 1,
      sym_field_reference,
    STATE(883), 1,
      sym__quoted_identifier,
  [14487] = 3,
    ACTIONS(1510), 1,
      aux_sym__quoted_identifier_token1,
    STATE(516), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1512), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [14498] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(186), 1,
      sym_code_block,
    STATE(723), 1,
      sym_var_section,
  [14511] = 3,
    STATE(844), 1,
      sym_editable_value,
    STATE(909), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14522] = 3,
    ACTIONS(1514), 1,
      anon_sym_RPAREN,
    STATE(797), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14533] = 3,
    ACTIONS(1516), 1,
      anon_sym_RPAREN,
    STATE(798), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14544] = 3,
    ACTIONS(1518), 1,
      anon_sym_RPAREN,
    STATE(993), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14555] = 3,
    ACTIONS(1520), 1,
      anon_sym_RPAREN,
    STATE(994), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14566] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    STATE(1015), 1,
      sym__quoted_identifier,
    ACTIONS(1522), 2,
      sym_identifier,
      sym_string_literal,
  [14577] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(182), 1,
      sym_code_block,
    STATE(716), 1,
      sym_var_section,
  [14590] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1524), 1,
      anon_sym_FILTER,
    ACTIONS(1526), 1,
      sym_identifier,
    STATE(1114), 1,
      sym__quoted_identifier,
  [14603] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1483), 1,
      sym_identifier,
    STATE(660), 1,
      sym_field_reference,
    STATE(883), 1,
      sym__quoted_identifier,
  [14616] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1485), 1,
      sym_identifier,
    STATE(1057), 1,
      sym_object_name,
    STATE(1059), 1,
      sym__quoted_identifier,
  [14629] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1399), 1,
      sym_identifier,
    STATE(758), 1,
      sym__quoted_identifier,
    STATE(1116), 1,
      sym__condition_field_reference,
  [14642] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(204), 1,
      sym_code_block,
    STATE(754), 1,
      sym_var_section,
  [14655] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(177), 1,
      sym_code_block,
    STATE(802), 1,
      sym_var_section,
  [14668] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(214), 1,
      sym_code_block,
    STATE(772), 1,
      sym_var_section,
  [14681] = 3,
    ACTIONS(1528), 1,
      anon_sym_RPAREN,
    STATE(810), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14692] = 3,
    ACTIONS(1530), 1,
      anon_sym_RPAREN,
    STATE(811), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14703] = 3,
    ACTIONS(1532), 1,
      anon_sym_RPAREN,
    STATE(1029), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14714] = 3,
    ACTIONS(1534), 1,
      anon_sym_RPAREN,
    STATE(1030), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14725] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    STATE(494), 1,
      sym__quoted_identifier,
    ACTIONS(1536), 2,
      sym_identifier,
      sym_integer,
  [14736] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1483), 1,
      sym_identifier,
    STATE(661), 1,
      sym_field_reference,
    STATE(883), 1,
      sym__quoted_identifier,
  [14749] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1483), 1,
      sym_identifier,
    STATE(665), 1,
      sym_field_reference,
    STATE(883), 1,
      sym__quoted_identifier,
  [14762] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1401), 1,
      sym_identifier,
    STATE(764), 1,
      sym_option_member,
    STATE(769), 1,
      sym__quoted_identifier,
  [14775] = 3,
    ACTIONS(1504), 1,
      anon_sym_field,
    ACTIONS(1538), 1,
      anon_sym_RBRACE,
    STATE(592), 2,
      sym_field_declaration,
      aux_sym_fields_repeat1,
  [14786] = 4,
    ACTIONS(1389), 1,
      anon_sym_var,
    ACTIONS(1393), 1,
      sym_identifier,
    STATE(817), 1,
      sym_parameter,
    STATE(837), 1,
      sym_modifier,
  [14799] = 4,
    ACTIONS(1540), 1,
      anon_sym_field,
    ACTIONS(1542), 1,
      anon_sym_const,
    ACTIONS(1544), 1,
      anon_sym_filter,
    ACTIONS(1546), 1,
      sym_string_literal,
  [14812] = 1,
    ACTIONS(1548), 4,
      anon_sym_CONST,
      anon_sym_FILTER,
      anon_sym_FIELD,
      sym_string_literal,
  [14819] = 3,
    ACTIONS(1550), 1,
      aux_sym__quoted_identifier_token1,
    STATE(517), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1552), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [14830] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(199), 1,
      sym_code_block,
    STATE(750), 1,
      sym_var_section,
  [14843] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(216), 1,
      sym_code_block,
    STATE(776), 1,
      sym_var_section,
  [14856] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    STATE(971), 1,
      sym__quoted_identifier,
    ACTIONS(1554), 2,
      sym_identifier,
      sym_integer,
  [14867] = 3,
    ACTIONS(1556), 1,
      aux_sym__quoted_identifier_token1,
    STATE(527), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1558), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [14878] = 3,
    ACTIONS(1560), 1,
      anon_sym_RBRACE,
    ACTIONS(1562), 1,
      anon_sym_field,
    STATE(592), 2,
      sym_field_declaration,
      aux_sym_fields_repeat1,
  [14889] = 1,
    ACTIONS(1565), 4,
      anon_sym_OnValidate,
      anon_sym_OnLookup,
      anon_sym_OnAssistEdit,
      anon_sym_OnDrillDown,
  [14896] = 3,
    ACTIONS(1567), 1,
      aux_sym__quoted_identifier_token1,
    STATE(528), 1,
      aux_sym__quoted_identifier_repeat1,
    ACTIONS(1569), 2,
      aux_sym__quoted_identifier_token2,
      aux_sym__quoted_identifier_token3,
  [14907] = 3,
    ACTIONS(1571), 1,
      anon_sym_RBRACE,
    ACTIONS(1573), 1,
      anon_sym_key,
    STATE(595), 2,
      sym_key_declaration,
      aux_sym_keys_repeat1,
  [14918] = 4,
    ACTIONS(1576), 1,
      anon_sym_tabledata,
    STATE(738), 1,
      sym_tabledata_permission,
    STATE(844), 1,
      sym_permissions_value,
    STATE(847), 1,
      sym_tabledata_permission_list,
  [14931] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1395), 1,
      sym_identifier,
    STATE(431), 1,
      sym__quoted_identifier,
    STATE(934), 1,
      sym__field_reference,
  [14944] = 2,
    STATE(844), 1,
      sym_subtype_value,
    ACTIONS(1578), 3,
      anon_sym_Install,
      anon_sym_Upgrade,
      anon_sym_Test,
  [14953] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(202), 1,
      sym_code_block,
    STATE(752), 1,
      sym_var_section,
  [14966] = 3,
    STATE(844), 1,
      sym_single_instance_value,
    STATE(857), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [14977] = 2,
    STATE(845), 1,
      sym_field_class_value,
    ACTIONS(1580), 3,
      anon_sym_FlowField,
      anon_sym_FlowFilter,
      anon_sym_Normal,
  [14986] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    STATE(978), 1,
      sym__quoted_identifier,
    ACTIONS(1582), 2,
      sym_identifier,
      sym_integer,
  [14997] = 4,
    ACTIONS(1460), 1,
      anon_sym_var,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(219), 1,
      sym_code_block,
    STATE(777), 1,
      sym_var_section,
  [15010] = 3,
    STATE(867), 1,
      sym_blank_zero_value,
    STATE(908), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15021] = 3,
    STATE(893), 1,
      sym_editable_value,
    STATE(909), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15032] = 2,
    STATE(844), 1,
      sym_field_class_value,
    ACTIONS(1580), 3,
      anon_sym_FlowField,
      anon_sym_FlowFilter,
      anon_sym_Normal,
  [15041] = 3,
    ACTIONS(1508), 1,
      anon_sym_key,
    ACTIONS(1584), 1,
      anon_sym_RBRACE,
    STATE(595), 2,
      sym_key_declaration,
      aux_sym_keys_repeat1,
  [15052] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1395), 1,
      sym_identifier,
    STATE(431), 1,
      sym__quoted_identifier,
    STATE(933), 1,
      sym__field_reference,
  [15065] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1435), 1,
      sym_identifier,
    STATE(714), 1,
      sym__quoted_identifier,
    STATE(768), 1,
      sym_key_field,
  [15078] = 3,
    STATE(844), 1,
      sym_blank_zero_value,
    STATE(908), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15089] = 4,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1399), 1,
      sym_identifier,
    STATE(758), 1,
      sym__quoted_identifier,
    STATE(1119), 1,
      sym__condition_field_reference,
  [15102] = 1,
    ACTIONS(1586), 3,
      ts_builtin_sym_end,
      anon_sym_table,
      anon_sym_codeunit,
  [15108] = 3,
    ACTIONS(1588), 1,
      anon_sym_COMMA,
    ACTIONS(1590), 1,
      anon_sym_RPAREN,
    STATE(688), 1,
      aux_sym_set_filter_statement_repeat1,
  [15118] = 3,
    ACTIONS(1592), 1,
      anon_sym_COMMA,
    ACTIONS(1594), 1,
      anon_sym_SEMI,
    STATE(666), 1,
      aux_sym_option_members_value_repeat1,
  [15128] = 3,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1596), 1,
      anon_sym_RPAREN,
    STATE(539), 1,
      aux_sym_expression_list_repeat1,
  [15138] = 3,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1598), 1,
      anon_sym_RPAREN,
    STATE(539), 1,
      aux_sym_expression_list_repeat1,
  [15148] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1600), 1,
      sym_identifier,
    STATE(1114), 1,
      sym__quoted_identifier,
  [15158] = 3,
    ACTIONS(1602), 1,
      anon_sym_SEMI,
    ACTIONS(1604), 1,
      anon_sym_RPAREN,
    STATE(643), 1,
      aux_sym_parameter_list_repeat1,
  [15168] = 1,
    ACTIONS(1606), 3,
      ts_builtin_sym_end,
      anon_sym_table,
      anon_sym_codeunit,
  [15174] = 3,
    ACTIONS(675), 1,
      anon_sym_DQUOTE,
    ACTIONS(1608), 1,
      sym_identifier,
    STATE(65), 1,
      sym__quoted_identifier,
  [15184] = 2,
    ACTIONS(1612), 1,
      anon_sym_FIELD,
    ACTIONS(1610), 2,
      anon_sym_CONST,
      anon_sym_FILTER,
  [15192] = 3,
    ACTIONS(1614), 1,
      anon_sym_COMMA,
    ACTIONS(1616), 1,
      anon_sym_RPAREN,
    STATE(628), 1,
      aux_sym_lookup_where_conditions_repeat1,
  [15202] = 3,
    ACTIONS(627), 1,
      anon_sym_DQUOTE,
    ACTIONS(1618), 1,
      sym_identifier,
    STATE(75), 1,
      sym__quoted_identifier,
  [15212] = 3,
    ACTIONS(1620), 1,
      anon_sym_COMMA,
    ACTIONS(1623), 1,
      anon_sym_RPAREN,
    STATE(624), 1,
      aux_sym_filter_conditions_repeat1,
  [15222] = 3,
    ACTIONS(1614), 1,
      anon_sym_COMMA,
    ACTIONS(1625), 1,
      anon_sym_RPAREN,
    STATE(622), 1,
      aux_sym_lookup_where_conditions_repeat1,
  [15232] = 3,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1627), 1,
      anon_sym_RPAREN,
    STATE(539), 1,
      aux_sym_expression_list_repeat1,
  [15242] = 3,
    ACTIONS(1629), 1,
      anon_sym_COMMA,
    ACTIONS(1631), 1,
      anon_sym_RPAREN,
    STATE(629), 1,
      aux_sym_where_conditions_repeat1,
  [15252] = 3,
    ACTIONS(1633), 1,
      anon_sym_COMMA,
    ACTIONS(1636), 1,
      anon_sym_RPAREN,
    STATE(628), 1,
      aux_sym_lookup_where_conditions_repeat1,
  [15262] = 3,
    ACTIONS(1638), 1,
      anon_sym_COMMA,
    ACTIONS(1641), 1,
      anon_sym_RPAREN,
    STATE(629), 1,
      aux_sym_where_conditions_repeat1,
  [15272] = 3,
    ACTIONS(1592), 1,
      anon_sym_COMMA,
    ACTIONS(1643), 1,
      anon_sym_SEMI,
    STATE(666), 1,
      aux_sym_option_members_value_repeat1,
  [15282] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1645), 1,
      sym_identifier,
    STATE(885), 1,
      sym__quoted_identifier,
  [15292] = 3,
    ACTIONS(1588), 1,
      anon_sym_COMMA,
    ACTIONS(1647), 1,
      anon_sym_RPAREN,
    STATE(633), 1,
      aux_sym_set_filter_statement_repeat1,
  [15302] = 3,
    ACTIONS(1588), 1,
      anon_sym_COMMA,
    ACTIONS(1649), 1,
      anon_sym_RPAREN,
    STATE(688), 1,
      aux_sym_set_filter_statement_repeat1,
  [15312] = 3,
    ACTIONS(1588), 1,
      anon_sym_COMMA,
    ACTIONS(1651), 1,
      anon_sym_RPAREN,
    STATE(663), 1,
      aux_sym_set_filter_statement_repeat1,
  [15322] = 3,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1653), 1,
      anon_sym_RPAREN,
    STATE(539), 1,
      aux_sym_expression_list_repeat1,
  [15332] = 3,
    ACTIONS(1576), 1,
      anon_sym_tabledata,
    STATE(738), 1,
      sym_tabledata_permission,
    STATE(966), 1,
      sym_tabledata_permission_list,
  [15342] = 2,
    STATE(1041), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15350] = 1,
    ACTIONS(1655), 3,
      ts_builtin_sym_end,
      anon_sym_table,
      anon_sym_codeunit,
  [15356] = 3,
    ACTIONS(637), 1,
      anon_sym_DQUOTE,
    ACTIONS(1657), 1,
      sym_identifier,
    STATE(64), 1,
      sym__quoted_identifier,
  [15366] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1659), 1,
      sym_identifier,
    STATE(886), 1,
      sym__quoted_identifier,
  [15376] = 1,
    ACTIONS(1661), 3,
      sym_identifier,
      sym_integer,
      sym_string_literal,
  [15382] = 3,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1663), 1,
      anon_sym_RPAREN,
    STATE(539), 1,
      aux_sym_expression_list_repeat1,
  [15392] = 3,
    ACTIONS(1602), 1,
      anon_sym_SEMI,
    ACTIONS(1665), 1,
      anon_sym_RPAREN,
    STATE(696), 1,
      aux_sym_parameter_list_repeat1,
  [15402] = 2,
    STATE(1042), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15410] = 3,
    ACTIONS(1667), 1,
      anon_sym_COMMA,
    ACTIONS(1669), 1,
      anon_sym_RPAREN,
    STATE(624), 1,
      aux_sym_filter_conditions_repeat1,
  [15420] = 3,
    ACTIONS(1588), 1,
      anon_sym_COMMA,
    ACTIONS(1671), 1,
      anon_sym_RPAREN,
    STATE(650), 1,
      aux_sym_set_filter_statement_repeat1,
  [15430] = 2,
    ACTIONS(1675), 1,
      anon_sym_LBRACK,
    ACTIONS(1673), 2,
      anon_sym_SEMI,
      anon_sym_RPAREN,
  [15438] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1677), 1,
      sym_identifier,
    STATE(406), 1,
      sym__quoted_identifier,
  [15448] = 1,
    ACTIONS(1679), 3,
      anon_sym_LBRACK,
      sym_procedure_modifier,
      anon_sym_procedure,
  [15454] = 3,
    ACTIONS(1588), 1,
      anon_sym_COMMA,
    ACTIONS(1681), 1,
      anon_sym_RPAREN,
    STATE(688), 1,
      aux_sym_set_filter_statement_repeat1,
  [15464] = 2,
    ACTIONS(1685), 1,
      anon_sym_where,
    ACTIONS(1683), 2,
      anon_sym_SEMI,
      anon_sym_else,
  [15472] = 1,
    ACTIONS(1687), 3,
      anon_sym_LBRACK,
      sym_procedure_modifier,
      anon_sym_procedure,
  [15478] = 3,
    ACTIONS(1689), 1,
      anon_sym_RPAREN,
    ACTIONS(1691), 1,
      anon_sym_where,
    STATE(1132), 1,
      sym_where_clause,
  [15488] = 3,
    ACTIONS(1691), 1,
      anon_sym_where,
    ACTIONS(1693), 1,
      anon_sym_RPAREN,
    STATE(1134), 1,
      sym_where_clause,
  [15498] = 2,
    STATE(956), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15506] = 2,
    STATE(957), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15514] = 1,
    ACTIONS(1695), 3,
      sym_identifier,
      sym_integer,
      sym_string_literal,
  [15520] = 1,
    ACTIONS(1697), 3,
      sym_identifier,
      sym_integer,
      sym_string_literal,
  [15526] = 3,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1699), 1,
      anon_sym_COLON,
    STATE(539), 1,
      aux_sym_expression_list_repeat1,
  [15536] = 3,
    ACTIONS(1691), 1,
      anon_sym_where,
    ACTIONS(1701), 1,
      anon_sym_RPAREN,
    STATE(1138), 1,
      sym_where_clause,
  [15546] = 3,
    ACTIONS(1691), 1,
      anon_sym_where,
    ACTIONS(1703), 1,
      anon_sym_RPAREN,
    STATE(1144), 1,
      sym_where_clause,
  [15556] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1705), 1,
      sym_identifier,
    STATE(423), 1,
      sym__quoted_identifier,
  [15566] = 3,
    ACTIONS(1588), 1,
      anon_sym_COMMA,
    ACTIONS(1707), 1,
      anon_sym_RPAREN,
    STATE(688), 1,
      aux_sym_set_filter_statement_repeat1,
  [15576] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1709), 1,
      sym_identifier,
    STATE(910), 1,
      sym__quoted_identifier,
  [15586] = 3,
    ACTIONS(1691), 1,
      anon_sym_where,
    ACTIONS(1711), 1,
      anon_sym_RPAREN,
    STATE(1146), 1,
      sym_where_clause,
  [15596] = 3,
    ACTIONS(1713), 1,
      anon_sym_COMMA,
    ACTIONS(1716), 1,
      anon_sym_SEMI,
    STATE(666), 1,
      aux_sym_option_members_value_repeat1,
  [15606] = 3,
    ACTIONS(1718), 1,
      anon_sym_RBRACK,
    ACTIONS(1720), 1,
      anon_sym_LPAREN,
    STATE(1056), 1,
      sym_attribute_arguments,
  [15616] = 2,
    STATE(997), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15624] = 2,
    STATE(998), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15632] = 1,
    ACTIONS(1722), 3,
      sym_identifier,
      sym_integer,
      sym_string_literal,
  [15638] = 1,
    ACTIONS(1724), 3,
      sym_identifier,
      sym_integer,
      sym_string_literal,
  [15644] = 1,
    ACTIONS(1726), 3,
      ts_builtin_sym_end,
      anon_sym_table,
      anon_sym_codeunit,
  [15650] = 2,
    ACTIONS(1728), 1,
      sym_identifier,
    STATE(133), 2,
      sym_variable_declaration,
      aux_sym_var_section_repeat1,
  [15658] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1730), 1,
      sym_identifier,
    STATE(427), 1,
      sym__quoted_identifier,
  [15668] = 3,
    ACTIONS(1732), 1,
      anon_sym_COMMA,
    ACTIONS(1734), 1,
      anon_sym_RPAREN,
    STATE(692), 1,
      aux_sym_key_field_list_repeat1,
  [15678] = 3,
    ACTIONS(1592), 1,
      anon_sym_COMMA,
    ACTIONS(1736), 1,
      anon_sym_SEMI,
    STATE(614), 1,
      aux_sym_option_members_value_repeat1,
  [15688] = 2,
    STATE(844), 1,
      sym_table_no_value,
    ACTIONS(1738), 2,
      sym_identifier,
      sym_integer,
  [15696] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1740), 1,
      sym_identifier,
    STATE(842), 1,
      sym__quoted_identifier,
  [15706] = 2,
    STATE(1033), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15714] = 2,
    STATE(1034), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15722] = 1,
    ACTIONS(1742), 3,
      sym_identifier,
      sym_integer,
      sym_string_literal,
  [15728] = 1,
    ACTIONS(1744), 3,
      sym_identifier,
      sym_integer,
      sym_string_literal,
  [15734] = 1,
    ACTIONS(1746), 3,
      sym_identifier,
      sym_integer,
      sym_string_literal,
  [15740] = 3,
    ACTIONS(657), 1,
      anon_sym_DQUOTE,
    ACTIONS(1748), 1,
      sym_identifier,
    STATE(77), 1,
      sym__quoted_identifier,
  [15750] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1750), 1,
      sym_identifier,
    STATE(430), 1,
      sym__quoted_identifier,
  [15760] = 2,
    ACTIONS(1752), 1,
      anon_sym_LBRACE,
    ACTIONS(1754), 2,
      anon_sym_RBRACE,
      anon_sym_key,
  [15768] = 2,
    STATE(1113), 1,
      sym_boolean,
    ACTIONS(1472), 2,
      anon_sym_true,
      anon_sym_false,
  [15776] = 3,
    ACTIONS(1756), 1,
      anon_sym_COMMA,
    ACTIONS(1759), 1,
      anon_sym_RPAREN,
    STATE(688), 1,
      aux_sym_set_filter_statement_repeat1,
  [15786] = 3,
    ACTIONS(1667), 1,
      anon_sym_COMMA,
    ACTIONS(1761), 1,
      anon_sym_RPAREN,
    STATE(645), 1,
      aux_sym_filter_conditions_repeat1,
  [15796] = 3,
    ACTIONS(1732), 1,
      anon_sym_COMMA,
    ACTIONS(1763), 1,
      anon_sym_RPAREN,
    STATE(675), 1,
      aux_sym_key_field_list_repeat1,
  [15806] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1765), 1,
      sym_identifier,
    STATE(174), 1,
      sym__quoted_identifier,
  [15816] = 3,
    ACTIONS(1767), 1,
      anon_sym_COMMA,
    ACTIONS(1770), 1,
      anon_sym_RPAREN,
    STATE(692), 1,
      aux_sym_key_field_list_repeat1,
  [15826] = 3,
    ACTIONS(1629), 1,
      anon_sym_COMMA,
    ACTIONS(1772), 1,
      anon_sym_RPAREN,
    STATE(627), 1,
      aux_sym_where_conditions_repeat1,
  [15836] = 3,
    ACTIONS(1056), 1,
      anon_sym_COMMA,
    ACTIONS(1774), 1,
      anon_sym_RPAREN,
    STATE(539), 1,
      aux_sym_expression_list_repeat1,
  [15846] = 2,
    ACTIONS(1776), 1,
      anon_sym_LBRACE,
    ACTIONS(1778), 2,
      anon_sym_RBRACE,
      anon_sym_field,
  [15854] = 3,
    ACTIONS(1780), 1,
      anon_sym_SEMI,
    ACTIONS(1783), 1,
      anon_sym_RPAREN,
    STATE(696), 1,
      aux_sym_parameter_list_repeat1,
  [15864] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1785), 1,
      sym_identifier,
    STATE(740), 1,
      sym__quoted_identifier,
  [15874] = 3,
    ACTIONS(1592), 1,
      anon_sym_COMMA,
    ACTIONS(1787), 1,
      anon_sym_SEMI,
    STATE(630), 1,
      aux_sym_option_members_value_repeat1,
  [15884] = 2,
    ACTIONS(1789), 1,
      sym_identifier,
    STATE(461), 2,
      sym_variable_declaration,
      aux_sym_var_section_repeat1,
  [15892] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1791), 1,
      sym_identifier,
    STATE(1128), 1,
      sym__quoted_identifier,
  [15902] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1793), 1,
      sym_identifier,
    STATE(830), 1,
      sym__quoted_identifier,
  [15912] = 1,
    ACTIONS(1795), 3,
      ts_builtin_sym_end,
      anon_sym_table,
      anon_sym_codeunit,
  [15918] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1797), 1,
      sym_identifier,
    STATE(1135), 1,
      sym__quoted_identifier,
  [15928] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1799), 1,
      sym_identifier,
    STATE(1136), 1,
      sym__quoted_identifier,
  [15938] = 3,
    ACTIONS(1588), 1,
      anon_sym_COMMA,
    ACTIONS(1801), 1,
      anon_sym_RPAREN,
    STATE(613), 1,
      aux_sym_set_filter_statement_repeat1,
  [15948] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1803), 1,
      sym_identifier,
    STATE(1140), 1,
      sym__quoted_identifier,
  [15958] = 3,
    ACTIONS(51), 1,
      anon_sym_DQUOTE,
    ACTIONS(1805), 1,
      sym_identifier,
    STATE(1141), 1,
      sym__quoted_identifier,
  [15968] = 2,
    ACTIONS(1807), 1,
      sym_identifier,
    STATE(553), 2,
      sym_variable_declaration,
      aux_sym_var_section_repeat1,
  [15976] = 1,
    ACTIONS(1809), 2,
      anon_sym_RBRACE,
      anon_sym_field,
  [15981] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(400), 1,
      sym_code_block,
  [15988] = 1,
    ACTIONS(1811), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [15993] = 1,
    ACTIONS(1813), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [15998] = 2,
    ACTIONS(1815), 1,
      sym_string_literal,
    STATE(844), 1,
      sym_option_caption_value,
  [16005] = 1,
    ACTIONS(1817), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16010] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(193), 1,
      sym_code_block,
  [16017] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(195), 1,
      sym_code_block,
  [16024] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(197), 1,
      sym_code_block,
  [16031] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(229), 1,
      sym_code_block,
  [16038] = 1,
    ACTIONS(1819), 2,
      anon_sym_var,
      anon_sym_begin,
  [16043] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(230), 1,
      sym_code_block,
  [16050] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(198), 1,
      sym_code_block,
  [16057] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(231), 1,
      sym_code_block,
  [16064] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(200), 1,
      sym_code_block,
  [16071] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(232), 1,
      sym_code_block,
  [16078] = 1,
    ACTIONS(1821), 2,
      anon_sym_SEMI,
      anon_sym_RPAREN,
  [16083] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(233), 1,
      sym_code_block,
  [16090] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(201), 1,
      sym_code_block,
  [16097] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(235), 1,
      sym_code_block,
  [16104] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(236), 1,
      sym_code_block,
  [16111] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(239), 1,
      sym_code_block,
  [16118] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(203), 1,
      sym_code_block,
  [16125] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(240), 1,
      sym_code_block,
  [16132] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(241), 1,
      sym_code_block,
  [16139] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(205), 1,
      sym_code_block,
  [16146] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(242), 1,
      sym_code_block,
  [16153] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(243), 1,
      sym_code_block,
  [16160] = 2,
    ACTIONS(1823), 1,
      anon_sym_SEMI,
    ACTIONS(1825), 1,
      anon_sym_else,
  [16167] = 2,
    ACTIONS(1827), 1,
      anon_sym_COMMA,
    ACTIONS(1829), 1,
      anon_sym_SEMI,
  [16174] = 1,
    ACTIONS(1831), 2,
      anon_sym_SEMI,
      anon_sym_else,
  [16179] = 1,
    ACTIONS(1833), 2,
      anon_sym_RPAREN,
      anon_sym_where,
  [16184] = 1,
    ACTIONS(737), 2,
      sym_identifier,
      anon_sym_begin,
  [16189] = 1,
    ACTIONS(741), 2,
      sym_identifier,
      anon_sym_begin,
  [16194] = 1,
    ACTIONS(1835), 2,
      sym_identifier,
      anon_sym_DQUOTE,
  [16199] = 2,
    ACTIONS(1837), 1,
      anon_sym_RPAREN,
    ACTIONS(1839), 1,
      sym_integer,
  [16206] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(208), 1,
      sym_code_block,
  [16213] = 2,
    ACTIONS(1841), 1,
      sym_identifier,
    STATE(848), 1,
      sym__procedure_name,
  [16220] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(209), 1,
      sym_code_block,
  [16227] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(211), 1,
      sym_code_block,
  [16234] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(504), 1,
      sym_code_block,
  [16241] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(212), 1,
      sym_code_block,
  [16248] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(213), 1,
      sym_code_block,
  [16255] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(215), 1,
      sym_code_block,
  [16262] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(176), 1,
      sym_code_block,
  [16269] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(217), 1,
      sym_code_block,
  [16276] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(218), 1,
      sym_code_block,
  [16283] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(220), 1,
      sym_code_block,
  [16290] = 1,
    ACTIONS(1623), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16295] = 1,
    ACTIONS(1843), 2,
      anon_sym_EQ,
      anon_sym_RPAREN,
  [16300] = 2,
    ACTIONS(1845), 1,
      anon_sym_COMMA,
    ACTIONS(1847), 1,
      anon_sym_RPAREN,
  [16307] = 2,
    ACTIONS(1849), 1,
      anon_sym_COMMA,
    ACTIONS(1851), 1,
      anon_sym_RPAREN,
  [16314] = 2,
    ACTIONS(1853), 1,
      anon_sym_RPAREN,
    ACTIONS(1855), 1,
      anon_sym_where,
  [16321] = 2,
    ACTIONS(1857), 1,
      anon_sym_begin,
    STATE(455), 1,
      sym_code_block,
  [16328] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(977), 1,
      sym_code_block,
  [16335] = 1,
    ACTIONS(1716), 2,
      anon_sym_COMMA,
      anon_sym_SEMI,
  [16340] = 2,
    ACTIONS(1859), 1,
      anon_sym_LBRACK,
    ACTIONS(1861), 1,
      anon_sym_RPAREN,
  [16347] = 2,
    ACTIONS(1861), 1,
      anon_sym_RPAREN,
    ACTIONS(1863), 1,
      anon_sym_LBRACK,
  [16354] = 2,
    ACTIONS(1865), 1,
      anon_sym_LBRACK,
    ACTIONS(1867), 1,
      anon_sym_RPAREN,
  [16361] = 1,
    ACTIONS(1770), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16366] = 1,
    ACTIONS(1869), 2,
      anon_sym_COMMA,
      anon_sym_SEMI,
  [16371] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(221), 1,
      sym_code_block,
  [16378] = 1,
    ACTIONS(1871), 2,
      anon_sym_SEMI,
      anon_sym_RPAREN,
  [16383] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(222), 1,
      sym_code_block,
  [16390] = 2,
    ACTIONS(745), 1,
      anon_sym_LPAREN,
    STATE(380), 1,
      sym_argument_list,
  [16397] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(223), 1,
      sym_code_block,
  [16404] = 1,
    ACTIONS(1873), 2,
      anon_sym_COMMA,
      anon_sym_SEMI,
  [16409] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(225), 1,
      sym_code_block,
  [16416] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(226), 1,
      sym_code_block,
  [16423] = 2,
    ACTIONS(1156), 1,
      anon_sym_LPAREN,
    STATE(319), 1,
      sym_argument_list,
  [16430] = 1,
    ACTIONS(1875), 2,
      anon_sym_SEMI,
      anon_sym_else,
  [16435] = 1,
    ACTIONS(1877), 2,
      anon_sym_SEMI,
      anon_sym_else,
  [16440] = 2,
    ACTIONS(1879), 1,
      anon_sym_field,
    ACTIONS(1881), 1,
      anon_sym_const,
  [16447] = 2,
    ACTIONS(1883), 1,
      anon_sym_RPAREN,
    ACTIONS(1885), 1,
      sym_integer,
  [16454] = 2,
    ACTIONS(1887), 1,
      anon_sym_field,
    ACTIONS(1889), 1,
      anon_sym_const,
  [16461] = 2,
    ACTIONS(1891), 1,
      anon_sym_COMMA,
    ACTIONS(1893), 1,
      anon_sym_RPAREN,
  [16468] = 2,
    ACTIONS(1895), 1,
      anon_sym_COMMA,
    ACTIONS(1897), 1,
      anon_sym_RPAREN,
  [16475] = 2,
    ACTIONS(1899), 1,
      anon_sym_COMMA,
    ACTIONS(1901), 1,
      anon_sym_RPAREN,
  [16482] = 2,
    ACTIONS(1903), 1,
      sym_integer,
    STATE(570), 1,
      sym_object_id,
  [16489] = 2,
    ACTIONS(1841), 1,
      sym_identifier,
    STATE(831), 1,
      sym__procedure_name,
  [16496] = 2,
    ACTIONS(1905), 1,
      anon_sym_SEMI,
    ACTIONS(1907), 1,
      sym_temporary,
  [16503] = 2,
    ACTIONS(1576), 1,
      anon_sym_tabledata,
    STATE(1021), 1,
      sym_tabledata_permission,
  [16510] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(181), 1,
      sym_code_block,
  [16517] = 2,
    ACTIONS(1841), 1,
      sym_identifier,
    STATE(838), 1,
      sym__procedure_name,
  [16524] = 2,
    ACTIONS(1166), 1,
      anon_sym_LPAREN,
    STATE(259), 1,
      sym_argument_list,
  [16531] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(183), 1,
      sym_code_block,
  [16538] = 2,
    ACTIONS(1909), 1,
      anon_sym_RPAREN,
    ACTIONS(1911), 1,
      sym_integer,
  [16545] = 1,
    ACTIONS(1913), 2,
      anon_sym_RBRACE,
      anon_sym_key,
  [16550] = 2,
    ACTIONS(1915), 1,
      anon_sym_COMMA,
    ACTIONS(1917), 1,
      anon_sym_RPAREN,
  [16557] = 2,
    ACTIONS(1919), 1,
      anon_sym_COMMA,
    ACTIONS(1921), 1,
      anon_sym_RPAREN,
  [16564] = 2,
    ACTIONS(1923), 1,
      anon_sym_COMMA,
    ACTIONS(1925), 1,
      anon_sym_RPAREN,
  [16571] = 1,
    ACTIONS(1927), 2,
      anon_sym_var,
      anon_sym_begin,
  [16576] = 1,
    ACTIONS(1929), 2,
      anon_sym_var,
      anon_sym_begin,
  [16581] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(185), 1,
      sym_code_block,
  [16588] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(227), 1,
      sym_code_block,
  [16595] = 2,
    ACTIONS(1841), 1,
      sym_identifier,
    STATE(970), 1,
      sym__procedure_name,
  [16602] = 1,
    ACTIONS(1931), 2,
      anon_sym_SEMI,
      anon_sym_RPAREN,
  [16607] = 2,
    ACTIONS(1174), 1,
      anon_sym_LPAREN,
    STATE(290), 1,
      sym_argument_list,
  [16614] = 1,
    ACTIONS(1636), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16619] = 2,
    ACTIONS(1933), 1,
      anon_sym_RPAREN,
    ACTIONS(1935), 1,
      sym_integer,
  [16626] = 2,
    ACTIONS(1937), 1,
      sym_procedure_modifier,
    ACTIONS(1939), 1,
      anon_sym_procedure,
  [16633] = 2,
    ACTIONS(1941), 1,
      anon_sym_COMMA,
    ACTIONS(1943), 1,
      anon_sym_RPAREN,
  [16640] = 2,
    ACTIONS(1945), 1,
      anon_sym_COMMA,
    ACTIONS(1947), 1,
      anon_sym_RPAREN,
  [16647] = 2,
    ACTIONS(1949), 1,
      anon_sym_COMMA,
    ACTIONS(1951), 1,
      anon_sym_RPAREN,
  [16654] = 1,
    ACTIONS(1641), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16659] = 2,
    ACTIONS(1953), 1,
      anon_sym_COMMA,
    ACTIONS(1955), 1,
      anon_sym_RPAREN,
  [16666] = 2,
    ACTIONS(1957), 1,
      anon_sym_COLON,
    ACTIONS(1959), 1,
      anon_sym_RBRACK,
  [16673] = 2,
    ACTIONS(1961), 1,
      anon_sym_COLON,
    ACTIONS(1963), 1,
      anon_sym_RBRACK,
  [16680] = 1,
    ACTIONS(1783), 2,
      anon_sym_SEMI,
      anon_sym_RPAREN,
  [16685] = 1,
    ACTIONS(1965), 2,
      anon_sym_RBRACE,
      anon_sym_key,
  [16690] = 2,
    ACTIONS(1967), 1,
      anon_sym_SEMI,
    ACTIONS(1969), 1,
      sym_temporary,
  [16697] = 1,
    ACTIONS(1971), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16702] = 2,
    ACTIONS(1903), 1,
      sym_integer,
    STATE(547), 1,
      sym_object_id,
  [16709] = 2,
    ACTIONS(1462), 1,
      anon_sym_begin,
    STATE(188), 1,
      sym_code_block,
  [16716] = 1,
    ACTIONS(1973), 2,
      anon_sym_RBRACE,
      anon_sym_field,
  [16721] = 1,
    ACTIONS(1975), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16726] = 2,
    ACTIONS(1815), 1,
      sym_string_literal,
    STATE(901), 1,
      sym_option_caption_value,
  [16733] = 1,
    ACTIONS(1977), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16738] = 1,
    ACTIONS(1979), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16743] = 1,
    ACTIONS(1981), 2,
      anon_sym_COMMA,
      anon_sym_RPAREN,
  [16748] = 2,
    ACTIONS(1983), 1,
      anon_sym_SEMI,
    ACTIONS(1985), 1,
      sym_temporary,
  [16755] = 1,
    ACTIONS(1987), 1,
      anon_sym_COMMA,
  [16759] = 1,
    ACTIONS(1989), 1,
      anon_sym_LPAREN,
  [16763] = 1,
    ACTIONS(1991), 1,
      anon_sym_COLON,
  [16767] = 1,
    ACTIONS(1993), 1,
      anon_sym_LPAREN_RPAREN,
  [16771] = 1,
    ACTIONS(1995), 1,
      anon_sym_of,
  [16775] = 1,
    ACTIONS(1997), 1,
      anon_sym_RPAREN,
  [16779] = 1,
    ACTIONS(1999), 1,
      sym_identifier,
  [16783] = 1,
    ACTIONS(2001), 1,
      sym_identifier,
  [16787] = 1,
    ACTIONS(2003), 1,
      anon_sym_LPAREN,
  [16791] = 1,
    ACTIONS(2005), 1,
      anon_sym_EQ,
  [16795] = 1,
    ACTIONS(2007), 1,
      anon_sym_RBRACK,
  [16799] = 1,
    ACTIONS(2009), 1,
      anon_sym_SEMI,
  [16803] = 1,
    ACTIONS(2011), 1,
      anon_sym_SEMI,
  [16807] = 1,
    ACTIONS(2013), 1,
      anon_sym_SEMI,
  [16811] = 1,
    ACTIONS(2015), 1,
      anon_sym_SEMI,
  [16815] = 1,
    ACTIONS(2017), 1,
      anon_sym_SEMI,
  [16819] = 1,
    ACTIONS(2019), 1,
      anon_sym_RPAREN,
  [16823] = 1,
    ACTIONS(2021), 1,
      anon_sym_SEMI,
  [16827] = 1,
    ACTIONS(2023), 1,
      anon_sym_LPAREN,
  [16831] = 1,
    ACTIONS(2025), 1,
      anon_sym_SEMI,
  [16835] = 1,
    ACTIONS(2027), 1,
      anon_sym_COLON,
  [16839] = 1,
    ACTIONS(2029), 1,
      anon_sym_RPAREN,
  [16843] = 1,
    ACTIONS(2031), 1,
      anon_sym_COLON,
  [16847] = 1,
    ACTIONS(2033), 1,
      anon_sym_SEMI,
  [16851] = 1,
    ACTIONS(2035), 1,
      anon_sym_SEMI,
  [16855] = 1,
    ACTIONS(2037), 1,
      anon_sym_LPAREN_RPAREN,
  [16859] = 1,
    ACTIONS(2039), 1,
      anon_sym_EQ,
  [16863] = 1,
    ACTIONS(2041), 1,
      anon_sym_SEMI,
  [16867] = 1,
    ACTIONS(2043), 1,
      anon_sym_EQ,
  [16871] = 1,
    ACTIONS(2045), 1,
      anon_sym_SEMI,
  [16875] = 1,
    ACTIONS(2047), 1,
      anon_sym_COLON,
  [16879] = 1,
    ACTIONS(2045), 1,
      anon_sym_SEMI,
  [16883] = 1,
    ACTIONS(2049), 1,
      anon_sym_LPAREN,
  [16887] = 1,
    ACTIONS(2051), 1,
      anon_sym_LPAREN_RPAREN,
  [16891] = 1,
    ACTIONS(2053), 1,
      anon_sym_RPAREN,
  [16895] = 1,
    ACTIONS(2055), 1,
      anon_sym_LPAREN,
  [16899] = 1,
    ACTIONS(2057), 1,
      anon_sym_LPAREN,
  [16903] = 1,
    ACTIONS(2059), 1,
      anon_sym_SEMI,
  [16907] = 1,
    ACTIONS(2061), 1,
      anon_sym_LPAREN_RPAREN,
  [16911] = 1,
    ACTIONS(2063), 1,
      anon_sym_EQ,
  [16915] = 1,
    ACTIONS(2065), 1,
      anon_sym_EQ,
  [16919] = 1,
    ACTIONS(2067), 1,
      anon_sym_RPAREN,
  [16923] = 1,
    ACTIONS(2069), 1,
      anon_sym_RPAREN,
  [16927] = 1,
    ACTIONS(2071), 1,
      anon_sym_EQ,
  [16931] = 1,
    ACTIONS(2073), 1,
      anon_sym_RPAREN,
  [16935] = 1,
    ACTIONS(2075), 1,
      anon_sym_SEMI,
  [16939] = 1,
    ACTIONS(2077), 1,
      anon_sym_EQ,
  [16943] = 1,
    ACTIONS(2079), 1,
      anon_sym_RPAREN,
  [16947] = 1,
    ACTIONS(2081), 1,
      anon_sym_SEMI,
  [16951] = 1,
    ACTIONS(2083), 1,
      anon_sym_SEMI,
  [16955] = 1,
    ACTIONS(2085), 1,
      anon_sym_SEMI,
  [16959] = 1,
    ACTIONS(2087), 1,
      anon_sym_LPAREN,
  [16963] = 1,
    ACTIONS(2089), 1,
      anon_sym_RPAREN,
  [16967] = 1,
    ACTIONS(2091), 1,
      anon_sym_DOT,
  [16971] = 1,
    ACTIONS(2093), 1,
      anon_sym_RPAREN,
  [16975] = 1,
    ACTIONS(2095), 1,
      anon_sym_COMMA,
  [16979] = 1,
    ACTIONS(2097), 1,
      anon_sym_COMMA,
  [16983] = 1,
    ACTIONS(2099), 1,
      anon_sym_LPAREN,
  [16987] = 1,
    ACTIONS(2101), 1,
      anon_sym_LPAREN,
  [16991] = 1,
    ACTIONS(2103), 1,
      anon_sym_LPAREN,
  [16995] = 1,
    ACTIONS(2105), 1,
      anon_sym_LPAREN,
  [16999] = 1,
    ACTIONS(2107), 1,
      anon_sym_RPAREN,
  [17003] = 1,
    ACTIONS(2109), 1,
      anon_sym_LPAREN,
  [17007] = 1,
    ACTIONS(2111), 1,
      anon_sym_SEMI,
  [17011] = 1,
    ACTIONS(1787), 1,
      anon_sym_SEMI,
  [17015] = 1,
    ACTIONS(2113), 1,
      anon_sym_LPAREN,
  [17019] = 1,
    ACTIONS(2115), 1,
      anon_sym_end,
  [17023] = 1,
    ACTIONS(2117), 1,
      anon_sym_LPAREN,
  [17027] = 1,
    ACTIONS(2119), 1,
      anon_sym_RBRACK,
  [17031] = 1,
    ACTIONS(2121), 1,
      anon_sym_SEMI,
  [17035] = 1,
    ACTIONS(1861), 1,
      anon_sym_RPAREN,
  [17039] = 1,
    ACTIONS(2123), 1,
      anon_sym_SEMI,
  [17043] = 1,
    ACTIONS(2125), 1,
      sym_integer,
  [17047] = 1,
    ACTIONS(1863), 1,
      anon_sym_LBRACK,
  [17051] = 1,
    ACTIONS(2127), 1,
      anon_sym_COLON,
  [17055] = 1,
    ACTIONS(2129), 1,
      sym_identifier,
  [17059] = 1,
    ACTIONS(2131), 1,
      anon_sym_RPAREN,
  [17063] = 1,
    ACTIONS(2133), 1,
      anon_sym_RPAREN,
  [17067] = 1,
    ACTIONS(2135), 1,
      anon_sym_SEMI,
  [17071] = 1,
    ACTIONS(2137), 1,
      anon_sym_SEMI,
  [17075] = 1,
    ACTIONS(2139), 1,
      anon_sym_RPAREN,
  [17079] = 1,
    ACTIONS(1736), 1,
      anon_sym_SEMI,
  [17083] = 1,
    ACTIONS(2141), 1,
      anon_sym_LPAREN,
  [17087] = 1,
    ACTIONS(2143), 1,
      anon_sym_LPAREN_RPAREN,
  [17091] = 1,
    ACTIONS(2145), 1,
      anon_sym_SEMI,
  [17095] = 1,
    ACTIONS(2147), 1,
      anon_sym_LPAREN,
  [17099] = 1,
    ACTIONS(2149), 1,
      anon_sym_LPAREN_RPAREN,
  [17103] = 1,
    ACTIONS(2151), 1,
      anon_sym_LPAREN_RPAREN,
  [17107] = 1,
    ACTIONS(2153), 1,
      anon_sym_LPAREN,
  [17111] = 1,
    ACTIONS(2155), 1,
      anon_sym_LPAREN_RPAREN,
  [17115] = 1,
    ACTIONS(2157), 1,
      anon_sym_LPAREN_RPAREN,
  [17119] = 1,
    ACTIONS(2159), 1,
      anon_sym_LPAREN,
  [17123] = 1,
    ACTIONS(2161), 1,
      anon_sym_LPAREN,
  [17127] = 1,
    ACTIONS(2163), 1,
      anon_sym_LPAREN,
  [17131] = 1,
    ACTIONS(2165), 1,
      anon_sym_LPAREN,
  [17135] = 1,
    ACTIONS(2167), 1,
      anon_sym_SEMI,
  [17139] = 1,
    ACTIONS(2169), 1,
      anon_sym_EQ,
  [17143] = 1,
    ACTIONS(2171), 1,
      anon_sym_EQ,
  [17147] = 1,
    ACTIONS(2173), 1,
      anon_sym_RBRACK,
  [17151] = 1,
    ACTIONS(2175), 1,
      sym_identifier,
  [17155] = 1,
    ACTIONS(2177), 1,
      anon_sym_LPAREN,
  [17159] = 1,
    ACTIONS(2179), 1,
      anon_sym_EQ,
  [17163] = 1,
    ACTIONS(2181), 1,
      anon_sym_RBRACK,
  [17167] = 1,
    ACTIONS(2183), 1,
      anon_sym_RPAREN,
  [17171] = 1,
    ACTIONS(2185), 1,
      anon_sym_RPAREN,
  [17175] = 1,
    ACTIONS(2187), 1,
      sym_string_literal,
  [17179] = 1,
    ACTIONS(2189), 1,
      anon_sym_LPAREN,
  [17183] = 1,
    ACTIONS(2191), 1,
      sym_integer,
  [17187] = 1,
    ACTIONS(2193), 1,
      anon_sym_RPAREN,
  [17191] = 1,
    ACTIONS(2195), 1,
      anon_sym_EQ,
  [17195] = 1,
    ACTIONS(2197), 1,
      sym_string_literal,
  [17199] = 1,
    ACTIONS(2199), 1,
      anon_sym_EQ,
  [17203] = 1,
    ACTIONS(2201), 1,
      anon_sym_RPAREN,
  [17207] = 1,
    ACTIONS(2203), 1,
      anon_sym_COLON,
  [17211] = 1,
    ACTIONS(2205), 1,
      anon_sym_EQ,
  [17215] = 1,
    ACTIONS(2207), 1,
      anon_sym_RPAREN,
  [17219] = 1,
    ACTIONS(2209), 1,
      anon_sym_RPAREN,
  [17223] = 1,
    ACTIONS(2211), 1,
      anon_sym_RPAREN,
  [17227] = 1,
    ACTIONS(2213), 1,
      anon_sym_SEMI,
  [17231] = 1,
    ACTIONS(2215), 1,
      anon_sym_EQ,
  [17235] = 1,
    ACTIONS(2217), 1,
      anon_sym_LPAREN,
  [17239] = 1,
    ACTIONS(2219), 1,
      anon_sym_LPAREN,
  [17243] = 1,
    ACTIONS(2221), 1,
      anon_sym_RPAREN,
  [17247] = 1,
    ACTIONS(2223), 1,
      anon_sym_RPAREN,
  [17251] = 1,
    ACTIONS(2225), 1,
      anon_sym_RPAREN,
  [17255] = 1,
    ACTIONS(2227), 1,
      anon_sym_end,
  [17259] = 1,
    ACTIONS(2229), 1,
      anon_sym_RPAREN,
  [17263] = 1,
    ACTIONS(2231), 1,
      anon_sym_RPAREN,
  [17267] = 1,
    ACTIONS(2233), 1,
      anon_sym_LPAREN,
  [17271] = 1,
    ACTIONS(2235), 1,
      anon_sym_RPAREN,
  [17275] = 1,
    ACTIONS(2237), 1,
      anon_sym_RPAREN,
  [17279] = 1,
    ACTIONS(2239), 1,
      anon_sym_RPAREN,
  [17283] = 1,
    ACTIONS(2241), 1,
      sym_identifier,
  [17287] = 1,
    ACTIONS(2243), 1,
      anon_sym_LBRACE,
  [17291] = 1,
    ACTIONS(2245), 1,
      anon_sym_RPAREN,
  [17295] = 1,
    ACTIONS(2247), 1,
      anon_sym_EQ,
  [17299] = 1,
    ACTIONS(2249), 1,
      anon_sym_SEMI,
  [17303] = 1,
    ACTIONS(2251), 1,
      anon_sym_LPAREN,
  [17307] = 1,
    ACTIONS(2253), 1,
      anon_sym_EQ,
  [17311] = 1,
    ACTIONS(2255), 1,
      anon_sym_SEMI,
  [17315] = 1,
    ACTIONS(2257), 1,
      anon_sym_LPAREN,
  [17319] = 1,
    ACTIONS(2259), 1,
      anon_sym_SEMI,
  [17323] = 1,
    ACTIONS(2261), 1,
      anon_sym_procedure,
  [17327] = 1,
    ACTIONS(2263), 1,
      sym_identifier,
  [17331] = 1,
    ACTIONS(2265), 1,
      sym_string_literal,
  [17335] = 1,
    ACTIONS(2267), 1,
      anon_sym_RPAREN,
  [17339] = 1,
    ACTIONS(2269), 1,
      anon_sym_LBRACE,
  [17343] = 1,
    ACTIONS(2271), 1,
      anon_sym_end,
  [17347] = 1,
    ACTIONS(2273), 1,
      anon_sym_SEMI,
  [17351] = 1,
    ACTIONS(2275), 1,
      anon_sym_COLON_EQ,
  [17355] = 1,
    ACTIONS(2277), 1,
      anon_sym_of,
  [17359] = 1,
    ACTIONS(2279), 1,
      sym_integer,
  [17363] = 1,
    ACTIONS(2281), 1,
      sym_integer,
  [17367] = 1,
    ACTIONS(2283), 1,
      sym_integer,
  [17371] = 1,
    ACTIONS(2285), 1,
      anon_sym_RPAREN,
  [17375] = 1,
    ACTIONS(2287), 1,
      anon_sym_of,
  [17379] = 1,
    ACTIONS(2289), 1,
      anon_sym_RPAREN,
  [17383] = 1,
    ACTIONS(2291), 1,
      anon_sym_RPAREN,
  [17387] = 1,
    ACTIONS(2293), 1,
      anon_sym_RPAREN,
  [17391] = 1,
    ACTIONS(2295), 1,
      anon_sym_SEMI,
  [17395] = 1,
    ACTIONS(2297), 1,
      anon_sym_SEMI,
  [17399] = 1,
    ACTIONS(2299), 1,
      anon_sym_SEMI,
  [17403] = 1,
    ACTIONS(2301), 1,
      anon_sym_SEMI,
  [17407] = 1,
    ACTIONS(2303), 1,
      anon_sym_RPAREN,
  [17411] = 1,
    ACTIONS(2305), 1,
      anon_sym_RPAREN,
  [17415] = 1,
    ACTIONS(2307), 1,
      anon_sym_RPAREN,
  [17419] = 1,
    ACTIONS(2309), 1,
      anon_sym_end,
  [17423] = 1,
    ACTIONS(2311), 1,
      anon_sym_RPAREN,
  [17427] = 1,
    ACTIONS(2313), 1,
      anon_sym_RPAREN,
  [17431] = 1,
    ACTIONS(2315), 1,
      anon_sym_SEMI,
  [17435] = 1,
    ACTIONS(2317), 1,
      anon_sym_EQ,
  [17439] = 1,
    ACTIONS(2319), 1,
      anon_sym_SEMI,
  [17443] = 1,
    ACTIONS(2321), 1,
      anon_sym_RPAREN,
  [17447] = 1,
    ACTIONS(2323), 1,
      anon_sym_SEMI,
  [17451] = 1,
    ACTIONS(2325), 1,
      anon_sym_procedure,
  [17455] = 1,
    ACTIONS(2327), 1,
      anon_sym_SEMI,
  [17459] = 1,
    ACTIONS(2329), 1,
      anon_sym_SEMI,
  [17463] = 1,
    ACTIONS(2331), 1,
      anon_sym_EQ,
  [17467] = 1,
    ACTIONS(2333), 1,
      anon_sym_LPAREN_RPAREN,
  [17471] = 1,
    ACTIONS(2335), 1,
      sym_identifier,
  [17475] = 1,
    ACTIONS(2337), 1,
      sym_identifier,
  [17479] = 1,
    ACTIONS(2339), 1,
      anon_sym_RPAREN,
  [17483] = 1,
    ACTIONS(2341), 1,
      anon_sym_RPAREN,
  [17487] = 1,
    ACTIONS(2343), 1,
      anon_sym_RPAREN,
  [17491] = 1,
    ACTIONS(2345), 1,
      anon_sym_LPAREN_RPAREN,
  [17495] = 1,
    ACTIONS(2347), 1,
      anon_sym_RPAREN,
  [17499] = 1,
    ACTIONS(2349), 1,
      anon_sym_LPAREN,
  [17503] = 1,
    ACTIONS(2351), 1,
      anon_sym_LPAREN,
  [17507] = 1,
    ACTIONS(2353), 1,
      anon_sym_LPAREN,
  [17511] = 1,
    ACTIONS(2355), 1,
      anon_sym_LPAREN,
  [17515] = 1,
    ACTIONS(2357), 1,
      anon_sym_SEMI,
  [17519] = 1,
    ACTIONS(2359), 1,
      anon_sym_SEMI,
  [17523] = 1,
    ACTIONS(2361), 1,
      anon_sym_RPAREN,
  [17527] = 1,
    ACTIONS(2363), 1,
      anon_sym_RPAREN,
  [17531] = 1,
    ACTIONS(2365), 1,
      anon_sym_RPAREN,
  [17535] = 1,
    ACTIONS(2367), 1,
      anon_sym_LBRACK,
  [17539] = 1,
    ACTIONS(2369), 1,
      anon_sym_LBRACK,
  [17543] = 1,
    ACTIONS(2371), 1,
      sym_integer,
  [17547] = 1,
    ACTIONS(2373), 1,
      anon_sym_EQ,
  [17551] = 1,
    ACTIONS(2375), 1,
      anon_sym_RPAREN,
  [17555] = 1,
    ACTIONS(2377), 1,
      anon_sym_RPAREN,
  [17559] = 1,
    ACTIONS(2379), 1,
      anon_sym_RPAREN,
  [17563] = 1,
    ACTIONS(2381), 1,
      anon_sym_end,
  [17567] = 1,
    ACTIONS(2383), 1,
      anon_sym_RPAREN,
  [17571] = 1,
    ACTIONS(2385), 1,
      anon_sym_RPAREN,
  [17575] = 1,
    ACTIONS(2387), 1,
      anon_sym_RBRACK,
  [17579] = 1,
    ACTIONS(2389), 1,
      anon_sym_LPAREN,
  [17583] = 1,
    ACTIONS(2391), 1,
      anon_sym_LPAREN,
  [17587] = 1,
    ACTIONS(2393), 1,
      anon_sym_RPAREN,
  [17591] = 1,
    ACTIONS(2395), 1,
      anon_sym_RPAREN,
  [17595] = 1,
    ACTIONS(2397), 1,
      ts_builtin_sym_end,
  [17599] = 1,
    ACTIONS(2399), 1,
      anon_sym_RPAREN,
  [17603] = 1,
    ACTIONS(2401), 1,
      anon_sym_RPAREN,
  [17607] = 1,
    ACTIONS(2403), 1,
      anon_sym_RPAREN,
  [17611] = 1,
    ACTIONS(2405), 1,
      sym_identifier,
  [17615] = 1,
    ACTIONS(2407), 1,
      sym_identifier,
  [17619] = 1,
    ACTIONS(2409), 1,
      anon_sym_RPAREN,
  [17623] = 1,
    ACTIONS(1959), 1,
      anon_sym_RBRACK,
  [17627] = 1,
    ACTIONS(2411), 1,
      anon_sym_COMMA,
  [17631] = 1,
    ACTIONS(2413), 1,
      anon_sym_LBRACE,
  [17635] = 1,
    ACTIONS(2415), 1,
      anon_sym_LBRACK,
  [17639] = 1,
    ACTIONS(2417), 1,
      anon_sym_EQ,
  [17643] = 1,
    ACTIONS(2419), 1,
      anon_sym_COLON,
  [17647] = 1,
    ACTIONS(2421), 1,
      anon_sym_RPAREN,
  [17651] = 1,
    ACTIONS(2423), 1,
      anon_sym_COLON_EQ,
  [17655] = 1,
    ACTIONS(2425), 1,
      anon_sym_RPAREN,
  [17659] = 1,
    ACTIONS(2427), 1,
      anon_sym_RBRACK,
  [17663] = 1,
    ACTIONS(2429), 1,
      anon_sym_LBRACE,
  [17667] = 1,
    ACTIONS(2431), 1,
      sym_integer,
  [17671] = 1,
    ACTIONS(2433), 1,
      anon_sym_LBRACE,
  [17675] = 1,
    ACTIONS(2435), 1,
      sym_string_literal,
  [17679] = 1,
    ACTIONS(2437), 1,
      anon_sym_LPAREN,
  [17683] = 1,
    ACTIONS(2439), 1,
      anon_sym_LPAREN,
  [17687] = 1,
    ACTIONS(2441), 1,
      anon_sym_LPAREN,
  [17691] = 1,
    ACTIONS(2443), 1,
      anon_sym_LPAREN,
  [17695] = 1,
    ACTIONS(2445), 1,
      anon_sym_LPAREN,
  [17699] = 1,
    ACTIONS(2447), 1,
      anon_sym_LPAREN,
  [17703] = 1,
    ACTIONS(2449), 1,
      anon_sym_LPAREN,
  [17707] = 1,
    ACTIONS(2451), 1,
      anon_sym_LPAREN,
  [17711] = 1,
    ACTIONS(2453), 1,
      anon_sym_OnRun,
  [17715] = 1,
    ACTIONS(2455), 1,
      sym_string_literal,
  [17719] = 1,
    ACTIONS(2457), 1,
      anon_sym_RPAREN,
  [17723] = 1,
    ACTIONS(2459), 1,
      anon_sym_EQ,
  [17727] = 1,
    ACTIONS(2461), 1,
      sym_string_literal,
  [17731] = 1,
    ACTIONS(2463), 1,
      anon_sym_EQ,
  [17735] = 1,
    ACTIONS(2465), 1,
      anon_sym_LPAREN,
  [17739] = 1,
    ACTIONS(2467), 1,
      sym_integer,
  [17743] = 1,
    ACTIONS(2469), 1,
      anon_sym_RPAREN,
  [17747] = 1,
    ACTIONS(2471), 1,
      anon_sym_COLON_EQ,
  [17751] = 1,
    ACTIONS(2473), 1,
      anon_sym_EQ,
  [17755] = 1,
    ACTIONS(2475), 1,
      sym_integer,
  [17759] = 1,
    ACTIONS(2477), 1,
      anon_sym_RPAREN,
  [17763] = 1,
    ACTIONS(2479), 1,
      sym_integer,
  [17767] = 1,
    ACTIONS(2481), 1,
      anon_sym_RPAREN,
  [17771] = 1,
    ACTIONS(2483), 1,
      anon_sym_LPAREN,
  [17775] = 1,
    ACTIONS(2485), 1,
      anon_sym_LPAREN,
  [17779] = 1,
    ACTIONS(2487), 1,
      anon_sym_LPAREN,
  [17783] = 1,
    ACTIONS(2489), 1,
      anon_sym_LPAREN,
  [17787] = 1,
    ACTIONS(2491), 1,
      anon_sym_LPAREN,
  [17791] = 1,
    ACTIONS(2493), 1,
      anon_sym_LPAREN,
  [17795] = 1,
    ACTIONS(2495), 1,
      anon_sym_LPAREN,
  [17799] = 1,
    ACTIONS(2497), 1,
      anon_sym_LPAREN,
  [17803] = 1,
    ACTIONS(2499), 1,
      anon_sym_LPAREN,
  [17807] = 1,
    ACTIONS(2501), 1,
      anon_sym_EQ,
  [17811] = 1,
    ACTIONS(2503), 1,
      anon_sym_EQ,
  [17815] = 1,
    ACTIONS(2505), 1,
      anon_sym_EQ,
  [17819] = 1,
    ACTIONS(2507), 1,
      sym_string_literal,
  [17823] = 1,
    ACTIONS(2509), 1,
      anon_sym_EQ,
  [17827] = 1,
    ACTIONS(2511), 1,
      anon_sym_EQ,
  [17831] = 1,
    ACTIONS(2513), 1,
      anon_sym_EQ,
  [17835] = 1,
    ACTIONS(2515), 1,
      anon_sym_COLON_EQ,
  [17839] = 1,
    ACTIONS(2517), 1,
      anon_sym_EQ,
  [17843] = 1,
    ACTIONS(2519), 1,
      anon_sym_EQ,
  [17847] = 1,
    ACTIONS(2521), 1,
      anon_sym_EQ,
  [17851] = 1,
    ACTIONS(2523), 1,
      anon_sym_SEMI,
  [17855] = 1,
    ACTIONS(2525), 1,
      anon_sym_LPAREN,
  [17859] = 1,
    ACTIONS(2527), 1,
      anon_sym_LPAREN,
  [17863] = 1,
    ACTIONS(2529), 1,
      anon_sym_LPAREN,
  [17867] = 1,
    ACTIONS(2531), 1,
      anon_sym_LPAREN,
  [17871] = 1,
    ACTIONS(2533), 1,
      anon_sym_LPAREN,
  [17875] = 1,
    ACTIONS(2535), 1,
      anon_sym_LPAREN,
  [17879] = 1,
    ACTIONS(2537), 1,
      anon_sym_LPAREN,
  [17883] = 1,
    ACTIONS(2539), 1,
      anon_sym_LPAREN,
  [17887] = 1,
    ACTIONS(2541), 1,
      anon_sym_SEMI,
  [17891] = 1,
    ACTIONS(2543), 1,
      anon_sym_RPAREN,
  [17895] = 1,
    ACTIONS(2545), 1,
      anon_sym_LPAREN,
  [17899] = 1,
    ACTIONS(2547), 1,
      anon_sym_RPAREN,
  [17903] = 1,
    ACTIONS(2549), 1,
      sym_string_literal,
  [17907] = 1,
    ACTIONS(2551), 1,
      anon_sym_RPAREN,
  [17911] = 1,
    ACTIONS(2553), 1,
      anon_sym_RPAREN,
  [17915] = 1,
    ACTIONS(2555), 1,
      anon_sym_RPAREN,
  [17919] = 1,
    ACTIONS(2557), 1,
      anon_sym_RPAREN,
  [17923] = 1,
    ACTIONS(2559), 1,
      anon_sym_COLON,
  [17927] = 1,
    ACTIONS(2561), 1,
      anon_sym_LPAREN,
  [17931] = 1,
    ACTIONS(2563), 1,
      anon_sym_SEMI,
  [17935] = 1,
    ACTIONS(2565), 1,
      anon_sym_LPAREN,
  [17939] = 1,
    ACTIONS(2567), 1,
      anon_sym_RBRACK,
  [17943] = 1,
    ACTIONS(2569), 1,
      anon_sym_RBRACK,
  [17947] = 1,
    ACTIONS(2571), 1,
      anon_sym_COMMA,
  [17951] = 1,
    ACTIONS(2573), 1,
      anon_sym_SEMI,
  [17955] = 1,
    ACTIONS(2575), 1,
      anon_sym_COLON,
  [17959] = 1,
    ACTIONS(2577), 1,
      anon_sym_LPAREN_RPAREN,
  [17963] = 1,
    ACTIONS(2579), 1,
      anon_sym_RPAREN,
  [17967] = 1,
    ACTIONS(2581), 1,
      anon_sym_SEMI,
  [17971] = 1,
    ACTIONS(2583), 1,
      anon_sym_RPAREN,
  [17975] = 1,
    ACTIONS(2585), 1,
      anon_sym_COMMA,
  [17979] = 1,
    ACTIONS(2587), 1,
      anon_sym_COMMA,
  [17983] = 1,
    ACTIONS(2589), 1,
      anon_sym_SEMI,
  [17987] = 1,
    ACTIONS(2591), 1,
      anon_sym_RPAREN,
  [17991] = 1,
    ACTIONS(2593), 1,
      anon_sym_SEMI,
  [17995] = 1,
    ACTIONS(2595), 1,
      anon_sym_COMMA,
  [17999] = 1,
    ACTIONS(2597), 1,
      anon_sym_COMMA,
  [18003] = 1,
    ACTIONS(2599), 1,
      anon_sym_LPAREN_RPAREN,
  [18007] = 1,
    ACTIONS(2601), 1,
      sym_integer,
  [18011] = 1,
    ACTIONS(2603), 1,
      anon_sym_RPAREN,
  [18015] = 1,
    ACTIONS(2605), 1,
      anon_sym_SEMI,
  [18019] = 1,
    ACTIONS(2607), 1,
      anon_sym_RPAREN,
  [18023] = 1,
    ACTIONS(2609), 1,
      anon_sym_RPAREN,
  [18027] = 1,
    ACTIONS(2611), 1,
      sym_identifier,
  [18031] = 1,
    ACTIONS(2613), 1,
      anon_sym_LPAREN_RPAREN,
  [18035] = 1,
    ACTIONS(2615), 1,
      anon_sym_LPAREN,
  [18039] = 1,
    ACTIONS(2617), 1,
      anon_sym_RBRACK,
  [18043] = 1,
    ACTIONS(2619), 1,
      anon_sym_LPAREN,
  [18047] = 1,
    ACTIONS(2621), 1,
      anon_sym_LPAREN,
  [18051] = 1,
    ACTIONS(2623), 1,
      anon_sym_LPAREN,
  [18055] = 1,
    ACTIONS(2625), 1,
      anon_sym_LPAREN,
  [18059] = 1,
    ACTIONS(2627), 1,
      anon_sym_LPAREN,
  [18063] = 1,
    ACTIONS(2629), 1,
      anon_sym_LPAREN,
  [18067] = 1,
    ACTIONS(2631), 1,
      sym_permission_type,
};

static const uint32_t ts_small_parse_table_map[] = {
  [SMALL_STATE(2)] = 0,
  [SMALL_STATE(3)] = 74,
  [SMALL_STATE(4)] = 148,
  [SMALL_STATE(5)] = 221,
  [SMALL_STATE(6)] = 294,
  [SMALL_STATE(7)] = 367,
  [SMALL_STATE(8)] = 440,
  [SMALL_STATE(9)] = 513,
  [SMALL_STATE(10)] = 586,
  [SMALL_STATE(11)] = 659,
  [SMALL_STATE(12)] = 739,
  [SMALL_STATE(13)] = 819,
  [SMALL_STATE(14)] = 899,
  [SMALL_STATE(15)] = 979,
  [SMALL_STATE(16)] = 1059,
  [SMALL_STATE(17)] = 1139,
  [SMALL_STATE(18)] = 1219,
  [SMALL_STATE(19)] = 1299,
  [SMALL_STATE(20)] = 1379,
  [SMALL_STATE(21)] = 1459,
  [SMALL_STATE(22)] = 1539,
  [SMALL_STATE(23)] = 1619,
  [SMALL_STATE(24)] = 1699,
  [SMALL_STATE(25)] = 1779,
  [SMALL_STATE(26)] = 1859,
  [SMALL_STATE(27)] = 1939,
  [SMALL_STATE(28)] = 2019,
  [SMALL_STATE(29)] = 2099,
  [SMALL_STATE(30)] = 2179,
  [SMALL_STATE(31)] = 2259,
  [SMALL_STATE(32)] = 2339,
  [SMALL_STATE(33)] = 2419,
  [SMALL_STATE(34)] = 2499,
  [SMALL_STATE(35)] = 2579,
  [SMALL_STATE(36)] = 2659,
  [SMALL_STATE(37)] = 2739,
  [SMALL_STATE(38)] = 2816,
  [SMALL_STATE(39)] = 2893,
  [SMALL_STATE(40)] = 2970,
  [SMALL_STATE(41)] = 3047,
  [SMALL_STATE(42)] = 3123,
  [SMALL_STATE(43)] = 3199,
  [SMALL_STATE(44)] = 3275,
  [SMALL_STATE(45)] = 3330,
  [SMALL_STATE(46)] = 3385,
  [SMALL_STATE(47)] = 3465,
  [SMALL_STATE(48)] = 3499,
  [SMALL_STATE(49)] = 3530,
  [SMALL_STATE(50)] = 3569,
  [SMALL_STATE(51)] = 3608,
  [SMALL_STATE(52)] = 3647,
  [SMALL_STATE(53)] = 3676,
  [SMALL_STATE(54)] = 3707,
  [SMALL_STATE(55)] = 3746,
  [SMALL_STATE(56)] = 3775,
  [SMALL_STATE(57)] = 3826,
  [SMALL_STATE(58)] = 3855,
  [SMALL_STATE(59)] = 3884,
  [SMALL_STATE(60)] = 3913,
  [SMALL_STATE(61)] = 3942,
  [SMALL_STATE(62)] = 3993,
  [SMALL_STATE(63)] = 4044,
  [SMALL_STATE(64)] = 4073,
  [SMALL_STATE(65)] = 4103,
  [SMALL_STATE(66)] = 4133,
  [SMALL_STATE(67)] = 4171,
  [SMALL_STATE(68)] = 4197,
  [SMALL_STATE(69)] = 4223,
  [SMALL_STATE(70)] = 4261,
  [SMALL_STATE(71)] = 4291,
  [SMALL_STATE(72)] = 4329,
  [SMALL_STATE(73)] = 4367,
  [SMALL_STATE(74)] = 4397,
  [SMALL_STATE(75)] = 4424,
  [SMALL_STATE(76)] = 4453,
  [SMALL_STATE(77)] = 4482,
  [SMALL_STATE(78)] = 4511,
  [SMALL_STATE(79)] = 4538,
  [SMALL_STATE(80)] = 4565,
  [SMALL_STATE(81)] = 4594,
  [SMALL_STATE(82)] = 4621,
  [SMALL_STATE(83)] = 4648,
  [SMALL_STATE(84)] = 4701,
  [SMALL_STATE(85)] = 4728,
  [SMALL_STATE(86)] = 4755,
  [SMALL_STATE(87)] = 4808,
  [SMALL_STATE(88)] = 4835,
  [SMALL_STATE(89)] = 4880,
  [SMALL_STATE(90)] = 4907,
  [SMALL_STATE(91)] = 4934,
  [SMALL_STATE(92)] = 4961,
  [SMALL_STATE(93)] = 4988,
  [SMALL_STATE(94)] = 5015,
  [SMALL_STATE(95)] = 5040,
  [SMALL_STATE(96)] = 5067,
  [SMALL_STATE(97)] = 5092,
  [SMALL_STATE(98)] = 5119,
  [SMALL_STATE(99)] = 5146,
  [SMALL_STATE(100)] = 5173,
  [SMALL_STATE(101)] = 5218,
  [SMALL_STATE(102)] = 5263,
  [SMALL_STATE(103)] = 5308,
  [SMALL_STATE(104)] = 5335,
  [SMALL_STATE(105)] = 5363,
  [SMALL_STATE(106)] = 5389,
  [SMALL_STATE(107)] = 5415,
  [SMALL_STATE(108)] = 5441,
  [SMALL_STATE(109)] = 5467,
  [SMALL_STATE(110)] = 5493,
  [SMALL_STATE(111)] = 5519,
  [SMALL_STATE(112)] = 5545,
  [SMALL_STATE(113)] = 5585,
  [SMALL_STATE(114)] = 5611,
  [SMALL_STATE(115)] = 5637,
  [SMALL_STATE(116)] = 5661,
  [SMALL_STATE(117)] = 5687,
  [SMALL_STATE(118)] = 5713,
  [SMALL_STATE(119)] = 5741,
  [SMALL_STATE(120)] = 5767,
  [SMALL_STATE(121)] = 5793,
  [SMALL_STATE(122)] = 5829,
  [SMALL_STATE(123)] = 5865,
  [SMALL_STATE(124)] = 5917,
  [SMALL_STATE(125)] = 5969,
  [SMALL_STATE(126)] = 6005,
  [SMALL_STATE(127)] = 6057,
  [SMALL_STATE(128)] = 6093,
  [SMALL_STATE(129)] = 6125,
  [SMALL_STATE(130)] = 6157,
  [SMALL_STATE(131)] = 6189,
  [SMALL_STATE(132)] = 6221,
  [SMALL_STATE(133)] = 6253,
  [SMALL_STATE(134)] = 6279,
  [SMALL_STATE(135)] = 6311,
  [SMALL_STATE(136)] = 6343,
  [SMALL_STATE(137)] = 6369,
  [SMALL_STATE(138)] = 6398,
  [SMALL_STATE(139)] = 6427,
  [SMALL_STATE(140)] = 6456,
  [SMALL_STATE(141)] = 6485,
  [SMALL_STATE(142)] = 6514,
  [SMALL_STATE(143)] = 6543,
  [SMALL_STATE(144)] = 6572,
  [SMALL_STATE(145)] = 6601,
  [SMALL_STATE(146)] = 6630,
  [SMALL_STATE(147)] = 6659,
  [SMALL_STATE(148)] = 6688,
  [SMALL_STATE(149)] = 6707,
  [SMALL_STATE(150)] = 6736,
  [SMALL_STATE(151)] = 6765,
  [SMALL_STATE(152)] = 6794,
  [SMALL_STATE(153)] = 6823,
  [SMALL_STATE(154)] = 6852,
  [SMALL_STATE(155)] = 6881,
  [SMALL_STATE(156)] = 6910,
  [SMALL_STATE(157)] = 6939,
  [SMALL_STATE(158)] = 6968,
  [SMALL_STATE(159)] = 6997,
  [SMALL_STATE(160)] = 7026,
  [SMALL_STATE(161)] = 7055,
  [SMALL_STATE(162)] = 7084,
  [SMALL_STATE(163)] = 7113,
  [SMALL_STATE(164)] = 7142,
  [SMALL_STATE(165)] = 7171,
  [SMALL_STATE(166)] = 7200,
  [SMALL_STATE(167)] = 7229,
  [SMALL_STATE(168)] = 7258,
  [SMALL_STATE(169)] = 7287,
  [SMALL_STATE(170)] = 7316,
  [SMALL_STATE(171)] = 7345,
  [SMALL_STATE(172)] = 7365,
  [SMALL_STATE(173)] = 7385,
  [SMALL_STATE(174)] = 7402,
  [SMALL_STATE(175)] = 7425,
  [SMALL_STATE(176)] = 7442,
  [SMALL_STATE(177)] = 7459,
  [SMALL_STATE(178)] = 7476,
  [SMALL_STATE(179)] = 7493,
  [SMALL_STATE(180)] = 7526,
  [SMALL_STATE(181)] = 7559,
  [SMALL_STATE(182)] = 7576,
  [SMALL_STATE(183)] = 7593,
  [SMALL_STATE(184)] = 7610,
  [SMALL_STATE(185)] = 7627,
  [SMALL_STATE(186)] = 7644,
  [SMALL_STATE(187)] = 7661,
  [SMALL_STATE(188)] = 7678,
  [SMALL_STATE(189)] = 7695,
  [SMALL_STATE(190)] = 7712,
  [SMALL_STATE(191)] = 7733,
  [SMALL_STATE(192)] = 7750,
  [SMALL_STATE(193)] = 7767,
  [SMALL_STATE(194)] = 7784,
  [SMALL_STATE(195)] = 7801,
  [SMALL_STATE(196)] = 7818,
  [SMALL_STATE(197)] = 7835,
  [SMALL_STATE(198)] = 7852,
  [SMALL_STATE(199)] = 7869,
  [SMALL_STATE(200)] = 7886,
  [SMALL_STATE(201)] = 7903,
  [SMALL_STATE(202)] = 7920,
  [SMALL_STATE(203)] = 7937,
  [SMALL_STATE(204)] = 7954,
  [SMALL_STATE(205)] = 7971,
  [SMALL_STATE(206)] = 7988,
  [SMALL_STATE(207)] = 8005,
  [SMALL_STATE(208)] = 8024,
  [SMALL_STATE(209)] = 8041,
  [SMALL_STATE(210)] = 8058,
  [SMALL_STATE(211)] = 8075,
  [SMALL_STATE(212)] = 8092,
  [SMALL_STATE(213)] = 8109,
  [SMALL_STATE(214)] = 8126,
  [SMALL_STATE(215)] = 8143,
  [SMALL_STATE(216)] = 8160,
  [SMALL_STATE(217)] = 8177,
  [SMALL_STATE(218)] = 8194,
  [SMALL_STATE(219)] = 8211,
  [SMALL_STATE(220)] = 8228,
  [SMALL_STATE(221)] = 8245,
  [SMALL_STATE(222)] = 8262,
  [SMALL_STATE(223)] = 8279,
  [SMALL_STATE(224)] = 8296,
  [SMALL_STATE(225)] = 8313,
  [SMALL_STATE(226)] = 8330,
  [SMALL_STATE(227)] = 8347,
  [SMALL_STATE(228)] = 8364,
  [SMALL_STATE(229)] = 8381,
  [SMALL_STATE(230)] = 8398,
  [SMALL_STATE(231)] = 8415,
  [SMALL_STATE(232)] = 8432,
  [SMALL_STATE(233)] = 8449,
  [SMALL_STATE(234)] = 8466,
  [SMALL_STATE(235)] = 8487,
  [SMALL_STATE(236)] = 8504,
  [SMALL_STATE(237)] = 8521,
  [SMALL_STATE(238)] = 8540,
  [SMALL_STATE(239)] = 8561,
  [SMALL_STATE(240)] = 8578,
  [SMALL_STATE(241)] = 8595,
  [SMALL_STATE(242)] = 8612,
  [SMALL_STATE(243)] = 8629,
  [SMALL_STATE(244)] = 8646,
  [SMALL_STATE(245)] = 8665,
  [SMALL_STATE(246)] = 8686,
  [SMALL_STATE(247)] = 8703,
  [SMALL_STATE(248)] = 8720,
  [SMALL_STATE(249)] = 8741,
  [SMALL_STATE(250)] = 8762,
  [SMALL_STATE(251)] = 8783,
  [SMALL_STATE(252)] = 8802,
  [SMALL_STATE(253)] = 8821,
  [SMALL_STATE(254)] = 8852,
  [SMALL_STATE(255)] = 8871,
  [SMALL_STATE(256)] = 8892,
  [SMALL_STATE(257)] = 8925,
  [SMALL_STATE(258)] = 8944,
  [SMALL_STATE(259)] = 8961,
  [SMALL_STATE(260)] = 8980,
  [SMALL_STATE(261)] = 8999,
  [SMALL_STATE(262)] = 9016,
  [SMALL_STATE(263)] = 9035,
  [SMALL_STATE(264)] = 9054,
  [SMALL_STATE(265)] = 9073,
  [SMALL_STATE(266)] = 9092,
  [SMALL_STATE(267)] = 9111,
  [SMALL_STATE(268)] = 9130,
  [SMALL_STATE(269)] = 9149,
  [SMALL_STATE(270)] = 9168,
  [SMALL_STATE(271)] = 9187,
  [SMALL_STATE(272)] = 9206,
  [SMALL_STATE(273)] = 9225,
  [SMALL_STATE(274)] = 9244,
  [SMALL_STATE(275)] = 9263,
  [SMALL_STATE(276)] = 9282,
  [SMALL_STATE(277)] = 9301,
  [SMALL_STATE(278)] = 9320,
  [SMALL_STATE(279)] = 9339,
  [SMALL_STATE(280)] = 9358,
  [SMALL_STATE(281)] = 9377,
  [SMALL_STATE(282)] = 9396,
  [SMALL_STATE(283)] = 9415,
  [SMALL_STATE(284)] = 9434,
  [SMALL_STATE(285)] = 9455,
  [SMALL_STATE(286)] = 9476,
  [SMALL_STATE(287)] = 9495,
  [SMALL_STATE(288)] = 9514,
  [SMALL_STATE(289)] = 9533,
  [SMALL_STATE(290)] = 9566,
  [SMALL_STATE(291)] = 9585,
  [SMALL_STATE(292)] = 9604,
  [SMALL_STATE(293)] = 9623,
  [SMALL_STATE(294)] = 9642,
  [SMALL_STATE(295)] = 9661,
  [SMALL_STATE(296)] = 9680,
  [SMALL_STATE(297)] = 9699,
  [SMALL_STATE(298)] = 9718,
  [SMALL_STATE(299)] = 9737,
  [SMALL_STATE(300)] = 9756,
  [SMALL_STATE(301)] = 9775,
  [SMALL_STATE(302)] = 9794,
  [SMALL_STATE(303)] = 9813,
  [SMALL_STATE(304)] = 9832,
  [SMALL_STATE(305)] = 9851,
  [SMALL_STATE(306)] = 9870,
  [SMALL_STATE(307)] = 9889,
  [SMALL_STATE(308)] = 9908,
  [SMALL_STATE(309)] = 9927,
  [SMALL_STATE(310)] = 9946,
  [SMALL_STATE(311)] = 9965,
  [SMALL_STATE(312)] = 9984,
  [SMALL_STATE(313)] = 10003,
  [SMALL_STATE(314)] = 10022,
  [SMALL_STATE(315)] = 10043,
  [SMALL_STATE(316)] = 10064,
  [SMALL_STATE(317)] = 10081,
  [SMALL_STATE(318)] = 10100,
  [SMALL_STATE(319)] = 10118,
  [SMALL_STATE(320)] = 10136,
  [SMALL_STATE(321)] = 10164,
  [SMALL_STATE(322)] = 10182,
  [SMALL_STATE(323)] = 10200,
  [SMALL_STATE(324)] = 10218,
  [SMALL_STATE(325)] = 10248,
  [SMALL_STATE(326)] = 10266,
  [SMALL_STATE(327)] = 10284,
  [SMALL_STATE(328)] = 10302,
  [SMALL_STATE(329)] = 10320,
  [SMALL_STATE(330)] = 10338,
  [SMALL_STATE(331)] = 10356,
  [SMALL_STATE(332)] = 10374,
  [SMALL_STATE(333)] = 10392,
  [SMALL_STATE(334)] = 10410,
  [SMALL_STATE(335)] = 10428,
  [SMALL_STATE(336)] = 10446,
  [SMALL_STATE(337)] = 10464,
  [SMALL_STATE(338)] = 10482,
  [SMALL_STATE(339)] = 10500,
  [SMALL_STATE(340)] = 10518,
  [SMALL_STATE(341)] = 10536,
  [SMALL_STATE(342)] = 10554,
  [SMALL_STATE(343)] = 10572,
  [SMALL_STATE(344)] = 10590,
  [SMALL_STATE(345)] = 10608,
  [SMALL_STATE(346)] = 10628,
  [SMALL_STATE(347)] = 10646,
  [SMALL_STATE(348)] = 10664,
  [SMALL_STATE(349)] = 10686,
  [SMALL_STATE(350)] = 10716,
  [SMALL_STATE(351)] = 10734,
  [SMALL_STATE(352)] = 10752,
  [SMALL_STATE(353)] = 10770,
  [SMALL_STATE(354)] = 10788,
  [SMALL_STATE(355)] = 10806,
  [SMALL_STATE(356)] = 10824,
  [SMALL_STATE(357)] = 10842,
  [SMALL_STATE(358)] = 10860,
  [SMALL_STATE(359)] = 10878,
  [SMALL_STATE(360)] = 10896,
  [SMALL_STATE(361)] = 10924,
  [SMALL_STATE(362)] = 10942,
  [SMALL_STATE(363)] = 10960,
  [SMALL_STATE(364)] = 10980,
  [SMALL_STATE(365)] = 10998,
  [SMALL_STATE(366)] = 11018,
  [SMALL_STATE(367)] = 11036,
  [SMALL_STATE(368)] = 11054,
  [SMALL_STATE(369)] = 11072,
  [SMALL_STATE(370)] = 11090,
  [SMALL_STATE(371)] = 11110,
  [SMALL_STATE(372)] = 11128,
  [SMALL_STATE(373)] = 11148,
  [SMALL_STATE(374)] = 11166,
  [SMALL_STATE(375)] = 11184,
  [SMALL_STATE(376)] = 11202,
  [SMALL_STATE(377)] = 11220,
  [SMALL_STATE(378)] = 11238,
  [SMALL_STATE(379)] = 11256,
  [SMALL_STATE(380)] = 11274,
  [SMALL_STATE(381)] = 11292,
  [SMALL_STATE(382)] = 11322,
  [SMALL_STATE(383)] = 11342,
  [SMALL_STATE(384)] = 11362,
  [SMALL_STATE(385)] = 11380,
  [SMALL_STATE(386)] = 11398,
  [SMALL_STATE(387)] = 11418,
  [SMALL_STATE(388)] = 11436,
  [SMALL_STATE(389)] = 11456,
  [SMALL_STATE(390)] = 11474,
  [SMALL_STATE(391)] = 11504,
  [SMALL_STATE(392)] = 11534,
  [SMALL_STATE(393)] = 11564,
  [SMALL_STATE(394)] = 11594,
  [SMALL_STATE(395)] = 11612,
  [SMALL_STATE(396)] = 11630,
  [SMALL_STATE(397)] = 11648,
  [SMALL_STATE(398)] = 11663,
  [SMALL_STATE(399)] = 11678,
  [SMALL_STATE(400)] = 11703,
  [SMALL_STATE(401)] = 11718,
  [SMALL_STATE(402)] = 11733,
  [SMALL_STATE(403)] = 11748,
  [SMALL_STATE(404)] = 11763,
  [SMALL_STATE(405)] = 11782,
  [SMALL_STATE(406)] = 11797,
  [SMALL_STATE(407)] = 11816,
  [SMALL_STATE(408)] = 11833,
  [SMALL_STATE(409)] = 11870,
  [SMALL_STATE(410)] = 11885,
  [SMALL_STATE(411)] = 11900,
  [SMALL_STATE(412)] = 11915,
  [SMALL_STATE(413)] = 11939,
  [SMALL_STATE(414)] = 11963,
  [SMALL_STATE(415)] = 11977,
  [SMALL_STATE(416)] = 11999,
  [SMALL_STATE(417)] = 12023,
  [SMALL_STATE(418)] = 12045,
  [SMALL_STATE(419)] = 12069,
  [SMALL_STATE(420)] = 12093,
  [SMALL_STATE(421)] = 12117,
  [SMALL_STATE(422)] = 12139,
  [SMALL_STATE(423)] = 12163,
  [SMALL_STATE(424)] = 12181,
  [SMALL_STATE(425)] = 12205,
  [SMALL_STATE(426)] = 12227,
  [SMALL_STATE(427)] = 12251,
  [SMALL_STATE(428)] = 12269,
  [SMALL_STATE(429)] = 12293,
  [SMALL_STATE(430)] = 12317,
  [SMALL_STATE(431)] = 12335,
  [SMALL_STATE(432)] = 12351,
  [SMALL_STATE(433)] = 12375,
  [SMALL_STATE(434)] = 12409,
  [SMALL_STATE(435)] = 12433,
  [SMALL_STATE(436)] = 12467,
  [SMALL_STATE(437)] = 12491,
  [SMALL_STATE(438)] = 12525,
  [SMALL_STATE(439)] = 12559,
  [SMALL_STATE(440)] = 12583,
  [SMALL_STATE(441)] = 12607,
  [SMALL_STATE(442)] = 12631,
  [SMALL_STATE(443)] = 12652,
  [SMALL_STATE(444)] = 12665,
  [SMALL_STATE(445)] = 12678,
  [SMALL_STATE(446)] = 12695,
  [SMALL_STATE(447)] = 12712,
  [SMALL_STATE(448)] = 12733,
  [SMALL_STATE(449)] = 12746,
  [SMALL_STATE(450)] = 12767,
  [SMALL_STATE(451)] = 12780,
  [SMALL_STATE(452)] = 12793,
  [SMALL_STATE(453)] = 12814,
  [SMALL_STATE(454)] = 12828,
  [SMALL_STATE(455)] = 12842,
  [SMALL_STATE(456)] = 12856,
  [SMALL_STATE(457)] = 12884,
  [SMALL_STATE(458)] = 12898,
  [SMALL_STATE(459)] = 12926,
  [SMALL_STATE(460)] = 12950,
  [SMALL_STATE(461)] = 12978,
  [SMALL_STATE(462)] = 12996,
  [SMALL_STATE(463)] = 13014,
  [SMALL_STATE(464)] = 13042,
  [SMALL_STATE(465)] = 13070,
  [SMALL_STATE(466)] = 13094,
  [SMALL_STATE(467)] = 13122,
  [SMALL_STATE(468)] = 13150,
  [SMALL_STATE(469)] = 13176,
  [SMALL_STATE(470)] = 13202,
  [SMALL_STATE(471)] = 13230,
  [SMALL_STATE(472)] = 13255,
  [SMALL_STATE(473)] = 13268,
  [SMALL_STATE(474)] = 13281,
  [SMALL_STATE(475)] = 13296,
  [SMALL_STATE(476)] = 13321,
  [SMALL_STATE(477)] = 13346,
  [SMALL_STATE(478)] = 13361,
  [SMALL_STATE(479)] = 13386,
  [SMALL_STATE(480)] = 13411,
  [SMALL_STATE(481)] = 13424,
  [SMALL_STATE(482)] = 13437,
  [SMALL_STATE(483)] = 13462,
  [SMALL_STATE(484)] = 13487,
  [SMALL_STATE(485)] = 13512,
  [SMALL_STATE(486)] = 13522,
  [SMALL_STATE(487)] = 13532,
  [SMALL_STATE(488)] = 13542,
  [SMALL_STATE(489)] = 13558,
  [SMALL_STATE(490)] = 13570,
  [SMALL_STATE(491)] = 13582,
  [SMALL_STATE(492)] = 13598,
  [SMALL_STATE(493)] = 13608,
  [SMALL_STATE(494)] = 13618,
  [SMALL_STATE(495)] = 13628,
  [SMALL_STATE(496)] = 13638,
  [SMALL_STATE(497)] = 13648,
  [SMALL_STATE(498)] = 13658,
  [SMALL_STATE(499)] = 13670,
  [SMALL_STATE(500)] = 13680,
  [SMALL_STATE(501)] = 13692,
  [SMALL_STATE(502)] = 13702,
  [SMALL_STATE(503)] = 13721,
  [SMALL_STATE(504)] = 13740,
  [SMALL_STATE(505)] = 13749,
  [SMALL_STATE(506)] = 13768,
  [SMALL_STATE(507)] = 13787,
  [SMALL_STATE(508)] = 13806,
  [SMALL_STATE(509)] = 13825,
  [SMALL_STATE(510)] = 13844,
  [SMALL_STATE(511)] = 13863,
  [SMALL_STATE(512)] = 13882,
  [SMALL_STATE(513)] = 13898,
  [SMALL_STATE(514)] = 13914,
  [SMALL_STATE(515)] = 13930,
  [SMALL_STATE(516)] = 13940,
  [SMALL_STATE(517)] = 13954,
  [SMALL_STATE(518)] = 13968,
  [SMALL_STATE(519)] = 13982,
  [SMALL_STATE(520)] = 13998,
  [SMALL_STATE(521)] = 14012,
  [SMALL_STATE(522)] = 14028,
  [SMALL_STATE(523)] = 14044,
  [SMALL_STATE(524)] = 14058,
  [SMALL_STATE(525)] = 14072,
  [SMALL_STATE(526)] = 14084,
  [SMALL_STATE(527)] = 14098,
  [SMALL_STATE(528)] = 14112,
  [SMALL_STATE(529)] = 14126,
  [SMALL_STATE(530)] = 14138,
  [SMALL_STATE(531)] = 14152,
  [SMALL_STATE(532)] = 14168,
  [SMALL_STATE(533)] = 14179,
  [SMALL_STATE(534)] = 14192,
  [SMALL_STATE(535)] = 14205,
  [SMALL_STATE(536)] = 14216,
  [SMALL_STATE(537)] = 14227,
  [SMALL_STATE(538)] = 14240,
  [SMALL_STATE(539)] = 14253,
  [SMALL_STATE(540)] = 14264,
  [SMALL_STATE(541)] = 14277,
  [SMALL_STATE(542)] = 14290,
  [SMALL_STATE(543)] = 14301,
  [SMALL_STATE(544)] = 14312,
  [SMALL_STATE(545)] = 14323,
  [SMALL_STATE(546)] = 14336,
  [SMALL_STATE(547)] = 14349,
  [SMALL_STATE(548)] = 14362,
  [SMALL_STATE(549)] = 14373,
  [SMALL_STATE(550)] = 14384,
  [SMALL_STATE(551)] = 14395,
  [SMALL_STATE(552)] = 14406,
  [SMALL_STATE(553)] = 14417,
  [SMALL_STATE(554)] = 14428,
  [SMALL_STATE(555)] = 14439,
  [SMALL_STATE(556)] = 14452,
  [SMALL_STATE(557)] = 14463,
  [SMALL_STATE(558)] = 14474,
  [SMALL_STATE(559)] = 14487,
  [SMALL_STATE(560)] = 14498,
  [SMALL_STATE(561)] = 14511,
  [SMALL_STATE(562)] = 14522,
  [SMALL_STATE(563)] = 14533,
  [SMALL_STATE(564)] = 14544,
  [SMALL_STATE(565)] = 14555,
  [SMALL_STATE(566)] = 14566,
  [SMALL_STATE(567)] = 14577,
  [SMALL_STATE(568)] = 14590,
  [SMALL_STATE(569)] = 14603,
  [SMALL_STATE(570)] = 14616,
  [SMALL_STATE(571)] = 14629,
  [SMALL_STATE(572)] = 14642,
  [SMALL_STATE(573)] = 14655,
  [SMALL_STATE(574)] = 14668,
  [SMALL_STATE(575)] = 14681,
  [SMALL_STATE(576)] = 14692,
  [SMALL_STATE(577)] = 14703,
  [SMALL_STATE(578)] = 14714,
  [SMALL_STATE(579)] = 14725,
  [SMALL_STATE(580)] = 14736,
  [SMALL_STATE(581)] = 14749,
  [SMALL_STATE(582)] = 14762,
  [SMALL_STATE(583)] = 14775,
  [SMALL_STATE(584)] = 14786,
  [SMALL_STATE(585)] = 14799,
  [SMALL_STATE(586)] = 14812,
  [SMALL_STATE(587)] = 14819,
  [SMALL_STATE(588)] = 14830,
  [SMALL_STATE(589)] = 14843,
  [SMALL_STATE(590)] = 14856,
  [SMALL_STATE(591)] = 14867,
  [SMALL_STATE(592)] = 14878,
  [SMALL_STATE(593)] = 14889,
  [SMALL_STATE(594)] = 14896,
  [SMALL_STATE(595)] = 14907,
  [SMALL_STATE(596)] = 14918,
  [SMALL_STATE(597)] = 14931,
  [SMALL_STATE(598)] = 14944,
  [SMALL_STATE(599)] = 14953,
  [SMALL_STATE(600)] = 14966,
  [SMALL_STATE(601)] = 14977,
  [SMALL_STATE(602)] = 14986,
  [SMALL_STATE(603)] = 14997,
  [SMALL_STATE(604)] = 15010,
  [SMALL_STATE(605)] = 15021,
  [SMALL_STATE(606)] = 15032,
  [SMALL_STATE(607)] = 15041,
  [SMALL_STATE(608)] = 15052,
  [SMALL_STATE(609)] = 15065,
  [SMALL_STATE(610)] = 15078,
  [SMALL_STATE(611)] = 15089,
  [SMALL_STATE(612)] = 15102,
  [SMALL_STATE(613)] = 15108,
  [SMALL_STATE(614)] = 15118,
  [SMALL_STATE(615)] = 15128,
  [SMALL_STATE(616)] = 15138,
  [SMALL_STATE(617)] = 15148,
  [SMALL_STATE(618)] = 15158,
  [SMALL_STATE(619)] = 15168,
  [SMALL_STATE(620)] = 15174,
  [SMALL_STATE(621)] = 15184,
  [SMALL_STATE(622)] = 15192,
  [SMALL_STATE(623)] = 15202,
  [SMALL_STATE(624)] = 15212,
  [SMALL_STATE(625)] = 15222,
  [SMALL_STATE(626)] = 15232,
  [SMALL_STATE(627)] = 15242,
  [SMALL_STATE(628)] = 15252,
  [SMALL_STATE(629)] = 15262,
  [SMALL_STATE(630)] = 15272,
  [SMALL_STATE(631)] = 15282,
  [SMALL_STATE(632)] = 15292,
  [SMALL_STATE(633)] = 15302,
  [SMALL_STATE(634)] = 15312,
  [SMALL_STATE(635)] = 15322,
  [SMALL_STATE(636)] = 15332,
  [SMALL_STATE(637)] = 15342,
  [SMALL_STATE(638)] = 15350,
  [SMALL_STATE(639)] = 15356,
  [SMALL_STATE(640)] = 15366,
  [SMALL_STATE(641)] = 15376,
  [SMALL_STATE(642)] = 15382,
  [SMALL_STATE(643)] = 15392,
  [SMALL_STATE(644)] = 15402,
  [SMALL_STATE(645)] = 15410,
  [SMALL_STATE(646)] = 15420,
  [SMALL_STATE(647)] = 15430,
  [SMALL_STATE(648)] = 15438,
  [SMALL_STATE(649)] = 15448,
  [SMALL_STATE(650)] = 15454,
  [SMALL_STATE(651)] = 15464,
  [SMALL_STATE(652)] = 15472,
  [SMALL_STATE(653)] = 15478,
  [SMALL_STATE(654)] = 15488,
  [SMALL_STATE(655)] = 15498,
  [SMALL_STATE(656)] = 15506,
  [SMALL_STATE(657)] = 15514,
  [SMALL_STATE(658)] = 15520,
  [SMALL_STATE(659)] = 15526,
  [SMALL_STATE(660)] = 15536,
  [SMALL_STATE(661)] = 15546,
  [SMALL_STATE(662)] = 15556,
  [SMALL_STATE(663)] = 15566,
  [SMALL_STATE(664)] = 15576,
  [SMALL_STATE(665)] = 15586,
  [SMALL_STATE(666)] = 15596,
  [SMALL_STATE(667)] = 15606,
  [SMALL_STATE(668)] = 15616,
  [SMALL_STATE(669)] = 15624,
  [SMALL_STATE(670)] = 15632,
  [SMALL_STATE(671)] = 15638,
  [SMALL_STATE(672)] = 15644,
  [SMALL_STATE(673)] = 15650,
  [SMALL_STATE(674)] = 15658,
  [SMALL_STATE(675)] = 15668,
  [SMALL_STATE(676)] = 15678,
  [SMALL_STATE(677)] = 15688,
  [SMALL_STATE(678)] = 15696,
  [SMALL_STATE(679)] = 15706,
  [SMALL_STATE(680)] = 15714,
  [SMALL_STATE(681)] = 15722,
  [SMALL_STATE(682)] = 15728,
  [SMALL_STATE(683)] = 15734,
  [SMALL_STATE(684)] = 15740,
  [SMALL_STATE(685)] = 15750,
  [SMALL_STATE(686)] = 15760,
  [SMALL_STATE(687)] = 15768,
  [SMALL_STATE(688)] = 15776,
  [SMALL_STATE(689)] = 15786,
  [SMALL_STATE(690)] = 15796,
  [SMALL_STATE(691)] = 15806,
  [SMALL_STATE(692)] = 15816,
  [SMALL_STATE(693)] = 15826,
  [SMALL_STATE(694)] = 15836,
  [SMALL_STATE(695)] = 15846,
  [SMALL_STATE(696)] = 15854,
  [SMALL_STATE(697)] = 15864,
  [SMALL_STATE(698)] = 15874,
  [SMALL_STATE(699)] = 15884,
  [SMALL_STATE(700)] = 15892,
  [SMALL_STATE(701)] = 15902,
  [SMALL_STATE(702)] = 15912,
  [SMALL_STATE(703)] = 15918,
  [SMALL_STATE(704)] = 15928,
  [SMALL_STATE(705)] = 15938,
  [SMALL_STATE(706)] = 15948,
  [SMALL_STATE(707)] = 15958,
  [SMALL_STATE(708)] = 15968,
  [SMALL_STATE(709)] = 15976,
  [SMALL_STATE(710)] = 15981,
  [SMALL_STATE(711)] = 15988,
  [SMALL_STATE(712)] = 15993,
  [SMALL_STATE(713)] = 15998,
  [SMALL_STATE(714)] = 16005,
  [SMALL_STATE(715)] = 16010,
  [SMALL_STATE(716)] = 16017,
  [SMALL_STATE(717)] = 16024,
  [SMALL_STATE(718)] = 16031,
  [SMALL_STATE(719)] = 16038,
  [SMALL_STATE(720)] = 16043,
  [SMALL_STATE(721)] = 16050,
  [SMALL_STATE(722)] = 16057,
  [SMALL_STATE(723)] = 16064,
  [SMALL_STATE(724)] = 16071,
  [SMALL_STATE(725)] = 16078,
  [SMALL_STATE(726)] = 16083,
  [SMALL_STATE(727)] = 16090,
  [SMALL_STATE(728)] = 16097,
  [SMALL_STATE(729)] = 16104,
  [SMALL_STATE(730)] = 16111,
  [SMALL_STATE(731)] = 16118,
  [SMALL_STATE(732)] = 16125,
  [SMALL_STATE(733)] = 16132,
  [SMALL_STATE(734)] = 16139,
  [SMALL_STATE(735)] = 16146,
  [SMALL_STATE(736)] = 16153,
  [SMALL_STATE(737)] = 16160,
  [SMALL_STATE(738)] = 16167,
  [SMALL_STATE(739)] = 16174,
  [SMALL_STATE(740)] = 16179,
  [SMALL_STATE(741)] = 16184,
  [SMALL_STATE(742)] = 16189,
  [SMALL_STATE(743)] = 16194,
  [SMALL_STATE(744)] = 16199,
  [SMALL_STATE(745)] = 16206,
  [SMALL_STATE(746)] = 16213,
  [SMALL_STATE(747)] = 16220,
  [SMALL_STATE(748)] = 16227,
  [SMALL_STATE(749)] = 16234,
  [SMALL_STATE(750)] = 16241,
  [SMALL_STATE(751)] = 16248,
  [SMALL_STATE(752)] = 16255,
  [SMALL_STATE(753)] = 16262,
  [SMALL_STATE(754)] = 16269,
  [SMALL_STATE(755)] = 16276,
  [SMALL_STATE(756)] = 16283,
  [SMALL_STATE(757)] = 16290,
  [SMALL_STATE(758)] = 16295,
  [SMALL_STATE(759)] = 16300,
  [SMALL_STATE(760)] = 16307,
  [SMALL_STATE(761)] = 16314,
  [SMALL_STATE(762)] = 16321,
  [SMALL_STATE(763)] = 16328,
  [SMALL_STATE(764)] = 16335,
  [SMALL_STATE(765)] = 16340,
  [SMALL_STATE(766)] = 16347,
  [SMALL_STATE(767)] = 16354,
  [SMALL_STATE(768)] = 16361,
  [SMALL_STATE(769)] = 16366,
  [SMALL_STATE(770)] = 16371,
  [SMALL_STATE(771)] = 16378,
  [SMALL_STATE(772)] = 16383,
  [SMALL_STATE(773)] = 16390,
  [SMALL_STATE(774)] = 16397,
  [SMALL_STATE(775)] = 16404,
  [SMALL_STATE(776)] = 16409,
  [SMALL_STATE(777)] = 16416,
  [SMALL_STATE(778)] = 16423,
  [SMALL_STATE(779)] = 16430,
  [SMALL_STATE(780)] = 16435,
  [SMALL_STATE(781)] = 16440,
  [SMALL_STATE(782)] = 16447,
  [SMALL_STATE(783)] = 16454,
  [SMALL_STATE(784)] = 16461,
  [SMALL_STATE(785)] = 16468,
  [SMALL_STATE(786)] = 16475,
  [SMALL_STATE(787)] = 16482,
  [SMALL_STATE(788)] = 16489,
  [SMALL_STATE(789)] = 16496,
  [SMALL_STATE(790)] = 16503,
  [SMALL_STATE(791)] = 16510,
  [SMALL_STATE(792)] = 16517,
  [SMALL_STATE(793)] = 16524,
  [SMALL_STATE(794)] = 16531,
  [SMALL_STATE(795)] = 16538,
  [SMALL_STATE(796)] = 16545,
  [SMALL_STATE(797)] = 16550,
  [SMALL_STATE(798)] = 16557,
  [SMALL_STATE(799)] = 16564,
  [SMALL_STATE(800)] = 16571,
  [SMALL_STATE(801)] = 16576,
  [SMALL_STATE(802)] = 16581,
  [SMALL_STATE(803)] = 16588,
  [SMALL_STATE(804)] = 16595,
  [SMALL_STATE(805)] = 16602,
  [SMALL_STATE(806)] = 16607,
  [SMALL_STATE(807)] = 16614,
  [SMALL_STATE(808)] = 16619,
  [SMALL_STATE(809)] = 16626,
  [SMALL_STATE(810)] = 16633,
  [SMALL_STATE(811)] = 16640,
  [SMALL_STATE(812)] = 16647,
  [SMALL_STATE(813)] = 16654,
  [SMALL_STATE(814)] = 16659,
  [SMALL_STATE(815)] = 16666,
  [SMALL_STATE(816)] = 16673,
  [SMALL_STATE(817)] = 16680,
  [SMALL_STATE(818)] = 16685,
  [SMALL_STATE(819)] = 16690,
  [SMALL_STATE(820)] = 16697,
  [SMALL_STATE(821)] = 16702,
  [SMALL_STATE(822)] = 16709,
  [SMALL_STATE(823)] = 16716,
  [SMALL_STATE(824)] = 16721,
  [SMALL_STATE(825)] = 16726,
  [SMALL_STATE(826)] = 16733,
  [SMALL_STATE(827)] = 16738,
  [SMALL_STATE(828)] = 16743,
  [SMALL_STATE(829)] = 16748,
  [SMALL_STATE(830)] = 16755,
  [SMALL_STATE(831)] = 16759,
  [SMALL_STATE(832)] = 16763,
  [SMALL_STATE(833)] = 16767,
  [SMALL_STATE(834)] = 16771,
  [SMALL_STATE(835)] = 16775,
  [SMALL_STATE(836)] = 16779,
  [SMALL_STATE(837)] = 16783,
  [SMALL_STATE(838)] = 16787,
  [SMALL_STATE(839)] = 16791,
  [SMALL_STATE(840)] = 16795,
  [SMALL_STATE(841)] = 16799,
  [SMALL_STATE(842)] = 16803,
  [SMALL_STATE(843)] = 16807,
  [SMALL_STATE(844)] = 16811,
  [SMALL_STATE(845)] = 16815,
  [SMALL_STATE(846)] = 16819,
  [SMALL_STATE(847)] = 16823,
  [SMALL_STATE(848)] = 16827,
  [SMALL_STATE(849)] = 16831,
  [SMALL_STATE(850)] = 16835,
  [SMALL_STATE(851)] = 16839,
  [SMALL_STATE(852)] = 16843,
  [SMALL_STATE(853)] = 16847,
  [SMALL_STATE(854)] = 16851,
  [SMALL_STATE(855)] = 16855,
  [SMALL_STATE(856)] = 16859,
  [SMALL_STATE(857)] = 16863,
  [SMALL_STATE(858)] = 16867,
  [SMALL_STATE(859)] = 16871,
  [SMALL_STATE(860)] = 16875,
  [SMALL_STATE(861)] = 16879,
  [SMALL_STATE(862)] = 16883,
  [SMALL_STATE(863)] = 16887,
  [SMALL_STATE(864)] = 16891,
  [SMALL_STATE(865)] = 16895,
  [SMALL_STATE(866)] = 16899,
  [SMALL_STATE(867)] = 16903,
  [SMALL_STATE(868)] = 16907,
  [SMALL_STATE(869)] = 16911,
  [SMALL_STATE(870)] = 16915,
  [SMALL_STATE(871)] = 16919,
  [SMALL_STATE(872)] = 16923,
  [SMALL_STATE(873)] = 16927,
  [SMALL_STATE(874)] = 16931,
  [SMALL_STATE(875)] = 16935,
  [SMALL_STATE(876)] = 16939,
  [SMALL_STATE(877)] = 16943,
  [SMALL_STATE(878)] = 16947,
  [SMALL_STATE(879)] = 16951,
  [SMALL_STATE(880)] = 16955,
  [SMALL_STATE(881)] = 16959,
  [SMALL_STATE(882)] = 16963,
  [SMALL_STATE(883)] = 16967,
  [SMALL_STATE(884)] = 16971,
  [SMALL_STATE(885)] = 16975,
  [SMALL_STATE(886)] = 16979,
  [SMALL_STATE(887)] = 16983,
  [SMALL_STATE(888)] = 16987,
  [SMALL_STATE(889)] = 16991,
  [SMALL_STATE(890)] = 16995,
  [SMALL_STATE(891)] = 16999,
  [SMALL_STATE(892)] = 17003,
  [SMALL_STATE(893)] = 17007,
  [SMALL_STATE(894)] = 17011,
  [SMALL_STATE(895)] = 17015,
  [SMALL_STATE(896)] = 17019,
  [SMALL_STATE(897)] = 17023,
  [SMALL_STATE(898)] = 17027,
  [SMALL_STATE(899)] = 17031,
  [SMALL_STATE(900)] = 17035,
  [SMALL_STATE(901)] = 17039,
  [SMALL_STATE(902)] = 17043,
  [SMALL_STATE(903)] = 17047,
  [SMALL_STATE(904)] = 17051,
  [SMALL_STATE(905)] = 17055,
  [SMALL_STATE(906)] = 17059,
  [SMALL_STATE(907)] = 17063,
  [SMALL_STATE(908)] = 17067,
  [SMALL_STATE(909)] = 17071,
  [SMALL_STATE(910)] = 17075,
  [SMALL_STATE(911)] = 17079,
  [SMALL_STATE(912)] = 17083,
  [SMALL_STATE(913)] = 17087,
  [SMALL_STATE(914)] = 17091,
  [SMALL_STATE(915)] = 17095,
  [SMALL_STATE(916)] = 17099,
  [SMALL_STATE(917)] = 17103,
  [SMALL_STATE(918)] = 17107,
  [SMALL_STATE(919)] = 17111,
  [SMALL_STATE(920)] = 17115,
  [SMALL_STATE(921)] = 17119,
  [SMALL_STATE(922)] = 17123,
  [SMALL_STATE(923)] = 17127,
  [SMALL_STATE(924)] = 17131,
  [SMALL_STATE(925)] = 17135,
  [SMALL_STATE(926)] = 17139,
  [SMALL_STATE(927)] = 17143,
  [SMALL_STATE(928)] = 17147,
  [SMALL_STATE(929)] = 17151,
  [SMALL_STATE(930)] = 17155,
  [SMALL_STATE(931)] = 17159,
  [SMALL_STATE(932)] = 17163,
  [SMALL_STATE(933)] = 17167,
  [SMALL_STATE(934)] = 17171,
  [SMALL_STATE(935)] = 17175,
  [SMALL_STATE(936)] = 17179,
  [SMALL_STATE(937)] = 17183,
  [SMALL_STATE(938)] = 17187,
  [SMALL_STATE(939)] = 17191,
  [SMALL_STATE(940)] = 17195,
  [SMALL_STATE(941)] = 17199,
  [SMALL_STATE(942)] = 17203,
  [SMALL_STATE(943)] = 17207,
  [SMALL_STATE(944)] = 17211,
  [SMALL_STATE(945)] = 17215,
  [SMALL_STATE(946)] = 17219,
  [SMALL_STATE(947)] = 17223,
  [SMALL_STATE(948)] = 17227,
  [SMALL_STATE(949)] = 17231,
  [SMALL_STATE(950)] = 17235,
  [SMALL_STATE(951)] = 17239,
  [SMALL_STATE(952)] = 17243,
  [SMALL_STATE(953)] = 17247,
  [SMALL_STATE(954)] = 17251,
  [SMALL_STATE(955)] = 17255,
  [SMALL_STATE(956)] = 17259,
  [SMALL_STATE(957)] = 17263,
  [SMALL_STATE(958)] = 17267,
  [SMALL_STATE(959)] = 17271,
  [SMALL_STATE(960)] = 17275,
  [SMALL_STATE(961)] = 17279,
  [SMALL_STATE(962)] = 17283,
  [SMALL_STATE(963)] = 17287,
  [SMALL_STATE(964)] = 17291,
  [SMALL_STATE(965)] = 17295,
  [SMALL_STATE(966)] = 17299,
  [SMALL_STATE(967)] = 17303,
  [SMALL_STATE(968)] = 17307,
  [SMALL_STATE(969)] = 17311,
  [SMALL_STATE(970)] = 17315,
  [SMALL_STATE(971)] = 17319,
  [SMALL_STATE(972)] = 17323,
  [SMALL_STATE(973)] = 17327,
  [SMALL_STATE(974)] = 17331,
  [SMALL_STATE(975)] = 17335,
  [SMALL_STATE(976)] = 17339,
  [SMALL_STATE(977)] = 17343,
  [SMALL_STATE(978)] = 17347,
  [SMALL_STATE(979)] = 17351,
  [SMALL_STATE(980)] = 17355,
  [SMALL_STATE(981)] = 17359,
  [SMALL_STATE(982)] = 17363,
  [SMALL_STATE(983)] = 17367,
  [SMALL_STATE(984)] = 17371,
  [SMALL_STATE(985)] = 17375,
  [SMALL_STATE(986)] = 17379,
  [SMALL_STATE(987)] = 17383,
  [SMALL_STATE(988)] = 17387,
  [SMALL_STATE(989)] = 17391,
  [SMALL_STATE(990)] = 17395,
  [SMALL_STATE(991)] = 17399,
  [SMALL_STATE(992)] = 17403,
  [SMALL_STATE(993)] = 17407,
  [SMALL_STATE(994)] = 17411,
  [SMALL_STATE(995)] = 17415,
  [SMALL_STATE(996)] = 17419,
  [SMALL_STATE(997)] = 17423,
  [SMALL_STATE(998)] = 17427,
  [SMALL_STATE(999)] = 17431,
  [SMALL_STATE(1000)] = 17435,
  [SMALL_STATE(1001)] = 17439,
  [SMALL_STATE(1002)] = 17443,
  [SMALL_STATE(1003)] = 17447,
  [SMALL_STATE(1004)] = 17451,
  [SMALL_STATE(1005)] = 17455,
  [SMALL_STATE(1006)] = 17459,
  [SMALL_STATE(1007)] = 17463,
  [SMALL_STATE(1008)] = 17467,
  [SMALL_STATE(1009)] = 17471,
  [SMALL_STATE(1010)] = 17475,
  [SMALL_STATE(1011)] = 17479,
  [SMALL_STATE(1012)] = 17483,
  [SMALL_STATE(1013)] = 17487,
  [SMALL_STATE(1014)] = 17491,
  [SMALL_STATE(1015)] = 17495,
  [SMALL_STATE(1016)] = 17499,
  [SMALL_STATE(1017)] = 17503,
  [SMALL_STATE(1018)] = 17507,
  [SMALL_STATE(1019)] = 17511,
  [SMALL_STATE(1020)] = 17515,
  [SMALL_STATE(1021)] = 17519,
  [SMALL_STATE(1022)] = 17523,
  [SMALL_STATE(1023)] = 17527,
  [SMALL_STATE(1024)] = 17531,
  [SMALL_STATE(1025)] = 17535,
  [SMALL_STATE(1026)] = 17539,
  [SMALL_STATE(1027)] = 17543,
  [SMALL_STATE(1028)] = 17547,
  [SMALL_STATE(1029)] = 17551,
  [SMALL_STATE(1030)] = 17555,
  [SMALL_STATE(1031)] = 17559,
  [SMALL_STATE(1032)] = 17563,
  [SMALL_STATE(1033)] = 17567,
  [SMALL_STATE(1034)] = 17571,
  [SMALL_STATE(1035)] = 17575,
  [SMALL_STATE(1036)] = 17579,
  [SMALL_STATE(1037)] = 17583,
  [SMALL_STATE(1038)] = 17587,
  [SMALL_STATE(1039)] = 17591,
  [SMALL_STATE(1040)] = 17595,
  [SMALL_STATE(1041)] = 17599,
  [SMALL_STATE(1042)] = 17603,
  [SMALL_STATE(1043)] = 17607,
  [SMALL_STATE(1044)] = 17611,
  [SMALL_STATE(1045)] = 17615,
  [SMALL_STATE(1046)] = 17619,
  [SMALL_STATE(1047)] = 17623,
  [SMALL_STATE(1048)] = 17627,
  [SMALL_STATE(1049)] = 17631,
  [SMALL_STATE(1050)] = 17635,
  [SMALL_STATE(1051)] = 17639,
  [SMALL_STATE(1052)] = 17643,
  [SMALL_STATE(1053)] = 17647,
  [SMALL_STATE(1054)] = 17651,
  [SMALL_STATE(1055)] = 17655,
  [SMALL_STATE(1056)] = 17659,
  [SMALL_STATE(1057)] = 17663,
  [SMALL_STATE(1058)] = 17667,
  [SMALL_STATE(1059)] = 17671,
  [SMALL_STATE(1060)] = 17675,
  [SMALL_STATE(1061)] = 17679,
  [SMALL_STATE(1062)] = 17683,
  [SMALL_STATE(1063)] = 17687,
  [SMALL_STATE(1064)] = 17691,
  [SMALL_STATE(1065)] = 17695,
  [SMALL_STATE(1066)] = 17699,
  [SMALL_STATE(1067)] = 17703,
  [SMALL_STATE(1068)] = 17707,
  [SMALL_STATE(1069)] = 17711,
  [SMALL_STATE(1070)] = 17715,
  [SMALL_STATE(1071)] = 17719,
  [SMALL_STATE(1072)] = 17723,
  [SMALL_STATE(1073)] = 17727,
  [SMALL_STATE(1074)] = 17731,
  [SMALL_STATE(1075)] = 17735,
  [SMALL_STATE(1076)] = 17739,
  [SMALL_STATE(1077)] = 17743,
  [SMALL_STATE(1078)] = 17747,
  [SMALL_STATE(1079)] = 17751,
  [SMALL_STATE(1080)] = 17755,
  [SMALL_STATE(1081)] = 17759,
  [SMALL_STATE(1082)] = 17763,
  [SMALL_STATE(1083)] = 17767,
  [SMALL_STATE(1084)] = 17771,
  [SMALL_STATE(1085)] = 17775,
  [SMALL_STATE(1086)] = 17779,
  [SMALL_STATE(1087)] = 17783,
  [SMALL_STATE(1088)] = 17787,
  [SMALL_STATE(1089)] = 17791,
  [SMALL_STATE(1090)] = 17795,
  [SMALL_STATE(1091)] = 17799,
  [SMALL_STATE(1092)] = 17803,
  [SMALL_STATE(1093)] = 17807,
  [SMALL_STATE(1094)] = 17811,
  [SMALL_STATE(1095)] = 17815,
  [SMALL_STATE(1096)] = 17819,
  [SMALL_STATE(1097)] = 17823,
  [SMALL_STATE(1098)] = 17827,
  [SMALL_STATE(1099)] = 17831,
  [SMALL_STATE(1100)] = 17835,
  [SMALL_STATE(1101)] = 17839,
  [SMALL_STATE(1102)] = 17843,
  [SMALL_STATE(1103)] = 17847,
  [SMALL_STATE(1104)] = 17851,
  [SMALL_STATE(1105)] = 17855,
  [SMALL_STATE(1106)] = 17859,
  [SMALL_STATE(1107)] = 17863,
  [SMALL_STATE(1108)] = 17867,
  [SMALL_STATE(1109)] = 17871,
  [SMALL_STATE(1110)] = 17875,
  [SMALL_STATE(1111)] = 17879,
  [SMALL_STATE(1112)] = 17883,
  [SMALL_STATE(1113)] = 17887,
  [SMALL_STATE(1114)] = 17891,
  [SMALL_STATE(1115)] = 17895,
  [SMALL_STATE(1116)] = 17899,
  [SMALL_STATE(1117)] = 17903,
  [SMALL_STATE(1118)] = 17907,
  [SMALL_STATE(1119)] = 17911,
  [SMALL_STATE(1120)] = 17915,
  [SMALL_STATE(1121)] = 17919,
  [SMALL_STATE(1122)] = 17923,
  [SMALL_STATE(1123)] = 17927,
  [SMALL_STATE(1124)] = 17931,
  [SMALL_STATE(1125)] = 17935,
  [SMALL_STATE(1126)] = 17939,
  [SMALL_STATE(1127)] = 17943,
  [SMALL_STATE(1128)] = 17947,
  [SMALL_STATE(1129)] = 17951,
  [SMALL_STATE(1130)] = 17955,
  [SMALL_STATE(1131)] = 17959,
  [SMALL_STATE(1132)] = 17963,
  [SMALL_STATE(1133)] = 17967,
  [SMALL_STATE(1134)] = 17971,
  [SMALL_STATE(1135)] = 17975,
  [SMALL_STATE(1136)] = 17979,
  [SMALL_STATE(1137)] = 17983,
  [SMALL_STATE(1138)] = 17987,
  [SMALL_STATE(1139)] = 17991,
  [SMALL_STATE(1140)] = 17995,
  [SMALL_STATE(1141)] = 17999,
  [SMALL_STATE(1142)] = 18003,
  [SMALL_STATE(1143)] = 18007,
  [SMALL_STATE(1144)] = 18011,
  [SMALL_STATE(1145)] = 18015,
  [SMALL_STATE(1146)] = 18019,
  [SMALL_STATE(1147)] = 18023,
  [SMALL_STATE(1148)] = 18027,
  [SMALL_STATE(1149)] = 18031,
  [SMALL_STATE(1150)] = 18035,
  [SMALL_STATE(1151)] = 18039,
  [SMALL_STATE(1152)] = 18043,
  [SMALL_STATE(1153)] = 18047,
  [SMALL_STATE(1154)] = 18051,
  [SMALL_STATE(1155)] = 18055,
  [SMALL_STATE(1156)] = 18059,
  [SMALL_STATE(1157)] = 18063,
  [SMALL_STATE(1158)] = 18067,
};

static const TSParseActionEntry ts_parse_actions[] = {
  [0] = {.entry = {.count = 0, .reusable = false}},
  [1] = {.entry = {.count = 1, .reusable = false}}, RECOVER(),
  [3] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_source_file, 0, 0, 0),
  [5] = {.entry = {.count = 1, .reusable = true}}, SHIFT(821),
  [7] = {.entry = {.count = 1, .reusable = true}}, SHIFT(787),
  [9] = {.entry = {.count = 1, .reusable = false}}, SHIFT(980),
  [11] = {.entry = {.count = 1, .reusable = false}}, SHIFT(985),
  [13] = {.entry = {.count = 1, .reusable = false}}, SHIFT(499),
  [15] = {.entry = {.count = 1, .reusable = false}}, SHIFT(480),
  [17] = {.entry = {.count = 1, .reusable = false}}, SHIFT(523),
  [19] = {.entry = {.count = 1, .reusable = false}}, SHIFT(579),
  [21] = {.entry = {.count = 1, .reusable = false}}, SHIFT(526),
  [23] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1044),
  [25] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1050),
  [27] = {.entry = {.count = 1, .reusable = false}}, SHIFT(800),
  [29] = {.entry = {.count = 1, .reusable = true}}, SHIFT(980),
  [31] = {.entry = {.count = 1, .reusable = true}}, SHIFT(985),
  [33] = {.entry = {.count = 1, .reusable = true}}, SHIFT(499),
  [35] = {.entry = {.count = 1, .reusable = true}}, SHIFT(480),
  [37] = {.entry = {.count = 1, .reusable = true}}, SHIFT(579),
  [39] = {.entry = {.count = 1, .reusable = true}}, SHIFT(526),
  [41] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1044),
  [43] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1050),
  [45] = {.entry = {.count = 1, .reusable = true}}, SHIFT(153),
  [47] = {.entry = {.count = 1, .reusable = false}}, SHIFT(165),
  [49] = {.entry = {.count = 1, .reusable = false}}, SHIFT(425),
  [51] = {.entry = {.count = 1, .reusable = true}}, SHIFT(559),
  [53] = {.entry = {.count = 1, .reusable = true}}, SHIFT(452),
  [55] = {.entry = {.count = 1, .reusable = false}}, SHIFT(207),
  [57] = {.entry = {.count = 1, .reusable = false}}, SHIFT(22),
  [59] = {.entry = {.count = 1, .reusable = false}}, SHIFT(37),
  [61] = {.entry = {.count = 1, .reusable = false}}, SHIFT(154),
  [63] = {.entry = {.count = 1, .reusable = false}}, SHIFT(284),
  [65] = {.entry = {.count = 1, .reusable = false}}, SHIFT(167),
  [67] = {.entry = {.count = 1, .reusable = false}}, SHIFT(421),
  [69] = {.entry = {.count = 1, .reusable = true}}, SHIFT(442),
  [71] = {.entry = {.count = 1, .reusable = false}}, SHIFT(21),
  [73] = {.entry = {.count = 1, .reusable = false}}, SHIFT(40),
  [75] = {.entry = {.count = 1, .reusable = false}}, SHIFT(169),
  [77] = {.entry = {.count = 1, .reusable = false}}, SHIFT(249),
  [79] = {.entry = {.count = 1, .reusable = false}}, SHIFT(163),
  [81] = {.entry = {.count = 1, .reusable = false}}, SHIFT(417),
  [83] = {.entry = {.count = 1, .reusable = true}}, SHIFT(449),
  [85] = {.entry = {.count = 1, .reusable = false}}, SHIFT(39),
  [87] = {.entry = {.count = 1, .reusable = false}}, SHIFT(139),
  [89] = {.entry = {.count = 1, .reusable = false}}, SHIFT(168),
  [91] = {.entry = {.count = 1, .reusable = false}}, SHIFT(370),
  [93] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(153),
  [96] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(146),
  [99] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(415),
  [102] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(559),
  [105] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(447),
  [108] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(207),
  [111] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0),
  [113] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(38),
  [116] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(162),
  [119] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(382),
  [122] = {.entry = {.count = 1, .reusable = false}}, SHIFT(146),
  [124] = {.entry = {.count = 1, .reusable = false}}, SHIFT(415),
  [126] = {.entry = {.count = 1, .reusable = true}}, SHIFT(447),
  [128] = {.entry = {.count = 1, .reusable = false}}, SHIFT(25),
  [130] = {.entry = {.count = 1, .reusable = false}}, SHIFT(38),
  [132] = {.entry = {.count = 1, .reusable = false}}, SHIFT(162),
  [134] = {.entry = {.count = 1, .reusable = false}}, SHIFT(382),
  [136] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(163),
  [139] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(417),
  [142] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(449),
  [145] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(39),
  [148] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(168),
  [151] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_code_block_repeat1, 2, 0, 0), SHIFT_REPEAT(370),
  [154] = {.entry = {.count = 1, .reusable = false}}, SHIFT(29),
  [156] = {.entry = {.count = 1, .reusable = false}}, SHIFT(238),
  [158] = {.entry = {.count = 1, .reusable = false}}, SHIFT(234),
  [160] = {.entry = {.count = 1, .reusable = false}}, SHIFT(248),
  [162] = {.entry = {.count = 1, .reusable = false}}, SHIFT(255),
  [164] = {.entry = {.count = 1, .reusable = false}}, SHIFT(363),
  [166] = {.entry = {.count = 1, .reusable = false}}, SHIFT(365),
  [168] = {.entry = {.count = 1, .reusable = false}}, SHIFT(445),
  [170] = {.entry = {.count = 1, .reusable = false}}, SHIFT(446),
  [172] = {.entry = {.count = 1, .reusable = false}}, SHIFT(386),
  [174] = {.entry = {.count = 1, .reusable = false}}, SHIFT(388),
  [176] = {.entry = {.count = 1, .reusable = false}}, SHIFT(59),
  [178] = {.entry = {.count = 1, .reusable = false}}, SHIFT(170),
  [180] = {.entry = {.count = 1, .reusable = false}}, SHIFT(60),
  [182] = {.entry = {.count = 1, .reusable = false}}, SHIFT(158),
  [184] = {.entry = {.count = 1, .reusable = false}}, SHIFT(141),
  [186] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0),
  [188] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1051),
  [191] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(408),
  [194] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(926),
  [197] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(927),
  [200] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(931),
  [203] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(939),
  [206] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(944),
  [209] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(673),
  [212] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(962),
  [215] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(963),
  [218] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(976),
  [221] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1004),
  [224] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_table_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(804),
  [227] = {.entry = {.count = 1, .reusable = true}}, SHIFT(638),
  [229] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1051),
  [231] = {.entry = {.count = 1, .reusable = true}}, SHIFT(408),
  [233] = {.entry = {.count = 1, .reusable = true}}, SHIFT(926),
  [235] = {.entry = {.count = 1, .reusable = true}}, SHIFT(927),
  [237] = {.entry = {.count = 1, .reusable = true}}, SHIFT(931),
  [239] = {.entry = {.count = 1, .reusable = true}}, SHIFT(939),
  [241] = {.entry = {.count = 1, .reusable = true}}, SHIFT(944),
  [243] = {.entry = {.count = 1, .reusable = true}}, SHIFT(673),
  [245] = {.entry = {.count = 1, .reusable = true}}, SHIFT(962),
  [247] = {.entry = {.count = 1, .reusable = true}}, SHIFT(963),
  [249] = {.entry = {.count = 1, .reusable = true}}, SHIFT(976),
  [251] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1004),
  [253] = {.entry = {.count = 1, .reusable = true}}, SHIFT(804),
  [255] = {.entry = {.count = 1, .reusable = true}}, SHIFT(702),
  [257] = {.entry = {.count = 1, .reusable = false}}, SHIFT(647),
  [259] = {.entry = {.count = 1, .reusable = false}}, SHIFT(805),
  [261] = {.entry = {.count = 1, .reusable = false}}, SHIFT(725),
  [263] = {.entry = {.count = 1, .reusable = true}}, SHIFT(672),
  [265] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1069),
  [267] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1072),
  [269] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1074),
  [271] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1079),
  [273] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1093),
  [275] = {.entry = {.count = 1, .reusable = true}}, SHIFT(941),
  [277] = {.entry = {.count = 1, .reusable = true}}, SHIFT(968),
  [279] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1028),
  [281] = {.entry = {.count = 1, .reusable = true}}, SHIFT(839),
  [283] = {.entry = {.count = 1, .reusable = true}}, SHIFT(856),
  [285] = {.entry = {.count = 1, .reusable = true}}, SHIFT(858),
  [287] = {.entry = {.count = 1, .reusable = true}}, SHIFT(869),
  [289] = {.entry = {.count = 1, .reusable = true}}, SHIFT(949),
  [291] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1007),
  [293] = {.entry = {.count = 1, .reusable = true}}, SHIFT(699),
  [295] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__quoted_identifier, 3, 0, 0),
  [297] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym__quoted_identifier, 3, 0, 0),
  [299] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_binary_expression, 3, 0, 17),
  [301] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_binary_expression, 3, 0, 17),
  [303] = {.entry = {.count = 1, .reusable = true}}, SHIFT(498),
  [305] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_repeat_statement, 4, 0, 38),
  [307] = {.entry = {.count = 1, .reusable = true}}, SHIFT(620),
  [309] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_repeat_statement, 4, 0, 38),
  [311] = {.entry = {.count = 1, .reusable = true}}, SHIFT(500),
  [313] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1010),
  [315] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_assignment_statement, 3, 0, 25),
  [317] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_assignment_statement, 3, 0, 25),
  [319] = {.entry = {.count = 1, .reusable = true}}, SHIFT(639),
  [321] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1045),
  [323] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_argument_list, 2, 0, 0),
  [325] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_argument_list, 2, 0, 0),
  [327] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_argument_list, 3, 0, 0),
  [329] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_argument_list, 3, 0, 0),
  [331] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0),
  [333] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(593),
  [336] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1094),
  [339] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1095),
  [342] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1097),
  [345] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1098),
  [348] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1099),
  [351] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1101),
  [354] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1102),
  [357] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(939),
  [360] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(944),
  [363] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_field_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1103),
  [366] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_method_call, 4, 0, 27),
  [368] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_method_call, 4, 0, 27),
  [370] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_argument_list, 4, 0, 0),
  [372] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_argument_list, 4, 0, 0),
  [374] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_code_block, 3, 0, 0),
  [376] = {.entry = {.count = 1, .reusable = true}}, SHIFT(67),
  [378] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_code_block, 2, 0, 0),
  [380] = {.entry = {.count = 1, .reusable = true}}, SHIFT(68),
  [382] = {.entry = {.count = 1, .reusable = true}}, SHIFT(709),
  [384] = {.entry = {.count = 1, .reusable = true}}, SHIFT(593),
  [386] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1094),
  [388] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1095),
  [390] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1097),
  [392] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1098),
  [394] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1099),
  [396] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1101),
  [398] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1102),
  [400] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1103),
  [402] = {.entry = {.count = 1, .reusable = true}}, SHIFT(823),
  [404] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_function_call, 2, 0, 9),
  [406] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_function_call, 2, 0, 9),
  [408] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_member_access, 3, 0, 15),
  [410] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_member_access, 3, 0, 15),
  [412] = {.entry = {.count = 1, .reusable = true}}, SHIFT(623),
  [414] = {.entry = {.count = 1, .reusable = true}}, SHIFT(929),
  [416] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_code_block, 4, 0, 0),
  [418] = {.entry = {.count = 1, .reusable = true}}, SHIFT(684),
  [420] = {.entry = {.count = 1, .reusable = true}}, SHIFT(973),
  [422] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__expression, 1, 0, 0),
  [424] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure_call, 1, 0, 6),
  [426] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_procedure_call, 1, 0, 6),
  [428] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_boolean, 1, 0, 0),
  [430] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_boolean, 1, 0, 0),
  [432] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__primary_expression, 3, 0, 0),
  [434] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym__primary_expression, 3, 0, 0),
  [436] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_property_list, 1, 0, 0),
  [438] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_enum_member_access, 3, 0, 16),
  [440] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_enum_member_access, 3, 0, 16),
  [442] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0),
  [444] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(1072),
  [447] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(1074),
  [450] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(1079),
  [453] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(1093),
  [456] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(941),
  [459] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(968),
  [462] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(1028),
  [465] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(839),
  [468] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(856),
  [471] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(858),
  [474] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(869),
  [477] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(949),
  [480] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_property_list_repeat1, 2, 0, 0), SHIFT_REPEAT(1007),
  [483] = {.entry = {.count = 1, .reusable = false}}, SHIFT(763),
  [485] = {.entry = {.count = 1, .reusable = false}}, SHIFT(348),
  [487] = {.entry = {.count = 1, .reusable = true}}, SHIFT(381),
  [489] = {.entry = {.count = 1, .reusable = false}}, SHIFT(379),
  [491] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_data_classification_property, 4, 0, 0),
  [493] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_caption_property, 4, 0, 0),
  [495] = {.entry = {.count = 1, .reusable = false}}, SHIFT(330),
  [497] = {.entry = {.count = 1, .reusable = false}}, SHIFT(270),
  [499] = {.entry = {.count = 1, .reusable = false}}, SHIFT(300),
  [501] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_case_statement_repeat1, 2, 0, 0), SHIFT_REPEAT(153),
  [504] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_case_statement_repeat1, 2, 0, 0),
  [506] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_case_statement_repeat1, 2, 0, 0), SHIFT_REPEAT(348),
  [509] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_case_statement_repeat1, 2, 0, 0), SHIFT_REPEAT(559),
  [512] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_case_statement_repeat1, 2, 0, 0), SHIFT_REPEAT(381),
  [515] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_case_statement_repeat1, 2, 0, 0), SHIFT_REPEAT(207),
  [518] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_property, 4, 0, 5),
  [520] = {.entry = {.count = 1, .reusable = true}}, SHIFT(818),
  [522] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1000),
  [524] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0),
  [526] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1072),
  [529] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1074),
  [532] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1079),
  [535] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1093),
  [538] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(941),
  [541] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(968),
  [544] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1028),
  [547] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(839),
  [550] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(856),
  [553] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(858),
  [556] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(869),
  [559] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(949),
  [562] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1007),
  [565] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1000),
  [568] = {.entry = {.count = 1, .reusable = true}}, SHIFT(796),
  [570] = {.entry = {.count = 1, .reusable = true}}, SHIFT(111),
  [572] = {.entry = {.count = 1, .reusable = true}}, SHIFT(391),
  [574] = {.entry = {.count = 1, .reusable = false}}, SHIFT(900),
  [576] = {.entry = {.count = 1, .reusable = false}}, SHIFT(765),
  [578] = {.entry = {.count = 1, .reusable = false}}, SHIFT(766),
  [580] = {.entry = {.count = 1, .reusable = false}}, SHIFT(903),
  [582] = {.entry = {.count = 1, .reusable = false}}, SHIFT(767),
  [584] = {.entry = {.count = 1, .reusable = false}}, SHIFT(905),
  [586] = {.entry = {.count = 1, .reusable = true}}, SHIFT(52),
  [588] = {.entry = {.count = 1, .reusable = true}}, SHIFT(324),
  [590] = {.entry = {.count = 1, .reusable = true}}, SHIFT(450),
  [592] = {.entry = {.count = 1, .reusable = true}}, SHIFT(390),
  [594] = {.entry = {.count = 1, .reusable = true}}, SHIFT(93),
  [596] = {.entry = {.count = 1, .reusable = true}}, SHIFT(393),
  [598] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_var_section, 2, 0, 0),
  [600] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_var_section, 2, 0, 0),
  [602] = {.entry = {.count = 1, .reusable = false}}, SHIFT(943),
  [604] = {.entry = {.count = 1, .reusable = true}}, SHIFT(82),
  [606] = {.entry = {.count = 1, .reusable = true}}, SHIFT(392),
  [608] = {.entry = {.count = 1, .reusable = true}}, SHIFT(349),
  [610] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_var_section_repeat1, 2, 0, 0),
  [612] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_var_section_repeat1, 2, 0, 0),
  [614] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_var_section_repeat1, 2, 0, 0), SHIFT_REPEAT(943),
  [617] = {.entry = {.count = 1, .reusable = true}}, SHIFT(429),
  [619] = {.entry = {.count = 1, .reusable = false}}, SHIFT(404),
  [621] = {.entry = {.count = 1, .reusable = true}}, SHIFT(407),
  [623] = {.entry = {.count = 1, .reusable = true}}, SHIFT(149),
  [625] = {.entry = {.count = 1, .reusable = false}}, SHIFT(69),
  [627] = {.entry = {.count = 1, .reusable = true}}, SHIFT(587),
  [629] = {.entry = {.count = 1, .reusable = true}}, SHIFT(69),
  [631] = {.entry = {.count = 1, .reusable = false}}, SHIFT(117),
  [633] = {.entry = {.count = 1, .reusable = true}}, SHIFT(137),
  [635] = {.entry = {.count = 1, .reusable = false}}, SHIFT(54),
  [637] = {.entry = {.count = 1, .reusable = true}}, SHIFT(532),
  [639] = {.entry = {.count = 1, .reusable = true}}, SHIFT(54),
  [641] = {.entry = {.count = 1, .reusable = false}}, SHIFT(90),
  [643] = {.entry = {.count = 1, .reusable = false}}, SHIFT(51),
  [645] = {.entry = {.count = 1, .reusable = true}}, SHIFT(51),
  [647] = {.entry = {.count = 1, .reusable = true}}, SHIFT(320),
  [649] = {.entry = {.count = 1, .reusable = true}}, SHIFT(399),
  [651] = {.entry = {.count = 1, .reusable = true}}, SHIFT(345),
  [653] = {.entry = {.count = 1, .reusable = true}}, SHIFT(155),
  [655] = {.entry = {.count = 1, .reusable = false}}, SHIFT(71),
  [657] = {.entry = {.count = 1, .reusable = true}}, SHIFT(591),
  [659] = {.entry = {.count = 1, .reusable = true}}, SHIFT(71),
  [661] = {.entry = {.count = 1, .reusable = false}}, SHIFT(113),
  [663] = {.entry = {.count = 1, .reusable = true}}, SHIFT(436),
  [665] = {.entry = {.count = 1, .reusable = true}}, SHIFT(416),
  [667] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_clustered_property, 4, 0, 73),
  [669] = {.entry = {.count = 1, .reusable = true}}, SHIFT(418),
  [671] = {.entry = {.count = 1, .reusable = true}}, SHIFT(159),
  [673] = {.entry = {.count = 1, .reusable = false}}, SHIFT(50),
  [675] = {.entry = {.count = 1, .reusable = true}}, SHIFT(594),
  [677] = {.entry = {.count = 1, .reusable = true}}, SHIFT(50),
  [679] = {.entry = {.count = 1, .reusable = false}}, SHIFT(79),
  [681] = {.entry = {.count = 1, .reusable = true}}, SHIFT(419),
  [683] = {.entry = {.count = 1, .reusable = false}}, SHIFT(73),
  [685] = {.entry = {.count = 1, .reusable = true}}, SHIFT(73),
  [687] = {.entry = {.count = 1, .reusable = true}}, SHIFT(420),
  [689] = {.entry = {.count = 1, .reusable = true}}, SHIFT(413),
  [691] = {.entry = {.count = 1, .reusable = true}}, SHIFT(422),
  [693] = {.entry = {.count = 1, .reusable = false}}, SHIFT(70),
  [695] = {.entry = {.count = 1, .reusable = true}}, SHIFT(70),
  [697] = {.entry = {.count = 1, .reusable = true}}, SHIFT(424),
  [699] = {.entry = {.count = 1, .reusable = false}}, SHIFT(49),
  [701] = {.entry = {.count = 1, .reusable = true}}, SHIFT(49),
  [703] = {.entry = {.count = 1, .reusable = true}}, SHIFT(426),
  [705] = {.entry = {.count = 1, .reusable = false}}, SHIFT(53),
  [707] = {.entry = {.count = 1, .reusable = true}}, SHIFT(53),
  [709] = {.entry = {.count = 1, .reusable = true}}, SHIFT(428),
  [711] = {.entry = {.count = 1, .reusable = true}}, SHIFT(439),
  [713] = {.entry = {.count = 1, .reusable = true}}, SHIFT(432),
  [715] = {.entry = {.count = 1, .reusable = false}}, SHIFT(48),
  [717] = {.entry = {.count = 1, .reusable = true}}, SHIFT(48),
  [719] = {.entry = {.count = 1, .reusable = true}}, SHIFT(434),
  [721] = {.entry = {.count = 1, .reusable = false}}, SHIFT(66),
  [723] = {.entry = {.count = 1, .reusable = true}}, SHIFT(66),
  [725] = {.entry = {.count = 1, .reusable = true}}, SHIFT(440),
  [727] = {.entry = {.count = 1, .reusable = true}}, SHIFT(412),
  [729] = {.entry = {.count = 1, .reusable = true}}, SHIFT(441),
  [731] = {.entry = {.count = 1, .reusable = false}}, SHIFT(72),
  [733] = {.entry = {.count = 1, .reusable = true}}, SHIFT(72),
  [735] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_variable_declaration, 4, 0, 8),
  [737] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_variable_declaration, 4, 0, 8),
  [739] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_variable_declaration, 5, 0, 14),
  [741] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_variable_declaration, 5, 0, 14),
  [743] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_permissions_property, 4, 0, 0),
  [745] = {.entry = {.count = 1, .reusable = true}}, SHIFT(130),
  [747] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 6, 0, 18),
  [749] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 6, 0, 12),
  [751] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 6, 0, 20),
  [753] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 6, 0, 22),
  [755] = {.entry = {.count = 1, .reusable = true}}, SHIFT(612),
  [757] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_codeunit_declaration_repeat1, 2, 0, 0),
  [759] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_codeunit_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1069),
  [762] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_codeunit_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(699),
  [765] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_codeunit_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(962),
  [768] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_codeunit_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(1004),
  [771] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_codeunit_declaration_repeat1, 2, 0, 0), SHIFT_REPEAT(804),
  [774] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 7, 0, 18),
  [776] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 7, 0, 28),
  [778] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 7, 0, 12),
  [780] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 7, 0, 29),
  [782] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 7, 0, 20),
  [784] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 7, 0, 32),
  [786] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 7, 0, 22),
  [788] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 7, 0, 33),
  [790] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_if_statement, 4, 0, 36),
  [792] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_if_statement, 4, 0, 36),
  [794] = {.entry = {.count = 1, .reusable = false}}, SHIFT(15),
  [796] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_fields, 3, 0, 0),
  [798] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_keys, 3, 0, 0),
  [800] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 18),
  [802] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 40),
  [804] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 28),
  [806] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 29),
  [808] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 12),
  [810] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 41),
  [812] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 32),
  [814] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 42),
  [816] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 22),
  [818] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 43),
  [820] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 8, 0, 33),
  [822] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 40),
  [824] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 18),
  [826] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 50),
  [828] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 41),
  [830] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 32),
  [832] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 51),
  [834] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 42),
  [836] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 43),
  [838] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 22),
  [840] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 9, 0, 52),
  [842] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 10, 0, 50),
  [844] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 10, 0, 51),
  [846] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 10, 0, 32),
  [848] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 10, 0, 60),
  [850] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 10, 0, 52),
  [852] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 11, 0, 60),
  [854] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_type_property, 4, 0, 0),
  [856] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_oninsert_trigger, 4, 0, 0),
  [858] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onmodify_trigger, 4, 0, 0),
  [860] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_ondelete_trigger, 4, 0, 0),
  [862] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onrename_trigger, 4, 0, 0),
  [864] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onvalidate_trigger, 4, 0, 0),
  [866] = {.entry = {.count = 1, .reusable = true}}, SHIFT(237),
  [868] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_code_block, 2, 0, 0),
  [870] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onaftergetrecord_trigger, 4, 0, 0),
  [872] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onafterinsertevent_trigger, 4, 0, 0),
  [874] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_code_block, 3, 0, 0),
  [876] = {.entry = {.count = 1, .reusable = true}}, SHIFT(244),
  [878] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onaftermodifyevent_trigger, 4, 0, 0),
  [880] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onafterdeleteevent_trigger, 4, 0, 0),
  [882] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onbeforeinsertevent_trigger, 4, 0, 0),
  [884] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onbeforemodifyevent_trigger, 4, 0, 0),
  [886] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onbeforedeleteevent_trigger, 4, 0, 0),
  [888] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_code_block, 4, 0, 0),
  [890] = {.entry = {.count = 1, .reusable = false}}, SHIFT(18),
  [892] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_drilldown_pageid_property, 4, 0, 0),
  [894] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_lookup_pageid_property, 4, 0, 0),
  [896] = {.entry = {.count = 1, .reusable = true}}, SHIFT(317),
  [898] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_exit_statement, 1, 0, 0),
  [900] = {.entry = {.count = 1, .reusable = true}}, SHIFT(157),
  [902] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_exit_statement, 1, 0, 0),
  [904] = {.entry = {.count = 1, .reusable = true}}, SHIFT(254),
  [906] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__statement, 1, 0, 0),
  [908] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym__statement, 1, 0, 0),
  [910] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_get_statement, 1, 0, 0),
  [912] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_get_statement, 1, 0, 0),
  [914] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_find_set_statement, 1, 0, 0),
  [916] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_find_set_statement, 1, 0, 0),
  [918] = {.entry = {.count = 1, .reusable = true}}, SHIFT(881),
  [920] = {.entry = {.count = 1, .reusable = true}}, SHIFT(888),
  [922] = {.entry = {.count = 1, .reusable = true}}, SHIFT(889),
  [924] = {.entry = {.count = 1, .reusable = true}}, SHIFT(890),
  [926] = {.entry = {.count = 1, .reusable = true}}, SHIFT(892),
  [928] = {.entry = {.count = 1, .reusable = true}}, SHIFT(895),
  [930] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__statement, 2, 0, 0),
  [932] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym__statement, 2, 0, 0),
  [934] = {.entry = {.count = 1, .reusable = true}}, SHIFT(257),
  [936] = {.entry = {.count = 1, .reusable = true}}, SHIFT(619),
  [938] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_fields, 4, 0, 0),
  [940] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_get_method, 4, 0, 37),
  [942] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_get_method, 4, 0, 37),
  [944] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_exit_statement, 4, 0, 0),
  [946] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_exit_statement, 4, 0, 0),
  [948] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_keys, 4, 0, 0),
  [950] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_find_set_method, 5, 0, 45),
  [952] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_find_set_method, 5, 0, 45),
  [954] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_insert_statement, 5, 0, 46),
  [956] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_insert_statement, 5, 0, 46),
  [958] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_modify_statement, 5, 0, 46),
  [960] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_modify_statement, 5, 0, 46),
  [962] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_delete_statement, 5, 0, 46),
  [964] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_delete_statement, 5, 0, 46),
  [966] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_reset_statement, 5, 0, 46),
  [968] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_reset_statement, 5, 0, 46),
  [970] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_find_first_statement, 5, 0, 46),
  [972] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_find_first_statement, 5, 0, 46),
  [974] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_find_last_statement, 5, 0, 46),
  [976] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_find_last_statement, 5, 0, 46),
  [978] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_next_statement, 5, 0, 46),
  [980] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_next_statement, 5, 0, 46),
  [982] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_case_statement, 5, 0, 47),
  [984] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_case_statement, 5, 0, 47),
  [986] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_if_statement, 6, 0, 53),
  [988] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_if_statement, 6, 0, 53),
  [990] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_find_set_method, 6, 0, 54),
  [992] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_find_set_method, 6, 0, 54),
  [994] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_insert_statement, 6, 0, 55),
  [996] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_insert_statement, 6, 0, 55),
  [998] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_modify_statement, 6, 0, 55),
  [1000] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_modify_statement, 6, 0, 55),
  [1002] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_delete_statement, 6, 0, 55),
  [1004] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_delete_statement, 6, 0, 55),
  [1006] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_next_statement, 6, 0, 56),
  [1008] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_next_statement, 6, 0, 56),
  [1010] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_case_statement, 6, 0, 47),
  [1012] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_case_statement, 6, 0, 47),
  [1014] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_find_set_method, 8, 0, 65),
  [1016] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_find_set_method, 8, 0, 65),
  [1018] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_insert_statement, 8, 0, 66),
  [1020] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_insert_statement, 8, 0, 66),
  [1022] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_set_range_statement, 8, 0, 67),
  [1024] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_set_range_statement, 8, 0, 67),
  [1026] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_set_filter_statement, 8, 0, 68),
  [1028] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_set_filter_statement, 8, 0, 68),
  [1030] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_set_filter_statement, 9, 0, 71),
  [1032] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_set_filter_statement, 9, 0, 71),
  [1034] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_set_range_statement, 10, 0, 78),
  [1036] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_set_range_statement, 10, 0, 78),
  [1038] = {.entry = {.count = 1, .reusable = true}}, SHIFT(161),
  [1040] = {.entry = {.count = 1, .reusable = true}}, SHIFT(288),
  [1042] = {.entry = {.count = 1, .reusable = false}}, SHIFT(19),
  [1044] = {.entry = {.count = 1, .reusable = false}}, SHIFT(11),
  [1046] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_procedure, 5, 0, 12),
  [1048] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_expression_list_repeat1, 2, 0, 0),
  [1050] = {.entry = {.count = 1, .reusable = true}}, SHIFT(691),
  [1052] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym_expression_list_repeat1, 2, 0, 0),
  [1054] = {.entry = {.count = 1, .reusable = true}}, SHIFT(836),
  [1056] = {.entry = {.count = 1, .reusable = true}}, SHIFT(142),
  [1058] = {.entry = {.count = 1, .reusable = true}}, SHIFT(55),
  [1060] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__primary_expression, 1, 0, 0),
  [1062] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym__primary_expression, 1, 0, 0),
  [1064] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_list, 1, 0, 0),
  [1066] = {.entry = {.count = 1, .reusable = true}}, SHIFT(364),
  [1068] = {.entry = {.count = 1, .reusable = true}}, SHIFT(366),
  [1070] = {.entry = {.count = 1, .reusable = true}}, SHIFT(151),
  [1072] = {.entry = {.count = 1, .reusable = true}}, SHIFT(377),
  [1074] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_value_set, 1, 0, 0),
  [1076] = {.entry = {.count = 1, .reusable = true}}, SHIFT(147),
  [1078] = {.entry = {.count = 1, .reusable = true}}, SHIFT(394),
  [1080] = {.entry = {.count = 1, .reusable = true}}, SHIFT(387),
  [1082] = {.entry = {.count = 1, .reusable = true}}, SHIFT(389),
  [1084] = {.entry = {.count = 1, .reusable = true}}, SHIFT(444),
  [1086] = {.entry = {.count = 1, .reusable = true}}, SHIFT(120),
  [1088] = {.entry = {.count = 1, .reusable = true}}, SHIFT(103),
  [1090] = {.entry = {.count = 1, .reusable = true}}, SHIFT(97),
  [1092] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_option_members_property, 5, 0, 0),
  [1094] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_decimal_places_property, 6, 0, 83),
  [1096] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_set_filter_statement_repeat1, 2, 0, 70),
  [1098] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_field_trigger_declaration, 4, 0, 82),
  [1100] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_relation_property, 4, 0, 0),
  [1102] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_field_class_property, 4, 0, 0),
  [1104] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_calc_formula_property, 4, 0, 0),
  [1106] = {.entry = {.count = 1, .reusable = true}}, SHIFT(131),
  [1108] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_blank_zero_property, 4, 0, 0),
  [1110] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1142),
  [1112] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1149),
  [1114] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1014),
  [1116] = {.entry = {.count = 1, .reusable = true}}, SHIFT(833),
  [1118] = {.entry = {.count = 1, .reusable = true}}, SHIFT(855),
  [1120] = {.entry = {.count = 1, .reusable = true}}, SHIFT(863),
  [1122] = {.entry = {.count = 1, .reusable = true}}, SHIFT(868),
  [1124] = {.entry = {.count = 1, .reusable = true}}, SHIFT(913),
  [1126] = {.entry = {.count = 1, .reusable = true}}, SHIFT(916),
  [1128] = {.entry = {.count = 1, .reusable = true}}, SHIFT(917),
  [1130] = {.entry = {.count = 1, .reusable = true}}, SHIFT(919),
  [1132] = {.entry = {.count = 1, .reusable = true}}, SHIFT(920),
  [1134] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_editable_property, 4, 0, 0),
  [1136] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_option_members_property, 4, 0, 0),
  [1138] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_option_caption_property, 4, 0, 0),
  [1140] = {.entry = {.count = 1, .reusable = true}}, SHIFT(648),
  [1142] = {.entry = {.count = 1, .reusable = true}}, SHIFT(125),
  [1144] = {.entry = {.count = 1, .reusable = true}}, SHIFT(121),
  [1146] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__table_reference, 1, 0, 0),
  [1148] = {.entry = {.count = 1, .reusable = true}}, SHIFT(437),
  [1150] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__assignable_expression, 1, 0, 0),
  [1152] = {.entry = {.count = 1, .reusable = true}}, SHIFT(395),
  [1154] = {.entry = {.count = 1, .reusable = true}}, SHIFT(433),
  [1156] = {.entry = {.count = 1, .reusable = true}}, SHIFT(128),
  [1158] = {.entry = {.count = 1, .reusable = true}}, SHIFT(119),
  [1160] = {.entry = {.count = 1, .reusable = true}}, SHIFT(321),
  [1162] = {.entry = {.count = 1, .reusable = true}}, SHIFT(318),
  [1164] = {.entry = {.count = 1, .reusable = true}}, SHIFT(435),
  [1166] = {.entry = {.count = 1, .reusable = true}}, SHIFT(134),
  [1168] = {.entry = {.count = 1, .reusable = true}}, SHIFT(110),
  [1170] = {.entry = {.count = 1, .reusable = true}}, SHIFT(260),
  [1172] = {.entry = {.count = 1, .reusable = true}}, SHIFT(438),
  [1174] = {.entry = {.count = 1, .reusable = true}}, SHIFT(132),
  [1176] = {.entry = {.count = 1, .reusable = true}}, SHIFT(81),
  [1178] = {.entry = {.count = 1, .reusable = true}}, SHIFT(291),
  [1180] = {.entry = {.count = 1, .reusable = true}}, SHIFT(92),
  [1182] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__field_reference, 1, 0, 0),
  [1184] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym__field_reference, 1, 0, 0),
  [1186] = {.entry = {.count = 1, .reusable = true}}, SHIFT(16),
  [1188] = {.entry = {.count = 1, .reusable = true}}, SHIFT(778),
  [1190] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1061),
  [1192] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1062),
  [1194] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1063),
  [1196] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1064),
  [1198] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1152),
  [1200] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1153),
  [1202] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1065),
  [1204] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1066),
  [1206] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1067),
  [1208] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1068),
  [1210] = {.entry = {.count = 1, .reusable = true}}, SHIFT(24),
  [1212] = {.entry = {.count = 1, .reusable = true}}, SHIFT(793),
  [1214] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1084),
  [1216] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1085),
  [1218] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1086),
  [1220] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1087),
  [1222] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1154),
  [1224] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1155),
  [1226] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1088),
  [1228] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1089),
  [1230] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1090),
  [1232] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1091),
  [1234] = {.entry = {.count = 1, .reusable = true}}, SHIFT(12),
  [1236] = {.entry = {.count = 1, .reusable = true}}, SHIFT(773),
  [1238] = {.entry = {.count = 1, .reusable = true}}, SHIFT(897),
  [1240] = {.entry = {.count = 1, .reusable = true}}, SHIFT(912),
  [1242] = {.entry = {.count = 1, .reusable = true}}, SHIFT(915),
  [1244] = {.entry = {.count = 1, .reusable = true}}, SHIFT(918),
  [1246] = {.entry = {.count = 1, .reusable = true}}, SHIFT(921),
  [1248] = {.entry = {.count = 1, .reusable = true}}, SHIFT(922),
  [1250] = {.entry = {.count = 1, .reusable = true}}, SHIFT(923),
  [1252] = {.entry = {.count = 1, .reusable = true}}, SHIFT(924),
  [1254] = {.entry = {.count = 1, .reusable = true}}, SHIFT(930),
  [1256] = {.entry = {.count = 1, .reusable = true}}, SHIFT(936),
  [1258] = {.entry = {.count = 1, .reusable = true}}, SHIFT(806),
  [1260] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1105),
  [1262] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1106),
  [1264] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1107),
  [1266] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1108),
  [1268] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1156),
  [1270] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1157),
  [1272] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1109),
  [1274] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1110),
  [1276] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1111),
  [1278] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1112),
  [1280] = {.entry = {.count = 1, .reusable = true}}, SHIFT(122),
  [1282] = {.entry = {.count = 1, .reusable = true}}, SHIFT(33),
  [1284] = {.entry = {.count = 1, .reusable = true}}, SHIFT(127),
  [1286] = {.entry = {.count = 1, .reusable = true}}, SHIFT(674),
  [1288] = {.entry = {.count = 1, .reusable = true}}, SHIFT(453),
  [1290] = {.entry = {.count = 1, .reusable = true}}, SHIFT(457),
  [1292] = {.entry = {.count = 1, .reusable = true}}, SHIFT(662),
  [1294] = {.entry = {.count = 1, .reusable = true}}, SHIFT(685),
  [1296] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_case_clause, 3, 0, 57),
  [1298] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_case_clause, 3, 0, 57),
  [1300] = {.entry = {.count = 1, .reusable = true}}, SHIFT(484),
  [1302] = {.entry = {.count = 1, .reusable = true}}, SHIFT(2),
  [1304] = {.entry = {.count = 1, .reusable = false}}, SHIFT(708),
  [1306] = {.entry = {.count = 1, .reusable = false}}, SHIFT(850),
  [1308] = {.entry = {.count = 1, .reusable = false}}, SHIFT(34),
  [1310] = {.entry = {.count = 1, .reusable = true}}, SHIFT(478),
  [1312] = {.entry = {.count = 1, .reusable = false}}, SHIFT(862),
  [1314] = {.entry = {.count = 1, .reusable = false}}, SHIFT(414),
  [1316] = {.entry = {.count = 1, .reusable = true}}, SHIFT(414),
  [1318] = {.entry = {.count = 1, .reusable = true}}, SHIFT(475),
  [1320] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1122),
  [1322] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_var_section_repeat1, 2, 0, 0), SHIFT_REPEAT(1122),
  [1325] = {.entry = {.count = 1, .reusable = true}}, SHIFT(471),
  [1327] = {.entry = {.count = 1, .reusable = true}}, SHIFT(482),
  [1329] = {.entry = {.count = 1, .reusable = true}}, SHIFT(479),
  [1331] = {.entry = {.count = 1, .reusable = true}}, SHIFT(476),
  [1333] = {.entry = {.count = 1, .reusable = true}}, SHIFT(483),
  [1335] = {.entry = {.count = 1, .reusable = true}}, SHIFT(990),
  [1337] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_record_type, 2, 0, 7),
  [1339] = {.entry = {.count = 1, .reusable = true}}, SHIFT(501),
  [1341] = {.entry = {.count = 1, .reusable = true}}, SHIFT(586),
  [1343] = {.entry = {.count = 1, .reusable = false}}, SHIFT(586),
  [1345] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_text_type, 1, 0, 0),
  [1347] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1027),
  [1349] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_text_type, 4, 0, 26),
  [1351] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_type_specification, 1, 0, 0),
  [1353] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_array_type, 6, 0, 48),
  [1355] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_source_file_repeat1, 2, 0, 0),
  [1357] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_source_file_repeat1, 2, 0, 0), SHIFT_REPEAT(821),
  [1360] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_source_file_repeat1, 2, 0, 0), SHIFT_REPEAT(787),
  [1363] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_source_file, 1, 0, 0),
  [1365] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_list_type, 5, 0, 0),
  [1367] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_dictionary_type, 7, 0, 0),
  [1369] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_codeunit_type, 2, 0, 7),
  [1371] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_query_type_value, 1, 0, 0),
  [1373] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_query_type, 2, 0, 7),
  [1375] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_dotnet_type, 2, 0, 7),
  [1377] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_comparison_operator, 1, 0, 0),
  [1379] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_comparison_operator, 1, 0, 0),
  [1381] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_basic_type, 1, 0, 0),
  [1383] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_arithmetic_operator, 1, 0, 0),
  [1385] = {.entry = {.count = 1, .reusable = false}}, REDUCE(sym_arithmetic_operator, 1, 0, 0),
  [1387] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_record_type, 3, 0, 7),
  [1389] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1009),
  [1391] = {.entry = {.count = 1, .reusable = true}}, SHIFT(464),
  [1393] = {.entry = {.count = 1, .reusable = false}}, SHIFT(832),
  [1395] = {.entry = {.count = 1, .reusable = true}}, SHIFT(431),
  [1397] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_onrun_trigger, 4, 0, 0),
  [1399] = {.entry = {.count = 1, .reusable = true}}, SHIFT(758),
  [1401] = {.entry = {.count = 1, .reusable = true}}, SHIFT(769),
  [1403] = {.entry = {.count = 1, .reusable = true}}, SHIFT(911),
  [1405] = {.entry = {.count = 1, .reusable = true}}, SHIFT(467),
  [1407] = {.entry = {.count = 1, .reusable = true}}, SHIFT(456),
  [1409] = {.entry = {.count = 1, .reusable = true}}, SHIFT(458),
  [1411] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1016),
  [1413] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1017),
  [1415] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1015),
  [1417] = {.entry = {.count = 1, .reusable = true}}, SHIFT(878),
  [1419] = {.entry = {.count = 1, .reusable = false}}, SHIFT(47),
  [1421] = {.entry = {.count = 1, .reusable = true}}, SHIFT(518),
  [1423] = {.entry = {.count = 1, .reusable = false}}, SHIFT(518),
  [1425] = {.entry = {.count = 1, .reusable = false}}, SHIFT(116),
  [1427] = {.entry = {.count = 1, .reusable = false}}, REDUCE(aux_sym__quoted_identifier_repeat1, 2, 0, 0),
  [1429] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym__quoted_identifier_repeat1, 2, 0, 0), SHIFT_REPEAT(518),
  [1432] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym__quoted_identifier_repeat1, 2, 0, 0), SHIFT_REPEAT(518),
  [1435] = {.entry = {.count = 1, .reusable = true}}, SHIFT(714),
  [1437] = {.entry = {.count = 1, .reusable = false}}, SHIFT(89),
  [1439] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_attribute_list_repeat1, 2, 0, 0), SHIFT_REPEAT(962),
  [1442] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_attribute_list_repeat1, 2, 0, 0),
  [1444] = {.entry = {.count = 1, .reusable = true}}, SHIFT(495),
  [1446] = {.entry = {.count = 1, .reusable = false}}, SHIFT(108),
  [1448] = {.entry = {.count = 1, .reusable = false}}, SHIFT(78),
  [1450] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_attribute_list, 1, 0, 0),
  [1452] = {.entry = {.count = 1, .reusable = true}}, SHIFT(859),
  [1454] = {.entry = {.count = 1, .reusable = true}}, SHIFT(894),
  [1456] = {.entry = {.count = 1, .reusable = true}}, SHIFT(524),
  [1458] = {.entry = {.count = 1, .reusable = false}}, SHIFT(524),
  [1460] = {.entry = {.count = 1, .reusable = true}}, SHIFT(708),
  [1462] = {.entry = {.count = 1, .reusable = true}}, SHIFT(34),
  [1464] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__simple_table_relation, 1, 0, 0),
  [1466] = {.entry = {.count = 1, .reusable = true}}, SHIFT(534),
  [1468] = {.entry = {.count = 1, .reusable = true}}, SHIFT(887),
  [1470] = {.entry = {.count = 1, .reusable = true}}, SHIFT(361),
  [1472] = {.entry = {.count = 1, .reusable = true}}, SHIFT(207),
  [1474] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_expression_list_repeat1, 2, 0, 0), SHIFT_REPEAT(142),
  [1477] = {.entry = {.count = 1, .reusable = true}}, SHIFT(367),
  [1479] = {.entry = {.count = 1, .reusable = true}}, SHIFT(368),
  [1481] = {.entry = {.count = 1, .reusable = true}}, SHIFT(369),
  [1483] = {.entry = {.count = 1, .reusable = true}}, SHIFT(883),
  [1485] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1059),
  [1487] = {.entry = {.count = 1, .reusable = true}}, SHIFT(965),
  [1489] = {.entry = {.count = 1, .reusable = true}}, SHIFT(322),
  [1491] = {.entry = {.count = 1, .reusable = true}}, SHIFT(323),
  [1493] = {.entry = {.count = 1, .reusable = true}}, SHIFT(396),
  [1495] = {.entry = {.count = 1, .reusable = true}}, SHIFT(325),
  [1497] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1130),
  [1499] = {.entry = {.count = 2, .reusable = false}}, REDUCE(aux_sym_var_section_repeat1, 2, 0, 0), SHIFT_REPEAT(1130),
  [1502] = {.entry = {.count = 1, .reusable = true}}, SHIFT(191),
  [1504] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1092),
  [1506] = {.entry = {.count = 1, .reusable = true}}, SHIFT(192),
  [1508] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1150),
  [1510] = {.entry = {.count = 1, .reusable = true}}, SHIFT(516),
  [1512] = {.entry = {.count = 1, .reusable = false}}, SHIFT(516),
  [1514] = {.entry = {.count = 1, .reusable = true}}, SHIFT(262),
  [1516] = {.entry = {.count = 1, .reusable = true}}, SHIFT(263),
  [1518] = {.entry = {.count = 1, .reusable = true}}, SHIFT(264),
  [1520] = {.entry = {.count = 1, .reusable = true}}, SHIFT(265),
  [1522] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1015),
  [1524] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1115),
  [1526] = {.entry = {.count = 1, .reusable = false}}, SHIFT(1114),
  [1528] = {.entry = {.count = 1, .reusable = true}}, SHIFT(292),
  [1530] = {.entry = {.count = 1, .reusable = true}}, SHIFT(293),
  [1532] = {.entry = {.count = 1, .reusable = true}}, SHIFT(294),
  [1534] = {.entry = {.count = 1, .reusable = true}}, SHIFT(295),
  [1536] = {.entry = {.count = 1, .reusable = true}}, SHIFT(494),
  [1538] = {.entry = {.count = 1, .reusable = true}}, SHIFT(258),
  [1540] = {.entry = {.count = 1, .reusable = true}}, SHIFT(950),
  [1542] = {.entry = {.count = 1, .reusable = true}}, SHIFT(951),
  [1544] = {.entry = {.count = 1, .reusable = true}}, SHIFT(958),
  [1546] = {.entry = {.count = 1, .reusable = true}}, SHIFT(960),
  [1548] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_filter_operator, 1, 0, 0),
  [1550] = {.entry = {.count = 1, .reusable = true}}, SHIFT(517),
  [1552] = {.entry = {.count = 1, .reusable = false}}, SHIFT(517),
  [1554] = {.entry = {.count = 1, .reusable = true}}, SHIFT(971),
  [1556] = {.entry = {.count = 1, .reusable = true}}, SHIFT(527),
  [1558] = {.entry = {.count = 1, .reusable = false}}, SHIFT(527),
  [1560] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_fields_repeat1, 2, 0, 0),
  [1562] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_fields_repeat1, 2, 0, 0), SHIFT_REPEAT(1092),
  [1565] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1131),
  [1567] = {.entry = {.count = 1, .reusable = true}}, SHIFT(528),
  [1569] = {.entry = {.count = 1, .reusable = false}}, SHIFT(528),
  [1571] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_keys_repeat1, 2, 0, 0),
  [1573] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_keys_repeat1, 2, 0, 0), SHIFT_REPEAT(1150),
  [1576] = {.entry = {.count = 1, .reusable = true}}, SHIFT(548),
  [1578] = {.entry = {.count = 1, .reusable = true}}, SHIFT(854),
  [1580] = {.entry = {.count = 1, .reusable = true}}, SHIFT(879),
  [1582] = {.entry = {.count = 1, .reusable = true}}, SHIFT(978),
  [1584] = {.entry = {.count = 1, .reusable = true}}, SHIFT(261),
  [1586] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_codeunit_declaration, 7, 0, 2),
  [1588] = {.entry = {.count = 1, .reusable = true}}, SHIFT(143),
  [1590] = {.entry = {.count = 1, .reusable = true}}, SHIFT(282),
  [1592] = {.entry = {.count = 1, .reusable = true}}, SHIFT(582),
  [1594] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_option_members_value, 2, 0, 0),
  [1596] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_expression_list, 2, 0, 0),
  [1598] = {.entry = {.count = 1, .reusable = true}}, SHIFT(58),
  [1600] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1114),
  [1602] = {.entry = {.count = 1, .reusable = true}}, SHIFT(584),
  [1604] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_parameter_list, 1, 0, 0),
  [1606] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_codeunit_declaration, 6, 0, 2),
  [1608] = {.entry = {.count = 1, .reusable = true}}, SHIFT(65),
  [1610] = {.entry = {.count = 1, .reusable = true}}, SHIFT(865),
  [1612] = {.entry = {.count = 1, .reusable = true}}, SHIFT(866),
  [1614] = {.entry = {.count = 1, .reusable = true}}, SHIFT(512),
  [1616] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_lookup_where_conditions, 2, 0, 0),
  [1618] = {.entry = {.count = 1, .reusable = true}}, SHIFT(75),
  [1620] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_filter_conditions_repeat1, 2, 0, 0), SHIFT_REPEAT(522),
  [1623] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_filter_conditions_repeat1, 2, 0, 0),
  [1625] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_lookup_where_conditions, 1, 0, 0),
  [1627] = {.entry = {.count = 1, .reusable = true}}, SHIFT(87),
  [1629] = {.entry = {.count = 1, .reusable = true}}, SHIFT(513),
  [1631] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_where_conditions, 2, 0, 0),
  [1633] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_lookup_where_conditions_repeat1, 2, 0, 0), SHIFT_REPEAT(512),
  [1636] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_lookup_where_conditions_repeat1, 2, 0, 0),
  [1638] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_where_conditions_repeat1, 2, 0, 0), SHIFT_REPEAT(513),
  [1641] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_where_conditions_repeat1, 2, 0, 0),
  [1643] = {.entry = {.count = 1, .reusable = true}}, SHIFT(397),
  [1645] = {.entry = {.count = 1, .reusable = true}}, SHIFT(885),
  [1647] = {.entry = {.count = 1, .reusable = true}}, SHIFT(311),
  [1649] = {.entry = {.count = 1, .reusable = true}}, SHIFT(312),
  [1651] = {.entry = {.count = 1, .reusable = true}}, SHIFT(358),
  [1653] = {.entry = {.count = 1, .reusable = true}}, SHIFT(451),
  [1655] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_declaration, 5, 0, 2),
  [1657] = {.entry = {.count = 1, .reusable = true}}, SHIFT(64),
  [1659] = {.entry = {.count = 1, .reusable = true}}, SHIFT(886),
  [1661] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1121),
  [1663] = {.entry = {.count = 1, .reusable = true}}, SHIFT(99),
  [1665] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_parameter_list, 2, 0, 0),
  [1667] = {.entry = {.count = 1, .reusable = true}}, SHIFT(522),
  [1669] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_filter_conditions, 2, 0, 0),
  [1671] = {.entry = {.count = 1, .reusable = true}}, SHIFT(341),
  [1673] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_code_type, 1, 0, 0),
  [1675] = {.entry = {.count = 1, .reusable = true}}, SHIFT(902),
  [1677] = {.entry = {.count = 1, .reusable = true}}, SHIFT(406),
  [1679] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_attribute, 4, 0, 4),
  [1681] = {.entry = {.count = 1, .reusable = true}}, SHIFT(342),
  [1683] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__simple_table_relation, 3, 0, 0),
  [1685] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1075),
  [1687] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_attribute, 3, 0, 4),
  [1689] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1124),
  [1691] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1125),
  [1693] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1133),
  [1695] = {.entry = {.count = 1, .reusable = true}}, SHIFT(786),
  [1697] = {.entry = {.count = 1, .reusable = true}}, SHIFT(961),
  [1699] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_value_set, 2, 0, 0),
  [1701] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1137),
  [1703] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1139),
  [1705] = {.entry = {.count = 1, .reusable = true}}, SHIFT(423),
  [1707] = {.entry = {.count = 1, .reusable = true}}, SHIFT(359),
  [1709] = {.entry = {.count = 1, .reusable = true}}, SHIFT(910),
  [1711] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1145),
  [1713] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_option_members_value_repeat1, 2, 0, 0), SHIFT_REPEAT(582),
  [1716] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_option_members_value_repeat1, 2, 0, 0),
  [1718] = {.entry = {.count = 1, .reusable = true}}, SHIFT(652),
  [1720] = {.entry = {.count = 1, .reusable = true}}, SHIFT(135),
  [1722] = {.entry = {.count = 1, .reusable = true}}, SHIFT(799),
  [1724] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1002),
  [1726] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_codeunit_declaration, 5, 0, 2),
  [1728] = {.entry = {.count = 1, .reusable = true}}, SHIFT(943),
  [1730] = {.entry = {.count = 1, .reusable = true}}, SHIFT(427),
  [1732] = {.entry = {.count = 1, .reusable = true}}, SHIFT(609),
  [1734] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_key_field_list, 2, 0, 0),
  [1736] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_option_members_value, 1, 0, 0),
  [1738] = {.entry = {.count = 1, .reusable = true}}, SHIFT(849),
  [1740] = {.entry = {.count = 1, .reusable = true}}, SHIFT(842),
  [1742] = {.entry = {.count = 1, .reusable = true}}, SHIFT(812),
  [1744] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1038),
  [1746] = {.entry = {.count = 1, .reusable = true}}, SHIFT(814),
  [1748] = {.entry = {.count = 1, .reusable = true}}, SHIFT(77),
  [1750] = {.entry = {.count = 1, .reusable = true}}, SHIFT(430),
  [1752] = {.entry = {.count = 1, .reusable = true}}, SHIFT(126),
  [1754] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_key_declaration, 6, 0, 39),
  [1756] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_set_filter_statement_repeat1, 2, 0, 72), SHIFT_REPEAT(143),
  [1759] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_set_filter_statement_repeat1, 2, 0, 72),
  [1761] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_filter_conditions, 1, 0, 0),
  [1763] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_key_field_list, 1, 0, 0),
  [1765] = {.entry = {.count = 1, .reusable = true}}, SHIFT(174),
  [1767] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_key_field_list_repeat1, 2, 0, 0), SHIFT_REPEAT(609),
  [1770] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_key_field_list_repeat1, 2, 0, 0),
  [1772] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_where_conditions, 1, 0, 0),
  [1774] = {.entry = {.count = 1, .reusable = true}}, SHIFT(107),
  [1776] = {.entry = {.count = 1, .reusable = true}}, SHIFT(62),
  [1778] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_field_declaration, 8, 0, 59),
  [1780] = {.entry = {.count = 2, .reusable = true}}, REDUCE(aux_sym_parameter_list_repeat1, 2, 0, 0), SHIFT_REPEAT(584),
  [1783] = {.entry = {.count = 1, .reusable = true}}, REDUCE(aux_sym_parameter_list_repeat1, 2, 0, 0),
  [1785] = {.entry = {.count = 1, .reusable = true}}, SHIFT(740),
  [1787] = {.entry = {.count = 1, .reusable = true}}, SHIFT(410),
  [1789] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1122),
  [1791] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1128),
  [1793] = {.entry = {.count = 1, .reusable = true}}, SHIFT(830),
  [1795] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_declaration, 6, 0, 2),
  [1797] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1135),
  [1799] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1136),
  [1801] = {.entry = {.count = 1, .reusable = true}}, SHIFT(281),
  [1803] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1140),
  [1805] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1141),
  [1807] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1130),
  [1809] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_field_declaration, 11, 0, 59),
  [1811] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_filter_condition, 9, 0, 81),
  [1813] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_filter_condition, 12, 0, 84),
  [1815] = {.entry = {.count = 1, .reusable = true}}, SHIFT(914),
  [1817] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_key_field, 1, 0, 0),
  [1819] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__procedure_return_specification, 3, 0, 30),
  [1821] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_parameter, 4, 0, 31),
  [1823] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_conditional_table_relation, 5, 0, 0),
  [1825] = {.entry = {.count = 1, .reusable = true}}, SHIFT(459),
  [1827] = {.entry = {.count = 1, .reusable = true}}, SHIFT(790),
  [1829] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_tabledata_permission_list, 1, 0, 0),
  [1831] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__simple_table_relation, 5, 0, 0),
  [1833] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_field_reference, 3, 0, 35),
  [1835] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_object_id, 1, 0, 0),
  [1837] = {.entry = {.count = 1, .reusable = true}}, SHIFT(378),
  [1839] = {.entry = {.count = 1, .reusable = true}}, SHIFT(891),
  [1841] = {.entry = {.count = 1, .reusable = true}}, SHIFT(967),
  [1843] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__condition_field_reference, 1, 0, 44),
  [1845] = {.entry = {.count = 1, .reusable = true}}, SHIFT(637),
  [1847] = {.entry = {.count = 1, .reusable = true}}, SHIFT(347),
  [1849] = {.entry = {.count = 1, .reusable = true}}, SHIFT(644),
  [1851] = {.entry = {.count = 1, .reusable = true}}, SHIFT(350),
  [1853] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1104),
  [1855] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1123),
  [1857] = {.entry = {.count = 1, .reusable = true}}, SHIFT(27),
  [1859] = {.entry = {.count = 1, .reusable = true}}, SHIFT(981),
  [1861] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_data_type, 1, 0, 0),
  [1863] = {.entry = {.count = 1, .reusable = true}}, SHIFT(982),
  [1865] = {.entry = {.count = 1, .reusable = true}}, SHIFT(983),
  [1867] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_data_type, 1, 0, 49),
  [1869] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_option_member, 1, 0, 0),
  [1871] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_code_type, 4, 0, 26),
  [1873] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_tabledata_permission, 4, 0, 13),
  [1875] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_conditional_table_relation, 7, 0, 0),
  [1877] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__simple_table_relation, 7, 0, 0),
  [1879] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1018),
  [1881] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1019),
  [1883] = {.entry = {.count = 1, .reusable = true}}, SHIFT(329),
  [1885] = {.entry = {.count = 1, .reusable = true}}, SHIFT(954),
  [1887] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1036),
  [1889] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1037),
  [1891] = {.entry = {.count = 1, .reusable = true}}, SHIFT(655),
  [1893] = {.entry = {.count = 1, .reusable = true}}, SHIFT(332),
  [1895] = {.entry = {.count = 1, .reusable = true}}, SHIFT(656),
  [1897] = {.entry = {.count = 1, .reusable = true}}, SHIFT(333),
  [1899] = {.entry = {.count = 1, .reusable = true}}, SHIFT(658),
  [1901] = {.entry = {.count = 1, .reusable = true}}, SHIFT(340),
  [1903] = {.entry = {.count = 1, .reusable = true}}, SHIFT(743),
  [1905] = {.entry = {.count = 1, .reusable = true}}, SHIFT(741),
  [1907] = {.entry = {.count = 1, .reusable = true}}, SHIFT(969),
  [1909] = {.entry = {.count = 1, .reusable = true}}, SHIFT(269),
  [1911] = {.entry = {.count = 1, .reusable = true}}, SHIFT(995),
  [1913] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_key_declaration, 8, 0, 39),
  [1915] = {.entry = {.count = 1, .reusable = true}}, SHIFT(668),
  [1917] = {.entry = {.count = 1, .reusable = true}}, SHIFT(272),
  [1919] = {.entry = {.count = 1, .reusable = true}}, SHIFT(669),
  [1921] = {.entry = {.count = 1, .reusable = true}}, SHIFT(273),
  [1923] = {.entry = {.count = 1, .reusable = true}}, SHIFT(671),
  [1925] = {.entry = {.count = 1, .reusable = true}}, SHIFT(280),
  [1927] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_return_type, 1, 0, 0),
  [1929] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__procedure_return_specification, 2, 0, 19),
  [1931] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_parameter, 3, 0, 21),
  [1933] = {.entry = {.count = 1, .reusable = true}}, SHIFT(299),
  [1935] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1031),
  [1937] = {.entry = {.count = 1, .reusable = true}}, SHIFT(972),
  [1939] = {.entry = {.count = 1, .reusable = true}}, SHIFT(792),
  [1941] = {.entry = {.count = 1, .reusable = true}}, SHIFT(679),
  [1943] = {.entry = {.count = 1, .reusable = true}}, SHIFT(302),
  [1945] = {.entry = {.count = 1, .reusable = true}}, SHIFT(680),
  [1947] = {.entry = {.count = 1, .reusable = true}}, SHIFT(303),
  [1949] = {.entry = {.count = 1, .reusable = true}}, SHIFT(682),
  [1951] = {.entry = {.count = 1, .reusable = true}}, SHIFT(310),
  [1953] = {.entry = {.count = 1, .reusable = true}}, SHIFT(641),
  [1955] = {.entry = {.count = 1, .reusable = true}}, SHIFT(357),
  [1957] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1080),
  [1959] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1081),
  [1961] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1082),
  [1963] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1083),
  [1965] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_key_declaration, 9, 0, 39),
  [1967] = {.entry = {.count = 1, .reusable = true}}, SHIFT(171),
  [1969] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1129),
  [1971] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_filter_condition, 6, 0, 64),
  [1973] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_field_declaration, 10, 0, 59),
  [1975] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_where_condition, 6, 0, 77),
  [1977] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_lookup_where_condition, 6, 0, 74),
  [1979] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_lookup_where_condition, 6, 0, 75),
  [1981] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_where_condition, 6, 0, 76),
  [1983] = {.entry = {.count = 1, .reusable = true}}, SHIFT(489),
  [1985] = {.entry = {.count = 1, .reusable = true}}, SHIFT(925),
  [1987] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1073),
  [1989] = {.entry = {.count = 1, .reusable = true}}, SHIFT(509),
  [1991] = {.entry = {.count = 1, .reusable = true}}, SHIFT(44),
  [1993] = {.entry = {.count = 1, .reusable = true}}, SHIFT(724),
  [1995] = {.entry = {.count = 1, .reusable = true}}, SHIFT(7),
  [1997] = {.entry = {.count = 1, .reusable = true}}, SHIFT(460),
  [1999] = {.entry = {.count = 1, .reusable = true}}, SHIFT(344),
  [2001] = {.entry = {.count = 1, .reusable = true}}, SHIFT(860),
  [2003] = {.entry = {.count = 1, .reusable = true}}, SHIFT(508),
  [2005] = {.entry = {.count = 1, .reusable = true}}, SHIFT(253),
  [2007] = {.entry = {.count = 1, .reusable = true}}, SHIFT(771),
  [2009] = {.entry = {.count = 1, .reusable = true}}, SHIFT(678),
  [2011] = {.entry = {.count = 1, .reusable = true}}, SHIFT(129),
  [2013] = {.entry = {.count = 1, .reusable = true}}, SHIFT(521),
  [2015] = {.entry = {.count = 1, .reusable = true}}, SHIFT(115),
  [2017] = {.entry = {.count = 1, .reusable = true}}, SHIFT(402),
  [2019] = {.entry = {.count = 1, .reusable = true}}, SHIFT(470),
  [2021] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_permissions_value, 1, 0, 0),
  [2023] = {.entry = {.count = 1, .reusable = true}}, SHIFT(511),
  [2025] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_no_value, 1, 0, 0),
  [2027] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_return_value, 1, 0, 11),
  [2029] = {.entry = {.count = 1, .reusable = true}}, SHIFT(686),
  [2031] = {.entry = {.count = 1, .reusable = true}}, SHIFT(3),
  [2033] = {.entry = {.count = 1, .reusable = true}}, SHIFT(403),
  [2035] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_subtype_value, 1, 0, 0),
  [2037] = {.entry = {.count = 1, .reusable = true}}, SHIFT(726),
  [2039] = {.entry = {.count = 1, .reusable = true}}, SHIFT(610),
  [2041] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_single_instance_value, 1, 0, 0),
  [2043] = {.entry = {.count = 1, .reusable = true}}, SHIFT(561),
  [2045] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_page_id_value, 1, 0, 0),
  [2047] = {.entry = {.count = 1, .reusable = true}}, SHIFT(45),
  [2049] = {.entry = {.count = 1, .reusable = true}}, SHIFT(519),
  [2051] = {.entry = {.count = 1, .reusable = true}}, SHIFT(728),
  [2053] = {.entry = {.count = 1, .reusable = true}}, SHIFT(780),
  [2055] = {.entry = {.count = 1, .reusable = true}}, SHIFT(566),
  [2057] = {.entry = {.count = 1, .reusable = true}}, SHIFT(514),
  [2059] = {.entry = {.count = 1, .reusable = true}}, SHIFT(405),
  [2061] = {.entry = {.count = 1, .reusable = true}}, SHIFT(729),
  [2063] = {.entry = {.count = 1, .reusable = true}}, SHIFT(506),
  [2065] = {.entry = {.count = 1, .reusable = true}}, SHIFT(781),
  [2067] = {.entry = {.count = 1, .reusable = true}}, SHIFT(942),
  [2069] = {.entry = {.count = 1, .reusable = true}}, SHIFT(466),
  [2071] = {.entry = {.count = 1, .reusable = true}}, SHIFT(783),
  [2073] = {.entry = {.count = 1, .reusable = true}}, SHIFT(959),
  [2075] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_relation_value, 1, 0, 0),
  [2077] = {.entry = {.count = 1, .reusable = true}}, SHIFT(585),
  [2079] = {.entry = {.count = 1, .reusable = true}}, SHIFT(465),
  [2081] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_type_value, 1, 0, 0),
  [2083] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_field_class_value, 1, 0, 0),
  [2085] = {.entry = {.count = 1, .reusable = true}}, SHIFT(228),
  [2087] = {.entry = {.count = 1, .reusable = true}}, SHIFT(545),
  [2089] = {.entry = {.count = 1, .reusable = true}}, SHIFT(351),
  [2091] = {.entry = {.count = 1, .reusable = true}}, SHIFT(697),
  [2093] = {.entry = {.count = 1, .reusable = true}}, SHIFT(352),
  [2095] = {.entry = {.count = 1, .reusable = true}}, SHIFT(683),
  [2097] = {.entry = {.count = 1, .reusable = true}}, SHIFT(974),
  [2099] = {.entry = {.count = 1, .reusable = true}}, SHIFT(507),
  [2101] = {.entry = {.count = 1, .reusable = true}}, SHIFT(520),
  [2103] = {.entry = {.count = 1, .reusable = true}}, SHIFT(558),
  [2105] = {.entry = {.count = 1, .reusable = true}}, SHIFT(569),
  [2107] = {.entry = {.count = 1, .reusable = true}}, SHIFT(353),
  [2109] = {.entry = {.count = 1, .reusable = true}}, SHIFT(580),
  [2111] = {.entry = {.count = 1, .reusable = true}}, SHIFT(409),
  [2113] = {.entry = {.count = 1, .reusable = true}}, SHIFT(581),
  [2115] = {.entry = {.count = 1, .reusable = true}}, SHIFT(354),
  [2117] = {.entry = {.count = 1, .reusable = true}}, SHIFT(536),
  [2119] = {.entry = {.count = 1, .reusable = true}}, SHIFT(493),
  [2121] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_calc_formula_value, 1, 0, 0),
  [2123] = {.entry = {.count = 1, .reusable = true}}, SHIFT(411),
  [2125] = {.entry = {.count = 1, .reusable = true}}, SHIFT(840),
  [2127] = {.entry = {.count = 1, .reusable = true}}, SHIFT(937),
  [2129] = {.entry = {.count = 1, .reusable = true}}, SHIFT(984),
  [2131] = {.entry = {.count = 1, .reusable = true}}, SHIFT(695),
  [2133] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_data_type, 6, 0, 80),
  [2135] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_blank_zero_value, 1, 0, 0),
  [2137] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_editable_value, 1, 0, 0),
  [2139] = {.entry = {.count = 1, .reusable = true}}, SHIFT(938),
  [2141] = {.entry = {.count = 1, .reusable = true}}, SHIFT(542),
  [2143] = {.entry = {.count = 1, .reusable = true}}, SHIFT(730),
  [2145] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_option_caption_value, 1, 0, 0),
  [2147] = {.entry = {.count = 1, .reusable = true}}, SHIFT(543),
  [2149] = {.entry = {.count = 1, .reusable = true}}, SHIFT(732),
  [2151] = {.entry = {.count = 1, .reusable = true}}, SHIFT(733),
  [2153] = {.entry = {.count = 1, .reusable = true}}, SHIFT(544),
  [2155] = {.entry = {.count = 1, .reusable = true}}, SHIFT(735),
  [2157] = {.entry = {.count = 1, .reusable = true}}, SHIFT(736),
  [2159] = {.entry = {.count = 1, .reusable = true}}, SHIFT(631),
  [2161] = {.entry = {.count = 1, .reusable = true}}, SHIFT(640),
  [2163] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1039),
  [2165] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1043),
  [2167] = {.entry = {.count = 1, .reusable = true}}, SHIFT(490),
  [2169] = {.entry = {.count = 1, .reusable = true}}, SHIFT(636),
  [2171] = {.entry = {.count = 1, .reusable = true}}, SHIFT(590),
  [2173] = {.entry = {.count = 1, .reusable = true}}, SHIFT(485),
  [2175] = {.entry = {.count = 1, .reusable = true}}, SHIFT(105),
  [2177] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1046),
  [2179] = {.entry = {.count = 1, .reusable = true}}, SHIFT(602),
  [2181] = {.entry = {.count = 1, .reusable = true}}, SHIFT(834),
  [2183] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1011),
  [2185] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1012),
  [2187] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1013),
  [2189] = {.entry = {.count = 1, .reusable = true}}, SHIFT(744),
  [2191] = {.entry = {.count = 1, .reusable = true}}, SHIFT(948),
  [2193] = {.entry = {.count = 1, .reusable = true}}, SHIFT(964),
  [2195] = {.entry = {.count = 1, .reusable = true}}, SHIFT(481),
  [2197] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1006),
  [2199] = {.entry = {.count = 1, .reusable = true}}, SHIFT(530),
  [2201] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1020),
  [2203] = {.entry = {.count = 1, .reusable = true}}, SHIFT(4),
  [2205] = {.entry = {.count = 1, .reusable = true}}, SHIFT(940),
  [2207] = {.entry = {.count = 1, .reusable = true}}, SHIFT(326),
  [2209] = {.entry = {.count = 1, .reusable = true}}, SHIFT(327),
  [2211] = {.entry = {.count = 1, .reusable = true}}, SHIFT(328),
  [2213] = {.entry = {.count = 1, .reusable = true}}, SHIFT(398),
  [2215] = {.entry = {.count = 1, .reusable = true}}, SHIFT(713),
  [2217] = {.entry = {.count = 1, .reusable = true}}, SHIFT(608),
  [2219] = {.entry = {.count = 1, .reusable = true}}, SHIFT(597),
  [2221] = {.entry = {.count = 1, .reusable = true}}, SHIFT(334),
  [2223] = {.entry = {.count = 1, .reusable = true}}, SHIFT(335),
  [2225] = {.entry = {.count = 1, .reusable = true}}, SHIFT(336),
  [2227] = {.entry = {.count = 1, .reusable = true}}, SHIFT(337),
  [2229] = {.entry = {.count = 1, .reusable = true}}, SHIFT(338),
  [2231] = {.entry = {.count = 1, .reusable = true}}, SHIFT(339),
  [2233] = {.entry = {.count = 1, .reusable = true}}, SHIFT(474),
  [2235] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_where_clause, 4, 0, 0),
  [2237] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_relation_condition, 3, 0, 34),
  [2239] = {.entry = {.count = 1, .reusable = true}}, SHIFT(343),
  [2241] = {.entry = {.count = 1, .reusable = true}}, SHIFT(667),
  [2243] = {.entry = {.count = 1, .reusable = true}}, SHIFT(556),
  [2245] = {.entry = {.count = 1, .reusable = true}}, SHIFT(712),
  [2247] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1158),
  [2249] = {.entry = {.count = 1, .reusable = true}}, SHIFT(173),
  [2251] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym__procedure_name, 1, 0, 3),
  [2253] = {.entry = {.count = 1, .reusable = true}}, SHIFT(469),
  [2255] = {.entry = {.count = 1, .reusable = true}}, SHIFT(742),
  [2257] = {.entry = {.count = 1, .reusable = true}}, SHIFT(502),
  [2259] = {.entry = {.count = 1, .reusable = true}}, SHIFT(246),
  [2261] = {.entry = {.count = 1, .reusable = true}}, SHIFT(746),
  [2263] = {.entry = {.count = 1, .reusable = true}}, SHIFT(114),
  [2265] = {.entry = {.count = 1, .reusable = true}}, SHIFT(634),
  [2267] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_data_type, 6, 0, 79),
  [2269] = {.entry = {.count = 1, .reusable = true}}, SHIFT(557),
  [2271] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_else_clause, 2, 0, 0),
  [2273] = {.entry = {.count = 1, .reusable = true}}, SHIFT(247),
  [2275] = {.entry = {.count = 1, .reusable = true}}, SHIFT(166),
  [2277] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1025),
  [2279] = {.entry = {.count = 1, .reusable = true}}, SHIFT(815),
  [2281] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1047),
  [2283] = {.entry = {.count = 1, .reusable = true}}, SHIFT(816),
  [2285] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_data_type, 2, 0, 58),
  [2287] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1026),
  [2289] = {.entry = {.count = 1, .reusable = true}}, SHIFT(266),
  [2291] = {.entry = {.count = 1, .reusable = true}}, SHIFT(267),
  [2293] = {.entry = {.count = 1, .reusable = true}}, SHIFT(268),
  [2295] = {.entry = {.count = 1, .reusable = true}}, SHIFT(401),
  [2297] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_data_classification_value, 1, 0, 0),
  [2299] = {.entry = {.count = 1, .reusable = true}}, SHIFT(94),
  [2301] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_count_formula, 5, 0, 24),
  [2303] = {.entry = {.count = 1, .reusable = true}}, SHIFT(274),
  [2305] = {.entry = {.count = 1, .reusable = true}}, SHIFT(275),
  [2307] = {.entry = {.count = 1, .reusable = true}}, SHIFT(276),
  [2309] = {.entry = {.count = 1, .reusable = true}}, SHIFT(277),
  [2311] = {.entry = {.count = 1, .reusable = true}}, SHIFT(278),
  [2313] = {.entry = {.count = 1, .reusable = true}}, SHIFT(279),
  [2315] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_sum_formula, 5, 0, 23),
  [2317] = {.entry = {.count = 1, .reusable = true}}, SHIFT(687),
  [2319] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_average_formula, 5, 0, 23),
  [2321] = {.entry = {.count = 1, .reusable = true}}, SHIFT(283),
  [2323] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_min_formula, 5, 0, 23),
  [2325] = {.entry = {.count = 1, .reusable = true}}, SHIFT(788),
  [2327] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_max_formula, 5, 0, 23),
  [2329] = {.entry = {.count = 1, .reusable = true}}, SHIFT(96),
  [2331] = {.entry = {.count = 1, .reusable = true}}, SHIFT(472),
  [2333] = {.entry = {.count = 1, .reusable = true}}, SHIFT(749),
  [2335] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_modifier, 1, 0, 0),
  [2337] = {.entry = {.count = 1, .reusable = true}}, SHIFT(84),
  [2339] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_relation_condition, 6, 0, 61),
  [2341] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_relation_condition, 6, 0, 62),
  [2343] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1055),
  [2345] = {.entry = {.count = 1, .reusable = true}}, SHIFT(722),
  [2347] = {.entry = {.count = 1, .reusable = true}}, SHIFT(820),
  [2349] = {.entry = {.count = 1, .reusable = true}}, SHIFT(617),
  [2351] = {.entry = {.count = 1, .reusable = true}}, SHIFT(568),
  [2353] = {.entry = {.count = 1, .reusable = true}}, SHIFT(571),
  [2355] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1060),
  [2357] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_lookup_formula, 8, 0, 23),
  [2359] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_tabledata_permission_list, 3, 0, 0),
  [2361] = {.entry = {.count = 1, .reusable = true}}, SHIFT(296),
  [2363] = {.entry = {.count = 1, .reusable = true}}, SHIFT(297),
  [2365] = {.entry = {.count = 1, .reusable = true}}, SHIFT(298),
  [2367] = {.entry = {.count = 1, .reusable = true}}, SHIFT(5),
  [2369] = {.entry = {.count = 1, .reusable = true}}, SHIFT(8),
  [2371] = {.entry = {.count = 1, .reusable = true}}, SHIFT(928),
  [2373] = {.entry = {.count = 1, .reusable = true}}, SHIFT(606),
  [2375] = {.entry = {.count = 1, .reusable = true}}, SHIFT(304),
  [2377] = {.entry = {.count = 1, .reusable = true}}, SHIFT(305),
  [2379] = {.entry = {.count = 1, .reusable = true}}, SHIFT(306),
  [2381] = {.entry = {.count = 1, .reusable = true}}, SHIFT(307),
  [2383] = {.entry = {.count = 1, .reusable = true}}, SHIFT(308),
  [2385] = {.entry = {.count = 1, .reusable = true}}, SHIFT(309),
  [2387] = {.entry = {.count = 1, .reusable = true}}, SHIFT(492),
  [2389] = {.entry = {.count = 1, .reusable = true}}, SHIFT(611),
  [2391] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1070),
  [2393] = {.entry = {.count = 1, .reusable = true}}, SHIFT(313),
  [2395] = {.entry = {.count = 1, .reusable = true}}, SHIFT(371),
  [2397] = {.entry = {.count = 1, .reusable = true}},  ACCEPT_INPUT(),
  [2399] = {.entry = {.count = 1, .reusable = true}}, SHIFT(355),
  [2401] = {.entry = {.count = 1, .reusable = true}}, SHIFT(356),
  [2403] = {.entry = {.count = 1, .reusable = true}}, SHIFT(375),
  [2405] = {.entry = {.count = 1, .reusable = true}}, SHIFT(497),
  [2407] = {.entry = {.count = 1, .reusable = true}}, SHIFT(95),
  [2409] = {.entry = {.count = 1, .reusable = true}}, SHIFT(376),
  [2411] = {.entry = {.count = 1, .reusable = true}}, SHIFT(6),
  [2413] = {.entry = {.count = 1, .reusable = true}}, SHIFT(42),
  [2415] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1058),
  [2417] = {.entry = {.count = 1, .reusable = true}}, SHIFT(515),
  [2419] = {.entry = {.count = 1, .reusable = true}}, SHIFT(762),
  [2421] = {.entry = {.count = 1, .reusable = true}}, SHIFT(463),
  [2423] = {.entry = {.count = 1, .reusable = true}}, SHIFT(145),
  [2425] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_table_relation_condition, 7, 0, 63),
  [2427] = {.entry = {.count = 1, .reusable = true}}, SHIFT(649),
  [2429] = {.entry = {.count = 1, .reusable = true}}, SHIFT(46),
  [2431] = {.entry = {.count = 1, .reusable = true}}, SHIFT(932),
  [2433] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_object_name, 1, 0, 1),
  [2435] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1118),
  [2437] = {.entry = {.count = 1, .reusable = true}}, SHIFT(549),
  [2439] = {.entry = {.count = 1, .reusable = true}}, SHIFT(550),
  [2441] = {.entry = {.count = 1, .reusable = true}}, SHIFT(551),
  [2443] = {.entry = {.count = 1, .reusable = true}}, SHIFT(552),
  [2445] = {.entry = {.count = 1, .reusable = true}}, SHIFT(945),
  [2447] = {.entry = {.count = 1, .reusable = true}}, SHIFT(946),
  [2449] = {.entry = {.count = 1, .reusable = true}}, SHIFT(947),
  [2451] = {.entry = {.count = 1, .reusable = true}}, SHIFT(782),
  [2453] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1008),
  [2455] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1120),
  [2457] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1151),
  [2459] = {.entry = {.count = 1, .reusable = true}}, SHIFT(596),
  [2461] = {.entry = {.count = 1, .reusable = true}}, SHIFT(646),
  [2463] = {.entry = {.count = 1, .reusable = true}}, SHIFT(677),
  [2465] = {.entry = {.count = 1, .reusable = true}}, SHIFT(510),
  [2467] = {.entry = {.count = 1, .reusable = true}}, SHIFT(841),
  [2469] = {.entry = {.count = 1, .reusable = true}}, SHIFT(739),
  [2471] = {.entry = {.count = 1, .reusable = true}}, SHIFT(150),
  [2473] = {.entry = {.count = 1, .reusable = true}}, SHIFT(598),
  [2475] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1126),
  [2477] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_data_type, 4, 0, 48),
  [2479] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1127),
  [2481] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_data_type, 4, 0, 69),
  [2483] = {.entry = {.count = 1, .reusable = true}}, SHIFT(562),
  [2485] = {.entry = {.count = 1, .reusable = true}}, SHIFT(563),
  [2487] = {.entry = {.count = 1, .reusable = true}}, SHIFT(564),
  [2489] = {.entry = {.count = 1, .reusable = true}}, SHIFT(565),
  [2491] = {.entry = {.count = 1, .reusable = true}}, SHIFT(986),
  [2493] = {.entry = {.count = 1, .reusable = true}}, SHIFT(987),
  [2495] = {.entry = {.count = 1, .reusable = true}}, SHIFT(988),
  [2497] = {.entry = {.count = 1, .reusable = true}}, SHIFT(795),
  [2499] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1076),
  [2501] = {.entry = {.count = 1, .reusable = true}}, SHIFT(600),
  [2503] = {.entry = {.count = 1, .reusable = true}}, SHIFT(468),
  [2505] = {.entry = {.count = 1, .reusable = true}}, SHIFT(601),
  [2507] = {.entry = {.count = 1, .reusable = true}}, SHIFT(705),
  [2509] = {.entry = {.count = 1, .reusable = true}}, SHIFT(360),
  [2511] = {.entry = {.count = 1, .reusable = true}}, SHIFT(604),
  [2513] = {.entry = {.count = 1, .reusable = true}}, SHIFT(605),
  [2515] = {.entry = {.count = 1, .reusable = true}}, SHIFT(140),
  [2517] = {.entry = {.count = 1, .reusable = true}}, SHIFT(531),
  [2519] = {.entry = {.count = 1, .reusable = true}}, SHIFT(825),
  [2521] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1143),
  [2523] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_lookup_formula, 4, 0, 23),
  [2525] = {.entry = {.count = 1, .reusable = true}}, SHIFT(575),
  [2527] = {.entry = {.count = 1, .reusable = true}}, SHIFT(576),
  [2529] = {.entry = {.count = 1, .reusable = true}}, SHIFT(577),
  [2531] = {.entry = {.count = 1, .reusable = true}}, SHIFT(578),
  [2533] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1022),
  [2535] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1023),
  [2537] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1024),
  [2539] = {.entry = {.count = 1, .reusable = true}}, SHIFT(808),
  [2541] = {.entry = {.count = 1, .reusable = true}}, SHIFT(148),
  [2543] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1147),
  [2545] = {.entry = {.count = 1, .reusable = true}}, SHIFT(664),
  [2547] = {.entry = {.count = 1, .reusable = true}}, SHIFT(826),
  [2549] = {.entry = {.count = 1, .reusable = true}}, SHIFT(632),
  [2551] = {.entry = {.count = 1, .reusable = true}}, SHIFT(827),
  [2553] = {.entry = {.count = 1, .reusable = true}}, SHIFT(828),
  [2555] = {.entry = {.count = 1, .reusable = true}}, SHIFT(824),
  [2557] = {.entry = {.count = 1, .reusable = true}}, SHIFT(362),
  [2559] = {.entry = {.count = 1, .reusable = true}}, SHIFT(9),
  [2561] = {.entry = {.count = 1, .reusable = true}}, SHIFT(505),
  [2563] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_count_formula, 4, 0, 24),
  [2565] = {.entry = {.count = 1, .reusable = true}}, SHIFT(503),
  [2567] = {.entry = {.count = 1, .reusable = true}}, SHIFT(975),
  [2569] = {.entry = {.count = 1, .reusable = true}}, SHIFT(907),
  [2571] = {.entry = {.count = 1, .reusable = true}}, SHIFT(657),
  [2573] = {.entry = {.count = 1, .reusable = true}}, SHIFT(172),
  [2575] = {.entry = {.count = 1, .reusable = true}}, SHIFT(10),
  [2577] = {.entry = {.count = 1, .reusable = true}}, SHIFT(710),
  [2579] = {.entry = {.count = 1, .reusable = true}}, SHIFT(992),
  [2581] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_sum_formula, 4, 0, 23),
  [2583] = {.entry = {.count = 1, .reusable = true}}, SHIFT(999),
  [2585] = {.entry = {.count = 1, .reusable = true}}, SHIFT(670),
  [2587] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1096),
  [2589] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_average_formula, 4, 0, 23),
  [2591] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1001),
  [2593] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_min_formula, 4, 0, 23),
  [2595] = {.entry = {.count = 1, .reusable = true}}, SHIFT(681),
  [2597] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1117),
  [2599] = {.entry = {.count = 1, .reusable = true}}, SHIFT(718),
  [2601] = {.entry = {.count = 1, .reusable = true}}, SHIFT(904),
  [2603] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1003),
  [2605] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_max_formula, 4, 0, 23),
  [2607] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1005),
  [2609] = {.entry = {.count = 1, .reusable = true}}, SHIFT(711),
  [2611] = {.entry = {.count = 1, .reusable = true}}, SHIFT(843),
  [2613] = {.entry = {.count = 1, .reusable = true}}, SHIFT(720),
  [2615] = {.entry = {.count = 1, .reusable = true}}, SHIFT(1148),
  [2617] = {.entry = {.count = 1, .reusable = true}}, REDUCE(sym_attribute_arguments, 3, 0, 10),
  [2619] = {.entry = {.count = 1, .reusable = true}}, SHIFT(700),
  [2621] = {.entry = {.count = 1, .reusable = true}}, SHIFT(701),
  [2623] = {.entry = {.count = 1, .reusable = true}}, SHIFT(703),
  [2625] = {.entry = {.count = 1, .reusable = true}}, SHIFT(704),
  [2627] = {.entry = {.count = 1, .reusable = true}}, SHIFT(706),
  [2629] = {.entry = {.count = 1, .reusable = true}}, SHIFT(707),
  [2631] = {.entry = {.count = 1, .reusable = true}}, SHIFT(775),
};

#ifdef __cplusplus
extern "C" {
#endif
#ifdef TREE_SITTER_HIDE_SYMBOLS
#define TS_PUBLIC
#elif defined(_WIN32)
#define TS_PUBLIC __declspec(dllexport)
#else
#define TS_PUBLIC __attribute__((visibility("default")))
#endif

TS_PUBLIC const TSLanguage *tree_sitter_al(void) {
  static const TSLanguage language = {
    .version = LANGUAGE_VERSION,
    .symbol_count = SYMBOL_COUNT,
    .alias_count = ALIAS_COUNT,
    .token_count = TOKEN_COUNT,
    .external_token_count = EXTERNAL_TOKEN_COUNT,
    .state_count = STATE_COUNT,
    .large_state_count = LARGE_STATE_COUNT,
    .production_id_count = PRODUCTION_ID_COUNT,
    .field_count = FIELD_COUNT,
    .max_alias_sequence_length = MAX_ALIAS_SEQUENCE_LENGTH,
    .parse_table = &ts_parse_table[0][0],
    .small_parse_table = ts_small_parse_table,
    .small_parse_table_map = ts_small_parse_table_map,
    .parse_actions = ts_parse_actions,
    .symbol_names = ts_symbol_names,
    .field_names = ts_field_names,
    .field_map_slices = ts_field_map_slices,
    .field_map_entries = ts_field_map_entries,
    .symbol_metadata = ts_symbol_metadata,
    .public_symbol_map = ts_symbol_map,
    .alias_map = ts_non_terminal_alias_map,
    .alias_sequences = &ts_alias_sequences[0][0],
    .lex_modes = ts_lex_modes,
    .lex_fn = ts_lex,
    .primary_state_ids = ts_primary_state_ids,
  };
  return &language;
}
#ifdef __cplusplus
}
#endif
