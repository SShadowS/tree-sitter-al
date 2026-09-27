"""Independent recognition and evaluation of AL conditional directives.

The semantics are the COMPILER's, recorded in docs/preproc-directive-semantics.md
and established by tools/config_oracle/probe_alc.py. Nothing here consults the
grammar or imports tree_sitter: a resolver that read the tree would let a
grammar bug hide itself (spec section 1).
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field


class ResolveError(Exception):
    """A construct outside the probed semantics. Reported as cannot-validate."""

    def __init__(self, reason: str, offset: int, detail: str = ""):
        super().__init__(f"{reason} at byte {offset}{': ' + detail if detail else ''}")
        self.reason = reason
        self.offset = offset


@dataclass(frozen=True)
class Sym:
    name: str


@dataclass(frozen=True)
class Lit:
    value: bool


@dataclass(frozen=True)
class Not:
    operand: object


@dataclass(frozen=True)
class And:
    left: object
    right: object


@dataclass(frozen=True)
class Or:
    left: object
    right: object


@dataclass(frozen=True)
class Condition:
    expr: object
    start: int
    end: int
    symbols: frozenset


_TOKEN = re.compile(rb"[ \t]*(?:(?P<ident>[A-Za-z_][A-Za-z0-9_]*)|(?P<punct>[()])|(?P<comment>//.*)|(?P<block>/\*)|(?P<other>[^ \t]))")
_KEYWORDS = {b"and", b"or", b"not"}
_LITERALS = {b"true": True, b"false": False}
_UNSUPPORTED_OPS = {b"xor"}


def _tokens(buf: bytes, start: int, end: int):
    pos = start
    out = []
    while pos < end:
        if not buf[pos:end].strip(b" \t"):
            break  # nothing left but trailing spaces/tabs -- not a token to raise on
        m = _TOKEN.match(buf, pos, end)
        if not m or m.end() == pos:
            raise ResolveError("unsupported-condition-token", pos)
        if m.group("comment") is not None:
            break
        if m.group("block") is not None:
            raise ResolveError("block-comment-on-directive", m.start("block"))
        if m.group("other") is not None:
            raise ResolveError("unsupported-condition-token", m.start("other"), m.group("other").decode("latin-1"))
        kind = "ident" if m.group("ident") is not None else "punct"
        out.append((kind, m.group(kind), m.start(kind), m.end(kind)))
        pos = m.end()
    return out


def parse_condition(buf: bytes, start: int, end: int) -> Condition:
    """Parse the condition occupying buf[start:end] (the text after `#if`/`#elif`)."""
    toks = _tokens(buf, start, end)
    if not toks:
        raise ResolveError("empty-condition", start)
    pos = 0
    symbols: set[str] = set()

    def peek_kw():
        if pos < len(toks) and toks[pos][0] == "ident":
            return toks[pos][1].lower()
        return None

    def primary():
        nonlocal pos
        if pos >= len(toks):
            raise ResolveError("unsupported-condition", end, "operand expected")
        kind, text, s, _ = toks[pos]
        if kind == "punct" and text == b"(":
            pos += 1
            inner = or_expr()
            if pos >= len(toks) or toks[pos][1] != b")":
                raise ResolveError("unsupported-condition", s, "unbalanced parenthesis")
            pos += 1
            return inner
        if kind == "ident" and text.lower() in _KEYWORDS:
            raise ResolveError("unsupported-condition", s, "operator where an operand is required")
        if kind == "ident" and text.lower() in _UNSUPPORTED_OPS:
            raise ResolveError("unsupported-condition", s)
        if kind == "ident":
            pos += 1
            if text.lower() in _LITERALS:
                return Lit(_LITERALS[text.lower()])
            symbols.add(text.decode("ascii"))
            return Sym(text.decode("ascii"))
        raise ResolveError("unsupported-condition", s)

    def unary():
        nonlocal pos
        if peek_kw() == b"not":
            pos += 1
            return Not(unary())
        return primary()

    def and_expr():
        nonlocal pos
        left = unary()
        while peek_kw() == b"and":
            pos += 1
            left = And(left, unary())
        return left

    def or_expr():
        nonlocal pos
        left = and_expr()
        while peek_kw() == b"or":
            pos += 1
            left = Or(left, and_expr())
        return left

    expr = or_expr()
    if pos != len(toks):
        raise ResolveError("unsupported-condition", toks[pos][2], "trailing token")
    return Condition(expr, toks[0][2], toks[-1][3], frozenset(symbols))


def evaluate(expr, env: frozenset) -> bool:
    if isinstance(expr, Sym):
        return expr.name in env
    if isinstance(expr, Lit):
        return expr.value
    if isinstance(expr, Not):
        return not evaluate(expr.operand, env)
    if isinstance(expr, And):
        return evaluate(expr.left, env) and evaluate(expr.right, env)
    if isinstance(expr, Or):
        return evaluate(expr.left, env) or evaluate(expr.right, env)
    raise TypeError(expr)


_DIRECTIVE = re.compile(rb"[ \t]*#[ \t]*(?P<word>[A-Za-z_][A-Za-z0-9_]*)")
_WORDS = {b"if", b"elif", b"else", b"endif", b"define", b"undef", b"pragma", b"region", b"endregion"}
_EXTRA_KIND = {"pragma": "pragma", "region": "preproc_region", "endregion": "preproc_endregion",
               "define": "preproc_define", "undef": "preproc_undef"}
_SYMBOL = re.compile(rb"[ \t]+(?P<sym>[A-Za-z_][A-Za-z0-9_]*)[ \t]*(?://.*)?$")
_REST_EMPTY = re.compile(rb"[ \t]*(?://.*)?$")
_BLOCK_ON_LINE = re.compile(rb"[ \t]*/\*")
_HASH_WORD = re.compile(rb"[ \t]*(?P<word>[A-Za-z_][A-Za-z0-9_]*)")


@dataclass(frozen=True)
class Directive:
    kind: str
    hash: int
    line_start: int
    keyword_end: int
    cond: Condition | None
    symbol: str | None
    line_end: int
    next_line: int


@dataclass(frozen=True)
class ExtraEvent:
    kind: str
    start: int
    end: int


@dataclass
class Resolution:
    env0: frozenset
    masked: bytes
    active: bytearray
    directives: list = field(default_factory=list)
    arm_choice: dict = field(default_factory=dict)
    extras: list = field(default_factory=list)
    trace: list = field(default_factory=list)


def _lines(src: bytes):
    """(line_start, line_end, next_line) for every line; line_end excludes \\r\\n."""
    pos, n = 0, len(src)
    while pos < n:
        nl = src.find(b"\n", pos)
        nxt = n if nl < 0 else nl + 1
        end = n if nl < 0 else nl
        if end > pos and src[end - 1:end] == b"\r":
            end -= 1
        yield pos, end, nxt
        pos = nxt


def _parse_directive(src: bytes, ls: int, le: int, nxt: int) -> Directive | None:
    if ls == 0 and src.startswith(b"\xef\xbb\xbf"):
        ls = 3                      # a leading BOM precedes the first line's text
    m = _DIRECTIVE.match(src, ls, le)
    if not m:
        return None
    word = m.group("word")
    after = m.end("word")
    if word.lower() not in _WORDS:
        raise ResolveError("unknown-directive", m.start(), word.decode("latin-1"))
    kind = word.lower().decode()
    hash_ = src.index(b"#", ls, le)
    cond = sym = None
    if kind in ("if", "elif"):
        cond = parse_condition(src, after, le)
    elif kind in ("else", "endif"):
        if _BLOCK_ON_LINE.match(src, after, le):
            raise ResolveError("block-comment-on-directive", after)
        if not _REST_EMPTY.match(src, after, le):
            raise ResolveError("trailing-token", after)
    elif kind in ("define", "undef"):
        sm = _SYMBOL.match(src, after, le)
        if not sm:
            raise ResolveError("malformed-define", after)
        sym = sm.group("sym").decode("ascii")
    return Directive(kind, hash_, ls, after, cond, sym, le, nxt)


class _Lexer:
    """Active-text lexer: tracks the states that can span a line."""

    NORMAL, BLOCK, VERBATIM = range(3)

    def __init__(self, src: bytes, extras: list, lenient: bool = False):
        self.src, self.extras, self.state, self.open_at = src, extras, self.NORMAL, 0
        self.lenient = lenient

    def line(self, ls: int, le: int) -> None:
        s, i = self.src, ls
        while i < le:
            if self.state == self.BLOCK:
                j = s.find(b"*/", i, le)
                if j < 0:
                    return
                self.extras.append(ExtraEvent("multiline_comment", self.open_at, j + 2))
                self.state, i = self.NORMAL, j + 2
            elif self.state == self.VERBATIM:
                j = s.find(b"'", i, le)
                while j >= 0 and s[j + 1:j + 2] == b"'":
                    j = s.find(b"'", j + 2, le)
                if j < 0:
                    return
                self.state, i = self.NORMAL, j + 1
            else:
                c = s[i:i + 1]
                if s.startswith(b"//", i):
                    self.extras.append(ExtraEvent("comment", i, le))
                    return
                if s.startswith(b"/*", i):
                    self.state, self.open_at, i = self.BLOCK, i, i + 2
                elif s.startswith(b"@'", i):
                    self.state, i = self.VERBATIM, i + 2
                elif c in (b"'", b'"'):
                    j = s.find(c, i + 1, le)
                    while c == b"'" and j >= 0 and s[j + 1:j + 2] == b"'":
                        j = s.find(c, j + 2, le)
                    if j < 0:
                        if self.lenient:  # alc never lexes an inactive arm's text
                            i = le         # so a lone quote there is not our error to raise
                            continue
                        raise ResolveError("unterminated-active-string", i)
                    i = j + 1
                elif c == b"#":
                    m = _HASH_WORD.match(s, i + 1, le)
                    if m and m.group("word").lower() in _WORDS and not self.lenient:
                        raise ResolveError("directive-after-code", i)
                    i += 1
                else:
                    i += 1


@dataclass
class _Frame:
    if_hash: int
    parent_active: bool
    taken: bool
    active: bool
    seen_else: bool


def resolve(source: bytes, env0: frozenset) -> Resolution:
    """Resolve one configuration. `env0` is the assignment of preprocessorSymbols."""
    env = set(env0)
    active = bytearray(len(source))
    masked = bytearray(source)
    res = Resolution(env0=env0, masked=b"", active=active)
    lexer = _Lexer(source, res.extras)
    stack: list[_Frame] = []

    def current_active() -> bool:
        return stack[-1].active if stack else True

    lead = 3 if source.startswith(b"\xef\xbb\xbf") else 0

    def blank(a: int, b: int) -> None:
        for k in range(max(a, lead), b):
            if masked[k] not in (0x0D, 0x0A):
                masked[k] = 0x20

    for ls, le, nxt in _lines(source):
        here = current_active()
        d = None
        if not here or lexer.state == _Lexer.NORMAL:
            d = _parse_directive(source, ls, le, nxt)
        if d is not None and d.kind in ("if", "elif", "else", "endif"):
            res.directives.append(d)
            if d.kind == "if":
                taken = here and evaluate(d.cond.expr, frozenset(env))
                stack.append(_Frame(d.hash, here, taken, taken, False))
                if here:
                    res.arm_choice[d.hash] = d.hash if taken else None
            else:
                if not stack:
                    raise ResolveError(f"unbalanced-{d.kind}", d.hash)
                f = stack[-1]
                if d.kind == "elif":
                    if f.seen_else:
                        raise ResolveError("elif-after-else", d.hash)
                    f.active = f.parent_active and not f.taken and evaluate(d.cond.expr, frozenset(env))
                elif d.kind == "else":
                    if f.seen_else:
                        raise ResolveError("duplicate-else", d.hash)
                    f.seen_else = True
                    f.active = f.parent_active and not f.taken
                else:
                    stack.pop()
                if d.kind in ("elif", "else") and f.active:
                    f.taken = True
                    res.arm_choice[f.if_hash] = d.hash
            blank(ls, nxt)
            continue
        if not here:
            blank(ls, nxt)
            continue
        for k in range(ls, nxt):
            active[k] = 1
        if d is not None:  # define/undef/pragma/region/endregion in active text
            if d.kind == "define":
                env.add(d.symbol)
            elif d.kind == "undef":
                env.discard(d.symbol)
            res.extras.append(ExtraEvent(_EXTRA_KIND[d.kind], d.hash, le))
            continue
        lexer.line(ls, le)
    if stack:
        raise ResolveError("unbalanced-if", stack[-1].if_hash)
    if lexer.state != _Lexer.NORMAL:
        raise ResolveError("unterminated-active-" + ("comment" if lexer.state == _Lexer.BLOCK else "verbatim"), len(source))
    res.masked = bytes(masked)
    res.extras.sort(key=lambda e: e.start)
    return res


@dataclass
class Discovery:
    directives: list
    free_symbols: tuple
    has_conditionals: bool


def _lenient_scan(source: bytes):
    """One naive whole-file pass, lexed as if every line were active.

    Cheap seed for the fixpoint in `discover()` below — not a correct answer
    on its own. A block comment or verbatim string that only spans lines
    because THIS pass treats an inactive arm as active can swallow real
    directives (and, symmetrically, one that alc never lexes because its
    arm is dead can look here like it "crosses" a directive that in fact
    still ends the group just fine). Never raises past the caller for that
    reason; a malformed directive line still raises through `_parse_directive`.
    """
    directives, cond_syms = [], set()
    lexer = _Lexer(source, [], lenient=True)
    for ls, le, nxt in _lines(source):
        dir_ = _parse_directive(source, ls, le, nxt) if lexer.state == _Lexer.NORMAL else None
        if dir_ is None:
            lexer.line(ls, le)
            continue
        if dir_.kind in ("if", "elif", "else", "endif"):
            directives.append(dir_)
            if dir_.cond is not None:
                cond_syms |= dir_.cond.symbols
    return directives, cond_syms


def discover(source: bytes) -> Discovery:
    """Find every conditional directive line and the free-symbol universe.

    No single lexing pass over the whole file — active or not — can see
    every directive an arbitrary configuration would reach: `resolve()`
    never lexes an inactive arm's text (matching alc), so a block comment or
    verbatim string opened in one arm can hide a directive from every OTHER
    configuration's point of view while a whole-file scan either wrongly
    swallows it (if the scan treats that arm as active) or wrongly reports
    it missing (if the arm is genuinely dead in every configuration and the
    scan can't know that). So this is a fixpoint union over configurations:
    seed a seemingly-free symbol set from a cheap lenient whole-file scan,
    then repeatedly enumerate every configuration of the current symbol set,
    resolve() each (skipping any that raise), and union the directives and
    condition-symbols the *reached* arms actually contain — growing the
    symbol set — until it stops growing.
    """
    first_error = None
    try:
        seed_directives, seed_symbols = _lenient_scan(source)
    except ResolveError as e:
        seed_directives, seed_symbols = [], set()
        first_error = e

    symbols = set(seed_symbols)
    round_directives: dict = {}
    any_success = False
    for _ in range(8):
        round_directives = {}
        round_symbols = set(symbols)
        any_success = False
        names = sorted(symbols)
        for bits in itertools.product((0, 1), repeat=len(names)):
            env = frozenset(n for n, bit in zip(names, bits) if bit)
            try:
                r = resolve(source, env)
            except ResolveError as e:
                if first_error is None:
                    first_error = e
                continue
            any_success = True
            for dd in r.directives:
                round_directives[dd.hash] = dd
                if dd.cond is not None:
                    round_symbols |= dd.cond.symbols
        if round_symbols == symbols:
            break
        symbols = round_symbols
    else:
        raise ResolveError("discovery-not-converging", len(source))

    if not any_success:
        # Every configuration raised, even in the final round -- the lenient
        # seed's directives (if it even found any) are a cheap, unvalidated
        # guess and must never be handed back as though they were confirmed;
        # surface the failure so the caller records cannot-validate instead.
        if first_error is not None:
            raise first_error
        raise ResolveError("discovery-failed", len(source))

    directives = sorted(round_directives.values(), key=lambda dd: dd.hash)
    free = tuple(sorted(symbols))
    return Discovery(directives, free, any(x.kind == "if" for x in directives))


def configurations(disc: Discovery) -> list:
    names = disc.free_symbols
    return [frozenset(n for n, bit in zip(names, bits) if bit)
            for bits in itertools.product((0, 1), repeat=len(names))]


def config_id(env: frozenset, free: tuple) -> str:
    if not free:
        return "-"
    return ",".join(f"{n}={1 if n in env else 0}" for n in free)


def arm_coverage(source: bytes, disc: Discovery) -> list:
    """Hashes of arm directives that no configuration ever selects.

    An `#if` arm is counted as chosen only when `arm_choice` maps to it. A
    group whose `#if` is false and which has no `#else` selects nothing, and
    its `#if` arm is correctly unreached.
    """
    arms = {x.hash for x in disc.directives if x.kind in ("if", "elif", "else")}
    chosen = set()
    for env in configurations(disc):
        chosen |= {h for h in resolve(source, env).arm_choice.values() if h is not None}
    return sorted(arms - chosen)
