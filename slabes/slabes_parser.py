
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
        if (
            (statements := self.statements())
            and
            (_endmarker := self.expect('ENDMARKER'))
        ):
            return [statements, _endmarker];
        self._reset(mark)
        return None;

    @memoize
    def statements(self) -> Optional[Any]:
        # statements: statement*
        # nullable=True
        mark = self._mark()
        if (
            (_loop0_1 := self._loop0_1(),)
        ):
            return _loop0_1;
        self._reset(mark)
        return None;

    @memoize
    def statement(self) -> Optional[Any]:
        # statement: expr ((',' expr))* '.'
        mark = self._mark()
        if (
            (expr := self.expr())
            and
            (_loop0_2 := self._loop0_2(),)
            and
            (literal := self.expect('.'))
        ):
            return [expr, _loop0_2, literal];
        self._reset(mark)
        return None;

    @memoize
    def expr(self) -> Optional[Any]:
        # expr: atom | declaration
        mark = self._mark()
        if (
            (atom := self.atom())
        ):
            return atom;
        self._reset(mark)
        if (
            (declaration := self.declaration())
        ):
            return declaration;
        self._reset(mark)
        return None;

    @memoize
    def declaration(self) -> Optional[Any]:
        # declaration: number_declaration
        mark = self._mark()
        if (
            (number_declaration := self.number_declaration())
        ):
            return number_declaration;
        self._reset(mark)
        return None;

    @memoize
    def number_declaration(self) -> Optional[Any]:
        # number_declaration: number_type NAME+ '<<' signed_number | invalid_number_declaration
        mark = self._mark()
        if (
            (number_type := self.number_type())
            and
            (_loop1_3 := self._loop1_3())
            and
            (literal := self.expect('<<'))
            and
            (signed_number := self.signed_number())
        ):
            return [number_type, _loop1_3, literal, signed_number];
        self._reset(mark)
        if (
            self.call_invalid_rules
            and
            (self.invalid_number_declaration())
        ):
            return None  # pragma: no cover;
        self._reset(mark)
        return None;

    @memoize
    def invalid_number_declaration(self) -> Optional[Any]:
        # invalid_number_declaration: number_type ((keywords | NAME))+ '<<' signed_number
        mark = self._mark()
        if (
            (self.number_type())
            and
            (names := self._loop1_4())
            and
            (self.expect('<<'))
            and
            (self.signed_number())
        ):
            return self . invalid_number_declaration_bad_names ( names );
        self._reset(mark)
        return None;

    @memoize
    def number_type(self) -> Optional[Any]:
        # number_type: TINY | SMALL | NORMAL | BIG
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
    def signed_number(self) -> Optional[Any]:
        # signed_number: sign? NUMBER
        mark = self._mark()
        if (
            (opt := self.sign(),)
            and
            (number := self.number())
        ):
            return [opt, number];
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
    def atom(self) -> Optional[Any]:
        # atom: NAME | NUMBER
        mark = self._mark()
        if (
            (name := self.name())
        ):
            return name;
        self._reset(mark)
        if (
            (number := self.number())
        ):
            return number;
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
    def _loop0_2(self) -> Optional[Any]:
        # _loop0_2: (',' expr)
        mark = self._mark()
        children = []
        while (
            (_tmp_5 := self._tmp_5())
        ):
            children.append(_tmp_5)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop1_3(self) -> Optional[Any]:
        # _loop1_3: NAME
        mark = self._mark()
        children = []
        while (
            (name := self.name())
        ):
            children.append(name)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop1_4(self) -> Optional[Any]:
        # _loop1_4: (keywords | NAME)
        mark = self._mark()
        children = []
        while (
            (_tmp_6 := self._tmp_6())
        ):
            children.append(_tmp_6)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _tmp_5(self) -> Optional[Any]:
        # _tmp_5: ',' expr
        mark = self._mark()
        if (
            (literal := self.expect(','))
            and
            (expr := self.expr())
        ):
            return [literal, expr];
        self._reset(mark)
        return None;

    @memoize
    def _tmp_6(self) -> Optional[Any]:
        # _tmp_6: keywords | NAME
        mark = self._mark()
        if (
            (keywords := self.keywords())
        ):
            return keywords;
        self._reset(mark)
        if (
            (name := self.name())
        ):
            return name;
        self._reset(mark)
        return None;

    KEYWORDS = ()
    SOFT_KEYWORDS = ()

if __name__ == '__main__':
    parser_main(SlabesParser)