from __future__ import annotations
from dataclasses import dataclass, field
from contextlib import contextmanager
from pathlib import Path

from . import ast_nodes as ast
from . import types as ts
from . import errors
from . import eval as ev
from .errors import report_fatal_at
from .location import Location
from .parser_base import DEFAULT_FILENAME


DIR = Path(__file__).parent


@dataclass
class IntTypeInfo:
    name: str
    bits: int
    ctype: str
    format: str
    can_be_signed: bool

    def signed_range(self) -> tuple[int, int]:
        if self.bits <= 0:
            return (0, 0)
        if self.bits == 1:
            return (0, 1)
        return (-(1 << (self.bits - 1)), (1 << (self.bits - 1)) - 1)

    def unsigned_range(self) -> tuple[int, int]:
        return (0, (1 << self.bits) - 1)


INT_TYPE_INFO = {
    "tiny": IntTypeInfo("tiny", 1, "int8_t", "%hh", True),
    "small": IntTypeInfo("small", 5, "int8_t", "%hh", True),
    "normal": IntTypeInfo("normal", 10, "int16_t", "%h", True),
    "big": IntTypeInfo("big", 15, "int16_t", "%h", True),
}


SIGN_UNSING = ["", "unsigned_"]


INT_TYPE_TEMPLATE = """
typedef /*ctype*/ slabes_type_/*name*/;

#define slabes_format_/*name*/ "/*format*/"
#define slabes_max_value_/*name*/ /*max_value*/
#define slabes_min_value_/*name*/ /*min_value*/

void assign_slabes_type_/*name*/(slabes_type_/*name*/ *var, slabes_type_/*name*/ value) {
#ifdef SLABES_DEBUG_OP
    printf("assign_slabes_type_/*name*/(%p, " slabes_format_/*name*/ ")\\n", var, value);
#endif
    *var = value;
}
"""


def make_int_types():
    for info in INT_TYPE_INFO.values():
        min_unsigned, max_unsigned = info.unsigned_range()
        if info.can_be_signed:
            min_signed, max_signed = info.signed_range()
        else:
            min_signed, max_signed = min_unsigned, max_unsigned
        yield (
            INT_TYPE_TEMPLATE.replace("/*ctype*/", info.ctype)
            .replace("/*name*/", info.name)
            .replace("/*format*/", info.format + "i")
            .replace("/*max_value*/", str(max_signed))
            .replace("/*min_value*/", str(min_signed))
        )
        yield (
            INT_TYPE_TEMPLATE.replace("/*ctype*/", "unsigned_" + info.ctype)
            .replace("/*name*/", "unsigned_" + info.name)
            .replace("/*format*/", info.format + "u")
            .replace("/*max_value*/", str(max_unsigned))
            .replace("/*min_value*/", str(min_unsigned))
        )


INT_TYPES = "\n".join(make_int_types())


INT_BIN_OP_TEMPLATE = """
slabes_type_/*name*/ slabes_op_/*op_name*/__/*name1*/__/*name2*/(slabes_type_/*name1*/ lhs, slabes_type_/*name2*/ rhs) {
    /*preamble*/
    slabes_type_/*name*/ result;
    /*op*/;
    /*postamble*/
#ifdef SLABES_DEBUG_OP
    printf("slabes_op_/*op_name*/__/*name1*/__/*name2*/(" slabes_format_/*name1*/ ", " slabes_format_/*name2*/ ")", lhs, rhs);
    printf(" -> " slabes_format_/*name*/ "\\n", result);
#endif
    return result;
}
"""

INT_BIN_OP_TEMPLATE_DIFFERENT_TYPES = """
#define slabes_op_/*op_name*/__/*name1*/__/*name2*/(lhs, rhs) \
    slabes_op_/*op_name*/__/*name*/__/*name*/(slabes_convert_/*name1*/_to_/*name*/(lhs), slabes_convert_/*name2*/_to_/*name*/(rhs))
"""

INT_BIN_OP_NO_CHECK = """
result = rhs /*op*/ lhs;
"""

INT_BIN_OP_CHECK_OVEFLOW_FULL = """
if (ckd_/*op_name*/(&result, lhs, rhs)) {
    result = slabes_max_value_/*name*/;
}
"""

