import os
import re
import shlex
from core.cli.file_selection import fzf_select_file
from core.engine.tracer import run_gdb_trace, run_gdb_trace_arm_linux
from core.engine.trace_analysis import analyze_trace
from config import BUILD_DIR, TRACE_DIR, ANALYSIS_DIR, DEFAULT_ARCHITECTURE
from config import log_info, log_debug, log_warning, log_error


def extract_function_name(binary_file):
    """Extrahuje jméno funkce z názvu binárního souboru."""
    #match = re.search(r"binary_\w+_(\w+)\.out", os.path.basename(binary_file))
    match = re.search(r"binary_[^_]+_([\w\-\d_]+)\.out", os.path.basename(binary_file))
    return match.group(1) if match else "unknown"

def trace_analysis(binary_file=None, param_file=None, architecture=DEFAULT_ARCHITECTURE):
    """Umožní uživateli vybrat binární soubor a spustit trace pro více sad parametrů."""

    if not binary_file:
        log_info("\n Vyber binární soubor:")
        binary_file = fzf_select_file(".out", BUILD_DIR)

    if not binary_file or not os.path.exists(binary_file):
        log_error("Nebyl vybrán binární soubor!")
        return

    func_name = extract_function_name(binary_file)
    param_sets = []

    # Načtení parametrů ze souboru, pokud je zadán
    if param_file:
        if not os.path.exists(param_file):
            log_error(f"Soubor s parametry {param_file} neexistuje!")
            return

        with open(param_file, "r") as f:
            for line in f:
                # Zpracování parametrů s mezerami
                params = shlex.split(line.strip())  # Používá shlex pro správné zpracování mezer
                param_sets.append(params)
        
        log_info(f"Načteno {len(param_sets)} sad parametrů ze souboru `{param_file}`.")

    # Ruční zadání parametrů, pokud nebyl dodán soubor
    if not param_sets:
        log_info("\n Zadej sady parametrů pro spuštění (každou sadu potvrď Enterem).")
        log_info("Dvakrát Enter (prázdný řádek) ukončí zadávání.")
        log_info("Pokud funkce nemá žádné parametry, jen stiskni Enter.")

        while True:
            param_input = input("[INPUT] Parametry: ").strip()
            if param_input == "" and len(param_sets) > 0:
                break  # Konec zadávání po druhém Enteru

            # Použití shlex.split pro správné zpracování parametrů s mezerami
            param_sets.append(shlex.split(param_input))    

    if not param_sets:
        param_sets.append([])  # Prázdná sada, pokud uživatel nic nezadá

    trace_file = ""
    output_json = ""
    # Spuštění trace a analýzy pro každou sadu parametrů
    for params in param_sets:
        if params:
            # Nahraď mezery v jednotlivých parametrech a odstraň nebezpečné znaky
            safe_params = [re.sub(r'\W+', '_', p) for p in params]
            param_str = "_".join(safe_params)

            quoted_params = [f"'{p}'" if ' ' in p else p for p in params]
            quoted_params_str = " ".join(quoted_params)
        else:
            quoted_params = []
            param_str = "no_params"
            quoted_params_str = ""

        if architecture == "arm":
            trace_file = os.path.join(TRACE_DIR, f"traceArm_{func_name}_{param_str}.log")
            log_info(f"\n Spouštím trace pro {binary_file} s parametry {quoted_params}")
            run_gdb_trace_arm_linux(binary_file, trace_file, quoted_params)
            json_filename = f"instructionsArm_{func_name}_{param_str}.json"
        else:    
            trace_file = os.path.join(TRACE_DIR, f"trace_{func_name}_{param_str}.log")
            log_info(f"\n Spouštím trace pro {binary_file} s parametry {quoted_params}")
            run_gdb_trace(binary_file, trace_file, quoted_params)
            json_filename = f"instructions_{func_name}_{param_str}.json"

        log_info(f"Trace dokončen! Výstup: {trace_file}")

        # Spuštění analýzy trace souboru
        output_json_dir = os.path.join(ANALYSIS_DIR, func_name)
        os.makedirs(output_json_dir, exist_ok=True)
                
        output_json = os.path.join(output_json_dir, json_filename)

        log_info(f"\n Probíhá analýza pro trace soubor: {trace_file}")
        analyze_trace(trace_file, binary_file, func_name, output_json, quoted_params_str)
        log_info(f"Analýza dokončena! Výstupní soubor: {output_json}")
    return output_json
