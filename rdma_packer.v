module rdma_packer(
input  wire clk,
input  wire rst,

//Input AXI Stream Interface
input  wire [0    : 0]    valid_slave,
output wire [0    : 0]    ready_slave,

//Output AXI Stream Interface
output wire [31   : 0]    data_master,
output wire [3    : 0]    keep_master,
output wire [0    : 0]    valid_master,
output wire [0    : 0]    last_master,
input  wire [0    : 0]    ready_master,

//Input results
input  wire [47   : 0]    src_address,
input  wire [47   : 0]    dst_address,
input  wire [0    : 0]    operation,
input  wire [30   : 0]    counter
);

localparam IDLE = 4'b01,
           HEAD = 4'b10;

reg [1:0] ps;
reg [1:0] ns;

wire is_idle;
wire is_head; 

assign is_idle = (ps == IDLE);
assign is_head = (ps == HEAD);

reg  [31  :0] temp_data;
reg  [3   :0] keep_out;
wire [0   :0] valid_out;
reg  [0   :0] last_out;
wire [0   :0] ready_out;

reg  [0   :0] last;
reg  [4   :0] header;
wire [31  :0] rdata;
wire header_last;
assign header_last = (header == 'd3);


assign valid_out = is_head;
assign last_out  = is_head & header_last;
assign ready_slave = ready_out;

assign data_master  = rdata;
assign valid_master = valid_out;
assign keep_master  = keep_out;
assign last_master  = last_out;
assign ready_out = ((ns == HEAD) | (is_head & (header < 'd3))) ? 0 : ready_master;

assign rdata = {
temp_data[7   :   0],
temp_data[15  :   8],
temp_data[23  :  16],
temp_data[31  :  24]
};

wire valid_ready_m;
assign valid_ready_m = valid_slave & ready_master;

wire valid_ready_s;
assign valid_ready_s = valid_slave & ready_slave;

always @(posedge clk or posedge rst) 
begin
    if (rst) ps <= IDLE;
    else     ps <= ns;
end

always @ (*)
begin
    case (ps)
        IDLE:   if  (valid_slave)   ns = HEAD;
                else                ns = IDLE;
        HEAD:   if (ready_master & header_last) 
                                    ns = IDLE;
                else                ns = HEAD;
        default:                    ns = IDLE;
    endcase
end

always @ (*)
    begin 
        keep_out = 0;
        if (is_head & header_last)
            keep_out = 4'hf;
        if (is_head)
            keep_out = 4'hf;
    end
    
always @ (*)
begin
    temp_data = 'd0;
    case (ps)
    HEAD:
        case (header)
            'd0   : 
            begin
                temp_data[31:0] = src_address[47:16];     
            end

            'd1   : 
            begin
                temp_data[31:16] = src_address[15:0];      
                temp_data[15:0] = dst_address[47:32];     
            end

            'd2   : 
            begin
                temp_data[31:0] = dst_address[31:0];      
            end

            'd3   : 
            begin
                temp_data[31:31] = operation[0:0];         
                temp_data[30:0] = counter[30:0];          
            end
        endcase
    endcase
end

always @(posedge clk or posedge rst) begin
    if (rst) 
        header <= 'd0;
    else if (~is_head)
        header <= 'd0;
    else if (ready_master)
        header <= header + 'd1;
    else
        header <= header;
end

endmodule