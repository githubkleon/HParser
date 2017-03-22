import sys
import os
import math
import random

random.seed(0)
#Get the parser name
file_name   = sys.argv[1]
parser_name = os.path.splitext(file_name)[0]
print "Parser:", parser_name

#Read parser description in
parser_file = open(file_name)
header = 0

protocols = ["AXIS"]
widths = [1,2,4,8,16,32,64]
endians = ["big","little"]

data_length_str = ""
data_length = 0
data_protocol = "AXIS"
data_endian = "big"
length_name = ""

parser_vector = []
for line in parser_file:
    key_value = line.split()
    if (len(key_value)):
        key = line.split()[0]
        value = line.split()[1]
    else:
        continue
    # print key, value
    if (key =="header"):
        header = float(value)
    elif (key == "data_length"):
        data_length_str = value
    elif (key == "data_protocol"):
        data_protocol = value
    elif (key == "data_width"):
        data_width = int(value)
    elif (key == "data_endian"):
        data_endian = value
    else:
        parser_vector.append((key,int(value)))

#check parser description
length_count = 0
length_pos = []
for pair in parser_vector:
    length_count = length_count + pair[1]

if (length_count == header * 8):
    print "The length of header is:",header,"bytes"
else:
    print "The length of header does not match!"
    exit(0)

if (data_protocol in protocols):
    print "The transmission protocol is:", data_protocol
else:
    print "The transmission protocol is not supported:", data_protocol
    exit(0)

if (data_width in widths):
    print "The transmission width is:", data_width
else:
    print "The transmission width is not supported:", data_width
    exit(0)

if (data_endian in endians):
    print "The transmission endian is:", data_endian
    # if (data_endian == "big"): print "(Network)"
else:
    print "The transmission endian is not supported:", data_endian
    exit(0)

for entry in parser_vector:
    if (data_length_str == entry[0]):
        print "The data length is count on:", entry[0]
        print "The width of length counter will be:", entry[1]
        data_length = entry[1]
        length_name = entry[0]

hd_parser_name = parser_name + "_parser"
hd_packer_name = parser_name + "_packer"
hd_testbench_name = parser_name + "_parser_packer_tb"

#####hardware parser file
hpf = open(hd_parser_name + ".v","w")
hpf.write("module " + hd_parser_name + "(\n")
hpf.write("input  wire clk,\n")
hpf.write("input  wire rst,\n")
hpf.write("\n")

if (data_protocol == "AXIS"):
    hpf.write("//Input AXI Stream Interface\n")
    hpf.write("input  wire [" + '{:<4}'.format(str(data_width * 8 - 1)) + " : 0]    data_slave,\n")
    hpf.write("input  wire [" + '{:<4}'.format(str(data_width - 1))     + " : 0]    keep_slave,\n")
    hpf.write("input  wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_slave,\n")
    hpf.write("input  wire [" + '{:<4}'.format(str(0))                  + " : 0]    last_slave,\n")
    hpf.write("output wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_slave,\n")
    hpf.write("\n")
    hpf.write("//Output AXI Stream Interface\n")
    if (data_length_str != ""):
        hpf.write("output wire [" + '{:<4}'.format(str(data_width * 8 - 1)) + " : 0]    data_master,\n")
        hpf.write("output wire [" + '{:<4}'.format(str(data_width - 1))     + " : 0]    keep_master,\n")
        hpf.write("output wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_master,\n")
        hpf.write("output wire [" + '{:<4}'.format(str(0))                  + " : 0]    last_master,\n")
        hpf.write("input  wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_master,\n")
    else:
        hpf.write("output wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_master,\n")
        hpf.write("input  wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_master,\n")
    entry_indicators = [0] * (len(parser_vector) - 1)
    entry_indicators.append(1)
    # print entry_indicators
    hpf.write("\n")
    hpf.write("//Output results\n")
    for entry,entry_id in zip (parser_vector,entry_indicators):
        hpf.write("output reg  [" + '{:<4}'.format(str(entry[1] - 1))       + " : 0]    " + entry[0])
        if (entry_id): hpf.write("\n")
        else: hpf.write(",\n")
hpf.write(");\n\n")
if (data_length_str != ""):
    hpf.write('''localparam IDLE = 4'b0001,
           HEAD = 4'b0010,
           DATA = 4'b0100,
           WAIT = 4'b1000;

reg [3:0] ps;
reg [3:0] ns;

wire is_idle;
wire is_head;
wire is_data;
wire is_wait; 

assign is_idle = (ps == IDLE);
assign is_head = (ps == HEAD);
assign is_data = (ps == DATA);
assign is_wait = (ps == WAIT);\n\n''')
else:
    hpf.write('''localparam IDLE = 2'b01,
           HEAD = 2'b10;

reg [1:0] ps;
reg [1:0] ns;

wire is_idle;
wire is_head;

assign is_idle = (ps == IDLE);
assign is_head = (ps == HEAD);\n\n''')

#check alignment
data_vector = []
data_col    = 0
data_row    = 0
data_vector.append([])

data_max_line = 0