INT_BIN_OP_CHECK_OVEFLOW_PARTIAL_LESS = INT_BIN_OP_NO_CHECK + """
if (result < slabes_min_value_/*name*/) {
    result = slabes_min_value_/*name*/;
}
"""

INT_BIN_OP_CHECK_OVEFLOW_PARTIAL_MORE = INT_BIN_OP_NO_CHECK + """
if (result > slabes_max_value_/*name*/) {
    result = slabes_max_value_/*name*/;
}
"""

INT_BIN_OP_CHECK_OVEFLOW_PARTIAL_MUCH_MORE = INT_BIN_OP_CHECK_OVEFLOW_FULL + """
else if (result > slabes_max_value_/*name*/) {
    result = slabes_max_value_/*name*/;
}
"""


INT_BIN_OP_INFO = [
    ("add", {
        "tiny": INT_BIN_OP_NO_CHECK.replace("/*op*/", "+"),
        "small": INT_BIN_OP_CHECK_OVEFLOW_PARTIAL_MORE.replace("/*op*/", "+"),
        "normal": INT_BIN_OP_CHECK_OVEFLOW_PARTIAL_MORE.replace("/*op*/", "+"),
        "big": INT_BIN_OP_CHECK_OVEFLOW_FULL,
    }),
    ("sub", {
        "tiny": INT_BIN_OP_NO_CHECK.replace("/*op*/", "-"),
        "small": INT_BIN_OP_CHECK_OVEFLOW_PARTIAL_LESS.replace("/*op*/", "-"),
        "normal": INT_BIN_OP_CHECK_OVEFLOW_PARTIAL_LESS.replace("/*op*/", "-"),
        "big": INT_BIN_OP_CHECK_OVEFLOW_FULL,
    }),
    ("mul", {
        "tiny": INT_BIN_OP_NO_CHECK.replace("/*op*/", "*"),
        "small": INT_BIN_OP_CHECK_OVEFLOW_PARTIAL_MUCH_MORE.replace("/*op*/", "*"),
        "normal": INT_BIN_OP_CHECK_OVEFLOW_PARTIAL_MUCH_MORE.replace("/*op*/", "*"),
        "big": INT_BIN_OP_CHECK_OVEFLOW_FULL,
    }),
    ("div", dict.fromkeys(INT_TYPE_INFO.keys(), INT_BIN_OP_NO_CHECK.replace("/*op*/", "/"))),
]

INT_BIN_OP_DIV_CODE = "if (rhs == 0) return slabes_max_value_/*name*/;"


def make_int_bin_ops():
    for i, info1 in enumerate(INT_TYPE_INFO.values()):
        for j, info2 in enumerate(INT_TYPE_INFO.values()):
            _, info, ind_max = max((i, info1, 0), (j, info2, 1))

            for op_name, op in INT_BIN_OP_INFO:
                if i != j:
                    template = INT_BIN_OP_TEMPLATE_DIFFERENT_TYPES
                else:
                    template = INT_BIN_OP_TEMPLATE

                preamble = INT_BIN_OP_DIV_CODE if op_name == "div" else ""
                postamble = ""
                for unsig1 in SIGN_UNSING:
                    for unsig2 in SIGN_UNSING:
                        yield (
                            template
                            .replace("/*preamble*/", preamble)
                            .replace("/*postamble*/", postamble)
                            .replace("/*op*/", op[info.name])
                            .replace("/*name*/", [unsig1, unsig2][ind_max] + info.name)
                            .replace("/*name1*/", unsig1 + info1.name)
                            .replace("/*name2*/", unsig2 + info2.name)
                            .replace("/*op_name*/", op_name)
                        )


INT_BIN_OPS = "\n".join(make_int_bin_ops())


INT_CMP_OP_TEMPLATE = """
slabes_type_tiny slabes_op_/*op_name*/__/*name1*/__/*name2*/(slabes_type_/*name1*/ lhs, slabes_type_/*name2*/ rhs) {
#ifdef SLABES_DEBUG_OP
    printf("slabes_op_/*op_name*/__/*name1*/__/*name2*/(" slabes_format_/*name1*/ ", " slabes_format_/*name2*/ ")", lhs, rhs);
#endif
    if (lhs /*op*/ rhs) {
#ifdef SLABES_DEBUG_OP
        printf(" -> true\\n");
#endif
        return slabes_max_value_unsigned_tiny;
    } else {
#ifdef SLABES_DEBUG_OP
        printf(" -> false\\n");
#endif
        return slabes_min_value_unsigned_tiny;
    }
}
"""


