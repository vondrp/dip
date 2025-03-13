set pagination off
set logging file trace.log
set logging on
file build/program_x86
start

set logging overwrite on

while 1
    if $pc >= 0x1070 && $pc < 0x1300 
        printf "%x: ", $pc
        x/i $pc
        x/5i $pc
    end
    stepi 
    if $pc == 0x0
        break
    end
end

set logging off
quit
