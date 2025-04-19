import os
from config import DEFAULT_GENERATED_MAIN, DEFAULT_GENERATED_MAIN_KLEE
from config import log_debug

# Skript pro generování hlavních souborů (`generated_main.c`, `generated_main_klee.c`, `generated_main_arm.c`)
# pro různé typy kompilací a analýz (KLEE, ARM bare-metal, x86/ARM).

# Veřejná proměnná pro cestu k generovanému souboru
_generated_main_path = DEFAULT_GENERATED_MAIN

# Getter pro cestu k generated_main.c
def get_generated_main_path():
    """Vrátí cestu k souboru `generated_main.c`."""
    return _generated_main_path

# Setter pro cestu k generated_main.c (pokud bude potřeba)
def set_generated_main_path(new_path):
    """Nastaví cestu k souboru `generated_main.c`."""
    global _generated_main_path
    _generated_main_path = new_path


# Veřejná proměnná pro cestu k generated_main_klee.c
_generated_main_klee_path = DEFAULT_GENERATED_MAIN_KLEE

# Getter pro cestu k generated_main_klee.c
def get_generated_main_klee_path():
    """Vrátí cestu k souboru `generated_main_klee.c`."""
    return _generated_main_klee_path

# Setter pro cestu k generated_main_klee.c (pokud bude potřeba)
def set_generated_main_klee_path(new_path):
    """Nastaví cestu k souboru `generated_main_klee.c`."""
    global _generated_main_klee_path
    _generated_main_klee_path = new_path


