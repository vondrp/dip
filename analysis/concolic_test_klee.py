import os
import subprocess
import struct
import re

# Konfigurace cest
BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "build", "klee")
BITCODE_FILE = os.path.join(BUILD_DIR, "klee_program.bc")
KTEST_TOOL = "ktest-tool"

def run_klee(build_dir, bitcode_file):
    """Spustí KLEE na LLVM bitcode souboru, výstupy se ukládají do 'klee-last'."""
    if not os.path.exists(bitcode_file):
        print(f"[ERROR] Bitcode soubor `{bitcode_file}` nebyl nalezen. Nejprve ho vygenerujte!")
        return None

    # Spuštění KLEE s výchozí složkou 'klee-last'
    klee_cmd = [
        "klee",
        "--optimize",
        "--libc=uclibc",  # Použití vestavěné knihovny KLEE
        "--posix-runtime",
        "--only-output-states-covering-new",
        bitcode_file
    ]

    print(f"[INFO] Spouštím KLEE: {' '.join(klee_cmd)}")
    subprocess.run(klee_cmd, check=True)

    # Vrátíme absolutní cestu ke `klee-last`
    klee_last_dir = os.path.join(build_dir, "klee-last")
    return klee_last_dir


def extract_klee_inputs(klee_out_dir):
    """Použije `ktest-tool` na výstupy KLEE a uloží je do souboru."""

    if not os.path.exists(klee_out_dir):
        print("[ERROR] Výstupní složka KLEE neexistuje. Ujistěte se, že KLEE byl spuštěn.")
        return

    print(f"[INFO] Prohledávám složku: {klee_out_dir}")
    
    test_files = sorted([f for f in os.listdir(klee_out_dir) if f.endswith(".ktest")])
    
    if not test_files:
        print("[WARNING] KLEE nenalezl žádné testovací vstupy.")
        return
    
    parsed_inputs_path = os.path.join(klee_out_dir, "raw_ktest_outputs.txt")

    with open(parsed_inputs_path, "w") as f:
        for test_file in test_files:
            test_path = os.path.join(klee_out_dir, test_file)
            print(f"  - Zpracovávám: {test_path}")

            # Spuštění `ktest-tool`
            result = subprocess.run(["ktest-tool", test_path], capture_output=True, text=True)
            
            f.write(f"=== {test_file} ===\n")
            f.write(result.stdout + "\n")

    print(f"[INFO] Uloženo do `{parsed_inputs_path}`")
    return parsed_inputs_path


def extract_gdb_inputs(klee_out_dir, raw_ktest_path, param_types):
    """Zpracuje výstup z `raw_ktest_outputs.txt` a extrahuje parametry pro GDB podle jejich typů."""
    
    gdb_inputs_path = os.path.join(klee_out_dir, "gdb_test_inputs.txt")

    if not os.path.exists(raw_ktest_path):
        print(f"[ERROR] Soubor `{raw_ktest_path}` neexistuje. Nejprve spusť `extract_klee_inputs`.")
        return

    print(f"[INFO] Zpracovávám `{raw_ktest_path}` pro GDB vstupy...")

    test_cases = []
    current_case = {}

    with open(raw_ktest_path, "r") as f:
        for line in f:
            param_match = re.match(r"object \d+: name: 'param_(\d+)'", line)
            if param_match:
                param_index = int(param_match.group(1))
                current_case[param_index] = None  # Přednastavíme hodnotu
                continue

            # Získání integer hodnoty
            int_match = re.match(r"object \d+: int : (-?\d+)", line)
            if int_match and param_index in current_case:
                current_case[param_index] = int(int_match.group(1))
                continue

            # Získání hex hodnoty (použijeme pro `double`)
            hex_match = re.match(r"object \d+: hex : (0x[0-9a-fA-F]+)", line)
            if hex_match and param_index in current_case:
                hex_val = int(hex_match.group(1), 16)

                if param_types[param_index] == "double":
                    try:
                        double_val = struct.unpack("d", struct.pack("Q", hex_val))[0]
                        current_case[param_index] = double_val
                    except struct.error:
                        current_case[param_index] = hex_val  # Pokud selže, ponecháme hexadecimální hodnotu
                else:
                    current_case[param_index] = hex_val
                continue

            # Získání textové hodnoty (`char`)
            text_match = re.match(r"object \d+: text: (.)", line)
            if text_match and param_types[param_index] == "char":
                current_case[param_index] = text_match.group(1)
                continue

            # Nový testovací případ
            if line.startswith("==="):  
                if current_case:
                    sorted_case = " ".join(str(current_case[i]) for i in sorted(current_case) if current_case[i] is not None)
                    test_cases.append(sorted_case)
                current_case = {}

    # Přidání posledního testovacího případu
    if current_case:
        sorted_case = " ".join(str(current_case[i]) for i in sorted(current_case) if current_case[i] is not None)
        test_cases.append(sorted_case)

    # Uložení do souboru
    with open(gdb_inputs_path, "w") as f:
        for case in test_cases:
            f.write(case + "\n")

    print(f"[INFO] Uloženo do `{gdb_inputs_path}`")
    return gdb_inputs_path, test_cases


def get_klee_test_inputs(build_dir, bitcode_file, param_types):
    """Spustí celý proces a vrátí cestu k testovacím vstupům i samotná data."""
    klee_out_dir = run_klee(build_dir, bitcode_file)
    if not klee_out_dir:
        return None, []

    raw_file = extract_klee_inputs(klee_out_dir)
    if not raw_file:
        return None, []

    gdb_inputs_path, test_cases = extract_gdb_inputs(klee_out_dir, raw_file, param_types)
    return gdb_inputs_path, test_cases

if __name__ == "__main__":
    param_types = ["int", "double", "char"]
    klee_out_dir = run_klee(BUILD_DIR, BITCODE_FILE)
    if klee_out_dir:
        raw_file = extract_klee_inputs(klee_out_dir)
        extract_gdb_inputs(klee_out_dir, raw_file, param_types)