INT_CMP_OP_INFO = {
    "eq": "==",
    "ne": "!=",
    "le": "<=",
    "ge": ">=",
}


def make_int_cmp_ops():
    for info1 in INT_TYPE_INFO.values():
        for info2 in INT_TYPE_INFO.values():
            for op_name, op in INT_CMP_OP_INFO.items():
                template = INT_CMP_OP_TEMPLATE

                for unsig1 in SIGN_UNSING:
                    for unsig2 in SIGN_UNSING:
                        yield (
                            template
                            .replace("/*op*/", op)
                            .replace("/*name1*/", unsig1 + info1.name)
                            .replace("/*name2*/", unsig2 + info2.name)
                            .replace("/*op_name*/", op_name)
                        )


INT_CMP_OPS = "\n".join(make_int_cmp_ops())


INT_CONVERT_TEMPLATE = """
slabes_type_/*name2*/ slabes_convert_/*name1*/_to_/*name2*/(slabes_type_/*name1*/ value) {
    value = /*arg*/;
#ifdef SLABES_DEBUG_OP
    printf("slabes_convert_/*name1*/_to_/*name2*/(" slabes_format_/*name1*/ ")", value);
#endif
    if (value > slabes_max_value_/*name2*/) {
#ifdef SLABES_DEBUG_OP
        printf(" -> " slabes_format_/*name2*/ "\\n", slabes_max_value_/*name2*/);
#endif
        return slabes_max_value_/*name2*/;
    } else if (value < slabes_min_value_/*name2*/) {
#ifdef SLABES_DEBUG_OP
        printf(" -> " slabes_format_/*name2*/ "\\n", slabes_min_value_/*name2*/);
#endif
        return slabes_min_value_/*name2*/;
    }
#ifdef SLABES_DEBUG_OP
    else {
        printf(" -> " slabes_format_/*name2*/ "\\n", (slabes_type_/*name2*/)value);
    }
#endif
    return value;
}
"""

INT_CONVERT_TEMPLATE_NOOP = """
#define slabes_convert_/*name1*/_to_/*name2*/(value) ((slabes_type_/*name2*/)/*arg*/)
"""

INT_REMOVE_SIGN = """
#define slabes_remove_sign_/*name*/ slabes_convert_/*name*/_to_unsigned_/*name*/
slabes_type_unsigned_/*name*/ slabes_convert_/*name*/_to_unsigned_/*name*/(slabes_type_/*name*/ value) {
#ifdef SLABES_DEBUG_OP
    printf("slabes_convert_/*name*/_to_unsigned_/*name*/(" slabes_format_/*name*/ ")", value);
#endif
    if (value < slabes_min_value_unsigned_/*name*/) {
#ifdef SLABES_DEBUG_OP
        printf(" -> " slabes_format_/*name*/ "\\n", slabes_min_value_unsigned_/*name*/);
#endif
        return slabes_min_value_unsigned_/*name*/;
    }
#ifdef SLABES_DEBUG_OP
    else {
        printf(" -> " slabes_format_/*name*/ "\\n", (slabes_type_unsigned_/*name*/)value);
    }
#endif
    return value;
}
"""

INT_ADD_SIGN = """
#define slabes_add_sign_/*name*/ slabes_convert_unsigned_/*name*/_to_/*name*/
slabes_type_/*name*/ slabes_convert_unsigned_/*name*/_to_/*name*/(slabes_type_unsigned_/*name*/ value) {
#ifdef SLABES_DEBUG_OP
    printf("slabes_convert_unsigned_/*name*/_to_/*name*/(" slabes_format_/*name*/ ")", value);
#endif
    if (value > slabes_max_value_/*name*/) {
#ifdef SLABES_DEBUG_OP
        printf(" -> " slabes_format_/*name*/ "\\n", slabes_max_value_/*name*/);
#endif
        return slabes_max_value_/*name*/;
    }
#ifdef SLABES_DEBUG_OP
    else {
        printf(" -> " slabes_format_/*name*/ "\\n", (slabes_type_/*name*/)value);
    }
#endif
    return value;
}
"""


