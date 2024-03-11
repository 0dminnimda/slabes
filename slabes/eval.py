from __future__ import annotations
from dataclasses import dataclass, field
from contextlib import contextmanager

from . import ast_nodes as ast
from .name_table import NameTable
from . import types as ts
from . import errors
from .errors import report_fatal_at
from .location import Location
from .parser_base import DEFAULT_FILENAME


@dataclass
class Eval:
    loc: Location = field(repr=False)

    def init(self, context: ScopeContext) -> None:
        raise NotImplementedError

    def eval(self, context: ScopeContext) -> Value:
        raise NotImplementedError


@dataclass
class Value(Eval):
    type: ts.Type = field(kw_only=True)

    def init(self, context: ScopeContext) -> None:
        pass

    def eval(self, context: ScopeContext) -> Value:
        return self


@dataclass
class ConstantInt(Eval):
    value: int


@dataclass
class Int(Value):
    value: int
    type: ts.Type = field(kw_only=True)


@dataclass
class Module(Value):
    # context: ScopeContext
    body: list[Eval]

    type: ts.Type = field(default=ts.MODULE_T, init=False)


@dataclass
class ScopeContext(NameTable):
    pass


@dataclass
class Ast2Eval(ast.Visitor):
    _filepath: str = field(default=DEFAULT_FILENAME)
    _lines: list[str] = field(default_factory=list)

    # context: ScopeContext

    block_evals: list[Eval] = field(default_factory=list)

    def visit(self, node):
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            report_fatal_at(
                self.loc(node),
                errors.SyntaxError,
                f"analysis node '{type(node).__name__}' is currently not supported",
                self._lines
            )
        return visitor(node)

    def transform(self, code: str, tree: ast.AST, filepath: str = DEFAULT_FILENAME) -> Eval:
        self._filepath = filepath
        self._lines = code.splitlines()
        return self.visit(tree)

    def loc(self, node: ast.AST) -> Location:
        return Location.from_ast(self._filepath, node)

    @contextmanager
    def change_evals(self, new_evals):
        old = self.block_evals
        self.block_evals = new_evals
        try:
            yield self.block_evals
        finally:
            self.block_evals = old

    def visit_Module(self, node: ast.Module):
        loc = self.loc(node)
        with self.change_evals([]) as body:
            self.generic_visit(node.body)
        return Module(loc, body)

    def visit_SingleExpression(self, node: ast.SingleExpression):
        if isinstance(node, ast.NumberDeclaration):
            value = self.visit(node)
        else:
            return

        self.block_evals.append(value)

    # def visit_NumericLiteral(self, node: ast.NumericLiteral):
    #     signed = node.signedness is not ast.NumericLiteral.Signedness.UNSIGNED
    #     ts.IntType(, signed)
    #     return Int(self.loc(node), node.value)
