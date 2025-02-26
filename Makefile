# Název výsledného souboru
TARGET = test.elf

# Kompilátor a linker
CC = arm-none-eabi-gcc
LD = arm-none-eabi-ld
OBJCOPY = arm-none-eabi-objcopy

# QEMU nastavení
QEMU = /home/vondrp/qemu920/qemu/build/qemu-system-arm
QEMU_MACHINE = vexpress-a15
QEMU_CPU = cortex-a15
QEMU_BIOS = /home/vondrp/qemu920/qemu/pc-bios/efi-virtio.rom
QEMU_BIOS_DIR = /home/vondrp/qemu920/qemu/pc-bios
QEMU_TRACE = -trace events=qemu_trace_events
QEMU_DEBUG = -d exec,cpu -D qemu-log.txt
QEMU_ICOUNT = -icount shift=3
QEMU_QMP = -qmp unix:qmp-sock,server,nowait

# Přepínače pro kompilátor
CFLAGS = -mcpu=cortex-a15 -marm -O2 -ffreestanding -nostartfiles

# Seznam zdrojových souborů
SRCS = test.c
OBJS = $(SRCS:.c=.o)

# Pravidlo pro sestavení
all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -T linker.ld -o $(TARGET) $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Pravidlo pro spuštění v QEMU
run: $(TARGET)
	$(QEMU) -machine $(QEMU_MACHINE) -cpu $(QEMU_CPU) \
	        -kernel $(TARGET) -bios $(QEMU_BIOS) \
	        -k en-us -L $(QEMU_BIOS_DIR) $(QEMU_ICOUNT) \
	        $(QEMU_TRACE) $(QEMU_DEBUG) $(QEMU_QMP)

# Vyčištění projektu
clean:
	rm -f $(TARGET) $(OBJS) qemu-log.txt
