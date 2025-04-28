#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAIN_DEFINED
#include "matrix.h"

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Použití: %s <pocet_radku> <pocet_sloupcu> \"<prvky_matice>\"\n", argv[0]);
        return 1;
    }

    uint32_t rows = (uint32_t)atoi(argv[1]);
    uint32_t cols = (uint32_t)atoi(argv[2]);
    const char *data_string = argv[3];

    if (rows == 0 || cols == 0) {
        fprintf(stderr, "Chybný počet řádků nebo sloupců.\n");
        return 1;
    }

    uint32_t expected_elements = rows * cols;

    matrix m;
    m.rows = rows;
    m.cols = cols;
    m.data = (real *)malloc(sizeof(real) * expected_elements);

    if (!m.data) {
        fprintf(stderr, "Chyba alokace paměti.\n");
        return 1;
    }

    // Parsování dat ze stringu
    char *data_copy = strdup(data_string); // vytvoří kopii řetězce, protože strtok mění vstup
    if (!data_copy) {
        fprintf(stderr, "Chyba kopírování dat.\n");
        free(m.data);
        return 1;
    }

    char *token = strtok(data_copy, " ");
    uint32_t index = 0;
    while (token != NULL && index < expected_elements) {
        m.data[index++] = (real)atof(token);
        token = strtok(NULL, " ");
    }

    free(data_copy);

    if (index != expected_elements) {
        fprintf(stderr, "Počet zadaných prvků (%u) neodpovídá očekávanému počtu (%u).\n", index, expected_elements);
        free(m.data);
        return 1;
    }

    // Volání funkce
    real max = matrix_max(&m);
    printf("Maximální hodnota v matici: %.6f\n", max);

    // Uvolnění paměti
    free(m.data);

    return 0;
}
