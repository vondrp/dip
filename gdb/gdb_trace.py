import gdb

class TraceAsm(gdb.Command):
    def __init__(self):
        super().__init__("trace-asm", gdb.COMMAND_USER)

    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        if len(argv) != 1:
            gdb.write("Použití: trace-asm <output_file>\n")
            return
        
        output_file = argv[0]    
        thread = gdb.inferiors()[0].threads()[0]

        text_base = "0x0"
        text_base_address = gdb.execute("info proc mappings", to_string=True)
        for line in text_base_address.split("\n"):
            if "r-xp" in line and "test_binary" in line:
                text_base = line.split()[0]
                break

        with open(output_file, "w") as f:
            f.write(f"TEXT_BASE {text_base}\n")
            gdb.write("Spuštěna analýza instrukcí... (běží v pozadí)\n")

            while thread.is_valid():
                frame = gdb.newest_frame()
                function_name = frame.name()

                if function_name:
                    pc = frame.pc()
                    instr = frame.architecture().disassemble(pc)[0]['asm']
                    
                    if instr.startswith("call") or instr.startswith("jmp"):
                        called_function = instr.split()[-1]
                        f.write(f"[CALL] {function_name} -> {called_function}\n")

                    f.write(f"{function_name}, {hex(pc)}: {instr}\n")

                gdb.execute("si", to_string=True)

        gdb.write("Analýza dokončena. Výstup v trace.log\n")

TraceAsm()
