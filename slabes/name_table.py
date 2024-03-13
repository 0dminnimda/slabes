from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, TypeVar, Generic

from . import ast_nodes as ast


@dataclass
class NameTable:
    """
    This structure is for anwering those questions:
    - Does this name exists here? 
    - Is it accessible?
    - Where did it come from?
    """

    outer: NameTable | None = field(default=None, kw_only=True)
    names: set[str] = field(default_factory=set, kw_only=True)  # Local names


NameTableT = TypeVar("NameTableT", bound=NameTable)


@dataclass
class NameTableVisitor(ast.Visitor, Generic[NameTableT]):
    table: NameTableT

    def declare_name(self, name: str) -> None:
        self.table.names.add(name)

    def visit_Function(self, node: ast.Function) -> None:
        self.declare_name(node.name)

    def visit_ArrayDeclaration(self, node: ast.ArrayDeclaration) -> None:
        for name in node.names:
            self.declare_name(name.value)

    def visit_NumberDeclaration(self, node: ast.NumberDeclaration) -> None:
        for name in node.names:
            self.declare_name(name.value)

    def visit_Argument(self, node: ast.Argument) -> None:
        self.declare_name(node.name.value)

    def visit_Check(self, node: ast.Check) -> None:
        pass

    def visit_Until(self, node: ast.Until) -> None:
        pass


def fill_name_table_from_ast(table: NameTableT, node: ast.AST) -> None:
    NameTableVisitor(table).visit(node)


def walk_up_name_tables(table: NameTableT | None) -> Iterable[NameTableT]:
    while table is not None:
        yield table
        table = table.outer


def lookup_origin(table: NameTableT | None, name: str) -> NameTableT | None:
    start = table
    for table in walk_up_name_tables(start):
        if name in table.names:
            return table

    return None
