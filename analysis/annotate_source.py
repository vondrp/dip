import json
import os

# Cesty k souborům
INSTRUCTIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "instructions.json")

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
    """ Přidá komentáře s počtem instrukcí do zdrojového kódu """
    data = load_instruction_data()
    if not data:
        return
    
    source_file = normalize_path(data["source_file"])
    instructions = {normalize_path(k.split(":")[0]) + ":" + k.split(":")[1]: v for k, v in data["instructions"].items()}

    if not os.path.exists(source_file):
        print(f"[ERROR] Soubor {source_file} neexistuje.")
        return

    print(f"[INFO] Otevírám soubor: {source_file}")

    with open(source_file, "r") as f:
        lines = f.readlines()

    updated_lines = []
    for i, line in enumerate(lines):
        line_number = i + 1
        key = f"{source_file}:{line_number}"

        if key in instructions:
            count = instructions[key]
            comment = f"  // {count} instrukcí"

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
