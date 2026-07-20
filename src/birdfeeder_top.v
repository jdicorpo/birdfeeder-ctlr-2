/*
 * Copyright (c) 2025 Jeff DiCorpo
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Door controller for a birdfeeder hatch driven by an SG90 continuous servo.
//
// ui_in[0] = trigger  : rising edge starts an open -> hold -> close cycle
// ui_in[1] = pest     : level-sensitive; forces an immediate close
// uo_out[0] = pwm_out : SG90 signal pin
module birdfeeder_top #(
    parameter CLK_FREQ      = 10_000_000,
    parameter OPEN_TIME_MS  = 800,
    parameter HOLD_TIME_MS  = 2000,
    parameter CLOSE_TIME_MS = 800
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
  localparam integer HOLD_TICKS  = (CLK_FREQ / 1000) * HOLD_TIME_MS;
  localparam integer CLOSE_TICKS = (CLK_FREQ / 1000) * CLOSE_TIME_MS;

  // Servo commands (see sg90_continuous_pwm)
  localparam [1:0] CMD_STOP  = 2'b00;
  localparam [1:0] CMD_OPEN  = 2'b01;
  localparam [1:0] CMD_CLOSE = 2'b10;

  // Door FSM
  localparam [2:0] ST_IDLE    = 3'd0;
  localparam [2:0] ST_OPENING = 3'd1;
  localparam [2:0] ST_OPEN    = 3'd2;
  localparam [2:0] ST_CLOSING = 3'd3;

  reg [2:0] state;
  reg [2:0] state_next;
  reg [31:0] timer;
  reg [31:0] timer_next;
  reg [1:0] servo_cmd;

  // Synchronize async inputs
  reg [1:0] trigger_sync;
  reg [1:0] pest_sync;
  reg       trigger_d;

  wire trigger = trigger_sync[1];
  wire pest    = pest_sync[1];
  wire trigger_rise = trigger & ~trigger_d;

  wire pwm_out;

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      trigger_sync <= 2'b00;
      pest_sync    <= 2'b00;
      trigger_d    <= 1'b0;
    end else begin
      trigger_sync <= {trigger_sync[0], ui_in[0]};
      pest_sync    <= {pest_sync[0], ui_in[1]};
      trigger_d    <= trigger;
    end
  end

  always @(*) begin
    state_next = state;
    timer_next = timer;
    servo_cmd  = CMD_STOP;

    case (state)
      ST_IDLE: begin
        servo_cmd = CMD_STOP;
        if (pest) begin
          // Already closed; ignore pest while idle
          state_next = ST_IDLE;
          timer_next = 32'd0;
        end else if (trigger_rise) begin
          state_next = ST_OPENING;
          timer_next = 32'd0;
        end
      end

      ST_OPENING: begin
        servo_cmd = CMD_OPEN;
        if (pest) begin
          state_next = ST_CLOSING;
          timer_next = 32'd0;
        end else if (timer >= OPEN_TICKS - 1) begin
          state_next = ST_OPEN;
          timer_next = 32'd0;
        end else begin
          timer_next = timer + 1'b1;
        end
      end

      ST_OPEN: begin
        servo_cmd = CMD_STOP;
        if (pest) begin
          state_next = ST_CLOSING;
          timer_next = 32'd0;
        end else if (timer >= HOLD_TICKS - 1) begin
          state_next = ST_CLOSING;
          timer_next = 32'd0;
        end else begin
          timer_next = timer + 1'b1;
        end
      end

      ST_CLOSING: begin
        servo_cmd = CMD_CLOSE;
        if (timer >= CLOSE_TICKS - 1) begin
          state_next = ST_IDLE;
          timer_next = 32'd0;
        end else begin
          timer_next = timer + 1'b1;
        end
      end

      default: begin
        state_next = ST_IDLE;
        timer_next = 32'd0;
        servo_cmd  = CMD_STOP;
      end
    endcase
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= ST_IDLE;
      timer <= 32'd0;
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

  assign uo_out[0]   = pwm_out;
  assign uo_out[2:1] = servo_cmd;
  assign uo_out[5:3] = state;
  assign uo_out[6]   = (state != ST_IDLE);
  assign uo_out[7]   = (state == ST_OPEN);

  assign uio_out = 8'b0;
  assign uio_oe  = 8'b0;

  wire _unused = &{ena, ui_in[7:2], uio_in, 1'b0};

endmodule