def generate_main_klee(target_function, params_with_const, header_file):
    """
    Vytvoří `generated_main_klee.c` pro analýzu s KLEE – s podporou pro pole, řetězce a konstanty.
    Parametry mohou být ve formátu "typ jméno" nebo "typ jméno=hodnota" pro konstanty.
    """
    """
    Vytvoří `generated_main_klee.c` pro analýzu s KLEE.

    Tento soubor bude obsahovat kód, který umožňuje spustit funkci s 
    symbolickými parametry, které budou použity v analýze s nástrojem KLEE.
    
    Args:
    - target_function (str): Název testované funkce.
    - params_with_const (list): Seznam parametrů funkce. Některé z nich mají zadanou hodnotu
    - header_file (str): Cesta k hlavičkovému souboru obsahujícímu deklaraci funkce.
    """
    import os

    generated_main_klee_path = os.path.join(os.path.dirname(header_file), "generated_main_klee.c")
    set_generated_main_klee_path(generated_main_klee_path)

    header_filename = os.path.basename(header_file)
    params_with_const = [p.strip() for p in params_with_const if p.strip()]
    has_void = len(params_with_const) == 1 and params_with_const[0] == "void"

    with open(generated_main_klee_path, "w") as f:
        f.write('#include <klee/klee.h>\n')
        f.write('#include <stdio.h>\n')
        f.write('#include <string.h>\n\n')
        f.write(f'#include "{header_filename}"\n\n')
        f.write('// Velikost symbolických polí/řetězců\n')
        f.write('#define SIZE 10\n\n')
        f.write("int main() {\n")

        if has_void:
            f.write(f'    printf("Spouštím test funkce: {target_function}\\n");\n')
            f.write(f'    {target_function}();\n')
            f.write("    return 0;\n}\n")
            return

        symbolic_params = []

        for i, param in enumerate(params_with_const):
            if "=" in param:
                decl_part, const_val = param.split("=", 1)
                decl_parts = decl_part.strip().split()
                param_type = " ".join(decl_parts[:-1])
                param_name_raw = decl_parts[-1] 

                var_name = f"param_{i}"
                const_val = const_val.strip().strip('"').strip("'")

                is_pointer = "*" in param_type or param_name_raw.strip().startswith("*")
                clean_type = param_type.replace("*", "").strip()

                log_debug(f"is_pointer: {is_pointer} clean_type: {clean_type}  raw: {param_name_raw}")
                if is_pointer and clean_type == "char":
                    # char * = "něco"
                    f.write(f'    {param_type} *{var_name} = "{const_val}";\n')
                    symbolic_params.append(var_name)

                elif is_pointer and clean_type in ["int", "float", "double"]:
                    # Např. int * = pole hodnot
                    elements = const_val.split()
                    array_init = ", ".join(elements)
                    array_size = len(elements)
                    f.write(f'    {clean_type} tmp_arr_{i}[{array_size}]] = {{{array_init}}};\n')
                    f.write(f'    {clean_type} *{var_name} = tmp_arr_{i};\n')
                    symbolic_params.append(var_name)
                
                elif is_pointer:
                    # Ukazatel na jiný typ – zatím nepodporováno
                    log_warn(f"Přeskakuji konstantu pro nepodporovaný ukazatelový typ: {param_type}")
                    continue
                else:
                    # Např. int x = 5;
                    f.write(f'    {param_type} {var_name} = {const_val};\n')
                    symbolic_params.append(var_name)
            else:
                # Symbolický parametr
                parts = param.strip().split()
                param_type = " ".join(parts[:-1])
                
                param_name = parts[1]

                log_debug(f" parts {param} parts {param_type} param name: {param_name}")
                is_pointer = "*" in param_type or "*" in param_name

                log_debug(f"is pointer {is_pointer}")
                #is_pointer = "*" in param_type or "*" in parts[-1]
                clean_type = param_type.replace("*", "").strip()
                var_name = f"param_{i}"

                if clean_type == "char" and is_pointer:
                    f.write(f"    char {var_name}[SIZE];\n")
                    f.write(f"    klee_make_symbolic({var_name}, sizeof({var_name}), \"{var_name}\");\n")
                    f.write(f"    {var_name}[SIZE - 1] = '\\0';\n")

                elif is_pointer and clean_type in ["int", "float", "double"]:
                    f.write(f"    {clean_type} {var_name}[SIZE];\n")
                    f.write(f"    klee_make_symbolic({var_name}, sizeof({var_name}), \"{var_name}\");\n")
                elif clean_type in ["int", "float", "double", "char", "unsigned"]:
                    f.write(f"    {clean_type} {var_name};\n")
                    f.write(f"    klee_make_symbolic(&{var_name}, sizeof({var_name}), \"{var_name}\");\n")
                else:
                    f.write(f"    {clean_type} {var_name};\n")
                    f.write(f"    klee_make_symbolic(&{var_name}, sizeof({var_name}), \"{var_name}\");\n")

                symbolic_params.append(var_name)

        f.write(f'\n    printf("Spouštím test funkce: {target_function}\\n");\n')
        f.write(f"    {target_function}({', '.join(symbolic_params)});\n")
        f.write("    return 0;\n}\n")

    log_debug("Vygenerován `generated_main_klee.c` se správnou podporou pro pole, řetězce i konstanty.")


