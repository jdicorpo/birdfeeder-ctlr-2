<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.
-->

## How it works

`birdfeeder_top` drives an SG90 continuous-rotation servo from a **single detection-arm switch**.

Cycle:

1. **OPENING** (display `1`) — open for 3 s  
2. **OPEN** (display `2`) — hold position (neutral/stop PWM) while the switch is closed; after release, wait 10 s  
3. **CLOSING** (display `3`) — close for 3 s  
4. **IDLE** (display `0`) — wait for the next arm trip  

Re-closing the arm during the wait restarts the 10 s timer. Tripping the arm during close aborts and reopens.

Arm input (OR'd, active-high): `ui_in[1]` **or** `uio[1]` (`uio[1]` OE off).

Diagnostic jog: `diag_up` / `diag_down` on `ui_in[2]` / `ui_in[3]`.

Servo commands: stop 1.5 ms, open 2.0 ms, close 1.0 ms. Clock 10 MHz.

## How to test

1. Assert the arm (`ui_in[1]` or `uio[1]`) to open; keep it closed to hold.  
2. Release and wait 10 s (or re-close briefly to restart the wait).  
3. Confirm close then idle.  
4. Use diag switches to jog the servo.

## External hardware

- 8-segment LED on `uo_out`
- SG90 on `uio[0]`
- One detection-arm switch on `ui_in[1]` or `uio[1]` (external bidir needs its own pulldown)
- Optional diag switches on `ui_in[2]` / `ui_in[3]`
