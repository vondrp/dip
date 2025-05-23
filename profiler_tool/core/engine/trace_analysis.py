import os
import re
import collections
import subprocess
import json
from config import get_call_instructions_regex, get_return_instructions_regex
from config import log_info, log_debug, log_warning, log_error
from config import ACTIVE_ARCHITECTURE

"""
Tento skript poskytuje funkce pro analýzu trace souborů, které obsahují instrukce generované během traceování vykonávaných funkcí v binárních souborech.
Skript slouží k analýze vykonaných instrukcí, extrahování informací o voláních funkcí, počítání instrukcí pro jednotlivé řádky kódu a detekci případných havárií aplikace během traceování.

Hlavní funkce skriptu:
- Získání statických a runtime adres funkcí.
- Mapování runtime adresy na statickou adresu a následné mapování na konkrétní řádek zdrojového kódu.
- Počítání instrukcí v rámci sledovaných funkcí.
- Ukládání výsledků analýzy do JSON formátu.
"""

def get_static_function_address(binary_path, function_name):
    """
    Získá statickou adresu funkce z binárního souboru pomocí příkazu `nm -n`.

    :param binary_path: Cesta k binárnímu souboru.
    :param function_name: Název funkce, pro kterou chceme zjistit statickou adresu.
    :return: Statická adresa funkce v hexadecimálním formátu (int), nebo None, pokud není nalezena.
    """

    try:
        output = subprocess.run(["nm", "-n", binary_path], capture_output=True, text=True).stdout
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) == 3 and parts[1] == "T" and parts[2] == function_name:
                return int(parts[0], 16)
    except Exception as e:
        log_error(f"Chyba při získávání statické adresy `{function_name}`: {e}")
    return None

def get_runtime_function_address(trace_file, function_name):
    """
    Najde runtime adresu funkce v trace log souboru.

    :param trace_file: Cesta k trace log souboru.
    :param function_name: Název funkce, pro kterou hledáme runtime adresu.
    :return: Runtime adresa funkce v hexadecimálním formátu (int), nebo None, pokud není nalezena.
    """

    call_instruction_regex = get_call_instructions_regex()
    log_debug(f"call instructions: {call_instruction_regex}")
    try:
        with open(trace_file, "r") as f:
            for line in f:
                # Upravíme regulární výraz pro RISC-V: ignorujeme 'ra' a získáme adresu
                if ACTIVE_ARCHITECTURE == "riscv":                    
                    match = re.search(rf"({call_instruction_regex})\s+([a-zA-Z0-9,]+)?\s*(0x[0-9a-fA-F]+)\s+<{re.escape(function_name)}>", line)
                else:
                    match = re.search(rf"({call_instruction_regex})\s+(0x[0-9a-fA-F]+)\s+<{re.escape(function_name)}>", line)

                if match:
                    log_debug(f" match runtime nalezen {match}")
                    # V případě RISC-V, pokud máme ra, tak ho ignorujeme
                    if ACTIVE_ARCHITECTURE == "riscv":
                        addr = match.group(3)
                    else:
                        addr = match.group(2)

                    log_debug(f"hexadecimální adresa: {addr}")                    
                    runtime_addr = int(addr, 16)
                    log_debug(f"Runtime adresa `{function_name}`: {hex(runtime_addr)}")
                    return runtime_addr
    except FileNotFoundError:
        log_error(f"Soubor `{trace_file}` nebyl nalezen.")
    except Exception as e:
        log_error(f"Chyba při čtení souboru: {e}")
    return None

def get_source_line(binary_path, addr, runtime_addr_target, static_addr_target):
    """
    Přepočítá runtime adresu na statickou a mapuje ji na zdrojový kód pomocí příkazu `addr2line`.

    :param binary_path: Cesta k binárnímu souboru.
    :param addr: Adresa (v hexadecimálním formátu), kterou chceme přeložit.
    :param runtime_addr_target: Runtime adresa cílové funkce.
    :param static_addr_target: Statická adresa cílové funkce.
    :return: Řádek zdrojového kódu odpovídající adrese, nebo None, pokud není možné najít.
    """
    try:
        if isinstance(addr, str):
            addr = int(addr, 16)
        
        offset = runtime_addr_target - static_addr_target
        real_addr = addr - offset
        result = subprocess.run(["addr2line", "-e", binary_path, hex(real_addr)], stdout=subprocess.PIPE, text=True)
        line = result.stdout.strip()
        
        if "??" in line:
            return None
        return line
    except Exception as e:
        log_error(f"Chyba addr2line: {e}")
    return None