def make_int_convertions():
    for info in INT_TYPE_INFO.values():
        yield (
            INT_REMOVE_SIGN
            .replace("/*name*/", info.name)
        )
        yield (
            INT_ADD_SIGN
            .replace("/*name*/", info.name)
        )

    for i, info1 in enumerate(INT_TYPE_INFO.values()):
        for j, info2 in enumerate(INT_TYPE_INFO.values()):
            if i > j:
                template = INT_CONVERT_TEMPLATE
            else:
                template = INT_CONVERT_TEMPLATE_NOOP

            for unsig1 in SIGN_UNSING:
                for unsig2 in SIGN_UNSING:
                    if unsig1 and not unsig2:
                        arg = f"slabes_convert_unsigned_{info1.name}_to_{info1.name}(value)"
                    elif not unsig1 and unsig2:
                        arg = f"slabes_convert_{info1.name}_to_unsigned_{info1.name}(value)"
                    else:
                        arg = "value"

                    yield (
                        template
                        .replace("/*name1*/", unsig1 + info1.name)
                        .replace("/*name2*/", unsig2 + info2.name)
                        .replace("/*arg*/", arg)
                    )


INT_CONVERTIONS = "\n".join(make_int_convertions())


MATRIX_TYPE_TEMPLATE = """
typedef slabes_type_/*name*/ *slabes_type_matrix_/*name*/;

#define slabes_format_/*name*/ "%p"

void init_slabes_type_matrix_/*name*/(slabes_type_matrix_/*name*/ *var, slabes_type_/*name*/ value, size_t size) {
#ifdef SLABES_DEBUG_OP
    printf("assign_slabes_type_matrix_/*name*/(%p, " slabes_format_/*name*/ ")\\n", var, value);
#endif
    if (*var == NULL) {
        *var = malloc(size * sizeof(slabes_type_/*name*/));
    }
    memset(*var, value, size * sizeof(slabes_type_/*name*/));
}

void assign_slabes_type_matrix_/*name*/(slabes_type_matrix_/*name*/ *var, slabes_type_matrix_/*name*/ value) {
#ifdef SLABES_DEBUG_OP
    printf("assign_slabes_type_matrix_/*name*/(%p, " slabes_format_/*name*/ ")\\n", var, value);
#endif
    *var = value;
}
"""


def make_matrix_types():
    for info in INT_TYPE_INFO.values():
        yield MATRIX_TYPE_TEMPLATE.replace("/*name*/", info.name)
        yield MATRIX_TYPE_TEMPLATE.replace("/*name*/", "unsigned_" + info.name)


MATRIX_TYPES = "\n".join(make_matrix_types())

TEMPLATE = Path(DIR / "slabes_template.c").read_text()

TEMPLATE = (
    TEMPLATE.replace("/*types*/", INT_TYPES + MATRIX_TYPES)
    .replace("/*ops*/", INT_BIN_OPS + INT_CMP_OPS)
    .replace("/*conv*/", INT_CONVERTIONS)
)


PART_SEPARATOR: str = " "

MAIN_FUNCTION = "main"


def is_variable(type):
    return not (
        isinstance(type, ts.FunctionType)
    )


