import os
import re

from core.cli.file_selection import fzf_select_file
from core.engine.generator import generate_main, generate_main_klee
from core.engine.compiler import compile_x86, compile_klee, compile_arm_linux
from core.engine.klee_runner import get_klee_test_inputs
from core.engine.trace_analysis import analyze_trace
from core.config import BUILD_DIR, KLEE_OUTPUT, DEFAULT_ARCHITECTURE, KLEE_RESULTS
from core.config import get_generated_main_path, get_generated_main_klee_path

def delete_file(file_path):
    """Odstraní zadaný soubor, pokud existuje."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[INFO] Smazán soubor: {file_path}")
        except Exception as e:
            print(f"[ERROR] Nepodařilo se smazat {file_path}: {e}")
    else:
        print(f"[DEBUG] Soubor {file_path} neexistuje, není co mazat.")

def extract_functions_from_header(header_file):
    """Najde deklarace funkcí v hlavičkovém souboru."""
    functions = {}
    with open(header_file, "r") as f:
        for line in f:
            match = re.match(r"^\s*(\w[\w\s\*]+)\s+(\w+)\s*\((.*?)\)\s*;", line)
            if match:
                return_type, func_name, params = match.groups()
                param_list = [p.strip() for p in params.split(",") if p]
                functions[func_name] = param_list
    return functions

def select_header_file(header_file=None):
    """Vybere hlavičkový soubor (.h) pomocí fzf."""
    if not header_file:
        print("\n[INFO] Vyber hlavičkový soubor (.h):")
        header_file = fzf_select_file(".h")
    
    print(f"[DEBUG] HEADER_FILE {header_file}")
    while not header_file or not os.path.exists(header_file):
        print("[ERROR] Chyba: Nevybral jsi platný .h soubor.")
        print("\n[INFO] Vyber znovu hlavičkový soubor (.h):")
        header_file = fzf_select_file(".h")
    
    return header_file

def extract_function_from_header(header_file):
    """Extrahuje funkce z hlavičkového souboru."""
    functions = extract_functions_from_header(header_file)
    if not functions:
        print(f"[ERROR] V souboru {header_file} nebyly nalezeny žádné funkce.")
        exit(1)
    return functions

def select_target_function(functions, function_name=None):
    """Umožní uživateli vybrat cílovou funkci ze seznamu funkcí."""
    if function_name:
        if function_name in functions:
            target_function = function_name
        else:
            print(f"[ERROR] Funkce `{function_name}` nebyla nalezena v hlavičkovém souboru.")
            print("\n[INFO] Nalezené funkce v hlavičkovém souboru:")
            for func, params in functions.items():
                param_str = ", ".join(params) if params else "void"
                print(f" - {func}({param_str})")

            target_function = input("\n[INFO] Zadej jméno funkce k použití: ")
            while target_function not in functions:
                print("[ERROR] Neplatná funkce. Zkus to znovu.")
                target_function = input("\n[INFO] Zadej jméno funkce k použití: ")
    else:
        print("\n[INFO] Nalezené funkce v hlavičkovém souboru:")
        for func, params in functions.items():
            param_str = ", ".join(params) if params else "void"
            print(f" - {func}({param_str})")

        target_function = input("\n[INFO] Zadej jméno funkce k použití: ")
        while target_function not in functions:
            print("[ERROR] Neplatná funkce. Zkus to znovu.")
            target_function = input("\n[INFO] Zadej jméno funkce k použití: ")

    print(f"[INFO] Vybraná funkce: {target_function}")
    return target_function

def select_source_file(directory, src_file=None):
    """Vybere odpovídající .c soubor."""
    if not src_file:
        print("\n[INFO] Vyber odpovídající .c soubor:")
        src_file = fzf_select_file(".c", directory)
    
    while not src_file or not os.path.exists(src_file):
        print("[ERROR] Chyba: Nevybral jsi platný .c soubor.")
        print("\n[INFO] Vyber znovu odpovídající .c soubor:")
        src_file = fzf_select_file(".c", directory)
    
    return src_file

def check_function_in_file(src_file, target_function):
    """Zkontroluje, zda .c soubor obsahuje požadovanou funkci."""
    with open(src_file, "r") as f:
        file_content = f.read()
        if target_function not in file_content:
            print(f"[ERROR] Soubor {src_file} neobsahuje funkci {target_function}.")
            choice = input("[INFO] Chceš vybrat jiný soubor? (y/n): ").strip().lower()
            if choice == 'y':
                return False 
            else:
                print(f"[INFO] Nezmění se soubor {src_file} ukončuje se běh.")
                exit(1)
    return True

def prepare_function(header_file=None, src_file=None, function_name=None, use_klee=False, architecture=DEFAULT_ARCHITECTURE):
    """Funkce pro výběr hlavičkového souboru, funkce a odpovídajícího .c souboru."""
    header_file = select_header_file(header_file)
    functions = extract_function_from_header(header_file)
    target_function = select_target_function(functions, function_name)
    
    # Extrahujeme adresář z hlavičkového souboru
    directory = os.path.dirname(header_file)
    
    # Vybereme odpovídající .c soubor
    src_file = select_source_file(directory, src_file)
    
    # Zkontrolujeme, zda .c soubor obsahuje funkci
    while not check_function_in_file(src_file, target_function):
        src_file = select_source_file(directory, src_file)

    # Generování `generated_main.c`
    generate_main(target_function, functions[target_function], header_file)
    print(f"\n[INFO] Generování `generated_main.c` dokončeno pro funkci `{target_function}` ze souboru `{header_file}`.")

    # Kompilace
    print("\n[INFO] Kompilace `generated_main.c`...")
    src_dir = os.path.dirname(src_file)
    if architecture == "arm":
        binary_file = os.path.join(BUILD_DIR, f"binary_ARM_{target_function}.out")
        compile_arm_linux(binary_file=binary_file, src_file=src_file, src_dir=src_dir)
    else:
        binary_file = os.path.join(BUILD_DIR, f"binary_x86_{target_function}.out")
        compile_x86(binary_file=binary_file, src_file=src_file, src_dir=src_dir)

    print(f"[INFO] Kompilace dokončena pro `{target_function}`.")
    #delete_file(get_generated_main_path())
    if use_klee:
        prepare_klee(header_file, src_file, target_function)

    print(f"[INFO] Vytovřený binární soubor: {binary_file}")
    return binary_file
    

def prepare_klee(header_file=None, src_file=None, function_name=None):
    """Funkce pro výběr hlavičkového souboru, funkce a odpovídajícího .c souboru pro KLEE."""
    header_file = select_header_file(header_file)
    functions = extract_function_from_header(header_file)
    target_function = select_target_function(functions, function_name)
    
    # Extrahujeme adresář z hlavičkového souboru
    directory = os.path.dirname(header_file)
    
    # Vybereme odpovídající .c soubor
    src_file = select_source_file(directory, src_file)
    
    # Zkontrolujeme, zda .c soubor obsahuje funkci
    while not check_function_in_file(src_file, target_function):
        src_file = select_source_file(directory, src_file)

    # Generování `generated_main_klee.c` pro KLEE
    generate_main_klee(target_function, functions[target_function], header_file)
    print(f"\n[INFO] Generování `generated_main_klee.c` dokončeno pro funkci `{target_function}` ze souboru `{header_file}`.")

    # Kompilace pro KLEE (bitcode)
    print("\n[INFO] Kompilace pro KLEE...")
    klee_dir = os.path.join(KLEE_OUTPUT, target_function)
    os.makedirs(klee_dir, exist_ok=True)
    compile_klee(klee_dir, src_file, os.path.dirname(src_file))
    print(f"[INFO] Kompilace pro KLEE dokončena.")

    # Vygenerování testovacích vstupů pro KLEE
    params = functions.get(target_function, [])
    param_types = [param.split()[0] for param in params]
    bitcode_file = os.path.join(klee_dir, "klee_program.bc")

    output_file = os.path.join(KLEE_RESULTS, f"gdb_inputs_{target_function}.txt")
    file_path, test_data = get_klee_test_inputs(klee_dir, bitcode_file, param_types, output_file)

    delete_file(get_generated_main_klee_path())
    print(f"[INFO] Testovací vstupy uloženy: {file_path}")
    print(f"[INFO] Testovací data: {test_data}")