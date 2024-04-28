PYTHON = "$(shell (which python3 2>/dev/null || which python 2>/dev/null) | head -1)"

prep_executable = $(eval $(1) := $(shell bash ./prep_exec.sh $(2)))

.PHONY: install
install:
	python3 -m pip install -e .

.PHONY: com
com: console_lib ralib_display_lib
	$(PYTHON) -m slabes tests/compile/all.slb
	$(PYTHON) -m slabes tests/compile/robot.slb

.PHONY: console_lib
console_lib:
	clang -shared -fPIC -o slabes/libslabes/console_display.so slabes/libslabes/console_display.c slabes/libslabes/slabes.c -l ltdl

.PHONY: ralib_display_lib
ralib_display_lib:
	clang -shared -fPIC -o slabes/libslabes/raylib_display.so slabes/libslabes/raylib_display.c slabes/libslabes/slabes.c -l ltdl -l raylib

.PHONY: run
run:
	$(call prep_executable, EXEC, ./tests/compile/all.out)
	$(EXEC)

.PHONY: generate_parser
generate_parser:
	python -m slabes.generate_parser
