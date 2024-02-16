import sys
import time
import token
import typing
import argparse
import traceback

from . import ast_nodes as ast
from . import errors

from pegen.parser import Parser, memoize
from pegen.tokenizer import Tokenizer
from tokenize import TokenInfo
from .lexer import lex, Keywords, _lexer
from .errors import report_fatal_at, report_at, report_collected
from .location import Location


DEFAULT_FILENAME = "<unknown>"


NUMBER_TYPE_KEWORDS = (
    Keywords.TINY,
    Keywords.SMALL,
    Keywords.NORMAL,
    Keywords.BIG,
)

NUMBEER_TYPES = tuple(k.value for k in NUMBER_TYPE_KEWORDS)


class ParserBase(Parser):
    filename: str

    def __init__(
        self,
        tokenizer: Tokenizer,
        *,
        filename: str = DEFAULT_FILENAME,
        verbose: bool = False,
    ) -> None:
        super().__init__(tokenizer, verbose=verbose)
        self.filename = filename

    def parse(self, rule: str):
        self.call_invalid_rules = False
        res = getattr(self, rule)()

        if res is None:
            self.call_invalid_rules = True

            # Reset the parser cache to be able to restart parsing from the
            # beginning.
            self._reset(0)
            self._cache.clear()

            res = getattr(self, rule)()

        if res is None:
            last_token = self._tokenizer.diagnose()

            print("DEBUG: last_token =", last_token)

            report_fatal_at(
                Location.from_token(self.filename, last_token),
                errors.SyntaxError,
                "invalid syntax",
                last_token.line,
            )

        return res

    @classmethod
    def parse_text(
        cls,
        text: str,
        filename: str = DEFAULT_FILENAME,
    ) -> ast.Module:
        tokenizer = Tokenizer(lex(text), path=filename)
        parser = cls(tokenizer, filename=filename)
        return parser.parse("start")

    def raise_syntax_error_at(
        self, message: str, node: ast.AST | TokenInfo, fatal: bool = False
    ):
        if isinstance(node, TokenInfo):
            start = node.start
            end = node.end
        else:
            start = node.lineno, node.col_offset
            end = node.end_lineno, node.end_col_offset

        self._raise_syntax_error(message, start, end, fatal=fatal)

    def raise_syntax_error_starting_from(
        self, message: str, start_node: ast.AST | TokenInfo, fatal: bool = False
    ):
        if isinstance(start_node, TokenInfo):
            start = start_node.start
        else:
            start = start_node.lineno, start_node.col_offset

        last_token = self._tokenizer.diagnose()

        self._raise_syntax_error(message, start, last_token.start, fatal=fatal)

    def _raise_syntax_error(
        self,
        message: str,
        start: tuple[int, int],
        end: tuple[int, int],
        line: str | None = None,
        fatal: bool = False,
    ):
        loc = Location(self.filename, *start, *end)
        if line is None:
            line = _lexer.lines[start[0] - 1]
        if fatal:
            report_fatal_at(loc, errors.SyntaxError, message, line)
        else:
            report_at(loc, errors.SyntaxError, message, line)

    def locs(self, tok: TokenInfo) -> dict[str, int]:
        return {
            "lineno": tok.start[0],
            "col_offset": tok.start[1],
            "end_lineno": tok.end[0],
            "end_col_offset": tok.end[1],
        }

    def make_name(self, name: TokenInfo, **loc) -> ast.Name:
        if name.type != token.NAME:
            self.raise_syntax_error_at(
                f"expected name, got keyword {token.tok_name[name.type]}",
                name,
            )
        return ast.Name(name.string, **loc)

    def make_number(self, tok: TokenInfo, sign: bool, **loc) -> ast.NumberLiteral:
        string = tok.string.replace("_", "")

        error_recovered = False
        if len(string) > 3:
            self.raise_syntax_error_at(
                "number literal too large to be represented by any integral type", tok
            )
            error_recovered = True

        return ast.NumberLiteral(
            (-1) ** (sign) * int(string, 32), **loc, error_recovered=error_recovered
        )

    def make_number_type(self, tok: TokenInfo, **loc) -> ast.NumberType:
        if tok.type == Keywords.TINY.value:
            return ast.NumberType(ast.NumberType.Kind.TINY, **loc)
        if tok.type == Keywords.SMALL.value:
            return ast.NumberType(ast.NumberType.Kind.SMALL, **loc)
        if tok.type == Keywords.NORMAL.value:
            return ast.NumberType(ast.NumberType.Kind.NORMAL, **loc)
        if tok.type == Keywords.BIG.value:
            return ast.NumberType(ast.NumberType.Kind.BIG, **loc)

        self.raise_syntax_error_at(
            f"expected number type, got {token.tok_name[tok.type]}", tok
        )
        return ast.NumberType(ast.NumberType.Kind.NORMAL, **loc, error_recovered=True)

    def make_number_declaration(
        self,
        type: ast.NumberType,
        names: list[ast.Name],
        value: ast.NumberLiteral,
        **loc,
    ) -> ast.NumberDeclaration:
        return ast.NumberDeclaration(type, names, value, **loc)

    def make_array_declaration(
        self,
        elem_t: ast.NumberType,
        size_t: ast.NumberType,
        names: list[ast.Name],
        value: ast.NumberLiteral,
        **loc,
    ) -> ast.ArrayDeclaration:
        return ast.ArrayDeclaration(elem_t, size_t, names, value, **loc)

    @memoize
    def TINY(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.TINY.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def SMALL(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.SMALL.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def NORMAL(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.NORMAL.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def BIG(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.BIG.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def FIELD(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.FIELD.value:
            return self._tokenizer.getnext()
        return None


def parser_main(parser_class: typing.Type[ParserBase]) -> None:
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Print timing stats; repeat for more debug output",
    )
    argparser.add_argument(
        "-q", "--quiet", action="store_true", help="Don't print the parsed program"
    )
    argparser.add_argument("filename", help="Input file ('-' to use stdin)")

    args = argparser.parse_args()
    verbose = args.verbose
    verbose_tokenizer = verbose >= 3
    verbose_parser = verbose == 2 or verbose >= 4

    t0 = time.time()

    filename = args.filename
    if filename == "" or filename == "-":
        filename = "<stdin>"
        file = sys.stdin
    else:
        file = open(args.filename)
    try:
        tokengen = lex(file.read(), filename)
        tokenizer = Tokenizer(tokengen, verbose=verbose_tokenizer)
        parser = parser_class(tokenizer, filename=filename, verbose=verbose_parser)
        tree = parser.parse("start")
        try:
            if file.isatty():
                endpos = 0
            else:
                endpos = file.tell()
        except IOError:
            endpos = 0
    finally:
        if file is not sys.stdin:
            file.close()

    t1 = time.time()

    if not tree:
        err = parser.make_syntax_error(filename)
        traceback.print_exception(err.__class__, err, None)
        sys.exit(1)

    report_collected()

    if not args.quiet:
        print(ast.dump(tree, indent=4))

    if verbose:
        dt = t1 - t0
        diag = tokenizer.diagnose()
        nlines = diag.end[0]
        if diag.type == token.ENDMARKER:
            nlines -= 1
        print(f"Total time: {dt:.3f} sec; {nlines} lines", end="")
        if endpos:
            print(f" ({endpos} bytes)", end="")
        if dt:
            print(f"; {nlines / dt:.0f} lines/sec")
        else:
            print()
        print("Caches sizes:")
        print(f"  token array : {len(tokenizer._tokens):10}")
        print(f"        cache : {len(parser._cache):10}")
