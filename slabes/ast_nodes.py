from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


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

    def fields(self):
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
class Type(AST):
    pass


@dataclass
class CompoundExpression(Statement):
    body: list[Expression]

    def fields(self):
        yield from super().fields()
        yield "body", self.body


@dataclass
class NumberType(Type):
    class Kind(Enum):
        TINY = auto()
        SMALL = auto()
        NORMAL = auto()
        BIG = auto()

    kind: Kind

    def fields(self):
        yield from super().fields()
        yield "kind", self.kind


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


class BinaryKind(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    EQ = auto()
    NE = auto()
    LE = auto()
    GE = auto()


@dataclass
class BinaryOperation(Expression):
    lhs: Expression
    op: BinaryKind
    rhs: Expression

    def fields(self):
        yield from super().fields()
        yield "lhs", self.lhs
        yield "op", self.op
        yield "rhs", self.rhs


@dataclass
class NumberDeclaration(Statement):
    type: NumberType
    names: list[Name]
    value: NumericLiteral

    def fields(self):
        yield from super().fields()
        yield "type", self.type
        yield "names", self.names
        yield "value", self.value


@dataclass
class ArrayDeclaration(Statement):
    element_type: NumberType
    size_type: NumberType
    names: list[Name]
    value: NumericLiteral

    def fields(self):
        yield from super().fields()
        yield "element_type", self.element_type
        yield "size_type", self.size_type
        yield "names", self.names
        yield "value", self.value


def dump(
    node: AST | list,
    annotate_fields: bool = True,
    include_attributes: bool = False,
    *,
    indent: int | str | None = None,
    max_simple_length: int = 80,
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

    if not isinstance(node, (AST, list)):
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
        elif isinstance(node, list):
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
        sep2 = ", "

        if isinstance(node, AST):
            args = []
            all_one_line = True
            for name, value in node.fields():
                value, one_line = _format(value, level)
                all_one_line = all_one_line and one_line
                if annotate_fields:
                    args.append(f"{name}={value}")
                else:
                    args.append(value)
            if include_attributes:
                for name, value in node.attributes():
                    value, one_line = _format(value, level)
                    all_one_line = all_one_line and one_line
                    args.append(f"{name}={value}")

            not_too_long = (
                all_one_line and sum(len(x) for x in args) <= max_simple_length
            )
            if len(args) == 1 or not_too_long:
                return f"{type(node).__name__}({sep2.join(args)})", True
            return f"{type(node).__name__}({prefix}{sep.join(args)}{postfix})", False

        elif isinstance(node, list):
            args = []
            all_one_line = True
            for value in node:
                value, one_line = _format(value, level)
                all_one_line = all_one_line and one_line
                args.append(value)

            not_too_long = (
                all_one_line and sum(len(x) for x in args) <= max_simple_length
            )
            if len(args) == 1 or not_too_long:
                return f"[{sep2.join(args)}]", True
            return f"[{prefix}{sep.join(args)}{postfix}]", False

        return repr(node), True

    return _format(node, 0)[0]
