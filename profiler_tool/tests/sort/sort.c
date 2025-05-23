#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sort.h"

// Funkce pro vkládání položky do seřazeného pole
static void insert_ordered(int *array, unsigned nelem, int item) {
    unsigned i = 0;
  
    for (; i != nelem; ++i) {
      if (item < array[i]) {
        memmove(&array[i+1], &array[i], sizeof(*array) * (nelem - i));
        break;
      }
    }
  
    array[i] = item;
  }

// Bubble sort algoritmus
void bubble_sort(int *array, unsigned nelem) {
    for (;;) {
      int done = 1;
  
      for (unsigned i = 0; i + 1 < nelem; ++i) {
        if (array[i+1] < array[i]) {
          int t = array[i + 1];
          array[i + 1] = array[i];
          array[i] = t;
          done = 0;
        }
      }
  
      break;
    }
  }

// Insertion sort algoritmus
void insertion_sort(int *array, unsigned nelem) {
  int *temp = malloc(sizeof(*temp) * nelem);

  for (unsigned i = 0; i != nelem; ++i)
    insert_ordered(temp, i, array[i]);

  memcpy(array, temp, sizeof(*array) * nelem);
  free(temp);
}


// Testovací funkce pro porovnání výsledků různých algoritmů
void test(int *array, unsigned nelem) {
    int *temp1 = malloc(sizeof(*array) * nelem);
    int *temp2 = malloc(sizeof(*array) * nelem);
  
    //printf("input: [%d, %d, %d, %d]\n",
    //       array[0], array[1], array[2], array[3]);
  
    memcpy(temp1, array, sizeof(*array) * nelem);
    memcpy(temp2, array, sizeof(*array) * nelem);
  
    insertion_sort(temp1, nelem);
    bubble_sort(temp2, nelem);
  
    //printf("insertion_sort: [%d, %d, %d, %d]\n",
    //       temp1[0], temp1[1], temp1[2], temp1[3]);
  
    //printf("bubble_sort   : [%d, %d, %d, %d]\n",
    //       temp2[0], temp2[1], temp2[2], temp2[3]);
  
    for (unsigned i = 0; i != nelem; ++i)
      assert(temp1[i] == temp2[i]);
  
    free(temp1);
    free(temp2);
}
