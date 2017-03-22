// test_bench.templet.v
`timescale 1ps/1ps
module parser_packer_tb;

reg clk;
reg rst;

initial clk = 0;
initial rst = 1;
always #2500 clk =~clk;


bus axism;
bus axiss;
regs;

paser ();
packer ();

initial
begin
    aximm = 0;
    axiss = 1;
end

task user_burst(
input xx,
input xx,
input axis
);
begin
    
end
endtask;