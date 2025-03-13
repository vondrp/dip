#include <stdint.h>
#include <stdlib.h>

volatile int result = 0;

void compute(int a, int b) {
    if ((a & 1) == 0) {
        result += a * b;
    } else if ((b % 3) == 0) {
        result -= (a / 2);
    } else {
        result ^= (b << 2);
    }

    if (b == 42) {
        result /= (b - 42);
    }

    if (a > 10000 && b > 10000) {
        result += 0x7FFFFFFF;
    }

    for (volatile int i = 0; i < 5; i++) {
        result += (result & 0xFF);
    }
}

void my_exit(int status) {
    exit(status);
}


int main() {
    volatile int a = 5, b = 10;  

    compute(a, b);
    
    return 0;
    //my_exit(0);
}
