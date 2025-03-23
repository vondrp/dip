import os
import re
import subprocess
import glob

from concolic_test_klee import get_klee_test_inputs
from analyze_trace_advanced import analyze_traces_in_folder
from compare_runs import compare_runs

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
SRC_FILE = os.path.join(os.path.dirname(__file__), "..", "src", "test_program.c")
GENERATED_MAIN = os.path.join(os.path.dirname(__file__), "..", "src", "generated_main.c")
GENERATED_MAIN_ANGR = os.path.join(os.path.dirname(__file__), "..", "src", "generated_main_angr.c")
GENERATED_MAIN_KLEE = os.path.join(os.path.dirname(__file__), "..", "src", "generated_main_klee.c")

GDB_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "gdb", "gdb_trace.py")


# Definice cesty ke složce pro KLEE
KLEE_BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "build", "klee")
os.makedirs(KLEE_BUILD_DIR, exist_ok=True)

def find_dependencies(source_file):
    """Najde všechny soubory, které `source_file` přímo includuje."""
    dependencies = set()
    with open(source_file, "r") as f:
        for line in f:
            match = re.match(r'#include\s+"(.+?)"', line)
            if match:
                dependencies.add(match.group(1))  # Uložíme název hlavičkového souboru
    return dependencies

def map_headers_to_sources():
    """Najde `.c` soubor pro každou `.h` hlavičku ve složce `src/`."""
    source_files = glob.glob(os.path.join(SRC_DIR, "*.c"))
    header_to_source = {}

    for src_file in source_files:
        base_name = os.path.splitext(os.path.basename(src_file))[0]
        header_file = f"{base_name}.h"
        header_to_source[header_file] = src_file  # Mapujeme `.h` → `.c`

    return header_to_source


def extract_functions_and_params(source_file):
    """Najde definice funkcí a jejich parametry v souboru."""
    functions = {}
    with open(source_file, "r") as f:
        for line in f:
            match = re.match(r"^\s*(\w+)\s+(\w+)\s*\((.*?)\)", line)
            if match:
                return_type, func_name, params = match.groups()
                param_list = [p.strip() for p in params.split(",") if p]
                functions[func_name] = param_list
    return functions

def generate_main_klee(target_function, params):
    """Vytvoří `generated_main_klee.c` pro analýzu s KLEE."""
    with open(GENERATED_MAIN_KLEE, "w") as f:
        f.write('#include <klee/klee.h>\n')
        f.write('#include <stdio.h>\n\n')
        f.write(f'extern void {target_function}({", ".join(params)});\n\n')

        f.write("int main() {\n")

        symbolic_params = []
        for i, param in enumerate(params):
            param_type = param.split()[0]  # Získáme typ parametru
            var_name = f"param_{i}"

            if "int" in param_type:
                f.write(f"    int {var_name};\n")
                f.write(f"    klee_make_symbolic(&{var_name}, sizeof({var_name}), \"{var_name}\");\n")
            elif "float" in param_type or "double" in param_type:
                f.write(f"    {param_type} {var_name};\n")
                f.write(f"    klee_make_symbolic(&{var_name}, sizeof({var_name}), \"{var_name}\");\n")
            elif "char" in param_type and "*" in param:  # Řetězec (`char *`)
                f.write(f"    char {var_name}[10];\n")  # Zajišťujeme pevnou velikost řetězce
                f.write(f"    klee_make_symbolic({var_name}, sizeof({var_name}), \"{var_name}\");\n")
            elif "char" in param_type:
                f.write(f"    char {var_name};\n")
                f.write(f"    klee_make_symbolic(&{var_name}, sizeof({var_name}), \"{var_name}\");\n")
            else:
                f.write(f"    {param_type} {var_name};\n")  # Ostatní typy (např. structy)

            symbolic_params.append(var_name)

        f.write(f'\n    printf("Spouštím test funkce: {target_function}\\n");\n')
        f.write(f"    {target_function}({', '.join(symbolic_params)});\n")

        f.write("    return 0;\n}\n")


