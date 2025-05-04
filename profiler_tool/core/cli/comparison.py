from core.engine.comparison import compare_runs
from core.cli.file_selection import fzf_select_files, fzf_select_directory
from config import ANALYSIS_DIR
from config import log_info, log_error


def compare_json_runs(folder=None, files=None):
    """
    Spustí porovnání běhů na základě výstupních JSON souborů.

    Tato funkce slouží jako CLI vstupní bod pro porovnání dat z více běhů. 
    Umožňuje buď předat cestu ke složce nebo konkrétním souborům přímo (např. při skriptovaném volání),
    nebo při nevyplnění obou variant spustí interaktivní výběr přes FZF.

    - Pokud není zadán `folder` ani `files`, uživatel si zvolí mezi výběrem složky nebo jednotlivých souborů.
    - Pro výběr se používají nástroje `fzf_select_directory` a `fzf_select_files`.
    - Funkce následně volá `compare_runs`, která provede analýzu a vygeneruje report.

    Parametry:
        folder (str, optional): Cesta ke složce s JSON soubory.
        files (list[str], optional): Seznam cest ke konkrétním JSON souborům.

    Návratová hodnota:
        None — Výstupem je logovaný report, případně chybová hlášení.

    Použití:
        compare_json_runs()  # spustí interaktivní výběr
        compare_json_runs(folder="/cesta/k/logum")  # zpracuje celou složku
        compare_json_runs(files=["run1.json", "run2.json"])  # zpracuje konkrétní soubory
    """
    if not files and not folder:
        log_info("\n Vyber složku s JSON soubory nebo ručně vyber soubory:")
        choice = input("[1] Vybrat složku\n[2] Vybrat konkrétní soubory\n> ")

        if choice == "1":
            folder = fzf_select_directory(ANALYSIS_DIR)
            if not folder:
                log_error("Nebyla vybrána žádná složka.")
                return
        elif choice == "2":
            files = fzf_select_files(".json", ANALYSIS_DIR)
            if not files:
                log_error("Nebyly vybrány žádné soubory.")
                return
        else:
            log_error("Neplatná volba. Ukončuji.")
            return

    if folder:
        compare_runs(folder)
    elif files:
        compare_runs(files=files)
    else:
        log_error("Nebyla vybrána žádná data pro porovnání.")
