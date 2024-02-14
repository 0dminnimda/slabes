from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AST:
    pass


@dataclass
class Module(AST):
    body: list[stmt]


@dataclass
class stmt(AST):
    pass
