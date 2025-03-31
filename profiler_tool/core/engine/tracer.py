import shutil
import subprocess
import time

from core.config import GDB_SCRIPT, GDB_SCRIPT_ARM


def run_gdb_trace(binary_file, trace_file, args):
    """Spustí GDB s vybranými parametry a zachytí instrukce do `trace.log`."""
    gdb_cmd = [
        "gdb", "-q", "-ex", f"source {GDB_SCRIPT}",
        "-ex", "starti",
        "-ex", f"trace-asm {trace_file}",
        "-ex", "quit",
        "--args", binary_file, *args
    ]
    print(f"Spouštím GDB: {' '.join(gdb_cmd)}")
    subprocess.run(gdb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_gdb_trace_arm_bm(binary_file, trace_file, args):
    """ Spustí ARM binárku v QEMU, připojí GDB a spustí trace skript. """

     # 🔹 Ověření dostupnosti QEMU-system-arm
    qemu_executable = shutil.which("qemu-system-arm")
    if not qemu_executable:
        raise FileNotFoundError("[ERROR] ❌ `qemu-system-arm` nebyl nalezen. Zkontrolujte instalaci.")

    # 🔹 Ověření dostupnosti GDB pro ARM
    gdb_executable = shutil.which("arm-none-eabi-gdb") or shutil.which("gdb-multiarch")
    if not gdb_executable:
        raise FileNotFoundError("[ERROR] ❌ `arm-none-eabi-gdb` nebo `gdb-multiarch` nebyl nalezen. Zkontrolujte instalaci.")

    # 🔹 1️⃣ Spustíme QEMU v GDB server módu (zastaveno na startu)
    """
    qemu_cmd = [
        qemu_executable,
        "-M", "virt",            # Virtuální ARM platforma
        "-cpu", "cortex-a15",     # CPU model
        "-m", "128M",            # Nastavení paměti
        "-nographic",            # Konzolový mód
        "-L", "/home/vondrp/buildroot/output/host/share/qemu", 
        "-bios", "efi-virtio.rom",
        "-kernel", binary_file,   # Použití binárního souboru jako kernelu
        "-gdb", "tcp::1234",      # Otevření GDB serveru na portu 1234
        "-S"                     # Zastavení před startem
    ]
    """
    qemu_cmd = [
    qemu_executable,
    "-M", "virt",            # Virtuální ARM platforma
    "-cpu", "cortex-a15",     # CPU model
    "-m", "128M",            # Nastavení paměti
    "-nographic",            # Konzolový mód
     "-L", "/home/vondrp/buildroot/output/host/share/qemu", 
    "-bios", "efi-virtio.rom",
    "-kernel", binary_file,
    "-append", "console=ttyAMA0",  # Simulace konzole
    "-gdb", "tcp::1234",      # Otevře GDB server na portu 1234
    "-S"                     # Zastaví před spuštěním
    ]

    print(f"[INFO] 🚀 Spouštím QEMU: {' '.join(qemu_cmd)}")
    qemu_proc = subprocess.Popen(qemu_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


    # Počkáme, než se QEMU inicializuje
    time.sleep(10)
    print(f"[INFO] gdb binary file: {binary_file}")
    # 🔹 3️⃣ Spustíme GDB pro ARM
    gdb_cmd = [
        gdb_executable, "-q",
        "-ex", "set pagination off",
        "-ex", "set confirm off",
        "-ex", "set architecture arm",
        "-ex", f"file {binary_file}",
        "-ex", "target remote localhost:1234",
        "-ex", "set $pc = 0x8000",   
        "-ex", "set $sp = 0x810000",
        "-ex", "info registers",      # Výpis registrů pro kontrolu
        "-ex", f"source {GDB_SCRIPT_ARM_BM}",
        "-ex", "starti",
        "-ex", f"trace-asm-arm {trace_file}",
        "-ex", "quit"
    ]

    print(f"[INFO] 🛠 Spouštím GDB: {' '.join(gdb_cmd)}")
    subprocess.run(gdb_cmd, check=True)

    # 🔹 4️⃣ Ukončíme QEMU po dokončení trace
    qemu_proc.terminate()
    print("[INFO] ✅ Trace dokončen, QEMU ukončen.")


def run_gdb_trace_arm_linux(binary_file, trace_file, args):
    """ Spustí ARM Linux binárku v QEMU, připojí GDB a provede tracing. """

    # 🔹 Ověření dostupnosti QEMU pro Linuxový ARM
    qemu_executable = shutil.which("qemu-arm")# or shutil.which("qemu-system-arm")
    if not qemu_executable:
        raise FileNotFoundError("[ERROR] ❌ `qemu-arm` nebo `qemu-system-arm` nebyl nalezen. Zkontrolujte instalaci.")

    # 🔹 Ověření dostupnosti GDB multiarch
    gdb_executable = shutil.which("gdb-multiarch")
    if not gdb_executable:
        raise FileNotFoundError("[ERROR] ❌ `gdb-multiarch` nebyl nalezen. Zkontrolujte instalaci.")

    # 🔹 1️⃣ Spustíme QEMU v GDB server módu
    qemu_cmd = [
        qemu_executable, "-L", "/usr/arm-linux-gnueabihf","-g", "1234",  # Spustí QEMU s GDB serverem na portu 1234
        binary_file, *args
    ]

    print(f"[INFO] 🚀 Spouštím QEMU: {' '.join(qemu_cmd)}")
    qemu_proc = subprocess.Popen(qemu_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Počkáme, než se QEMU inicializuje
    time.sleep(2)

    # 🔹 2️⃣ Spustíme GDB a připojíme se k QEMU
    gdb_cmd = [
        gdb_executable, "-q",
        "-ex", f"source {GDB_SCRIPT_ARM}",
        "-ex", "set pagination off",
        "-ex", "set confirm off",
        "-ex", "set architecture arm",
        "-ex", "set sysroot /usr/arm-linux-gnueabihf",
        "-ex", "set logging file gdb_log.txt",
        "-ex", "set logging overwrite on",
        "-ex", "set logging on",
        "-ex", f"file {binary_file}",
        "-ex", "info functions",
        "-ex", "target remote localhost:1234",
        "-ex", "info registers",
        "-ex", "starti",
        "-ex", f"trace-asm {trace_file}",
        "-ex", "set logging off",
        "-ex", "quit"
    ]

    """
    gdb_cmd = [
        gdb_executable, "-q",
        "-ex", f"source {GDB_SCRIPT_ARM}",
        "-ex", "set pagination off",
        "-ex", "set confirm off",
        "-ex", "set architecture arm",
        "-ex", "set sysroot /usr/arm-linux-gnueabihf",
        "-ex", f"file {binary_file}",
        "-ex", "info functions",
        "-ex", "target remote localhost:1234",
        "-ex", "info registers",
        "-ex", "set logging file gdb_log.txt",
        "-ex", "set logging overwrite on",
        "-ex", "set logging on",
        "-ex", "starti",
        "-ex", f"trace-asm {trace_file}",
        "-ex", "set logging off",
        "-ex", "quit"
    ]
    """
    print(f"[INFO] 🛠 Spouštím GDB: {' '.join(gdb_cmd)}")
    subprocess.run(gdb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 3️⃣ Ukončíme QEMU po dokončení trace
    qemu_proc.terminate()
    print("[INFO] ✅ Trace dokončen, QEMU ukončen.")
