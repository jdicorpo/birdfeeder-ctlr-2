# SPDX-FileCopyrightText: © 2025 Jeff DiCorpo
# SPDX-License-Identifier: Apache-2.0

"""Cocotb tests for the birdfeeder door FSM + SG90 PWM.

RTL sims: CLK_FREQ=100_000, OPEN/WAIT/CLOSE = 1/3/1 ms
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge


CLK_FREQ = 100_000
OPEN_TIME_MS = 1
WAIT_TIME_MS = 3
CLOSE_TIME_MS = 1

OPEN_TICKS = (CLK_FREQ // 1000) * OPEN_TIME_MS
WAIT_TICKS = (CLK_FREQ // 1000) * WAIT_TIME_MS
CLOSE_TICKS = (CLK_FREQ // 1000) * CLOSE_TIME_MS

ST_IDLE = 0
ST_OPENING = 1
ST_OPEN = 2
ST_CLOSING = 3

CMD_STOP = 0
CMD_OPEN = 1
CMD_CLOSE = 2

SEG = {
    ST_IDLE: 0b0111111,
    ST_OPENING: 0b0000110,
    ST_OPEN: 0b1011011,
    ST_CLOSING: 0b1001111,
}

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


async def set_inputs(dut, *, arm=0, diag_up=0, diag_down=0):
    dut.ui_in.value = (int(diag_down) << 3) | (int(diag_up) << 2) | (int(arm) << 1)


async def settle_inputs(dut, cycles=3):
    await ClockCycles(dut.clk, cycles)


async def start_arm_cycle(dut):
    await set_inputs(dut, arm=1)
    await settle_inputs(dut)
    assert state_of(dut) == ST_OPENING


async def wait_state(dut, expected, timeout_cycles):
    for _ in range(timeout_cycles):
        if state_of(dut) == expected:
            return
        await RisingEdge(dut.clk)
    assert False, f"timeout waiting for state {expected}, last={state_of(dut)}"


def assert_display(dut, expected_state, *, dp=None):
    assert state_of(dut) == expected_state
    assert seg_of(dut) == SEG[expected_state]
    if dp is None:
        dp = 0 if expected_state == ST_IDLE else 1
    assert int(dut.dp.value) == dp


@cocotb.test()
async def test_idle_after_reset(dut):
    await reset_dut(dut)
    assert_display(dut, ST_IDLE)
    assert cmd_of(dut) == CMD_STOP
    assert int(dut.pwm_oe.value) == 0


@cocotb.test()
async def test_arm_full_cycle(dut):
    """arm: OPENING -> OPEN (held) -> wait -> CLOSING -> IDLE"""
    await reset_dut(dut)
    await start_arm_cycle(dut)
    assert cmd_of(dut) == CMD_OPEN

    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)
    assert cmd_of(dut) == CMD_STOP  # hold position

    await set_inputs(dut, arm=0)
    await settle_inputs(dut)
    assert state_of(dut) == ST_OPEN

    await wait_state(dut, ST_CLOSING, WAIT_TICKS + 10)
    assert cmd_of(dut) == CMD_CLOSE

    await wait_state(dut, ST_IDLE, CLOSE_TICKS + 10)
    assert int(dut.pwm_oe.value) == 0


@cocotb.test()
async def test_arm_holds_open_until_released(dut):
    await reset_dut(dut)
    await start_arm_cycle(dut)
    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)

    await ClockCycles(dut.clk, WAIT_TICKS + 50)
    assert state_of(dut) == ST_OPEN
    assert cmd_of(dut) == CMD_STOP


@cocotb.test()
async def test_arm_reclose_resets_wait(dut):
    """Closing the arm again during wait restarts the 10 s countdown."""
    await reset_dut(dut)
    await start_arm_cycle(dut)
    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)

    await set_inputs(dut, arm=0)
    await settle_inputs(dut)
    await ClockCycles(dut.clk, WAIT_TICKS - 2)
    assert state_of(dut) == ST_OPEN

    await set_inputs(dut, arm=1)
    await settle_inputs(dut)
    await set_inputs(dut, arm=0)
    await settle_inputs(dut)

    await ClockCycles(dut.clk, WAIT_TICKS - 2)
    assert state_of(dut) == ST_OPEN
    await wait_state(dut, ST_CLOSING, 20)


@cocotb.test()
async def test_arm_aborts_closing(dut):
    await reset_dut(dut)
    await start_arm_cycle(dut)
    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)
    await set_inputs(dut, arm=0)
    await settle_inputs(dut)
    await wait_state(dut, ST_CLOSING, WAIT_TICKS + 10)

    await set_inputs(dut, arm=1)
    await settle_inputs(dut)
    assert state_of(dut) == ST_OPENING
    assert cmd_of(dut) == CMD_OPEN


@cocotb.test()
async def test_pwm_on_bidir_during_open(dut):
    await reset_dut(dut)
    await start_arm_cycle(dut)

    saw_high = False
    for _ in range(50):
        if int(dut.pwm_out.value) == 1:
            saw_high = True
            break
        await RisingEdge(dut.clk)
    assert saw_high


@cocotb.test()
async def test_arm_via_uio_alt(dut):
    """Detection arm on uio[1] starts the cycle."""
    await reset_dut(dut)
    dut.uio_in.value = 0b010
    await settle_inputs(dut)
    assert state_of(dut) == ST_OPENING


@cocotb.test()
async def test_diag_up_hold_to_run(dut):
    await reset_dut(dut)
    await set_inputs(dut, diag_up=1)
    await settle_inputs(dut)
    assert state_of(dut) == ST_IDLE
    assert cmd_of(dut) == CMD_OPEN
    await set_inputs(dut, diag_up=0)
    await settle_inputs(dut)
    assert cmd_of(dut) == CMD_STOP


@cocotb.test()
async def test_diag_down_hold_to_run(dut):
    await reset_dut(dut)
    await set_inputs(dut, diag_down=1)
    await settle_inputs(dut)
    assert cmd_of(dut) == CMD_CLOSE
    await set_inputs(dut, diag_down=0)
    await settle_inputs(dut)
    assert cmd_of(dut) == CMD_STOP


@cocotb.test()
async def test_diag_both_cancel(dut):
    await reset_dut(dut)
    await set_inputs(dut, diag_up=1, diag_down=1)
    await settle_inputs(dut)
    assert cmd_of(dut) == CMD_STOP


@cocotb.test()
async def test_diag_freezes_automatic_cycle(dut):
    await reset_dut(dut)
    await start_arm_cycle(dut)
    await set_inputs(dut, arm=1, diag_up=1)
    await settle_inputs(dut)
    await ClockCycles(dut.clk, OPEN_TICKS + 20)
    assert state_of(dut) == ST_OPENING
    await set_inputs(dut, arm=1, diag_up=0)
    await settle_inputs(dut)
    await wait_state(dut, ST_OPEN, OPEN_TICKS + 10)
