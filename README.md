![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# Birdfeeder

Tiny Tapeout Verilog design that opens and closes a birdfeeder hatch with an SG90 continuous-rotation servo.

- [Project datasheet notes](docs/info.md)
- Author: Jeff DiCorpo
- Top module: `tt_um_jdicorpo_birdfeeder` (wraps `birdfeeder_top`)
- Clock: 10 MHz

## How it works

A rising edge on `trigger` starts an open → hold → close cycle. `pest` forces an immediate close if the door is opening or already open.

| State | Servo | Duration |
|-------|-------|----------|
| IDLE | stop | wait for trigger |
| OPENING | open | 800 ms |
| OPEN | stop | 2 s |
| CLOSING | close | 800 ms |

PWM command encoding:

| cmd | Action | Pulse width |
|-----|--------|-------------|
| 00 | Stop | 1.5 ms |
| 01 | Open | 2.0 ms |
| 10 | Close | 1.0 ms |

## Pinout

| Pin | Name | Description |
|-----|------|-------------|
| `ui_in[0]` | trigger | Rising edge starts a door cycle |
| `ui_in[1]` | pest | Level-sensitive; forces close |
| `uo_out[0]` | pwm_out | SG90 signal |
| `uo_out[2:1]` | servo_cmd | Current PWM command |
| `uo_out[5:3]` | state | 0 idle, 1 opening, 2 open, 3 closing |
| `uo_out[6]` | busy | High when not idle |
| `uo_out[7]` | door_open | High during OPEN hold |

## Source layout

| File | Role |
|------|------|
| `src/project.v` | Tiny Tapeout `tt_um_*` wrapper |
| `src/birdfeeder_top.v` | Door FSM |
| `src/sg90_continuous_pwm.v` | 50 Hz SG90 PWM generator |

## Simulation

```sh
cd test
make -B
```

RTL sims use a 100 kHz clock and 1/2/1 ms door timings so the suite finishes quickly. See [test/README.md](test/README.md).

## Hardware

- SG90 continuous-rotation servo on `uo_out[0]`
- Trigger input (button, bird sensor, etc.) on `ui_in[0]`
- Optional pest / close sensor on `ui_in[1]`

## Tiny Tapeout

This repo uses the Tiny Tapeout GitHub Actions to build GDS, docs, FPGA bitstream, and run cocotb tests via [LibreLane](https://www.zerotoasiccourse.com/terminology/librelane/).

- [Enable GitHub Pages for the results viewer](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part)
- [FAQ](https://tinytapeout.com/faq/)
- [Submit to a shuttle](https://app.tinytapeout.com/)
- [Local hardening](https://www.tinytapeout.com/guides/local-hardening/)
