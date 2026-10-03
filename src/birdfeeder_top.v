/*
 * Copyright (c) 2025 Jeff DiCorpo
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Door controller for a birdfeeder hatch driven by an SG90 continuous servo.
//
// Single detection-arm switch (pest):
//   open 3 s -> hold open while switch closed -> wait 10 s after release ->
//   close 3 s -> idle
// Re-closing the switch during the wait restarts the 10 s timer.
//
// ui_in[1] / uio[1] = arm/pest : level-sensitive detection-arm switch
// ui_in[2]          = diag_up  : hold to drive servo open/up until released
// ui_in[3]          = diag_down: hold to drive servo close/down until released
// uo_out            = 8-seg LED : digit shows FSM state; DP lit when PWM active
// uio[0]            = pwm_out  : SG90 signal (OE on only when PWM active)
// uio[1]            = arm_alt  : alternate detection-arm input (OE off)
module birdfeeder_top #(
    parameter CLK_FREQ      = 10_000_000,
    parameter OPEN_TIME_MS  = 3000,
    parameter WAIT_TIME_MS  = 10000,
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

  localparam integer OPEN_TICKS  = (CLK_FREQ / 1000) * OPEN_TIME_MS;
  localparam integer WAIT_TICKS  = (CLK_FREQ / 1000) * WAIT_TIME_MS;
  localparam integer CLOSE_TICKS = (CLK_FREQ / 1000) * CLOSE_TIME_MS;

  localparam [1:0] CMD_STOP  = 2'b00;
  localparam [1:0] CMD_OPEN  = 2'b01;
  localparam [1:0] CMD_CLOSE = 2'b10;

  localparam [2:0] ST_IDLE    = 3'd0;
  localparam [2:0] ST_OPENING = 3'd1;
  localparam [2:0] ST_OPEN    = 3'd2;
  localparam [2:0] ST_CLOSING = 3'd3;

  reg [2:0] state;
  reg [2:0] state_next;
  reg [31:0] timer;
  reg [31:0] timer_next;
  reg [1:0] fsm_cmd;

  reg [1:0] arm_sync;
  reg [1:0] diag_up_sync;
  reg [1:0] diag_down_sync;

  wire arm      = arm_sync[1];
  wire diag_up  = diag_up_sync[1];
  wire diag_down = diag_down_sync[1];

  wire diag_up_only   = diag_up & ~diag_down;
  wire diag_down_only = diag_down & ~diag_up;
  wire diag_override  = diag_up_only | diag_down_only;

  wire [1:0] servo_cmd = diag_up_only   ? CMD_OPEN  :
                         diag_down_only ? CMD_CLOSE :
                                          fsm_cmd;

  wire pwm_out;
  wire [6:0] seg;
  wire       busy = (state != ST_IDLE);
  wire       pwm_enable = busy | diag_override;

  // Single detection-arm switch: ui_in[1] or uio[1]
  wire arm_raw = ui_in[1] | uio_in[1];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      arm_sync       <= 2'b00;
      diag_up_sync   <= 2'b00;
      diag_down_sync <= 2'b00;
    end else begin
      arm_sync       <= {arm_sync[0], arm_raw};
      diag_up_sync   <= {diag_up_sync[0], ui_in[2]};
      diag_down_sync <= {diag_down_sync[0], ui_in[3]};
    end
  end

  always @(*) begin
    state_next = state;
    timer_next = timer;
    fsm_cmd    = CMD_STOP;

    case (state)
      ST_IDLE: begin
        fsm_cmd = CMD_STOP;
        if (arm) begin
          state_next = ST_OPENING;
          timer_next = 32'd0;
        end
      end

      ST_OPENING: begin
        fsm_cmd = CMD_OPEN;
        if (timer >= OPEN_TICKS - 1) begin
          state_next = ST_OPEN;
          timer_next = 32'd0;
        end else begin
          timer_next = timer + 1'b1;
        end
      end

      ST_OPEN: begin
        // Hold position (neutral PWM) after travel completes
        fsm_cmd = CMD_STOP;
        if (arm) begin
          // Switch still closed: stay open; wait starts only after release
          state_next = ST_OPEN;
          timer_next = 32'd0;
        end else if (timer >= WAIT_TICKS - 1) begin
          state_next = ST_CLOSING;
          timer_next = 32'd0;
        end else begin
          // Switch open: count 10 s wait (another close of the switch resets via arm)
          state_next = ST_OPEN;
          timer_next = timer + 1'b1;
        end
      end

      ST_CLOSING: begin
        if (arm) begin
          // Arm trips again: abort close and reopen
          fsm_cmd    = CMD_OPEN;
          state_next = ST_OPENING;
          timer_next = 32'd0;
        end else begin
          fsm_cmd = CMD_CLOSE;
          if (timer >= CLOSE_TICKS - 1) begin
            state_next = ST_IDLE;
            timer_next = 32'd0;
          end else begin
            timer_next = timer + 1'b1;
          end
        end
      end

      default: begin
        state_next = ST_IDLE;
        timer_next = 32'd0;
        fsm_cmd    = CMD_STOP;
      end
    endcase
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= ST_IDLE;
      timer <= 32'd0;
    end else if (diag_override) begin
      state <= state;
      timer <= timer;
    end else begin
      state <= state_next;
      timer <= timer_next;
    end
  end

  sg90_continuous_pwm #(
      .CLK_FREQ(CLK_FREQ)
  ) servo (
      .clk(clk),
      .rst_n(rst_n),
      .cmd(servo_cmd),
      .pwm_out(pwm_out)
  );

  function automatic [6:0] digit7;
    input [2:0] value;
    begin
      case (value)
        3'd0: digit7 = 7'b0111111;
        3'd1: digit7 = 7'b0000110;
        3'd2: digit7 = 7'b1011011;
        3'd3: digit7 = 7'b1001111;
        default: digit7 = 7'b0000000;
      endcase
    end
  endfunction

  assign seg = digit7(state);

  assign uo_out[6:0] = seg;
  assign uo_out[7]   = pwm_enable;

  assign uio_out[0]   = pwm_enable ? pwm_out : 1'b0;
  assign uio_out[7:1] = 7'b0;
  assign uio_oe[0]    = pwm_enable;
  assign uio_oe[7:1]  = 7'b0;

  wire _unused = &{ena, ui_in[0], ui_in[7:4], uio_in[0], uio_in[7:2], 1'b0};

endmodule
