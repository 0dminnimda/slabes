from __future__ import annotations

from dataclasses import dataclass,field
from enum import Enum, auto


@dataclass
class AST:
    lineno: int = field(kw_only=True)
    col_offset: int = field(kw_only=True)
    end_lineno: int = field(kw_only=True)
    end_col_offset: int = field(kw_only=True)

    error_recovered: bool = field(default=False, kw_only=True)


@dataclass
class Module(AST):
    body: list[Statement]


@dataclass
class Statement(AST):
    pass


@dataclass
class Expression(AST):
    pass


@dataclass
class Type(AST):
    pass


@dataclass
class NumberType(Type):
    class Kind(Enum):
        TINY = auto()
        SMALL = auto()
        NORMAL = auto()
        BIG = auto()

    kind: Kind


@dataclass
class NumberLiteral(Expression):
    value: int

    # def __str__(self) -> str:
    #     return str(self)


@dataclass
class Name(Expression):
    value: str


@dataclass
class NumberDeclaration(Statement):
    type: NumberType
    names: list[Name]
    value: NumberLiteral
