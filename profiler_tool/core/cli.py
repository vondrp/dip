import argparse
import os
import re
import subprocess


from core.config import BASE_DIR

from core.engine.generator import generate_main, generate_main_klee
from core.engine.compiler import compile_x86, compile_klee
from core.engine.tracer import run_gdb_trace
from core.engine.klee_runner import get_klee_test_inputs

#from core.engine.analyzer import analyze_trace, compare_runs

def fzf_select_file(extension):
    """Použije fzf k výběru souboru s danou příponou."""
    try:
        # Získáme aktuální adresář, ve kterém se nacházíme
        #current_dir = os.getcwd()

        # Přidáme možnost vrácení se zpět o úroveň výš
        #command = f"find {current_dir} -type f -name '*{extension}' | fzf --preview 'cat {}' --bind 'ctrl-u:up,ctrl-d:down,ctrl-h:backward-delete-char'"

        # Spustíme fzf a získáme vybraný soubor
        #file_path = subprocess.check_output(command, shell=True).decode().strip()

        # Použijeme příkaz find a fzf pro vyhledání souboru
        command = f"find . -type f -name '*{extension}' | fzf"
        file_path = subprocess.check_output(command, shell=True).decode().strip()
        
        # Zkontrolujeme, jestli uživatel vybral nějaký soubor
        if file_path and os.path.exists(file_path):
            return file_path
        else:
            print(f"❌ Nebyl vybrán žádný {extension} soubor.")
            return None
    except subprocess.CalledProcessError:
        print("❌ fzf nebyl úspěšně spuštěn nebo nenalezl žádný soubor. Zkusíme manuální volbu.")
        # Pokud fzf selže, dáme možnost manuálního výběru souboru
        file_path = input(f"Zadej cestu k {extension} souboru: ").strip()
        
        if not os.path.exists(file_path):
            print(f"❌ Soubor {file_path} neexistuje.")
            return None
        
        return file_path
    return None  # Pokud nic nevybral


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


def select_function(header_file=None, src_file=None, use_klee=False):
    """Nechá uživatele vybrat .h soubor, funkci a odpovídající .c soubor."""
    print(f"Klee {use_klee}")
    # ✅ Výběr hlavičkového souboru pomocí fzf
    if not header_file:
        print("\n📂 Vyber hlavičkový soubor (.h):")
        header_file = fzf_select_file(".h")

    # Kontrola platnosti .h souboru, opakovat, dokud nebude platný
    while not header_file or not os.path.exists(header_file):
        print("❌ Chyba: Nevybral jsi platný .h soubor.")
        print("\n📂 Vyber znovu hlavičkový soubor (.h):")
        header_file = fzf_select_file(".h")    


    # 🔍 Extrakce funkcí z hlavičkového souboru
    functions = extract_functions_from_header(header_file)
    if not functions:
        print(f"❌ V souboru {header_file} nebyly nalezeny žádné funkce.")
        exit(1)

    # 🛠 Výběr funkce
    print("\n📌 Nalezené funkce v hlavičkovém souboru:")
    for func, params in functions.items():
        param_str = ", ".join(params) if params else "void"
        print(f" - {func}({param_str})")

    target_function = input("\n📝 Zadej jméno funkce k použití: ")
    while target_function not in functions:
        print("❌ Neplatná funkce. Zkus to znovu.")
        target_function = input("\n📝 Zadej jméno funkce k použití: ")    


    param_types = [param.split()[0] for param in functions[target_function]]
    print(f"Parametry typy: {param_types}")
    # 🛠 Výběr .c souboru pomocí fzf, pokud není zadán
    if not src_file:
        print("\n📂 Vyber odpovídající .c soubor:")
        src_file = fzf_select_file(".c")

    # Kontrola platnosti .c souboru a existence vybrané funkce
    while not src_file or not os.path.exists(src_file):
        print("❌ Chyba: Nevybral jsi platný .c soubor.")
        print("\n📂 Vyber znovu odpovídající .c soubor:")
        src_file = fzf_select_file(".c")

    # Zkontrolujeme, jestli .c soubor obsahuje funkci
    with open(src_file, "r") as f:
        file_content = f.read()
        if target_function not in file_content:
            print(f"❌ Soubor {src_file} neobsahuje funkci {target_function}. Zkus to znovu.")
            src_file = None
            while not src_file or not os.path.exists(src_file) or target_function not in open(src_file).read():
                print("\n📂 Vyber odpovídající .c soubor s požadovanou funkcí:")
                src_file = fzf_select_file(".c")

    # Vygenerování `generated_main.c`
    generate_main(target_function, functions[target_function], header_file)

    print(f"\n✅ Generování `generated_main.c` dokončeno pro funkci `{target_function}` ze souboru `{header_file}`.")

    # 🔧 Kompilace souboru `generated_main.c`
    print("\n🔨 Kompilace `generated_main.c`...")
    src_dir = os.path.dirname(src_file)
    binary_file = os.path.join(BASE_DIR, "build", f"binary_{target_function}.out")
    compile_x86(binary_file=binary_file, src_file=src_file, src_dir = src_dir)
    print(f"✅ Kompilace dokončena pro `generated_main.c`.")

    if use_klee:
        klee_dir = os.path.join(BASE_DIR, "logs", target_function, "klee_output")
        os.makedirs(klee_dir, exist_ok=True)
        bitcode_file = os.path.join(klee_dir, "klee_program.bc")
 
        generate_main_klee(target_function, functions[target_function], header_file)
        print(f"✅ Vygenerován `generated_main_klee.c`.")

        compile_klee(klee_dir, src_file, src_dir)
        print(f"✅ Kompilace pro KLEE dokončena.")

        file_path, test_data = get_klee_test_inputs(klee_dir, bitcode_file, param_types)
        print(f"[INFO] 📁 Testovací vstupy uloženy: {file_path}")
        print(f"[INFO] 🔍 Testovací data: {test_data}")


