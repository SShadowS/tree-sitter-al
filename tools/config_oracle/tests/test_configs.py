import pytest

from tools.config_oracle import directives as d


def test_define_only_symbol_is_not_free():
    src = b"#define DEBUG\n#if A and DEBUG\nx;\n#endif\n"
    disc = d.discover(src)
    assert disc.free_symbols == ("A",)
    assert len(d.configurations(disc)) == 2


def test_enumeration_is_exhaustive_and_ordered():
    disc = d.discover(b"#if B\n#endif\n#if A\n#endif\n")
    assert [d.config_id(e, disc.free_symbols) for e in d.configurations(disc)] == [
        "A=0,B=0", "A=0,B=1", "A=1,B=0", "A=1,B=1"]


def test_no_conditionals():
    disc = d.discover(b"#region R\nx;\n#endregion\n")
    assert disc.has_conditionals is False
    assert d.config_id(frozenset(), disc.free_symbols) == "-"


def test_unreachable_arm_is_reported():
    src = b"#if A\n#if not A\nx;\n#endif\n#endif\n"
    disc = d.discover(src)
    unreached = d.arm_coverage(src, disc)
    assert unreached == [src.index(b"#if not A")]


def test_first_match_mutation_is_caught(monkeypatch):
    """Spec section 1 'Resolver self-test': switching #elif to independent
    evaluation must fail a named case. This test IS that named case run under
    the mutation; it asserts the mutant produces the wrong mask."""
    src = b"#if A\none;\n#elif A\ntwo;\n#endif\n"
    good = d.resolve(src, frozenset({"A"})).masked
    assert b"one;" in good and b"two;" not in good

    real = d.resolve

    def independent_elif(source, env0):
        # Mutant: evaluate each #elif as if no earlier arm had been taken.
        r = real(source.replace(b"#elif", b"#endif\n#if"), env0)
        return r

    monkeypatch.setattr(d, "resolve", independent_elif)
    mutant = d.resolve(src, frozenset({"A"})).masked
    assert b"two;" in mutant, "the mutation did not change behaviour, so the named case cannot detect it"


# --- Lenient discovery vs. strict resolve (controller ruling overriding the brief) ---
# alc never lexes inactive text, so discover() must not reject a file merely because
# some OTHER configuration's arm contains a construct that would only be illegal if
# that arm were active (an unterminated quote, a mid-line directive word). resolve()
# still enforces those rules strictly for the one configuration it evaluates.

def test_discover_is_lenient_about_unterminated_quote_in_an_arm():
    src = b"#if A\nx;\n#else\n  Message('abc\n#endif\n"
    disc = d.discover(src)
    assert len(disc.directives) == 3
    assert [x.kind for x in disc.directives] == ["if", "else", "endif"]


def test_resolve_still_strict_when_that_arm_is_active():
    src = b"#if A\nx;\n#else\n  Message('abc\n#endif\n"
    with pytest.raises(d.ResolveError) as err:
        d.resolve(src, frozenset())  # A unset: the #else arm (the bad one) is active
    assert err.value.reason == "unterminated-active-string"


def test_discover_is_lenient_about_mid_line_directive_word_in_an_arm():
    src = b"#if A\nx; #if B\n#endif\n"
    disc = d.discover(src)
    assert disc.has_conditionals is True
    with pytest.raises(d.ResolveError) as err:
        d.resolve(src, frozenset({"A"}))  # A set: the arm with the mid-line #if is active
    assert err.value.reason == "directive-after-code"
