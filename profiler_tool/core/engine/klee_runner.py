"""
klee_runner.py - Spouští KLEE pro analýzu testovacích vstupů a extrahuje data pro GDB.

Tento modul:
- Spouští KLEE na LLVM bitcode souboru
- Extrahuje vstupy z KLEE výstupů pomocí `ktest-tool`
- Převádí KLEE výstupy do podoby vhodné pro testování v GDB

Použití:
    from core.klee_runner import get_klee_test_inputs
"""

import os
import subprocess
import struct
import re
import shutil
from core.config import KLEE_EXECUTABLE, KLEE_OPTIONS, KTEST_TOOL


def run_klee(build_dir, bitcode_file):
    """Spustí KLEE na LLVM bitcode souboru, výstupy se ukládají do 'klee-last'."""
    
    if not os.path.exists(bitcode_file):
        print(f"[ERROR] Bitcode soubor `{bitcode_file}` nebyl nalezen. Nejprve ho vygenerujte!")
        return None

    if not shutil.which(KLEE_EXECUTABLE):
        print("[ERROR] KLEE není nainstalován nebo není v PATH.")
        return None

    # Spuštění KLEE
    klee_cmd = [KLEE_EXECUTABLE] + KLEE_OPTIONS + [bitcode_file]

    print(f"[INFO] Spouštím KLEE: {' '.join(klee_cmd)}")
    try:
        subprocess.run(klee_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] KLEE selhal: {e}")
        return None

    return os.path.join(build_dir, "klee-last")


def extract_klee_inputs(klee_out_dir):
    """Použije `ktest-tool` na výstupy KLEE a uloží je do souboru."""
    
    if not os.path.exists(klee_out_dir):
        print("[ERROR] Výstupní složka KLEE neexistuje.")
        return None

    test_files = sorted([f for f in os.listdir(klee_out_dir) if f.endswith(".ktest")])

    if not test_files:
        print("[WARNING] KLEE nenalezl žádné testovací vstupy.")
        return None
    
    parsed_inputs_path = os.path.join(klee_out_dir, "raw_ktest_outputs.txt")

    with open(parsed_inputs_path, "w") as f:
        for test_file in test_files:
            test_path = os.path.join(klee_out_dir, test_file)
            result = subprocess.run([KTEST_TOOL, test_path], capture_output=True, text=True)
            f.write(f"=== {test_file} ===\n")
            f.write(result.stdout + "\n")

    print(f"[INFO] Uloženo do `{parsed_inputs_path}`")
    return parsed_inputs_path


def extract_gdb_inputs(klee_out_dir, raw_ktest_path, param_types):
    """Zpracuje výstup z `raw_ktest_outputs.txt` a extrahuje parametry pro GDB."""

    if not os.path.exists(raw_ktest_path):
        print(f"[ERROR] Soubor `{raw_ktest_path}` neexistuje.")
        return None, []

    gdb_inputs_path = os.path.join(klee_out_dir, "gdb_test_inputs.txt")
    test_cases = []
    current_case = {}

    print(f"PARAMETRY typy {param_types}")
    with open(raw_ktest_path, "r") as f:
        for line in f:
            param_match = re.match(r"object \d+: name: 'param_(\d+)'", line)
            if param_match:
                param_index = int(param_match.group(1))
                current_case[param_index] = None
                continue

            int_match = re.match(r"object \d+: int : (-?\d+)", line)
            if int_match and param_index in current_case:
                current_case[param_index] = int(int_match.group(1))
                continue

            hex_match = re.match(r"object \d+: hex : (0x[0-9a-fA-F]+)", line)
            if hex_match and param_index in current_case:
                hex_val = int(hex_match.group(1), 16)
                if param_types[param_index] == "double":
                    try:
                        double_val = struct.unpack("d", struct.pack("Q", hex_val))[0]
                        current_case[param_index] = double_val
                    except struct.error:
                        current_case[param_index] = hex_val
                else:
                    current_case[param_index] = hex_val
                continue

            text_match = re.match(r"object \d+: text: (.)", line)
            if text_match and param_types[param_index] == "char":
                current_case[param_index] = text_match.group(1)
                continue

            if line.startswith("==="):
                if current_case:
                    sorted_case = " ".join(str(current_case[i]) for i in sorted(current_case) if current_case[i] is not None)
                    test_cases.append(sorted_case)
                current_case = {}

    if current_case:
        sorted_case = " ".join(str(current_case[i]) for i in sorted(current_case) if current_case[i] is not None)
        test_cases.append(sorted_case)

    with open(gdb_inputs_path, "w") as f:
        for case in test_cases:
            f.write(case + "\n")

    print(f"[INFO] Uloženo do `{gdb_inputs_path}`")
    return gdb_inputs_path, test_cases


def get_klee_test_inputs(build_dir, bitcode_file, param_types):
    """Spustí celý proces a vrátí cestu k testovacím vstupům i samotná data."""
    klee_out_dir = run_klee(build_dir, bitcode_file)
    print("run_klee finished")
    if not klee_out_dir:
        return None, []

    print("before extract klee inputs")
    raw_file = extract_klee_inputs(klee_out_dir)
    if not raw_file:
        return None, []
    
    print("before return extract gdb inputs")
    return extract_gdb_inputs(klee_out_dir, raw_file, param_types)
