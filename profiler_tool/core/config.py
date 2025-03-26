import os

# Základní adresář projektu
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Adresář pro buildy KLEE
KLEE_BUILD_DIR = os.path.join(BASE_DIR, "build", "klee")

# Cesta k KLEE bitcode testovacímu souboru
KLEE_BITCODE_FILE = os.path.join(KLEE_BUILD_DIR, "klee_program.bc")

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
GENERATED_MAIN_KLEE = os.path.join(os.path.dirname(__file__), "..", "..", "src", "generated_main_klee.c")

