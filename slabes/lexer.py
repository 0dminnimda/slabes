import re
import token
from tokenize import TokenInfo
from itertools import accumulate
from enum import Enum, auto

from . import errors
from .ply import lex as _ply_lex
from .errors import report_fatal_at, report_at
from .location import Location


class Keywords(Enum):
    TINY = token.N_TOKENS
    SMALL = auto()
    NORMAL = auto()
    BIG = auto()
    FIELD = auto()
    BEGIN = auto()
    END = auto()
    UNTIL = auto()
    DO = auto()
    CHECK = auto()
    GO = auto()
    RL = auto()
    RR = auto()
    SONAR = auto()
    COMPASS = auto()
    RETURN = auto()
    N_TOKENS = auto()


token.N_TOKENS = Keywords.N_TOKENS.value


INITIAL_STATE = "INITIAL"
INVALID_STATE = "INVALID"


class Lexer:
    def __init__(self) -> None:
        self.ply_lexer: _ply_lex.Lexer = _ply_lex.lex(module=self, optimize=True)
        self.reset("", "")

    def reset(self, text: str, filename: str):
        self.text = text
        self.lines = text.splitlines()
        self.cumlen = [0] + list(accumulate((len(it) + 1 for it in self.lines)))
        self.filename = filename
        self.reset_ply(text)

    def reset_ply(self, text: str, state: str = INITIAL_STATE):
        self.reset_ply_state(state)
        self.ply_lexer.input(text)
        self.ply_lexer.lineno = 1

    def reset_ply_state(self, state: str = INITIAL_STATE):
        self.ply_lexer.begin(state)

    def skip_ply_by(self, count: int):
        lexpos = self.ply_lexer.lexpos
        self.ply_lexer.lexpos += count
        self.ply_lexer.lineno += self.text.count("\n", lexpos, self.ply_lexer.lexpos)

    token_name_to_type = {
        "NAME": token.NAME,
        "NUMBER": token.NUMBER,
        "COMMENT": token.COMMENT,
    }

    for k, v in Keywords.__members__.items():
        if v is Keywords.N_TOKENS:
            continue
        token_name_to_type[k] = v.value
        token.tok_name[v.value] = k

    states = ((INVALID_STATE, "exclusive"),)

    keywords = {
        k.lower(): k
        for k, v in Keywords.__members__.items()
        if v is not Keywords.N_TOKENS
    }

    # keywords can be shortened while those shortenings are unique
    # small = smal = sma = sm, but not s, because of sonar
    reserved_names = tuple(keywords.keys())
    for name in reserved_names:
        for partial in accumulate(name):
            if partial == name:
                continue

            if partial in keywords:
                keywords[partial] = ""
            else:
                keywords[partial] = keywords[name]
    keywords = {k: v for k, v in keywords.items() if v}

    multichar_literals = [
        # statment delimeters
        ",", ".",

        # assigment
        "<<", ">>",

        # arithmetic operators
        "+", "-", "\\", "/",

        # comparison operators
        "==", "<>", "<=", "=>",

        # brackets
        "(", ")", "[", "]",
    ]
    token_name_to_type.update(dict.fromkeys(multichar_literals, token.OP))

    tokens = list(token_name_to_type.keys())

    t_ANY_OP = "|".join(re.escape(it) for it in multichar_literals)
    t_ANY_COMMENT = r"\#.*"
    t_ANY_ignore = " \t"

    t_INITIAL_NUMBER = r"\b(?!_)[A-W0-9_]+(?<!_)\b"

    def t_INITIAL_NAME(self, t):
        r"\b[a-z_][a-z0-9_]*\b"
        t.type = self.keywords.get(t.value, "NAME")
        return t

    def t_INVALID_NAME_NUMBER(self, t):
        r"\b[a-wA-W0-9_]+\b"
        tok = self.ply_token_to_py(t)
        loc = Location.from_token(self.filename, tok)
        if tok.string[0].isdigit() and not tok.string.isupper():
            msg = f"numbers have to be uppercase. Did you mean '{tok.string.upper()}'?"
            t.type = "NUMBER"
        elif tok.string.startswith("_"):
            msg = f"numbers cannot start with an underscore. Did you mean '{tok.string.lstrip('_')}'?"
            t.type = "NAME"
        elif not tok.string[0].isdigit() and not tok.string.islower():
            msg = f"names have to be lowercase. Did you mean '{tok.string.lower()}'?"
            t.type = "NAME"
        elif not tok.string.isupper() and not tok.string.islower():
            # XXX: is it even reachable?
            msg = "numbers have to be uppercase and names have to be lowercase"
            t.type = "NUMBER"
        elif tok.string.endswith("_"):
            msg = f"numbers cannot end with an underscore. Did you mean '{tok.string.rstrip('_')}'?"
            t.type = "NAME"
        else:
            msg = "invalid number or name"
            t.type = "NAME"
        report_at(loc, errors.SyntaxError, msg, tok.line)
        self.reset_ply_state()
        return t

    def t_ANY_newline(self, t):
        r"\n+"
        t.lexer.lineno += t.value.count("\n")

    def t_INVALID_error(self, t):
        tok = self.ply_token_to_py(t)
        loc = Location.from_token(self.filename, tok)
        # point to just one character because error token goes to the end of the string
        loc = loc.without_end()
        msg = "illegal combination of characters"
        report_fatal_at(loc, errors.SyntaxError, msg, tok.line)

    def t_INITIAL_error(self, t):
        self.reset_ply(self.text, INVALID_STATE)
        self.skip_ply_by(t.lexpos)
        return self.ply_lexer.token()

    def ply_token_to_py(self, tok):
        string = tok.value
        type = self.token_name_to_type.get(tok.type, token.OP)
        lineno = tok.lineno
        column_offset = tok.lexpos - self.cumlen[lineno - 1]
        end_lineno = lineno + string.count("\n")
        if lineno == end_lineno:
            end_column_offset = column_offset + len(string)
        else:
            end_column_offset = tok.lexpos + len(string) - self.cumlen[end_lineno - 1]
        line = self.lines[lineno - 1]
        return TokenInfo(
            type, string, (lineno, column_offset), (end_lineno, end_column_offset), line
        )


_lexer = Lexer()


def lex(text: str, filename: str = "<unknown>"):
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    _lexer.reset(text, filename)

    for tok in _lexer.ply_lexer:
        yield _lexer.ply_token_to_py(tok)
    yield TokenInfo(
        token.ENDMARKER, "", (len(_lexer.lines) + 1, 0), (len(_lexer.lines) + 1, 0), ""
    )