@dataclass
class GenerateC:
    temporary_parts: list[str] = field(default_factory=list)
    main_parts: list[str] = field(default_factory=list)
    declaration_parts: list[str] = field(default_factory=list)

    current_temp: int = 0

    scope: ev.ScopeValue = field(init=False)

    _filepath: str = field(default=DEFAULT_FILENAME)
    _lines: list[str] = field(default_factory=list)

    def visit(self, node):
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is None:
            report_fatal_at(
                node.loc,
                errors.SyntaxError,
                f"analysis node '{type(node).__name__}' is currently not supported for codegen",
                self._lines,
            )
        return visitor(node)

    def merge_parts(self, parts: list[str]) -> str:
        return PART_SEPARATOR.join(parts).replace(";;", ";\n")

    def generate(
        self, code: str, eval: ev.Module, filepath: str = DEFAULT_FILENAME
    ) -> str:
        self._filepath = filepath
        self._lines = code.splitlines()
        self.visit(eval)
        assert (
            len(self.temporary_parts) == 0
        ), "temporary_parts should be saved before generation"
        return (
            TEMPLATE.replace("/*file*/", filepath)
            .replace("/*decl*/", self.merge_parts(self.declaration_parts))
            .replace("/*main*/", self.merge_parts(self.main_parts))
        )

    def collect(self, *args, **kwargs) -> str:
        previous = len(self.temporary_parts)
        self.put(*args, **kwargs)
        result = " ".join(self.temporary_parts[previous:])
        del self.temporary_parts[previous:]
        return result

    @contextmanager
    def isolate(self):
        old = self.temporary_parts, self.current_temp
        self.temporary_parts = []
        self.current_temp = 0

        yield self.temporary_parts

        self.temporary_parts, self.current_temp = old

    def save(self, parts: list[str], to_parts: list[str], front: bool = False) -> None:
        if front:
            to_parts[0:0] = parts
        else:
            to_parts.extend(parts)

    def put(self, *values, sep: str | None = None) -> None:
        """
        Each non-string value gets visited,
        then if the value or result of the visit is not None,
        it gets directly added to temporary_parts.
        If sep is not None it is added between the values.
        If the value is tuple, its items will be visited without adding sep in between.
        """

        first = True
        for value in values:
            if value is None:
                continue

            if not first and sep is not None:
                self.temporary_parts.append(sep)
            first = False

            if type(value) is not tuple:
                value = (value,)

            for item in value:
                if type(item) is not str:
                    item = self.visit(item)

                if item is not None:
                    self.temporary_parts.append(item)

    @contextmanager
    def new_scope(self, new: ev.ScopeValue):
        old = getattr(self, "scope", None)
        self.scope = new
        try:
            yield self.scope
        finally:
            if old is not None:
                self.scope = old

    def visit_str(self, string: str) -> str:
        return string

    def put_scope_finalization(self, node: ev.ScopeValue):
        for name, value in node.name_to_value.items():
            if node.names[name].is_arg:
                continue
            if not isinstance(value, ev.Matrix):
                continue
            self.put("free(", self.var_name(name), ");;")

    def handle_scope(self, node: ev.ScopeValue):
        for name, value in node.name_to_value.items():
            if node.names[name].is_arg:
                continue
            if not is_variable(value.type):
                continue
            self.put(self.type_name(value.type), self.var_name(name), " = 0;;")

        with self.new_scope(node):
            for it in node.body:
                self.put(it, ";;")

        self.put_scope_finalization(node)

    def visit_Module(self, node: ev.Module):
        self.scope = node

        with self.isolate() as program:
            self.handle_scope(node)

        self.save(program, self.main_parts)

    def function_name(self, name: str) -> str:
        return "slabes_func_" + name

    def visit_Function(self, node: ev.Function):
        if node.name == MAIN_FUNCTION:
            name = "program_main"
        else:
            name = self.function_name(node.name)

        with self.isolate() as decl:
            self.put(self.type_name(node.return_value.type))
            args = []
            for arg_name, arg in (node.args or {}).items():
                args.append(self.type_name(arg.type) + " " + self.var_name(arg_name))
            self.put(name, "(", ", ".join(args) or "void", ")")

        with self.isolate() as defn:
            self.put("{\n")

            self.handle_scope(node)

            self.put("}\n")

        self.save(decl + [";\n"], self.declaration_parts)
        self.save(decl, self.main_parts)
        self.save(defn, self.main_parts)

    def type_name(self, node: ts.Type) -> str:
        return "slabes_type_" + node.name()

    def type_max(self, node: ts.Type) -> str:
        return "slabes_max_value_" + node.name()

    def type_min(self, node: ts.Type) -> str:
        return "slabes_min_value_" + node.name()

    def var_name(self, name: str) -> str:
        return "slabes_var_" + name

    def visit_Assign(self, node: ev.Assign):
        for name in node.names:
            tp = self.scope.name_to_value[name].type

            if isinstance(node.value, ev.Matrix):
                assert isinstance(tp, ts.MatrixType), "Matrix evaluated not to MatrixType"
                self.put(f"init_slabes_type_matrix_{tp.item_type.name()}(&{self.var_name(name)},", node.value, ",", self.type_max(node.value.type.index_type) ,")")
                continue

            if is_variable(tp):
                self.put(
                    "assign_" + self.type_name(tp),
                    "(&",
                    self.var_name(name),
                    ",",
                )

            if isinstance(node.value, ev.Int):
                assert isinstance(tp, ts.IntType), "Int evaluated not to IntType"
                signed = "" if tp.signed else "unsigned_"
                conv = "slabes_convert_" + signed + "big" + "_to_" + tp.name()
                self.put(conv, "(", node.value, ")")
            elif isinstance(tp, ts.IntType) and isinstance(node.value.evaluated.type, ts.IntType):
                conv = "slabes_convert_" + node.value.evaluated.type.name() + "_to_" + tp.name()
                self.put(conv, "(", node.value, ")")
            else:
                self.put(node.value)

            if is_variable(tp):
                self.put(");;")

    def visit_Int(self, node: ev.Int):
        return str(node.value)

    def visit_Name(self, node: ev.Name):
        self.put(self.var_name(node.value))

    def visit_Matrix(self, node: ev.Matrix):
        return str(node.value)

    def visit_Call(self, node: ev.Call):
        if isinstance(node.operand.evaluated, ev.FuncPrint):
            self.handle_print(node)
        elif isinstance(node.operand.evaluated, ev.FuncAssert):
            self.handle_assert(node)
        else:
            assert isinstance(node.operand.evaluated, ev.Function), report_fatal_at(
                node.loc, errors.TypeError, "Not a function"
            )

            args = self.collect(*node.args, sep=",")
            self.put(self.function_name(node.operand.evaluated.name), "(", args, ")")

    def as_format(self, node: ts.Type) -> str:
        return "slabes_format_" + node.name()

    def handle_print(self, node: ev.Call):
        format = ""
        for arg in node.args:
            value = arg.evaluated
            format += self.as_format(value.type) + ' " " '
        format += r'"\n"'

        args = self.collect(format, *node.args, sep=",")
        self.put("printf(", args, ")")

    def handle_assert(self, node: ev.Call):
        for arg in node.args:
            value = arg.evaluated
            convert = "slabes_convert_" + value.type.name() + "_to_unsigned_tiny"
            exact_str = arg.loc.get_exact_str_from_lines(self._lines)
            if exact_str is None:
                message = "expression"
            else:
                message = "'" + exact_str + "'"
            message += f" evaluated to false (at {arg.loc})"
            self.put("slabes_assert(", convert, "(", arg, "),", '"' + message + '"', ")")

    def bin_op_name(self, op: ast.BinOp) -> str:
        return "slabes_op_" + op.name.lower()

    def visit_BinaryOperation(self, node: ev.BinaryOperation):
        self.put(
            self.bin_op_name(node.op)
            + "__"
            + node.lhs.evaluated.type.name()
            + "__"
            + node.rhs.evaluated.type.name()
        )
        self.put("(", node.lhs, ",", node.rhs, ")")

    def cmp_op_name(self, op: ast.CmpOp) -> str:
        return "slabes_op_" + op.name.lower()

    def visit_CompareOperation(self, node: ev.CompareOperation):
        lhs = node.operand
        for i, (op, rhs) in enumerate(zip(node.ops, node.operands)):
            if i:
                self.put("&&")

            self.put(
                self.cmp_op_name(op)
                + "__"
                + lhs.evaluated.type.name()
                + "__"
                + rhs.evaluated.type.name()
            )
            self.put("(", lhs, ",", rhs, ")")

            lhs = rhs

    def visit_SubscriptOperation(self, node: ev.SubscriptOperation):
        self.put(node.value, "[", node.index1, "+", node.index2, "*", self.type_max(node.value.evaluated.type.index_type), "]")

    def visit_Return(self, node: ev.Return):
        if isinstance(node.evaluated, ev.Int):
            self.put_scope_finalization(self.scope)
            self.put("return ", node.evalue, ";")
        else:
            report_fatal_at(
                node.loc,
                errors.TypeError,
                f"return type '{node.evaluated.type}' is not supported in codegen"
            )

    def visit_Condition(self, node: ev.Condition):
        self.put("if (", node.test, ") {\n")
        for it in node.body:
            self.put(it, ";;")
        self.put("}\n")

    def visit_Loop(self, node: ev.Loop):
        self.put("while (!(", node.test, ")) {\n")
        for it in node.body:
            self.put(it, ";;")
        self.put("}\n")
