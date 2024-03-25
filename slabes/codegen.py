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



TEMPLATE = """
// GENERATED FROM /*file*/

#include <stdio.h>
#include <stdbool.h>

#define make_int_type(ctype, name) \\
typedef ctype slabes_type_##name; \\
\\
void assign_slabes_type_##name(ctype *var, ctype value) { \\
    *var = value; \\
}

make_int_type(bool, unsigned_tiny)
make_int_type(bool, tiny)
make_int_type(char, unsigned_small)
make_int_type(char, small)
make_int_type(short, unsigned_normal)
make_int_type(short, normal)
make_int_type(short, unsigned_big)
make_int_type(short, big)

/*decl*/

/*main*/

int main(int argc, char *argv[]) {
    printf("Starting...\\n");
    program_main();
    printf("Finishing...\\n");
    return 0;
}
"""


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
            self.put(self.type_name(tp), self.var_name(name), ";;")
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

    def visit_Call(self, node: ev.Call):
        args = self.collect(*node.args, sep=",")
        if node.name == "print":
            self.handle_print(node)
        else:
            self.put(self.function_name(node.name), "(", args, ")")

    def as_format(self, node: ts.Type) -> str:
        return "slabes_format_" + node.name()

    def handle_print(self, node: ev.Call):
        format = ""
        for arg in node.args:
            value = arg.evaluated
            self.put(self.as_format(value.type))
            # self.put(self.function_name(node.name), "(", args, ")")
        format += "\n"

    def visit_Name(self, node: ev.Name):
        self.put(node.value)
