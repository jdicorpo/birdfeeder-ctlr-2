<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

`birdfeeder_top` runs a door state machine that drives an SG90 continuous-rotation servo over PWM on a bidirectional pin, and shows the FSM state on the 8-segment LED.

On a rising edge of `trigger` (`ui_in[0]`), the hatch cycles:

1. **OPENING** (display `1`) — servo runs open for 800 ms
2. **OPEN** (display `2`) — servo stops; door held open for 2 s
3. **CLOSING** (display `3`) — servo runs close for 800 ms
4. **IDLE** (display `0`) — servo stopped; wait for the next trigger

`pest` (`ui_in[1]`) is level-sensitive. If asserted during OPENING or OPEN, the FSM immediately enters CLOSING.

The decimal point (`uo_out[7]`) is lit whenever the controller is busy (not idle).

Servo commands:

| cmd | Action | Pulse width |
|-----|--------|-------------|
| 00  | Stop   | 1.5 ms      |
| 01  | Open   | 2.0 ms      |
| 10  | Close  | 1.0 ms      |

The design expects a 10 MHz clock.

## How to test

1. Clock at 10 MHz.
2. Pulse `ui_in[0]` high to start a door cycle.
3. Watch the 8-segment display (`uo_out`) show `0` → `1` → `2` → `3` → `0`.
4. Probe `uio[0]` for the servo PWM waveform.
5. Assert `ui_in[1]` during OPEN to force an early close.

## External hardware

- 8-segment LED on `uo_out[7:0]` (standard Tiny Tapeout / demoboard mapping)
- SG90 continuous rotation servo signal on bidirectional pin `uio[0]`
- Trigger source on `ui_in[0]` (button, bird sensor, etc.)
- Optional pest / close sensor on `ui_in[1]`
