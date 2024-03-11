

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

/*decl*/

/*main*/

int main(int argc, char *argv[]) {
    printf("Starting...\\n");
    program_main(argc, argv);
    printf("Finishing...\\n");
    return 0;
}
"""


PART_SEPARATOR: str = " "


@dataclass
class GenerateC:
    temporary_parts: list[str] = field(default_factory=list)
    main_parts: list[str] = field(default_factory=list)
    declaration_parts: list[str] = field(default_factory=list)

    current_temp: int = 0

    _filepath: str = field(default=DEFAULT_FILENAME)
    _lines: list[str] = field(default_factory=list)

    def visit(self, node):
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            report_fatal_at(
                node.loc,
                errors.SyntaxError,
                f"analysis node '{type(node).__name__}' is currently not supported",
                self._lines
            )
        return visitor(node)

    def merge_parts(self, parts: list[str]) -> str:
        return PART_SEPARATOR.join(parts).replace(";;", ";\n")

    def generate(self, code: str, eval: ev.Module, filepath: str = DEFAULT_FILENAME) -> str:
        self._filepath = filepath
        self._lines = code.splitlines()
        self.visit(eval)
        assert (
            len(self.temporary_parts) == 0
        ), "temporary_parts should be saved before generation"
        return (
            TEMPLATE
            .replace("/*file*/", filepath)
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

    def visit_str(self, string: str) -> str:
        return string

    def visit_Module(self, node: ast.Module):
        with self.isolate() as program:
            self.put("/* program entry point */\n")
            self.put("void program_main(int argc, char *argv[]) {\n")

            for sub in node.body:
                self.put(sub)

            self.put("}\n")

        self.save(program, self.main_parts)
