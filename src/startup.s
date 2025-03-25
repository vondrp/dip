.section .vectors, "a"
.global _start
_start:
    ldr pc, =reset_handler  // Nastaví PC na naši resetovací rutinu

reset_handler:
    ldr sp, =0x810000   // Nastavení stack pointeru
    bl main             // Skok do main
    b .                 // Nekonečná smyčka (aby se program nezastavil)
