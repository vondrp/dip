#include <stdint.h>

volatile int result = 0;

// Výpočetní funkce pro embedded systém
/*void compute(int a, int b) {
    if ((a & 1) == 0) {
        result += a * b;
    } else if ((b % 3) == 0) {
        result -= (a / 2);
    } else {
        result ^= (b << 2);
    }

    // Simulace operací na registru (výpočetní smyčka)
    for (volatile int i = 0; i < 5; i++) {
        result += (result & 0xFF);
    }
}
*/
void compute(int a, int b) {
    if ((a & 1) == 0) {
        result += a * b;
    } else if ((b % 3) == 0) {
        result -= (a / 2);
    } else {
        result ^= (b << 2);
    }

    // 💀 Záměrná chyba: Dělení nulou při b == 42
    if (b == 42) {
        result /= (b - 42);  // Dělení nulou → způsobí výjimku
    }

    // 🔥 Přetečení: Pokud a a b mají velké hodnoty
    if (a > 10000 && b > 10000) {
        result += 0x7FFFFFFF;  // Přidání maximální hodnoty pro přetečení
    }

    // Simulace operací na registru (výpočetní smyčka)
    for (volatile int i = 0; i < 5; i++) {
        result += (result & 0xFF);
    }
}



// Implementace _exit pro bare-metal ARM prostředí
void _exit(int status) {
    (void)status;
    while (1) { }  // Nekonečná smyčka pro ukončení programu
}

// Funkce pro ukončení programu
void my_exit(int status) {
    asm volatile ("nop");  // No operation (pro debugging)
    asm volatile ("nop");
    asm volatile ("wfi");  // Wait for interrupt (energeticky úsporné)
    _exit(status);
}

int main() {
    volatile int a = 0;
    volatile int b = 0;

    // Vstupy budou nastaveny symbolicky v Angr
    compute(a, b);
    my_exit(0);
}