def generate_main_angr(target_function, params):
    """Vytvoří `generated_main.c`, který umožní Angr efektivně analyzovat vstupy."""
    with open(GENERATED_MAIN_ANGR, "w") as f:
        f.write('#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n')
        f.write('#define MAIN_DEFINED\n')
        f.write('#include "test_program.c"\n\n')

        f.write("int main(int argc, char *argv[]) {\n")
        f.write("    if (argc < %d) {\n" % (len(params) + 1))
        f.write(f'        printf("Použití: %s {" ".join(["<param>" for _ in params])}\\n", argv[0]);\n')
        f.write("        return 1;\n    }\n\n")

        converted_params = []
        for i, param in enumerate(params):
            param_type = param.split()[0]
            var_name = f"param_{i}"

            # Použití `volatile`, aby zabránilo optimalizacím a zajistilo symbolickou exekuci
            if "int" in param_type:
                f.write(f"    volatile {param_type} {var_name} = atoi(argv[{i + 1}]);\n")
            elif "float" in param_type or "double" in param_type:
                f.write(f"    volatile {param_type} {var_name} = atof(argv[{i + 1}]);\n")
            elif "char" in param_type and "*" in param:  # Řetězec (`char *`)
                f.write(f"    volatile {param_type} {var_name} = argv[{i + 1}];\n")
            elif "char" in param_type:  # Jednotlivý znak (`char`)
                f.write(f"    volatile {param_type} {var_name} = argv[{i + 1}][0];\n")
            else:
                f.write(f"    volatile {param_type} {var_name};\n")  # Ostatní typy

            converted_params.append(var_name)

        f.write(f'\n    printf("Spouštím test funkce: {target_function}\\n");\n')
        f.write(f"    {target_function}({', '.join(converted_params)});\n")

        f.write("    return 0;\n}\n")

def generate_main(target_function, params):
    """Vytvoří `generated_main.c` pro volání vybrané funkce s argumenty z příkazové řádky."""
    with open(GENERATED_MAIN, "w") as f:
        f.write('#include <stdio.h>\n#include <stdlib.h>\n')
        f.write('#define MAIN_DEFINED\n')
        f.write('#include "test_program.h"\n\n')

        f.write("int main(int argc, char *argv[]) {\n")
        f.write("    if (argc < %d) {\n" % (len(params) + 1))
        f.write(f'        printf("Použití: %s {" ".join(["<param>" for _ in params])}\\n", argv[0]);\n')
        f.write("        return 1;\n    }\n")

        converted_params = []
        for i, param in enumerate(params):
            param_type = param.split()[0]
            if "int" in param_type:
                converted_params.append(f"atoi(argv[{i + 1}])")
            elif "float" in param_type or "double" in param_type:
                converted_params.append(f"atof(argv[{i + 1}])")
            elif "char" in param_type:
                converted_params.append(f"argv[{i + 1}][0]")  # Použijeme první znak řetězce
            else:
                converted_params.append(f"argv[{i + 1}]")

        f.write(f'    printf("Spouštím test funkce: {target_function}\\n");\n')
        f.write(f"    {target_function}({', '.join(converted_params)});\n")
        f.write("    return 0;\n}\n")

def compile_angr(binary_file):
    """Přeloží program optimalizovaný pro Angr."""
    needed_headers = find_dependencies(SRC_FILE)
    header_to_source = map_headers_to_sources()

    # Najdeme odpovídající `.c` soubory
    needed_sources = {header_to_source[h] for h in needed_headers if h in header_to_source}
    needed_sources.add(GENERATED_MAIN_ANGR)  # Speciální main pro Angr

    compile_cmd = [
        "gcc", "-g", "-O0", "-fno-omit-frame-pointer", "-fno-strict-aliasing", "-no-pie",
        "-o", binary_file
    ] + list(needed_sources)

    print(f"[INFO] Kompiluji pro Angr: {' '.join(compile_cmd)}")
    subprocess.run(compile_cmd, check=True)


