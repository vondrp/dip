#include "helper2.h"

int power(int base, int exp) {
    int result = 1;
    while (exp > 0) {
        result *= base;
        exp--;
    }
    return result;
}

int switch_test(int value) {
    switch (value % 3) {
        case 0: return 10;
        case 1: return 20;
        case 2: return 30;
        default: return 0;
    }
}
