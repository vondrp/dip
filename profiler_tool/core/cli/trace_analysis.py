import os
import re
from core.cli.file_selection import fzf_select_file
from core.engine.tracer import run_gdb_trace, run_gdb_trace_arm_linux
from core.engine.trace_analysis import analyze_trace
from core.config import BUILD_DIR, TRACE_DIR, ANALYSIS_DIR

def extract_function_name(binary_file):
    """Extrahuje jméno funkce z názvu binárního souboru."""
    match = re.search(r"binary_\w+_(\w+)\.out", os.path.basename(binary_file))
    return match.group(1) if match else "unknown"

def trace_analysis(binary_file=None, param_file=None, isArm = False):
    """Umožní uživateli vybrat binární soubor a spustit trace pro více sad parametrů."""

    if not binary_file:
        print("\n[INFO] Vyber binární soubor:")
        binary_file = fzf_select_file(".out", BUILD_DIR)

    if not binary_file or not os.path.exists(binary_file):
        print("[ERROR] Nebyla vybrána žádná binárka.")
        return

    func_name = extract_function_name(binary_file)
    param_sets = []

    # Načtení parametrů ze souboru, pokud je zadán
    if param_file:
        if not os.path.exists(param_file):
            print(f"[ERROR] Soubor {param_file} neexistuje!")
            return

        with open(param_file, "r") as f:
            for line in f:
                params = line.strip().split()
                param_sets.append(params)
        
        print(f"[INFO] Načteno {len(param_sets)} sad parametrů ze souboru `{param_file}`.")

    # Ruční zadání parametrů, pokud nebyl dodán soubor
    if not param_sets:
        print("\n[INFO] Zadej sady parametrů pro spuštění (každou sadu potvrď Enterem).")
        print("[INFO] Dvakrát Enter (prázdný řádek) ukončí zadávání.")
        print("[INFO] Pokud funkce nemá žádné parametry, jen stiskni Enter.")

        while True:
            param_input = input("[INPUT] Parametry: ").strip()
            if param_input == "" and len(param_sets) > 0:
                break  # Konec zadávání po druhém Enteru
            param_sets.append(param_input.split())

    if not param_sets:
        param_sets.append([])  # Prázdná sada, pokud uživatel nic nezadá

    # Spuštění trace a analýzy pro každou sadu parametrů
    for params in param_sets:
        param_str = "_".join(params) if params else "no_params"

        if isArm:
            trace_file = os.path.join(TRACE_DIR, f"traceArm_{func_name}_{param_str}.log")
            print(f"\n[INFO] Spouštím trace pro {binary_file} s parametry {params}")
            run_gdb_trace_arm_linux(binary_file, trace_file, params)
        else:    
            trace_file = os.path.join(TRACE_DIR, f"trace_{func_name}_{param_str}.log")
            print(f"\n[INFO] Spouštím trace pro {binary_file} s parametry {params}")
            run_gdb_trace(binary_file, trace_file, params)
        print(f"[INFO] Trace dokončen! Výstup: {trace_file}")

        # Spuštění analýzy trace souboru
        output_json_dir = os.path.join(ANALYSIS_DIR, func_name)
        os.makedirs(output_json_dir, exist_ok=True)

        if isArm:
            json_filename = f"instructionsArm_{func_name}_{param_str}.json"
        else:
            json_filename = f"instructions_{func_name}_{param_str}.json"
        
        output_json = os.path.join(output_json_dir, json_filename)

        print(f"\n[INFO] Probíhá analýza pro trace soubor: {trace_file}")
        analyze_trace(trace_file, binary_file, func_name, output_json)
        print(f"[INFO] Analýza dokončena! Výstupní soubor: {output_json}")
