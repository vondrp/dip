import os
import re
import collections
import subprocess
import json

TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "traceT.log")
BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "test_program.elf")  
SOURCE_FILE = os.path.join(os.path.dirname(__file__), "..", "src", "test_program.c")  

# Seznam funkcí, které nás zajímají
ALLOWED_FUNCTIONS = {"compute"}

#  Filtr pro systémové knihovny (abychom se zaměřili jen na uživatelský kód)
#SYSTEM_LIBRARIES = {"__libc_start_main", "_dl_", "pthread_", "atexit", "exit"}


def get_text_base_from_log(trace_file):
    """
    Načte runtime adresu TEXT_BASE z trace.log
    """
    with open(trace_file, "r") as f:
        for line in f:
            match = re.match(r"TEXT_BASE\s+(0x[0-9a-fA-F]+)", line)
            if match:
                text_base = int(match.group(1), 16)
                print(f"[INFO] Nalezen TEXT_BASE: {hex(text_base)}")
                return text_base

    print("[ERROR] TEXT_BASE nebyl nalezen v logu.")
    return None


def get_text_section_start(binary_path):
    """
    Získá statickou adresu .text sekce v binárce
    """
    try:
        readelf_output = subprocess.run(["readelf", "-S", binary_path], capture_output=True, text=True).stdout
        for line in readelf_output.split("\n"):
            if ".text" in line:
                static_start = int(line.split()[3], 16)
                print(f"[INFO] Statická adresa .text sekce: {hex(static_start)}")
                return static_start
    except Exception as e:
        print(f"[ERROR] Chyba při získávání statické adresy .text: {e}")

    return None


def get_source_line(binary_path, addr, text_base, static_text_start):
    """
    Přepočítá runtime adresu na statickou a mapuje ji na zdrojový kód pomocí `addr2line`
    """
    try:
        runtime_addr = int(addr, 16)
        real_addr = runtime_addr - text_base + static_text_start  

        print(f"[DEBUG] Přepočítaná adresa {addr} -> {hex(real_addr)}")

        # Ověříme, zda real_addr nezačíná v rámci instrukce (musí být zarovnáno na 4B nebo 16B)
        if real_addr % 4 != 0:
            real_addr -= real_addr % 4  # Zaokrouhlíme dolů na 4B zarovnání

        result = subprocess.run(["addr2line", "-e", binary_path, hex(real_addr)], stdout=subprocess.PIPE, text=True)
        line = result.stdout.strip()
        print(f"[DEBUG] addr2line výstup: {line}")

        if "??" in line:
            return None
        return line
    except Exception as e:
        print(f"[ERROR] Chyba addr2line: {e}")
        return None

def get_source_line(binary_path, addr, text_base, static_text_start):
    """
    Přepočítá runtime adresu na statickou a mapuje ji na zdrojový kód pomocí `addr2line`
    """
    try:
        # Ověříme, že proměnné jsou správně načtené
        if isinstance(addr, str):
            addr = int(addr, 16)  # Převod adresy z hex stringu na číslo
        if isinstance(text_base, str):
            text_base = int(text_base, 16)

        # Použijeme fixní offset mezi runtime a statickými adresami
        offset = text_base - static_text_start
        real_addr = addr - offset  # Přepočet dynamické adresy na statickou

        print(f"[DEBUG] Přepočítaná adresa {hex(addr)} -> {hex(real_addr)} (offset: {hex(offset)})")

        # Zaokrouhlení dolů na 4B zarovnání
        real_addr &= ~0x3

        # Spustíme addr2line pro získání čísla řádku
        result = subprocess.run(["addr2line", "-e", binary_path, hex(real_addr)], stdout=subprocess.PIPE, text=True)
        line = result.stdout.strip()
        print(f"[DEBUG] addr2line výstup: {line}")

        if "??" in line:
            return None  # Nepodařilo se namapovat adresu
        return line
    except Exception as e:
        print(f"[ERROR] Chyba addr2line: {e}")
        return None


def parse_trace(file_path, text_base, static_text_start):
    """
    Načte trace.log, extrahuje instrukce a mapuje je na řádky zdrojového kódu.
    """
    source_line_counts = collections.defaultdict(int)

    with open(file_path, "r") as f:
        for line in f:
            match = re.match(r"(\w+),\s+(0x[0-9a-fA-F]+):\s+(\w+)", line)
            if match:
                function_name, address, instruction = match.groups()

                if function_name not in ALLOWED_FUNCTIONS:
                    continue  

                source_line = get_source_line(BINARY_FILE, address, text_base, static_text_start)
                if source_line:
                    source_line_counts[source_line] += 1  
                else:
                    print(f"[WARNING] Nepodařilo se namapovat adresu {address}")

    return source_line_counts


def save_json(source_line_counts):
    """
    Uloží výsledky do JSON souboru.
    """
    output_file = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions.json")
    json_data = {"source_file": SOURCE_FILE, "instructions": source_line_counts}

    with open(output_file, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"[INFO] Výsledky uloženy do {output_file}")


if __name__ == "__main__":
    print("[INFO] Spouštím analýzu trace logu")

    text_base = get_text_base_from_log(TRACE_FILE)
    static_text_start = get_text_section_start(BINARY_FILE)

    if text_base is None or static_text_start is None:
        print("[ERROR] Nepodařilo se získat potřebné adresy. Analýza nebude přesná.")
    else:
        print(f"[INFO] Text Base (runtime): {hex(text_base)}, Static .text start: {hex(static_text_start)}")

    source_line_counts = parse_trace(TRACE_FILE, text_base, static_text_start)
    save_json(source_line_counts)

    print("[INFO] Analýza dokončena!")
