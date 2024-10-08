from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import Any, Iterable


@dataclass
class AST:
    lineno: int = field(kw_only=True)
    col_offset: int = field(kw_only=True)
    end_lineno: int = field(kw_only=True)
    end_col_offset: int = field(kw_only=True)

    error_recovered: bool = field(default=False, kw_only=True)

    def attributes(self):
        yield "lineno", self.lineno
        yield "col_offset", self.col_offset
        yield "end_lineno", self.end_lineno
        yield "end_col_offset", self.end_col_offset
        yield "error_recovered", self.error_recovered

    def fields(self) -> Iterable[tuple[str, Any]]:
        # yield zero, children should add their own fields
        for _ in range(0):
            yield "", None


@dataclass
class Module(AST):
    body: list[Statement]

    def fields(self):
        yield from super().fields()
        yield "body", self.body


@dataclass
class Statement(AST):
    pass


@dataclass
class Expression(AST):
    pass


@dataclass
class TypeRef(AST):
    pass


class NumberType(IntEnum):
    TINY = auto()
    SMALL = auto()
    NORMAL = auto()
    BIG = auto()


@dataclass
class NumberTypeRef(TypeRef):
    type: NumberType

    def fields(self):
        yield from super().fields()
        yield "type", self.type


@dataclass
class NumericLiteral(Expression):
    class Signedness(Enum):
        POSITIVE = auto()
        NEGATIVE = auto()
        UNSIGNED = auto()

    value: int
    signedness: Signedness

    def fields(self):
        yield from super().fields()
        yield "value", self.value
        yield "signedness", self.signedness

    # def __str__(self) -> str:
    #     return str(self)

Signedness = NumericLiteral.Signedness


@dataclass
class Name(Expression):
    value: str

    def fields(self):
        yield from super().fields()
        yield "value", self.value


@dataclass
class Subscript(Expression):
    value: Name
    index1: Expression
    index2: Expression

    def fields(self):
        yield from super().fields()
        yield "value", self.value
        yield "index1", self.index1
        yield "index2", self.index2


@dataclass
class BasicAssignment(AST):
    targets: list[Name | Subscript]
    value: Expression

    def fields(self):
        yield from super().fields()
        yield "targets", self.targets
        yield "value", self.value


@dataclass
class Assignment(Expression):
    parts: list[BasicAssignment]

    def fields(self):
        yield from super().fields()
        yield "parts", self.parts


class RobOp(Enum):
    MOVE = auto()
    ROT_LEFT = auto()
    ROT_RIGHT = auto()
    SONAR = auto()
    COMPASS = auto()


@dataclass
class RobotOperation(Expression):
    op: RobOp

    def fields(self):
        yield from super().fields()
        yield "op", self.op


@dataclass
class SingleExpression(Statement):
    body: Expression

    def fields(self):
        yield from super().fields()
        yield "body", self.body