for entry in parser_vector:
    entry_remain = entry[1]
    entry_start  = 0
    # max_col      = 1
    # max_row      = 1

    while(entry_remain > 0):
         if (data_col + entry_remain <= data_width * 8):
            data_point  = (data_col,data_col + entry_remain-1)
            entry_point = (entry[1] - entry_start - entry_remain, entry[1] - entry_start - 1)
            data_vector[data_row].append((data_point,entry[0],entry_point))
            data_col    += entry_remain
            data_col    = data_col % (data_width * 8)
            # data_max_line = max(data_max_line,max_col)
            if (data_col == 0):
                # print data_col
                data_row += 1
                data_vector.append([])
            break
         else:
            data_diff     = data_width * 8 - data_col
            data_point    = (data_col,data_width * 8-1)
            entry_remain  = entry_remain - data_diff
            entry_point   = (entry[1] - entry_start - data_diff, entry[1] - entry_start - 1)
            data_vector[data_row].append((data_point,entry[0],entry_point))
            data_row      += 1
            data_vector.append([])
            data_col      = 0
            entry_start   = entry_start + data_diff

if (data_col == 0):
    data_vector.pop()
    data_max_line = data_row - 1
else:
    data_max_line = data_row

length_vector = []
data_indicators = range(0, len(data_vector))
for data_row,data_id in zip(data_vector,data_indicators):
    for data_col in data_row:
        if (data_col[1] == length_name):
            length_vector.append((data_id, data_col))

alignpoint = (int(header) % data_width) * 8
# print alignpoint

# print data_max_line
if (data_length_str != ""):
    hpf.write("wire ["  + '{:<4}'.format(str(data_width*8-1)) + ":0] data_out;\n\
reg  ["             + '{:<4}'.format(str(data_width-1))   + ":0] keep_out;\n\
wire ["             + '{:<4}'.format(str(0))              + ":0] valid_out;\n\
wire ["             + '{:<4}'.format(str(0))              + ":0] last_out;\n\
wire ["             + '{:<4}'.format(str(0))              + ":0] ready_out;\n\n")
else:
    hpf.write("reg  ["             + '{:<4}'.format(str(0))              + ":0] valid_out;\n")
    hpf.write("wire ["             + '{:<4}'.format(str(0))              + ":0] ready_out;\n\n")


if (data_length_str != ""):
    hpf.write("reg  ["  + '{:<4}'.format(str(data_width*8-1)) + ":0] data;\n\
reg  ["             + '{:<4}'.format(str(0))              + ":0] valid;\n\
reg  ["             + '{:<4}'.format(str(0))              + ":0] last;\n")
else:
    hpf.write("reg  ["  + '{:<4}'.format(str(data_width*8-1)) + ":0] data;\n\
reg  ["             + '{:<4}'.format(str(0))              + ":0] last;\n")

if (data_length_str != ""):
    if (alignpoint != 0):
        hpf.write("reg  ["  + '{:<4}'.format(str(data_width*8-1)) + ":0] data_r;\n")

if (data_length_str != ""):
    hpf.write("reg  ["  + '{:<4}'.format(str(data_length-1))    + ":0] length;\n")
hpf.write("reg  ["  + '{:<4}'.format(str(int(math.floor(math.log(header,2)))))  + ":0] header;\n")
hpf.write("wire ["  + '{:<4}'.format(str(data_width*8-1))   + ":0] rdata;\n\n")


if (data_length_str != ""):
    if (alignpoint != 0):
        hpf.write("assign data_out = {data[" + str(alignpoint-1) + ":0], data_r["\
        + str(data_width*8-1) + ":" + str(alignpoint) + "]};\n")
    else:
        hpf.write("assign data_out = data[" + str(data_width*8-1) + ":0];\n")
if (data_length_str != ""):
    hpf.write("\n\
assign valid_out = (is_data & valid) | last;\n\
assign last_out  = (length <= 'd" + '{:<3}'.format(str(data_width)) + ") & valid_out;\n\
assign ready_slave = ready_out & ~last;\n\
\n")
else:
    hpf.write("\n\
assign ready_slave = ready_out & ~last;\n\
\n")

if (data_length_str != ""):
    hpf.write('''
assign data_master  = data_out;
assign valid_master = valid_out;
assign keep_master  = keep_out;
assign last_master  = last_out;
assign ready_out    = ready_master;
''')
else:
    hpf.write('''
assign valid_master = valid_out;
assign ready_out    = ready_master;
''')

if (data_length_str != ""):
    hpf.write('''always @ (*)
begin 
    keep_out = 0;
    case (length)\n''')
    for i in range(0,data_width):
        hpf.write("        'd" + '{:<3}'.format(str(data_width - i - 1)) + ": keep_out = " + '{:>3}'.format(str(data_width)) + "'h")
        hpf.write(("%0"+ str(data_width/4) +"x")% ((2**data_width - 1) >> (i+1)))
        hpf.write(";\n")

    hpf.write('''        default: keep_out = ''' + '{:>3}'.format(str(data_width)) + "'h")
    hpf.write(("%0"+ str(data_width/4) +"x")% ((2**data_width - 1)))
    hpf.write(''';
    endcase
end
\n''')

if (data_endian == "big"):
    hpf.write("assign rdata = {\n")
    for i in range(0,data_width):
        hpf.write("data[" + '{:<4}'.format(str((i+1)*8-1)) + ":" + '{:>4}'.format(str(i*8)) + "]")
        if (i == data_width - 1):
            hpf.write("\n")
        else:
            hpf.write(",\n")
    hpf.write("};\n\n")
else:
    hpf.write("assign rdata = data;\n\n")

hpf.write('''wire valid_ready;
assign valid_ready = valid_slave & ready_slave;

wire true_last;
assign true_last = last_slave & valid_ready;
\n''')

hpf.write('''wire header_last;
assign header_last = (header == 'd''' + str(data_max_line) + ");\n\n")

hpf.write("always @(posedge clk or posedge rst) \n\
begin\n\
    if (rst) ps <= IDLE;\n\
    else     ps <= ns;\n\
end\n\n")

