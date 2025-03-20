import json
import os

# Cesty k souborům
INSTRUCTIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions_compute_10_0.json")

def load_instruction_data():
    """ Načte JSON soubor s instrukcemi """
    if not os.path.exists(INSTRUCTIONS_FILE):
        print("[ERROR] Soubor instructions.json neexistuje.")
        return None
    
    with open(INSTRUCTIONS_FILE, "r") as f:
        return json.load(f)

def normalize_path(path):
    """ Normalizuje cestu pro porovnání """
    return os.path.abspath(os.path.realpath(path))

def annotate_source_code():
    """ Přidá komentáře s počtem instrukcí do zdrojového kódu a detekuje pád programu """
    data = load_instruction_data()
    if not data:
        return
    
    source_file = normalize_path(data["source_file"])
    instructions = data["instructions"]
    crash_detected = data.get("crash_detected", False)
    crash_last_executed_line = data.get("crash_last_executed_line", None)

    if not os.path.exists(source_file):
        print(f"[ERROR] Soubor {source_file} neexistuje.")
        return

    print(f"[INFO] Otevírám soubor: {source_file}")

    # Převod instrukcí na formát {řádek: počet instrukcí}
    instruction_map = {}
    for key, value in instructions.items():
        try:
            # Extrahujeme číslo řádku
            line_number = key.split(":")[-1]
            instruction_map[line_number] = value
        except IndexError:
            print(f"[WARNING] Chybný formát klíče: {key}")

    print(f"[DEBUG] Normalizovaná čísla řádků v instructions.json: {list(instruction_map.keys())}")

    with open(source_file, "r") as f:
        lines = f.readlines()

    updated_lines = []
    for i, line in enumerate(lines):
        line_number = str(i + 1)  # JSON klíče jsou jako řetězce

        # Přidání počtu instrukcí
        comment_parts = []
        if line_number in instruction_map:
            instruction_count = instruction_map[line_number]
            comment_parts.append(f"Celkem: {instruction_count} instrukcí")

        # Přidání varování o crashi
        if crash_detected and crash_last_executed_line and crash_last_executed_line.endswith(f":{line_number}"):
            comment_parts.append("⚠ CRASH DETECTED! ⚠")

        # Pokud existuje něco k přidání, přidáme komentář
        if comment_parts:
            comment = "  // " + " | ".join(comment_parts)
            if "//" in line:
                print(f"[WARNING] Řádek {line_number} už obsahuje komentář, přeskočeno.")
            else:
                print(f"[INFO] Přidávám anotaci na řádek {line_number}: {comment}")
                line = line.rstrip() + comment + "\n"

        updated_lines.append(line)

    with open(source_file, "w") as f:
        f.writelines(updated_lines)

    print(f"[INFO] Anotace přidány do {source_file}")

if __name__ == "__main__":
    annotate_source_code()
