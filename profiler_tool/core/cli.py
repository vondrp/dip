import argparse
import os
import re
import subprocess


from core.config import BUILD_DIR, LOGS_DIR, TRACE_DIR, ANALYSIS_DIR

from core.engine.generator import generate_main, generate_main_klee
from core.engine.compiler import compile_x86, compile_klee
from core.engine.tracer import run_gdb_trace
from core.engine.klee_runner import get_klee_test_inputs
from core.engine.trace_analysis import analyze_trace
from core.engine.comparison import compare_runs


#from core.engine.analyzer import analyze_trace, compare_runs
def fzf_select_files(extension, directory="."):
    """Použije fzf k výběru jednoho nebo více souborů s danou příponou v zadaném adresáři."""
    try:
        command = f"find {directory} -type f -name '*{extension}' | fzf -m"
        file_paths = subprocess.check_output(command, shell=True).decode().strip().split("\n")
        return [f for f in file_paths if os.path.exists(f)]
    except subprocess.CalledProcessError:
        print("❌ fzf nebyl úspěšně spuštěn nebo nenalezl žádné soubory. Zkusíme manuální volbu.")
        file_paths = input(f"Zadej cesty k {extension} souborům (oddělené mezerou): ").strip().split()
        return [f for f in file_paths if os.path.exists(f)]
        
def fzf_select_file(extension, directory="."):
    """Použije fzf k výběru souboru s danou příponou v zadaném adresáři."""
    try:
        command = f"find {directory} -type f -name '*{extension}' | fzf"
        file_path = subprocess.check_output(command, shell=True).decode().strip()
        return file_path if file_path and os.path.exists(file_path) else None
    except subprocess.CalledProcessError:
        print("❌ fzf nebyl úspěšně spuštěn nebo nenalezl žádný soubor. Zkusíme manuální volbu.")
        # Pokud fzf selže, dáme možnost manuálního výběru souboru
        file_path = input(f"Zadej cestu k {extension} souboru: ").strip()
        
        if not os.path.exists(file_path):
            print(f"❌ Soubor {file_path} neexistuje.")
            return None
        
        return file_path
    
    return None


def fzf_select_directory(base_dir):
    """Použije fzf k výběru složky v zadaném adresáři."""
    try:
        command = f"find {base_dir} -type d | fzf"
        directory = subprocess.check_output(command, shell=True).decode().strip()
        return directory if directory and os.path.exists(directory) else None
    except subprocess.CalledProcessError:
        print("❌ fzf nebyl úspěšně spuštěn nebo nenalezl žádnou složku. Zkusíme manuální volbu.")
        directory = input(f"Zadej cestu ke složce v {base_dir}: ").strip()
        return directory if os.path.exists(directory) else None


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
    binary_file = os.path.join(BUILD_DIR, f"binary_{target_function}.out")
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


def extract_function_name(binary_file):
    """Extrahuje jméno funkce z názvu binárního souboru."""
    match = re.search(r"binary_(\w+)\.out", os.path.basename(binary_file))
    return match.group(1) if match else "unknown"



