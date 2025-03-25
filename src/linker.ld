ENTRY(_start)

SECTIONS
{
    . = 0x8000;

    .text : {
        *(.text)
        *(.text.*)
    } 

    . = ALIGN(4);
    .data : {
        *(.data)
        *(.data.*)
    }

    . = ALIGN(4);
    .bss : {
        *(.bss)
        *(COMMON)
    }
}
