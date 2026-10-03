<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

`birdfeeder_top` runs a door state machine that drives an SG90 continuous-rotation servo over PWM on a bidirectional pin, and shows the FSM state on the 8-segment LED.

Pest detection starts an open → wait → close cycle:

1. **OPENING** (display `1`) — servo runs open for 3 s
2. **OPEN** (display `2`) — stay open while pest is asserted; after pest clears, wait 10 s (servo stopped)
3. **CLOSING** (display `3`) — servo runs close for 3 s
4. **IDLE** (display `0`) — servo stopped; wait for the next pest event

A rising edge on `trigger` during **OPEN** resets the 10 s wait timer. If pest asserts again during **CLOSING**, the close is aborted and the controller returns to **OPENING**.

Trigger and pest may come from either the dedicated inputs or the bidirectional port (OR'd, active-high):

- trigger = `ui_in[0]` **or** `uio[1]`
- pest = `ui_in[1]` **or** `uio[2]`

`uio[1]` / `uio[2]` are configured as inputs (`uio_oe` off). The onboard piano-switch pull-downs apply only to `ui_in`. For switches on the bidir PMOD, add an external ~10k pulldown to GND and switch to 3.3V.

Diagnostic hold-to-run switches:

- `diag_up` (`ui_in[2]`) — drive open/up while held
- `diag_down` (`ui_in[3]`) — drive close/down while held
- both held — cancel (no diagnostic drive)

While a diagnostic switch is active, the automatic FSM is frozen. PWM on `uio[0]` is enabled only during an automatic cycle or diagnostic jog (disabled in idle).

The decimal point (`uo_out[7]`) is lit whenever PWM is active.

Servo commands:

| cmd | Action | Pulse width |
|-----|--------|-------------|
| 00  | Stop   | 1.5 ms      |
| 01  | Open   | 2.0 ms      |
| 10  | Close  | 1.0 ms      |

The design expects a 10 MHz clock.

## How to test

1. Clock at 10 MHz.
2. Assert `ui_in[1]` (pest) to open; keep it high to hold open.
3. Release pest and wait 10 s (or pulse `ui_in[0]` to restart the wait).
4. Watch close for 3 s, then idle.
5. Hold `ui_in[2]` or `ui_in[3]` to jog the servo up/down until released.

## External hardware

- 8-segment LED on `uo_out[7:0]` (standard Tiny Tapeout / demoboard mapping)
- SG90 continuous rotation servo signal on bidirectional pin `uio[0]`
- Pest sensor on `ui_in[1]` or alternate `uio[2]`
- Detection-arm / activity switch on `ui_in[0]` or alternate `uio[1]` (resets wait)
- Diagnostic up/down switches on `ui_in[2]` / `ui_in[3]`
- External bidir switches need their own pulldown (board pulldowns are on `ui_in` only)
