import os
import re
import shutil

from core.cli.file_selection import fzf_select_file
from core.engine.generator import get_generated_main_path, get_generated_main_klee_path, set_generated_main_path
from core.engine.generator import generate_main, generate_main_klee, generate_main_template
from core.engine.compiler import compile_klee, compile_binary
from core.engine.klee_runner import get_klee_test_inputs
from core.engine.trace_analysis import analyze_trace
from config import BUILD_DIR, KLEE_OUTPUT, ACTIVE_ARCHITECTURE, KLEE_RESULTS, REMOVE_GENERATED_MAIN
from config import log_info, log_debug, log_warning, log_error


def delete_file(file_path):
    """
    Odstraní zadaný soubor, pokud existuje.

    Parametry:
        file_path (str): Cesta k souboru ke smazání.

    Návratová hodnota:
        None
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            log_debug(f"Smazán soubor: {file_path}")
        except Exception as e:
            log_error(f"[Nepodařilo se smazat {file_path}: {e}")
    else:
        log_debug(f"Soubor {file_path} neexistuje, není co mazat.")

def extract_functions_from_header(header_file):
    """
    Najde deklarace funkcí v hlavičkovém souboru.

    Parametry:
        header_file (str): Cesta k .h souboru.

    Návratová hodnota:
        dict[str, list[str]]: Mapa názvů funkcí na seznam parametrů.
    """
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
    """
    Vybere nebo ověří hlavičkový soubor pomocí FZF.

    Parametry:
        header_file (str | None): Cesta k hlavičkovému souboru nebo None pro ruční výběr.

    Návratová hodnota:
        str: Validní cesta k hlavičkovému souboru.
    """
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
    """
    Extrahuje deklarace funkcí z hlavičkového souboru a ověří, že nějaké existují.

    Parametry:
        header_file (str): Cesta k .h souboru.

    Návratová hodnota:
        dict[str, list[str]]: Nalezené funkce a jejich parametry.
    """
    functions = extract_functions_from_header(header_file)
    if not functions:
        log_error(f"V souboru {header_file} nebyly nalezeny žádné funkce.")
        exit(1)
    return functions

def select_target_function(functions, function_name=None):
    """
    Vybere cílovou funkci ze seznamu funkcí.

    Parametry:
        functions (dict[str, list[str]]): Mapa dostupných funkcí.
        function_name (str | None): Název funkce pro automatický výběr (volitelné).

    Návratová hodnota:
        str: Vybraná funkce.
    """
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
    """
    Vybere odpovídající .c soubor.

    Parametry:
        directory (str): Kořenový adresář pro výběr.
        src_file (str | None): Předvolený soubor nebo None pro výběr.

    Návratová hodnota:
        str: Cesta k validnímu .c souboru.
    """
    if not src_file:
        log_info("\n Vyber odpovídající .c soubor:")
        src_file = fzf_select_file(".c")
    
    while not src_file or not os.path.exists(src_file):
        log_error("Chyba: Nevybral jsi platný .c soubor.")
        log_info("\n Vyber znovu odpovídající .c soubor:")
        src_file = fzf_select_file(".c")
    
    return src_file

def check_function_in_file(src_file, target_function):
    """
    Zkontroluje, zda .c soubor obsahuje zadanou funkci.

    Parametry:
        src_file (str): Cesta k .c souboru.
        target_function (str): Název hledané funkce.

    Návratová hodnota:
        bool: True pokud funkce existuje, jinak False (nebo ukončí běh).
    """
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

def prepare_function(header_file=None, src_file=None, function_name=None, use_klee=False, architecture=ACTIVE_ARCHITECTURE, main_mode="auto", own_main_file=None):
    """
    Připraví hlavičku, funkci a .c soubor pro testování nebo kompilaci.

    Parametry:
        header_file (str | None): Cesta k .h souboru.
        src_file (str | None): Cesta k .c souboru.
        function_name (str | None): Název funkce.
        use_klee (bool): Příznak zda se připravuje pro KLEE.
        architecture (str): Cílová architektura.
        main_mode (str): Způsob generování mainu ("auto", "template", "own").
        own_main_file (str | None): Vlastní main soubor.

    Návratová hodnota:
        str: Cesta ke generovanému binárnímu souboru.
    """

    header_file, target_function, functions = select_and_validate_function(header_file, function_name)

    # Extrahujeme adresář z hlavičkového souboru
    directory = os.path.dirname(header_file)
    
    # Vybereme odpovídající .c soubor
    src_file = select_and_validate_source_file(directory, src_file, target_function)

    # Generování `generated_main.c` souboru
    generate_main_file(target_function, functions, header_file, main_mode, own_main_file, directory)


    # Kompilace a generování binárního souboru
    binary_file = compile_and_generate_binary(src_file, target_function, architecture)

    if REMOVE_GENERATED_MAIN:
        delete_file(get_generated_main_path())
    
    if use_klee:
        prepare_klee(header_file, src_file, target_function)

    log_info(f"Vytvořen binární soubor: {binary_file}")
    return binary_file
    

def prepare_klee(header_file=None, src_file=None, function_name=None, architecture="native"):
    """
    Připraví soubory pro spuštění testů pomocí KLEE.

    Parametry:
        header_file (str | None): Hlavičkový soubor.
        src_file (str | None): Zdrojový soubor.
        function_name (str | None): Název funkce.
        architecture (str): Cílová architektura.

    Návratová hodnota:
        None
    """
    header_file, target_function, functions = select_and_validate_function(header_file, function_name)
    
    # Extrahujeme adresář z hlavičkového souboru
    directory = os.path.dirname(header_file)
    
    # Vybereme odpovídající .c soubor
    src_file = select_and_validate_source_file(directory, src_file, target_function)

    params = functions[target_function]
    constant_params = []

    log_info("\n Tato funkce má následující parametry:")
    for i, p in enumerate(params):
        print(f"  [{i}] {p}")
        
    log_info("\nChcete některé parametry zadat jako *konstanty* (namísto symbolických)?")
    log_info("Zadáním konstanty lze zjednodušit analýzu a předejít problémům při práci s pamětí nebo vstupy.")
    log_info("V některých případech (např. při alokaci nebo práci s řetězci) je zadání konstanty nutné nebo výrazně spolehlivější.")
    log_info("Příklady zadání:")
    log_info("  - Řetězec: hello")
    log_info("  - Pole (např. int *): 5 6 7 8")


    for i, param in enumerate(params):
        user_input = input(f"Zadejte hodnotu pro parametr '{param}' (ENTER ponechá jako symbolický): ")
        if user_input.strip():
            param_name = param.split()[-1]
            const_value = user_input.strip()
            # Uložíme ve formátu: "typ jméno=hodnota"
            constant_params.append(f"{param}={const_value}")
        else:
            constant_params.append(param)

    log_debug(constant_params)
    
    # Generování `generated_main_klee.c` pro KLEE
    generate_main_klee(target_function, constant_params, header_file)
    log_info(f"\n Generování `generated_main_klee.c` dokončeno pro funkci `{target_function}` ze souboru `{header_file}`.")

    # Kompilace pro KLEE (bitcode)
    log_info("Kompilace pro KLEE...")
    klee_dir = os.path.join(KLEE_OUTPUT, target_function)
    os.makedirs(klee_dir, exist_ok=True)
    compile_klee(klee_dir, src_file, os.path.dirname(src_file), target_arch=architecture)
    log_info(f"Kompilace pro KLEE dokončena.")

    # Vygenerování testovacích vstupů pro KLEE
    params = functions.get(target_function, [])
    param_types = [parse_param_type(param) for param in params]

    bitcode_file = os.path.join(klee_dir, "klee_program.bc")

    output_file = os.path.join(KLEE_RESULTS, f"gdb_inputs_{target_function}.txt")
    file_path, test_data = get_klee_test_inputs(klee_dir, bitcode_file, param_types, output_file, target_arch=architecture)

    if REMOVE_GENERATED_MAIN:
        delete_file(get_generated_main_klee_path())
    
    log_info(f"Testovací vstupy uloženy: {file_path}")
    log_info(f"Testovací data: {test_data}")


def parse_param_type(param_decl):
    """
    Převede deklaraci parametru na čistý typ.
     Např.:
        'int *array' -> 'int*'
        'const char *name' -> 'char*'

    Parametry:
        param_decl (str): Deklarace parametru, např. 'const int *x'.

    Návratová hodnota:
        str: Základní typ (např. 'int*').
    """
    tokens = param_decl.replace(',', '').split()
    base_type = ""
    for token in tokens[:-1]:
        # ignoruj 'const' a podobné modifikátory
        if token == "const":
            continue
        base_type += token.replace("*", "")  # odstranění případné * z base
    var_name = tokens[-1]

    # Pokud v názvu nebo kdekoliv je *, je to pointer
    if "*" in param_decl:
        return base_type + "*"
    return base_type

def select_and_validate_function(header_file=None, function_name=None):
    """
    Vybere hlavičkový soubor a ověří zvolenou funkci.

    Parametry:
        header_file (str | None): Cesta k .h souboru.
        function_name (str | None): Název cílové funkce.

    Návratová hodnota:
        tuple[str, str, dict[str, list[str]]]: (hlavičkový soubor, název funkce, mapa funkcí)
    """
    header_file = select_header_file(header_file)
    functions = extract_function_from_header(header_file)
    target_function = select_target_function(functions, function_name)
    return header_file, target_function, functions

def select_and_validate_source_file(directory, src_file, target_function):
    """
    Vybere a ověří zdrojový soubor podle funkce.

    Parametry:
        directory (str): Adresář pro hledání.
        src_file (str): Předvolený zdrojový soubor.
        target_function (str): Cílová funkce.

    Návratová hodnota:
        str: Validní .c soubor obsahující cílovou funkci.
    """
    src_file = select_source_file(directory, src_file)
    while not check_function_in_file(src_file, target_function):
        src_file = select_source_file(directory, src_file)
    return src_file

def generate_main_file(target_function, functions, header_file, main_mode, own_main_file, directory):
    """
    Generuje main soubor podle zvoleného módu.

    Parametry:
        target_function (str): Cílová funkce.
        functions (dict): Mapa funkcí.
        header_file (str): Cesta k .h souboru.
        main_mode (str): Mód generování ('auto', 'template', 'own').
        own_main_file (str | None): Vlastní main soubor.
        directory (str): Cílový adresář.

    Návratová hodnota:
        None
    """
    if main_mode == "auto":
        generate_main(target_function, functions[target_function], header_file)
    elif main_mode == "template":
        generate_main_template(target_function, functions[target_function], header_file)
        log_info("Template generated_main.c byl vygenerován. Upravte ho manuálně podle potřeby.")
        input("\nPozastaveno: Upravte `generated_main.c` dle potřeby a stiskněte ENTER pro pokračování...")
    elif main_mode == "own":
        own_main_file = handle_own_main_file(own_main_file, directory)
        set_generated_main_path(own_main_file)
    else:
        raise ValueError(f"Neplatný mód main generování: {main_mode}")    

def handle_own_main_file(own_main_file, directory):
    """
    Zpracuje vlastní main soubor a zkopíruje ho jako generated_main.c.

    Parametry:
        own_main_file (str): Cesta k vlastnímu main souboru.
        directory (str): Cílový adresář.

    Návratová hodnota:
        str: Cesta ke zkopírovanému souboru generated_main.c.
    """

    log_debug(f"Own main file: {own_main_file} {not os.path.exists(own_main_file)} {not own_main_file} ")
    if not own_main_file or not os.path.exists(own_main_file):
        log_info("Nebyl zadán platný vlastní main soubor.")
        log_info("Vyberte vlastní main soubor (`*.c`) pro pokračování:")
        own_main_file = fzf_select_file(".c")

        while not own_main_file or not os.path.exists(own_main_file):
            log_error("Chyba: Nevybral jsi platný .c soubor.")
            own_main_file = fzf_select_file(".c")
    
    dest = os.path.join(directory, "generated_main.c")
    # Ověříme, že nebudeme kopírovat soubor sám na sebe
    if os.path.abspath(own_main_file) != os.path.abspath(dest):
        shutil.copyfile(own_main_file, dest)
        log_info(f"Váš vlastní main soubor `{own_main_file}` byl zkopírován jako `generated_main.c`.")
    else:
        log_info(f"Váš vlastní main soubor již je `generated_main.c`. Kopírování není potřeba.")
    return dest

def compile_and_generate_binary(src_file, target_function, architecture):
    """
    Zkompiluje soubor a vytvoří výstupní binární soubor.

    Parametry:
        src_file (str): Zdrojový .c soubor.
        target_function (str): Název funkce.
        architecture (str): Cílová architektura ('arm', 'riscv', 'x86').

    Návratová hodnota:
        str: Cesta k binárnímu souboru.
    """
    log_debug("\n Kompilace `generated_main.c`...")
    src_dir = os.path.dirname(src_file)
    binary_file = ""
    if architecture == "arm":
        binary_file = os.path.join(BUILD_DIR, f"binary_ARM_{target_function}.out")
    elif architecture == "riscv":
        binary_file = os.path.join(BUILD_DIR, f"binary_RISCV_{target_function}.out")
    else:
        binary_file = os.path.join(BUILD_DIR, f"binary_x86_{target_function}.out")

    compile_binary(binary_file=binary_file, src_file=src_file, src_dir=src_dir, platform=architecture)
    log_info(f"Kompilace dokončena pro `{target_function}`.")
    return binary_file