def generate_main(target_function, params, header_file):
    """
    Vytvoří `generated_main.c` pro volání vybrané funkce s argumenty z příkazové řádky.

    Tento soubor obsahuje funkci `main`, která přijímá argumenty z příkazové řádky,
    konvertuje je do odpovídajících typů a volá cílovou funkci s těmito parametry.
    
    Args:
    - target_function (str): Název testované funkce.
    - params (list): Seznam parametrů funkce.
    - header_file (str): Cesta k hlavičkovému souboru obsahujícímu deklaraci funkce.
    """
    
    generated_main_path = os.path.join(os.path.dirname(header_file), "generated_main.c")
    header_filename = os.path.basename(header_file)
    set_generated_main_path(generated_main_path)
    
    # získej seznam parametrů
    params = [p.strip() for p in params if p.strip()]
    has_void = len(params) == 1 and params[0] == "void"


    with open(generated_main_path, "w") as f:
        f.write('#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n')
        f.write('#define MAIN_DEFINED\n')
        f.write(f'#include "{header_filename}"\n\n')

        f.write("int main(int argc, char *argv[]) {\n")

        if not has_void:
            f.write("    if (argc < %d) {\n" % (len(params) + 1))
            f.write(f'        printf("Použití: %s {" ".join(["<param>" for _ in params])}\\n", argv[0]);\n')
            f.write("        return 1;\n    }\n")

        converted_params = []
        for i, param in enumerate(params):
            if param.strip() == "void":
                continue

            param_type = param.split()[0]  # Typ parametru
            param_name = param.split()[1] if len(param.split()) > 1 else None  # Název parametru

            param_name_clean = param_name[1:]  # Název parametru bez prvního znaku (ukazetele *)

            # Zpracování pro ukazatel
            if "*" in param_name:  # Pokud jde o ukazatel (např. int* array)

                if any(t in param_type for t in ("int", "float", "double")):
                    f.write(f'    // Zpracování pole z jednoho argumentu\n')
                    f.write(f'    int count_{i + 1} = 1;\n')
                    f.write(f'    char *tmp_{i + 1} = argv[{i + 1}];\n')
                    f.write(f'    for (int i = 0; tmp_{i + 1}[i]; ++i) {{\n')
                    f.write(f'        if (tmp_{i + 1}[i] == \' \') count_{i + 1}++;\n')
                    f.write(f'    }}\n')
                    f.write(f'    {param_type} {param_name_clean}[count_{i + 1}];\n')
                    f.write(f'    int i_{i + 1} = 0;\n')
                    f.write(f'    char *token_{i + 1} = strtok(argv[{i + 1}], " ");\n')
                    f.write(f'    while (token_{i + 1} != NULL && i_{i + 1} < count_{i + 1}) {{\n')
                    if "int" in param_type:
                        f.write(f'          {param_name_clean}[i_{i + 1}++] = atoi(token_{i + 1}); \n')
                    else:
                        f.write(f'          {param_name_clean}[i_{i + 1}++] = atof(token_{i + 1}); \n')
                    f.write(f'          token_{i + 1} = strtok(NULL, " "); \n')
                    f.write(f'    }}\n')
                    converted_params.append(param_name_clean)
                elif "char" in param_type:  # Zpracování pro char*
                    # Pro char* použijeme celý řetězec (argv[i+1])
                    converted_params.append(f"argv[{i + 1}]")
                else:
                    f.write(f'    {param_type} {param_name}[argc - 1];\n')
                    f.write(f'    for (int i = 0; i < argc - 1; ++i) {{\n')
                    f.write(f'        {param_name}[i] = argv[i + 1];\n')  # Pro ostatní typy
                    f.write(f'    }}\n')
                    converted_params.append(param_name)

            # Zpracování pro ostatní hodnoty (ne ukazatel)
            else:  # Neukazatel, pouze hodnoty
                if "int" in param_type:
                    converted_params.append(f"atoi(argv[{i + 1}])")
                elif "float" in param_type:
                    converted_params.append(f"atof(argv[{i + 1}])")
                elif "char" in param_type:
                    converted_params.append(f"argv[{i + 1}]")
                elif "unsigned" in param_type:
                    converted_params.append(f"strtoul(argv[{i + 1}], NULL, 10)")    
                elif "void" in param_type:
                    f.write(f'    // Parametr typu void není podporován.\n')
                else:
                    converted_params.append(f"argv[{i + 1}]")

        f.write(f'    printf("Spouštím test funkce: {target_function}\\n");\n')
        f.write(f"    {target_function}({', '.join(converted_params)});\n")
        f.write("    return 0;\n}\n")
    
    log_debug(f"Vygenerován `generated_main.c`.")

def generate_main_arm(target_function, params):
    """
    Vytvoří `generated_main_arm.c` přizpůsobený pro bare-metal ARM.

    Tento soubor je určen pro generování kódu pro bare-metal ARM aplikace.
    Obsahuje simulovanou funkci pro výstup přes UART a generování parametrů
    s pevnými hodnotami pro testování.

    Args:
    - target_function (str): Název testované funkce.
    - params (list): Seznam parametrů funkce.
    """
    
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

    log_debug(f"Vygenerován `generated_main_arm.c` pro ARM bare-metal.")
    return generate_main_file 
