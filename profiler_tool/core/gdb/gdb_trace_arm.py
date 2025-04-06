import gdb

class TraceAsmARM(gdb.Command):
    def __init__(self):
        super().__init__("trace-asm-arm", gdb.COMMAND_USER)

    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        if len(argv) != 2:
            gdb.write("Použití: trace-asm-arm <output_file> <temp_func_file>\n")
            return

        output_file = argv[0]
        functions_file = argv[1]
        function_names = set()
        with open(functions_file) as f:
            for line in f:
                name = line.strip()
                if name:
                    function_names.add(name)

        gdb.write(f"Počet v funciton names: {len(function_names)}\n")
        # Pokusíme se najít textovou základnu
        text_base = "0x0"
        try:
            text_base_address = gdb.execute("info proc mappings", to_string=True)
            for line in text_base_address.split("\n"):
                if "r-xp" in line and "test_binary" in line:
                    text_base = line.split()[0]
                    break
        except Exception as e:
            gdb.write(f"[WARN] Nepodařilo se získat mappingy: {e}\n")

        with open(output_file, "w") as f:
            f.write(f"TEXT_BASE {text_base}\n")
            gdb.write("Spuštěna analýza instrukcí (ARM)... (běží v pozadí)\n")

            # Nejprve necháme binárku běžet
            # gdb.execute("continue", to_string=True)

            # Po návratu z continue zkusíme trace (pokud program neskončil)
            try:
                inferior = gdb.inferiors()[0]
                if not inferior.is_valid():
                    gdb.write("[INFO] Program byl ukončen, žádné instrukce ke sledování.\n")
                    return

                thread = inferior.threads()[0]
                thread.switch()
                frame = gdb.newest_frame()

                while frame is not None and frame.is_valid():
                    try:
                        pc = frame.pc()
                        disasm = frame.architecture().disassemble(pc)
                        function_name = frame.name() or "???"

                        if disasm:
                            instr = disasm[0]['asm']

                            if instr.startswith("bl") or instr.startswith("blx") or instr.startswith("b "):
                                called_function = instr.split()[-1]
                                f.write(f"[CALL] {function_name} -> {called_function}\n")
                                called_function = instr.split()[-1].strip('<>')  # Odstraníme < a > z názvu funkce

                                # Pokud volaná funkce není naše, použijeme nexti
                                if called_function not in function_names:
                                    f.write(f"{function_name}, {hex(pc)}: {instr}\n")
                                    gdb.execute("nexti", to_string=True)
                                    frame = gdb.newest_frame()
                                    continue

                                    

                            f.write(f"{function_name}, {hex(pc)}: {instr}\n")
                        else:
                            gdb.write(f"[WARN] Disasm selhal na {hex(pc)}\n")

                        gdb.execute("stepi", to_string=True)
                        frame = gdb.newest_frame()
                    except Exception as e:
                        gdb.write(f"[ERROR] Chyba během trace: {e}\n")
                        break

            except Exception as e:
                gdb.write(f"[ERROR] Trace se nezdařil: {e}\n")

            gdb.write("Analýza dokončena. Výstup v trace.log\n")

TraceAsmARM()
