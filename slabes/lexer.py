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
        self.lines = text.splitlines()
        self.cumlen = [0] + list(accumulate((len(it) + 1 for it in self.lines)))
        self.filename = filename
        self.ply_lexer.input(text)


    token_name_to_type = {
        "NAME": token.NAME,
        "NUMBER": token.NUMBER,
        "COMMENT": token.COMMENT,
    }


    tokens = list(token_name_to_type.keys())


    literals = [",", ".", "=", "+", "-", "*", "/", "(", ")"]


    t_NAME = r"[a-z_][a-z0-9_]*"
    t_NUMBER = r"[A-W0-9_]+"

    t_COMMENT = r"\#.*"
    t_ignore = " \t"





    def t_newline(self, t):
        r"\n+"
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        tok = self.ply_token_to_py(t)
        loc = Location.from_token(self.filename, tok)
        # point to just one character because error token goes to the end of the string
        loc = loc.without_end()
        msg = "illegal combination of characters"
        report_fatal_at(loc, "SyntaxError", msg, tok.line)

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
    yield TokenInfo(token.ENDMARKER, "", (len(_lexer.lines) + 1, 0), (len(_lexer.lines) + 1, 0), "")
