from __future__ import annotations
from dataclasses import dataclass, field

from . import ast_nodes as ast


@dataclass(frozen=True)
class Type:
    def name(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class IntType(Type):
    kind: ast.NumberType
    signed: bool = field(default=False)

    def name(self) -> str:
        res = ""
        if not self.signed:
            res += "unsigned_"

        if self.kind is ast.NumberType.TINY:
            res += "tiny"
        elif self.kind is ast.NumberType.SMALL:
            res += "small"
        elif self.kind is ast.NumberType.NORMAL:
            res += "normal"
        elif self.kind is ast.NumberType.BIG:
            res += "big"
        else:
            assert False, f"Unknown number kind: {self.kind}"

        return res


@dataclass(frozen=True)
class ModuleType(Type):
    def name(self) -> str:
        return "module"


MODULE_T = ModuleType()


@dataclass(frozen=True)
class FunctionType(Type):
    def name(self) -> str:
        return "function"


FUNCTION_T = FunctionType()
