KTEST_TOOL = "ktest-tool"
KLEE_EXECUTABLE = "klee"

KLEE_OPTIONS = [
    "--optimize",
    "--libc=uclibc",
    "--posix-runtime",
    "--only-output-states-covering-new"
]
