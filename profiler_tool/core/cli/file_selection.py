import os
import subprocess
from config import log_info, log_error


def get_directory_from_user(current_directory):
    """Zobrazí aktuální adresář a umožní uživateli změnit ho."""
    if current_directory == '.':
        current_directory = os.path.abspath(current_directory)

    log_info(f"Aktuální adresář: {current_directory}")
    choice = input("Chceš změnit adresář? (y/n): ").strip().lower()
    
    if choice == 'y':
        while True:
            new_directory = input(f"Zadej nový adresář (aktuální je {current_directory}): ").strip()
            if os.path.isdir(new_directory):
                return new_directory
            else:
                log_error(f"{new_directory} není platný adresář.")
                retry_choice = input(f"Chceš zadat jiný adresář, nebo zůstat v {current_directory}? (zadat/zůstat): ").strip().lower()
                if retry_choice == 'zůstat':
                    return current_directory
                elif retry_choice != 'zadat':
                    log_error("Neplatná volba, zůstáváme ve stávajícím adresáři.")
                    return current_directory
    return current_directory

def fzf_select_files(extension, directory="."):
    """Vybere pomocí fzf jeden nebo více souborů s danou příponou v daném adresáři."""
    directory = get_directory_from_user(directory)  
    try:
        command = f"find {directory} -type f -name '*{extension}' | fzf -m"
        file_paths = subprocess.check_output(command, shell=True).decode().strip().split("\n")
        return [f for f in file_paths if os.path.exists(f)]
    except subprocess.CalledProcessError:
        log_error("fzf nebyl úspěšně spuštěn nebo nenalezl žádné soubory. Přepínám na manuální zadání.")
        file_paths = input(f"Zadej cesty k {extension} souborům (oddělené mezerou): ").strip().split()
        return [f for f in file_paths if os.path.exists(f)]

def fzf_select_file(extension, directory="."):
    """Vybere pomocí fzf jeden soubor s danou příponou v daném adresáři."""
    directory = get_directory_from_user(directory)  
    try:
        command = f"find {directory} -type f -name '*{extension}' | fzf"
        file_path = subprocess.check_output(command, shell=True).decode().strip()
        return file_path if file_path and os.path.exists(file_path) else None
    except subprocess.CalledProcessError:
        log_error("fzf nebyl úspěšně spuštěn nebo nenalezl žádný soubor. Přepínám na manuální zadání.")
        file_path = input(f"Zadej cestu k {extension} souboru: ").strip()
        if not os.path.exists(file_path):
            log_error(f"Soubor {file_path} neexistuje.")
            return None
        return file_path

def fzf_select_directory(base_dir):
    """Vybere pomocí fzf složku v daném adresáři."""
    base_dir = get_directory_from_user(base_dir)  
    try:
        command = f"find {base_dir} -type d | fzf"
        directory = subprocess.check_output(command, shell=True).decode().strip()
        return directory if directory and os.path.exists(directory) else None
    except subprocess.CalledProcessError:
        log_error("fzf nebyl úspěšně spuštěn nebo nenalezl žádnou složku. Přepínám na manuální zadání.")
        directory = input(f"Zadej cestu ke složce v {base_dir}: ").strip()
        return directory if os.path.exists(directory) else None
