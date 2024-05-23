from __future__ import annotations

from dataclasses import dataclass, field
from contextlib import contextmanager
from typing import ClassVar, cast

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

    def compare_operation(self, op: ast.CmpOp, rhs: Value, reversed: bool) -> Value | None:
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
    targets: list[Eval]
    value: Eval

    def raw_eval(self, context: ScopeContext) -> Value:
        is_value = isinstance(self.value, Value)
        # Allow for recursive functions to find themselves in the outer scope
        if is_value:
            value = cast(Value, self.value)
        else:
            value = self.value.evaluate(context)

        for target in self.targets:
            if isinstance(target, Name):
                name = target.value
                origin = lookup_origin(context, name) or context
                origin.set_name_value(name, value, self.loc)
            else:
                assert isinstance(target, SubscriptOperation), f"assignment not to name or subscript is not supported, got {type(target)}"
                target.evaluate(context)

        if is_value:
            self.value.evaluate(context)

        return value


@dataclass
class Call(Eval):
    operand: Eval
    args: list[Eval]

    def raw_eval(self, context: ScopeContext) -> Value:
        func = self.operand.evaluate(context)
        if not isinstance(func, Function):
            report_fatal_at(
                self.loc,
                errors.TypeError,
                f"call operation expected function type, got '{func.type}'"
            )
        args = [arg.evaluate(context) for arg in self.args]
        func.check_args(args, self.loc)
        return func.return_value


@dataclass
class Return(Eval):
    evalue: Eval

    def raw_eval(self, context: ScopeContext) -> Value:
        if not isinstance(context, Function):
            report_fatal_at(
                self.loc,
                errors.TypeError,
                f"return can be used only inside function, not '{type(context).__name__}'"
            )

        value = self.evalue.evaluate(context)
        conv = value.convert_to(context.return_value)
        if conv is None:
            report_fatal_at(
                self.loc,
                errors.TypeError,
                f"expression type '{value.type}' does not match return type '{context.return_value.type}'"
            )
        return conv


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
class CompareOperation(Eval):
    operand: Eval
    ops: list[ast.CmpOp]
    operands: list[Eval]

    def raw_eval(self, context: ScopeContext) -> Value:
        lhs_e = self.operand
        lhs = lhs_e.evaluate(context)
        for op, rhs_e in zip(self.ops, self.operands):
            rhs = rhs_e.evaluate(context)

            res = lhs.compare_operation(op, rhs, False)
            if res is None:
                res = rhs.compare_operation(op, lhs, True)
            if res is None:
                report_fatal_at(
                    lhs_e.loc.merge(lhs_e.loc),
                    errors.TypeError,
                    f"compare operation '{op}' not supported for '{lhs.type}' and '{rhs.type}'"
                )

            lhs_e = rhs_e
            lhs = rhs

        return res


@dataclass
class SubscriptOperation(Eval):
    value: Eval
    index1: Eval
    index2: Eval

    def raw_eval(self, context: ScopeContext) -> Value:
        value = self.value.evaluate(context)
        if not isinstance(value, Matrix):
            report_fatal_at(
                self.loc,
                errors.TypeError,
                f"subscript is supported only for Matrix, not {value.type}"
            )

        index_self = Int(self.loc, 0, type=value.type.index_type)
        index1 = self.index1.evaluate(context)
        index2 = self.index2.evaluate(context)
        for index in [index1, index2]:
            if index.convert_to(index_self) is None:
                report_fatal_at(
                    self.loc,
                    errors.TypeError,
                    f"cannot use {index.type} as index (cannot convert to {index_self.type})"
                )

        return Int(self.loc, 0, type=value.type.item_type)


@dataclass
class Name(Eval):
    value: str

    def raw_eval(self, context: ScopeContext) -> Value:
        return lookup_name(context, self.value, self.loc)


@dataclass
class Condition(Eval):
    test: Eval
    body: list[Eval]

    def raw_eval(self, context: ScopeContext) -> Value:
        test = self.test.evaluate(context)

        for stmt in self.body:
            stmt.evaluate(context)

        return test


