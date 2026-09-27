import pytest

from tools.config_oracle import directives as d


def test_free_symbols_include_every_symbol_used_in_a_reached_condition():
    # A symbol #define'd only inside an arm can still be supplied externally
    # via preprocessorSymbols, so it stays free whether or not it is ever
    # #define'd/#undef'd anywhere (controller ruling, fix round 1).
    src = b"#define DEBUG\n#if A and DEBUG\nx;\n#endif\n"
    disc = d.discover(src)
    assert disc.free_symbols == ("A", "DEBUG")
    assert len(d.configurations(disc)) == 4


def test_symbol_defined_only_inside_an_arm_is_still_free():
    src = b"#if X\n#define B\n#endif\n#if B\ny;\n#endif\n"
    disc = d.discover(src)
    assert disc.free_symbols == ("B", "X")
    # X unset means the internal "#define B" never fires, but B is still
    # reachable by supplying it externally.
    assert d.resolve(src, frozenset({"B"})).masked.count(b"y;") == 1


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


# --- Fixpoint discovery (controller ruling, fix round 1) ---
# A single whole-file lexing pass cannot see every directive: a block comment
# or verbatim string inside one arm swallows directive-looking text for EVERY
# configuration alike, even though resolve() (which never lexes inactive text)
# would see those directives just fine in a configuration where that arm is
# inactive. discover() must therefore union reached directives/symbols over
# enumerated configurations until the symbol set stops growing.

def test_discovery_finds_directives_hidden_by_an_active_arms_block_comment():
    src = b"#if A\n/* comment\n#if B\nx;\n#endif\ncomment end */\ny;\n#endif\n"
    disc = d.discover(src)
    assert [x.hash for x in disc.directives] == [0, 17, 26, 51]
    assert [x.kind for x in disc.directives] == ["if", "if", "endif", "endif"]
    assert disc.free_symbols == ("A", "B")


def test_discover_falls_back_to_seed_when_it_succeeds_but_every_configuration_raises():
    """Every configuration's resolve() fails here (each arm has its own
    unterminated string), but the LENIENT seed scan succeeds -- it tolerates
    an unterminated quote that might only be in dead code. discover() must
    hand back the seed's directives/symbols so the runner can report each
    configuration as its own cannot-validate record, rather than losing the
    file's directives entirely."""
    src = b"#if A\n  x := 'unterminated\n#else\n  y := 'also\n#endif\n"
    disc = d.discover(src)
    assert [x.kind for x in disc.directives] == ["if", "else", "endif"]
    assert disc.free_symbols == ("A",)
    assert disc.has_conditionals is True
    for env in (frozenset(), frozenset({"A"})):
        with pytest.raises(d.ResolveError):
            d.resolve(src, env)


def test_discover_raises_when_the_seed_itself_raises_and_every_configuration_raises():
    """An unknown directive word makes even the lenient seed scan raise (it
    still enforces real directive syntax, per _parse_directive), and it
    appears in every arm here so every configuration's resolve() raises too
    -- there is nothing to fall back to, so discover() must raise."""
    src = b"#if A\n#bogus\n#else\n#bogus\n#endif\n"
    with pytest.raises(d.ResolveError):
        d.discover(src)
    for env in (frozenset(), frozenset({"A"})):
        with pytest.raises(d.ResolveError):
            d.resolve(src, env)


def test_discover_still_succeeds_when_some_configuration_resolves():
    src = b"#if A\nx;\n#else\ny;\n#endif\n"
    disc = d.discover(src)
    assert disc.has_conditionals is True
    assert len(disc.directives) == 3


def test_discovery_survives_a_comment_never_closed_in_a_dead_arm():
    # "#if false" is never taken, so its "/*" is never lexed and never
    # swallows the following "#endif" — matching alc, which does not lex
    # inactive text. The whole-file seed scan alone WOULD wrongly cross the
    # directive here; discover() must not fail on it.
    disc = d.discover(b"#if false\n/* never closed\n#endif\n")
    assert len(disc.directives) == 2
    assert [x.kind for x in disc.directives] == ["if", "endif"]
