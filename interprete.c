#include <stdio.h>
#include <stdbool.h>
#include <assert.h>
#include <stdlib.h>
#ifdef NCURSES
#include <ncurses.h>
#endif
#include "listes.h"
#include "curiosity.h"

/*
 *  Auteur(s) :
 *  Date :
 *  Suivi des Modifications :
 *
 */

void stop (void)
{
    char enter = '\0';
    printf ("Appuyer sur entrée pour continuer...\n");
    while (enter != '\r' && enter != '\n') { enter = getchar(); }
}

int interprete (sequence_t* seq, bool debug)
{
    char commande;
    int ret;
    
    sequence_t pile;
    pile.tete = NULL;

    debug = true; /* À enlever par la suite et utiliser "-d" sur la ligne de commandes */
    
    /* L'affichage est désactivé en mode silencieux */
    if (! silent_mode) {
        printf ("Programme:");
        afficher(seq);
        printf ("\n");
        if (debug) stop();
    }

    while (seq->tete != NULL) {
        
        commande = depiler(seq);

        if (commande >= '0' && commande <= '9') {
            empiler(&pile, commande - '0'); 
        } 
        else {
            switch (commande) {
                case '+':
                {
                    int b = depiler(&pile);
                    int a = depiler(&pile);
                    empiler(&pile, a + b);
                    break;
                }
                case '-':
                {
                    int b = depiler(&pile);
                    int a = depiler(&pile);
                    empiler(&pile, a - b);
                    break;
                }
                case '*':
                {
                    int b = depiler(&pile);
                    int a = depiler(&pile);
                    empiler(&pile, a * b);
                    break;
                }
                case 'P':
                {
                    int arg = depiler(&pile);
                    pose(arg);
                    break;
                }
                case 'M':
                {
                    int dir = depiler(&pile);
                    int res = mesure(dir);
                    empiler(&pile, res);
                    break;
                }
                case '{':
                {
                    sequence_t* bloc = malloc(sizeof(sequence_t));
                    bloc->tete = NULL;
                    
                    int nb_accolades = 1;
                    cellule_t* courant = NULL;

                    while (seq->tete != NULL && nb_accolades > 0) {
                        char c = depiler(seq);
                        
                        if (c == '{') nb_accolades++;
                        if (c == '}') nb_accolades--;

                        if (nb_accolades > 0) {
                            cellule_t* nouv = nouvelleCellule();
                            nouv->command = c;
                            if (bloc->tete == NULL) {
                                bloc->tete = nouv;
                                courant = nouv;
                            } else {
                                courant->suivant = nouv;
                                courant = nouv;
                            }
                        }
                    }
                    empiler_bloc(&pile, bloc);
                    break;
                }
                case '?':
                {
                    sequence_t* blocF = depiler_bloc(&pile);
                    sequence_t* blocV = depiler_bloc(&pile);
                    int condition = depiler(&pile);

                    sequence_t* a_executer = (condition != 0) ? blocV : blocF;
                    sequence_t* a_ignorer = (condition != 0) ? blocF : blocV;

                    if (a_executer != NULL && a_executer->tete != NULL) {
                        cellule_t* fin = a_executer->tete;
                        while (fin->suivant != NULL) {
                            fin = fin->suivant;
                        }
                        fin->suivant = seq->tete;
                        seq->tete = a_executer->tete;
                        free(a_executer);
                    }

                    if (a_ignorer != NULL) {
                        while (a_ignorer->tete != NULL) {
                            depiler(a_ignorer);
                        }
                        free(a_ignorer);
                    }
                    break;
                }
                case 'A':
                    ret = avance();
                    if (ret == VICTOIRE) return VICTOIRE;
                    if (ret == RATE)     return RATE;
                    break;
                case 'G':
                    gauche();
                    break;
                case 'D':
                    droite();
                    break;
                case ' ':
                case '\n':
                    break;
                default:
                    eprintf("Caractère inconnu: '%c'\n", commande);
            }
        }

        /* Affichage pour faciliter le debug */
        if (! silent_mode) {
            afficherCarte();
            printf ("Programme restant : ");
            afficher(seq);
            printf ("\n");
            if (debug) stop();
        }
    }

    /* Si on sort de la boucle sans arriver sur la cible, c'est raté :-( */
    return CIBLERATEE;
}