def normalize_discriminators(source_line_counts):
    """
    Sjednotí instrukce na řádcích s a bez 'discriminator', odstraní redundantní varianty.

    :param source_line_counts: Počty instrukcí pro jednotlivé řádky kódu.
    :return: Normalizované počty instrukcí bez 'discriminator'.
    """
    normalized_counts = collections.defaultdict(int)

    for line, count in source_line_counts.items():
        base_line = re.sub(r" \(discriminator \d+\)", "", line) 
        normalized_counts[base_line] += count

    return normalized_counts

def count_function_instructions(file, called_function, original_function):
    """
    Počítá instrukce volané funkce až do návratu zpět do `original_function`, sleduje zanoření funkcí.

    :param file: Otevřený soubor trace logu.
    :param called_function: Název právě volané funkce.
    :param original_function: Název původní funkce, do které se má počítání instrukcí vrátit.
    :return: Počet instrukcí vykonaných mezi voláním `called_function` a návratem do `original_function`.
    """
    instruction_count = 0
    recursion_depth = 1 if called_function == original_function else 0

    log_debug(f"Spuštěno `count_function_instructions`, sledujeme návrat do `{original_function}` rec depth {recursion_depth}")
    return_instructions_regex = get_return_instructions_regex()

    for line in file:
        if line.startswith(f"{original_function},"):
            if recursion_depth > 0:
                if re.search(return_instructions_regex, line):
                    recursion_depth -= 1
                    log_debug(f"Zmenšení úrovně zanoření provedeno na řáce: {line}")
                    if recursion_depth == 0:
                        log_debug(f"Návrat do `{original_function}`, zastavujeme počítání")
                        return instruction_count, line
                
                instruction_count += 1
                continue
            else:
                log_debug(f"Návrat do `{original_function}`, zastavujeme počítání")
                return instruction_count, line    

        if line.startswith("[CALL]"):
            match = re.match(r"\[CALL\] (\w+) -> <(\w+)>", line)
            if match:
                called_function = match.group(2)
                if called_function == original_function:
                    recursion_depth += 1
                continue

        if re.match(r"(\w+),\s+(0x[0-9a-fA-F]+):\s+(\w+)", line):
            instruction_count += 1

    log_warning(f"[WARNING] Funkce `{original_function}` se při zanoření do jiné funkce nevrátila, vracíme {instruction_count} instrukcí")
    return instruction_count, None


