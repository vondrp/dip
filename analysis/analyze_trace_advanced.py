import os
import re
import collections
import subprocess
import json

# Název testované funkce
TARGET_FUNCTION = "X"

# TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trace.log")
# BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "test_binary")
# OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions.json")

#TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trace_compute_42_5.log")
#BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "test_binary_compute_42_5")
#OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions_compute_42_5.json")

#TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trace_cycle_5.log")
#BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "test_binary_cycle_5")
#OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions_cycle_5.json")

#TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trace_recurse_7.log")
#BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "test_binary_recurse_7")
#OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions_recurse_7.json")

#TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trace_A_5.log")
#BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "test_binary_A_5")
#OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions_A_5.json")

TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trace_X_8.log")
BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "test_binary_X_8")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions_X_8.json")

SOURCE_FILE = os.path.join(os.path.dirname(__file__), "..", "src", "test_program.c")


def get_static_function_address(binary_path, function_name):
    """Získá statickou adresu funkce z binárního souboru pomocí `nm -n`."""
    try:
        output = subprocess.run(["nm", "-n", binary_path], capture_output=True, text=True).stdout
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) == 3 and parts[1] == "T" and parts[2] == function_name:
                return int(parts[0], 16)
    except Exception as e:
        print(f"[ERROR] Chyba při získávání statické adresy `{function_name}`: {e}")
    return None

def get_runtime_function_address(trace_file, function_name):
    """Najde runtime adresu funkce v logovacím souboru."""
    try:
        with open(trace_file, "r") as f:
            for line in f:
                match = re.search(r"call\s+(0x[0-9a-fA-F]+)\s+<" + re.escape(function_name) + ">", line)
                if match:
                    runtime_addr = int(match.group(1), 16)
                    print(f"[INFO] Runtime adresa `{function_name}`: {hex(runtime_addr)}")
                    return runtime_addr
    except FileNotFoundError:
        print(f"[ERROR] Soubor `{trace_file}` nebyl nalezen.")
    except Exception as e:
        print(f"[ERROR] Chyba při čtení souboru: {e}")
    return None

def get_source_line(binary_path, addr, runtime_addr_target, static_addr_target):
    """Přepočítá runtime adresu na statickou a mapuje ji na zdrojový kód pomocí `addr2line`."""
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
        print(f"[ERROR] Chyba addr2line: {e}")
    return None

def normalize_discriminators(source_line_counts):
    """Sjednotí instrukce na řádcích s a bez 'discriminator', odstraní redundantní varianty."""
    normalized_counts = collections.defaultdict(int)

    for line, count in source_line_counts.items():
        base_line = re.sub(r" \(discriminator \d+\)", "", line) 
        normalized_counts[base_line] += count

    return normalized_counts

def count_function_instructions(file, called_function, original_function):
    """Počítá instrukce volané funkce až do návratu zpět do `original_function`, sleduje zanoření."""
    instruction_count = 0
    recursion_depth = 1 if called_function == original_function else 0

    print(f"[INFO] Spuštěno `count_function_instructions`, sledujeme návrat do `{original_function}` rec depth {recursion_depth}")

    for line in file:
        if line.startswith(f"{original_function},"):
            if recursion_depth > 0:
                if "ret" in line:
                    recursion_depth -= 1
                    if recursion_depth == 0:
                        print(f"[DEBUG] Návrat do `{original_function}`, zastavujeme počítání")
                        return instruction_count, line
                
                instruction_count += 1
                continue
            else:
                print(f"[DEBUG] Návrat do `{original_function}`, zastavujeme počítání")
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

    print(f"[WARNING] Funkce `{original_function}` se neobjevila, vracíme {instruction_count} instrukcí")
    return instruction_count, None


def parse_trace(file_path, runtime_addr_target, static_addr_target):
    """Analyzuje logovací soubor a extrahuje instrukce pro `TARGET_FUNCTION`."""
    source_line_counts = collections.defaultdict(int)
    inside_target_function = False
    last_call_source_line = None
    
    with open(file_path, "r") as f:
        line = f.readline()
        while line:
            if f"call   {hex(runtime_addr_target)} <{TARGET_FUNCTION}>" in line and inside_target_function != True:
                inside_target_function = True
                line = f.readline()
                continue
            
            if inside_target_function:
                match = re.match(r"\w+,\s+(0x[0-9a-fA-F]+):\s+(\w+)", line)
                if match:
                    address, instruction = match.groups()
                    source_line = get_source_line(BINARY_FILE, address, runtime_addr_target, static_addr_target)
                    
                    if source_line:
                        source_line_counts[source_line] += 1
                    
                    # volani funkci uvnitr testovane funkce
                    call_match = re.match(r".*call\s+(0x[0-9a-fA-F]+)\s+<(.*?)>", line)
                    if call_match:
                        called_function = call_match.group(2)
                        last_call_source_line = source_line
                        print(f"[DEBUG] Detekováno volání `{called_function}` na řádku `{source_line}`")
                        
                        call_instruction_count, last_read_line = count_function_instructions(f, called_function, TARGET_FUNCTION)    
                    
                        if last_call_source_line:
                            print(f"[DEBUG] Počet instrukcí pro `{called_function}`: {call_instruction_count}")
                            source_line_counts[last_call_source_line] += call_instruction_count
                        
                        if last_read_line:
                            line = last_read_line
                            continue
                        
                if re.search(r"\bret\b", line):
                    inside_target_function = False
                    break
            
            line = f.readline()

    source_line_counts = normalize_discriminators(source_line_counts)
    print(f"[INFO] Celkem instrukcí ve `{TARGET_FUNCTION}`: {sum(source_line_counts.values())}")
    return source_line_counts



def save_json(source_line_counts):
    """Uloží výsledky analýzy do JSON souboru."""
    json_data = {
        "source_file": SOURCE_FILE,
        "instructions": source_line_counts
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(json_data, f, indent=4)
    
    print(f"[INFO] Výsledky uloženy do {OUTPUT_FILE}")

def main():
    """Hlavní funkce pro spuštění analýzy."""
    print(f"[INFO] Spouštím analýzu trace logu pro funkci `{TARGET_FUNCTION}`")
    static_addr_target = get_static_function_address(BINARY_FILE, TARGET_FUNCTION)
    runtime_addr_target = get_runtime_function_address(TRACE_FILE, TARGET_FUNCTION)
    
    if static_addr_target is None or runtime_addr_target is None:
        print(f"[ERROR] Nepodařilo se získat adresy funkce `{TARGET_FUNCTION}`!")
        exit(1)
    
    print(f"[INFO] Statická adresa `{TARGET_FUNCTION}`: {hex(static_addr_target)}")
    print(f"[INFO] Runtime adresa `{TARGET_FUNCTION}`: {hex(runtime_addr_target)}")
    
    source_line_counts = parse_trace(TRACE_FILE, runtime_addr_target, static_addr_target)
    save_json(source_line_counts)
    print(f"[INFO] Analýza `{TARGET_FUNCTION}` dokončena!")

if __name__ == "__main__":
    main()
