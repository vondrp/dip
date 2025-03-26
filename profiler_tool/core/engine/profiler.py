import os
import re

from core.config import BASE_DIR
from core.engine.generator import generate_main, generate_main_klee, generate_main_arm
from core.engine.compiler import compile_x86, compile_klee, compile_arm_bm
from core.engine.tracer import run_gdb_trace, run_gdb_trace_arm_bm
#from core.engine.analyzer import analyze_traces, compare_runs
from core.engine.klee_runner import get_klee_test_inputs

def cleanup():
    """Odstraní `generated_main.c`."""
    if os.path.exists(GENERATED_MAIN):
        os.remove(GENERATED_MAIN)
        print("[INFO] Smazán `generated_main.c`")

    if os.path.exists(GENERATED_MAIN_KLEE):
        os.remove(GENERATED_MAIN_KLEE) 
        print("[INFO] Smazán `generated_main_klee.c`")
  

def extract_functions_and_params(source_file):
    """Najde definice funkcí a jejich parametry v souboru."""
    functions = {}
    with open(source_file, "r") as f:
        for line in f:
            match = re.match(r"^\s*(\w+)\s+(\w+)\s*\((.*?)\)", line)
            if match:
                return_type, func_name, params = match.groups()
                param_list = [p.strip() for p in params.split(",") if p]
                functions[func_name] = param_list
    return functions

def select_target_function(src_file):
    functions = extract_functions_and_params(src_file)
    if not functions:
        print("Nenalezeny žádné funkce v souboru.")
        exit(1)
    
    print("Nalezené funkce:")
    for func, params in functions.items():
        print(f" - {func}({', '.join(params)})")
    
    target_function = input("Zadej jméno funkce k testování: ")
    if target_function not in functions:
        print("Neplatná funkce.")
        exit(1)
    
    return target_function, functions[target_function], functions

def prepare_directories(target_function):
    trace_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs", target_function)
    os.makedirs(trace_dir, exist_ok=True)
    
    klee_dir = os.path.join(trace_dir, "klee")
    os.makedirs(klee_dir, exist_ok=True)
    
    return trace_dir, klee_dir


def get_function_params(function_params):
    param_values = []
    for param in function_params:
        value = input(f"Zadej hodnotu pro `{param}`: ")
        param_values.append(value)

    return param_values    


def run_klee_analysis(target_function, functions, param_types, klee_dir, src_file, src_dir):
    bitcode_file = os.path.join(klee_dir, "klee_program.bc")
    generate_main_klee(target_function, functions[target_function])
    compile_klee(klee_dir, src_file, src_dir)
    
    file_path, test_data = get_klee_test_inputs(klee_dir, bitcode_file, param_types)
    print(f"[INFO] 📁 Testovací vstupy uloženy: {file_path}")
    return test_data


def main():
    """ Hlavní orchestrátor profilování """
    print("[INFO] 🔍 Spouštím profiler...")
    
    src_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", "src", "test_program.c")
    src_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "src")


    # 1️⃣ Výběr cílové funkce a parametrů
    target_function, param_types, functions = select_target_function(src_file)
    param_values = get_function_params(functions[target_function])
    param_str = "_".join(param_values).replace(" ", "")
    
    # 2️⃣ Příprava adresářů
    trace_dir, klee_dir = prepare_directories(target_function)
    
    # 3️⃣ Generování main souborů a kompilace
    generate_main(target_function, functions[target_function])
    binary_file = os.path.join(BASE_DIR, "build", f"test_{target_function}_{param_str}")
    compile_x86(binary_file=binary_file, src_file=src_file, src_dir = src_dir)
    
    # 4️⃣ Spuštění KLEE a získání testovacích vstupů
    test_data = run_klee_analysis(target_function, functions, param_types, klee_dir, src_file, src_dir)
    #generate_main_klee(target_function, functions[target_function])
    #klee_bitcode = compile_klee(klee_dir)
    #klee_inputs = get_klee_test_inputs(klee_dir, klee_bitcode, param_types)
    
    """
    # 5️⃣ Spuštění trace běhů
    trace_file_user = os.path.join(trace_dir, f"trace_{target_function}_{param_str}.log")
    run_gdb_trace(binary_file, trace_file_user, param_values)
    
    for i, klee_params in enumerate(klee_inputs):
        trace_file_klee = os.path.join(trace_dir, f"trace_{target_function}_{i}.log")
        run_gdb_trace(binary_file, trace_file_klee, klee_params)
    
    # 6️⃣ Analýza výsledků
    analyze_traces(trace_dir)
    compare_runs(trace_dir)
    
    print("[INFO] ✅ Profilování dokončeno.")
    """

if __name__ == "__main__":
    main()
