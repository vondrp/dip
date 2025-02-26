// Jednoduchý ARM program pro testování v QEMU
volatile int result = 0;

void compute() {
    int a = 10;
    int b = 20;
    for (int i = 0; i < 3; i++) {
        result += a * b;  // Jednoduchá smyčka s aritmetikou
        result -= a;       // Přidáme odčítání, aby byly operace různorodé
    }
}

// Implementace _exit pro bare-metal prostředí
void _exit(int status) {
    (void)status;  // Potlačí warning o nevyužité proměnné
    while (1) { }  // Nekonečná smyčka, program nemá OS ke kterému by se vrátil
}

int main() {
    compute();
    _exit(0);  // Volání _exit místo nekonečné smyčky
}
