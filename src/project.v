/*
 * Copyright (c) 2025 Jeff DiCorpo
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Tiny Tapeout requires a tt_um_* top module name.
// Design logic lives in birdfeeder_top.
module tt_um_jdicorpo_birdfeeder #(
    parameter CLK_FREQ      = 10_000_000,
    parameter OPEN_TIME_MS  = 3000,
    parameter HOLD_TIME_MS  = 2000,
    parameter CLOSE_TIME_MS = 3000
) (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

  birdfeeder_top #(
      .CLK_FREQ(CLK_FREQ),
      .OPEN_TIME_MS(OPEN_TIME_MS),
      .HOLD_TIME_MS(HOLD_TIME_MS),
      .CLOSE_TIME_MS(CLOSE_TIME_MS)
  ) birdfeeder (
      .ui_in(ui_in),
      .uo_out(uo_out),
      .uio_in(uio_in),
      .uio_out(uio_out),
      .uio_oe(uio_oe),
      .ena(ena),
      .clk(clk),
      .rst_n(rst_n)
  );

endmodule
