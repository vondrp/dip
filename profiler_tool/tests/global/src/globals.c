#include <stdio.h>
#include "../include/globals.h"

// Definice globálních proměnných
int global_counter = 0;
const int MAX_LIMIT = 100;
int status_flag = 0;

// Statická globální proměnná (lokální jen pro tento soubor)
static int internal_static = 5;

void increment_counter(void) {
    global_counter++;
    printf("Counter: %d\n", global_counter);
}

void reset_counter(void) {
    global_counter = 0;
    printf("Counter reset\n");
}

void set_status(int flag) {
    status_flag = flag;
    printf("Status flag set to: %d\n", status_flag);
}

int check_threshold(int value) {
    if (value > MAX_LIMIT) {
        printf("Hodnota %d přesahuje limit %d\n", value, MAX_LIMIT);
        return 1;
    } else {
        printf("Hodnota %d je v mezích\n", value);
        return 0;
    }
}
