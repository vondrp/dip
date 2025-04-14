import os
import re

from core.cli.file_selection import fzf_select_file
from core.engine.generator import get_generated_main_path, get_generated_main_klee_path
from core.engine.generator import generate_main, generate_main_klee
from core.engine.compiler import compile_x86, compile_klee, compile_arm_linux
from core.engine.klee_runner import get_klee_test_inputs
from core.engine.trace_analysis import analyze_trace
from config import BUILD_DIR, KLEE_OUTPUT, DEFAULT_ARCHITECTURE, KLEE_RESULTS
from config import log_info, log_debug, log_warning, log_error


def delete_file(file_path):
    """Odstraní zadaný soubor, pokud existuje."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            log_debug(f"Smazán soubor: {file_path}")
        except Exception as e:
            log_error(f"[Nepodařilo se smazat {file_path}: {e}")
    else:
        log_debug(f"Soubor {file_path} neexistuje, není co mazat.")

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
        log_info("\n Vyber hlavičkový soubor (.h):")
        header_file = fzf_select_file(".h")
    
    log_debug(f"HEADER_FILE {header_file}")
    while not header_file or not os.path.exists(header_file):
        log_error("Chyba: Nevybral jsi platný .h soubor.")
        log_info("\n Vyber znovu hlavičkový soubor (.h):")
        header_file = fzf_select_file(".h")
    
    return header_file

def extract_function_from_header(header_file):
    """Extrahuje funkce z hlavičkového souboru."""
    functions = extract_functions_from_header(header_file)
    if not functions:
        log_error(f"V souboru {header_file} nebyly nalezeny žádné funkce.")
        exit(1)
    return functions

def select_target_function(functions, function_name=None):
    """Umožní uživateli vybrat cílovou funkci ze seznamu funkcí."""
    if function_name:
        if function_name in functions:
            target_function = function_name
        else:
            log_error(f"Funkce `{function_name}` nebyla nalezena v hlavičkovém souboru.")
            log_info("\n Nalezené funkce v hlavičkovém souboru:")
            for func, params in functions.items():
                param_str = ", ".join(params) if params else "void"
                print(f" - {func}({param_str})")

            target_function = input("\n[INFO] Zadej jméno funkce k použití: ")
            while target_function not in functions:
                log_warning("Neplatná funkce. Zkus to znovu.")
                target_function = input("\n[INFO] Zadej jméno funkce k použití: ")
    else:
        log_info("\n Nalezené funkce v hlavičkovém souboru:")
        for func, params in functions.items():
            param_str = ", ".join(params) if params else "void"
            print(f" - {func}({param_str})")

        target_function = input("\n[INFO] Zadej jméno funkce k použití: ")
        while target_function not in functions:
            print("[ERROR] Neplatná funkce. Zkus to znovu.")
            target_function = input("\n[INFO] Zadej jméno funkce k použití: ")

    log_info(f"Vybraná funkce: {target_function}")
    return target_function

def select_source_file(directory, src_file=None):
    """Vybere odpovídající .c soubor."""
    if not src_file:
        log_info("\n Vyber odpovídající .c soubor:")
        src_file = fzf_select_file(".c")
    
    while not src_file or not os.path.exists(src_file):
        log_error("Chyba: Nevybral jsi platný .c soubor.")
        log_info("\n Vyber znovu odpovídající .c soubor:")
        src_file = fzf_select_file(".c")
    
    return src_file

def check_function_in_file(src_file, target_function):
    """Zkontroluje, zda .c soubor obsahuje požadovanou funkci."""
    with open(src_file, "r") as f:
        file_content = f.read()
        if target_function not in file_content:
            log_error(f"Soubor {src_file} neobsahuje funkci {target_function}.")
            choice = input("[INFO] Chceš vybrat jiný soubor? (y/n): ").strip().lower()
            if choice == 'y':
                return False 
            else:
                log_info(f"Nezmění se soubor {src_file} ukončuje se běh.")
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
    log_info(f"\nGenerování `generated_main.c` dokončeno pro funkci `{target_function}` ze souboru `{header_file}`.")

    # Kompilace
    log_info("\n Kompilace `generated_main.c`...")
    src_dir = os.path.dirname(src_file)
    if architecture == "arm":
        binary_file = os.path.join(BUILD_DIR, f"binary_ARM_{target_function}.out")
        compile_arm_linux(binary_file=binary_file, src_file=src_file, src_dir=src_dir)
    else:
        log_debug(f"src file = {src_file}   src dir = {src_dir}")
        binary_file = os.path.join(BUILD_DIR, f"binary_x86_{target_function}.out")
        compile_x86(binary_file=binary_file, src_file=src_file, src_dir=src_dir)

    log_info(f"Kompilace dokončena pro `{target_function}`.")
    #delete_file(get_generated_main_path())
    if use_klee:
        prepare_klee(header_file, src_file, target_function)

    log_info(f"Vytvořen binární soubor: {binary_file}")
    return binary_file
    

def prepare_klee(header_file=None, src_file=None, function_name=None, architecture="native"):
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
    log_info(f"\n Generování `generated_main_klee.c` dokončeno pro funkci `{target_function}` ze souboru `{header_file}`.")

    # Kompilace pro KLEE (bitcode)
    log_info("Kompilace pro KLEE...")
    klee_dir = os.path.join(KLEE_OUTPUT, target_function)
    os.makedirs(klee_dir, exist_ok=True)
    compile_klee(klee_dir, src_file, os.path.dirname(src_file), target_arch=architecture)
    log_info(f"Kompilace pro KLEE dokončena.")

    # Vygenerování testovacích vstupů pro KLEE
    params = functions.get(target_function, [])
    param_types = [param.split()[0] for param in params]
    bitcode_file = os.path.join(klee_dir, "klee_program.bc")

    output_file = os.path.join(KLEE_RESULTS, f"gdb_inputs_{target_function}.txt")
    file_path, test_data = get_klee_test_inputs(klee_dir, bitcode_file, param_types, output_file, target_arch=architecture)

    delete_file(get_generated_main_klee_path())
    log_info(f"Testovací vstupy uloženy: {file_path}")
    log_info(f"Testovací data: {test_data}")