@dataclass
class Loop(Eval):
    test: Eval
    body: list[Eval]

    def raw_eval(self, context: ScopeContext) -> Value:
        test = self.test.evaluate(context)

        for stmt in self.body:
            stmt.evaluate(context)

        return test


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

    def compare_operation(self, op: ast.BinOp, rhs: Value, reversed: bool) -> Value | None:
        if isinstance(rhs, Int):
            return Int(self.loc, 0, type=ts.IntType(ast.NumberType.TINY))
        return None


@dataclass
class Matrix(Value):
    value: int
    type: ts.MatrixType = field(kw_only=True)

    def convert_to(self, other: Value) -> Value | None:
        if isinstance(other.type, type(self.type)) and self.type.item_type == other.type.item_type:
            return Matrix(self.loc, self.value, type=other.type)
        return None

    # def binary_operation(self, op: ast.BinOp, rhs: Value, reversed: bool) -> Value | None:
    #     if isinstance(rhs, Matrix):
    #         rhs.
    #         kind = max(self.type.kind, rhs.type.kind)
    #         return Matrix(self.loc, 0, type=ts.IntType(kind))
    #     return None

    def compare_operation(self, op: ast.BinOp, rhs: Value, reversed: bool) -> Value | None:
        if isinstance(rhs, Matrix):
            return Int(self.loc, 0, type=ts.IntType(ast.NumberType.TINY))
        return None


@dataclass
class ScopeValue(Value, ScopeContext):
    body: list[Eval] = field(default_factory=list, kw_only=True, repr=False)

    def raw_eval(self, context: ScopeContext) -> Value:
        for it in self.body:
            it.evaluate(self)
        return self


@dataclass
class Module(ScopeValue):
    type: ts.Type = field(default=ts.MODULE_T, init=False)


FunctionArgs = dict[str, Value] | None


@dataclass
class Function(ScopeValue):
    name: str
    args: FunctionArgs  # None is to disable argument checking & evaluation
    return_value: Value

    type: ts.Type = field(default=ts.FUNCTION_T, init=False)

    def check_args(self, args: list[Value], loc: Location) -> None:
        if self.args is None:
            return

        if len(args)!= len(self.args):
            report_fatal_at(
                loc,
                errors.TypeError,
                f"function '{self.name}' expected {len(self.args)} arguments, got {len(args)}"
            )
        for (name, arg), got in zip(self.args.items(), args):
            if got.convert_to(arg) is None:
                report_fatal_at(
                    loc,
                    errors.TypeError,
                    f"function '{self.name}' expected argument '{name}' of type '{arg.type}', got '{got.type}'"
                )

    def raw_eval(self, context: ScopeContext) -> Value:
        if self.args is not None:
            for name, arg in self.args.items():
                self.set_name_value(name, arg, BuiltinLoc)
        return super().raw_eval(context)


@dataclass
class FuncPrint(Function):
    name: str = field(default="print", init=False)
    args: ClassVar[FunctionArgs] = None
    return_value: Value = field(default_factory=lambda: Int(BuiltinLoc, 0, type=ts.IntType(ast.NumberType.TINY)), init=False)


@dataclass
class FuncAssert(Function):
    name: str = field(default="__assert", init=False)
    args: ClassVar[FunctionArgs] = None
    return_value: Value = field(default_factory=lambda: Int(BuiltinLoc, 0, type=ts.IntType(ast.NumberType.TINY)), init=False)


@dataclass
class FuncGenerateMaze(Function):
    name: str = field(default="__generate_maze", init=False)
    args: ClassVar[FunctionArgs] = {}
    return_value: Value = field(default_factory=lambda: Int(BuiltinLoc, 0, type=ts.IntType(ast.NumberType.TINY)), init=False)


@dataclass
class RobotCommandGo(Function):
    name: str = field(default="__robot_command_go", init=False)
    args: ClassVar[FunctionArgs] = {}
    return_value: Value = field(default_factory=lambda: Int(BuiltinLoc, 0, type=ts.IntType(ast.NumberType.TINY)), init=False)


