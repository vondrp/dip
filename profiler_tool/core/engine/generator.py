import os

from core.config import set_generated_main_path, get_generated_main_path
from core.config import set_generated_main_klee_path, get_generated_main_klee_path



def generate_main_klee(target_function, params, header_file):

    generated_main_klee_path = os.path.join(os.path.dirname(header_file), "generated_main_klee.c")
    set_generated_main_klee_path(generated_main_klee_path)

    header_filename = os.path.basename(header_file)

    """Vytvoří `generated_main_klee.c` pro analýzu s KLEE."""
    with open(generated_main_klee_path, "w") as f:
        f.write('#include <klee/klee.h>\n')
        f.write('#include <stdio.h>\n\n')
        f.write(f'#include "{header_filename}"\n\n')

        #f.write(f'extern void {target_function}({", ".join(params)});\n\n')

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

def generate_main(target_function, params, header_file):
    """Vytvoří `generated_main.c` pro volání vybrané funkce s argumenty z příkazové řádky."""

    generated_main_path = os.path.join(os.path.dirname(header_file), "generated_main.c")
    header_filename = os.path.basename(header_file)
    set_generated_main_path(generated_main_path)

    with open(generated_main_path, "w") as f:
        f.write('#include <stdio.h>\n#include <stdlib.h>\n')
        f.write('#define MAIN_DEFINED\n')
        f.write(f'#include "{header_filename}"\n\n')

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

def generate_main_arm(target_function, params):
    """Vytvoří `generated_main_arm.c` přizpůsobený pro bare-metal ARM."""

    generate_main_file = os.path.join(os.path.dirname(__file__), "..", "src", "generated_main_arm.c")

    with open(generate_main_file , "w") as f:
        f.write('#include <stdint.h>\n')  # Použití stdint.h místo stdlib.h
        f.write('#include "arm_test_program.h"\n\n')

        # Simulovaná výstupní funkce pro bare-metal (nahradí printf)
        f.write("void arm_print(const char *msg) {\n")
        f.write('    volatile char *uart = (volatile char *)0x09000000; // UART na QEMU\n')
        f.write('    while (*msg) *uart = *(msg++);\n')
        f.write("}\n\n")

        # Hlavní funkce (nebude vracet int, protože běžně na ARM bez OS není návratová hodnota)
        f.write("void main() {\n")

        f.write(f'    arm_print("Spouštím test funkce: {target_function}\\n");\n')

        converted_params = []
        for i, param in enumerate(params):
            param_type = param.split()[0]
            var_name = f"param_{i}"

            if "int" in param_type:
                f.write(f"    int {var_name} = {i * 10 + 1};  // Testovací hodnota\n")
            elif "float" in param_type or "double" in param_type:
                f.write(f"    {param_type} {var_name} = {i * 0.5 + 1.0};\n")
            elif "char" in param_type:
                f.write(f"    char {var_name} = 'A' + {i};\n")
            else:
                f.write(f"    {param_type} {var_name};  // U neznámých typů neinicializujeme\n")

            converted_params.append(var_name)

        f.write(f"    {target_function}({', '.join(converted_params)});\n")
        f.write("    while (1); // Nekonečná smyčka (běžné u bare-metal aplikací)\n")
        f.write("}\n")

    print(f"[INFO] ✅ Vygenerován `generated_main_arm.c` pro ARM bare-metal.")
    return generate_main_file 
