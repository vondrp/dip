import angr
import claripy

def analyze_function(binary_path):
    proj = angr.Project(binary_path, auto_load_libs=False, arch="ARMEL")

    func_addr = proj.loader.find_symbol("check").rebased_addr

    # Symbolické vstupy (dvě 32bitové hodnoty)
    arg1 = claripy.BVS("arg1", 32)
    arg2 = claripy.BVS("arg2", 32)

    state = proj.factory.call_state(func_addr, arg1, arg2)

    # 🛠️ Oprava: Naplnění neznámých registrů a paměti nulami
    state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_MEMORY)
    state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_REGISTERS)

    simgr = proj.factory.simulation_manager(state)

    def is_interesting(state):
        return state.solver.eval(state.regs.r0) == 1  # Funkce vrací 1

    simgr.explore(find=is_interesting)

    if simgr.found:
        found_state = simgr.found[0]
        solution1 = found_state.solver.eval(arg1)
        solution2 = found_state.solver.eval(arg2)
        print(f"✅ Vstupy vedoucí k úspěchu: {solution1}, {solution2}")
    else:
        print("❌ Žádný úspěšný vstup nenalezen.")

if __name__ == "__main__":
    analyze_function("./build/test_2_arm.elf")
