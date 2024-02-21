from __future__ import annotations
from dataclasses import dataclass

from .name_table import NameTable


@dataclass
class Eval:
    def init(self, context: ScopeContext) -> None:
        raise NotImplementedError

    def eval(self, context: ScopeContext) -> None:
        raise NotImplementedError


@dataclass
class ScopeContext(NameTable):
    pass
