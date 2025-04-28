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


def generate_main_header_includes(header_filename, bm=False):
    """
    Vytvoří hlavičkový soubor pro `main` funkci.

    Tato funkce generuje základní hlavičky a potřebné definice pro soubor `main.c`.
    Podle parametru `bm` se rozhoduje, zda se bude generovat kód pro bare-metal nebo pro OS.

    Args:
    - header_filename (str): Název hlavičkového souboru, který bude zahrnut.
    - bm (bool): Určuje, zda generovat kód pro bare-metal (`True`) nebo pro OS (`False`).

    Returns:
    - str: Generovaný kód zahrnující potřebné hlavičky.
    """
    includes = ""
    if not bm:
        includes += '#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n'
    includes += '#define MAIN_DEFINED\n'
    includes += f'#include "{header_filename}"\n\n'
    return includes


def generate_param_code(params, bm=False):
    """
    Generuje kód pro parametry funkce v `main` funkci.

    Tato funkce vytváří kód pro parametry funkce na základě typu a názvu parametru. Podle parametru `bm` 
    se generují různé hodnoty pro bare-metal a OS verzi. Pro bare-metal jsou parametry hardkodované, 
    zatímco pro OS jsou parametry čteny z argumentů příkazové řádky.

    Args:
    - params (list): Seznam parametrů, kterými funkce přijímá.
    - bm (bool): Určuje, zda generovat kód pro bare-metal (`True`) nebo pro OS (`False`).

    Returns:
    - tuple: Generovaný kód pro parametry a seznam konvertovaných parametrů pro funkci.
    """
    code = ""
    converted_params = []
    params = [p.strip() for p in params if p.strip()]
    has_void = len(params) == 1 and params[0] == "void"

    for i, param in enumerate(params):
        if param == "void":
            continue

        param_type = param.split()[0]
        param_name = param.split()[1] if len(param.split()) > 1 else f"param{i+1}"
        param_name_clean = param_name[1:] if "*" in param_name else param_name

        if bm:
            # Bare-metal: hardcoded hodnoty
            if "*" in param_name:
                if any(t in param_type for t in ("int", "unsigned")):
                    code += f"{param_type} {param_name_clean}[] = {{1, 2, 3, 4}};\n"
                elif any(t in param_type for t in ("float", "double")):
                    code += f"{param_type} {param_name_clean}[] = {{1.1, 2.2, 3.3, 4.4}};\n"
                elif "char" in param_type and "*" in param_type:
                    code += f"{param_type} {param_name_clean}[] = {{\"foo\", \"bar\", \"baz\"}};\n"
                else:
                    code += f"{param_type} {param_name_clean}[] = {{0}};\n"
                converted_params.append(param_name_clean)
            else:
                if "int" in param_type:
                    code += f"{param_type} {param_name} = {i + 1};\n"
                elif "unsigned" in param_type:
                    code += f"{param_type} {param_name} = {i + 10}u;\n"
                elif "float" in param_type:
                    code += f"{param_type} {param_name} = {float(i + 1):.1f}f;\n"
                elif "double" in param_type:
                    code += f"{param_type} {param_name} = {float(i + 1):.2f};\n"
                elif "char" in param_type and "*" in param_type:
                    code += f'{param_type} {param_name} = "test_string";\n'
                elif "char" in param_type:
                    code += f"{param_type} {param_name} = 'a';\n"
                else:
                    code += f"{param_type} {param_name} = 0;\n"
                converted_params.append(param_name)
        else:
            # OS: čte z argv
            if "*" in param_name:
                num_var = f"{param_name_clean}"
                count_var = f"count_{i+1}"
                token_var = f"token_{i+1}"
                idx_var = f"i_{i+1}"
                tmp_var = f"tmp_{i+1}"
                arg_idx = f"argv[{i+1}]"

                if any(t in param_type for t in ("int", "float", "double", "unsigned")):
                    code += f"    int {count_var} = 1;\n"
                    code += f"    char *{tmp_var} = {arg_idx};\n"
                    code += f"    for (int i = 0; {tmp_var}[i]; ++i) if ({tmp_var}[i] == ' ') {count_var}++;\n"
                    code += f"    {param_type} {num_var}[{count_var}];\n"
                    code += f"    int {idx_var} = 0;\n"
                    code += f"    char *{token_var} = strtok({arg_idx}, \" \");\n"
                    code += f"    while ({token_var} != NULL && {idx_var} < {count_var}) {{\n"
                    convert_func = "atoi" if "int" in param_type or "unsigned" in param_type else "atof"
                    code += f"        {num_var}[{idx_var}++] = {convert_func}({token_var});\n"
                    code += f"        {token_var} = strtok(NULL, \" \");\n"
                    code += f"    }}\n"
                    converted_params.append(num_var)
                
                elif "char" in param_type:
                    converted_params.append(arg_idx)

                else:
                    code += f"    {param_type} {param_name}[argc - 1];\n"
                    code += f"    for (int i = 0; i < argc - 1; ++i) {{\n"
                    code += f"        {param_name}[i] = argv[i + 1];\n"
                    code += f"    }}\n"
                    converted_params.append(param_name)
            else:
                if "int" in param_type:
                    converted_params.append(f"atoi(argv[{i+1}])")
                elif any(t in param_type for t in ("float", "double")):
                    converted_params.append(f"atof(argv[{i+1}])")
                elif "char" in param_type:
                    converted_params.append(f"argv[{i+1}][0]")
                elif "unsigned" in param_type:
                    converted_params.append(f"strtoul(argv[{i + 1}], NULL, 10)")    
                else:
                    converted_params.append(f"argv[{i+1}]")

    return code, ", ".join(converted_params)


