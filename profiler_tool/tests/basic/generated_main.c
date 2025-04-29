#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAIN_DEFINED
#include "helper1.h"

int main(int argc, char *argv[]) {
    if (argc < 3) {
        printf("Použití: %s <param> <param>\n", argv[0]);
        return 1;
    }
    printf("Spouštím test funkce: add\n");
    add(atoi(argv[1]), atoi(argv[2]));
    return 0;
}
