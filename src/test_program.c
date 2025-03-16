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
