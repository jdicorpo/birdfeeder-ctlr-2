# Birdfeeder testbench

Cocotb tests for the door FSM (`birdfeeder_top`) and SG90 PWM driver.

## Signals

| TB wire | Source | Meaning |
|---------|--------|---------|
| `trigger` | `ui_in[0]` | Rising edge starts open→hold→close |
| `pest` | `ui_in[1]` | Forces close from OPENING/OPEN |
| `diag_up` | `ui_in[2]` | Hold to jog servo open/up |
| `diag_down` | `ui_in[3]` | Hold to jog servo close/down |
| `seg` | `uo_out[6:0]` | 7-seg digit for FSM state |
| `dp` | `uo_out[7]` | PWM active (decimal point) |
| `pwm_out` | `uio_out[0]` | Servo PWM |
| `pwm_oe` | `uio_oe[0]` | PWM OE (off when inactive) |

## How to run

RTL simulation (uses a 100 kHz clock and 1/2/1 ms door timings):

```sh
make -B
```

Gate-level simulation (after hardening; copy the GL netlist to `gate_level_netlist.v`):

```sh
make -B GATES=yes
```

## Waves

```sh
gtkwave tb.vcd tb.gtkw
# or
surfer tb.vcd
```
