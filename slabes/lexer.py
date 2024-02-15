import re
import token
from tokenize import TokenInfo
from itertools import accumulate

from .ply import lex as _ply_lex
from .errors import report_fatal_at
from .location import Location


class Lexer:
    def __init__(self) -> None:
        self.ply_lexer: _ply_lex.Lexer = _ply_lex.lex(module=self)
        self.reset("", "")

    def reset(self, text: str, filename: str):
        self.text = text
        self.lines = text.splitlines()
        self.cumlen = [0] + list(accumulate((len(it) + 1 for it in self.lines)))
        self.filename = filename
        self.reset_ply(text, "INITIAL")

    def reset_ply(self, text: str, state: str):
        self.ply_lexer.begin(state)
        self.ply_lexer.input(text)
        self.ply_lexer.lineno = 1

    def skip_ply_by(self, count: int):
        lexpos = self.ply_lexer.lexpos
        self.ply_lexer.lexpos += count
        self.ply_lexer.lineno += self.text.count("\n", lexpos, self.ply_lexer.lexpos)

    token_name_to_type = {
        "NAME": token.NAME,
        "NUMBER": token.NUMBER,
        "COMMENT": token.COMMENT,
    }

    states = (("INVALID", "exclusive"),)

    tokens = list(token_name_to_type.keys())

    literals = [",", ".", "=", "+", "-", "*", "/", "(", ")"]

    t_INITIAL_NAME = r"\b[a-z_][a-z0-9_]*\b"
    t_INITIAL_NUMBER = r"\b(?!_)[A-W0-9_]+(?<!_)\b"

    t_ANY_COMMENT = r"\#.*"
    t_ANY_ignore = " \t"

    def t_INVALID_NAME_NUMBER(self, t):
        r"\b[a-wA-W0-9_]+\b"
        tok = self.ply_token_to_py(t)
        loc = Location.from_token(self.filename, tok)
        if tok.string[0].isdigit() and not tok.string.isupper():
            msg = f"numbers have to be uppercase. Did you mean '{tok.string.upper()}'?"
        elif tok.string.startswith("_"):
            msg = f"numbers cannot start with an underscore. Did you mean '{tok.string.lstrip('_')}'?"
        elif not tok.string[0].isdigit() and not tok.string.islower():
            msg = f"names have to be lowercase. Did you mean '{tok.string.lower()}'?"
        elif not tok.string.isupper() and not tok.string.islower():
            # XXX: is it even reachable?
            msg = "numbers have to be uppercase and names have to be lowercase"
        elif tok.string.endswith("_"):
            msg = f"numbers cannot end with an underscore. Did you mean '{tok.string.rstrip('_')}'?"
        else:
            msg = "invalid number or name"
        report_fatal_at(loc, "SyntaxError", msg, tok.line)

    def t_ANY_newline(self, t):
        r"\n+"
        t.lexer.lineno += t.value.count("\n")

    def t_INVALID_error(self, t):
        tok = self.ply_token_to_py(t)
        loc = Location.from_token(self.filename, tok)
        # point to just one character because error token goes to the end of the string
        loc = loc.without_end()
        msg = "illegal combination of characters"
        report_fatal_at(loc, "SyntaxError", msg, tok.line)

    def t_INITIAL_error(self, t):
        self.reset_ply(self.text, "INVALID")
        self.skip_ply_by(t.lexpos)
        for tok in self.ply_lexer:
            pass  # should error
        assert False, "error state passed without error"

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
