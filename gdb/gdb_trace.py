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

        # 🟢 Získáme základní adresu `.text` sekce
        text_base_address = gdb.execute("info proc mappings", to_string=True)
        for line in text_base_address.split("\n"):
            if "r-xp" in line and "test_program.elf" in line:  # Hledáme správnou sekci
                text_base = line.split()[0]  # První hodnota je začátek sekce
                break
        else:
            text_base = "0x0"  # Defaultní hodnota pokud nenalezeno

        with open(output_file, "w") as f:
            # 🟢 Zapíšeme offset do logu
            f.write(f"TEXT_BASE {text_base}\n")

            while thread.is_valid():
                frame = gdb.newest_frame()
                pc = frame.pc()
                instr = frame.architecture().disassemble(pc)[0]['asm']
                function_name = frame.name()

                f.write(f"{function_name}, {hex(pc)}: {instr}\n")
                gdb.execute("si", to_string=True)

TraceAsm()
