# comparison.py
from core.engine.comparison import compare_runs
from .file_selection import fzf_select_files, fzf_select_directory

def compare_json_runs(folder=None, files=None):
    """Porovná běhy na základě JSON souborů."""
    if not folder:
        folder = fzf_select_directory()

    if not files:
        files = fzf_select_files(".json")

    compare_runs(folder=folder, files=files)
