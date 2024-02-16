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
class NumberLiteral(Expression):
    value: int

    def fields(self):
        yield from super().fields()
        yield "value", self.value

    # def __str__(self) -> str:
    #     return str(self)


@dataclass
class Name(Expression):
    value: str

    def fields(self):
        yield from super().fields()
        yield "value", self.value


@dataclass
class NumberDeclaration(Statement):
    type: NumberType
    names: list[Name]
    value: NumberLiteral

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
    value: NumberLiteral

    def fields(self):
        yield from super().fields()
        yield "element_type", self.element_type
        yield "size_type", self.size_type
        yield "names", self.names
        yield "value", self.value


def dump(
    node: AST,
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

    if not isinstance(node, AST):
        raise TypeError("expected AST, got %r" % node.__class__.__name__)

    if indent is not None and not isinstance(indent, str):
        good_indent = " " * indent
    else:
        good_indent = indent

    def _next_level(node, level: int) -> int:
        if isinstance(node, AST):
            if include_attributes:
                return level + 1

            two_or_more_fields = any(
                i > 0 for i, _ in enumerate(node.fields())
            )
            if two_or_more_fields:
                return level + 1
        elif isinstance(node, list):
            if len(node) >= 2:
                return level + 1
        return level

    def _format(node, level: int) -> tuple[str, bool]:
        level = _next_level(node, level)

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
            keywords = annotate_fields
            for name, value in node.fields():
                value, simple = _format(value, level)
                allsimple = allsimple and simple
                if keywords:
                    args.append("%s=%s" % (name, value))
                else:
                    args.append(value)
            if include_attributes:
                for name, value in node.attributes():
                    value, simple = _format(value, level)
                    allsimple = allsimple and simple
                    args.append("%s=%s" % (name, value))
            if allsimple and len(args) <= 3:
                return f"{type(node).__name__}({', '.join(args)})", not args
            if len(args) == 1:
                return f"{type(node).__name__}({args[0]})", allsimple
            return f"{type(node).__name__}({prefix}{sep.join(args)}{postfix})", False
        elif isinstance(node, list):
            if not node:
                return "[]", True
            if len(node) == 1:
                value, simple = _format(node[0], 0)
                return f"[{value}]", simple
            return (
                f"[{prefix}{sep.join(_format(x, level)[0] for x in node)}{postfix}]",
                False,
            )

        return repr(node), True

    return _format(node, 0)[0]