if (data_length_str != ""):
    hpf.write("always @ (*)\n\
begin\n\
    case (ps)\n\
        IDLE:   if  " + '{:<16}'.format("(valid_ready)") + "ns = HEAD;\n\
                else" + '{:<16}'.format("")              + "ns = IDLE;\n\
        HEAD:   if  " + '{:<16}'.format("(valid_ready & header_last)") + "\n\
                    " + '{:<16}'.format("")              + "ns = DATA;\n\
                else" + '{:<16}'.format("")              + "ns = HEAD;\n\
        DATA:   if (last_out & ready_master) \n\
                begin\n\
                    if (last)       ns = IDLE;\n\
                    else            ns = WAIT;\n\
                end\n\
                else                ns = DATA;\n\
        WAIT:   if (true_last)      ns = IDLE;\n\
                else                ns = WAIT;\n\
        default:                    ns = IDLE;\n\
    endcase\n\
end\n\n")
else:
        hpf.write("always @ (*)\n\
begin\n\
    case (ps)\n\
        IDLE:   if  " + '{:<16}'.format("(valid_ready)") + "ns = HEAD;\n\
                else" + '{:<16}'.format("")              + "ns = IDLE;\n\
        HEAD:   if (ready_master & header_last) \n\
                                    ns = IDLE;\n\
                else                ns = HEAD;\n\
        default:                    ns = IDLE;\n\
    endcase\n\
end\n\n")

hpf.write('''always @ (posedge clk)
begin 
    if (valid_ready) begin
        data <= data_slave;''')
if (alignpoint != 0 and data_length_str != ""):
    hpf.write('''
        data_r <= data;''')
hpf.write('''
    end
    else begin
        data <= data;''')
if (alignpoint != 0 and data_length_str != ""):
    hpf.write('''
        data_r <= data_r;''')
hpf.write('''
    end
end
''')

if (data_length_str != ""):
    hpf.write('''
always @ (posedge clk or posedge rst) 
begin
    if (rst)
        valid <= 'b0;
    else if (ready_master)
        valid <= valid_ready;
    else
        valid <= valid;
end
''')

hpf.write('''
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

''')

hpf.write("always @ (posedge clk or posedge rst)\n\
begin\n\
    if (rst)\n\
    begin\n")
for entry in parser_vector:
        hpf.write("        " + entry[0] + " <= 'd0;\n")

hpf.write("\
    end\n\
    else if (is_head)")
hpf.write("\n\
        case (header)")

entry_counters = range(0,len(data_vector))

for entry_row,entry_number in zip(data_vector,entry_counters):
    hpf.write("\n\
            'd" + '{:<3}'.format(str(entry_number)) + " : \n\
            begin\n")
    col_counters = range(0, len(entry_row))
    for entry_col,col_number in zip(entry_row,col_counters):
        hpf.write("\
                " + str(entry_col[1]) + "[" + str(entry_col[2][1]) + ":" + str(entry_col[2][0]) + "]" + " <= ")
        hpf.write("rdata[" + str(data_width*8 - 1 - entry_col[0][0]) + ":" + str(data_width*8 - 1 - entry_col[0][1]) + "];\n" )
        if (length_name == entry_col[1]):
            length_pos.append((entry_number,col_number))
    hpf.write("\
            end\n")
hpf.write("\
        endcase\n")

hpf.write("\
    else\n\
    begin\n")

for entry in parser_vector:
        hpf.write("        " + entry[0] + " <= " + entry[0] + ";\n")

hpf.write("\
    end\n")
hpf.write("\
end\n\n")

if (data_length_str != ""):
    hpf.write("always @ (posedge clk or posedge rst)\n\
begin\n\
    if (rst) \n\
        length <= 'd0;\n")
    for length_entry in length_pos:
        length_inst = data_vector[length_entry[0]][length_entry[1]]
        # print length_inst
        hpf.write("\
    else if (is_head & (header == 'd" + str(length_entry[0]) + "))\n\
        length[" + str(length_inst[2][1]) + ":" + str(length_inst[2][0]) + "]" + " <= rdata[" + str(data_width*8 - 1 - length_inst[0][0]) + ":" + str(data_width*8 - 1 - length_inst[0][1]) + "]" + ";\n")
    hpf.write("\
    else if (valid_out & ready_master)\n\
        length <= length - 'd" + str(data_width) + ";\n\
    else if (ns == IDLE) \n\
        length <= 'd0;\n\
    else \n\
        length <= length;\n\
end\n\n")

hpf.write('''always @(posedge clk or posedge rst) begin
    if (rst) 
        header <= 'd0;
    else if (~is_head)
        header <= 'd0;''')
hpf.write('''
    else if (valid_ready)
        header <= header + 'd1;
    else
        header <= header;
end

''')

if (data_length_str == ""):
    hpf.write('''
always @(posedge clk or posedge rst) begin
    if (rst) 
        valid_out <= 'd0;
    else
        valid_out <= (is_head & ready_master & header_last);
end

''')

hpf.write("endmodule")
hpf.close()

#Hardware packer file
hpf = open(hd_packer_name + ".v","w")
hpf.write("module " + hd_packer_name + "(\n")
hpf.write("input  wire clk,\n")
hpf.write("input  wire rst,\n")
hpf.write("\n")

