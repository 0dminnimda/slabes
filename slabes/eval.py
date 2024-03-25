from __future__ import annotations
from dataclasses import dataclass, field
from contextlib import contextmanager

from . import ast_nodes as ast
from .name_table import NameTable, fill_name_table_from_ast, lookup_origin
from . import types as ts
from . import errors
from .errors import report_at, report_fatal_at
from .location import Location, BuiltinLoc
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
        if self._evaluated is None:
            res = self.raw_eval(context)
            self._evaluated = res
        return self._evaluated

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

    def convert_to(self, other: Value) -> Value | None:
        if self.type == other.type:
            return self
        return None

    def binary_operation(self, op: ast.BinOp, rhs: Value, reversed: bool) -> Value | None:
        return None


@dataclass
class ScopeContext(NameTable):
    name_to_value: dict[str, Value] = field(default_factory=dict, kw_only=True)

    def set_name_value(self, name: str, value: Value, loc: Location) -> None:
        have = self.name_to_value.get(name)
        if have is None:
            self.name_to_value[name] = value
        else:
            converted = value.convert_to(have)
            if converted is None:
                report_at(
                    loc,
                    errors.TypeError,
                    f"declared type '{have.type}' does not match assigned type '{value.type}'"
                )
            else:
                self.name_to_value[name] = converted

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
                f"call operation expected function type, got '{func.type}'"
            )
        args = [arg.evaluate(context) for arg in self.args]
        return Int(self.loc, 0, type=ts.IntType(ast.NumberType.TINY))


@dataclass
class BinaryOperation(Eval):
    lhs: Eval
    op: ast.BinOp
    rhs: Eval

    def raw_eval(self, context: ScopeContext) -> Value:
        lhs = self.lhs.evaluate(context)
        rhs = self.rhs.evaluate(context)

        res = lhs.binary_operation(self.op, rhs, False)
        if res is None:
            res = rhs.binary_operation(self.op, lhs, True)
        if res is None:
            report_fatal_at(
                self.loc,
                errors.TypeError,
                f"binary operation '{self.op}' not supported for '{lhs.type}' and '{rhs.type}'"
            )

        return res


@dataclass
class Name(Eval):
    value: str

    def raw_eval(self, context: ScopeContext) -> Value:
        return lookup_name(context, self.value, self.loc)


@dataclass
class Int(Value):
    value: int
    type: ts.IntType = field(kw_only=True)

    def convert_to(self, other: Value) -> Value | None:
        if isinstance(other.type, type(self.type)):
            return Int(self.loc, self.value, type=other.type)
        return None

    def binary_operation(self, op: ast.BinOp, rhs: Value, reversed: bool) -> Value | None:
        if isinstance(rhs, Int):
            kind = max(self.type.kind, rhs.type.kind)
            return Int(self.loc, 0, type=ts.IntType(kind))
        return None


@dataclass
class ScopeValue(Value, ScopeContext):
    body: list[Eval] = field(default_factory=list, kw_only=True)

    def raw_eval(self, context: ScopeContext) -> Value:
        for it in self.body:
            it.evaluate(self)
        return self


@dataclass
class Module(ScopeValue):
    type: ts.Type = field(default=ts.MODULE_T, init=False)


@dataclass
class Function(ScopeValue):
    name: str

    type: ts.Type = field(default=ts.FUNCTION_T, init=False)


@dataclass
class FuncPrint(Function):
    name: str = field(default="print", init=False)


BUILTINS = {
    "print": FuncPrint(BuiltinLoc)
}


def make_builtin_context():
    context = ScopeContext(names=set(BUILTINS.keys()))
    for name, value in BUILTINS.items():
        Assign(BuiltinLoc, [name], value).evaluate(context)
    return context


BUILTIN_CONTEXT = make_builtin_context()


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
            if res is None:
                continue
            self.scope.body.append(res)

    def visit_Module(self, node: ast.Module):
        loc = self.loc(node)

        mod = Module(loc)
        fill_name_table_from_ast(mod, node)
        mod.outer = BUILTIN_CONTEXT

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
            names.append(name.value)
        self.scope.body.append(Assign(loc, names, lit))

    def visit_Assignment(self, node: ast.Assignment):
        loc = self.loc(node)
        for assign in node.parts:
            names = []
            value = self.visit(assign.value)
            for name in assign.targets:
                if isinstance(name, ast.Subscript):
                    report_fatal_at(
                        loc,
                        errors.SyntaxError,
                        "subscript assignment is not implemeented",
                        self._lines,
                    )
                names.append(name.value)
            self.scope.body.append(Assign(self.loc(assign), names, value))

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

    def visit_BinaryOperation(self, node: ast.BinaryOperation):
        loc = self.loc(node)

        return BinaryOperation(loc, self.visit(node.lhs), node.op, self.visit(node.rhs))
