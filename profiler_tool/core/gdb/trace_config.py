import re
import json
import os
import gdb

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "trace_config.json"))

_blacklist_patterns = []
_blacklist_regexes = []

def _load_blacklist_config():
    global _blacklist_patterns, _blacklist_regexes

    print(f"[INFO] Pokouším se načíst konfigurační soubor: {CONFIG_PATH}")

    if not os.path.exists(CONFIG_PATH):
        print(f"[WARN] Konfigurační soubor neexistuje: {CONFIG_PATH}")
        return

    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            _blacklist_patterns = config.get("function_blacklist_patterns", [])
            _blacklist_regexes = [re.compile(p) for p in _blacklist_patterns]

        print(f"[INFO] Načteno {len(_blacklist_patterns)} blacklist patternů.")
    except Exception as e:
        print(f"[ERROR] Chyba při načítání konfigurace: {e}")
        _blacklist_patterns = []
        _blacklist_regexes = []

def is_blacklisted_function(function_name: str) -> bool:
    gdb.write(f"volase is lbacklisted function")
    if not _blacklist_regexes:
        _load_blacklist_config()

    return any(regex.search(function_name) for regex in _blacklist_regexes)
