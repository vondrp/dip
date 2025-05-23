import gdb
import re
import json
import os

# ---------- trace_config.py LOGIKA ----------
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "trace_config.json"))

_blacklist_patterns = []
_blacklist_regexes = []

def _load_blacklist_config():
    global _blacklist_patterns, _blacklist_regexes

    try:
        gdb.write(f"[INFO] Načítám konfiguraci z {CONFIG_PATH}\n")
        if not os.path.exists(CONFIG_PATH):
            gdb.write(f"[WARN] Soubor nenalezen: {CONFIG_PATH}\n")
            return

        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            _blacklist_patterns = config.get("function_blacklist_patterns", [])
            _blacklist_regexes = [re.compile(p) for p in _blacklist_patterns]

        gdb.write(f"[INFO] Načteno {len(_blacklist_patterns)} vzorů pro blacklist.\n")

    except Exception as e:
        gdb.write(f"[ERROR] Nepodařilo se načíst konfiguraci: {e}\n")

def is_blacklisted_function(function_name: str) -> bool:
    if not _blacklist_regexes:
        _load_blacklist_config()

    return any(regex.search(function_name) for regex in _blacklist_regexes)

# ---------- konec trace_config.py LOGIKY ----------


class TraceAsmRISCV(gdb.Command):
    def __init__(self):
        super().__init__("trace-asm-riscv", gdb.COMMAND_USER)

    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        if len(argv) != 1:
            gdb.write("Použití: trace-asm-riscv <output_file>\n")
            return

        output_file = argv[0]

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
            gdb.write("Spuštěna analýza instrukcí (RISC-V)... (běží v pozadí)\n")

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

                            if instr.startswith("jal") or instr.startswith("jalr"):
                                called_function = instr.split()[-1]
                                f.write(f"[CALL] {function_name} -> {called_function}\n")
                                called_function = instr.split()[-1].strip('<>')

                                if is_blacklisted_function(called_function):
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

TraceAsmRISCV()