def compile_klee(klee_dir, src_file):
    """Přeloží program pro použití s KLEE a uloží výstup do `klee_dir`."""
    
    main_bc = os.path.join(klee_dir, "generated_main_klee.bc")
    linked_bc = os.path.join(klee_dir, "klee_program.bc")

    print(f"[INFO] 📂 Vytvářím KLEE build: {klee_dir}")

    # Najdeme všechny závislé soubory
    dependencies = find_dependencies(src_file)
    header_to_source = map_headers_to_sources()
    needed_sources = {header_to_source[h] for h in dependencies if h in header_to_source}
    needed_sources.add(src_file)  # Přidáme hlavní zdrojový soubor
    needed_sources = list(needed_sources)  # Převedeme na seznam

    print(f"[INFO] 📜 Překládané zdrojové soubory: {needed_sources}")

    # Překlad `generated_main_klee.c`
    subprocess.run([
        "clang-13", "-emit-llvm", "-g", "-c",
        "-I/home/vondrp/manualKlee/klee/include",  # Cesta ke klee.h
        GENERATED_MAIN_KLEE, "-o", main_bc
    ], check=True)

    # Překlad všech potřebných souborů
    bc_files = []
    for src in needed_sources:
        bc_file = os.path.join(klee_dir, os.path.basename(src).replace(".c", ".bc"))
        subprocess.run([
            "clang-13", "-emit-llvm", "-g", "-c",
            "-DMAIN_DEFINED",
            src, "-o", bc_file
        ], check=True)
        bc_files.append(bc_file)

    print(f"[INFO] ✅ Přeložené BC soubory: {bc_files}")

    # Spojení všech `.bc` souborů do jednoho
    subprocess.run(["llvm-link-13", main_bc] + bc_files + ["-o", linked_bc], check=True)

    print(f"[INFO] ✅ Spojený LLVM bitcode: {linked_bc}")



def compile_klee_old(klee_dir):
    """Přeloží program pro použití s KLEE a uloží výstup do `build/klee/`."""
    main_bc = os.path.join(klee_dir, "generated_main_klee.bc")
    test_bc = os.path.join(klee_dir, "test_program.bc")
    linked_bc = os.path.join(klee_dir, "klee_program.bc")

    print(f"[INFO] 📂 Vytvářím KLEE build: {klee_dir}")
    print(f"[INFO] Generovaný LLVM bitcode pro main: {main_bc}")
    print(f"[INFO] Generovaný LLVM bitcode pro test_program: {test_bc}")

    # Překlad `generated_main_klee.c`
    subprocess.run([
        "clang-13", "-emit-llvm", "-g", "-c",
        "-I/home/vondrp/manualKlee/klee/include",  # Cesta ke klee.h
        GENERATED_MAIN_KLEE, "-o", main_bc
    ], check=True)

    # Překlad `test_program.c`
    subprocess.run([
        "clang-13", "-emit-llvm", "-g", "-c",
        "-DMAIN_DEFINED",
        SRC_FILE, "-o", test_bc
    ], check=True)

    # Spojení `.bc` souborů do jednoho
    subprocess.run(["llvm-link-13", main_bc, test_bc, "-o", linked_bc], check=True)

    print(f"[INFO] ✅ Spojený LLVM bitcode: {linked_bc}")

def compile(binary_file):
    """Přeloží pouze potřebné `.c` soubory pro `generated_main.c`."""
    needed_headers = find_dependencies(SRC_FILE)
    header_to_source = map_headers_to_sources()

    # Najdeme odpovídající `.c` soubory
    needed_sources = {header_to_source[h] for h in needed_headers if h in header_to_source}
    needed_sources.add(GENERATED_MAIN)  # Vždy přidáme `generated_main.c`

    compile_cmd = ["gcc", "-g", "-fno-omit-frame-pointer", "-o", binary_file] + list(needed_sources)
    print(f"Kompiluji: {' '.join(compile_cmd)}")
    subprocess.run(compile_cmd, check=True)


