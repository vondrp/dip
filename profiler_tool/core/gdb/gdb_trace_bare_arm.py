import gdb

class TraceAsmARM(gdb.Command):
    """ Vlastní příkaz `trace-asm-arm` pro sledování instrukcí na bare-metal ARM. """
    
    def __init__(self):
        super().__init__("trace-asm-arm", gdb.COMMAND_USER)

    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        if len(argv) != 1:
            gdb.write("Použití: trace-asm-arm <output_file>\n")
            return
        
        output_file = argv[0]
        gdb.write(f"Spouštěna analýza instrukcí... Výstup: {output_file}\n")

        # **Ověření, zda PC není nulové (chyba v QEMU)**
        try:
            pc = gdb.parse_and_eval("$pc")
            if int(pc) == 0:
                gdb.write("❌ CHYBA: PC je nulové! Možná špatná inicializace QEMU.\n")
                return
        except gdb.error:
            gdb.write("❌ CHYBA: Nelze načíst hodnotu PC.\n")
            return
        
        # **Nastavení startovní adresy PC a SP**
        gdb.execute("set $pc = 0x8000", to_string=True)
        gdb.execute("set $sp = 0x810000", to_string=True)  # Stack pointer na vhodnou adresu

        with open(output_file, "w") as f:
            while True:
                try:
                    # **Kontrola platnosti registrů**
                    pc = gdb.parse_and_eval("$pc")
                    if int(pc) == 0:
                        gdb.write("❌ CHYBA: PC je 0x00000000! Možná špatné spouštění.\n")
                        break

                    # **Disassemblujeme aktuální instrukci**
                    instr = gdb.execute(f"x/i {pc}", to_string=True).strip()

                    # **Zapíšeme do souboru**
                    f.write(f"{instr}\n")

                    # **Krok na další instrukci**
                    gdb.execute("stepi", to_string=True)

                except gdb.error as e:
                    gdb.write(f"❌ Chyba během trace: {e}\n")
                    break

        gdb.write("✅ Analýza dokončena.\n")

# **Zaregistrujeme příkaz v GDB**
TraceAsmARM()