if (data_protocol == "AXIS"):
    hpf.write("//Input AXI Stream Interface\n")
    if (data_length_str != ""):
        hpf.write("input  wire [" + '{:<4}'.format(str(data_width * 8 - 1)) + " : 0]    data_slave,\n")
        hpf.write("input  wire [" + '{:<4}'.format(str(data_width - 1))     + " : 0]    keep_slave,\n")
        hpf.write("input  wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_slave,\n")
        hpf.write("input  wire [" + '{:<4}'.format(str(0))                  + " : 0]    last_slave,\n")
        hpf.write("output wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_slave,\n")
    else:
        hpf.write("input  wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_slave,\n")
        hpf.write("output wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_slave,\n")
    hpf.write("\n")
    hpf.write("//Output AXI Stream Interface\n")
    hpf.write("output wire [" + '{:<4}'.format(str(data_width * 8 - 1)) + " : 0]    data_master,\n")
    hpf.write("output wire [" + '{:<4}'.format(str(data_width - 1))     + " : 0]    keep_master,\n")
    hpf.write("output wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_master,\n")
    hpf.write("output wire [" + '{:<4}'.format(str(0))                  + " : 0]    last_master,\n")
    hpf.write("input  wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_master,\n")

    entry_indicators = [0] * (len(parser_vector) - 1)
    entry_indicators.append(1)
    # print entry_indicators
    hpf.write("\n")
    hpf.write("//Input results\n")
    for entry,entry_id in zip (parser_vector,entry_indicators):
        hpf.write("input  wire [" + '{:<4}'.format(str(entry[1] - 1))       + " : 0]    " + entry[0])
        if (entry_id): hpf.write("\n")
        else: hpf.write(",\n")
hpf.write(");\n\n")
if (data_length_str != ""):
    hpf.write('''localparam IDLE = 4'b0001,
           HEAD = 4'b0010,
           DATA = 4'b0100,
           WAIT = 4'b1000;

reg [3:0] ps;
reg [3:0] ns;

wire is_idle;
wire is_head;
wire is_data;
wire is_wait; 

assign is_idle = (ps == IDLE);
assign is_head = (ps == HEAD);
assign is_data = (ps == DATA);
assign is_wait = (ps == WAIT);\n\n''')
else:
    hpf.write('''localparam IDLE = 4'b01,
           HEAD = 4'b10;

reg [1:0] ps;
reg [1:0] ns;

wire is_idle;
wire is_head; 

assign is_idle = (ps == IDLE);
assign is_head = (ps == HEAD);\n\n''')

if (data_length_str != ""):
    hpf.write("reg  ["  + '{:<4}'.format(str(data_width*8-1))   + ":0] temp_data;\n\
reg  ["             + '{:<4}'.format(str(data_width-1))   + ":0] keep_out;\n\
wire ["             + '{:<4}'.format(str(0))              + ":0] valid_out;\n\
wire ["             + '{:<4}'.format(str(0))              + ":0] last_out;\n\
wire ["             + '{:<4}'.format(str(0))              + ":0] ready_out;\n\n")
else:
    hpf.write("reg  ["  + '{:<4}'.format(str(data_width*8-1))   + ":0] temp_data;\n\
reg  ["             + '{:<4}'.format(str(data_width-1))   + ":0] keep_out;\n\
wire ["             + '{:<4}'.format(str(0))              + ":0] valid_out;\n\
reg  ["             + '{:<4}'.format(str(0))              + ":0] last_out;\n\
wire ["             + '{:<4}'.format(str(0))              + ":0] ready_out;\n\n")

if (data_length_str != ""):
    hpf.write("reg  ["  + '{:<4}'.format(str(data_width*8-1)) + ":0] data;\n\
reg  ["             + '{:<4}'.format(str(0))              + ":0] valid;\n")

hpf.write("\
reg  ["             + '{:<4}'.format(str(0))              + ":0] last;\n")

if (alignpoint != 0 and data_length_str != ""):
    hpf.write("reg  ["  + '{:<4}'.format(str(data_width*8-1)) + ":0] data_r;\n")
if (data_length_str != ""):
    hpf.write("reg  ["  + '{:<4}'.format(str(data_length-1))    + ":0] length;\n")
hpf.write("reg  ["  + '{:<4}'.format(str(int(math.floor(math.log(header,2)))))  + ":0] header;\n")
hpf.write("wire ["  + '{:<4}'.format(str(data_width*8-1))   + ":0] rdata;\n")
if (data_length_str != ""):
    hpf.write("wire ["  + '{:<4}'.format(str(data_width*8-1))   + ":0] data_slave_rev;\n")


hpf.write('''wire header_last;
assign header_last = (header == 'd''' + str(int(data_max_line)) + ");\n\n")

if (data_length_str != ""):
    hpf.write("\n\
assign valid_out = is_head | (is_data & valid) | last;\n\
assign last_out  = is_data & (length <= 'd" + '{:<3}'.format(str(data_width)) + ") & valid_out;\n")
else:
    hpf.write("\n\
assign valid_out = is_head;\n\
assign last_out  = is_head & header_last;\n")

if (data_length_str != ""):
    hpf.write("\
assign ready_slave = ready_out & ~last;\n")
else:
    hpf.write("\
assign ready_slave = ready_out;\n")
hpf.write('''
assign data_master  = rdata;
assign valid_master = valid_out;
assign keep_master  = keep_out;
assign last_master  = last_out;
''')

if (data_length_str != ""):
    if (alignpoint == 0):  
        if (data_max_line == 0):
            hpf.write("assign ready_out = (ns == HEAD) ? 0 : ready_master;\n\n")
        else:
            hpf.write("assign ready_out = ((ns == HEAD) | (is_head & (header < 'd" + str(data_max_line) + "))) ? 0 : ready_master;\n\n")
    else:
        if (data_max_line == 0):
            hpf.write("assign ready_out = ready_master;\n\n")
        else:
            hpf.write("assign ready_out = ((ns == HEAD) | (is_head & (header < 'd" + str(data_max_line - 1) + "))) ? 0 : ready_master;\n\n")
