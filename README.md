![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# Birdfeeder

Tiny Tapeout Verilog design that opens and closes a birdfeeder hatch with an SG90 continuous-rotation servo.

- [Project datasheet notes](docs/info.md)
- Author: Jeff DiCorpo
- Top module: `tt_um_jdicorpo_birdfeeder` (wraps `birdfeeder_top`)
- Clock: 10 MHz

## How it works

A pest detection starts an **open → wait → close** cycle:

1. **OPENING** — drive open for 3 s  
2. **OPEN** — stay open while pest is asserted; after pest clears, wait **10 s**  
3. **CLOSING** — drive close for 3 s  
4. **IDLE** — stop and wait for the next pest event  

A rising edge on **trigger** during **OPEN** resets the 10 s wait timer (extends time open). Pest returning during **CLOSING** aborts the close and opens again.

Hold-to-run diagnostic switches jog the servo without starting a cycle:

- `diag_up` — drive open/up until released
- `diag_down` — drive close/down until released
- both held — cancel (no drive)

While a diagnostic switch is held, the automatic FSM is frozen.

| State | Display | Servo | Duration / condition |
|-------|---------|-------|----------------------|
| IDLE | `0` | stop | wait for pest |
| OPENING | `1` | open | 3 s |
| OPEN | `2` | open while pest / stop while waiting | pest held, then 10 s wait |
| CLOSING | `3` | close | 3 s |

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
| `ui_in[0]` | trigger | Rising edge resets open-wait timer (or use `uio[1]`) |
| `ui_in[1]` | pest | Starts/holds open cycle (or use `uio[2]`) |
| `ui_in[2]` | diag_up | Hold to jog servo open/up |
| `ui_in[3]` | diag_down | Hold to jog servo close/down |
| `uo_out[6:0]` | seg_a…seg_g | 8-segment digit for FSM state |
| `uo_out[7]` | dp | Decimal point while PWM active |
| `uio[0]` | pwm_out | SG90 PWM (enabled when active) |
| `uio[1]` | trigger_alt | Alternate trigger input (OE off) |
| `uio[2]` | pest_alt | Alternate pest input (OE off) |

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

RTL sims use a 100 kHz clock and short door timings so the suite finishes quickly. See [test/README.md](test/README.md).

## Hardware

- 8-segment LED on `uo_out` (Tiny Tapeout demoboard mapping)
- SG90 continuous-rotation servo on bidirectional `uio[0]`
- Pest sensor on `ui_in[1]` **or** `uio[2]` (OR'd)
- Detection-arm / activity switch on `ui_in[0]` **or** `uio[1]` (resets wait)
- Diagnostic up/down switches on `ui_in[2]` / `ui_in[3]`

### Switch wiring

**Onboard `ui_in` piano switches** already include board pull-downs — use those for bench testing with no extra parts.

**External switches on `uio[1]` / `uio[2]`** (PMOD) do **not** share those pull-downs. Wire active-high:

1. Pulldown (~10k) from the GPIO to GND  
2. Switch between the GPIO and 3.3V  

Leave unused `ui_in` bits low (switches off) so they don’t hold the OR high.

## Tiny Tapeout

This repo uses the Tiny Tapeout GitHub Actions to build GDS, docs, FPGA bitstream, and run cocotb tests via [LibreLane](https://www.zerotoasiccourse.com/terminology/librelane/).

- [Enable GitHub Pages for the results viewer](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part)
- [FAQ](https://tinytapeout.com/faq/)
- [Submit to a shuttle](https://app.tinytapeout.com/)
- [Local hardening](https://www.tinytapeout.com/guides/local-hardening/)
