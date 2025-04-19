"""
klee_runner.py - Spouští KLEE pro analýzu testovacích vstupů a extrahuje data pro GDB.

Tento modul:
- Spouští KLEE na LLVM bitcode souboru.
- Extrahuje vstupy z KLEE výstupů pomocí `ktest-tool`.
- Převádí KLEE výstupy do podoby vhodné pro testování v GDB.

Použití:
    from core.klee_runner import get_klee_test_inputs
"""

import os
import subprocess
import struct
import re
import shutil
from config import KLEE_EXECUTABLE, KLEE_OPTIONS, KTEST_TOOL
from config import log_info, log_debug, log_warning, log_error


def run_klee(build_dir, bitcode_file):
    """
    Spustí KLEE na LLVM bitcode souboru a uloží výstupy do složky 'klee-last'.

    Parametry:
    build_dir (str): Cesta k adresáři pro kompilaci.
    bitcode_file (str): Cesta k LLVM bitcode souboru, který bude analyzován.

    Návratová hodnota:
    str: Cesta k výstupní složce 'klee-last', kde jsou uloženy výsledky analýzy.
    """
    
    # Ověříme, zda soubor bitcode existuje
    if not os.path.exists(bitcode_file):
        log_error(f"Bitcode soubor `{bitcode_file}` nebyl nalezen. Nejprve ho vygenerujte!")
        return None

    # Ověříme, zda je KLEE k dispozici v PATH
    if not shutil.which(KLEE_EXECUTABLE):
        log_error("KLEE není nainstalován nebo není v PATH.")
        return None

    # Příkaz pro spuštění KLEE
    klee_cmd = [KLEE_EXECUTABLE] + KLEE_OPTIONS + [bitcode_file]

    log_info(f"Spouštím KLEE: {' '.join(klee_cmd)}")
    try:
        subprocess.run(klee_cmd, check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"KLEE selhal: {e}")
        return None

    # Vrátí cestu k výstupní složce 'klee-last'
    return os.path.join(build_dir, "klee-last")


def extract_klee_inputs(klee_out_dir):
    """
    Použije `ktest-tool` na výstupy KLEE a uloží je do souboru.

    Parametry:
    klee_out_dir (str): Cesta k výstupní složce KLEE, kde jsou uloženy soubory s testovými vstupy.

    Návratová hodnota:
    str: Cesta k souboru, kde jsou uložena zpracovaná KLEE data.
    """
    
    # Ověříme, zda existuje složka s výstupy KLEE
    if not os.path.exists(klee_out_dir):
        log_error("Výstupní složka KLEE neexistuje.")
        return None

    # Seznam souborů .ktest
    test_files = sorted([f for f in os.listdir(klee_out_dir) if f.endswith(".ktest")])

    if not test_files:
        log_error("KLEE nenalezl žádné testovací vstupy.")
        return None
    
    # Cesta pro uložení raw výstupů
    parsed_inputs_path = os.path.join(klee_out_dir, "raw_ktest_outputs.txt")

    # Zpracování každého souboru s testovými vstupy
    with open(parsed_inputs_path, "w") as f:
        for test_file in test_files:
            test_path = os.path.join(klee_out_dir, test_file)
            result = subprocess.run([KTEST_TOOL, test_path], capture_output=True, text=True)
            f.write(f"=== {test_file} ===\n")
            f.write(result.stdout + "\n")

    log_debug(f"Raw KLEE data uložena do `{parsed_inputs_path}`")
    return parsed_inputs_path