else: 
    if (data_max_line == 0):
        hpf.write("assign ready_out = ready_master;\n\n")
    else:
        hpf.write("assign ready_out = ((ns == HEAD) | (is_head & (header < 'd" + str(data_max_line) + "))) ? 0 : ready_master;\n\n")

if (data_length_str != ""):
    hpf.write('''always @ (*)
    begin 
        keep_out = 0;
        case (length)\n''')
    for i in range(0,data_width):
        hpf.write("        'd" + '{:<3}'.format(str(data_width - i - 1)) + ": keep_out = " + '{:>3}'.format(str(data_width)) + "'h")
        hpf.write(("%0"+ str(data_width/4) +"x")% ((2**data_width - 1) >> (i+1)))
        hpf.write(";\n")
    
    hpf.write('''        default: keep_out = ''' + '{:>3}'.format(str(data_width)) + "'h")
    hpf.write(("%0"+ str(data_width/4) +"x")% ((2**data_width - 1)))
    hpf.write(''';
        endcase
    end
    \n''')

if (data_length_str != ""):
    if (data_endian == "big"):
        hpf.write("assign data_slave_rev = {\n")
        for i in range(0,data_width):
            hpf.write("data_slave[" + '{:<4}'.format(str((i+1)*8-1)) + ":" + '{:>4}'.format(str(i*8)) + "]")
            if (i == data_width - 1):
                hpf.write("\n")
            else:
                hpf.write(",\n")
        hpf.write("};\n\n")
    else:
        hpf.write("assign data_slave_rev = data_salve;\n\n")

hpf.write("assign rdata = {\n")
for i in range(0,data_width):
    hpf.write("temp_data[" + '{:<4}'.format(str((i+1)*8-1)) + ":" + '{:>4}'.format(str(i*8)) + "]")
    if (i == data_width - 1):
        hpf.write("\n")
    else:
        hpf.write(",\n")
hpf.write("};\n\n")

if (data_length_str != ""):
    hpf.write('''wire valid_ready_m;
assign valid_ready_m = valid_slave & ready_master;

wire valid_ready_s;
assign valid_ready_s = valid_slave & ready_slave;

wire true_last;
assign true_last = last_slave & valid_ready_s;
\n''')
else:
    hpf.write('''wire valid_ready_m;
assign valid_ready_m = valid_slave & ready_master;

wire valid_ready_s;
assign valid_ready_s = valid_slave & ready_slave;

''')

hpf.write("always @(posedge clk or posedge rst) \n\
begin\n\
    if (rst) ps <= IDLE;\n\
    else     ps <= ns;\n\
end\n\n")

if (data_length_str != ""):
    hpf.write("always @ (*)\n\
begin\n\
    case (ps)\n\
        IDLE:   if  " + '{:<16}'.format("(valid_slave)") + "ns = HEAD;\n\
                else" + '{:<16}'.format("")              + "ns = IDLE;\n\
        HEAD:   if  " + '{:<16}'.format("(ready_master & header_last)") + "\n\
                    " + '{:<16}'.format("")              + "ns = DATA;\n\
                else" + '{:<16}'.format("")              + "ns = HEAD;\n\
        DATA:   if (last_out & ready_master) \n\
                begin\n\
                    if (last)       ns = IDLE;\n\
                    else            ns = WAIT;\n\
                end\n\
                else                ns = DATA;\n\
        WAIT:   if (true_last)      ns = IDLE;\n\
                else                ns = WAIT;\n\
        default:                    ns = IDLE;\n\
    endcase\n\
end\n\n")
else:
    hpf.write("always @ (*)\n\
begin\n\
    case (ps)\n\
        IDLE:   if  " + '{:<16}'.format("(valid_slave)") + "ns = HEAD;\n\
                else" + '{:<16}'.format("")              + "ns = IDLE;\n\
        HEAD:   if (ready_master & header_last) \n\
                                    ns = IDLE;\n\
                else                ns = HEAD;\n\
        default:                    ns = IDLE;\n\
    endcase\n\
end\n\n")

if (data_length_str == ""):
    hpf.write('''always @ (*)
    begin 
        keep_out = 0;''')
    hpf.write('''
        if (is_head & header_last)
            keep_out = ''')
    hpf.write("%d'h%x;"%(data_width,(2**data_width-1) >> (alignpoint/8)))
    hpf.write('''
        if (is_head)
            keep_out = ''')
    hpf.write("%d'h%x;"%(data_width,(2**data_width-1)))
    hpf.write('''
    end
    \n''')

if (data_length_str != ""):
    hpf.write('''always @ (posedge clk)
begin 
    if (valid_ready_s) begin
        data <= data_slave_rev;''')
    if (alignpoint != 0):
        hpf.write('''
        data_r <= data;''')
    hpf.write('''
    end
    else begin
        data <= data;''')
    if (alignpoint != 0):
        hpf.write('''
        data_r <= data_r;''')
    hpf.write('''
    end
end

always @ (posedge clk or posedge rst)
begin
    if (rst)
        valid <= 'b0;
    else if (ready_master) 
        valid <= valid_ready_s;
    else
        valid <= valid;
end
''')

if (data_length_str != ""):
    hpf.write('''
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

''')

