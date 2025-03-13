import os
import re
import collections
import subprocess

TRACE_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "trace.log")
BINARY_FILE = os.path.join(os.path.dirname(__file__), "..", "build", "program_x86")  # Přizpůsob podle názvu binárky

# 📌 Seznam funkcí, které nás zajímají (ZMĚŇ podle svého programu!)
ALLOWED_FUNCTIONS = {"main", "compute", "my_exit"}

# 📌 Pokud chceš sledovat všechny funkce, nastav False
USE_FILTER = True  # Pouze zvolené funkce

def get_source_line(binary_path, addr):
    """
    Použije `addr2line` pro získání odpovídajícího řádku zdrojového kódu.
    """
    try:
        result = subprocess.run(["addr2line", "-e", binary_path, hex(int(addr, 16))], stdout=subprocess.PIPE, text=True)
        line = result.stdout.strip()
        if "??" in line:
            return None
        return line
    except:
        return None

def parse_trace(file_path):
    """
    Načte trace.log, extrahuje instrukce a jejich četnost + mapování na řádky kódu.
    """
    instruction_counts = collections.Counter()
    function_counts = collections.Counter()
    instruction_sequences = collections.defaultdict(list)
    source_line_counts = collections.defaultdict(int)  # Nově: Počet instrukcí na řádku kódu ve filtrovaných funkcích

    with open(file_path, "r") as f:
        prev_instr = None
        for line in f:
            match = re.match(r"(\w+),\s+(0x[0-9a-fA-F]+):\s+(\w+)", line)
            if match:
                function_name, address, instruction = match.groups()

                # 📌 Instrukce evidujeme vždy
                instruction_counts[instruction] += 1
                function_counts[function_name] += 1

                # 📌 Mapování na zdrojový kód jen ve filtrovaných funkcích
                if not USE_FILTER or function_name in ALLOWED_FUNCTIONS:
                    source_line = get_source_line(BINARY_FILE, address)
                    if source_line:
                        source_line_counts[source_line] += 1

                if prev_instr == instruction:
                    instruction_sequences[instruction].append((address, function_name))

                prev_instr = instruction

    return instruction_counts, function_counts, instruction_sequences, source_line_counts

def generate_report(instr_counts, func_counts, instr_sequences, source_line_counts):
    """
    Vytvoří report o analýze kódu.
    """
    print("\n📊 **Analýza běhu programu**")

    filter_status = "Pouze vlastní funkce" if USE_FILTER else "Všechny funkce"
    print(f"\n🔍 **Použitý filtr:** {filter_status}")

    print("\n🔹 **TOP 10 nejčastějších instrukcí:**")
    for instr, count in instr_counts.most_common(10):
        print(f"{instr}: {count}")

    print("\n🔹 **TOP 10 funkcí s nejvíce instrukcemi:**")
    for func, count in func_counts.most_common(10):
        print(f"{func}: {count}")

    print("\n⚠️ **Možná úzká místa (dlouhé smyčky stejné instrukce):**")
    for instr, occurrences in instr_sequences.items():
        if len(occurrences) > 5:  # Heuristická detekce smyček
            unique_functions = set(func for _, func in occurrences)
            print(f"{instr} opakuje {len(occurrences)}x ve funkcích: {', '.join(unique_functions)}")
            print(f"   Adresy: {', '.join(addr for addr, _ in occurrences[:5])}...")

    print("\n📌 **Počet instrukcí vykonaných na jednotlivých řádcích kódu (pouze ve filtrovaných funkcích):**")
    sorted_lines = sorted(source_line_counts.items(), key=lambda x: x[1], reverse=True)
    for line, count in sorted_lines[:10]:
        print(f"{line}: {count} instrukcí")

if __name__ == "__main__":
    print("📊 **Spuštění analýzy trace logu...**")

    instr_counts, func_counts, instr_sequences, source_line_counts = parse_trace(TRACE_FILE)
    
    generate_report(instr_counts, func_counts, instr_sequences, source_line_counts)

    print("\n✅ **Analýza dokončena!**")
