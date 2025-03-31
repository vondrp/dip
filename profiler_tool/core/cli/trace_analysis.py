# trace_analysis.py
import os
from .file_selection import fzf_select_file
from core.engine.tracer import run_gdb_trace
from core.engine.trace_analysis import analyze_trace

def trace_analysis(binary_file=None, param_file=None):
    """Umožní uživateli vybrat binárku a spustit trace pro více sad parametrů."""
    if not binary_file:
        binary_file = fzf_select_file(".out")

    if not binary_file or not os.path.exists(binary_file):
        print("❌ Nebyla vybrána žádná binárka.")
        return

    param_sets = []

    # Načítání parametrů
    if param_file:
        with open(param_file, "r") as f:
            param_sets = [line.strip().split() for line in f]

    # Ruční zadání parametrů
    if not param_sets:
        while True:
            param_input = input("📝 Parametry: ").strip()
            if param_input == "":
                break
            param_sets.append(param_input.split())

    # Spuštění trace a analýza
    for params in param_sets:
        trace_file = f"trace_{params}.log"
        run_gdb_trace(binary_file, trace_file, params)
        analyze_trace(trace_file)
