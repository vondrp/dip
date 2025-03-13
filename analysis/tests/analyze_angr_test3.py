import angr
import claripy
from angr.exploration_techniques.stochastic import StochasticSearch


def setup_project(binary_path, arch):
    """Inicializuje projekt angr pro daný binární soubor."""
    if arch == "ARM":
        proj = angr.Project(binary_path, auto_load_libs=False, arch="ARMEL")
    elif arch == "x86":
        proj = angr.Project(binary_path, auto_load_libs=False, arch="X86")
    else:
        raise ValueError("Podporované architektury jsou pouze 'ARM' nebo 'x86'.")
    
    return proj    

def get_function_and_result_addresses(proj):
    """Získá adresy funkce compute a globální proměnné result."""
    func_addr = proj.loader.find_symbol("compute").rebased_addr
    result_addr = proj.loader.find_symbol("result").rebased_addr
    return func_addr, result_addr

def create_symbolic_inputs():
    """Vytvoří symbolické vstupy (dvě 32bitové hodnoty)."""
    arg1 = claripy.BVS("arg1", 32)
    arg2 = claripy.BVS("arg2", 32)
    return arg1, arg2

def create_initial_state(proj, func_addr, arg1, arg2):
    """Vytvoří počáteční stav pro volání funkce compute(a, b)."""
    state = proj.factory.call_state(func_addr, arg1, arg2)
    state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_MEMORY)
    state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_REGISTERS)
    return state

def is_interesting(state, result_addr, proj):
    """Určuje, zda je daný stav zajímavý na základě změn hodnoty result."""
    possible_results = state.solver.eval_upto(
        state.memory.load(result_addr, 4, endness=proj.arch.memory_endness), 5
    )
    
    if all(val == 0 for val in possible_results):
        return False
    
    return any(abs(val) > 100 for val in possible_results) or any(val != 0 for val in possible_results)

def run_analysis(binary_path, arch = "ARM", max_tests=10):
    """Spouští analýzu binárního souboru pomocí angr a hledá zajímavé testovací vstupy."""
    proj = setup_project(binary_path, arch)
    func_addr, result_addr = get_function_and_result_addresses(proj)
    arg1, arg2 = create_symbolic_inputs()
    state = create_initial_state(proj, func_addr, arg1, arg2)
    
    simgr = proj.factory.simulation_manager(state, veritesting=True)
    
    simgr.use_technique(angr.exploration_techniques.DFS())
    #simgr.use_technique(StochasticSearch(start_state=state))
    simgr.explore(find=lambda s: is_interesting(s, result_addr, proj), num_find=max_tests)
    
    test_cases = extract_test_cases(simgr, arg1, arg2, max_tests)
    save_test_cases(test_cases)

def extract_test_cases(simgr, arg1, arg2, max_tests):
    """Extrahuje nalezené testovací vstupy ze stavů nalezených simulátorem."""
    test_cases = set()
    for found_state in simgr.found[:max_tests]:
        solutions1 = found_state.solver.eval_upto(arg1, 5)
        solutions2 = found_state.solver.eval_upto(arg2, 5)

        for s1, s2 in zip(solutions1, solutions2):
            test_cases.add((s1, s2))
            print(f"Vygenerovaný vstup: a={s1}, b={s2}")
    
    return test_cases

def save_test_cases(test_cases):
    """Uloží testovací vstupy do souboru test_inputs.txt."""
    with open("test_inputs.txt", "w") as f:
        for a, b in test_cases:
            f.write(f"{a} {b}\n")
    print(f"Uloženo {len(test_cases)} testovacích vstupů do 'test_inputs.txt'.")

if __name__ == "__main__":
    run_analysis("./build/program_x86", arch="x86", max_tests=10000)
    #run_analysis("./build/test_3.elf", arch="ARM", max_tests=100)
