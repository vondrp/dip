"""
Modul analyzer poskytuje pomocné analytické funkce pro zpracování logů a dalších dat.
Slouží jako obecná knihovna pro analýzu dat v projektu.
"""

import os
import json

def load_log_file(log_path):
    """Načte logovací soubor a vrátí jeho obsah jako seznam řádků."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Logovací soubor {log_path} neexistuje.")
    
    with open(log_path, "r", encoding="utf-8") as file:
        return file.readlines()

def parse_json_log(log_path):
    """Načte JSON log a vrátí ho jako Python slovník."""
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"JSON log {log_path} neexistuje.")
    
    with open(log_path, "r", encoding="utf-8") as file:
        return json.load(file)

def extract_function_calls(log_lines):
    """Extrahuje seznam volání funkcí z logovacího souboru."""
    function_calls = []
    for line in log_lines:
        if "CALL" in line:
            function_calls.append(line.strip())
    return function_calls
