# logger.py
import sys

LOG_LEVELS = ["debug", "info", "warning", "error"]
_current_level = "debug"

def set_log_level(level):
    global _current_level
    if level.lower() in LOG_LEVELS:
        _current_level = level.lower()

def _should_log(level):
    return LOG_LEVELS.index(level) >= LOG_LEVELS.index(_current_level)

def log_debug(msg):    _should_log("debug")   and print(f"[DEBUG] {msg}", file=sys.stderr)
def log_info(msg):     _should_log("info")    and print(f"[INFO] {msg}", file=sys.stderr)
def log_warning(msg):  _should_log("warning") and print(f"[WARNING] {msg}", file=sys.stderr)
def log_error(msg):    _should_log("error")   and print(f"[ERROR] {msg}", file=sys.stderr)
