import shutil
import subprocess
import time
import socket
import tempfile
import re
from config import GDB_SCRIPT, GDB_SCRIPT_ARM, GDB_SCRIPT_RISCV
from config import log_info, log_debug, log_warning, log_error

"""
Tento skript obsahuje funkce pro automatizaci traceování ARM binárek v QEMU prostředí s využitím GDB.
Hlavním účelem skriptu je spuštění binárního souboru v emulátoru QEMU, připojení GDB pro ladění,
a následné traceování instrukcí ARM. Skript také implementuje čekání na připravenost QEMU pomocí 
kontroly otevřeného portu 1234 (použití netstat) a provádí traceování jak pro standardní ARM aplikace, 
tak i pro specifické ARM buildy.
"""

def run_gdb_trace(binary_file, trace_file, args):
    """
    Spustí GDB s vybranými parametry a zachytí instrukce do `trace.log`.

    Parametry:
    binary_file (str): Cesta k binárnímu souboru, který má být traceován.
    trace_file (str): Cesta k souboru, kam budou uloženy trace instrukce.
    args (list): Seznam argumentů, které budou předány binárnímu souboru při spuštění.
    Návratová hodnota:
    None
    """
    gdb_cmd = [
        "gdb", "-q", "-ex", f"source {GDB_SCRIPT}",
        "-ex", "set logging file gdb_log.txt",
        "-ex", "set logging on",
        "-ex", "starti",
        "-ex", f"trace-asm {trace_file}",
        "-ex", "quit",
        "--args", binary_file, *args
    ]

    log_info(f"Spouštím GDB: {' '.join(gdb_cmd)}")
    
    subprocess.run(gdb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_for_qemu_ready(timeout=30):
    """
    Čeká na to, až bude QEMU připraveno na připojení (používá netstat).

    Parametry:
    timeout (int): Časový limit (v sekundách), po kterém skript přestane čekat. Výchozí je 30 sekund.

    Návratová hodnota:
    bool: True, pokud je QEMU připraveno na připojení, jinak False.
    """
    for _ in range(timeout):
        try:
            result = subprocess.run(
                ['netstat', '-tuln'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if '1234' in result.stdout and 'LISTEN' in result.stdout:
                return True 
        except subprocess.CalledProcessError:
            pass
        time.sleep(2)
    return False


def run_gdb_trace_qemu(binary_file, trace_file, args, platform="arm"):
    """
    Spustí binárku v QEMU, připojí GDB a provede tracing pro ARM nebo RISC-V.

    Parametry:
        binary_file (str): Cesta k binárnímu souboru pro Linux.
        trace_file (str): Cesta k souboru, kam budou uloženy trace instrukce.
        args (list): Argumenty pro spuštění binárního souboru v QEMU.
        platform (str): 'arm' nebo 'riscv'
    """
    # Výběr QEMU a GDB architektury dle platformy
    if platform == "arm":
        qemu_executable = shutil.which("qemu-arm")
        gdb_arch = "arm"
        gdb_script = GDB_SCRIPT_ARM
        trace_cmd = f"trace-asm-arm {trace_file}"
    elif platform == "riscv":
        qemu_executable = shutil.which("qemu-riscv64")
        gdb_arch = "riscv:rv64"
        gdb_script = GDB_SCRIPT_RISCV
        trace_cmd = f"trace-asm-riscv {trace_file}"
    else:
        raise ValueError(f"Neznámá platforma: {platform}")

    if not qemu_executable:
        raise FileNotFoundError(f"[ERROR] QEMU pro platformu `{platform}` nebyl nalezen.")

    gdb_executable = shutil.which("gdb-multiarch")
    if not gdb_executable:
        raise FileNotFoundError("[ERROR] `gdb-multiarch` nebyl nalezen. Zkontrolujte instalaci.")

    # Spuštění QEMU v GDB server módu
    qemu_cmd = [qemu_executable, "-g", "1234", binary_file, *args]
    log_info(f"Spouštím QEMU: {' '.join(qemu_cmd)}")
    qemu_proc = subprocess.Popen(qemu_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not wait_for_qemu_ready():
        raise RuntimeError("[ERROR] QEMU není připraveno na připojení během timeoutu.")

    # GDB příkaz
    gdb_cmd = [
        gdb_executable, "-q",
        "-ex", f"source {gdb_script}",
        "-ex", "set pagination off",
        "-ex", "set confirm off",
        "-ex", f"set architecture {gdb_arch}",
        "-ex", "set logging file gdb_log.txt",
        "-ex", "set logging overwrite on",
        "-ex", "set logging enabled on",
        "-ex", f"file {binary_file}",
        "-ex", "target remote localhost:1234",
        "-ex", "break main",
        "-ex", "continue",
        "-ex", trace_cmd,
        "-ex", "set logging enabled off",
        "-ex", "quit"
    ]

    log_info(f"Spouštím GDB: {' '.join(gdb_cmd)}")
    subprocess.run(gdb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Ukončíme QEMU
    qemu_proc.terminate()
    log_info("Trace dokončen, QEMU ukončen.")


def run_gdb_trace_qemu_bm(binary_file, trace_file, platform="arm_bm", qemu_machine="virt", cpu_model=None, qemu_extra_args=None):
    """
    Spustí bare-metal binárku v QEMU, připojí GDB a provede tracing pro ARM nebo RISC-V.

    Parametry:
        binary_file (str): Cesta k binárnímu souboru pro bare-metal.
        trace_file (str): Cesta k souboru, kam budou uloženy trace instrukce.
        platform (str): 'arm_bm' nebo 'riscv_bm'
        qemu_machine (str): QEMU machine model (např. "virt", "lm3s6965evb", "sifive_e").
        cpu_model (str|None): Volitelný CPU model (např. "cortex-a15" pro ARM).
        qemu_extra_args (list|None): Další argumenty pro QEMU (např. ["-nographic"])
    """
    if platform == "arm_bm":
        qemu_executable = shutil.which("qemu-system-arm")
        gdb_arch = "arm"
        gdb_script = GDB_SCRIPT_ARM
        trace_cmd = f"trace-asm-arm {trace_file}"
    elif platform == "riscv_bm":
        qemu_executable = shutil.which("qemu-system-riscv64")
        gdb_arch = "riscv:rv64"
        gdb_script = GDB_SCRIPT_RISCV
        trace_cmd = f"trace-asm-riscv {trace_file}"
    else:
        raise ValueError(f"Neznámá platforma: {platform}")

    if not qemu_executable:
        raise FileNotFoundError(f"[ERROR] QEMU pro platformu `{platform}` nebyl nalezen.")

    gdb_executable = shutil.which("gdb-multiarch")
    if not gdb_executable:
        raise FileNotFoundError("[ERROR] `gdb-multiarch` nebyl nalezen. Zkontrolujte instalaci.")

    qemu_cmd = [
        qemu_executable,
        "-M", qemu_machine,
        "-nographic",
        "-kernel", binary_file,
        "-gdb", "tcp::1234",
        "-S"
    ]

    if cpu_model and platform == "arm_bm":
        qemu_cmd += ["-cpu", cpu_model]

    if qemu_extra_args:
        qemu_cmd += qemu_extra_args

    log_info(f"Spouštím QEMU (bare-metal): {' '.join(qemu_cmd)}")
    qemu_proc = subprocess.Popen(qemu_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not wait_for_qemu_ready():
        raise RuntimeError("[ERROR] QEMU není připraveno na připojení během timeoutu.")

    gdb_cmd = [
        gdb_executable, "-q",
        "-ex", f"source {gdb_script}",
        "-ex", "set pagination off",
        "-ex", "set confirm off",
        "-ex", f"set architecture {gdb_arch}",
        "-ex", "set logging file gdb_log.txt",
        "-ex", "set logging overwrite on",
        "-ex", "set logging enabled on",
        "-ex", f"file {binary_file}",
        "-ex", "target remote localhost:1234",
        "-ex", "break *0x0",
        "-ex", "continue",
        "-ex", trace_cmd,
        "-ex", "set logging enabled off",
        "-ex", "quit"
    ]

    log_info(f"Spouštím GDB: {' '.join(gdb_cmd)}")
    subprocess.run(gdb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    qemu_proc.terminate()
    log_info("Trace dokončen, QEMU ukončen.")
