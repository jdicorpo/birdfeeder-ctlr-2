# SPDX-FileCopyrightText: © 2025 Jeff DiCorpo
# SPDX-License-Identifier: Apache-2.0

"""Cocotb tests for the birdfeeder door FSM + SG90 PWM.

RTL sims instantiate birdfeeder_top from tb.v with shortened timings:
  CLK_FREQ=100_000, OPEN/HOLD/CLOSE = 1/2/1 ms
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


# Must match timings in test/tb.v (RTL)
CLK_FREQ = 100_000
OPEN_TIME_MS = 1
HOLD_TIME_MS = 2
CLOSE_TIME_MS = 1

OPEN_TICKS = (CLK_FREQ // 1000) * OPEN_TIME_MS
HOLD_TICKS = (CLK_FREQ // 1000) * HOLD_TIME_MS
CLOSE_TICKS = (CLK_FREQ // 1000) * CLOSE_TIME_MS

ST_IDLE = 0
ST_OPENING = 1
ST_OPEN = 2
ST_CLOSING = 3

CMD_STOP = 0
CMD_OPEN = 1
CMD_CLOSE = 2

# uo[6:0] = {G,F,E,D,C,B,A}
SEG = {
    ST_IDLE: 0b0111111,
    ST_OPENING: 0b0000110,
    ST_OPEN: 0b1011011,
    ST_CLOSING: 0b1001111,
}

# 100 kHz -> 10 us period
CLK_PERIOD_NS = 10_000


def state_of(dut):
    return int(dut.user_project.state.value)


def cmd_of(dut):
    return int(dut.user_project.servo_cmd.value)


def seg_of(dut):
    return int(dut.seg.value)


async def reset_dut(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, unit="ns").start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 3)


async def set_inputs(dut, *, trigger=0, pest=0, diag_up=0, diag_down=0):
    dut.ui_in.value = (
        (int(diag_down) << 3)
        | (int(diag_up) << 2)
        | (int(pest) << 1)
        | int(trigger)
    )


async def settle_inputs(dut, cycles=3):
    """Wait for 2-FF synchronizers."""
    await ClockCycles(dut.clk, cycles)


async def pulse_trigger(dut):
    await set_inputs(dut, trigger=0, pest=0)
    await ClockCycles(dut.clk, 2)
    await set_inputs(dut, trigger=1, pest=0)
    for _ in range(8):
        await RisingEdge(dut.clk)
        if state_of(dut) == ST_OPENING:
            break
    else:
        assert False, f"expected OPENING after trigger, got state={state_of(dut)}"


async def wait_state(dut, expected, timeout_cycles):
    for _ in range(timeout_cycles):
        if state_of(dut) == expected:
            return
        await RisingEdge(dut.clk)
    assert False, f"timeout waiting for state {expected}, last={state_of(dut)}"


def assert_display(dut, expected_state, *, dp=None):
    assert state_of(dut) == expected_state
    assert seg_of(dut) == SEG[expected_state], (
        f"seg mismatch for state {expected_state}: "
        f"got {seg_of(dut):07b}, expected {SEG[expected_state]:07b}"
    )
    if dp is None:
        dp = 0 if expected_state == ST_IDLE else 1
    assert int(dut.dp.value) == dp


@cocotb.test()
async def test_idle_after_reset(dut):
    await reset_dut(dut)

    assert_display(dut, ST_IDLE)
    assert cmd_of(dut) == CMD_STOP
    assert int(dut.pwm_oe.value) == 0
    assert int(dut.uio_oe.value) == 0
    assert int(dut.pwm_out.value) == 0


@cocotb.test()
async def test_trigger_full_door_cycle(dut):
    """trigger: IDLE -> OPENING -> OPEN -> CLOSING -> IDLE"""
    await reset_dut(dut)
    await pulse_trigger(dut)

    assert_display(dut, ST_OPENING)
    assert cmd_of(dut) == CMD_OPEN
    assert int(dut.pwm_oe.value) == 1

    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)
    assert_display(dut, ST_OPEN)
    assert cmd_of(dut) == CMD_STOP
    assert int(dut.pwm_oe.value) == 1  # stop pulses while holding open

    await wait_state(dut, ST_CLOSING, HOLD_TICKS + 10)
    assert_display(dut, ST_CLOSING)
    assert cmd_of(dut) == CMD_CLOSE
    assert int(dut.pwm_oe.value) == 1

    await wait_state(dut, ST_IDLE, CLOSE_TICKS + 10)
    assert_display(dut, ST_IDLE)
    assert cmd_of(dut) == CMD_STOP
    assert int(dut.pwm_oe.value) == 0
    assert int(dut.pwm_out.value) == 0


@cocotb.test()
async def test_pest_aborts_open_hold(dut):
    """pest while OPEN forces CLOSING, then IDLE."""
    await reset_dut(dut)
    await pulse_trigger(dut)
    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)

    await set_inputs(dut, trigger=0, pest=1)
    await wait_state(dut, ST_CLOSING, 10)
    assert_display(dut, ST_CLOSING)
    assert cmd_of(dut) == CMD_CLOSE

    await wait_state(dut, ST_IDLE, CLOSE_TICKS + 10)
    assert_display(dut, ST_IDLE)


@cocotb.test()
async def test_pest_aborts_opening(dut):
    """pest during OPENING skips hold and closes immediately."""
    await reset_dut(dut)
    await pulse_trigger(dut)
    assert_display(dut, ST_OPENING)

    await set_inputs(dut, trigger=0, pest=1)
    await wait_state(dut, ST_CLOSING, 10)
    assert_display(dut, ST_CLOSING)

    await wait_state(dut, ST_IDLE, CLOSE_TICKS + 10)
    assert_display(dut, ST_IDLE)


@cocotb.test()
async def test_trigger_ignored_while_busy(dut):
    """A second trigger during OPENING must not restart the cycle."""
    await reset_dut(dut)
    await pulse_trigger(dut)
    assert state_of(dut) == ST_OPENING

    await set_inputs(dut, trigger=0, pest=0)
    await ClockCycles(dut.clk, 2)
    await set_inputs(dut, trigger=1, pest=0)
    await ClockCycles(dut.clk, 4)

    assert state_of(dut) == ST_OPENING
    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)
    await wait_state(dut, ST_CLOSING, HOLD_TICKS + 10)
    await wait_state(dut, ST_IDLE, CLOSE_TICKS + 10)


@cocotb.test()
async def test_pwm_on_bidir_during_open(dut):
    """While OPENING, pwm on uio[0] should go high early in the frame."""
    await reset_dut(dut)
    await pulse_trigger(dut)
    assert cmd_of(dut) == CMD_OPEN
    assert int(dut.pwm_oe.value) == 1

    saw_high = False
    for _ in range(50):
        if int(dut.pwm_out.value) == 1:
            saw_high = True
            break
        await RisingEdge(dut.clk)

    assert saw_high, "pwm_out on uio[0] never went high during OPENING"


@cocotb.test()
async def test_diag_up_hold_to_run(dut):
    """diag_up drives open while held, then disables PWM on release."""
    await reset_dut(dut)

    await set_inputs(dut, diag_up=1)
    await settle_inputs(dut)

    assert state_of(dut) == ST_IDLE
    assert cmd_of(dut) == CMD_OPEN
    assert int(dut.pwm_oe.value) == 1
    assert int(dut.dp.value) == 1

    await set_inputs(dut, diag_up=0)
    await settle_inputs(dut)

    assert state_of(dut) == ST_IDLE
    assert cmd_of(dut) == CMD_STOP
    assert int(dut.pwm_oe.value) == 0
    assert int(dut.dp.value) == 0


@cocotb.test()
async def test_diag_down_hold_to_run(dut):
    """diag_down drives close while held, then disables PWM on release."""
    await reset_dut(dut)

    await set_inputs(dut, diag_down=1)
    await settle_inputs(dut)

    assert state_of(dut) == ST_IDLE
    assert cmd_of(dut) == CMD_CLOSE
    assert int(dut.pwm_oe.value) == 1

    await set_inputs(dut, diag_down=0)
    await settle_inputs(dut)

    assert cmd_of(dut) == CMD_STOP
    assert int(dut.pwm_oe.value) == 0


@cocotb.test()
async def test_diag_both_cancel(dut):
    """Holding both diagnostic switches cancels the override."""
    await reset_dut(dut)

    await set_inputs(dut, diag_up=1, diag_down=1)
    await settle_inputs(dut)

    assert state_of(dut) == ST_IDLE
    assert cmd_of(dut) == CMD_STOP
    assert int(dut.pwm_oe.value) == 0


@cocotb.test()
async def test_diag_freezes_automatic_cycle(dut):
    """Holding diag_up during OPENING freezes the FSM timer."""
    await reset_dut(dut)
    await pulse_trigger(dut)
    assert state_of(dut) == ST_OPENING

    await set_inputs(dut, diag_up=1)
    await settle_inputs(dut)
    assert cmd_of(dut) == CMD_OPEN

    # Wait longer than an open phase; state should remain OPENING
    await ClockCycles(dut.clk, OPEN_TICKS + 20)
    assert state_of(dut) == ST_OPENING

    await set_inputs(dut, diag_up=0)
    await settle_inputs(dut)
    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)
