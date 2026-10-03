# Birdfeeder testbench

| TB wire | Source | Meaning |
|---------|--------|---------|
| `arm` | `ui_in[1]` | Detection-arm switch |
| `arm_alt` | `uio_in[1]` | Alternate arm input |
| `diag_up` / `diag_down` | `ui_in[2]` / `[3]` | Manual jog |
| `seg` / `dp` | `uo_out` | Display |
| `pwm_out` / `pwm_oe` | `uio[0]` | Servo PWM |

```sh
make -B
```