def run_trace(binary, params):
    """Spustí binárku s parametry a vytvoří trace.log."""
    # TODO: Spuštění a získání logu
    print(f"Spouštím {binary} s parametry {params}")

def analyze_trace(trace_file):
    """Analyzuje trace.log a vytvoří JSON."""
    # TODO: Implementace analýzy
    print(f"Analyzuji {trace_file} -> výstupní JSON")

def compare_results(json_dir):
    """Porovná více výsledků analýzy."""
    # TODO: Implementace porovnání
    print(f"Porovnávám výsledky v {json_dir}")

def main():
    parser = argparse.ArgumentParser(description="CLI nástroj pro analýzu binárek.")
    subparsers = parser.add_subparsers(dest="command")

    # Výběr funkce a kompilace
    select_parser = subparsers.add_parser("select-function", help="Vyber funkci z .h souboru a kompiluj.")
    select_parser.add_argument("-H", "--header", required=False, help="Hlavičkový soubor .h")
    select_parser.add_argument("-c", "--source", required=False, help="Zdrojový soubor .c")
    select_parser.add_argument("--klee", action="store_true", help="Použít KLEE analýzu")


    # Spuštění trace
    trace_parser = subparsers.add_parser("run-trace", help="Spusť binárku a vytvoř trace.log")
    trace_parser.add_argument("binary", help="Binární soubor")
    trace_parser.add_argument("params", nargs="+", help="Parametry pro spuštění")

    # Analýza trace logu
    analyze_parser = subparsers.add_parser("analyze-trace", help="Analyzuj trace.log")
    analyze_parser.add_argument("trace_file", help="Trace log k analýze")

    # Porovnání výsledků
    compare_parser = subparsers.add_parser("compare-results", help="Porovnej výsledky analýzy")
    compare_parser.add_argument("json_dir", help="Složka s JSON soubory")

    args = parser.parse_args()

    if args.command == "select-function":
        select_function(header_file=args.header, src_file=args.source, use_klee=args.klee)
    elif args.command == "run-trace":
        run_trace(args.binary, args.params)
    elif args.command == "analyze-trace":
        analyze_trace(args.trace_file)
    elif args.command == "compare-results":
        compare_results(args.json_dir)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