def run_trace(binary_file=None, param_file=None):
    """Umožní uživateli vybrat binárku a spustit trace pro více sad parametrů (ze souboru nebo ručně)."""
    if not binary_file:
        print("\n📂 Vyber binární soubor:")
        binary_file = fzf_select_file(".out", BUILD_DIR)

    if not binary_file or not os.path.exists(binary_file):
        print("❌ Nebyla vybrána žádná binárka.")
        return

    func_name = extract_function_name(binary_file)

    param_sets = []

    # 🔍 Pokud je zadaný soubor s parametry, načteme je
    if param_file:
        if not os.path.exists(param_file):
            print(f"❌ Soubor {param_file} neexistuje!")
            return

        with open(param_file, "r") as f:
            for line in f:
                params = line.strip().split()
                param_sets.append(params)
        
        print(f"📄 Načteno {len(param_sets)} sad parametrů ze souboru `{param_file}`.")

    # 📝 Ruční zadávání, pokud není soubor
    if not param_sets:
        print("\n🔢 Zadej sady parametrů pro spuštění (každou sadu potvrď Enterem).")
        print("💡 Dvakrát Enter (prázdný řádek) ukončí zadávání.")
        print("📌 Pokud funkce nemá žádné parametry, jen stiskni Enter.")

        while True:
            param_input = input("📝 Parametry: ").strip()
            if param_input == "" and len(param_sets) > 0:
                break  # Konec zadávání po druhém Enteru
            param_sets.append(param_input.split())

    if not param_sets:
        param_sets.append([])  # Prázdná sada, pokud uživatel nic nezadá

    # 🔄 Spustit trace a analýzu pro každou sadu parametrů
    for params in param_sets:
        param_str = "_".join(params) if params else "no_params"
        trace_file = os.path.join(TRACE_DIR, f"trace_{func_name}_{param_str}.log")

        print(f"\n🛠 Spouštím trace pro {binary_file} s parametry {params}")
        run_gdb_trace(binary_file, trace_file, params)
        print(f"✅ Trace dokončen! Výstup: {trace_file}")

        # Spustit analýzu trace souboru
        output_json_dir = os.path.join(ANALYSIS_DIR, func_name)
        os.makedirs(output_json_dir, exist_ok=True)

        json_filename = f"instructions_{func_name}_{param_str}.json"
        output_json = os.path.join(output_json_dir, json_filename)

        print(f"\n🔍 Probíhá analýza pro trace soubor: {trace_file}")
        analyze_trace(trace_file, binary_file, func_name, output_json)
        print(f"✅ Analýza dokončena! Výstupní soubor: {output_json}")


def compare_json_runs(folder=None, files=None):
    """Porovná běhy na základě JSON souborů ze složky nebo ručně vybraných souborů."""
    if not files and not folder:
        print("\n📂 Vyber složku s JSON soubory nebo ručně vyber soubory:")
        choice = input("[1] Vybrat složku\n[2] Vybrat konkrétní soubory\n> ")

        if choice == "1":
            folder = fzf_select_directory(ANALYSIS_DIR)
            if not folder:
                print("❌ Nebyla vybrána žádná složka.")
                return
        elif choice == "2":
            files = fzf_select_files(".json", ANALYSIS_DIR)  # Musíme tuto funkci správně implementovat
            if not files:
                print("❌ Nebyly vybrány žádné soubory.")
                return
        else:
            print("❌ Neplatná volba. Ukončuji.")
            return

    if folder:
        compare_runs(folder)  # Pokud máme složku, předáme ji funkci
    elif files:
        compare_runs(files=files)  # Pokud máme soubory, předáme je
    else:
        print("❌ Nebyla vybrána žádná data pro porovnání.")

def main():
    parser = argparse.ArgumentParser(description="CLI nástroj pro analýzu binárek.")
    subparsers = parser.add_subparsers(dest="command")

    # Výběr funkce a kompilace
    select_parser = subparsers.add_parser("select-function", help="Vyber funkci z .h souboru a kompiluj.")
    select_parser.add_argument("-H", "--header", required=False, help="Hlavičkový soubor .h")
    select_parser.add_argument("-c", "--source", required=False, help="Zdrojový soubor .c")
    select_parser.add_argument("--klee", action="store_true", help="Použít KLEE analýzu")

    # Spuštění trace
    trace_parser = subparsers.add_parser("run-trace", help="Spusť binárku, vytvoř trace.log a proveď analýzu")
    trace_parser.add_argument("-b", "--binary", help="Cesta k binárnímu souboru")
    trace_parser.add_argument("-p", "--params", nargs="*", help="Parametry pro spuštění binárky")

    trace_parser = subparsers.add_parser("run-trace", help="Spusť binárku, vytvoř trace.log a proveď analýzu")
    trace_parser.add_argument("-b", "--binary", help="Cesta k binárnímu souboru")
    trace_parser.add_argument("-f", "--file", help="Soubor obsahující sady parametrů (každý řádek = jedna sada)")

    # Porovnání běhů
    compare_parser = subparsers.add_parser("compare-runs", help="Porovnej běhy na základě JSON souborů")
    compare_parser.add_argument("-d", "--directory", help="Složka s JSON soubory")
    compare_parser.add_argument("-f", "--files", nargs="*", help="Seznam JSON souborů k porovnání")


    args = parser.parse_args()

    if args.command == "select-function":
        select_function(header_file=args.header, src_file=args.source, use_klee=args.klee)
    elif args.command == "run-trace":
        run_trace(args.binary, args.file)
    elif args.command == "compare-runs":
        compare_json_runs(folder=args.directory, files=args.files)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
