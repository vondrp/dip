#include <stdint.h>

int check(int a, int b) {
    if (a == 42 && b == 13) {
        return 1;  // Tohle by měl Angr najít
    }
    return 0;
}

int main() {
    volatile int a = 0;  // Volatile zabrání optimalizaci
    volatile int b = 0;

    return check(a, b);
}

// arm-linux-gnueabi-gcc -o build/test_2_arm.elf src/test_2.c -static