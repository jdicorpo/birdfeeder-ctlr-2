# SPDX-FileCopyrightText: © 2025 Jeff DiCorpo
# SPDX-License-Identifier: Apache-2.0

"""Cocotb tests for the birdfeeder door FSM + SG90 PWM.

RTL sims instantiate birdfeeder_top from tb.v with shortened timings:
  CLK_FREQ=100_000, OPEN/HOLD/CLOSE = 1/2/1 ms
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


# Must match SIM_* overrides in test/Makefile (RTL)
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

# 100 kHz -> 10 us period
CLK_PERIOD_NS = 10_000


def state_of(dut):
    return int(dut.state.value)


def cmd_of(dut):
    return int(dut.servo_cmd.value)


async def reset_dut(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_NS, unit="ns").start())

    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    # Synchronizers need 2 flops; give an extra cycle of margin
    await ClockCycles(dut.clk, 3)


async def set_inputs(dut, *, trigger=0, pest=0):
    dut.ui_in.value = (int(pest) << 1) | int(trigger)


async def pulse_trigger(dut):
    """Generate a rising edge on trigger, then release."""
    await set_inputs(dut, trigger=0, pest=0)
    await ClockCycles(dut.clk, 2)
    await set_inputs(dut, trigger=1, pest=0)
    # Wait for synchronizer + edge detect to enter OPENING
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


@cocotb.test()
async def test_idle_after_reset(dut):
    await reset_dut(dut)

    assert state_of(dut) == ST_IDLE
    assert cmd_of(dut) == CMD_STOP
    assert int(dut.busy.value) == 0
    assert int(dut.door_open.value) == 0
    assert int(dut.uio_out.value) == 0
    assert int(dut.uio_oe.value) == 0


@cocotb.test()
async def test_trigger_full_door_cycle(dut):
    """trigger: IDLE -> OPENING -> OPEN -> CLOSING -> IDLE"""
    await reset_dut(dut)
    await pulse_trigger(dut)

    assert cmd_of(dut) == CMD_OPEN
    assert int(dut.busy.value) == 1
    assert int(dut.door_open.value) == 0

    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)
    assert cmd_of(dut) == CMD_STOP
    assert int(dut.door_open.value) == 1

    await wait_state(dut, ST_CLOSING, HOLD_TICKS + 10)
    assert cmd_of(dut) == CMD_CLOSE
    assert int(dut.door_open.value) == 0

    await wait_state(dut, ST_IDLE, CLOSE_TICKS + 10)
    assert cmd_of(dut) == CMD_STOP
    assert int(dut.busy.value) == 0


@cocotb.test()
async def test_pest_aborts_open_hold(dut):
    """pest while OPEN forces CLOSING, then IDLE."""
    await reset_dut(dut)
    await pulse_trigger(dut)
    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)

    await set_inputs(dut, trigger=0, pest=1)
    await wait_state(dut, ST_CLOSING, 10)
    assert cmd_of(dut) == CMD_CLOSE

    await wait_state(dut, ST_IDLE, CLOSE_TICKS + 10)
    assert cmd_of(dut) == CMD_STOP


@cocotb.test()
async def test_pest_aborts_opening(dut):
    """pest during OPENING skips hold and closes immediately."""
    await reset_dut(dut)
    await pulse_trigger(dut)
    assert state_of(dut) == ST_OPENING

    await set_inputs(dut, trigger=0, pest=1)
    await wait_state(dut, ST_CLOSING, 10)
    assert cmd_of(dut) == CMD_CLOSE

    await wait_state(dut, ST_IDLE, CLOSE_TICKS + 10)


@cocotb.test()
async def test_trigger_ignored_while_busy(dut):
    """A second trigger during OPENING must not restart the cycle."""
    await reset_dut(dut)
    await pulse_trigger(dut)
    assert state_of(dut) == ST_OPENING

    # Extra trigger edges while opening
    await set_inputs(dut, trigger=0, pest=0)
    await ClockCycles(dut.clk, 2)
    await set_inputs(dut, trigger=1, pest=0)
    await ClockCycles(dut.clk, 4)

    assert state_of(dut) == ST_OPENING
    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)
    await wait_state(dut, ST_CLOSING, HOLD_TICKS + 10)
    await wait_state(dut, ST_IDLE, CLOSE_TICKS + 10)


@cocotb.test()
async def test_pwm_active_during_open_command(dut):
    """While OPENING, pwm_out should go high early in the 20 ms frame."""
    await reset_dut(dut)
    await pulse_trigger(dut)
    assert cmd_of(dut) == CMD_OPEN

    # At 100 kHz, a 20 ms PWM period is 2000 clocks; pulse is 2.0 ms = 200 clocks.
    # Sample soon after entering OPENING — line should be high.
    saw_high = False
    for _ in range(50):
        if int(dut.pwm_out.value) == 1:
            saw_high = True
            break
        await RisingEdge(dut.clk)

    assert saw_high, "pwm_out never went high during OPENING"
