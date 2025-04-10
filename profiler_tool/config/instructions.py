CALL_INSTRUCTIONS = [
    "call", "jmp", "callq", "jmpq", "callx",  # Pro x86
    "bl", "bx", "b", "blx"                   # Pro ARM
]

RETURN_INSTRUCTIONS = [
    "ret",            # Pro x86, s hranicemi slova
    "bx lr",              # Pro ARM (verze ARMv7)
    "mov pc, lr",         # Pro ARM (verze ARMv8)
    "blx lr",             # Pro ARM (možnost při volání funkce)
    "pop\s+\{r7,\s+pc\}"   # pro ARM
]

def get_call_instructions_regex():
    return "|".join([rf"\b{instr}\b" for instr in CALL_INSTRUCTIONS])

def get_return_instructions_regex():
    return "|".join([rf"{instr}" for instr in RETURN_INSTRUCTIONS])
