
#!/usr/bin/env python
# @generated by pegen from slabes/slabes.peg

import sys
import tokenize
import itertools
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
        # statements: statement_group+
        mark = self._mark()
        if (
            (a := self._loop1_1())
        ):
            return list ( itertools . chain . from_iterable ( a ) );
        self._reset(mark)
        return None;

    @memoize
    def statement_group(self) -> Optional[list [ast . Statement]]:
        # statement_group: (','+).statement+ ','* '.'
        mark = self._mark()
        if (
            (stmts := self._gather_2())
            and
            (self._loop0_4(),)
            and
            (self.expect('.'))
        ):
            return stmts;
        self._reset(mark)
        return None;

    @memoize
    def statement(self) -> Optional[ast . Statement]:
        # statement: &UNTIL ~ until_stmt | declaration | expr
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        cut = False
        if (
            (self.positive_lookahead(self.UNTIL, ))
            and
            (cut := True)
            and
            (until_stmt := self.until_stmt())
        ):
            return until_stmt;
        self._reset(mark)
        if cut:
            return None;
        if (
            (declaration := self.declaration())
        ):
            return declaration;
        self._reset(mark)
        if (
            (expr := self.expr())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return ast . SingleExpression ( expr , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def until_stmt(self) -> Optional[ast . Until]:
        # until_stmt: UNTIL expr DO statement_group
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (self.UNTIL())
            and
            (expr := self.expr())
            and
            (self.DO())
            and
            (statement_group := self.statement_group())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return ast . Until ( expr , statement_group , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def declaration(self) -> Optional[ast . NumberDeclaration]:
        # declaration: &FIELD ~ array_declaration | number_declaration
        mark = self._mark()
        cut = False
        if (
            (self.positive_lookahead(self.FIELD, ))
            and
            (cut := True)
            and
            (array_declaration := self.array_declaration())
        ):
            return array_declaration;
        self._reset(mark)
        if cut:
            return None;
        if (
            (number_declaration := self.number_declaration())
        ):
            return number_declaration;
        self._reset(mark)
        return None;

    @memoize
    def array_declaration(self) -> Optional[ast . ArrayDeclaration]:
        # array_declaration: FIELD number_type number_type identifier+ '<<' expr | recover_array_declaration
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
            (val := self.expr())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_array_declaration ( elem_t , size_t , names , val , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (recover_array_declaration := self.recover_array_declaration())
        ):
            return recover_array_declaration;
        self._reset(mark)
        return None;

    @memoize
    def recover_array_declaration(self) -> Optional[ast . ArrayDeclaration]:
        # recover_array_declaration: FIELD word word word+ '<<' expr
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
            (val := self.expr())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_array_declaration ( self . make_number_type ( elem_t , ** self . locs ( elem_t ) ) , self . make_number_type ( size_t , ** self . locs ( size_t ) ) , [self . make_name ( name , ** self . locs ( name ) ) for name in names] , val , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def number_declaration(self) -> Optional[ast . NumberDeclaration]:
        # number_declaration: number_type identifier+ '<<' expr | recover_number_declaration
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
            (val := self.expr())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_number_declaration ( type , names , val , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (recover_number_declaration := self.recover_number_declaration())
        ):
            return recover_number_declaration;
        self._reset(mark)
        return None;

    @memoize
    def recover_number_declaration(self) -> Optional[ast . NumberDeclaration]:
        # recover_number_declaration: word word+ '<<' expr
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
            (val := self.expr())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_number_declaration ( self . make_number_type ( type , ** self . locs ( type ) ) , [self . make_name ( name , ** self . locs ( name ) ) for name in names] , val , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def expr(self) -> Optional[ast . Expression]:
        # expr: assignment | invalid_expr
        mark = self._mark()
        if (
            (assignment := self.assignment())
        ):
            return assignment;
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
    def assignment(self) -> Optional[Any]:
        # assignment: comparison ((('<<' | '>>') comparison))+ | comparison
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (start := self.comparison())
            and
            (rest := self._loop1_9())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_assignment ( start , rest , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (comparison := self.comparison())
        ):
            return comparison;
        self._reset(mark)
        return None;

    @memoize
    def comparison(self) -> Optional[Any]:
        # comparison: sum
        mark = self._mark()
        if (
            (sum := self.sum())
        ):
            return sum;
        self._reset(mark)
        return None;

    @memoize_left_rec
    def sum(self) -> Optional[Any]:
        # sum: sum '+' term | sum '-' term | term
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.sum())
            and
            (self.expect('+'))
            and
            (b := self.term())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return ast . BinaryOperation ( a , ast . BinaryKind . ADD , b , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (a := self.sum())
            and
            (self.expect('-'))
            and
            (b := self.term())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return ast . BinaryOperation ( a , ast . BinaryKind . SUB , b , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (term := self.term())
        ):
            return term;
        self._reset(mark)
        return None;

    @memoize_left_rec
    def term(self) -> Optional[Any]:
        # term: term '\\' factor | term '/' factor | factor
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.term())
            and
            (self.expect('\\'))
            and
            (b := self.factor())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return ast . BinaryOperation ( a , ast . BinaryKind . MUL , b , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (a := self.term())
            and
            (self.expect('/'))
            and
            (b := self.factor())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return ast . BinaryOperation ( a , ast . BinaryKind . DIV , b , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        if (
            (factor := self.factor())
        ):
            return factor;
        self._reset(mark)
        return None;

    @memoize
    def factor(self) -> Optional[Any]:
        # factor: primary
        mark = self._mark()
        if (
            (primary := self.primary())
        ):
            return primary;
        self._reset(mark)
        return None;

    @memoize_left_rec
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
        # subscript: primary '[' expr* ']' | recover_subscript
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.primary())
            and
            (self.expect('['))
            and
            (exprs := self._loop0_10(),)
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
            (exprs := self._loop0_11(),)
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
        # atom: identifier | signed_number | &'(' group | recover_atom
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
        if (
            (self.positive_lookahead(self.expect, '('))
            and
            (group := self.group())
        ):
            return group;
        self._reset(mark)
        if (
            (recover_atom := self.recover_atom())
        ):
            return recover_atom;
        self._reset(mark)
        return None;

    @memoize
    def recover_atom(self) -> Optional[Any]:
        # recover_atom: word
        mark = self._mark()
        tok = self._tokenizer.peek()
        start_lineno, start_col_offset = tok.start
        if (
            (a := self.word())
        ):
            tok = self._tokenizer.get_last_non_whitespace_token()
            end_lineno, end_col_offset = tok.end
            return self . make_name ( a , lineno=start_lineno, col_offset=start_col_offset, end_lineno=end_lineno, end_col_offset=end_col_offset );
        self._reset(mark)
        return None;

    @memoize
    def group(self) -> Optional[Any]:
        # group: '(' comparison ')'
        mark = self._mark()
        if (
            (self.expect('('))
            and
            (a := self.comparison())
            and
            (self.expect(')'))
        ):
            return a;
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
        # keyword: number_type_raw | FIELD | BEGIN | END | UNTIL | DO | CHECK | GO | RL | RR | SONAR | COMPASS
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
        if (
            (BEGIN := self.BEGIN())
        ):
            return BEGIN;
        self._reset(mark)
        if (
            (END := self.END())
        ):
            return END;
        self._reset(mark)
        if (
            (UNTIL := self.UNTIL())
        ):
            return UNTIL;
        self._reset(mark)
        if (
            (DO := self.DO())
        ):
            return DO;
        self._reset(mark)
        if (
            (CHECK := self.CHECK())
        ):
            return CHECK;
        self._reset(mark)
        if (
            (GO := self.GO())
        ):
            return GO;
        self._reset(mark)
        if (
            (RL := self.RL())
        ):
            return RL;
        self._reset(mark)
        if (
            (RR := self.RR())
        ):
            return RR;
        self._reset(mark)
        if (
            (SONAR := self.SONAR())
        ):
            return SONAR;
        self._reset(mark)
        if (
            (COMPASS := self.COMPASS())
        ):
            return COMPASS;
        self._reset(mark)
        return None;

    @memoize
    def _loop1_1(self) -> Optional[Any]:
        # _loop1_1: statement_group
        mark = self._mark()
        children = []
        while (
            (statement_group := self.statement_group())
        ):
            children.append(statement_group)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _loop0_3(self) -> Optional[Any]:
        # _loop0_3: (','+) statement
        mark = self._mark()
        children = []
        while (
            (self._loop1_12())
            and
            (elem := self.statement())
        ):
            children.append(elem)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _gather_2(self) -> Optional[Any]:
        # _gather_2: statement _loop0_3
        mark = self._mark()
        if (
            (elem := self.statement())
            is not None
            and
            (seq := self._loop0_3())
            is not None
        ):
            return [elem] + seq;
        self._reset(mark)
        return None;

    @memoize
    def _loop0_4(self) -> Optional[Any]:
        # _loop0_4: ','
        mark = self._mark()
        children = []
        while (
            (literal := self.expect(','))
        ):
            children.append(literal)
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
    def _loop1_9(self) -> Optional[Any]:
        # _loop1_9: (('<<' | '>>') comparison)
        mark = self._mark()
        children = []
        while (
            (_tmp_13 := self._tmp_13())
        ):
            children.append(_tmp_13)
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
    def _loop0_11(self) -> Optional[Any]:
        # _loop0_11: expr
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
    def _loop1_12(self) -> Optional[Any]:
        # _loop1_12: ','
        mark = self._mark()
        children = []
        while (
            (literal := self.expect(','))
        ):
            children.append(literal)
            mark = self._mark()
        self._reset(mark)
        return children;

    @memoize
    def _tmp_13(self) -> Optional[Any]:
        # _tmp_13: ('<<' | '>>') comparison
        mark = self._mark()
        if (
            (_tmp_14 := self._tmp_14())
            and
            (comparison := self.comparison())
        ):
            return [_tmp_14, comparison];
        self._reset(mark)
        return None;

    @memoize
    def _tmp_14(self) -> Optional[Any]:
        # _tmp_14: '<<' | '>>'
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
