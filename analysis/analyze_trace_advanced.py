import os
import re
import collections
import subprocess
import json

TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trace.log")
BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "test_binary")
SOURCE_FILE = os.path.join(os.path.dirname(__file__), "..", "src", "test_program.c")

def get_static_function_address(binary_path, function_name):
    """Získá statickou adresu funkce z binárky pomocí `nm -n`."""
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
    """Najde runtime adresu funkce v zadaném log souboru."""
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
        return None
    except Exception as e:
        print(f"[ERROR] Při čtení souboru došlo k chybě: {e}")
        return None

    print(f"[ERROR] Runtime adresa `{function_name}` nebyla nalezena v logu.")
    return None

def get_text_base_from_log(trace_file):
    """Načte runtime adresu TEXT_BASE z `trace.log`."""
    with open(trace_file, "r") as f:
        for line in f:
            match = re.match(r"TEXT_BASE\s+(0x[0-9a-fA-F]+)", line)
            if match:
                text_base = int(match.group(1), 16)
                print(f"[INFO] Nalezen TEXT_BASE: {hex(text_base)}")
                return text_base

    print("[ERROR] TEXT_BASE nebyl nalezen v logu.")
    return None

def get_source_line(binary_path, addr, runtime_addr_compute, static_addr_compute):
    """Přepočítá runtime adresu na statickou a mapuje ji na zdrojový kód pomocí `addr2line`."""
    try:
        if isinstance(addr, str):
            addr = int(addr, 16)

        offset = runtime_addr_compute - static_addr_compute
        real_addr = addr - offset

        result = subprocess.run(["addr2line", "-e", binary_path, hex(real_addr)], stdout=subprocess.PIPE, text=True)
        line = result.stdout.strip()

        if "??" in line:
            return None
        return line
    except Exception as e:
        print(f"[ERROR] Chyba addr2line: {e}")
        return None

def parse_trace(file_path, runtime_addr_compute, static_addr_compute):
    """Analyzuje trace.log a extrahuje instrukce jen pro funkci `compute`."""
    source_line_counts = collections.defaultdict(int)
    call_instruction_count = 0
    inside_compute = False

    with open(file_path, "r") as f:
        for line in f:
            # Zachytáváme vstup do funkce `compute`
            if f"call   {hex(runtime_addr_compute)} <compute>" in line:
                inside_compute = True
                continue

            if inside_compute:
                match = re.match(r"\w+,\s+(0x[0-9a-fA-F]+):\s+(\w+)", line)
                if match:
                    address, instruction = match.groups()
                    source_line = get_source_line(BINARY_FILE, address, runtime_addr_compute, static_addr_compute)

                    if source_line:
                        source_line_counts[source_line] += 1
                    else:
                        print(f"[WARNING] Nepodařilo se namapovat adresu {address}")

                    # Detekce volání jiné funkce
                    if "call" in instruction:
                        call_instruction_count += 1

                # Pokud narazíme na `ret`, znamená to konec funkce `compute`
                if "ret" in line:
                    inside_compute = False

    print(f"[INFO] Celkem instrukcí ve `compute`: {sum(source_line_counts.values())}")
    print(f"[INFO] Instrukce spotřebované voláním jiných funkcí: {call_instruction_count}")

    return source_line_counts

def save_json(source_line_counts):
    """Uloží výsledky do JSON souboru."""
    output_file = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions.json")
    json_data = {"source_file": SOURCE_FILE, "instructions": source_line_counts}

    with open(output_file, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"[INFO] Výsledky uloženy do {output_file}")

if __name__ == "__main__":
    print("[INFO] Spouštím analýzu trace logu")

    text_base = get_text_base_from_log(TRACE_FILE)
    static_addr_compute = get_static_function_address(BINARY_FILE, "compute")
    runtime_addr_compute = get_runtime_function_address(TRACE_FILE, "compute")

    print(f"[INFO] Statická adresa `compute`: {hex(static_addr_compute) if static_addr_compute else 'Nenalezena'}")
    print(f"[INFO] Runtime adresa `compute`: {hex(runtime_addr_compute) if runtime_addr_compute else 'Nenalezena'}")

    if static_addr_compute is None or runtime_addr_compute is None:
        print("[ERROR] Nepodařilo se získat adresy funkce `compute`!")
        exit(1)

    print("[SUCCESS] Úspěšně nalezeny obě adresy!")

    source_line_counts = parse_trace(TRACE_FILE, runtime_addr_compute, static_addr_compute)
    save_json(source_line_counts)

    print("[INFO] Analýza dokončena!")
