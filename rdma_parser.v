module rdma_parser(
input  wire clk,
input  wire rst,

//Input AXI Stream Interface
input  wire [31   : 0]    data_slave,
input  wire [3    : 0]    keep_slave,
input  wire [0    : 0]    valid_slave,
input  wire [0    : 0]    last_slave,
output wire [0    : 0]    ready_slave,

//Output AXI Stream Interface
output wire [0    : 0]    valid_master,
input  wire [0    : 0]    ready_master,

//Output results
output reg  [47   : 0]    src_address,
output reg  [47   : 0]    dst_address,
output reg  [0    : 0]    operation,
output reg  [30   : 0]    counter
);

localparam IDLE = 2'b01,
           HEAD = 2'b10;

reg [1:0] ps;
reg [1:0] ns;

wire is_idle;
wire is_head;

assign is_idle = (ps == IDLE);
assign is_head = (ps == HEAD);

reg  [0   :0] valid_out;
wire [0   :0] ready_out;

reg  [31  :0] data;
reg  [0   :0] last;
reg  [4   :0] header;
wire [31  :0] rdata;


assign ready_slave = ready_out & ~last;


assign valid_master = valid_out;
assign ready_out    = ready_master;
assign rdata = {
data[7   :   0],
data[15  :   8],
data[23  :  16],
data[31  :  24]
};

wire valid_ready;
assign valid_ready = valid_slave & ready_slave;

wire true_last;
assign true_last = last_slave & valid_ready;

wire header_last;
assign header_last = (header == 'd3);

always @(posedge clk or posedge rst) 
begin
    if (rst) ps <= IDLE;
    else     ps <= ns;
end

always @ (*)
begin
    case (ps)
        IDLE:   if  (valid_ready)   ns = HEAD;
                else                ns = IDLE;
        HEAD:   if (ready_master & header_last) 
                                    ns = IDLE;
                else                ns = HEAD;
        default:                    ns = IDLE;
    endcase
end

always @ (posedge clk)
begin 
    if (valid_ready) begin
        data <= data_slave;
    end
    else begin
        data <= data;
    end
end

always @ (posedge clk or posedge rst)
begin
    if (rst)
        last <= 1'b0;
    else if (true_last)
        last <= 1'b1;
    else if (ns == IDLE)
        last <= 1'b0;
    else
        last <= last;
end

always @ (posedge clk or posedge rst)
begin
    if (rst)
    begin
        src_address <= 'd0;
        dst_address <= 'd0;
        operation <= 'd0;
        counter <= 'd0;
    end
    else if (is_head)
        case (header)
            'd0   : 
            begin
                src_address[47:16] <= rdata[31:0];
            end

            'd1   : 
            begin
                src_address[15:0] <= rdata[31:16];
                dst_address[47:32] <= rdata[15:0];
            end

            'd2   : 
            begin
                dst_address[31:0] <= rdata[31:0];
            end

            'd3   : 
            begin
                operation[0:0] <= rdata[31:31];
                counter[30:0] <= rdata[30:0];
            end
        endcase
    else
    begin
        src_address <= src_address;
        dst_address <= dst_address;
        operation <= operation;
        counter <= counter;
    end
end

always @(posedge clk or posedge rst) begin
    if (rst) 
        header <= 'd0;
    else if (~is_head)
        header <= 'd0;
    else if (valid_ready)
        header <= header + 'd1;
    else
        header <= header;
end


always @(posedge clk or posedge rst) begin
    if (rst) 
        valid_out <= 'd0;
    else
        valid_out <= (is_head & ready_master & header_last);
end

endmodule