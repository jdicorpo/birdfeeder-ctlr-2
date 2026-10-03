![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# Birdfeeder

Tiny Tapeout Verilog design that opens and closes a birdfeeder hatch with an SG90 continuous-rotation servo.

- [Project datasheet notes](docs/info.md)
- Author: Jeff DiCorpo
- Top module: `tt_um_jdicorpo_birdfeeder` (wraps `birdfeeder_top`)
- Clock: 10 MHz

## How it works

A single **detection-arm** switch runs an **open → wait → close** cycle:

1. **OPENING** — drive open for 3 s  
2. **OPEN** — hold position (neutral PWM) while the arm switch is closed; after release, wait **10 s**  
3. **CLOSING** — drive close for 3 s  
4. **IDLE** — stop until the arm trips again  

Closing the arm again during the 10 s wait restarts the wait. Tripping the arm during close aborts and reopens.

Hold-to-run diagnostic switches jog the servo without starting a cycle:

- `diag_up` — drive open/up until released
- `diag_down` — drive close/down until released
- both held — cancel (no drive)

| State | Display | Servo | Duration / condition |
|-------|---------|-------|----------------------|
| IDLE | `0` | stop | wait for arm |
| OPENING | `1` | open | 3 s |
| OPEN | `2` | stop (hold) | arm closed, then 10 s wait |
| CLOSING | `3` | close | 3 s |

PWM command encoding:

| cmd | Action | Pulse width |
|-----|--------|-------------|
| 00 | Stop | 1.5 ms |
| 01 | Open | 2.0 ms |
| 10 | Close | 1.0 ms |

## Pinout

| Pin | Name | Description |
|-----|------|-------------|
| `ui_in[1]` | arm | Detection-arm switch (or use `uio[1]`) |
| `ui_in[2]` | diag_up | Hold to jog servo open/up |
| `ui_in[3]` | diag_down | Hold to jog servo close/down |
| `uo_out[6:0]` | seg_a…seg_g | 8-segment digit for FSM state |
| `uo_out[7]` | dp | Decimal point while PWM active |
| `uio[0]` | pwm_out | SG90 PWM (enabled when active) |
| `uio[1]` | arm_alt | Alternate detection-arm input (OE off) |

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

See [test/README.md](test/README.md).

## Hardware

- 8-segment LED on `uo_out`
- SG90 continuous-rotation servo on `uio[0]`
- **One** detection-arm switch on `ui_in[1]` **or** `uio[1]` (OR'd)
- Diagnostic up/down on `ui_in[2]` / `ui_in[3]`

### Switch wiring

**Onboard `ui_in[1]` piano switch** already has a board pull-down.

**External switch on `uio[1]`:** add ~10k pulldown to GND, switch to 3.3V (active-high). Leave unused `ui_in` switches off.

## Tiny Tapeout

- [Enable GitHub Pages for the results viewer](https://tinytapeout.com/faq/#my-github-action-is-failing-on-the-pages-part)
- [FAQ](https://tinytapeout.com/faq/)
- [Submit to a shuttle](https://app.tinytapeout.com/)
- [Local hardening](https://www.tinytapeout.com/guides/local-hardening/)
