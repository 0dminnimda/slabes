from __future__ import annotations

from dataclasses import dataclass, field
from typing import NoReturn

from .location import Location


@dataclass
class CompilerError(Exception):
    loc: Location
    error_name: str
    message: str
    line: str | None = field(default=None, repr=False)

    def __str__(self):
        result = f'Error in file "{self.loc.filepath}", line {self.loc.lineno}, column {self.loc.col_offset}\n\n'
        result += self.point_to_line()
        result += f"{self.error_name}: {self.message}"
        return result

    def point_to_line(self, prefix: str = " " * 2) -> str:
        if self.line is not None:
            result = prefix + self.line + "\n"
            result += prefix + self.loc.first_line_pointer(self.line) + "\n"
            return result
        return prefix + f"<could not get the line '{self.loc}'>\n\n"


_reported = []


def report_at(
    loc: Location,
    error_name: str,
    message: str,
    line: str | None = None,
):
    _reported.append(CompilerError(loc, error_name, message, line))


def report_collected(separator: str = "\n" + "="*80 + "\n"):
    if not _reported:
        return

    for i, error in enumerate(_reported):
        if i:
            print(separator)
        print(str(error))
    _reported.clear()

    exit(1)


def report_fatal_at(
    loc: Location,
    error_name: str,
    message: str,
    line: str | None = None,
) -> NoReturn:
    print(str(CompilerError(loc, error_name, message, line)))
    exit(1)


SyntaxError = "SyntaxError"