@dataclass
class RobotCommandRL(Function):
    name: str = field(default="__robot_command_rl", init=False)
    args: ClassVar[FunctionArgs] = {}
    return_value: Value = field(default_factory=lambda: Int(BuiltinLoc, 0, type=ts.IntType(ast.NumberType.TINY)), init=False)


@dataclass
class RobotCommandRR(Function):
    name: str = field(default="__robot_command_rr", init=False)
    args: ClassVar[FunctionArgs] = {}
    return_value: Value = field(default_factory=lambda: Int(BuiltinLoc, 0, type=ts.IntType(ast.NumberType.TINY)), init=False)


@dataclass
class RobotCommandSonar(Function):
    name: str = field(default="__robot_command_sonar", init=False)
    args: ClassVar[FunctionArgs] = {}
    return_value: Value = field(default_factory=lambda: Int(BuiltinLoc, 0, type=ts.IntType(ast.NumberType.TINY)), init=False)


@dataclass
class RobotCommandCompass(Function):
    name: str = field(default="__robot_command_compass", init=False)
    args: ClassVar[FunctionArgs] = {}
    return_value: Value = field(default_factory=lambda: Int(BuiltinLoc, 0, type=ts.IntType(ast.NumberType.TINY)), init=False)


BUILTINS = {
    "print": FuncPrint(BuiltinLoc),
    "assert": FuncAssert(BuiltinLoc),
    "generate_maze": FuncGenerateMaze(BuiltinLoc),
    "__robot_command_go": RobotCommandGo(BuiltinLoc),
    "__robot_command_rl": RobotCommandRL(BuiltinLoc),
    "__robot_command_rr": RobotCommandRR(BuiltinLoc),
    "__robot_command_sonar": RobotCommandSonar(BuiltinLoc),
    "__robot_command_compass": RobotCommandCompass(BuiltinLoc),
}


def make_builtin_context():
    context = ScopeContext(outer=None)
    for name in BUILTINS.keys():
        context.names[name]
    for name, value in BUILTINS.items():
        Assign(BuiltinLoc, [Name(BuiltinLoc, name)], value).evaluate(context)
    return context


BUILTIN_CONTEXT = make_builtin_context()


