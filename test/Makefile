# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
WAVES ?= 1
TOPLEVEL_LANG ?= verilog
SRC_DIR = $(PWD)/../src
PROJECT_SOURCES = project.v birdfeeder_top.v sg90_continuous_pwm.v

# Fast RTL timing: 100 kHz clock, 1/2/1 ms door phases
SIM_CLK_FREQ     ?= 100000
SIM_OPEN_TIME_MS ?= 1
SIM_HOLD_TIME_MS ?= 2
SIM_CLOSE_TIME_MS?= 1

ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD				= sim_build/rtl
VERILOG_SOURCES += $(addprefix $(SRC_DIR)/,$(PROJECT_SOURCES))
COMPILE_ARGS 		+= -Ptt_um_jdicorpo_birdfeeder.CLK_FREQ=$(SIM_CLK_FREQ)
COMPILE_ARGS 		+= -Ptt_um_jdicorpo_birdfeeder.OPEN_TIME_MS=$(SIM_OPEN_TIME_MS)
COMPILE_ARGS 		+= -Ptt_um_jdicorpo_birdfeeder.HOLD_TIME_MS=$(SIM_HOLD_TIME_MS)
COMPILE_ARGS 		+= -Ptt_um_jdicorpo_birdfeeder.CLOSE_TIME_MS=$(SIM_CLOSE_TIME_MS)

else

# Gate level simulation:
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DUSE_POWER_PINS
COMPILE_ARGS    += -DSIM
COMPILE_ARGS    += -DUNIT_DELAY=\#1
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += $(PWD)/gate_level_netlist.v

endif

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I$(SRC_DIR)

# Include the testbench sources:
VERILOG_SOURCES += $(PWD)/tb.v
TOPLEVEL = tb

# List test modules to run, separated by commas and without the .py suffix:
COCOTB_TEST_MODULES = test

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