def parse_trace(file_path, runtime_addr_target, static_addr_target, binary_file, function_name):
    """
    Analyzuje trace log soubor a extrahuje instrukce pro funkci `function_name`.

    :param file_path: Cesta k trace log souboru.
    :param runtime_addr_target: Runtime adresa cílové funkce.
    :param static_addr_target: Statická adresa cílové funkce.
    :param binary_file: Cesta k binárnímu souboru.
    :param function_name: Název analyzované funkce.
    :return: Slovník počtů instrukcí pro jednotlivé řádky, informaci o detekované havárii a poslední vykonaný řádek.
    """
    source_line_counts = collections.defaultdict(int)
    inside_target_function = False
    last_executed_line = None
    crash_detected = False
    
    call_instructions_regex = get_call_instructions_regex()
    return_instructions_regex = get_return_instructions_regex()

    with open(file_path, "r") as f:
        line = f.readline()
        while line:
            if re.search(rf"({call_instructions_regex})\s+(?:[a-zA-Z0-9_]+\s*,\s*)?{hex(runtime_addr_target)}\s+<{re.escape(function_name)}>", line) and not inside_target_function:
                log_debug(f"v parse_trace zaznamenáno volání funkce")
            #if re.search(rf"({call_instructions_regex})\s+{hex(runtime_addr_target)} <{function_name}>", line) and inside_target_function != True:
                inside_target_function = True
                line = f.readline()
                continue
            
            if inside_target_function:
                match = re.match(r"\w+,\s+(0x[0-9a-fA-F]+):\s+(\w+)", line)
                if match:
                    if re.match(r"\bmain\b,", line):
                        inside_target_function = False
                        break

                    address, instruction = match.groups()
                    last_executed_line = get_source_line(binary_file, address, runtime_addr_target, static_addr_target)
                    
                    if last_executed_line:
                        source_line_counts[last_executed_line] += 1
                    
                    # volani funkci uvnitr testovane funkce
                    #call_match = re.match(rf".*({call_instructions_regex})\s+(0x[0-9a-fA-F]+)\s+<(.*?)>", line)
                    call_match = re.match(rf".*({call_instructions_regex})\s+(?:[a-zA-Z0-9_]+\s*,\s*)?(0x[0-9a-fA-F]+)\s+<(.+?)>", line)
                    if call_match:
                        called_function = call_match.group(3)
                        log_debug(f"Detekováno volání `{called_function}` na řádku `{last_executed_line}`")
                        
                        call_instruction_count, last_read_line = count_function_instructions(f, called_function, function_name)    
                    
                        if last_executed_line:
                            log_debug(f"Počet instrukcí pro `{called_function}`: {call_instruction_count}")
                            source_line_counts[last_executed_line] += call_instruction_count
                        
                        if last_read_line:
                            line = last_read_line
                            continue
                        
                #if re.search(rf"\bret\b", line):
                #if re.search(return_instructions_regex, line):
                #    inside_target_function = False
                #    break
            
            line = f.readline()

    source_line_counts = normalize_discriminators(source_line_counts)

    if inside_target_function == True:
         crash_detected = inside_target_function 
         log_warning(f"Detekováno náhlé ukončení programu! Poslední řádek: `{last_executed_line}`")

    log_info(f"Celkem instrukcí ve `{function_name}`: {sum(source_line_counts.values())}")
    return source_line_counts, crash_detected, last_executed_line


def save_json(source_line_counts, crash_detected, crash_last_executed_line, json_output_path, function_name, params, source_file):
    """
    Uloží výsledky analýzy do JSON souboru.

    :param source_line_counts: Počty instrukcí pro jednotlivé řádky.
    :param crash_detected: Detekována havárie programu.
    :param crash_last_executed_line: Poslední vykonaný řádek před havárií.
    :param json_output_path: Cesta k výstupnímu JSON souboru.
    :param function_name: Název analyzované funkce.
    :param params: Parametry testované funkce.
    :param source_file: Cesta ke zdrojovému souboru.
    """

    # Celkový počet provedených instrukcí
    total_instructions = sum(source_line_counts.values())
    
    json_data = {
        "source_file": source_file,
        "platform": ACTIVE_ARCHITECTURE,
        "function": function_name,
        "params": params,
        "total_instructions": total_instructions,
        "instructions": source_line_counts
    }
    
    # Přidáme info o havárii, pokud byla detekována
    if crash_detected:
        json_data["crash_detected"] = True
        json_data["crash_last_executed_line"] = crash_last_executed_line

    with open(json_output_path, "w") as f:
        json.dump(json_data, f, indent=4)
    
    log_info(f"Výsledky uloženy do `{json_output_path}`")

