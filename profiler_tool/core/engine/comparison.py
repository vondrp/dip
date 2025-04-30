import os
import json
from collections import defaultdict
from config import ANALYSIS_DIR
from config import log_info, log_warning, log_error


# Konstanta pro složku s JSON soubory
default_analysis_folder = os.path.join(os.path.dirname(__file__), "..", "logs", "compute", "analysis")
output_file = os.path.join(default_analysis_folder, "comparison_report.txt")

def load_json_files(file_paths):
    """Načte všechny JSON soubory a vrátí seznam jejich dat."""
    data = []
    
    for file_path in file_paths:
        if not file_path.endswith(".json"):
            continue
        with open(file_path, "r") as f:
            try:
                content = json.load(f)
                content["file_name"] = os.path.basename(file_path)  # Přidáme název souboru
                data.append(content)
            except json.JSONDecodeError:
                log_error(f"Chyba při čtení {file_path}, soubor není validní JSON.")

    return data

def analyze_instruction_counts(data):
    """Analyzuje počet instrukcí pro jednotlivé běhy."""
    instruction_stats = []
    
    for entry in data:
        total_instructions = sum(entry["instructions"].values())
        instruction_stats.append({
            "params": entry.get("params", "N/A"),
            "platform": entry.get("platform", "unknown"),
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

def find_most_executed_lines_by_platform_and_params(data):
    """Najde nejčastěji vykonávané řádky pro každou kombinaci platformy a parametrů."""
    grouped_line_counts = defaultdict(lambda: defaultdict(int))

    for entry in data:
        platform = entry.get("platform", "unknown")
        params = entry.get("params", "N/A")
        key = (platform, params)

        for line, count in entry["instructions"].items():
            grouped_line_counts[key][line] += count

    # Vrátíme top 5 pro každou kombinaci
    result = {}
    for key, line_counts in grouped_line_counts.items():
        sorted_lines = sorted(line_counts.items(), key=lambda x: x[1], reverse=True)
        result[key] = sorted_lines[:5]

    return result

def detect_crashes(data):
    """Zjistí, které běhy vedly k pádu programu."""
    crashes = []

    for entry in data:
        if entry.get("crash_detected"):
            crashes.append({
                "platform": entry.get("platform", "unknown"),
                "params": entry.get("params", "N/A"),
                "last_executed_line": entry.get("crash_last_executed_line", "N/A")
            })

    return crashes

def generate_report(data, output_file):
    """Vytvoří srovnávací report a uloží ho do souboru."""
    instruction_stats = analyze_instruction_counts(data)
    most_executed_lines = find_most_executed_lines(data)
    lines_by_platform_and_params = find_most_executed_lines_by_platform_and_params(data)
    crashes = detect_crashes(data)

    report_lines = []
    report_lines.append("Srovnávací report")
    report_lines.append("-" * 40)
    
    # Počet instrukcí
    report_lines.append("\nPočet instrukcí (min - max):")
    for entry in instruction_stats:
        label = f"{entry['platform']} | {entry['params']}"
        report_lines.append(f"  - {label}: {entry['total_instructions']} instrukcí")

    # Nejčastěji vykonávané řádky
    report_lines.append("\nNejčastěji vykonávané řádky (celkově):")
    for line, count in most_executed_lines:
        report_lines.append(f"  - {line} → {count}×")

    # Nejčastěji vykonávané řádky podle platformy a parametrů
    report_lines.append("\nNejčastěji vykonávané řádky podle platformy a parametrů:")
    for (platform, params), lines in lines_by_platform_and_params.items():
        report_lines.append(f"- {platform} | param: {params}")
        for line, count in lines:
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
    
    log_info(f"Report uložen do {output_file}")


def compare_runs(folder=None, files=None):
    """Porovná běhy funkcí na základě JSON souborů ve složce nebo vybraných souborů."""
    if folder:
        json_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".json")]
    elif files:
        json_files = files
    else:
        log_warning("Nebyly nalezeny žádné JSON soubory k porovnání.")
        return

    data = load_json_files(json_files)
    if not data:
        log_warning(f"Nebyly nalezeny žádné platné JSON soubory")
        return
    
    output_file = os.path.join(folder if folder else ANALYSIS_DIR, "comparison_report.txt")
    generate_report(data, output_file)

def main():
    """Hlavní funkce pro spouštění skriptu samostatně."""
    log_info(f"Spouštím porovnání pro složku: {default_analysis_folder}")
    compare_runs(default_analysis_folder)

if __name__ == "__main__":
    main()
