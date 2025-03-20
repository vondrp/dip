import os
import re
import subprocess
import glob

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "src")
SRC_FILE = os.path.join(os.path.dirname(__file__), "..", "src", "test_program.c")
GENERATED_MAIN = os.path.join(os.path.dirname(__file__), "..", "src", "generated_main.c")
GDB_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "gdb", "gdb_trace.py")


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

def generate_main(target_function, params):
    """Vytvoří `generated_main.c` pro volání vybrané funkce s argumenty z příkazové řádky."""
    with open(GENERATED_MAIN, "w") as f:
        f.write('#include <stdio.h>\n#include <stdlib.h>\n')
        f.write('#define MAIN_DEFINED\n')
        f.write('#include "test_program.c"\n\n')

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
            else:
                converted_params.append(f"argv[{i + 1}]")

        f.write(f'    printf("Spouštím test funkce: {target_function}\\n");\n')
        f.write(f"    {target_function}({', '.join(converted_params)});\n")
        f.write("    return 0;\n}\n")


def compile(binary_file):
    """Přeloží pouze potřebné `.c` soubory pro `generated_main.c`."""
    needed_headers = find_dependencies(SRC_FILE)
    header_to_source = map_headers_to_sources()

    # Najdeme odpovídající `.c` soubory
    needed_sources = {header_to_source[h] for h in needed_headers if h in header_to_source}
    needed_sources.add(GENERATED_MAIN)  # Vždy přidáme `generated_main.c`

    compile_cmd = ["gcc", "-g", "-o", binary_file] + list(needed_sources)
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
        print("Smazán `generated_main.c`")

if __name__ == "__main__":
    functions = extract_functions_and_params(SRC_FILE)
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

    param_values = []
    for param in functions[target_function]:
        value = input(f"Zadej hodnotu pro `{param}`: ")
        param_values.append(value)

    param_str = "_".join(param_values).replace(" ", "")
    binary_file = os.path.join(os.path.dirname(__file__), f"..", "build", f"test_binary_{target_function}_{param_str}")
    trace_file = os.path.join(os.path.dirname(__file__), f"..", "logs", f"trace_{target_function}_{param_str}.log")

    generate_main(target_function, functions[target_function])
    compile(binary_file)
    run_gdb_trace(binary_file, trace_file, param_values)
    cleanup()
