from __future__ import annotations

from dataclasses import dataclass
from tokenize import TokenInfo
from . import ast_nodes as ast


@dataclass(frozen=True)
class Location:
    filepath: str
    lineno: int
    col_offset: int
    end_lineno: int | None = None
    end_col_offset: int | None = None

    @classmethod
    def from_token(cls, filepath: str, token: TokenInfo) -> Location:
        lineno, offset = token.start
        end_lineno, end_offset = token.end
        return cls(
            filepath,
            lineno,
            offset,
            end_lineno,
            end_offset,
        )

    @classmethod
    def from_ast(cls, filepath: str, node: ast.AST) -> Location:
        return cls(
            filepath,
            node.lineno,
            node.col_offset,
            node.end_lineno,
            node.end_col_offset,
        )

    def merge(self, other: Location) -> Location:
        if self.filepath != other.filepath:
            raise ValueError("Locations do not share the same file")

        if self.lineno == other.lineno:
            lineno = self.lineno
            col_offset = min(self.col_offset, other.col_offset)
        else:
            if self.lineno < other.lineno:
                lineno = self.lineno
                col_offset = self.col_offset
            else:
                lineno = other.lineno
                col_offset = other.col_offset

        if self.end_lineno is None or other.end_lineno is None:
            if self.end_lineno is not None:
                end_lineno = self.end_lineno
                end_col_offset = self.end_col_offset
            elif other.end_lineno is not None:
                end_lineno = other.end_lineno
                end_col_offset = other.end_col_offset
        elif self.end_lineno == other.end_lineno:
            end_lineno = self.end_lineno
            if self.end_col_offset is None and other.end_col_offset is None:
                end_col_offset = None
            elif other.end_col_offset is None:
                end_col_offset = self.end_col_offset
            elif self.end_col_offset is None:
                end_col_offset = other.end_col_offset
            else:
                end_col_offset = max(self.end_col_offset, other.end_col_offset)
        else:
            if self.end_lineno > other.end_lineno:
                end_lineno = self.end_lineno
                end_col_offset = self.end_col_offset
            else:
                end_lineno = other.end_lineno
                end_col_offset = other.end_col_offset

        return Location(
            self.filepath,
            lineno,
            col_offset,
            end_lineno,
            end_col_offset,
        )

    def without_end(self) -> Location:
        return Location(
            self.filepath,
            self.lineno,
            self.col_offset,
            None,
            None,
        )

    def __str__(self) -> str:
        result = f"{self.filepath}:{self.lineno}:{self.col_offset}"
        if self.end_lineno is not None and self.end_col_offset is not None:
            result += f":{self.end_lineno}:{self.end_col_offset}"
        return result

    def get_exact_str_from_lines(self, lines: list[str]) -> str | None:
        if self.lineno > len(lines):
            return None
        return lines[self.lineno - 1][self.col_offset:self.end_col_offset]

    def first_line_end(self, line: str | None = None) -> int | None:
        # if the node is single line, use it's end
        if self.lineno == self.end_lineno:
            return self.end_col_offset

        # if the node is multiline then if possible
        # use the length of the first line as the end
        if line is not None and self.end_lineno is not None:
            return len(line)

        # otherwise the end is not known, use None
        return None

    def first_line_pointer(self, line: str | None = None) -> str:
        """Constructs a string with '^' characters to highlight
        a code segment within its first line."""

        start = self.col_offset
        end = self.first_line_end(line)
        if end is not None:
            return " " * start + "^" * (end - start)
        return " " * start + "^ "


BuiltinLoc = Location("<built-in>", -1, -1, -1, -1)
