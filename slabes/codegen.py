from __future__ import annotations
from dataclasses import dataclass, field
from contextlib import contextmanager

from . import ast_nodes as ast
from . import types as ts
from . import errors
from . import eval as ev
from .errors import report_fatal_at
from .location import Location
from .parser_base import DEFAULT_FILENAME


INT_TYPE_TEMPLATE = """
typedef /*ctype*/ slabes_type_/*name*/;

#define slabes_format_/*name*/ "/*format*/"

void assign_slabes_type_/*name*/(slabes_type_/*name*/ *var, slabes_type_/*name*/ value) {
    *var = value;
}
"""

INT_TYPE_INFO = [
    ("bool", "tiny", "%hh", False),
    ("char", "small", "%hh", True),
    ("short", "normal", "%h", True),
    ("short", "big", "%h", True),
]


def make_int_types():
    for ctype, name, format, can_be_unsigned in INT_TYPE_INFO:
        yield (
            INT_TYPE_TEMPLATE.replace("/*ctype*/", ctype)
            .replace("/*name*/", name)
            .replace("/*format*/", format + "i")
        )
        ctype = ("unsigned " if can_be_unsigned else "") + ctype
        yield (
            INT_TYPE_TEMPLATE.replace("/*ctype*/", ctype)
            .replace("/*name*/", "unsigned_" + name)
            .replace("/*format*/", format + "u")
        )


INT_TYPES = "\n".join(make_int_types())


INT_OP_TEMPLATE = """
slabes_type_/*name*/ slabes_op_/*op_name*/__/*name1*/__/*name2*/(slabes_type_/*name1*/ lhs, slabes_type_/*name2*/ rhs) {
    return lhs /*op*/ rhs;
}
"""

INT_OP_INFO = [
    ("+", "add"),
    ("-", "sub"),
    ("*", "mul"),
    ("/", "div"),
]


def make_int_ops():
    for i, (_, name1, *_) in enumerate(INT_TYPE_INFO):
        for j, (_, name2, *_) in enumerate(INT_TYPE_INFO):
            _, name = max((i, name1), (j, name2))

            for op, op_name in INT_OP_INFO:
                yield (
                    INT_OP_TEMPLATE.replace("/*name*/", name)
                    .replace("/*name1*/", name1)
                    .replace("/*name2*/", name2)
                    .replace("/*op*/", op)
                    .replace("/*op_name*/", op_name)
                )
                yield (
                    INT_OP_TEMPLATE.replace("/*name*/", "unsigned_" + name)
                    .replace("/*name1*/", "unsigned_" + name1)
                    .replace("/*name2*/", "unsigned_" + name2)
                    .replace("/*op*/", op)
                    .replace("/*op_name*/", op_name)
                )


INT_OPS = "\n".join(make_int_ops())


TEMPLATE = """
// GENERATED FROM /*file*/

#include <stdio.h>
#include <stdbool.h>

/*int-types*/
/*int-ops*/

/*decl*/

/*main*/

int main(int argc, char *argv[]) {
    printf("Starting...\\n");
    program_main();
    printf("Finishing...\\n");
    return 0;
}
"""

TEMPLATE = (
    TEMPLATE.replace("/*int-types*/", INT_TYPES)
    .replace("/*int-ops*/", INT_OPS)
)


PART_SEPARATOR: str = " "

MAIN_FUNCTION = "main"


