#include <stdio.h>

// Funkce pro kontrolu chybového kódu
int check_error_code(int code) {
    if (code == 42) {  // Magická hodnota, kterou hledáme
        return 1;  // Chyba detekována
    }
    return 0;  // Vše v pořádku
}

int main() {
    int input;
    printf("Zadejte chybový kód: ");
    scanf("%d", &input);

    if (check_error_code(input)) {
        printf("Chyba detekována!\n");
    } else {
        printf("Vše v pořádku.\n");
    }
    
    return 0;
}
