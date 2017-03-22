`timescale 1ps/1ps
module rdma_parser_packer_tb;
reg clk;
reg rst;

initial clk = 0;
initial rst = 1;
always #2500 clk =~clk;

initial #10000 rst = 0;

reg  [0    : 0]    valid_slave;
wire [0    : 0]    ready_slave;

//Output AXI Stream Interface
wire [31   : 0]    data_master;
wire [3    : 0]    keep_master;
wire [0    : 0]    valid_master;
wire [0    : 0]    last_master;
wire [0    : 0]    ready_master;
wire [0    : 0]    valid_master3;
reg  [0    : 0]    ready_master3;

//Input results
reg  [47   : 0]    src_address;
wire [47   : 0]    src_address1;
reg  [47   : 0]    dst_address;
wire [47   : 0]    dst_address1;
reg  [0    : 0]    operation;
wire [0    : 0]    operation1;
reg  [30   : 0]    counter;
wire [30   : 0]    counter1;
integer i;
integer seed;


initial
begin
src_address = 0;
dst_address = 0;
operation = 0;
counter = 0;
seed = 0;

wait(!rst);

interval;
burst('hd82c07cc53ed,'hc2094cbc7ce0,'h0,'h21242f1f);
interval;

wait(valid_master3);
if(src_address1 != 'hd82c07cc53ed)
$display("src_address unmatch@length 2");
else
$display("src_address match@length 2");

if(dst_address1 != 'hc2094cbc7ce0)
$display("dst_address unmatch@length 2");
else
$display("dst_address match@length 2");

if(operation1 != 'h0)
$display("operation unmatch@length 2");
else
$display("operation match@length 2");

if(counter1 != 'h21242f1f)
$display("counter unmatch@length 2");
else
$display("counter match@length 2");

burst('h82e2e66f8cb8,'h67a9c37d622c,'h1,'h26d2f38f);
interval;

wait(valid_master3);
if(src_address1 != 'h82e2e66f8cb8)
$display("src_address unmatch@length 3");
else
$display("src_address match@length 3");

if(dst_address1 != 'h67a9c37d622c)
$display("dst_address unmatch@length 3");
else
$display("dst_address match@length 3");

if(operation1 != 'h1)
$display("operation unmatch@length 3");
else
$display("operation match@length 3");

if(counter1 != 'h26d2f38f)
$display("counter unmatch@length 3");
else
$display("counter match@length 3");

burst('h7a02420b7523,'h9558867c887b,'h1,'h40999432);
interval;

wait(valid_master3);
if(src_address1 != 'h7a02420b7523)
$display("src_address unmatch@length 4");
else
$display("src_address match@length 4");

if(dst_address1 != 'h9558867c887b)
$display("dst_address unmatch@length 4");
else
$display("dst_address match@length 4");

if(operation1 != 'h1)
$display("operation unmatch@length 4");
else
$display("operation match@length 4");

if(counter1 != 'h40999432)
$display("counter unmatch@length 4");
else
$display("counter match@length 4");

burst('h4826866478cc,'hc17c626308da,'h1,'h2010977f);
interval;

wait(valid_master3);
if(src_address1 != 'h4826866478cc)
$display("src_address unmatch@length 5");
else
$display("src_address match@length 5");

if(dst_address1 != 'hc17c626308da)
$display("dst_address unmatch@length 5");
else
$display("dst_address match@length 5");

if(operation1 != 'h1)
$display("operation unmatch@length 5");
else
$display("operation match@length 5");

if(counter1 != 'h2010977f)
$display("counter unmatch@length 5");
else
$display("counter match@length 5");

burst('he8e521710ac2,'hfb97d43690c5,'h1,'h737a2c82);
interval;

wait(valid_master3);
if(src_address1 != 'he8e521710ac2)
$display("src_address unmatch@length 6");
else
$display("src_address match@length 6");

if(dst_address1 != 'hfb97d43690c5)
$display("dst_address unmatch@length 6");
else
$display("dst_address match@length 6");

if(operation1 != 'h1)
$display("operation unmatch@length 6");
else
$display("operation match@length 6");

if(counter1 != 'h737a2c82)
$display("counter unmatch@length 6");
else
$display("counter match@length 6");

burst('h4f65d4c32911,'hbad640e25c19,'h1,'h578cc915);
interval;

wait(valid_master3);
if(src_address1 != 'h4f65d4c32911)
$display("src_address unmatch@length 7");
else
$display("src_address match@length 7");

if(dst_address1 != 'hbad640e25c19)
$display("dst_address unmatch@length 7");
else
$display("dst_address match@length 7");

if(operation1 != 'h1)
$display("operation unmatch@length 7");
else
$display("operation match@length 7");

if(counter1 != 'h578cc915)
$display("counter unmatch@length 7");
else
$display("counter match@length 7");

end

always@(posedge clk or posedge rst) begin
    if (rst)
        ready_master3 = 0;
    else
        ready_master3 = $random(seed)%2;
end

rdma_packer rdma_packer0(
.clk(clk),
.rst(rst),
.valid_slave(valid_slave),
.ready_slave(ready_slave),

//Input results
.src_address(src_address),
.dst_address(dst_address),
.operation(operation),
.counter(counter),

//Output AXI Stream Interface
.data_master  (data_master ),
.keep_master  (keep_master ),
.valid_master (valid_master),
.last_master  (last_master ),
.ready_master (ready_master)
);

rdma_parser rdma_parser0(
.clk(clk),
.rst(rst),
//Input AXI Stream Interface
.data_slave(data_master),
.keep_slave(keep_master),
.valid_slave(valid_master),
.last_slave(last_master),
.ready_slave(ready_master),

//Input results
.src_address(src_address1),
.dst_address(dst_address1),
.operation(operation1),
.counter(counter1),

//Output AXI Stream Interface
.valid_master (valid_master3),
.ready_master (ready_master3)
);

task burst(
input  [47   : 0]    src_address_tsk,
input  [47   : 0]    dst_address_tsk,
input  [0    : 0]    operation_tsk,
input  [30   : 0]    counter_tsk
);
reg flag;
begin
    flag = 0;
    do begin
        valid_slave = 1;
        src_address = src_address_tsk;
        dst_address = dst_address_tsk;
        operation = operation_tsk;
        counter = counter_tsk;

        #1;
        if (ready_slave) flag = 1;
        @(posedge clk);
    end while(~flag);
        
end
endtask

task interval;
begin
        valid_slave = 0;
        @(posedge clk);
end
endtask

endmodule