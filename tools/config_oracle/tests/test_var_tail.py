from tools.config_oracle.tests import witness

# preproc_split_var_section_tail (test/corpus/var_section_does_not_swallow_procedures_test.txt,
# case 2): the #if arm continues the global var section (Y) and then starts a
# procedure (P); no #else, so A=0 selects no arm at all (nothing merged, no P).
SRC = b"codeunit 1 T\n{\n    var\n        X: Integer;\n#if A\n        Y: Integer;\n\n    procedure P()\n    begin\n    end;\n#endif\n\n    procedure Q()\n    begin\n    end;\n}\n"

# An #else arm with its own `variables`, so both arms' merges are exercised
# (Ruling 1): A=1 merges Y and emits P, A=0 merges Z and emits R.
SRC_ELSE = (b"codeunit 1 T\n{\n    var\n        X: Integer;\n#if A\n        Y: Integer;\n\n"
           b"    procedure P()\n    begin\n    end;\n#else\n        Z: Integer;\n\n"
           b"    procedure R()\n    begin\n    end;\n#endif\n\n    procedure Q()\n    begin\n    end;\n}\n")


def test_var_tail_every_config(al_parser):
    witness.assert_produces(al_parser, SRC, "preproc_split_var_section_tail")
    witness.assert_all_pass(al_parser, SRC)


def test_var_tail_both_arms_have_variables(al_parser):
    witness.assert_produces(al_parser, SRC_ELSE, "preproc_split_var_section_tail")
    witness.assert_all_pass(al_parser, SRC_ELSE)


def test_merge_into_the_wrong_sibling_is_caught(al_parser, monkeypatch):
    from tools.config_oracle.lowering import engine

    # Baseline: every configuration passes before the mutation.
    witness.assert_all_pass(al_parser, SRC)

    monkeypatch.setattr(engine.VarTailMerge, "apply", lambda self, prev: prev)  # drop the variables
    v = witness.verdicts(al_parser, SRC)
    # A=1 selects the arm that merges Y into X's var_section: dropping it must be caught.
    assert v["A=1"][0] != "pass", v
    # A=0 selects no arm (no #else): nothing to merge, so the mutation changes nothing.
    assert v["A=0"][0] == "pass", v
