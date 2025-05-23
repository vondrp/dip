import os
import glob
import re
import subprocess
from core.engine.generator import get_generated_main_path, get_generated_main_klee_path
from config import log_info, log_debug
from config import BM_STARTUP, BM_LINKER

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
            match = re.match(r'\s*#include\s*[<"](.+?)[">]', line)
            if match:
                header_path = match.group(1)
                dependencies.add(os.path.basename(header_path))
                #dependencies.add(match.group(1))  # Uložíme název hlavičkového souboru

    log_debug(f"Závislosti pro {source_file}: {dependencies}")       
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

    log_debug(f"Header to source: {header_to_source}")
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


def compile_binary(binary_file, src_file, src_dir, platform="arm"):
    """Přeloží potřebné `.c` soubory pro danou platformu (arm, riscv, native/x86).

    Parametry:
        binary_file (str): Cílový binární soubor.
        src_file (str): Hlavní zdrojový soubor.
        src_dir (str): Adresář se zdrojovými soubory.
        platform (str): Platforma pro kompilaci ('arm', 'riscv', 'native').
    """
    needed_headers = find_dependencies(src_file)
    header_to_source = map_headers_to_sources(src_dir)

    # Najdeme odpovídající `.c` soubory
    needed_sources = {header_to_source[h] for h in needed_headers if h in header_to_source}
    needed_sources.add(get_generated_main_path())  # Vždy přidáme `generated_main.c`

    log_debug(f"Needed sources: {needed_sources}")

    # Výběr překladače a specifických flagů dle platformy
    if platform == "arm":
        compiler = "arm-linux-gnueabihf-gcc"
        flags = ["-DMAIN_DEFINED", "-fno-pie", "-no-pie", "-g", "-static", "-fno-omit-frame-pointer"]
    elif platform == "riscv":
        compiler = "riscv64-linux-gnu-gcc"
        flags = ["-DMAIN_DEFINED", "-fno-pie", "-no-pie", "-g", "-static", "-fno-omit-frame-pointer"]
        #flags = ["-g", "-static", "-march=rv64imac", "-mabi=lp64"]
    elif platform == "native":
        compiler = "gcc"
        flags = ["-DMAIN_DEFINED", "-g", "-fno-omit-frame-pointer"]
    else:
        raise ValueError(f"Neznámá platforma: {platform}")

    compile_cmd = [compiler] + flags + ["-o", binary_file] + list(needed_sources)

    log_debug(f"Kompiluji pro platformu '{platform}': {' '.join(compile_cmd)}")
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

def compile_binary_bm(binary_file, src_file, src_dir, platform="arm_bm"):
    """Přeloží potřebné `.c` soubory pro platformu bare-metal ARM (arm_bm).

    Parametry:
        binary_file (str): Cílový binární soubor.
        src_file (str): Hlavní zdrojový soubor.
        src_dir (str): Adresář se zdrojovými soubory.
        platform (str): Platforma pro kompilaci ('arm_bm').
    """
    needed_headers = find_dependencies(src_file)
    header_to_source = map_headers_to_sources(src_dir)

    # Najdeme odpovídající `.c` soubory
    needed_sources = {header_to_source[h] for h in needed_headers if h in header_to_source}
    
    needed_sources.add(get_generated_main_path())  # Vždy přidáme `generated_main.c`

    log_debug(f"Needed sources: {needed_sources}")

    if platform == "arm_bm":
        # Nastavení pro ARM bare-metal (ARM toolchain: arm-none-eabi)
        assembler = "arm-none-eabi-as"
        compiler = "arm-none-eabi-gcc"
        linker = "arm-none-eabi-ld"
        objcopy = "arm-none-eabi-objcopy"
        
        # Přepínače pro ARM bare-metal kompilaci
        flags = ["-mcpu=arm926ej-s", "-g", "-nostdlib", "-ffreestanding", "-static"]

        # Linker a startup soubory
        linker_script = BM_LINKER  # Předpokládáme, že BM_LINKER obsahuje cestu k linker skriptu
        startup_file = BM_STARTUP  # Předpokládáme, že BM_STARTUP obsahuje cestu k startup souboru

        # Kompilace startup souboru
        log_debug(f"Spouštím assembler pro startup: {startup_file}")
        #startup_output = os.path.join(os.path.dirname(startup_file), "startup.o")

        startup_output = "startup.o"

        subprocess.run([assembler, "-g", startup_file, "-o", startup_output], check=True)

        # Kompilace C souborů
        for src in needed_sources:
            log_debug(f"Komplikuji C soubor: {src}")
            subprocess.run([compiler] + flags + ["-c", src, "-o", f"{src}.o"], check=True)

        # Linkování všech objektových souborů
        object_files = [f"{src}.o" for src in needed_sources] #+ [startup_output]
        log_debug(f"Linkování: {linker} -T {linker_script} {' '.join(object_files)} -o test.elf")
        subprocess.run([linker, "-T", linker_script] + object_files + ["-lnosys", "-lgcc", "-o", "test.elf"], check=True)


        # Převod ELF na binární soubor
        log_debug(f"Převod ELF na binární soubor: {objcopy} -O binary test.elf {binary_file}")
        subprocess.run([objcopy, "-O", "binary", "test.elf", binary_file], check=True)

    else:
        raise ValueError(f"Neznámá platforma: {platform}")
    
    log_debug(f"Vygenerován binární soubor: {binary_file}")