def analyze_traces_in_folder(trace_folder, output_folder, binary_file, function_name, source_file):
    """Analyzuje všechny trace logy ve složce `trace_folder` a uloží JSON výstupy do `output_folder`."""
    
    if not os.path.exists(trace_folder):
        log_error(f"Složka `{trace_folder}` neexistuje, analýza ukončena!")
        return

    os.makedirs(output_folder, exist_ok=True)  # Vytvoří výstupní složku, pokud neexistuje

    trace_files = [f for f in os.listdir(trace_folder) if f.endswith(".log")]

    if not trace_files:
        log_warning(f"Nebyly nalezeny žádné trace logy ve složce `{trace_folder}`!")
        return

    log_info(f"Nalezeno {len(trace_files)} trace logů k analýze v `{trace_folder}`.")

    # Získáme statickou a runtime adresu pro testovanou funkci
    static_addr_target = get_static_function_address(binary_file, function_name)
    
    if static_addr_target is None:
        log_error(f"Nepodařilo se získat statickou adresu pro funkci `{function_name}`, analýza přeskočena!")
        return

    for trace_file in trace_files:
        trace_path = os.path.join(trace_folder, trace_file)

        # Najdeme parametry z názvu souboru (trace_<function_name>_<params>.log)
        match = re.match(rf"trace_{re.escape(function_name)}_(.*)\.log", trace_file)
        if not match:
            log_warning(f"Soubor `{trace_file}` neodpovídá formátu `trace_{function_name}_<parametry>.log`, přeskočeno.")
            continue

        params_str = match.group(1)
        json_output_path = os.path.join(output_folder, f"instructions_{function_name}_{params_str}.json")

        params_str = params_str.replace("_", " ")
        log_info(f"Analyzuji `{trace_file}` (parametry: {params_str})")

        runtime_addr_target = get_runtime_function_address(trace_path, function_name)

        if runtime_addr_target is None:
            log_error(f"Nepodařilo se získat runtime adresu pro `{trace_file}`, přeskočeno.")
            continue

        source_line_counts, crash_detected, last_executed_line = parse_trace(trace_path, runtime_addr_target, static_addr_target, binary_file, function_name)

        # Uložení do JSON pomocí save_json
        save_json(source_line_counts, crash_detected, last_executed_line, json_output_path, function_name, params_str, source_file)

    log_info(f"Analýza všech trace logů ve složce `{trace_folder}` dokončena!")



def analyze_trace(trace_file, binary_file, target_function, output_json, params):
    """
    Analyzuje jeden konkrétní trace soubor a uloží výsledky do JSON souboru.
    
    :param trace_file: Cesta k trace souboru.
    :param binary_file: Cesta k binárnímu souboru.
    :param target_function: Název analyzované funkce.
    :param output_json: Cesta k výstupnímu JSON souboru.
    :param params: Parametry s nimiž byl trace_file vytvořen
    """
    static_addr_target = get_static_function_address(binary_file, target_function)
    if static_addr_target is None:
        log_error(f"Nepodařilo se získat statickou adresu pro funkci `{target_function}`!")
        return

    runtime_addr_target = get_runtime_function_address(trace_file, target_function)
    if runtime_addr_target is None:
        log_error(f"Nepodařilo se získat runtime adresu pro `{trace_file}`, přeskočeno.")
        return

    #register_file = + trace_file + ".regs"
    #registers = load_registers_from_file(register_file)
    source_line_counts, crash_detected, last_executed_line = parse_trace(
        trace_file, runtime_addr_target, static_addr_target, binary_file, target_function
    )

    # Extrahování parametrů z názvu souboru (trace_<function_name>_<params>.log)
    match = re.match(rf"trace_{re.escape(target_function)}_(.*)\.log", os.path.basename(trace_file))

    # Získání source_file z prvního záznamu v source_line_counts
    first_line_key = next(iter(source_line_counts))
    source_file = first_line_key.split(":")[0]

    save_json(source_line_counts, crash_detected, last_executed_line, output_json, target_function, params, source_file)
    log_info(f"Analýza `{trace_file}` dokončena a výsledky uloženy do `{output_json}`.")    


def load_registers_from_file(regs_file_path):
    """
    Načte registry ze souboru ve formátu generovaném GDB.
    
    Vrací:
        dict[str, int] - mapa názvů registrů na jejich hodnoty (v hex).
    """
    registers = {}

    with open(regs_file_path, "r") as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) >= 2:
                reg_name = parts[0]
                reg_value_hex = parts[1]
                try:
                    registers[reg_name] = int(reg_value_hex, 16)
                except ValueError:
                    pass  # pokud by tam náhodou bylo něco divného (nemělo by)
    
    return registers
