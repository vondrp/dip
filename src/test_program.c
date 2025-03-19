#include <stdio.h>
#include <stdlib.h>

// 🔹 Funkce, která se nikdy nezavolá
void unused_function() {
    printf("Tato funkce se nikdy neprovede!\n");
}

void logic_branch(int x) {
    if (x > 100) {
        printf("Velká hodnota x=%d\n", x);
    } else {
        printf("Malá hodnota x=%d\n", x);
    }
} 

void compute(int a, int b) {
    if (a == 42) {
        printf("Tajná větev odhalena! a=%d\n", a);
    }
    if (b == 0) {
        printf("Chyba: dělení nulou!\n");
        int x = 1 / b;
    }
    printf("Konec compute funkce");
}

void cycle(int a) {  // initialization: Celkem: 4 instrukcí / Iterací: 1×
    a = a + 10;  // initialization: Celkem: 1 instrukcí / Iterací: 1×

    a +=10;  // initialization: Celkem: 1 instrukcí / Iterací: 1×
    a = a + 10;  // initialization: Celkem: 1 instrukcí / Iterací: 1×
    
    for (int i = 0; i < 5; i++) {  // initialization: Celkem: 2 instrukcí / Iterací: 1× | discriminator 1: Celkem: 12 instrukcí / Iterací: 3× | discriminator 3: Celkem: 5 instrukcí / Iterací: 3×
        a = a + 10;  // discriminator 3: Celkem: 5 instrukcí / Iterací: 1×
    }
}  // initialization: Celkem: 4 instrukcí / Iterací: 1×


void recurse(int n) {  
    if (n == 0) return;  
    printf("Rek s n=%d\n", n);  
    recurse(n - 1);  
}

void B(int n);


void A(int n) {
    if (n <= 0) return;  // Zastavení rekurze
    B(n - 1);  // Nepřímá rekurze voláním B()
}

void B(int n) {
    if (n <= 0) return;  // Zastavení rekurze
    A(n - 1);  // Nepřímá rekurze voláním A()
}

void Y(int n);
void Z(int n);

void X(int n) {
    if (n <= 0) return;  // Zastavení rekurze
    Y(n - 1);  // Volání Y()
}

void Y(int n) {
    if (n <= 0) return;  // Zastavení rekurze
    Z(n - 1);  // Volání Z()
}

void Z(int n) {
    if (n <= 0) return;  // Zastavení rekurze
    X(n - 1);  // Volání X()
}


#ifndef MAIN_DEFINED
int main(int argc, char *argv[]) {
    int a = 10, b = 2;
    if (argc > 2) {
        a = atoi(argv[1]);
        b = atoi(argv[2]);
    }

    printf("Spouštím program s a=%d, b=%d\n", a, b);
    compute(a, b);
    logic_branch(a + b);

    return 0;
}
#endif
