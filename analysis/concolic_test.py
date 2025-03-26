import angr
import claripy
import os
import struct

from angr.exploration_techniques import Veritesting, LoopSeer, StochasticSearch

# ⚙ Konfigurace
BINARY_PATH = os.path.join(os.path.dirname(__file__), "..", "build", "angr_compute")
TARGET_FUNCTION = "compute"

def create_symbolic_arguments(arg_types):
    """
    Vytvoří symbolické vstupy podle předaných typů parametrů.
    """
    symbolic_args = []
    for i, arg_type in enumerate(arg_types):
        if arg_type == "int":
            symbolic_args.append(claripy.BVS(f"int_arg_{i}", 32))
        elif arg_type == "double":
            symbolic_args.append(claripy.BVS(f"double_arg_{i}", 64))  # 64-bitová reprezentace
        elif arg_type == "char":
            symbolic_args.append(claripy.BVS(f"char_arg_{i}", 8))
        else:
            print(f"[WARNING] Neznámý typ `{arg_type}`, používám `int` jako výchozí hodnotu.")
            symbolic_args.append(claripy.BVS(f"unknown_arg_{i}", 32))  # Defaultně `int`
    return symbolic_args

def should_explore(state):
    """
    Určuje, zda je stav zajímavý na základě možných hodnot.
    """
    rdi_val = state.solver.eval(state.regs.rdi, cast_to=int)
    rsi_val = state.solver.eval(state.regs.rsi, cast_to=int)

    if rdi_val == 42:
        print(f"[DEBUG] ✅ Nalezen stav, kde `rdi == 42`!")
        return True

    if rsi_val == 0:
        print(f"[DEBUG] ⚠️ Nalezen stav, kde `rsi == 0` (dělení nulou?)")
        return True

    return False

def extract_test_cases(simgr, symbolic_args, param_types):
    """
    Extrahuje a správně vypíše hodnoty nalezených vstupů.
    """
    test_cases = set()
    for found in simgr.found:
        extracted_values = []
        for arg, arg_type in zip(symbolic_args, param_types):
            if arg_type == "double":
                int_value = found.solver.eval(arg, cast_to=int)
                value = struct.unpack('d', struct.pack('Q', int_value))[0]  # Převod na double
            elif arg_type == "char":
                int_value = found.solver.eval(arg, cast_to=int)
                value = chr(int_value) if 0 <= int_value <= 255 else '?'
            else:
                value = found.solver.eval(arg, cast_to=int)
            extracted_values.append(value)

        test_cases.add(tuple(extracted_values))

    return list(test_cases)

def concolic_test(binary_path, function_name, param_types):
    """
    Spustí konkolické testování pro zadanou binárku a funkci.
    """
    print(f"[INFO] 🚀 Spouštím konkolické testování na `{binary_path}` s funkcí `{function_name}`")
    print(f"[INFO] 📌 Parametry: {param_types}")

    proj = angr.Project(binary_path, auto_load_libs=False)

    # 📍 Získáme adresu funkce
    cfg = proj.analyses.CFGFast()
    function = cfg.kb.functions.function(name=function_name)
    if not function:
        print(f"[ERROR] ❌ Funkce `{function_name}` nebyla nalezena.")
        return

    function_addr = function.addr
    print(f"[INFO] ✅ Funkce `{function_name}` nalezena na adrese: {hex(function_addr)}")

    # 📌 Vytvoříme symbolické proměnné podle zadaných parametrů
    symbolic_args = create_symbolic_arguments(param_types)

    # 🏁 Vytvoříme počáteční stav pro symbolickou exekuci
    state = proj.factory.call_state(function_addr, *symbolic_args)
    state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_MEMORY)
    state.options.add(angr.options.ZERO_FILL_UNCONSTRAINED_REGISTERS)
    state.options.add(angr.options.LAZY_SOLVES)  # Zabrání slučování stavů

    # 🌍 Simulation manager s lepšími technikami
    simgr = proj.factory.simulation_manager(state)
    simgr.use_technique(Veritesting())  # Zlepší analýzu podmínek
    simgr.use_technique(LoopSeer())  # Lepší průchod smyčkami
    #simgr.use_technique(StochasticSearch(start_state=state))  # Náhodné prozkoumávání větví

    print("[INFO] 🧠 Spouštím konkolické testování...")
    simgr.explore(find=should_explore, num_find=50)

    # 📌 Výpis dostupných stashů
    print(f"[INFO] 📦 Dostupné stashe: {simgr.stashes.keys()}")

    # 📌 Výstup nalezených vstupů
    test_cases = extract_test_cases(simgr, symbolic_args, param_types)

    if test_cases:
        print("[INFO] ✅ Nalezené vstupy vedoucí k různým větvím:")
        for case in test_cases:
            print(f"  - {case}")
    else:
        print("[WARNING] ❌ Nebyly nalezeny žádné nové vstupy.")

if __name__ == "__main__":
    # 🛠 Testovací volání – v `generate_run.py` se to nahradí skutečnými hodnotami
    TEST_PARAM_TYPES = ["int", "int"]
    concolic_test(BINARY_PATH, TARGET_FUNCTION, TEST_PARAM_TYPES)
