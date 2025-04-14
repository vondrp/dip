#ifndef GLOBALS_H
#define GLOBALS_H

// Globální proměnné
extern int global_counter;
extern const int MAX_LIMIT;
extern int status_flag;

// Funkce manipulující s globálními proměnnými
void increment_counter(void);
void reset_counter(void);
void set_status(int flag);
int check_threshold(int value);

#endif // GLOBALS_H
