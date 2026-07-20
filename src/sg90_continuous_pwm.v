`timescale 1ns / 1ps

module sg90_continuous_pwm #(
    // The system clock frequency in Hz. 
    // The PRD specifies a range of 10 kHz to 12 MHz; adjust this parameter to match your exact clock.
    parameter CLK_FREQ = 10_000_000 
)(
    input wire clk,
    input wire rst_n,           // Active-low reset
    input wire [1:0] cmd,       // Control signal from FSM -> 00: Stop, 01: Open, 10: Close
    output reg pwm_out          // PWM output to the SG90 signal pin
);

    // Calculate tick thresholds based on the parameterized clock frequency
    // 50 Hz frequency equates to a 20 ms total period.
    localparam PERIOD_TICKS = CLK_FREQ / 50; 
    
    // Standard continuous servo pulse widths
    localparam PULSE_1_0_MS = CLK_FREQ / 1000;         // 1.0 ms (Close)
    localparam PULSE_1_5_MS = (CLK_FREQ * 15) / 10000; // 1.5 ms (Stop/Neutral)
    localparam PULSE_2_0_MS = CLK_FREQ / 500;          // 2.0 ms (Open)

    reg [31:0] counter;
    reg [31:0] active_duty_cycle;

    // Combinational logic to map the FSM command to the correct pulse width
    always @(*) begin
        case (cmd)
            2'b00: active_duty_cycle = PULSE_1_5_MS; // Idle/Stop
            2'b01: active_duty_cycle = PULSE_2_0_MS; // Open hatch
            2'b10: active_duty_cycle = PULSE_1_0_MS; // Close hatch (pest detected)
            default: active_duty_cycle = PULSE_1_5_MS; // Default to safe stop
        endcase
    end

    // Sequential logic for the PWM counter and output generation
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 0;
            pwm_out <= 1'b0;
        end else begin
            // Reset counter at the end of the 20ms period
            if (counter >= (PERIOD_TICKS - 1)) begin
                counter <= 0;
            end else begin
                counter <= counter + 1;
            end
            
            // Drive the PWM line HIGH if the counter is within the active duty cycle duration
            if (counter < active_duty_cycle) begin
                pwm_out <= 1'b1;
            end else begin
                pwm_out <= 1'b0;
            end
        end
    end

endmodule
