import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

BUILD_DIR = os.path.join(BASE_DIR, "build")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TRACE_DIR = os.path.join(OUTPUT_DIR, "traces")
KLEE_OUTPUT = os.path.join(OUTPUT_DIR, "klee-output")
KLEE_RESULTS = os.path.join(OUTPUT_DIR, "klee-results")
ANALYSIS_DIR = os.path.join(OUTPUT_DIR, "analysis")

DEFAULT_GENERATED_MAIN = os.path.join(BASE_DIR, "tests", "src", "generated_main.c")
DEFAULT_GENERATED_MAIN_KLEE = os.path.join(BASE_DIR, "tests", "src", "generated_main_klee.c")

GDB_SCRIPT = os.path.join(BASE_DIR, "core", "gdb", "gdb_trace.py")
GDB_SCRIPT_ARM = os.path.join(BASE_DIR, "core", "gdb", "gdb_trace_arm.py")
GDB_SCRIPT_ARM_BM = os.path.join(BASE_DIR, "core", "gdb", "gdb_trace_bare_arm.py")
