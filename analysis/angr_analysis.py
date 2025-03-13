import angr
import sys
import subprocess

BINARY_PATH = "build/test_program"

def analyze_cfg(binary_path):
    """
    Vygeneruje a analyzuje Control Flow Graph (CFG).
    """
    print(f"\nNačítám binární soubor: {binary_path}")
    proj = angr.Project(binary_path, auto_load_libs=False)

    print("Generuji Control Flow Graph (CFG)...")
    cfg = proj.analyses.CFGEmulated()

    print("\nNalezené funkce:")
    relevant_functions = [func for func in cfg.kb.functions.values() if not func.name.startswith("sub_") and "Unresolvable" not in func.name]

    for func in relevant_functions:
        print(f"  - {func.name} (adresa: {hex(func.addr)})")

    return proj, cfg, relevant_functions

def find_unreachable_code(cfg, functions):
    """
    Hledá neprozkoumané části kódu.
    """
    print("\nHledám neprozkoumané části kódu...")
    unreachable_functions = [func for func in functions if not func.block_addrs]

    if unreachable_functions:
        print("Nalezeny neprozkoumané funkce:")
        for func in unreachable_functions:
            print(f"  - {func.name} (adresa: {hex(func.addr)})")
    else:
        print("Všechny důležité funkce jsou dosažitelné.")

def find_zero_division(proj):
    """
    Hledá možné dělení nulou pomocí symbolické exekuce.
    """
    print("\nHledám dělení nulou...")
    state = proj.factory.entry_state()
    simgr = proj.factory.simulation_manager(state)

    def is_zero_division(state):
        try:
            if state.solver.eval(state.regs.rax) == 0:
                return True
        except:
            return False
        return False

    simgr.explore(find=is_zero_division)

    if simgr.found:
        print("Nalezeno možné dělení nulou!")
        for found in simgr.found:
            addr = found.addr
            instr = get_instruction_at(proj, addr)
            source_info = get_source_line(BINARY_PATH, addr)

            print(f"  - Adresa: {hex(addr)}")
            print(f"    Instrukce: {instr}")
            print(f"    Zdrojový kód: {source_info if source_info else 'Nepodařilo se zjistit zdrojový kód'}")
    else:
        print("Nebyla nalezena žádná situace s dělením nulou.")

def get_instruction_at(proj, addr):
    """
    Disassembluje instrukci na dané adrese.
    """
    try:
        block = proj.factory.block(addr)
        if block.capstone.insns:
            return block.capstone.insns[0].insn.mnemonic + " " + block.capstone.insns[0].insn.op_str
        return "Neznámá instrukce"
    except:
        return "Neznámá instrukce"

def get_source_line(binary_path, addr):
    """
    Použije `addr2line` pro získání odpovídajícího řádku zdrojového kódu.
    """
    try:
        result = subprocess.run(["addr2line", "-e", binary_path, hex(addr)], stdout=subprocess.PIPE, text=True)
        line = result.stdout.strip()

        if "??" in line:
            return None
        return line
    except:
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        BINARY_PATH = sys.argv[1]

    proj, cfg, functions = analyze_cfg(BINARY_PATH)
    find_unreachable_code(cfg, functions)
    find_zero_division(proj)

    print("\nAnalýza dokončena.")
