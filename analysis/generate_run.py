import os
import re
import subprocess

SRC_FILE = os.path.join(os.path.dirname(__file__), "..", "src", "test_program.c")
GENERATED_MAIN = os.path.join(os.path.dirname(__file__), "..", "src", "generated_main.c")
BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "test_binary")
TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trace.log")
GDB_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "gdb", "gdb_trace.py")

def extract_functions_and_params(source_file):
    """
    Načte zdrojový soubor a najde všechny definice funkcí + jejich parametry.
    """
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
    """
    Vytvoří nový soubor `generated_main.c`, který volá zvolenou funkci.
    Používá makro, aby se předešlo duplikaci `main()`.
    """
    with open(GENERATED_MAIN, "w") as f:
        f.write('#include <stdio.h>\n#include <stdlib.h>\n')
        f.write('#define MAIN_DEFINED\n')  # Zabrání překladu původního main()
        f.write('#include "test_program.c"\n\n')

        f.write("int main(int argc, char *argv[]) {\n")
        f.write("    if (argc < %d) {\n" % (len(params) + 1))
        f.write(f'        printf("Použití: %s {" ".join(["<param>" for _ in params])}\\n", argv[0]);\n')
        f.write("        return 1;\n    }\n")

        # Převedeme vstupní parametry
        converted_params = []
        for i, param in enumerate(params):
            param_type = param.split()[0]  # Např. `int`, `float`, `char*`
            if "int" in param_type:
                converted_params.append(f"atoi(argv[{i + 1}])")
            elif "float" in param_type or "double" in param_type:
                converted_params.append(f"atof(argv[{i + 1}])")
            else:
                converted_params.append(f"argv[{i + 1}]")  # Předpokládáme `char*`

        f.write(f'    printf("[INFO] Spouštím test funkce: {target_function}\\n");\n')
        f.write(f"    {target_function}({', '.join(converted_params)});\n")
        f.write("    return 0;\n}\n")

def run_gdb_trace():
    """Spustí program v GDB a zachytí instrukce do souboru."""
    gdb_cmd = [
        "gdb", "-q", "-ex", f"source {GDB_SCRIPT}",
        "-ex", f"starti",
        "-ex", f"trace-asm {TRACE_FILE}",
        "--args", BINARY_FILE, "10", "5"  # Testovací parametry, lze upravit
    ]
    print(f"🐛 Spouštím GDB: {' '.join(gdb_cmd)}")
    subprocess.run(gdb_cmd)

"""
def generate_main(target_function, params):
   
    Vytvoří nový soubor `generated_main.c`, který volá zvolenou funkci.
    
    with open(GENERATED_MAIN, "w") as f:
        f.write('#include <stdio.h>\n#include <stdlib.h>\n#include "test_program.c"\n\n')
        f.write("int main(int argc, char *argv[]) {\n")
        f.write("    if (argc < %d) {\n" % (len(params) + 1))
        f.write(f'        printf("Použití: %s {" ".join(["<param>" for _ in params])}\\n", argv[0]);\n')
        f.write("        return 1;\n    }\n")

        # Převedeme vstupní parametry
        converted_params = []
        for i, param in enumerate(params):
            param_type = param.split()[0]  # Např. `int`, `float`, `char*`
            if "int" in param_type:
                converted_params.append(f"atoi(argv[{i + 1}])")
            elif "float" in param_type or "double" in param_type:
                converted_params.append(f"atof(argv[{i + 1}])")
            else:
                converted_params.append(f"argv[{i + 1}]")  # Předpokládáme `char*`

        f.write(f'    printf("[INFO] Spouštím test funkce: {target_function}\\n");\n')
        f.write(f"    {target_function}({', '.join(converted_params)});\n")
        f.write("    return 0;\n}\n")
"""
        
def compile():
    """
    Přeloží `generated_main.c` a spustí program.
    """
    compile_cmd = ["gcc", "-g", "-o", BINARY_FILE, GENERATED_MAIN]
    print(f"🔨 Kompiluji: {' '.join(compile_cmd)}")
    subprocess.run(compile_cmd, check=True)

    #print("🚀 Spouštěj program...")
    #subprocess.run([BINARY_FILE] + ["10", "5"])  # Testovací vstupy

def cleanup():
    """
    Smaže vygenerovaný soubor `generated_main.c`.
    """
    if os.path.exists(GENERATED_MAIN):
        os.remove(GENERATED_MAIN)
        print("🧹 Smazán `generated_main.c`")

if __name__ == "__main__":
    functions = extract_functions_and_params(SRC_FILE)
    if not functions:
        print("❌ Nenalezeny žádné funkce v souboru.")
        exit(1)

    print("🔍 Nalezené funkce:")
    for func, params in functions.items():
        print(f" - {func}({', '.join(params)})")

    target_function = input("🔹 Zadej jméno funkce k testování: ")
    
    if target_function not in functions:
        print("❌ Neplatná funkce.")
        exit(1)

    generate_main(target_function, functions[target_function])
    compile()
    run_gdb_trace()
    cleanup()
