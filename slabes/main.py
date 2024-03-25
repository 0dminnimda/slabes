import sys
import argparse
import subprocess
import platform

from pathlib import Path
from dataclasses import dataclass

from .slabes_parser import parse
from .name_table import NameTable, fill_name_table_from_ast
from .eval import Ast2Eval
from . import eval as ev
from .codegen import GenerateC
from . import ast_nodes as ast
from . import errors


IS_ANDROID = "android" in platform.platform().lower()


@dataclass
class Config:
    in_path: str
    bin_path: Path
    c_path: Path

    source: str

    optimize: int = 0
    debug: bool = False
    memcheck: bool = False

    max_cc_errors: int = 3
    cc: str = "clang"


def parse_args(argv: list[str] = sys.argv) -> Config:
    argparser = argparse.ArgumentParser()
    argparser.add_argument("filename", help="Input file ('-' to use stdin)")
    argparser.add_argument("-c", nargs="?", default=None, help="Output c file")
    argparser.add_argument("-o", "--output", nargs="?", default=None, help="Output binary file")

    args = argparser.parse_args(argv[1:])

    input_file = args.filename
    if input_file == "" or input_file == "-":
        input_file = "<stdin>"
        text = sys.stdin.read()
    else:
        text = Path(input_file).read_text("utf-8")

    if isinstance(args.c, str):
        c_file = Path(args.c)
    else:
        c_file = Path(input_file).with_suffix(".c")

    if isinstance(args.output, str):
        bin_file = Path(args.output)
    else:
        bin_file = Path(input_file).with_suffix(".out")

    return Config(
        input_file, bin_file, c_file, text, 
    )


def run_cc(c_code: str, conf: Config) -> int:
    args = [conf.cc, "-x", "c", "-"]
    args += ["-o", str(conf.bin_path), "-std=c11"]
    args += [f"-O{conf.optimize}"]
    # args += ["-Wall", "-Wextra", "-Werror", "-pedantic"]

    if conf.cc.startswith("clang"):
        args.append(f"-ferror-limit={conf.max_cc_errors}")
    else:
        args.append(f"-fmax-errors={conf.max_cc_errors}")

    if conf.debug:
        args.append("-g")
    if conf.memcheck:
        sanitize = "-fsanitize=address"
        if not IS_ANDROID:
            sanitize += ",undefined"
            if platform.system() != "Windows":
                sanitize += ",vptr"
        args.append(sanitize)

    print(" ".join(args))
    result = subprocess.run(args, input=c_code, capture_output=True, encoding="utf-8")
    if result.returncode:
        print(result.stderr)
    return result.returncode


def main(argv: list[str] = sys.argv) -> None:
    conf = parse_args(argv)

    tree = parse(conf.source, conf.in_path)

    evalue = Ast2Eval().transform(conf.source, tree, conf.in_path)
    assert isinstance(evalue, ev.Module), "got non-module evalue after ast transformation"

    errors.report_collected()

    evalue.evaluate(ev.BUILTIN_CONTEXT)

    c_code = GenerateC().generate(conf.source, evalue, conf.in_path)

    # print(ast.dump(tree, indent=4))
    # print(evalue)

    conf.c_path.write_text(c_code, "utf-8")

    exit(run_cc(c_code, conf))
