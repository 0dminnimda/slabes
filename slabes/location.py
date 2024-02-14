from __future__ import annotations

from dataclasses import dataclass
from tokenize import TokenInfo


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

    def __str__(self) -> str:
        result = f"{self.filepath}:{self.lineno}:{self.col_offset}"
        if self.end_lineno is not None and self.end_col_offset is not None:
            result += f":{self.end_lineno}:{self.end_col_offset}"
        return result

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
