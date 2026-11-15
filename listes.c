#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <assert.h>
#include <string.h>
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

bool silent_mode = true;


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
    if (texte == NULL || texte[0] == '\0') return;

    size_t len = strlen(texte);
    sequence_t **blocs = malloc((len + 1) * sizeof(sequence_t*));
    cellule_t **fins = malloc((len + 1) * sizeof(cellule_t*));
    int prof = 0;
    blocs[0] = seq;
    fins[0] = NULL;

    for (int i = 0; texte[i] != '\0'; i++) {
        char c = texte[i];

        if (c == '}') {
            if (prof > 0) prof--;
            continue;
        }

        cellule_t *nouv = nouvelleCellule();
        nouv->command = c;

        if (fins[prof] == NULL) blocs[prof]->tete = nouv;
        else fins[prof]->suivant = nouv;
        fins[prof] = nouv;

        if (c == '{') {
            sequence_t *b = malloc(sizeof(sequence_t));
            b->tete = NULL;
            nouv->bloc = b;
            prof++;
            blocs[prof] = b;
            fins[prof] = NULL;
        }
    }
    free(blocs);
    free(fins);
}


void afficher(sequence_t* seq) {
    assert(seq);
    for (cellule_t *c = seq->tete; c != NULL; c = c->suivant) {
        if (c->bloc != NULL) { printf("{"); afficher(c->bloc); printf("}"); }
        else printf("%c", c->command);
    }
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
    if (seq->tete == NULL || seq->tete->bloc == NULL) return NULL;
    cellule_t* a_supprimer = seq->tete;
    sequence_t* valeur_bloc = a_supprimer->bloc;
    seq->tete = a_supprimer->suivant;
    detruireCellule(a_supprimer);
    return valeur_bloc;
}
void echanger_2elem_sommet(sequence_t *pile) {
    if (pile->tete == NULL || pile->tete->suivant == NULL) return;
    cellule_t *a = pile->tete;       
    cellule_t *b = a->suivant;     
    a->suivant = b->suivant;
    b->suivant = a;
    pile->tete = b;
}
void inserer_en_tete(sequence_t *routine, sequence_t *bloc){
    
    assert(routine != NULL);
    assert(bloc != NULL);
    if (bloc->tete == NULL) {
        free(bloc);
        return;
    }
    cellule_t *c = bloc->tete;
    while (c->suivant != NULL) c = c->suivant;
    c->suivant = routine->tete;
    routine->tete = bloc->tete;
    bloc->tete = NULL;
    free(bloc);
}

sequence_t* cloner_bloc(sequence_t* src) {
    assert(src != NULL);
    sequence_t* copie = malloc(sizeof(sequence_t));
    copie->tete = NULL;
    cellule_t* fin = NULL;
    for (cellule_t* c = src->tete; c != NULL; c = c->suivant) {
        cellule_t* nouv = nouvelleCellule();
        nouv->command = c->command;
        if (c->bloc != NULL) nouv->bloc = cloner_bloc(c->bloc);
        if (fin == NULL) copie->tete = nouv; else fin->suivant = nouv;
        fin = nouv;
    }
    return copie;
}
bool sommet_est_bloc(sequence_t *pile) {
    return pile->tete != NULL && pile->tete->bloc != NULL;
}
void detruire_bloc(sequence_t *b) {
    assert(b != NULL);
    cellule_t *c = b->tete;
    while (c != NULL) {
        cellule_t *suiv = c->suivant;
        if (c->bloc != NULL) detruire_bloc(c->bloc);
        detruireCellule(c);
        c = suiv;
    }
    free(b);
}
