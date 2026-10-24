#ifndef LISTES_H
#define LISTES_H

#include <stdbool.h>

/*
 * Pour réaliser des tests de performance, désactiver tous les 
 * affichages.
 * Pour cela, le plus simple est de compiler avec la macro 'SILENT' définie, en 
 * faisant 'make silent'
 */

#ifdef SILENT

/* Desactive tous les affichages */
#define printf(fmt, ...) (0)
#define eprintf(fmt, ...) (0)
#define putchar(c) (0)
/* Desactive les 'Appuyer sur entrée pour continuer' */
#define getchar() ('\n')

#else

#define eprintf(...) fprintf (stderr, __VA_ARGS__)

#endif

extern bool silent_mode;




struct cellule {
    char command;
    struct sequence* bloc; 
    struct cellule *suivant;
};
typedef struct cellule cellule_t;

struct sequence {
    cellule_t *tete;
};
typedef struct sequence sequence_t;

cellule_t* nouvelleCellule (void);

void detruireCellule (cellule_t*);

void conversion (char *texte, sequence_t *seq);

void afficher (sequence_t* seq);

void empiler(sequence_t* seq, char c); // j ai ajouter une cellule pour le debut de la liste
char depiler(sequence_t* seq); // supprime la premiere ccellule pour liberer la mimoire  

void empiler_bloc(sequence_t* seq, sequence_t* b);
sequence_t* depiler_bloc(sequence_t* seq);

#endif
