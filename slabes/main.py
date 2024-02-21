import sys
import argparse

from pathlib import Path

from .errors import report_collected
from .slabes_parser import SlabesParser
from .name_table import NameTable, fill_name_table_from_ast
from . import ast_nodes as ast


def main(argv: list[str] = sys.argv) -> None:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("filename", help="Input file ('-' to use stdin)")

    args = argparser.parse_args(argv[1:])

    filename = args.filename
    if filename == "" or filename == "-":
        text = sys.stdin.read()
    else:
        text = Path(filename).read_text("utf-8")

    parser, tree = SlabesParser.parse_text(text, filename)

    report_collected()
    if tree is None:
        parser.report_syntax_error_at_last_token(filename, fatal=True)
        assert False, "unreachable"

    table = NameTable()
    fill_name_table_from_ast(table, tree)

    print(ast.dump(tree, indent=4))
    print(table)
