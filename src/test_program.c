#include <stdio.h>
#include <stdlib.h>
#include "helper.h"

#include "test_program.h"
#include "helper1.h"
#include "helper2.h"
#include "helper3.h"

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

void compute(int a, int b) {  // Celkem: 6 instrukcí
    if (a == 42) {  // Celkem: 2 instrukcí
        printf("Tajná větev odhalena! a=%d\n", a);
    }
    if (b == 0) {  // Celkem: 2 instrukcí
        printf("Chyba: dělení nulou!\n");  // Celkem: 150 instrukcí
        int x = 1 / b;  // Celkem: 4 instrukcí | ⚠ CRASH DETECTED! ⚠
    }
    printf("Konec compute funkce");
}

void cycle(int a) {
    a = a + 10;

    a +=10;
    a = a + 10;

    for (int i = 0; i < 5; i++) {
        a = a + 10;
    }
}


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

void external_call() {  // Celkem: 3 instrukcí
    printf("Volám externí funkci z helper.c\n");  // Celkem: 159 instrukcí
    helper_function();  // Celkem: 167 instrukcí
}  // Celkem: 3 instrukcí


int angrT(int a, double b, char c) {

    if (b > 5.5) {
        return 0;
    }

    if (c == 'c') {
        return 1;
    }

    if (a > 50) {
        return 2;
    }

    return 3;
}

int compute_ret(int a, int b) {
    if (a == 42) {
        return a / 2;
    }
    if (b == 0) {
        int x = 1 / b;
        return x;
    }
    return (a + b);
}


// Funkce compute() volá další funkce a obsahuje větve, cykly atd.
int compute_adv(int a, int b) {
    int result = 0;

    printf("Start compute: a=%d, b=%d\n", a, b);

    // Podmíněné větvení
    if (a > b) {
        result += add(a, b);
    } else if (a < b) {
        result += multiply(a, b);
    } else {
        result += power(a, 2);
    }

    // Cyklus (počítá součet čísel od 0 do a)
    for (int i = 0; i < a; i++) {
        result += i;
    }

    // Volání rekurzivní funkce (faktoriál)
    result += factorial(a % 5);

    // Volání funkce se switch-case
    result += switch_test(a);

    printf("End compute: result=%d\n", result);
    return result;
}

/*
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
#endif*/