def extract_gdb_inputs(raw_ktest_path, param_types, output_file):
    """
    Zpracuje výstup z `raw_ktest_outputs.txt` a extrahuje parametry pro GDB.

    Parametry:
    raw_ktest_path (str): Cesta k souboru s raw výstupy KLEE.
    param_types (list): Seznam typů parametrů pro testovací případy.
    output_file (str): Cesta k souboru, do kterého budou uloženy extrahované parametry pro GDB.

    Návratová hodnota:
    tuple: Cesta k výstupnímu souboru a seznam zpracovaných testovacích případů.
    """
    
    # Ověření, zda soubor s raw daty existuje
    if not os.path.exists(raw_ktest_path):
        log_error(f"Soubor raw KLEE dat `{raw_ktest_path}` neexistuje.")
        return None, []

    # Příprava seznamu testovacích případů
    test_cases = []
    current_case = {}

    log_debug(f"Klee má na vstupu datové typy: {param_types}")
    
    with open(raw_ktest_path, "r") as f:
        for line in f:
            param_match = re.match(r"object \d+: name: 'param_(\d+)'", line)
            if param_match:
                param_index = int(param_match.group(1))
                current_case[param_index] = None
                continue

            # Zpracování hodnoty typu int
            int_match = re.match(r"object \d+: int : (-?\d+)", line)
            if int_match and param_index in current_case:
                current_case[param_index] = int(int_match.group(1))
                continue

            # Zpracování hodnoty v hexadecimálním formátu
            hex_match = re.match(r"object \d+: hex : (0x[0-9a-fA-F]+)", line)
            if hex_match and param_index in current_case:
                hex_str = hex_match.group(1)[2:]  # odstraň '0x'


                # Zajistíme délku pro násobky 8 (kvůli double), 4 (kvůli float/int)
                if len(hex_str) % 2 != 0:
                    hex_str = "0" + hex_str  # zarovnání do sudého počtu znaků
                bytes_data = bytes.fromhex(hex_str)

                param_type = param_types[param_index]

                try:
                    if param_type == "int*":
                        ints = list(struct.unpack(f"<{len(bytes_data)//4}i", bytes_data))
                        current_case[param_index] = ints

                    elif param_type == "float*":
                        floats = list(struct.unpack(f"<{len(bytes_data)//4}f", bytes_data))
                        current_case[param_index] = floats

                    elif param_type == "double*":
                        doubles = list(struct.unpack(f"<{len(bytes_data)//8}d", bytes_data))
                        current_case[param_index] = doubles

                    elif param_type == "float":
                        current_case[param_index] = struct.unpack("<f", bytes_data[:4])[0]

                    elif param_type == "double":
                        current_case[param_index] = struct.unpack("<d", bytes_data[:8])[0]

                    else:
                        # fallback – uložíme jako integer
                        current_case[param_index] = int(hex_match.group(1), 16)

                except struct.error:
                    current_case[param_index] = []
                continue

            """
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
            """

            # Zpracování hodnoty typu char
            text_match = re.match(r"object \d+: text: (.)", line)
            if text_match and param_types[param_index] == "char":
                current_case[param_index] = text_match.group(1)
                continue

            # Pokud jsme našli nový testovací případ, přidáme předchozí
            if line.startswith("==="):
                if current_case:
                    sorted_case = " ".join(str(current_case[i]) for i in sorted(current_case) if current_case[i] is not None)
                    test_cases.append(sorted_case)
                current_case = {}

    # Pokud ještě existuje nějaký neuzavřený testovací případ, přidáme ho
    if current_case:
        sorted_case = " ".join(str(current_case[i]) for i in sorted(current_case) if current_case[i] is not None)
        test_cases.append(sorted_case)

    # Uložení výsledků do výstupního souboru
    with open(output_file, "w") as f:
        for case in test_cases:
            f.write(case + "\n")

    log_info(f"Parametry nalezené s KLEE uloženy do: `{output_file}`")
    return output_file, test_cases


def get_klee_test_inputs(build_dir, bitcode_file, param_types, output_file, target_arch="native"):
    """
    Spustí celý proces analýzy a vrátí cestu k testovacím vstupům i samotná data.

    Parametry:
    build_dir (str): Cesta k adresáři pro kompilaci.
    bitcode_file (str): Cesta k LLVM bitcode souboru.
    param_types (list): Seznam datových typů parametrů.
    output_file (str): Cesta k výstupnímu souboru pro testovací vstupy.
    target_arch (str): Architektura cílového systému ("native" nebo "arm").

    Návratová hodnota:
    tuple: Cesta k výstupnímu souboru a seznam testovacích případů.
    """
    
    if target_arch == "arm":
        klee_out_dir = run_klee_with_qemu(build_dir, bitcode_file)
    else:
        klee_out_dir = run_klee(build_dir, bitcode_file)
    
    if not klee_out_dir:
        return None, []

    raw_file = extract_klee_inputs(klee_out_dir)
    if not raw_file:
        return None, []
    
    return extract_gdb_inputs(raw_file, param_types, output_file)


def run_klee_with_qemu(build_dir, bitcode_file, qemu_executable="qemu-arm"):
    """
    Spustí KLEE na LLVM bitcode souboru v emulovaném ARM prostředí pomocí QEMU.

    Parametry:
    build_dir (str): Cesta k adresáři pro kompilaci.
    bitcode_file (str): Cesta k LLVM bitcode souboru.
    qemu_executable (str): Cesta k QEMU executable pro ARM (výchozí je "qemu-arm").

    Návratová hodnota:
    str: Cesta k výstupní složce 'klee-last'.
    """
    
    # Ověření dostupnosti QEMU pro ARM
    if not shutil.which(qemu_executable):
        raise FileNotFoundError(f"[ERROR] `{qemu_executable}` nebyl nalezen. Zkontrolujte instalaci.")

    # Ověření dostupnosti KLEE
    if not shutil.which(KLEE_EXECUTABLE):
        raise FileNotFoundError(f"[ERROR] `{KLEE_EXECUTABLE}` není nainstalováno nebo není v PATH.")

    # Vytvoření příkazu pro spuštění KLEE pomocí QEMU
    klee_cmd = [
        qemu_executable,
        KLEE_EXECUTABLE,
        *KLEE_OPTIONS,
        bitcode_file
    ]

    log_info(f"Spouštím KLEE na emulovaném ARM prostředí: {' '.join(map(str, klee_cmd))}") 

    try:
        # Spustíme KLEE s QEMU
        subprocess.run(klee_cmd, check=True)
    except subprocess.CalledProcessError as e:
        log_error(f"KLEE selhal: {e}")
        return None

    log_info("KLEE dokončeno. Výsledky by měly být uloženy ve 'klee-last'.")
    return os.path.join(build_dir, "klee-last")
