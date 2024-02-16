
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
    def start(self) -> Optional[Any]:
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
        # statement: declaration '.' | ','.expr+ '.'
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
            (exprs := self._gather_2())
            and
            (self.expect('.'))
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return ast . CompoundExpression ( exprs , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def expr(self) -> Optional[ast . Expression]:
        # expr: atom | invalid_expr
        mark = self._mark()
        if (
            (atom := self.atom())
        ):
            return atom;
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
            return self . raise_syntax_error_at ( "expected expression, got declaration." " Did you mean to use '.' before/after this declaration?" , a , fatal = True , );
        self._reset(mark)
        return None;

    @memoize
    def declaration(self) -> Optional[ast . NumberDeclaration]:
        # declaration: number_declaration
        mark = self._mark()
        if (
            (number_declaration := self.number_declaration())
        ):
            return number_declaration;
        self._reset(mark)
        return None;

    @memoize
    def number_declaration(self) -> Optional[ast . NumberDeclaration]:
        # number_declaration: number_type identifier+ '<<' signed_number | bad_number_declaration
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (type := self.number_type())
            and
            (names := self._loop1_4())
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
            (bad_number_declaration := self.bad_number_declaration())
        ):
            return bad_number_declaration;
        self._reset(mark)
        return None;

    @memoize
    def bad_number_declaration(self) -> Optional[ast . NumberDeclaration]:
        # bad_number_declaration: word word+ '<<' signed_number
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (type := self.word())
            and
            (names := self._loop1_5())
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
    def signed_number(self) -> Optional[ast . NumberLiteral]:
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
            return self . make_number ( num , sign is not None and sign . string == "-" , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
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
        # number_type: number_type_
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.number_type_())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_number_type ( a , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def number_type_(self) -> Optional[Any]:
        # number_type_: TINY | SMALL | NORMAL | BIG
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
        # word: NAME | keywords
        mark = self._mark()
        if (
            (name := self.name())
        ):
            return name;
        self._reset(mark)
        if (
            (keywords := self.keywords())
        ):
            return keywords;
        self._reset(mark)
        return None;

    @memoize
    def keywords(self) -> Optional[Any]:
        # keywords: TINY | SMALL | NORMAL | BIG
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
        # _loop1_4: identifier
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
    def _loop1_5(self) -> Optional[Any]:
        # _loop1_5: word
        mark = self._mark()
        children = []
        while (
            (word := self.word())
        ):
            children.append(word)
            mark = self._mark()
        self._reset(mark)
        return children;

    KEYWORDS = ()
    SOFT_KEYWORDS = ()

if __name__ == '__main__':
    parser_main(SlabesParser)
