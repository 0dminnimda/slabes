from __future__ import annotations

from dataclasses import dataclass,field


@dataclass
class AST:
    lineno: int = field(kw_only=True)
    col_offset: int = field(kw_only=True)
    end_lineno: int = field(kw_only=True)
    end_col_offset: int = field(kw_only=True)


@dataclass
class Module(AST):
    body: list[stmt]


@dataclass
class stmt(AST):
    pass