#Registers
hpf.write('''always @ (*)
begin
    temp_data = 'd0;
    case (ps)
    HEAD:
        case (header)''')

entry_counters = range(0,len(data_vector))

for entry_row,entry_number in zip(data_vector,entry_counters):
    if ((alignpoint == 0) | (entry_number != len(data_vector))):
        hpf.write("\n\
            'd" + '{:<3}'.format(str(entry_number)) + " : \n\
            begin")
        col_counters = range(0, len(entry_row))
        for entry_col,col_number in zip(entry_row,col_counters):
            hpf.write("\n\
                temp_data[" + str(data_width*8 - 1 - entry_col[0][0]) + ":" + str(data_width*8 - 1 - entry_col[0][1]) + "] = ")
            hpf.write('{:<24}'.format(str(entry_col[1]) + "[" + str(entry_col[2][1]) + ":" + str(entry_col[2][0]) + "];"))
        hpf.write("\n\
            end\n")
    else:
        hpf.write("\n\
            'd" + '{:<3}'.format(str(entry_number)) + " : \n\
            begin")
        col_counters = range(0, len(entry_row))
        for entry_col,col_number in zip(entry_row,col_counters):
            hpf.write("\n\
                temp_data[" + str(data_width*8 - 1 - entry_col[0][0]) + ":" + str(data_width*8 - 1 - entry_col[0][1]) + "] = ")
            hpf.write('{:<24}'.format(str(entry_col[1]) + "[" + str(entry_col[2][1]) + ":" + str(entry_col[2][0]) + "];"))

        hpf.write("\n\
                temp_data[" + str(alignpoint-1) + ":0] = data["+ str(data_width*8-1) +":" + str(alignpoint) + "];")
        hpf.write("\n\
            end\n")
hpf.write("\
        endcase\n")
if (data_length_str != ""):
    hpf.write('''
    DATA:
        temp_data = ''')
    if (alignpoint != 0):
        hpf.write("{data_r[" + str(alignpoint-1) + ":0], data["\
    + str(data_width*8-1) + ":" + str(alignpoint) + "]};\n")
    else:
        hpf.write("data[" + str(data_width*8-1) + ":0];\n")
hpf.write("\
    endcase\n")
hpf.write("\
end\n\n")

if (data_length_str != ""):
    hpf.write("always @ (posedge clk or posedge rst)\n\
begin\n\
    if (rst) \n\
        length <= 'd0;\n")
    hpf.write("\
    else if (ns == HEAD)\n\
        length <= " + length_name + ";\n")
    hpf.write("\
    else if (is_data & valid_out & ready_master)\n\
        length <= length - 'd" + str(data_width) + ";\n\
    else if (ns == IDLE) \n\
        length <= 'd0;\n\
    else \n\
        length <= length;\n\
end\n\n")

#header counter 
hpf.write('''always @(posedge clk or posedge rst) begin
    if (rst) 
        header <= 'd0;
    else if (~is_head)
        header <= 'd0;''')
hpf.write('''
    else if (ready_master)
        header <= header + 'd1;
    else
        header <= header;
end

''')

hpf.write("endmodule")
hpf.close()


#Hardware packer test bench
hpf = open(hd_testbench_name + ".v",'w')
hpf.write("`timescale 1ps/1ps\n")
hpf.write("module " + hd_testbench_name + ";\n")
hpf.write('''reg clk;
reg rst;

initial clk = 0;
initial rst = 1;
always #2500 clk =~clk;

initial #10000 rst = 0;

''')

if (data_protocol == "AXIS"):
    if (data_length_str != ""):
        hpf.write("//Input AXI Stream Interface\n")
        hpf.write("reg  [" + '{:<4}'.format(str(data_width * 8 - 1)) + " : 0]    data_slave;\n")
        hpf.write("reg  [" + '{:<4}'.format(str(data_width - 1))     + " : 0]    keep_slave;\n")
        hpf.write("reg  [" + '{:<4}'.format(str(0))                  + " : 0]    valid_slave;\n")
        hpf.write("reg  [" + '{:<4}'.format(str(0))                  + " : 0]    last_slave;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_slave;\n")
    else:
        hpf.write("reg  [" + '{:<4}'.format(str(0))                  + " : 0]    valid_slave;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_slave;\n")        

    hpf.write("\n")
    hpf.write("//Output AXI Stream Interface\n")
    hpf.write("wire [" + '{:<4}'.format(str(data_width * 8 - 1)) + " : 0]    data_master;\n")
    hpf.write("wire [" + '{:<4}'.format(str(data_width - 1))     + " : 0]    keep_master;\n")
    hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_master;\n")
    hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    last_master;\n")
    hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_master;\n")

    if (data_length_str != ""):
        hpf.write("wire [" + '{:<4}'.format(str(data_width * 8 - 1)) + " : 0]    data_master1;\n")
        hpf.write("wire [" + '{:<4}'.format(str(data_width - 1))     + " : 0]    keep_master1;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_master1;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    last_master1;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_master1;\n")

        hpf.write("wire [" + '{:<4}'.format(str(data_width * 8 - 1)) + " : 0]    data_master2;\n")
        hpf.write("wire [" + '{:<4}'.format(str(data_width - 1))     + " : 0]    keep_master2;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_master2;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    last_master2;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    ready_master2;\n")

        hpf.write("wire [" + '{:<4}'.format(str(data_width * 8 - 1)) + " : 0]    data_master3;\n")
        hpf.write("wire [" + '{:<4}'.format(str(data_width - 1))     + " : 0]    keep_master3;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_master3;\n")
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    last_master3;\n")
        hpf.write("reg  [" + '{:<4}'.format(str(0))                  + " : 0]    ready_master3;\n")
    else:     
        hpf.write("wire [" + '{:<4}'.format(str(0))                  + " : 0]    valid_master3;\n")
        hpf.write("reg  [" + '{:<4}'.format(str(0))                  + " : 0]    ready_master3;\n")

    hpf.write("\n")
    hpf.write("//Input results\n")
    for entry in parser_vector:
        hpf.write("reg  [" + '{:<4}'.format(str(entry[1] - 1))       + " : 0]    " + entry[0] + ";\n")
        hpf.write("wire [" + '{:<4}'.format(str(entry[1] - 1))       + " : 0]    " + entry[0] + "1;\n")
        # hpf.write("wire [" + '{:<4}'.format(str(entry[1] - 1))       + " : 0]    " + entry[0] + "2;\n")
        if (data_length_str != ""):
            hpf.write("wire [" + '{:<4}'.format(str(entry[1] - 1))       + " : 0]    " + entry[0] + "3;\n")

