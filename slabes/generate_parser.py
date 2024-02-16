from . import lexer  # update the python tokens

from pegen.__main__ import main
import sys

sys.argv = "pegen -q slabes/slabes.peg -o slabes/slabes_parser.py".split(" ")
main()