@dataclass
class GenerateC:
    temporary_parts: list[str] = field(default_factory=list)
    main_parts: list[str] = field(default_factory=list)
    declaration_parts: list[str] = field(default_factory=list)

    current_temp: int = 0

    scope: ev.ScopeValue = field(init=False)

    _filepath: str = field(default=DEFAULT_FILENAME)
    _lines: list[str] = field(default_factory=list)

    def visit(self, node):
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            report_fatal_at(
                node.loc,
                errors.SyntaxError,
                f"analysis node '{type(node).__name__}' is currently not supported for codegen",
                self._lines,
            )
        return visitor(node)

    def merge_parts(self, parts: list[str]) -> str:
        return PART_SEPARATOR.join(parts).replace(";;", ";\n")

    def generate(
        self, code: str, eval: ev.Module, filepath: str = DEFAULT_FILENAME
    ) -> str:
        self._filepath = filepath
        self._lines = code.splitlines()
        self.visit(eval)
        assert (
            len(self.temporary_parts) == 0
        ), "temporary_parts should be saved before generation"
        return (
            TEMPLATE.replace("/*file*/", filepath)
            .replace("/*decl*/", self.merge_parts(self.declaration_parts))
            .replace("/*main*/", self.merge_parts(self.main_parts))
        )

    def collect(self, *args, **kwargs) -> str:
        previous = len(self.temporary_parts)
        self.put(*args, **kwargs)
        result = " ".join(self.temporary_parts[previous:])
        del self.temporary_parts[previous:]
        return result

    @contextmanager
    def isolate(self):
        old = self.temporary_parts, self.current_temp
        self.temporary_parts = []
        self.current_temp = 0

        yield self.temporary_parts

        self.temporary_parts, self.current_temp = old

    def save(self, parts: list[str], to_parts: list[str], front: bool = False) -> None:
        if front:
            to_parts[0:0] = parts
        else:
            to_parts.extend(parts)

    def put(self, *values, sep: str | None = None) -> None:
        """
        Each non-string value gets visited,
        then if the value or result of the visit is not None,
        it gets directly added to temporary_parts.
        If sep is not None it is added between the values.
        If the value is tuple, its items will be visited without adding sep in between.
        """

        first = True
        for value in values:
            if value is None:
                continue

            if not first and sep is not None:
                self.temporary_parts.append(sep)
            first = False

            if type(value) is not tuple:
                value = (value,)

            for item in value:
                if type(item) is not str:
                    item = self.visit(item)

                if item is not None:
                    self.temporary_parts.append(item)

    @contextmanager
    def new_scope(self, new: ev.ScopeValue):
        old = getattr(self, "scope", None)
        self.scope = new
        try:
            yield self.scope
        finally:
            if old is not None:
                self.scope = old

    def visit_str(self, string: str) -> str:
        return string

    def handle_scope(self, node: ev.ScopeValue):
        for name, value in node.name_to_value.items():
            self.put(self.type_name(value.type), self.var_name(name), ";;")

        with self.new_scope(node):
            for it in node.body:
                self.put(it, ";;")

    def visit_Module(self, node: ev.Module):
        self.scope = node

        with self.isolate() as program:
            self.handle_scope(node)

        self.save(program, self.main_parts)

    def function_name(self, name: str) -> str:
        return "slabes_func_" + name

    def visit_Function(self, node: ev.Function):
        if node.name == MAIN_FUNCTION:
            name = "program_main"
        else:
            name = self.function_name(node.name)

        with self.isolate() as decl:
            self.put("void", name, "()")

        with self.isolate() as defn:
            self.put("{\n")

            self.handle_scope(node)

            self.put("}\n")

        self.save(decl + [";\n"], self.declaration_parts)
        self.save(decl, self.main_parts)
        self.save(defn, self.main_parts)

    def type_name(self, node: ts.Type) -> str:
        return "slabes_type_" + node.name()

    def var_name(self, name: str) -> str:
        return "slabes_var_" + name

    def visit_Assign(self, node: ev.Assign):
        for name in node.names:
            tp = self.scope.name_to_value[name].type
            self.put(
                "assign_" + self.type_name(tp),
                "(&",
                self.var_name(name),
                ",",
                node.value,
                ");;",
            )

    def visit_Int(self, node: ev.Int):
        return str(node.value)

    def visit_Name(self, node: ev.Name):
        self.put(self.var_name(node.value))

    def visit_Call(self, node: ev.Call):
        if node.name == "print":
            self.handle_print(node)
        else:
            args = self.collect(*node.args, sep=",")
            self.put(self.function_name(node.name), "(", args, ")")

    def as_format(self, node: ts.Type) -> str:
        return "slabes_format_" + node.name()

    def handle_print(self, node: ev.Call):
        format = ""
        for arg in node.args:
            value = arg.evaluated
            format += self.as_format(value.type) + ' " " '
        format += r'"\n"'

        args = self.collect(format, *node.args, sep=",")
        self.put("printf(", args, ")")

    def bin_op_name(self, op: ast.BinOp) -> str:
        return "slabes_op_" + op.name.lower()

    def visit_BinaryOperation(self, node: ev.BinaryOperation):
        self.put(
            self.bin_op_name(node.op)
            + "__"
            + node.lhs.evaluated.type.name()
            + "__"
            + node.rhs.evaluated.type.name()
        )
        self.put("(", node.lhs, ",", node.rhs, ")")
