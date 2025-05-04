import os
import re
import shlex
from core.cli.file_selection import fzf_select_file
from core.engine.tracer import run_gdb_trace, run_gdb_trace_qemu
from core.engine.trace_analysis import analyze_trace
from config import BUILD_DIR, TRACE_DIR, ANALYSIS_DIR, ACTIVE_ARCHITECTURE
from config import log_info, log_debug, log_warning, log_error


def extract_function_name(binary_file):
    """
    Extrahuje jméno funkce z názvu binárního souboru na základě předem definovaného formátu.
    
    Například: 'binary_riscv_add.out' → 'add'
    """
    match = re.search(r"binary_[^_]+_([\w\-\d_]+)\.out", os.path.basename(binary_file))
    return match.group(1) if match else "unknown"

def load_param_sets_from_file(param_file):
    """
    Načte sady parametrů ze zadaného souboru.
    
    Každý řádek je interpretován jako jedna sada argumentů.
    """
    if not os.path.exists(param_file):
        log_error(f"Soubor s parametry {param_file} neexistuje!")
        return []

    param_sets = []
    with open(param_file, "r") as f:
        for line in f:
            params = shlex.split(line.strip())
            if params:
                param_sets.append(params)

    log_info(f"Načteno {len(param_sets)} sad parametrů ze souboru `{param_file}`.")
    return param_sets


def prompt_param_sets_from_user():
    """
    Umožní uživateli interaktivně zadat sady parametrů.
    
    Zadávání končí dvojím Enterem.
    """
    log_info("\nZadej sady parametrů pro spuštění (každou sadu potvrď Enterem).")
    log_info("Dvakrát Enter (prázdný řádek) ukončí zadávání.")
    log_info("Pokud funkce nemá žádné parametry, jen stiskni Enter.")

    param_sets = []
    while True:
        param_input = input("[INPUT] Parametry: ").strip()
        if param_input == "" and len(param_sets) > 0:
            break
        param_sets.append(shlex.split(param_input))
    return param_sets or [[]]


def generate_trace_and_analyze(binary_file, func_name, params, architecture):
    """
    Spustí trace a analýzu pro jednu sadu parametrů a vrátí cestu k výstupnímu JSON souboru.
    """
    safe_params = [re.sub(r'\W+', '_', p) for p in params]
    param_str = "_".join(safe_params) if params else "no_params"
    quoted_params = [f"'{p}'" if ' ' in p else p for p in params]
    quoted_params_str = " ".join(quoted_params)

    # Volba názvu a cesty pro trace
    if architecture == "arm":
        trace_file = os.path.join(TRACE_DIR, f"traceArm_{func_name}_{param_str}.log")
        json_filename = f"instructionsArm_{func_name}_{param_str}.json"
        run_gdb_trace_qemu(binary_file, trace_file, quoted_params, architecture)
    elif architecture == "riscv":
        trace_file = os.path.join(TRACE_DIR, f"traceRiscv_{func_name}_{param_str}.log")
        json_filename = f"instructionsRiscv_{func_name}_{param_str}.json"
        run_gdb_trace_qemu(binary_file, trace_file, quoted_params, architecture)
    else:
        trace_file = os.path.join(TRACE_DIR, f"trace_{func_name}_{param_str}.log")
        json_filename = f"instructions_{func_name}_{param_str}.json"
        run_gdb_trace(binary_file, trace_file, quoted_params)

    log_info(f"\nSpouštím trace pro {binary_file} s parametry {quoted_params}")
    log_info(f"Trace dokončen! Výstup: {trace_file}")

    # Analýza trace
    output_json_dir = os.path.join(ANALYSIS_DIR, func_name)
    os.makedirs(output_json_dir, exist_ok=True)
    output_json = os.path.join(output_json_dir, json_filename)

    log_info(f"\nProbíhá analýza pro trace soubor: {trace_file}")
    analyze_trace(trace_file, binary_file, func_name, output_json, quoted_params_str)
    log_info(f"Analýza dokončena! Výstupní soubor: {output_json}")

    return output_json


def trace_analysis(binary_file=None, param_file=None, architecture=ACTIVE_ARCHITECTURE):
    """
    Hlavní funkce, která umožňuje provést trace a analýzu binárního souboru pro různé sady parametrů.

    Pokud není zadán binární soubor ani parametry, je možné je interaktivně zadat.
    """
    if not binary_file:
        log_info("\nVyber binární soubor:")
        binary_file = fzf_select_file(".out", BUILD_DIR)

    if not binary_file or not os.path.exists(binary_file):
        log_error("Nebyl vybrán binární soubor!")
        return

    func_name = extract_function_name(binary_file)

    # Načti parametry buď ze souboru nebo od uživatele
    param_sets = load_param_sets_from_file(param_file) if param_file else prompt_param_sets_from_user()
    if not param_sets:
        param_sets = [[]]  # Prázdná sada jako výchozí

    last_output = ""
    for params in param_sets:
        last_output = generate_trace_and_analyze(binary_file, func_name, params, architecture)

    return last_output
