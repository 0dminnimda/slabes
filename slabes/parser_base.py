import sys
import time
import token
import typing
import argparse
import traceback

from . import ast_nodes as ast

from pegen.parser import Parser, memoize
from pegen.tokenizer import Tokenizer
from pprint import pprint
from .lexer import lex, Keywords
from .errors import report_fatal_at
from .location import Location


DEFAULT_FILENAME = "<unknown>"


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
                "SyntaxError",
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

    @memoize
    def SMALL(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.SMALL.value:
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
        tokengen = lex(file.read())
        tokenizer = Tokenizer(tokengen, verbose=verbose_tokenizer)
        parser = parser_class(tokenizer, verbose=verbose_parser)
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

    if not args.quiet:
        pprint(tree)

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