hpf.write("integer i;\n");
hpf.write("integer seed;\n")
hpf.write("\n")
hpf.write('''
initial
begin
''')

for entry in parser_vector:
    hpf.write(entry[0] + " = 0;\n")
hpf.write("seed = 0;\n")

# hpf.write("ready_master3 = 1;\n")

hpf.write("\nwait(!rst);\n")

hpf.write('''
interval;
''')
for validlength in range(2,8):
    hpf.write('''burst(''')
    
    validation = []
    validdata = 0

    entry_indicators = range(0,len(parser_vector))
    for entry,entry_id in zip (parser_vector,entry_indicators):
        temp = random.randint(0,2**entry[1]-1)
        if (data_length_str != ""):
            if (entry[0] != length_name):
                validation.append(temp)
                hpf.write("'h%x,"%temp)
            else:
                validation.append(validlength * data_width)
                hpf.write("'h%x,"%(validlength * data_width))
        else:
            validation.append(temp)
            if (entry_id != len(parser_vector) - 1):
                hpf.write("'h%x,"%temp)
            else:
                hpf.write("'h%x"%temp)


    # if (data_length_str == ""):
    #     validation.append(validlength * data_width)
    #     hpf.write("'h%x"%(validlength * data_width))
        
    if (data_length_str != ""):
        validdata = random.randint(0,2**(data_width*8)-1)
        hpf.write("'h%x,"%validdata)
    
        hpf.write("'d%d"%(validlength))
    
    hpf.write(''');
interval;

''')

    hpf.write('''wait(valid_master3);\n''')
    # entry_indicators = range(0, len(parser_vector))
    if (data_length_str != ""):
        for entry,compare in zip(parser_vector,validation):
            hpf.write("if(" + entry[0] + "3 != 'h%x)\n"%compare)
            hpf.write('''$display("''' + entry[0] + ''' unmatch@length ''' + str(validlength) + '''");\n''')
            hpf.write("else\n")
            hpf.write('''$display("''' + entry[0] + ''' match@length ''' + str(validlength) + '''");\n\n''')
    else:
        for entry,compare in zip(parser_vector,validation):
            hpf.write("if(" + entry[0] + "1 != 'h%x)\n"%compare)
            hpf.write('''$display("''' + entry[0] + ''' unmatch@length ''' + str(validlength) + '''");\n''')
            hpf.write("else\n")
            hpf.write('''$display("''' + entry[0] + ''' match@length ''' + str(validlength) + '''");\n\n''')

hpf.write("end\n\n")

hpf.write('''always@(posedge clk or posedge rst) begin
    if (rst)
        ready_master3 = 0;
    else
        ready_master3 = $random(seed)%2;
end

''')


hpf.write(hd_packer_name + " " + hd_packer_name + "0(\n")
hpf.write(".clk(clk),\n")
hpf.write(".rst(rst),\n")
if (data_protocol == "AXIS"):
    if (data_length_str != ""):
        hpf.write("//Input AXI Stream Interface\n")
        hpf.write(".data_slave(data_slave),\n")
        hpf.write(".keep_slave(keep_slave),\n")
        hpf.write(".valid_slave(valid_slave),\n")
        hpf.write(".last_slave(last_slave),\n")
        hpf.write(".ready_slave(ready_slave),\n")
    else:
        hpf.write(".valid_slave(valid_slave),\n")
        hpf.write(".ready_slave(ready_slave),\n")

    hpf.write("\n")
    hpf.write("//Input results\n")
    for entry in parser_vector:
        hpf.write("." + entry[0] + "(" + entry[0] + "),\n")

    hpf.write("\n")
    hpf.write("//Output AXI Stream Interface\n")
    
    hpf.write(".data_master  (data_master ),\n")
    hpf.write(".keep_master  (keep_master ),\n")
    hpf.write(".valid_master (valid_master),\n")
    hpf.write(".last_master  (last_master ),\n")
    hpf.write(".ready_master (ready_master)\n);\n\n")

