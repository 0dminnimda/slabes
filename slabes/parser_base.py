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

    def report_syntax_error_at(
        self, message: str, node: ast.AST | TokenInfo, fatal: bool = False
    ):
        if isinstance(node, TokenInfo):
            start = node.start
            end = node.end
        else:
            start = node.lineno, node.col_offset
            end = node.end_lineno, node.end_col_offset

        self._report_syntax_error(message, start, end, fatal=fatal)

    def report_syntax_error_starting_from(
        self, message: str, start_node: ast.AST | TokenInfo, fatal: bool = False
    ):
        if isinstance(start_node, TokenInfo):
            start = start_node.start
        else:
            start = start_node.lineno, start_node.col_offset

        last_token = self._tokenizer.diagnose()

        self._report_syntax_error(message, start, last_token.start, fatal=fatal)

    def _report_syntax_error(
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

    def locs(self, node: ast.AST | TokenInfo) -> dict[str, int]:
        if isinstance(node, TokenInfo):
            return {
                "lineno": node.start[0],
                "col_offset": node.start[1],
                "end_lineno": node.end[0],
                "end_col_offset": node.end[1],
            }
        return {
            "lineno": node.lineno,
            "col_offset": node.col_offset,
            "end_lineno": node.end_lineno,
            "end_col_offset": node.end_col_offset,
        }

    def make_name(self, name: ast.AST | TokenInfo, **loc) -> ast.Name:
        if not isinstance(name, TokenInfo):
            return ast.Name("<invalid>", **loc, error_recovered=True)
        if name.type != token.NAME:
            self.report_syntax_error_at(
                f"expected name, got keyword {token.tok_name[name.type]}",
                name,
            )
        return ast.Name(name.string, **loc)

    def make_number(
        self, tok: TokenInfo, sign: TokenInfo | None, **loc
    ) -> ast.NumericLiteral:
        string = tok.string.replace("_", "")

        error_recovered = False
        if len(string) > 3:
            self.report_syntax_error_at(
                "number literal too large to be represented by any integral type", tok
            )
            error_recovered = True

        if sign is None:
            sign_multiple = 1
            signedness = ast.NumericLiteral.Signedness.UNSIGNED
        elif sign.string == "-":
            sign_multiple = -1
            signedness = ast.NumericLiteral.Signedness.NEGATIVE
        else:
            sign_multiple = 1
            signedness = ast.NumericLiteral.Signedness.POSITIVE

        return ast.NumericLiteral(
            sign_multiple * int(string, 32),
            signedness,
            **loc,
            error_recovered=error_recovered,
        )

    def make_number_type(self, tok: TokenInfo, **loc) -> ast.NumbeTypeRef:
        if tok.type == Keywords.TINY.value:
            return ast.NumbeTypeRef(ast.NumbeType.TINY, **loc)
        if tok.type == Keywords.SMALL.value:
            return ast.NumbeTypeRef(ast.NumbeType.SMALL, **loc)
        if tok.type == Keywords.NORMAL.value:
            return ast.NumbeTypeRef(ast.NumbeType.NORMAL, **loc)
        if tok.type == Keywords.BIG.value:
            return ast.NumbeTypeRef(ast.NumbeType.BIG, **loc)

        self.report_syntax_error_at(
            f"expected number type, got {token.tok_name[tok.type]}", tok
        )
        return ast.NumbeTypeRef(ast.NumbeType.NORMAL, **loc, error_recovered=True)

    def make_number_declaration(
        self,
        type: ast.NumbeTypeRef,
        names: list[ast.Name],
        value: ast.AST,
        **loc,
    ) -> ast.NumberDeclaration:
        if not isinstance(value, ast.NumericLiteral):
            self.report_syntax_error_at(
                "number can be initialized only with a constant number", value
            )
            value = ast.NumericLiteral(
                0,
                ast.NumericLiteral.Signedness.UNSIGNED,
                error_recovered=True,
                **self.locs(value),
            )
        return ast.NumberDeclaration(type, names, value, **loc)

    def make_array_declaration(
        self,
        elem_t: ast.NumbeTypeRef,
        size_t: ast.NumbeTypeRef,
        names: list[ast.Name],
        value: ast.AST,
        **loc,
    ) -> ast.ArrayDeclaration:
        if not isinstance(value, ast.NumericLiteral):
            self.report_syntax_error_at(
                "array can be initialized only with a constant number", value
            )
            value = ast.NumericLiteral(
                0,
                ast.NumericLiteral.Signedness.UNSIGNED,
                error_recovered=True,
                **self.locs(value),
            )
        return ast.ArrayDeclaration(elem_t, size_t, names, value, **loc)

    def make_subscript(
        self,
        name: ast.AST | TokenInfo,
        indices: list[ast.Expression],
        **loc,
    ):
        if not isinstance(name, ast.Name):
            self.report_syntax_error_at("subscript requires a name", name)
            return ast.Statement(**loc, error_recovered=True)
        if len(indices) != 2:
            self.report_syntax_error_at(
                f"subscript requires exactly two indices, got {len(indices)}",
                indices[-1] if indices else name,
            )
            return ast.Statement(**loc, error_recovered=True)
        return ast.Subscript(name, indices[0], indices[1], **loc)

    def is_assignment_target(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return True
        if isinstance(node, ast.Subscript):
            return True
        return False

    def _make_basic_assignment(
        self, to_left: bool, group: list[ast.Expression]
    ) -> ast.BasicAssignment | None:
        if to_left:
            targets = group[:-1][::-1]
            value = group[-1]
        else:
            targets = group[1:]
            value = group[0]

        for node in targets:
            if not self.is_assignment_target(node):
                self.report_syntax_error_at(
                    f"assignment to expression {type(node).__name__} not allowed", node
                )
                return None

        return ast.BasicAssignment(
            targets,  # type: ignore
            value,
            lineno=group[0].lineno,
            col_offset=group[0].col_offset,
            end_lineno=group[-1].end_lineno,
            end_col_offset=group[-1].end_col_offset,
        )

    def _producee_assignment_groups(
        self,
        curr_value: ast.Expression,
        pairs: list[tuple[TokenInfo, ast.Expression]],
    ):
        assert pairs, "cannot assign to/from nothing, pairs is empty"

        # group operands with the same op
        # so those are compressed just into one group
        # a << b << c
        # a >> b >> c
        group: list[ast.Expression] = []

        # let's use out imagination to create the path before
        # we need the loop to continue the first group
        prev_to_left = pairs[0][0].string == "<<"

        for op, next_value in pairs:
            to_left = op.string == "<<"

            group.append(curr_value)

            if prev_to_left == to_left:
                curr_value = next_value
                continue

            yield prev_to_left, group

            group = []

            # ... >> curent << ... - skip, ">>" takes presedance
            # ... << curent >> ... - copy to both
            if prev_to_left:
                group.append(curr_value)

            curr_value = next_value
            prev_to_left = to_left

        group.append(curr_value)
        yield prev_to_left, group

    def make_assignment(
        self,
        prev_value: ast.Expression,
        pairs: list[tuple[TokenInfo, ast.Expression]],
        **loc,
    ):
        error_recovered = False
        prev_bass = None
        basic_assigns = []
        for to_left, group in self._producee_assignment_groups(prev_value, pairs):
            # ignore groups that don't result is any operations
            if len(group) <= 1:
                continue

            bass = self._make_basic_assignment(to_left, group)
            if bass is not None:
                if prev_bass is not None and prev_bass.value is bass.value:
                    # merge basic assignments that share the same value
                    # a << b >> c  <===>  c << a << b
                    # a << b << c >> d >> e  <===>  e << d << b << a << c
                    prev_bass.targets += bass.targets
                else:
                    prev_bass = bass
                    basic_assigns.append(bass)
            else:
                # skip erroneous targets
                error_recovered = True

        return ast.Assignment(basic_assigns, **loc, error_recovered=error_recovered)

    def make_robot_op(self, tok: TokenInfo, **loc) -> ast.RobotOperation:
        if tok.type == Keywords.GO.value:
            return ast.RobotOperation(ast.RobOp.MOVE, **loc)
        if tok.type == Keywords.RL.value:
            return ast.RobotOperation(ast.RobOp.ROT_LEFT, **loc)
        if tok.type == Keywords.RR.value:
            return ast.RobotOperation(ast.RobOp.ROT_RIGHT, **loc)
        if tok.type == Keywords.SONAR.value:
            return ast.RobotOperation(ast.RobOp.SONAR, **loc)
        if tok.type == Keywords.COMPASS.value:
            return ast.RobotOperation(ast.RobOp.COMPASS, **loc)

        self.report_syntax_error_at(
            f"expected robot operation, got {token.tok_name[tok.type]}", tok, fatal=True
        )
        assert False, "unreachable"

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

    @memoize
    def BEGIN(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.BEGIN.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def END(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.END.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def UNTIL(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.UNTIL.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def DO(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.DO.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def CHECK(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.CHECK.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def GO(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.GO.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def RL(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.RL.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def RR(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.RR.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def SONAR(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.SONAR.value:
            return self._tokenizer.getnext()
        return None

    @memoize
    def COMPASS(self):
        tok = self._tokenizer.peek()
        if tok.type == Keywords.COMPASS.value:
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
