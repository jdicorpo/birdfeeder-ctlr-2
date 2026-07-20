# Birdfeeder testbench

Cocotb tests for the door FSM (`birdfeeder_top`) and SG90 PWM driver.

## Signals

| TB wire | Source | Meaning |
|---------|--------|---------|
| `trigger` | `ui_in[0]` | Rising edge starts open→hold→close |
| `pest` | `ui_in[1]` | Forces close from OPENING/OPEN |
| `pwm_out` | `uo_out[0]` | Servo PWM |
| `servo_cmd` | `uo_out[2:1]` | 00 stop / 01 open / 10 close |
| `state` | `uo_out[5:3]` | 0 idle, 1 opening, 2 open, 3 closing |
| `busy` | `uo_out[6]` | Not idle |
| `door_open` | `uo_out[7]` | In OPEN hold |

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