def run_gdb_trace(binary_file, trace_file, args):
    """Spustí GDB s vybranými parametry a zachytí instrukce do `trace.log`."""
    gdb_cmd = [
        "gdb", "-q", "-ex", f"source {GDB_SCRIPT}",
        "-ex", "starti",
        "-ex", f"trace-asm {trace_file}",
        "-ex", "quit",
        "--args", binary_file, *args
    ]
    print(f"Spouštím GDB: {' '.join(gdb_cmd)}")
    subprocess.run(gdb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def cleanup():
    """Odstraní `generated_main.c`."""
    if os.path.exists(GENERATED_MAIN):
        os.remove(GENERATED_MAIN)
        print("[INFO] Smazán `generated_main.c`")

    if os.path.exists(GENERATED_MAIN_KLEE):
        os.remove(GENERATED_MAIN_KLEE) 
        print("[INFO] Smazán `generated_main_klee.c`")
  

def select_target_function(src_file):
    functions = extract_functions_and_params(src_file)
    if not functions:
        print("Nenalezeny žádné funkce v souboru.")
        exit(1)
    
    print("Nalezené funkce:")
    for func, params in functions.items():
        print(f" - {func}({', '.join(params)})")
    
    target_function = input("Zadej jméno funkce k testování: ")
    if target_function not in functions:
        print("Neplatná funkce.")
        exit(1)
    
    return target_function, functions[target_function], functions

def prepare_directories(target_function):
    trace_dir = os.path.join(os.path.dirname(__file__), "..", "logs", target_function)
    os.makedirs(trace_dir, exist_ok=True)
    
    klee_dir = os.path.join(trace_dir, "klee")
    os.makedirs(klee_dir, exist_ok=True)
    
    return trace_dir, klee_dir

def run_klee_analysis(target_function, functions, param_types, klee_dir, src_file):
    bitcode_file = os.path.join(klee_dir, "klee_program.bc")
    generate_main_klee(target_function, functions[target_function])
    compile_klee(klee_dir, src_file)
    
    file_path, test_data = get_klee_test_inputs(klee_dir, bitcode_file, param_types)
    print(f"[INFO] 📁 Testovací vstupy uloženy: {file_path}")
    return test_data

def compile_and_trace(target_function, functions, param_values, param_str, trace_dir, binary_file):
    generate_main(target_function, functions[target_function])
    compile(binary_file)
    
    trace_file_user = os.path.join(trace_dir, f"trace_{target_function}_{param_str}.log")
    run_gdb_trace(binary_file, trace_file_user, param_values)

def run_klee_traces(binary_file, test_data, trace_dir, target_function):
    for i, klee_params in enumerate(test_data):
        klee_param_list = klee_params.split()
        klee_param_str = "_".join(klee_param_list)
        trace_file_klee = os.path.join(trace_dir, f"trace_{target_function}_{klee_param_str}.log")
        print(f"[INFO] 🔍 Spouštím GDB pro KLEE vstupy: {klee_param_list}")
        run_gdb_trace(binary_file, trace_file_klee, klee_param_list)

def analyze_results(trace_dir, binary_file, target_function):
    analysis_output_dir = os.path.join(trace_dir, "analysis")
    analyze_traces_in_folder(trace_dir, analysis_output_dir, binary_file, target_function)
    compare_runs(analysis_output_dir)

def main_logic():
    src_file = os.path.join(os.path.dirname(__file__), "..", "src", "test_program.c")
    target_function, param_types, functions = select_target_function(src_file)
    
    param_values = []
    for param in functions[target_function]:
        value = input(f"Zadej hodnotu pro `{param}`: ")
        param_values.append(value)
    param_str = "_".join(param_values).replace(" ", "")
    
    trace_dir, klee_dir = prepare_directories(target_function)
    test_data = run_klee_analysis(target_function, functions, param_types, klee_dir, SRC_FILE)
    
    binary_file = os.path.join(os.path.dirname(__file__), "..", "build", f"test_{target_function}_{param_str}")
    compile_and_trace(target_function, functions, param_values, param_str, trace_dir, binary_file)
    run_klee_traces(binary_file, test_data, trace_dir, target_function)
    analyze_results(trace_dir, binary_file, target_function)
    cleanup()

if __name__ == "__main__":
    main_logic()