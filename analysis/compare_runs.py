import os
import json
from collections import defaultdict

# Konstanta pro složku s JSON soubory
default_analysis_folder = os.path.join(os.path.dirname(__file__), "..", "logs", "compute", "analysis")
output_file = os.path.join(default_analysis_folder, "comparison_report.txt")

def load_json_files(folder_path):
    """Načte všechny JSON soubory ve složce a vrátí seznam jejich dat."""
    data = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "r") as f:
                content = json.load(f)
                content["file_name"] = file_name  # Přidáme název souboru
                data.append(content)
    return data

def analyze_instruction_counts(data):
    """Analyzuje počet instrukcí pro jednotlivé běhy."""
    instruction_stats = []
    
    for entry in data:
        total_instructions = sum(entry["instructions"].values())
        instruction_stats.append({
            "params": entry.get("params", "N/A"),
            "total_instructions": total_instructions
        })
    
    instruction_stats.sort(key=lambda x: x["total_instructions"])
    return instruction_stats

def find_most_executed_lines(data):
    """Najde nejčastěji vykonávané řádky kódu napříč běhy."""
    line_counts = defaultdict(int)
    
    for entry in data:
        for line, count in entry["instructions"].items():
            line_counts[line] += count
    
    sorted_lines = sorted(line_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_lines[:5]  # Vrátíme top 5 nejčastějších řádků

def detect_crashes(data):
    """Zjistí, které běhy vedly k pádu programu."""
    crashes = []
    
    for entry in data:
        if entry.get("crash_detected"):
            crashes.append({
                "params": entry.get("params", "N/A"),
                "last_executed_line": entry.get("crash_last_executed_line", "N/A")
            })
    
    return crashes

def generate_report(data, output_file):
    """Vytvoří srovnávací report a uloží ho do souboru."""
    instruction_stats = analyze_instruction_counts(data)
    most_executed_lines = find_most_executed_lines(data)
    crashes = detect_crashes(data)

    report_lines = []
    report_lines.append("Srovnávací report")
    report_lines.append("-" * 40)
    
    # Počet instrukcí
    report_lines.append("\nPočet instrukcí (min - max):")
    for entry in instruction_stats:
        report_lines.append(f"  - {entry['params']}: {entry['total_instructions']} instrukcí")

    # Nejčastěji vykonávané řádky
    report_lines.append("\nNejčastěji vykonávané řádky:")
    for line, count in most_executed_lines:
        report_lines.append(f"  - {line} → {count}×")

    # Pády programu
    if crashes:
        report_lines.append("\nPády programu:")
        for crash in crashes:
            report_lines.append(f"  - Parametry: {crash['params']} → Poslední řádek: {crash['last_executed_line']}")
    else:
        report_lines.append("\nŽádné pády programu nebyly detekovány.")

    # Uložení reportu do souboru
    with open(output_file, "w") as f:
        f.write("\n".join(report_lines))
    
    print(f"[INFO] Report uložen do {output_file}")

def compare_runs(folder_path):
    """Porovná běhy funkcí na základě JSON souborů v dané složce."""
    data = load_json_files(folder_path)
    if not data:
        print(f"[ERROR] Nebyly nalezeny žádné JSON soubory ve složce {folder_path}")
        return
    
    output_file = os.path.join(folder_path, "comparison_report.txt")
    generate_report(data, output_file)

def main():
    """Hlavní funkce pro spouštění skriptu samostatně."""
    print(f"[INFO] Spouštím porovnání pro složku: {default_analysis_folder}")
    compare_runs(default_analysis_folder)

if __name__ == "__main__":
    main()