def generate_main(target_function, params, header_file):
    """
    Vytvoří `generated_main.c` pro volání vybrané funkce s argumenty z příkazové řádky.

    Tento soubor obsahuje funkci `main`, která přijímá argumenty z příkazové řádky,
    konvertuje je do odpovídajících typů a volá cílovou funkci s těmito parametry.

    Args:
    - target_function (str): Název testované funkce.
    - params (list): Seznam parametrů funkce.
    - header_file (str): Cesta k hlavičkovému souboru obsahujícímu deklaraci funkce.

    Returns:
    - None: Funkce generuje soubor `generated_main.c`.
    """
    generated_main_path = os.path.join(os.path.dirname(header_file), "generated_main.c")
    set_generated_main_path(generated_main_path)
    header_filename = os.path.basename(header_file)
    has_void = len(params) == 1 and params[0] == "void"

    with open(generated_main_path, "w") as f:
        f.write(generate_main_header_includes(header_filename, bm=False))
        f.write("int main(int argc, char *argv[]) {\n")
        if not has_void:
            f.write(f"    if (argc < {len(params) + 1}) {{\n")
            f.write(f'        printf("Použití: %s {" ".join(["<param>" for _ in params])}\\n", argv[0]);\n')
            f.write("        return 1;\n    }\n")
        code, args = generate_param_code(params, bm=False)
        f.write(code)
        f.write(f'    printf("Spouštím test funkce: {target_function}\\n");\n')
        f.write(f"    {target_function}({args});\n")
        f.write("    return 0;\n}\n")



def generate_main_bm(target_function, params, header_file):
    """
    Vytvoří `generated_main.c` pro volání vybrané funkce v bare-metal režimu.

    Tento soubor obsahuje funkci `main`, která nevyžaduje argumenty z příkazové řádky,
    ale všechny hodnoty jsou hardkodované pro bare-metal prostředí.

    Args:
    - target_function (str): Název testované funkce.
    - params (list): Seznam parametrů funkce.
    - header_file (str): Cesta k hlavičkovému souboru obsahujícímu deklaraci funkce.

    Returns:
    - None: Funkce generuje soubor `generated_main.c`.
    """
    generated_main_path = os.path.join(os.path.dirname(header_file), "generated_main.c")
    set_generated_main_path(generated_main_path)
    header_filename = os.path.basename(header_file)

    with open(generated_main_path, "w") as f:
        f.write(generate_main_header_includes(header_filename, bm=True))
        f.write("void main() {\n")
        code, args = generate_param_code(params, bm=True)
        f.write(code)
        f.write(f"    {target_function}({args});\n")
        f.write("    while (1); // Nekonečná smyčka\n")
        f.write("}\n")

def generate_main_template(target_function, params, header_file):
    """
    Vytvoří šablonový soubor `generated_main.c`, který si uživatel může upravit ručně.

    Args:
    - target_function (str): Název cílové funkce.
    - params (list): Seznam parametrů funkce.
    - header_file (str): Cesta k hlavičkovému souboru.
    """
    generated_main_path = os.path.join(os.path.dirname(header_file), "generated_main.c")
    set_generated_main_path(generated_main_path)
    header_filename = os.path.basename(header_file)

    with open(generated_main_path, "w") as f:
        f.write(generate_main_header_includes(header_filename, bm=False))
        f.write("int main(int argc, char *argv[]) {\n")
        f.write("    // TODO: Přidejte vlastní kód pro načítání parametrů.\n")
        f.write(f"    // Příklad volání funkce:\n")
        params_list = ", ".join(["/* param */" for _ in params]) if params else ""
        f.write(f"    {target_function}({params_list});\n")
        f.write("    return 0;\n}\n")
