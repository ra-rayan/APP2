#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <assert.h>
#ifdef NCURSES
#include <ncurses.h>
#endif
#include "listes.h"


/*
 *  Auteur(s) :
 *  Date :
 *  Suivi des Modifications :
 *
 */

bool silent_mode = false;


cellule_t* nouvelleCellule (void) {
    cellule_t *cel = malloc(sizeof(cellule_t));
    if (cel == NULL) return NULL; 
    cel->suivant = NULL; 
    cel->command = '\0';
    cel->bloc = NULL; 
    return cel;
}

void detruireCellule (cellule_t* cel)
    {free(cel);
}   


/* Attention: seq est utilisée pour une "valeur de retour", pour y stocker la 
 * séquence. Donc il n'y a pas de garantie sur son état, en particulier 
 * seq->tete peut ne pas être initialisée à NULL.
 */
void conversion(char *texte, sequence_t *seq) {
    seq->tete = NULL;
    
    if (texte == NULL || texte[0] == '\0') {
        return; // Si le texte est vide, on s'arrête là
    }

    int i = 0;
    cellule_t *courant = NULL;

    while (texte[i] != '\0') {
        cellule_t *nouveau = nouvelleCellule();
        nouveau->command = texte[i];

        if (seq->tete == NULL) {
            seq->tete = nouveau;
            courant = nouveau;
        } else {
            courant->suivant = nouveau;
            courant = nouveau; // avance
        }
        i++;
    }
}



void rec_aff(cellule_t *cel){
    if (cel != NULL){
        printf("%c", cel->command); 
        rec_aff(cel->suivant);
    }
}


void afficher (sequence_t* seq)
{
    assert (seq);
    rec_aff(seq->tete);
       
}

void empiler(sequence_t* seq, char c) {
    cellule_t* nouvelle = nouvelleCellule();
    nouvelle->command = c;
    nouvelle->suivant = seq->tete;
    seq->tete = nouvelle;
}

char depiler(sequence_t* seq) {
    if (seq->tete == NULL) {
        return '\0'; 
    }
    cellule_t* a_supprimer = seq->tete;
    char valeur = a_supprimer->command;
    seq->tete = a_supprimer->suivant;
    detruireCellule(a_supprimer);
    return valeur;
}

void empiler_bloc(sequence_t* seq, sequence_t* b) {
    cellule_t* nouvelle = nouvelleCellule();
    nouvelle->bloc = b;
    nouvelle->command = '{'; 
    nouvelle->suivant = seq->tete;
    seq->tete = nouvelle;
}

sequence_t* depiler_bloc(sequence_t* seq) {
    if (seq->tete == NULL || seq->tete->command != '{') {
        return NULL; 
    }
    cellule_t* a_supprimer = seq->tete;
    sequence_t* valeur_bloc = a_supprimer->bloc;
    seq->tete = a_supprimer->suivant;
    detruireCellule(a_supprimer);
    return valeur_bloc;
}
