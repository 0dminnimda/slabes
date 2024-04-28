PYTHON = "$(shell (which python3 2>/dev/null || which python 2>/dev/null) | head -1)"

prep_executable = $(eval $(1) := $(shell bash ./prep_exec.sh $(2)))

.PHONY: install
install: get_libtool
	python3 -m pip install -e .

.PHONY: com
com:
	$(PYTHON) -m slabes tests/compile/all.slb

.PHONY: run
run:
	$(call prep_executable, EXEC, ./tests/compile/all.out)
	$(EXEC)

.PHONY: generate_parser
generate_parser:
	python -m slabes.generate_parser

.PHONY: get_libtool
get_libtool:
	(cd slabes && git clone git://git.savannah.gnu.org/libtool.git --depth 1)
