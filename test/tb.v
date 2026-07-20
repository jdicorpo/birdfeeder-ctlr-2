`default_nettype none
`timescale 1ns / 1ps

/* Birdfeeder door controller testbench.
 * Instantiates the Tiny Tapeout top and exposes named wires for cocotb / waves.
 *
 * RTL sims use a fast clock / short door timings so cocotb finishes quickly.
 * Gate-level sims use the hardened netlist as-is.
 */
module tb ();

  initial begin
    $dumpfile("tb.vcd");
    $dumpvars(0, tb);
    #1;
  end

  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;

  // Named aliases matching birdfeeder_top pinout
  wire       trigger    = ui_in[0];
  wire       pest       = ui_in[1];
  wire       pwm_out    = uo_out[0];
  wire [1:0] servo_cmd  = uo_out[2:1];
  wire [2:0] state      = uo_out[5:3];
  wire       busy       = uo_out[6];
  wire       door_open  = uo_out[7];

`ifdef GL_TEST
  wire VPWR = 1'b1;
  wire VGND = 1'b0;

  tt_um_jdicorpo_birdfeeder user_project (
      .VPWR(VPWR),
      .VGND(VGND),
      .ui_in  (ui_in),
      .uo_out (uo_out),
      .uio_in (uio_in),
      .uio_out(uio_out),
      .uio_oe (uio_oe),
      .ena    (ena),
      .clk    (clk),
      .rst_n  (rst_n)
  );
`else
  // Instantiate the design top with short timings (do not rely on iverilog -P).
  birdfeeder_top #(
      .CLK_FREQ(100_000),
      .OPEN_TIME_MS(1),
      .HOLD_TIME_MS(2),
      .CLOSE_TIME_MS(1)
  ) user_project (
      .ui_in  (ui_in),
      .uo_out (uo_out),
      .uio_in (uio_in),
      .uio_out(uio_out),
      .uio_oe (uio_oe),
      .ena    (ena),
      .clk    (clk),
      .rst_n  (rst_n)
  );
`endif

endmodule
