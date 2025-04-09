CALL_INSTRUCTIONS = [
    "call", "jmp", "callq", "jmpq", "callx",  # Pro x86
    "bl", "bx", "b", "blx"                   # Pro ARM
]

RETURN_INSTRUCTIONS = [
    "ret",            # Pro x86
    "bx lr",          # Pro ARM (verze ARMv7)
    "mov pc, lr",     # Pro ARM (verze ARMv8)
    "blx lr",         # Pro ARM (možnost při volání funkce)
]

def get_call_instructions_regex():
    return "|".join([rf"\b{instr}\b" for instr in CALL_INSTRUCTIONS])

def get_return_instructions_regex():
    return "|".join([rf"\b{instr}\b" for instr in RETURN_INSTRUCTIONS])
