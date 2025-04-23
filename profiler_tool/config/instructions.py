from .arch import ACTIVE_ARCHITECTURE

_call_instructions = None
_return_instructions = None


def _init_instruction_sets():
    global _call_instructions, _return_instructions

    if ACTIVE_ARCHITECTURE == "x86" or ACTIVE_ARCHITECTURE == "native":
        _call_instructions = [
            "call", "jmp", "callq", "jmpq", "callx"
        ]
        _return_instructions = [
            "ret"
        ]
    elif ACTIVE_ARCHITECTURE == "arm":
        _call_instructions = [
            "bl", "bx", "b", "blx"
        ]
        _return_instructions = [
            "bx lr",
            "mov pc, lr",
            "blx lr",
            r"pop\s+\{r7,\s+pc\}"
        ]
    elif ACTIVE_ARCHITECTURE == "riscv":
        _call_instructions = [
            "jal", "jalr"
        ]
        _return_instructions = [
            "ret",  # standardně alias pro jalr x0, x1, 0
            "jalr x0"
        ]
    else:
        raise ValueError(f"Neznámá architektura: {ACTIVE_ARCHITECTURE}")


def get_call_instructions_regex():
    global _call_instructions
    if _call_instructions is None:
        _init_instruction_sets()
    return "|".join([rf"\b{instr}\b" for instr in _call_instructions])


def get_return_instructions_regex():
    global _return_instructions
    if _return_instructions is None:
        _init_instruction_sets()
    return "|".join([rf"{instr}" for instr in _return_instructions])
