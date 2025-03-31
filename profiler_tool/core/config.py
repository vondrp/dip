import os

# Základní adresář projektu
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Adresář pro buildy
BUILD_DIR = os.path.join(BASE_DIR, "build")

# Adresář logů
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Adresář trace
TRACE_DIR = os.path.join(LOGS_DIR, "traces")

# Adresář klee výsledků
KLEE_OUTPUT = os.path.join(LOGS_DIR, "klee-output")

# Adresář s analýzymi
ANALYSIS_DIR = os.path.join(LOGS_DIR, "analysis")

# Cesta k `ktest-tool`
KTEST_TOOL = "ktest-tool"

# Cesta ke spustitelnému souboru KLEE (změňte, pokud není v `PATH`)
KLEE_EXECUTABLE = "klee"

# Výchozí parametry pro běh KLEE
KLEE_OPTIONS = [
    "--optimize",
    "--libc=uclibc",
    "--posix-runtime",
    "--only-output-states-covering-new"
]


GENERATED_MAIN = os.path.join(os.path.dirname(__file__), "..", "..", "src", "generated_main.c")

# Veřejná proměnná pro cestu k generovanému souboru
_generated_main_path = os.path.join(os.path.dirname(__file__), "..", "..", "src", "generated_main.c")

# Getter pro cestu k generated_main.c
def get_generated_main_path():
    return _generated_main_path

# Setter pro cestu k generated_main.c (pokud bude potřeba)
def set_generated_main_path(new_path):
    global _generated_main_path
    _generated_main_path = new_path


GENERATED_MAIN_KLEE = os.path.join(os.path.dirname(__file__), "..", "..", "src", "generated_main_klee.c")

# Veřejná proměnná pro cestu k generated_main_klee.c
_generated_main_klee_path = os.path.join(os.path.dirname(__file__), "..", "..", "src", "generated_main_klee.c")

# Getter pro cestu k generated_main_klee.c
def get_generated_main_klee_path():
    return _generated_main_klee_path

# Setter pro cestu k generated_main_klee.c (pokud bude potřeba)
def set_generated_main_klee_path(new_path):
    global _generated_main_klee_path
    _generated_main_klee_path = new_path

GDB_SCRIPT = os.path.join(os.path.dirname(__file__), "gdb", "gdb_trace.py")
GDB_SCRIPT_ARM = os.path.join(os.path.dirname(__file__), "gdb", "gdb_trace_arm.py")
GDB_SCRIPT_ARM_BM = os.path.join(os.path.dirname(__file__), "gdb", "gdb_trace_bare_arm.py")

