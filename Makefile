PYTHON = "$(shell (which python3 2>/dev/null || which python 2>/dev/null) | head -1)"

prep_executable = $(eval $(1) := $(shell bash ./prep_exec.sh $(2)))

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
