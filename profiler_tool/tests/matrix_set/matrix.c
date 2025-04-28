#include "matrix.h"

float compute_avg(matrix *m) {
    if (!m || !m->data || m->rows == 0 || m->cols == 0)
        return -1.0f;

    float sum = 0.0f;
    uint32_t total = m->rows * m->cols;

    for (uint32_t i = 0; i < total; i++) {
        sum += m->data[i];
    }

    return sum / total;
}

int matrix_is_empty(matrix *m) {
    return (!m || m->rows == 0 || m->cols == 0 || !m->data);
}

real matrix_max(matrix *m) {
    if (!m || !m->data || m->rows == 0 || m->cols == 0)
        return -9999.0f; // error marker

    real max_val = m->data[0];
    for (uint32_t i = 1; i < m->rows * m->cols; i++) {
        if (m->data[i] > max_val)
            max_val = m->data[i];
    }
    return max_val;
}

uint32_t count_nonzero(matrix *m) {
    if (!m || !m->data || m->rows == 0 || m->cols == 0)
        return 0;

    uint32_t count = 0;
    for (uint32_t i = 0; i < m->rows * m->cols; i++) {
        if (m->data[i] != 0.0f)
            count++;
    }
    return count;
}
