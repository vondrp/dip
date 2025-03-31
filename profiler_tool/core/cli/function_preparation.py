# function_preparation.py
import os
from .file_selection import fzf_select_file
from core.engine.generator import generate_main, generate_main_klee
from core.engine.compiler import compile_x86, compile_klee
from core.engine.klee_runner import get_klee_test_inputs
from core.engine.trace_analysis import analyze_trace

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

def prepare_function(header_file=None, src_file=None, function_name=None, use_klee=False):
    """Nechá uživatele vybrat .h soubor, funkci a odpovídající .c soubor."""
    # ✅ Výběr hlavičkového souboru pomocí fzf
    if not header_file:
        header_file = fzf_select_file(".h")

    while not header_file or not os.path.exists(header_file):
        print("❌ Chyba: Nevybral jsi platný .h soubor.")
        header_file = fzf_select_file(".h")

    # 🔍 Extrakce funkcí z hlavičkového souboru
    functions = extract_functions_from_header(header_file)
    if not functions:
        print(f"❌ V souboru {header_file} nebyly nalezeny žádné funkce.")
        exit(1)

    # Výběr funkce
    if function_name:
        if function_name in functions:
            target_function = function_name
        else:
            print(f"❌ Funkce `{function_name}` nebyla nalezena v `{header_file}`.")
            target_function = input("\n📝 Zadej jméno funkce k použití: ")
    else:
        target_function = input("\n📝 Zadej jméno funkce k použití: ")

    print(f"📌 Vybraná funkce: {target_function}")

    # Generování kódu
    generate_main(target_function, functions[target_function], header_file)
    print(f"\n✅ Generování `generated_main.c` dokončeno pro funkci `{target_function}` ze souboru `{header_file}`.")

    # Kompilace
    binary_file = f"binary_{target_function}.out"
    compile_x86(binary_file, src_file)
    print(f"✅ Kompilace dokončena pro `{target_function}`.")

    # KLEE analýza
    if use_klee:
        klee_dir = os.path.join(KLEE_OUTPUT, target_function)
        os.makedirs(klee_dir, exist_ok=True)
        generate_main_klee(target_function, functions[target_function], header_file)
        print(f"✅ Vygenerován `generated_main_klee.c`.")  
        compile_klee(klee_dir, src_file)
