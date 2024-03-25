from __future__ import annotations
from dataclasses import dataclass, field
from contextlib import contextmanager

from . import ast_nodes as ast
from .name_table import NameTable, fill_name_table_from_ast, lookup_origin
from . import types as ts
from . import errors
from .errors import report_at, report_fatal_at
from .location import Location
from .parser_base import DEFAULT_FILENAME


@dataclass
class Eval:
    loc: Location = field(repr=False)
    _evaluated: Value | None = field(default=None, init=False)

    def init(self, context: ScopeContext) -> None:
        raise NotImplementedError

    def raw_eval(self, context: ScopeContext) -> Value:
        raise NotImplementedError

    def evaluate(self, context: ScopeContext) -> Value:
        if self.evaluated is None:
            res = self.raw_eval(context)
            self.evaluated = res
        return self.evaluated

    @property
    def evaluated(self):
        assert self._evaluated is not None
        return self._evaluated

    @evaluated.setter
    def evaluated(self, value):
        self._evaluated = value


@dataclass
class Value(Eval):
    type: ts.Type = field(kw_only=True)

    def init(self, context: ScopeContext) -> None:
        pass

    def raw_eval(self, context: ScopeContext) -> Value:
        return self


@dataclass
class ScopeContext(NameTable):
    name_to_value: dict[str, Value] = field(default_factory=dict, kw_only=True)

    def set_name_value(self, name: str, value: Value, loc: Location) -> None:
        have = self.name_to_value.get(name)
        if have is None:
            self.name_to_value[name] = value
        else:
            if have.type != value.type:
                report_at(
                    loc,
                    errors.TypeError,
                    f"declared type '{have.type}' does not match assigned type '{value.type}'"
                )

    def get_name_value(self, name: str, loc: Location) -> Value:
        have = self.name_to_value.get(name)
        if have is None:
            report_fatal_at(
                loc,
                errors.NameError,
                f"name '{name}' is not defined"
            )
        else:
            return have


# @dataclass
# class ConstantInt(Eval):
#     value: int


def lookup_name(context: ScopeContext, name: str, loc: Location) -> Value:
    origin = lookup_origin(context, name)
    if origin is None:
        report_fatal_at(
            loc,
            errors.NameError,
            f"name '{name}' is not defined"
        )
    else:
        return origin.get_name_value(name, loc)


@dataclass
class Assign(Eval):
    names: list[str]
    value: Eval

    def raw_eval(self, context: ScopeContext) -> Value:
        value = self.value.evaluate(context)
        for name in self.names:
            origin = lookup_origin(context, name) or context
            origin.set_name_value(name, value, self.loc)
        return value


@dataclass
class Call(Eval):
    name: str
    args: list[Eval]

    def raw_eval(self, context: ScopeContext) -> Value:
        func = lookup_name(context, self.name, self.loc)
        if not isinstance(func, Function):
            report_fatal_at(
                self.loc,
                errors.TypeError,
                f"call operation expected functoin type, got '{func.type}'"
            )
        return Int(self.loc, 0, type=ts.IntType(ast.NumberType.TINY))


@dataclass
class Name(Eval):
    value: str

    def raw_eval(self, context: ScopeContext) -> Value:
        return lookup_name(context, self.value, self.loc)


@dataclass
class Int(Value):
    value: int
    type: ts.Type = field(kw_only=True)


@dataclass
class ScopeValue(Value, ScopeContext):
    body: list[Eval] = field(default_factory=list, kw_only=True)

    def raw_eval(self, context: ScopeContext) -> Value:
        for it in self.body:
            it.evaluate(context)
        return self


@dataclass
class Module(ScopeValue):
    type: ts.Type = field(default=ts.MODULE_T, init=False)


@dataclass
class Function(ScopeValue):
    name: str

    type: ts.Type = field(default=ts.FUNCTION_T, init=False)


@dataclass
class Ast2Eval(ast.Visitor):
    _filepath: str = field(default=DEFAULT_FILENAME)
    _lines: list[str] = field(default_factory=list)

    scope: ScopeValue = field(init=False)

    def visit(self, node):
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            report_fatal_at(
                self.loc(node),
                errors.SyntaxError,
                f"analysis node '{type(node).__name__}' is currently not supported for evalation",
                self._lines,
            )
        return visitor(node)

    def transform(
        self, code: str, tree: ast.AST, filepath: str = DEFAULT_FILENAME
    ) -> Eval:
        self._filepath = filepath
        self._lines = code.splitlines()
        return self.visit(tree)

    def loc(self, node: ast.AST) -> Location:
        return Location.from_ast(self._filepath, node)

    @contextmanager
    def new_scope(self, new: ScopeValue):
        old = getattr(self, "scope" , None)
        self.scope = new
        try:
            yield self.scope
        finally:
            if old is not None:
                self.scope = old

    def handle_body(self, body):
        for it in body:
            res = self.visit(it)
            if res is not None:
                self.scope.body.append(res)

    def visit_Module(self, node: ast.Module):
        loc = self.loc(node)

        mod = Module(loc)
        fill_name_table_from_ast(mod, node)

        with self.new_scope(mod):
            self.handle_body(node.body)

        return mod

    def visit_SingleExpression(self, node: ast.SingleExpression):
        if isinstance(node.body, ast.Call):
            value = self.visit(node.body)
        else:
            self.visit(node.body)
            return None
        return value

        self.scope.body.append(value)

    def visit_NumericLiteral(
        self, node: ast.NumericLiteral, kind: ast.NumberType = ast.NumberType.BIG
    ):
        signed = node.signedness is not ast.NumericLiteral.Signedness.UNSIGNED
        return Int(self.loc(node), node.value, type=ts.IntType(kind, signed))

    def visit_NumberDeclaration(self, node: ast.NumberDeclaration):
        loc = self.loc(node)
        lit = self.visit_NumericLiteral(node.value, node.type.type)
        names = []
        for name in node.names:
            self.scope.set_name_value(name.value, lit, self.loc(name))
            names.append(name.value)
        res = Assign(loc, names, self.visit(node.value))
        return res

    def visit_Function(self, node: ast.Function):
        loc = self.loc(node)

        func = Function(loc, node.name)
        fill_name_table_from_ast(func, node)
        func.outer = self.scope

        with self.new_scope(func):
            self.handle_body(node.body)

        return func

    def visit_Call(self, node: ast.Call):
        loc = self.loc(node)

        return Call(loc, node.name.value, [self.visit(it) for it in node.args])

    def visit_Name(self, node: ast.Name):
        loc = self.loc(node)

        return Name(loc, node.value)
