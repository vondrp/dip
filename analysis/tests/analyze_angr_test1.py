import angr
import claripy

def analyze_function(binary_path):
    proj = angr.Project(binary_path, auto_load_libs=False, arch="ARMEL")  # ARM 32-bit

    # Najdeme adresu funkce (pokud není v symbolech, použij objdump/readelf)
    func_addr = proj.loader.find_symbol("check_error_code").rebased_addr

    # Symbolický vstupní parametr (int = 32bit)
    arg = claripy.BVS("arg", 32)

    # Vytvoření ARM stavu simulujícího volání funkce
    state = proj.factory.call_state(func_addr, arg)

    # Opravy neznámých registrů (důležité pro stabilitu)
    state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_MEMORY)
    state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_REGISTERS)

    simgr = proj.factory.simulation_manager(state)

    # Hledáme, kdy funkce vrátí 1 (ARM používá R0 jako návratovou hodnotu)
    def is_interesting(state):
        return state.solver.eval(state.regs.r0) == 1  # R0 obsahuje návratovou hodnotu

    simgr.explore(find=is_interesting)

    if simgr.found:
        found_state = simgr.found[0]
        solution = found_state.solver.eval(arg)
        print(f"Vstup vedoucí k chybě: {solution}")
    else:
        print("Žádný problémový vstup nenalezen.")

if __name__ == "__main__":
    analyze_function("./build/test_1_arm.elf")