@dataclass
class Ast2Eval(ast.Visitor):
    _filepath: str = field(default=DEFAULT_FILENAME)
    _lines: list[str] = field(default_factory=list)

    scope: ScopeValue = field(init=False)
    current_body: list[Eval] = field(init=False)

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

    @contextmanager
    def new_body(self, new: list[Eval]):
        old = getattr(self, "current_body" , None)
        self.current_body = new
        try:
            yield self.current_body
        finally:
            if old is not None:
                self.current_body = old

    def handle_body(self, body):
        for it in body:
            res = self.visit(it)
            if res is None:
                continue
            self.current_body.append(res)

    def visit_Module(self, node: ast.Module):
        loc = self.loc(node)

        mod = Module(loc)
        fill_name_table_from_ast(mod, node)
        mod.outer = BUILTIN_CONTEXT

        with self.new_scope(mod), self.new_body(mod.body):
            self.handle_body(node.body)

        return mod

    def visit_SingleExpression(self, node: ast.SingleExpression):
        return self.visit(node.body)

        self.current_body.append(value)

    def visit_NumericLiteral(
        self, node: ast.NumericLiteral, kind: ast.NumberType = ast.NumberType.BIG
    ):
        signed = node.signedness is not ast.Signedness.POSITIVE
        value = node.value
        if node.signedness is ast.Signedness.NEGATIVE:
            value = -value
        return Int(self.loc(node), value, type=ts.IntType(kind, signed))

    def visit_NumberDeclaration(self, node: ast.NumberDeclaration):
        loc = self.loc(node)
        lit = self.visit_NumericLiteral(node.value, node.type.type)
        targets = []
        for name in node.names:
            targets.append(self.visit(name))
        self.current_body.append(Assign(loc, targets, lit))

    def visit_ArrayDeclaration(self, node: ast.ArrayDeclaration):
        loc = self.loc(node)
        lit = self.visit_NumericLiteral(node.value, node.element_type.type)
        item_type = lit.type
        index_type = ts.IntType(node.size_type.type, ast.Signedness.POSITIVE)
        val = Matrix(loc, lit.value, type=ts.MatrixType(item_type, index_type))
        targets = []
        for name in node.names:
            targets.append(self.visit(name))
        self.current_body.append(Assign(loc, targets, val))

    def visit_Assignment(self, node: ast.Assignment):
        loc = self.loc(node)
        for assign in node.parts:
            targets = []
            value = self.visit(assign.value)
            for target in assign.targets:
                targets.append(self.visit(target))
            self.current_body.append(Assign(self.loc(assign), targets, value))

    def visit_NumberTypeRef(self, node: ast.NumberTypeRef):
        return ts.IntType(node.type)

    def visit_Function(self, node: ast.Function):
        loc = self.loc(node)

        return_type = self.visit(node.return_type)
        if isinstance(return_type, ts.IntType):
            ret = Int(loc, 0, type=return_type)
        else:
            report_fatal_at(
                loc,
                errors.TypeError,
                f"return type '{return_type}' is not supported"
            )

        args: FunctionArgs = {}
        for arg in node.args:
            arg_val = Int(loc, 0, type=self.visit(arg.type))
            args[arg.name.value] = arg_val

        func = Function(loc, node.name, args, ret)
        fill_name_table_from_ast(func, node)
        func.outer = self.scope

        self.current_body.append(Assign(loc, [Name(loc, node.name)], func))

        with self.new_scope(func), self.new_body(func.body):
            self.handle_body(node.body)

    def visit_Call(self, node: ast.Call):
        loc = self.loc(node)

        return Call(loc, self.visit(node.name), [self.visit(it) for it in node.args])

    def visit_Return(self, node: ast.Return):
        loc = self.loc(node)

        return Return(loc, self.visit(node.value))

    def visit_Name(self, node: ast.Name):
        loc = self.loc(node)

        return Name(loc, node.value)

    def visit_Check(self, node: ast.Check):
        loc = self.loc(node)

        body = []
        with self.new_body(body):
            self.handle_body(node.body)
        return Condition(loc, self.visit(node.test), body)

    def visit_Until(self, node: ast.Until):
        loc = self.loc(node)

        body = []
        with self.new_body(body):
            self.handle_body(node.body)
        return Loop(loc, self.visit(node.test), body)

    def visit_CompareOperation(self, node: ast.CompareOperation):
        loc = self.loc(node)

        operands = [self.visit(it) for it in node.operands]
        return CompareOperation(loc, self.visit(node.operand), node.ops, operands)

    def visit_BinaryOperation(self, node: ast.BinaryOperation):
        loc = self.loc(node)

        return BinaryOperation(loc, self.visit(node.lhs), node.op, self.visit(node.rhs))

    def visit_Subscript(self, node: ast.Subscript):
        loc = self.loc(node)

        return SubscriptOperation(loc, self.visit(node.value), self.visit(node.index1), self.visit(node.index2))

    def visit_RobotOperation(self, node: ast.RobotOperation):
        loc = self.loc(node)

        if node.op == ast.RobOp.MOVE:
            return Call(loc, BUILTINS["__robot_command_go"], [])
        if node.op == ast.RobOp.ROT_LEFT:
            return Call(loc, BUILTINS["__robot_command_rl"], [])
        if node.op == ast.RobOp.ROT_RIGHT:
            return Call(loc, BUILTINS["__robot_command_rr"], [])
        if node.op == ast.RobOp.SONAR:
            return Call(loc, BUILTINS["__robot_command_sonar"], [])
        if node.op == ast.RobOp.COMPASS:
            return Call(loc, BUILTINS["__robot_command_compass"], [])
        report_fatal_at(
            loc,
            errors.SyntaxError,
            f"robot operation '{node.op}' is not implemented for eval",
        )
