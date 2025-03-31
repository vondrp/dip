# file_selection.py
import os
import subprocess

def fzf_select_files(extension, directory="."):
    """Použije fzf k výběru jednoho nebo více souborů s danou příponou v zadaném adresáři."""
    try:
        command = f"find {directory} -type f -name '*{extension}' | fzf -m"
        file_paths = subprocess.check_output(command, shell=True).decode().strip().split("\n")
        return [f for f in file_paths if os.path.exists(f)]
    except subprocess.CalledProcessError:
        print("❌ fzf nebyl úspěšně spuštěn nebo nenalezl žádné soubory. Zkusíme manuální volbu.")
        file_paths = input(f"Zadej cesty k {extension} souborům (oddělené mezerou): ").strip().split()
        return [f for f in file_paths if os.path.exists(f)]

def fzf_select_file(extension, directory="."):
    """Použije fzf k výběru souboru s danou příponou v zadaném adresáři."""
    try:
        command = f"find {directory} -type f -name '*{extension}' | fzf"
        file_path = subprocess.check_output(command, shell=True).decode().strip()
        return file_path if file_path and os.path.exists(file_path) else None
    except subprocess.CalledProcessError:
        print("❌ fzf nebyl úspěšně spuštěn nebo nenalezl žádný soubor. Zkusíme manuální volbu.")
        file_path = input(f"Zadej cestu k {extension} souboru: ").strip()
        if not os.path.exists(file_path):
            print(f"❌ Soubor {file_path} neexistuje.")
            return None
        return file_path

def fzf_select_directory(base_dir):
    """Použije fzf k výběru složky v zadaném adresáři."""
    try:
        command = f"find {base_dir} -type d | fzf"
        directory = subprocess.check_output(command, shell=True).decode().strip()
        return directory if directory and os.path.exists(directory) else None
    except subprocess.CalledProcessError:
        print("❌ fzf nebyl úspěšně spuštěn nebo nenalezl žádnou složku. Zkusíme manuální volbu.")
        directory = input(f"Zadej cestu ke složce v {base_dir}: ").strip()
        return directory if os.path.exists(directory) else None
