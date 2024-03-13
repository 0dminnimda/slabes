from __future__ import annotations
from dataclasses import dataclass, field

from . import ast_nodes as ast


@dataclass(frozen=True)
class Type:
    pass


@dataclass(frozen=True)
class IntType(Type):
    kind: ast.NumbeType
    signed: bool = field(default=False)


@dataclass(frozen=True)
class ModuleType(Type):
    pass


MODULE_T = ModuleType()


@dataclass(frozen=True)
class FunctionType(Type):
    pass


FUNCTION_T = FunctionType()