class BinOp(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()


@dataclass
class BinaryOperation(Expression):
    lhs: Expression
    op: BinOp
    rhs: Expression

    def fields(self):
        yield from super().fields()
        yield "lhs", self.lhs
        yield "op", self.op
        yield "rhs", self.rhs


class UnrOp(Enum):
    POS = auto()
    NEG = auto()


@dataclass
class UnaryOperation(Expression):
    op: UnrOp
    operand: Expression

    def fields(self):
        yield from super().fields()
        yield "op", self.op
        yield "operand", self.operand


class CmpOp(Enum):
    EQ = auto()
    NE = auto()
    LE = auto()
    GE = auto()


@dataclass
class CompareOperation(Expression):
    operand: Expression
    ops: list[CmpOp]
    operands: list[Expression]

    def fields(self):
        yield from super().fields()
        yield "operand", self.operand
        yield "ops", self.ops
        yield "operands", self.operands


@dataclass
class Call(Expression):
    name: Name
    args: list[Expression]

    def fields(self):
        yield from super().fields()
        yield "name", self.name
        yield "args", self.args


@dataclass
class NumberDeclaration(Statement):
    type: NumberTypeRef
    names: list[Name]
    value: NumericLiteral

    def fields(self):
        yield from super().fields()
        yield "type", self.type
        yield "names", self.names
        yield "value", self.value


@dataclass
class ArrayDeclaration(Statement):
    element_type: NumberTypeRef
    size_type: NumberTypeRef
    names: list[Name]
    value: NumericLiteral

    def fields(self):
        yield from super().fields()
        yield "element_type", self.element_type
        yield "size_type", self.size_type
        yield "names", self.names
        yield "value", self.value


@dataclass
class Until(Statement):
    test: Expression
    body: list[Statement]

    def fields(self):
        yield from super().fields()
        yield "test", self.test
        yield "body", self.body


@dataclass
class Check(Statement):
    test: Expression
    body: list[Statement]

    def fields(self):
        yield from super().fields()
        yield "test", self.test
        yield "body", self.body


@dataclass
class Argument(AST):
    type: NumberTypeRef
    name: Name

    def fields(self):
        yield from super().fields()
        yield "type", self.type
        yield "name", self.name


@dataclass
class Function(Statement):
    return_type: NumberTypeRef
    name: str
    args: list[Argument]
    body: list[Statement]

    def fields(self):
        yield from super().fields()
        yield "return_type", self.return_type
        yield "name", self.name
        yield "args", self.args
        yield "body", self.body


@dataclass
class Return(Statement):
    value: Expression

    def fields(self):
        yield from super().fields()
        yield "value", self.value


def dump(
    node: AST | list,
    annotate_fields: bool = True,
    include_attributes: bool = False,
    *,
    indent: int | str | None = None,
) -> str:
    """
    Return a formatted dump of the tree in node.  This is mainly useful for
    debugging purposes.  If annotate_fields is true (by default),
    the returned string will show the names and the values for fields.
    If annotate_fields is false, the result string will be more compact by
    omitting unambiguous field names.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    include_attributes can be set to true.  If indent is a non-negative
    integer or string, then the tree will be pretty-printed with that indent
    level. None (the default) selects the single line representation.
    """

    if not isinstance(node, (AST, list, tuple)):
        raise TypeError("expected AST, got %r" % node.__class__.__name__)

    if indent is not None and not isinstance(indent, str):
        good_indent = " " * indent
    else:
        good_indent = indent

    def _format(node, level: int) -> tuple[str, bool]:
        if isinstance(node, AST):
            if include_attributes:
                level += 1
            elif sum(1 for _ in node.fields()) >= 2:
                level += 1
        elif isinstance(node, (list, tuple)):
            if len(node) >= 2:
                level += 1

        if good_indent is not None:
            prefix = "\n" + good_indent * level
            postfix = "\n" + good_indent * (level - 1)
            sep = ",\n" + good_indent * level
        else:
            prefix = ""
            postfix = ""
            sep = ", "

        if isinstance(node, AST):
            args = []
            allsimple = True
            for name, value in node.fields():
                value, simple = _format(value, level)
                allsimple = allsimple and simple
                if annotate_fields:
                    args.append(f"{name}={value}")
                else:
                    args.append(value)
            if include_attributes:
                for name, value in node.attributes():
                    value, simple = _format(value, level)
                    allsimple = allsimple and simple
                    args.append(f"{name}={value}")
            if allsimple and len(args) <= 3:
                return f"{type(node).__name__}({', '.join(args)})", not args
            if len(args) == 1:
                return f"{type(node).__name__}({args[0]})", allsimple
            return f"{type(node).__name__}({prefix}{sep.join(args)}{postfix})", False
        elif isinstance(node, (list, tuple)):
            parens = "()" if isinstance(node, tuple) else "[]"

            args = []
            allsimple = True
            for value in node:
                value, simple = _format(value, level)
                allsimple = allsimple and simple
                args.append(value)

            if allsimple and len(args) <= 3:
                return f"{parens[0]}{', '.join(args)}{parens[1]}", not args
            if len(args) == 1:
                return f"{parens[0]}{args[0]}{parens[1]}", allsimple
            return f"{parens[0]}{prefix}{sep.join(args)}{postfix}{parens[1]}", False

        return repr(node), True

    return _format(node, 0)[0]


class Visitor:
    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        if not isinstance(node, AST):
            return

        for _, value in node.fields():
            if isinstance(value, (list, tuple)):
                for item in value:
                    self.visit(item)
            else:
                self.visit(value)

    def visit_list(self, value: list) -> None:
        for it in value:
            self.visit(it)

    def visit_tuple(self, value: tuple) -> None:
        for it in value:
            self.visit(it)