if (data_length_str != ""):
    hpf.write(hd_packer_name + " " + hd_packer_name + "1(\n")
    hpf.write(".clk(clk),\n")
    hpf.write(".rst(rst),\n")
    if (data_protocol == "AXIS"):
        hpf.write("//Input AXI Stream Interface\n")
        hpf.write(".data_slave(data_master1),\n")
        hpf.write(".keep_slave(keep_master1),\n")
        hpf.write(".valid_slave(valid_master1),\n")
        hpf.write(".last_slave(last_master1),\n")
        hpf.write(".ready_slave(ready_master1),\n")
    
        hpf.write("\n")
        hpf.write("//Input results\n")
        for entry in parser_vector:
            hpf.write("." + entry[0] + "(" + entry[0] + "1),\n")
    
        hpf.write("\n")
        hpf.write("//Output AXI Stream Interface\n")
        if (data_length_str != ""):
            hpf.write(".data_master  (data_master2),\n")
            hpf.write(".keep_master  (keep_master2),\n")
            hpf.write(".valid_master (valid_master2),\n")
            hpf.write(".last_master  (last_master2),\n")
            hpf.write(".ready_master (ready_master2)\n);\n\n")


hpf.write(hd_parser_name + " " + hd_parser_name + "0(\n")
hpf.write(".clk(clk),\n")
hpf.write(".rst(rst),\n")
if (data_protocol == "AXIS"):
    hpf.write("//Input AXI Stream Interface\n")
    hpf.write(".data_slave(data_master),\n")
    hpf.write(".keep_slave(keep_master),\n")
    hpf.write(".valid_slave(valid_master),\n")
    hpf.write(".last_slave(last_master),\n")
    hpf.write(".ready_slave(ready_master),\n")

    hpf.write("\n")
    hpf.write("//Input results\n")
    for entry in parser_vector:
        hpf.write("." + entry[0] + "(" + entry[0] + "1),\n")

    hpf.write("\n")
    hpf.write("//Output AXI Stream Interface\n")
    if (data_length_str != ""):
        hpf.write(".data_master  (data_master1),\n")
        hpf.write(".keep_master  (keep_master1),\n")
        hpf.write(".valid_master (valid_master1),\n")
        hpf.write(".last_master  (last_master1),\n")
        hpf.write(".ready_master (ready_master1)\n);\n\n")
    else:
        hpf.write(".valid_master (valid_master3),\n")
        hpf.write(".ready_master (ready_master3)\n);\n\n")


if (data_length_str != ""):
    hpf.write(hd_parser_name + " " + hd_parser_name + "1(\n")
    hpf.write(".clk(clk),\n")
    hpf.write(".rst(rst),\n")
    if (data_protocol == "AXIS"):
        hpf.write("//Input AXI Stream Interface\n")
        hpf.write(".data_slave(data_master2),\n")
        hpf.write(".keep_slave(keep_master2),\n")
        hpf.write(".valid_slave(valid_master2),\n")
        hpf.write(".last_slave(last_master2),\n")
        hpf.write(".ready_slave(ready_master2),\n")
    
        hpf.write("\n")
        hpf.write("//Input results\n")
        for entry in parser_vector:
            hpf.write("." + entry[0] + "(" + entry[0] + "3),\n")
    
        hpf.write("\n")
        hpf.write("//Output AXI Stream Interface\n")
        if (data_length_str != ""):
            hpf.write(".data_master  (data_master3),\n")
            hpf.write(".keep_master  (keep_master3),\n")
            hpf.write(".valid_master (valid_master3),\n")
            hpf.write(".last_master  (last_master3),\n")
            hpf.write(".ready_master (ready_master3)\n);\n\n")

if (data_length_str != ""):
    hpf.write('''task burst(
''')
    for entry in parser_vector:
        hpf.write("input  [" + '{:<4}'.format(str(entry[1]-1)) + " : 0]    " + entry[0] + "_tsk,\n")

    hpf.write('''input  [''' + '{:<4}'.format(str(data_width * 8 - 1)) + ''' : 0]    data_tsk,
input  [31   : 0]    length_tsk
);
reg flag;
begin
    i = 0;
    flag = 0;
    @(posedge clk);
    while(i < length_tsk - 1)
    begin
        data_slave  = data_tsk;
        valid_slave = 1;
        keep_slave  = -1;
        last_slave  = 0;
''')
    for entry in parser_vector:
        hpf.write("        " + entry[0] + " = " + entry[0] + "_tsk;\n")

    hpf.write('''

        @(posedge clk);
        //if (ready_slave) $display ("1");
        if (ready_slave) i = i + 1;
        else             i = i;
        
    end

    do begin
        data_slave  = data_tsk;
        valid_slave = 1;
        keep_slave  = -1;
        last_slave  = 1;
''')
    for entry in parser_vector:
        hpf.write("        " + entry[0] + " = " + entry[0] + "_tsk;\n")

    hpf.write('''
        #1;
        if (ready_slave) flag = 1;
        @(posedge clk);
    end while(~flag);
        
end
endtask

''')

    hpf.write('''task interval;
begin
        data_slave  = 0;
        valid_slave = 0;
        keep_slave  = 0;
        last_slave  = 0;
''')
# for entry in parser_vector:
#     hpf.write("        " + entry[0] + " = 0;\n") 
    hpf.write('''    
end
endtask

''')
else:
    hpf.write('''task burst(
''')
    entry_indicators = range(0,len(parser_vector))
    for entry,entry_id in zip(parser_vector,entry_indicators):
        hpf.write("input  [" + '{:<4}'.format(str(entry[1]-1)) + " : 0]    " + entry[0] + "_tsk")
        if (entry_id == len(parser_vector) - 1):
            hpf.write("")
        else:
            hpf.write(",\n")

    hpf.write('''
);
reg flag;
begin
    flag = 0;
    do begin
        valid_slave = 1;
''')
    for entry in parser_vector:
        hpf.write("        " + entry[0] + " = " + entry[0] + "_tsk;\n")

    hpf.write('''
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

''')

hpf.write("endmodule")
