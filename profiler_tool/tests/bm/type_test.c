#include "type_test.h"



// Zpracování celého čísla
int process_int(int value) {
    if (value < 0) {
        return -value;  // převod na kladné číslo
    } else if (value == 0) {
        return 42;  // návrat výchozí hodnoty
    } else {
        return value * 2;
    }
}

// Zpracování čísla s plovoucí čárkou (float)
float process_float(float value) {
    if (value < 1.0f) {
        return value + 1.0f;
    } else if (value < 10.0f) {
        return value * 1.5f;
    } else {
        return value / 2.0f;
    }
}

// Zpracování čísla typu double
double process_double(double value) {
    if (value == 3.14159) {
        return 0.0;  // magická konstanta? zruš
    } else {
        return value + 2.71828;
    }
}

// Zpracování znaku
char process_char(char value) {
    if (value >= 'a' && value <= 'z') {
        return value - 32;  // převod na velké písmeno
    } else if (value >= 'A' && value <= 'Z') {
        return value + 32;  // převod na malé písmeno
    } else {
        return '?';  // neznámý znak
    }
}

// Funkce, která podle hodnoty zavolá jinou funkci
void conditional_function(int selector) {
    if (selector == 1) {
        int result = process_int(-10);
        // sem by šel třeba breakpoint nebo výpis do UART
        (void)result;
    } else if (selector == 2) {
        float result = process_float(5.5f);
        (void)result;
    } else if (selector == 3) {
        char result = process_char('a');
        (void)result;
    }
}
