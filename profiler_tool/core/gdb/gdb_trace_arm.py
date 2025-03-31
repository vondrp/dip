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

        # 🔹 Získání TEXT_BASE adresy
        text_base = "0x0"
        mappings = gdb.execute("info proc mappings", to_string=True)
        for line in mappings.split("\n"):
            if "r-xp" in line and "binary_" in line:  # Uprav podle názvu binárky
                text_base = line.split()[0]
                break

        with open(output_file, "w") as f:
            f.write(f"TEXT_BASE {text_base}\n")  # Uložení základní adresy
            gdb.write("Spuštěna analýza instrukcí... (běží v pozadí)\n")

            while thread.is_valid():
                frame = gdb.newest_frame()  

                if frame:
                    pc = int(gdb.parse_and_eval("$pc"))  # Program Counter
                    instr_data = frame.architecture().disassemble(pc)[0]
                    instr = instr_data['asm']

                    # 🔹 Získání názvu funkce
                    function_name = frame.name()
                    if not function_name:
                        try:
                            symbol_info = gdb.execute(f"info symbol {pc}", to_string=True).strip()
                            function_name = symbol_info.split()[0] if "No symbol matches" not in symbol_info else "??"
                        except:
                            function_name = "??"

                    # 🔹 Detekce volání funkcí (CALL, BL, BLX)
                    if instr.startswith("bl") or instr.startswith("blx") or instr.startswith("call"):
                        called_function = instr.split()[-1]
                        f.write(f"[CALL] {function_name} -> {called_function}\n")

                    # 🔹 Formátování výstupu
                    f.write(f"{function_name}, {hex(pc)}: {instr}\n")

                gdb.execute("si", to_string=True)  # Krokování po instrukcích

        gdb.write("Analýza dokončena. Výstup v trace.log\n")

TraceAsm()
