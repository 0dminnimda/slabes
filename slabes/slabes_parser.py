
#!/usr/bin/env python
# @generated by pegen from slabes/slabes.gram

import sys
import tokenize
import typing

from typing import Any, Optional

from pegen.parser import memoize, memoize_left_rec, logger
from . import ast_nodes as ast
from .parser_base import ParserBase as Parser, parser_main
# Keywords and soft keywords are listed at the end of the parser definition.
class SlabesParser(Parser):

    @memoize
    def start(self) -> Optional[ast . Module]:
        # start: statements $
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.statements())
            and
            (self.expect('ENDMARKER'))
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return ast . Module ( a , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def statements(self) -> Optional[list [ast . Statement]]:
        # statements: statement*
        # nullable=True
        mark = self._mark()
        if (
            (a := self._loop0_1(),)
        ):
            return a;
        self._reset(mark)
        return None;

    @memoize
    def statement(self) -> Optional[ast . Statement]:
        # statement: declaration '.' | assignment '.' | ','.expr+ '.'
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (declaration := self.declaration())
            and
            (self.expect('.'))
        ):
            return declaration;
        self._reset(mark)
        if (
            (assignment := self.assignment())
            and
            (self.expect('.'))
        ):
            return assignment;
        self._reset(mark)
        if (
            (exprs := self._gather_2())
            and
            (self.expect('.'))
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return ast . CompoundExpression ( exprs , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize_left_rec
    def expr(self) -> Optional[ast . Expression]:
        # expr: primary | invalid_expr
        mark = self._mark()
        if (
            (primary := self.primary())
        ):
            return primary;
        self._reset(mark)
        if (
            self.call_invalid_rules
            and
            (self.invalid_expr())
        ):
            return None  # pragma: no cover;
        self._reset(mark)
        return None;

    @memoize
    def invalid_expr(self) -> Optional[Any]:
        # invalid_expr: declaration
        mark = self._mark()
        if (
            (a := self.declaration())
        ):
            return self . report_syntax_error_at ( "expected expression, got declaration." " Did you mean to use '.' before/after this declaration?" , a , fatal = True , );
        self._reset(mark)
        return None;

    @memoize
    def assignment(self) -> Optional[ast . Assignment]:
        # assignment: expr ((('<<' | '>>') expr))+
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (start := self.expr())
            and
            (rest := self._loop1_4())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_assignment ( start , rest , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def declaration(self) -> Optional[ast . NumberDeclaration]:
        # declaration: array_declaration | number_declaration
        mark = self._mark()
        if (
            (array_declaration := self.array_declaration())
        ):
            return array_declaration;
        self._reset(mark)
        if (
            (number_declaration := self.number_declaration())
        ):
            return number_declaration;
        self._reset(mark)
        return None;

    @memoize
    def array_declaration(self) -> Optional[ast . ArrayDeclaration]:
        # array_declaration: FIELD number_type number_type identifier+ '<<' signed_number | recover_array_declaration
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (self.FIELD())
            and
            (elem_t := self.number_type())
            and
            (size_t := self.number_type())
            and
            (names := self._loop1_5())
            and
            (self.expect('<<'))
            and
            (signed_number := self.signed_number())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_array_declaration ( elem_t , size_t , names , signed_number , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (recover_array_declaration := self.recover_array_declaration())
        ):
            return recover_array_declaration;
        self._reset(mark)
        return None;

    @memoize
    def recover_array_declaration(self) -> Optional[ast . ArrayDeclaration]:
        # recover_array_declaration: FIELD word word word+ '<<' signed_number
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (self.FIELD())
            and
            (elem_t := self.word())
            and
            (size_t := self.word())
            and
            (names := self._loop1_6())
            and
            (self.expect('<<'))
            and
            (signed_number := self.signed_number())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_array_declaration ( self . make_number_type ( elem_t , ** self . locs ( elem_t ) ) , self . make_number_type ( size_t , ** self . locs ( size_t ) ) , [self . make_name ( name , ** self . locs ( name ) ) for name in names] , signed_number , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def number_declaration(self) -> Optional[ast . NumberDeclaration]:
        # number_declaration: number_type identifier+ '<<' signed_number | recover_number_declaration
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (type := self.number_type())
            and
            (names := self._loop1_7())
            and
            (self.expect('<<'))
            and
            (signed_number := self.signed_number())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_number_declaration ( type , names , signed_number , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (recover_number_declaration := self.recover_number_declaration())
        ):
            return recover_number_declaration;
        self._reset(mark)
        return None;

    @memoize
    def recover_number_declaration(self) -> Optional[ast . NumberDeclaration]:
        # recover_number_declaration: word word+ '<<' signed_number
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (type := self.word())
            and
            (names := self._loop1_8())
            and
            (self.expect('<<'))
            and
            (signed_number := self.signed_number())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_number_declaration ( self . make_number_type ( type , ** self . locs ( type ) ) , [self . make_name ( name , ** self . locs ( name ) ) for name in names] , signed_number , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @logger
    def primary(self) -> Optional[Any]:
        # primary: subscript | atom
        mark = self._mark()
        if (
            (subscript := self.subscript())
        ):
            return subscript;
        self._reset(mark)
        if (
            (atom := self.atom())
        ):
            return atom;
        self._reset(mark)
        return None;

    @logger
    def subscript(self) -> Optional[ast . Subscript]:
        # subscript: expr '[' expr* ']' | recover_subscript
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.expr())
            and
            (self.expect('['))
            and
            (exprs := self._loop0_9(),)
            and
            (self.expect(']'))
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_subscript ( a , exprs , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (recover_subscript := self.recover_subscript())
        ):
            return recover_subscript;
        self._reset(mark)
        return None;

    @memoize
    def recover_subscript(self) -> Optional[ast . Subscript]:
        # recover_subscript: word '[' expr* ']'
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.word())
            and
            (self.expect('['))
            and
            (exprs := self._loop0_10(),)
            and
            (self.expect(']'))
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_subscript ( self . make_name ( a , ** self . locs ( a ) ) , exprs , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def atom(self) -> Optional[Any]:
        # atom: identifier | signed_number
        mark = self._mark()
        if (
            (identifier := self.identifier())
        ):
            return identifier;
        self._reset(mark)
        if (
            (signed_number := self.signed_number())
        ):
            return signed_number;
        self._reset(mark)
        return None;

    @memoize
    def signed_number(self) -> Optional[ast . NumericLiteral]:
        # signed_number: sign? NUMBER
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (sign := self.sign(),)
            and
            (num := self.number())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_number ( num , sign , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def sign(self) -> Optional[Any]:
        # sign: '+' | '-'
        mark = self._mark()
        if (
            (literal := self.expect('+'))
        ):
            return literal;
        self._reset(mark)
        if (
            (literal := self.expect('-'))
        ):
            return literal;
        self._reset(mark)
        return None;

    @memoize
    def number_type(self) -> Optional[ast . NumberType]:
        # number_type: number_type_raw
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.number_type_raw())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_number_type ( a , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def number_type_raw(self) -> Optional[Any]:
        # number_type_raw: TINY | SMALL | NORMAL | BIG
        mark = self._mark()
        if (
            (TINY := self.TINY())
        ):
            return TINY;
        self._reset(mark)
        if (
            (SMALL := self.SMALL())
        ):
            return SMALL;
        self._reset(mark)
        if (
            (NORMAL := self.NORMAL())
        ):
            return NORMAL;
        self._reset(mark)
        if (
            (BIG := self.BIG())
        ):
            return BIG;
        self._reset(mark)
        return None;

    @memoize
    def identifier(self) -> Optional[ast . Name]:
        # identifier: NAME
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.name())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_name ( a , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def word(self) -> Optional[Any]:
        # word: NAME | keyword
        mark = self._mark()
        if (
            (name := self.name())
        ):
            return name;
        self._reset(mark)
        if (
            (keyword := self.keyword())
        ):
            return keyword;
        self._reset(mark)
        return None;

    @memoize
    def keyword(self) -> Optional[Any]:
        # keyword: number_type_raw | FIELD
        mark = self._mark()
        if (
            (number_type_raw := self.number_type_raw())
        ):
            return number_type_raw;
        self._reset(mark)
        if (
            (FIELD := self.FIELD())
        ):
            return FIELD;
        self._reset(mark)
        return None;

    @memoize
    def _loop0_1(self) -> Optional[Any]:
        # _loop0_1: statement
        mark = self._mark()
        children = []
        while (
            (statement := self.statement())
        ):
            children.append(statement)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop0_3(self) -> Optional[Any]:
        # _loop0_3: ',' expr
        mark = self._mark()
        children = []
        while (
            (self.expect(','))
            and
            (elem := self.expr())
        ):
            children.append(elem)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _gather_2(self) -> Optional[Any]:
        # _gather_2: expr _loop0_3
        mark = self._mark()
        if (
            (elem := self.expr())
            is not None
            and
            (seq := self._loop0_3())
            is not None
        ):
            return [elem] + seq;
        self._reset(mark)
        return None;

    @memoize
    def _loop1_4(self) -> Optional[Any]:
        # _loop1_4: (('<<' | '>>') expr)
        mark = self._mark()
        children = []
        while (
            (_tmp_11 := self._tmp_11())
        ):
            children.append(_tmp_11)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop1_5(self) -> Optional[Any]:
        # _loop1_5: identifier
        mark = self._mark()
        children = []
        while (
            (identifier := self.identifier())
        ):
            children.append(identifier)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop1_6(self) -> Optional[Any]:
        # _loop1_6: word
        mark = self._mark()
        children = []
        while (
            (word := self.word())
        ):
            children.append(word)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop1_7(self) -> Optional[Any]:
        # _loop1_7: identifier
        mark = self._mark()
        children = []
        while (
            (identifier := self.identifier())
        ):
            children.append(identifier)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop1_8(self) -> Optional[Any]:
        # _loop1_8: word
        mark = self._mark()
        children = []
        while (
            (word := self.word())
        ):
            children.append(word)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop0_9(self) -> Optional[Any]:
        # _loop0_9: expr
        mark = self._mark()
        children = []
        while (
            (expr := self.expr())
        ):
            children.append(expr)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop0_10(self) -> Optional[Any]:
        # _loop0_10: expr
        mark = self._mark()
        children = []
        while (
            (expr := self.expr())
        ):
            children.append(expr)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _tmp_11(self) -> Optional[Any]:
        # _tmp_11: ('<<' | '>>') expr
        mark = self._mark()
        if (
            (_tmp_12 := self._tmp_12())
            and
            (expr := self.expr())
        ):
            return [_tmp_12, expr];
        self._reset(mark)
        return None;

    @memoize
    def _tmp_12(self) -> Optional[Any]:
        # _tmp_12: '<<' | '>>'
        mark = self._mark()
        if (
            (literal := self.expect('<<'))
        ):
            return literal;
        self._reset(mark)
        if (
            (literal := self.expect('>>'))
        ):
            return literal;
        self._reset(mark)
        return None;

    KEYWORDS = ()
    SOFT_KEYWORDS = ()

if __name__ == '__main__':
    parser_main(SlabesParser)
