from . import lexer

from pegen.__main__ import main
import sys

sys.argv = "pegen -q slabes/slabes.gram -o slabes/slabes_parser.py".split(" ")
main()
