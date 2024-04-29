PYTHON = "$(shell (which python3 2>/dev/null || which python 2>/dev/null) | head -1)"

prep_executable = $(eval $(1) := $(shell bash ./prep_exec.sh $(2)))

DISPLAY = ":1"
NO_DISPLAY = ":0"

.PHONY: install
install:
	python3 -m pip install -e .

.PHONY: com
com: console_lib ralib_display_lib console_slabes raylib_slabes
	$(PYTHON) -m slabes tests/compile/all.slb
	$(PYTHON) -m slabes tests/compile/robot.slb

.PHONY: console_lib
console_lib:
	clang -shared -fPIC -o slabes/libslabes/console_display.so slabes/libslabes/console_display.c slabes/libslabes/slabes.c -l ltdl

.PHONY: ralib_display_lib
ralib_display_lib:
	clang -shared -fPIC -o slabes/libslabes/raylib_display.so slabes/libslabes/raylib_display.c slabes/libslabes/slabes.c -l ltdl -l raylib -l m

.PHONY: console_slabes
console_slabes:
	clang -o slabes/libslabes/slabes_console.out slabes/libslabes/slabes_console.c -l ltdl

.PHONY: raylib_slabes
raylib_slabes:
	clang -o slabes/libslabes/slabes_raylib.out slabes/libslabes/slabes_raylib.c -l ltdl -l raylib -l m

.PHONY: run
run:
	$(call prep_executable, EXEC, ./tests/compile/robot.out)
	$(EXEC)

.PHONY: run_con
run_con:
	$(call prep_executable, SLIB, ./slabes/libslabes/console_display.so)
	$(call prep_executable, EXEC, ./tests/compile/robot.out)
	$(EXEC) $(SLIB)

.PHONY: run_ray
run_ray:
	$(call prep_executable, SLIB, ./slabes/libslabes/raylib_display.so)
	$(call prep_executable, EXEC, ./tests/compile/robot.out)
	DISPLAY=$(DISPLAY) $(EXEC) $(SLIB)

.PHONY: run_con_sl
run_con_sl:
	$(call prep_executable, EXEC, ./slabes/libslabes/slabes_console.out)
	$(EXEC)

.PHONY: run_ray_sl
run_ray_sl:
	$(call prep_executable, EXEC, ./slabes/libslabes/slabes_raylib.out)
	DISPLAY=$(DISPLAY) $(EXEC)

# https://wiki.termux.com/wiki/Graphical_Environment
.PHONY: setup_termux_gui
setup_termux_gui:
	vncserver :1 -localhost

.PHONY: generate_parser
generate_parser:
	python -m slabes.generate_parser
