KTEST_TOOL = "ktest-tool"
KLEE_EXECUTABLE = "klee"

KLEE_OPTIONS = [
    "--optimize",
    "--libc=uclibc",
    "--posix-runtime",
    "--only-output-states-covering-new",
    "--max-time=2min",
    "--max-memory=4096",
    "--max-forks=10000"
]