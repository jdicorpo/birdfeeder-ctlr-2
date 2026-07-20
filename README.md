![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# Birdfeeder

Tiny Tapeout Verilog design that opens and closes a birdfeeder hatch with an SG90 continuous-rotation servo.

- [Project datasheet notes](docs/info.md)
- Author: Jeff DiCorpo
- Top module: `tt_um_jdicorpo_birdfeeder` (wraps `birdfeeder_top`)
- Clock: 10 MHz

## How it works

A rising edge on `trigger` starts an open → hold → close cycle. `pest` forces an immediate close if the door is opening or already open.

Hold-to-run diagnostic switches jog the servo without starting a cycle:

- `diag_up` — drive open/up until released
- `diag_down` — drive close/down until released
- both held — cancel (no drive)

While a diagnostic switch is held, the automatic FSM is frozen.

| State | Display | Servo | Duration |
|-------|---------|-------|----------|
| IDLE | `0` | stop | wait for trigger |
| OPENING | `1` | open | 800 ms |
| OPEN | `2` | stop | 2 s |
| CLOSING | `3` | close | 800 ms |

The decimal point lights whenever PWM is active (automatic cycle or diagnostic jog).

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
| `ui_in[2]` | diag_up | Hold to jog servo open/up |
| `ui_in[3]` | diag_down | Hold to jog servo close/down |
| `uo_out[6:0]` | seg_a…seg_g | 8-segment digit for FSM state |
| `uo_out[7]` | dp | Decimal point while PWM active |
| `uio[0]` | pwm_out | SG90 PWM (enabled when active) |

## Source layout

| File | Role |
|------|------|
| `src/project.v` | Tiny Tapeout `tt_um_*` wrapper |
| `src/birdfeeder_top.v` | Door FSM + 8-segment display |
| `src/sg90_continuous_pwm.v` | 50 Hz SG90 PWM generator |

## Simulation

```sh
cd test
make -B
```

RTL sims use a 100 kHz clock and 1/2/1 ms door timings so the suite finishes quickly. See [test/README.md](test/README.md).

## Hardware

- 8-segment LED on `uo_out` (Tiny Tapeout demoboard mapping)
- SG90 continuous-rotation servo on bidirectional `uio[0]`
- Trigger input (button, bird sensor, etc.) on `ui_in[0]`
- Optional pest / close sensor on `ui_in[1]`
- Diagnostic up/down switches on `ui_in[2]` / `ui_in[3]`

## Tiny Tapeout

This repo uses the Tiny Tapeout GitHub Actions to build GDS, docs, FPGA bitstream, and run cocotb tests via [LibreLane](https://www.zerotoasiccourse.com/terminology/librelane/).

- [Enable GitHub Pages for the results viewer](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part)
- [FAQ](https://tinytapeout.com/faq/)
- [Submit to a shuttle](https://app.tinytapeout.com/)
- [Local hardening](https://www.tinytapeout.com/guides/local-hardening/)
