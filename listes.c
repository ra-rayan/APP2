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


cellule_t* nouvelleCellule (void)
{
    cellule_t *cel=malloc(sizeof(cellule_t));
    cel->suivant=NULL;
    cel->command='\0';
    return cel;
    printf("\n>>>>>>>>>>> A Faire : liste.c/nouvelleCellule() <<<<<<<<<<<<<<<<\n");
    return NULL;
}


void detruireCellule (cellule_t* cel)
{
    free(cel);
    printf("\n>>>>>>>>>>> A Faire : liste.c/detruireCellule() <<<<<<<<<<<<<<<<\n");
}


/* Attention: seq est utilisée pour une "valeur de retour", pour y stocker la 
 * séquence. Donc il n'y a pas de garantie sur son état, en particulier 
 * seq->tete peut ne pas être initialisée à NULL.
 */
void conversion (char *texte, sequence_t *seq)
{
  cellule_t *queue=seq->tete;
  int i=0;
  while (texte[i]!='\0'){
    queue=nouvelleCellule;
    queue->command=texte[i];
    queue->suivant;
  }

    printf("\n>>>>>>>>>>> A Faire : liste.c/conversion() <<<<<<<<<<<<<<<<\n");
}



void rec_aff(cellule_t *cel){
    if (cel!=NULL){
        printf("%c ",cel->command);
        rec_aff(cel->suivant);
    }
    
}


void afficher (sequence_t* seq)
{
    assert (seq);
    rec_aff(seq->tete);
     /* Le pointeur doit être valide */   
}

