import os
import glob
import re
import subprocess
from core.engine.generator import get_generated_main_path, get_generated_main_klee_path
from config import log_info, log_debug

# Tento skript se zabývá kompilací C programů pro různé architektury a platformy,
# včetně generování bitového kódu pro KLEE a kompilace pro ARM, x86 a bare-metal.

def find_dependencies(source_file):
    """Najde všechny soubory, které `source_file` přímo includuje.
    
    Parametry:
        source_file (str): Cesta k souboru, ve kterém hledáme závislosti.

    Návratová hodnota:
        set: Množina závislých hlavičkových souborů.
    """
    dependencies = set()
    with open(source_file, "r") as f:
        for line in f:
            match = re.match(r'#include\s+"(.+?)"', line)
            if match:
                dependencies.add(match.group(1))  # Uložíme název hlavičkového souboru
    return dependencies

def map_headers_to_sources(src_dir):
    """Najde `.c` soubor pro každou `.h` hlavičku ve složce `src/`.
    
    Parametry:
        src_dir (str): Adresář obsahující zdrojové soubory.

    Návratová hodnota:
        dict: Mapa, která přiřadí názvy hlavičkových souborů k odpovídajícím `.c` souborům.
    """
    source_files = glob.glob(os.path.join(src_dir, "*.c"))
    header_to_source = {}

    for src_file in source_files:
        base_name = os.path.splitext(os.path.basename(src_file))[0]
        header_file = f"{base_name}.h"
        header_to_source[header_file] = src_file  # Mapujeme `.h` → `.c`

    return header_to_source

def compile_klee(klee_dir, src_file, src_dir, target_arch="native"):
    """Přeloží program pro použití s KLEE a uloží výstup do `klee_dir`.
    
    Parametry:
        klee_dir (str): Adresář, do kterého se uloží přeložený bitový kód.
        src_file (str): Hlavní zdrojový soubor.
        src_dir (str): Adresář se zdrojovými soubory.
        target_arch (str): Cílová architektura pro kompilaci (výchozí je "native").
    """
    generated_main_klee = get_generated_main_klee_path()

    main_bc = os.path.join(klee_dir, "generated_main_klee.bc")
    linked_bc = os.path.join(klee_dir, "klee_program.bc")

    log_info(f"Vytvářím KLEE build: {klee_dir}")

    # Najdeme všechny závislé soubory
    dependencies = find_dependencies(src_file)
    header_to_source = map_headers_to_sources(src_dir)
    needed_sources = {header_to_source[h] for h in dependencies if h in header_to_source}
    needed_sources.add(src_file)  # Přidáme hlavní zdrojový soubor
    needed_sources = list(needed_sources)  # Převedeme na seznam

    log_info(f"Překládané zdrojové soubory: {needed_sources}")

    # Příprava kompilátorových přepínačů pro ARM nebo x86
    arch_flags = []
    if target_arch == "native":
        log_info("Kompilace pro nativní platformu.")
    elif target_arch == "aarch64":
        arch_flags = ["-target", "aarch64-linux-gnu"]  # Pro ARM64
    elif target_arch == "arm":
        arch_flags = ["-target", "arm-linux-gnueabi"]  # Pro ARM32
    else:
        arch_flags = ["-target", "x86_64-linux-gnu"]  # Výchozí pro x86_64

    # Překlad `generated_main_klee.c`
    subprocess.run([
        "clang-13", "-emit-llvm", "-g", "-c",
        *arch_flags,  # Přidáme architekturu
        "-static" if target_arch != "native" else "",  # Statická kompilace pro cizí platformu (ne pro native)
        "",  # Cesta ke klee.h
        generated_main_klee, "-o", main_bc
    ], check=True)

    # Překlad všech potřebných souborů
    bc_files = []
    for src in needed_sources:
        bc_file = os.path.join(klee_dir, os.path.basename(src).replace(".c", ".bc"))
        subprocess.run([
            "clang-13", "-emit-llvm", "-g", "-c",
            "-static" if target_arch != "native" else "",  # Statická kompilace pro cizí platformu (ne pro native)
            *arch_flags,
            "-DMAIN_DEFINED",
            src, "-o", bc_file
        ], check=True)
        bc_files.append(bc_file)

    log_info(f"Přeložené BC soubory: {bc_files}")

    # Spojení všech `.bc` souborů do jednoho
    subprocess.run(["llvm-link-13", main_bc] + bc_files + ["-o", linked_bc], check=True)
    log_info(f"Spojený LLVM bitcode: {linked_bc}")

def compile_x86(binary_file, src_file, src_dir):
    """Přeloží pouze potřebné `.c` soubory pro `generated_main.c`.
    
    Parametry:
        binary_file (str): Cílový binární soubor.
        src_file (str): Hlavní zdrojový soubor.
        src_dir (str): Adresář se zdrojovými soubory.
    """
    needed_headers = find_dependencies(src_file)
    header_to_source = map_headers_to_sources(src_dir)

    # Najdeme odpovídající `.c` soubory
    needed_sources = {header_to_source[h] for h in needed_headers if h in header_to_source}
    needed_sources.add(get_generated_main_path())  # Vždy přidáme `generated_main.c`

    compile_cmd = ["gcc", "-g", "-fno-omit-frame-pointer", "-o", binary_file] + list(needed_sources)
    log_debug(f"Kompiluji: {' '.join(compile_cmd)}")
    subprocess.run(compile_cmd, check=True)

def compile_arm_linux(binary_file, src_file, src_dir):
    """Přeloží pouze potřebné `.c` soubory pro `generated_main.c` pro ARM Linux.
    
    Parametry:
        binary_file (str): Cílový binární soubor.
        src_file (str): Hlavní zdrojový soubor.
        src_dir (str): Adresář se zdrojovými soubory.
    """
    needed_headers = find_dependencies(src_file)
    header_to_source = map_headers_to_sources(src_dir)

    # Najdeme odpovídající `.c` soubory
    needed_sources = {header_to_source[h] for h in needed_headers if h in header_to_source}
    needed_sources.add(get_generated_main_path())  # Vždy přidáme `generated_main.c`

    compile_cmd = ["arm-linux-gnueabihf-gcc", "-fno-pie", "-no-pie", "-g", "-static", "-fno-omit-frame-pointer", "-o", binary_file] + list(needed_sources)
    log_debug(f"Kompiluji: {' '.join(compile_cmd)}")
    subprocess.run(compile_cmd, check=True)

def compile_arm_bm(binary_file, src_file, generated_main_file):
    """Přeloží program pro ARM bare-metal.
    
    Parametry:
        binary_file (str): Cílový binární soubor.
        src_file (str): Hlavní zdrojový soubor.
        generated_main_file (str): Cesta k souboru `generated_main.c`.
    """
    needed_sources = [
        generated_main_file,
        ARM_START,  # startup.s
        src_file
    ]

    # Kompilace bez standardních knihoven
    compile_cmd = [
        "arm-none-eabi-gcc", "-g", "-fno-omit-frame-pointer", "-ffreestanding",
        "-nostdlib", "-nostartfiles", "-T", ARM_LINKER,
        "-o", binary_file
    ] + needed_sources

    log_info(f"Kompiluji pro ARM: {' '.join(compile_cmd)}")
    subprocess.run(compile_cmd, check=True)
