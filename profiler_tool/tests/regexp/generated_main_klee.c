#include <klee/klee.h>
#include <stdio.h>

#include "regexp.h"

int main() {
    char param_0[10];
    klee_make_symbolic(param_0, sizeof(param_0), "param_0");
    char param_1[10];
    klee_make_symbolic(param_1, sizeof(param_1), "param_1");

    printf("Spouštím test funkce: match\n");
    match(param_0, param_1);
    return 0;
}
