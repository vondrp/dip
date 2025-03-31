from core.engine.comparison import compare_runs
from core.cli.file_selection import fzf_select_files, fzf_select_directory
from core.config import ANALYSIS_DIR

def compare_json_runs(folder=None, files=None):
    """Porovná běhy na základě JSON souborů ze složky nebo ručně vybraných souborů."""
    if not files and not folder:
        print("\n[INFO] Vyber složku s JSON soubory nebo ručně vyber soubory:")
        choice = input("[1] Vybrat složku\n[2] Vybrat konkrétní soubory\n> ")

        if choice == "1":
            folder = fzf_select_directory(ANALYSIS_DIR)
            if not folder:
                print("[ERROR] Nebyla vybrána žádná složka.")
                return
        elif choice == "2":
            files = fzf_select_files(".json", ANALYSIS_DIR)
            if not files:
                print("[ERROR] Nebyly vybrány žádné soubory.")
                return
        else:
            print("[ERROR] Neplatná volba. Ukončuji.")
            return

    if folder:
        compare_runs(folder)
    elif files:
        compare_runs(files=files)
    else:
        print("[ERROR] Nebyla vybrána žádná data pro porovnání.")
