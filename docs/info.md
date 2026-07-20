<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

`birdfeeder_top` runs a door state machine that drives an SG90 continuous-rotation servo over PWM.

On a rising edge of `trigger` (`ui_in[0]`), the hatch cycles:

1. **OPENING** — servo runs open for 800 ms
2. **OPEN** — servo stops; door held open for 2 s
3. **CLOSING** — servo runs close for 800 ms
4. **IDLE** — servo stopped; wait for the next trigger

`pest` (`ui_in[1]`) is level-sensitive. If asserted during OPENING or OPEN, the FSM immediately enters CLOSING.

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
3. Watch `uo_out[0]` (PWM), `uo_out[2:1]` (servo cmd), and `uo_out[5:3]` (state).
4. Assert `ui_in[1]` during OPEN to force an early close.

Status outputs:

| pin | meaning |
|-----|---------|
| uo[0] | pwm_out |
| uo[2:1] | servo_cmd |
| uo[5:3] | state (0=idle, 1=opening, 2=open, 3=closing) |
| uo[6] | busy |
| uo[7] | door_open |

## External hardware

- SG90 continuous rotation servo for the hatch
- Trigger source on `ui_in[0]` (button, bird sensor, etc.)
- Optional pest / close sensor on `ui_in[1]`
