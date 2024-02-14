import token
from tokenize import TokenInfo
from itertools import accumulate

from .errors import report_fatal_at
from .location import Location


token_name_to_type = {
    "NAME": token.NAME,
    "NUMBER": token.NUMBER,
}


tokens = list(token_name_to_type.keys())

literals = ["=", "+", "-", "*", "/", "(", ")"]


t_NAME = r"[a-zA-Z_][a-zA-Z0-9_]*"
t_NUMBER = r"\d+"

t_ignore = " \t"


def t_newline(t):
    r"\n+"
    t.lexer.lineno += t.value.count("\n")


def t_error(t):
    tok = ply_token_to_py(t)
    loc = Location.from_token(current_filename, tok)
    msg = "Illegal combination of characters"
    report_fatal_at(loc, "SyntaxError", msg, tok.line)


from .ply import lex as ply_lex

lexer = ply_lex.lex()


def ply_token_to_py(tok):
    string = tok.value
    type = token_name_to_type.get(tok.type, token.OP)
    lineno = tok.lineno
    column_offset = tok.lexpos - cumlen[lineno - 1]
    end_column_offset = column_offset + len(string)
    line = lines[lineno - 1]
    return TokenInfo(
        type, string, (lineno, column_offset), (lineno, end_column_offset), line
    )


lines = []
cumlen = []
current_filename = ""


def lex(text: str, filename: str = "<unknown>"):
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    global lines, cumlen, current_filename
    current_filename = filename
    lines = text.splitlines()
    cumlen = [0] + list(accumulate((len(it) + 1 for it in lines)))

    lexer.input(text)

    for tok in lexer:
        yield ply_token_to_py(tok)
    yield TokenInfo(token.ENDMARKER, '', (len(lines) + 1, 0), (len(lines) + 1, 0), '')
