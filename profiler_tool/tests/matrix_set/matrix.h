#ifndef MATRIX_H
#define MATRIX_H

#include <stdint.h>

/** Typ dat uložených v matici */
typedef float real;

/** Struktura reprezentující jednoduchou 2D matici */
typedef struct {
    uint32_t rows;
    uint32_t cols;
    real *data;
} matrix;

// Vrací průměr hodnot v matici
float compute_avg(matrix *m);

// Zjistí, zda je matice prázdná (0x0 nebo nealokovaná data)
int matrix_is_empty(matrix *m);

// Vrací maximální hodnotu v matici nebo zápornou hodnotu při chybě
real matrix_max(matrix *m);

// Vrací počet nenulových prvků
uint32_t count_nonzero(matrix *m);

#endif // MATRIX_H
