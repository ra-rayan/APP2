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
    //int ret;
    
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
        
        sequence_t *bloc_cel = seq->tete->bloc;
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
                empiler_bloc(&pile, bloc_cel);
                break;}
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
                case 'X':
                {
                    echanger_2elem_sommet(&pile);
                    break;
                }
                case '!':
                    {sequence_t* bloc = depiler_bloc(&pile);
                    inserer_en_tete(seq, bloc);
                    break;
                }
                case 'B':
                {   int n=depiler(&pile);
                    sequence_t* cmd = depiler_bloc(&pile);
                    if (n > 0) {
                            sequence_t* copie = cloner_bloc(cmd);
                            empiler_bloc(&pile, cmd);
                            empiler(&pile, n - 1);
                            cellule_t* b = nouvelleCellule();
                            b->command = 'B';
                            b->suivant = seq->tete;
                            seq->tete = b;                         
                            inserer_en_tete(seq, copie); 
                            free(copie);
                            } 
                            else {
                                while (cmd->tete != NULL) depiler(cmd);
                                free(cmd);
                                }
                            break;
                            }
                case 'R':
                {
                    int x = depiler(&pile);
                    int n = depiler(&pile);
                    if (n <= 0) break;
                    x = ((x % n) + n) % n;
                    cellule_t** tab = malloc(n * sizeof(cellule_t*));
                    for (int i = n - 1; i >= 0; i--) {
                        assert(pile.tete != NULL);
                        tab[i] = pile.tete;
                        pile.tete = pile.tete->suivant;
                    }
                    for (int i = 0; i < n; i++) {
                        cellule_t* c = tab[(i + x) % n];
                        c->suivant = pile.tete;
                        pile.tete = c;
                    }
                    free(tab);
                    break;
                }
                case 'C':
                {
                    if (sommet_est_bloc(&pile)) {
                        sequence_t* b = depiler_bloc(&pile);
                        sequence_t* copie = cloner_bloc(b);
                        empiler_bloc(&pile, b);
                        empiler_bloc(&pile, copie);
                    } else {
                        int v = depiler(&pile);
                        empiler(&pile, v);
                        empiler(&pile, v);
                    }
                    break;
                }
                case 'I':
                {
                    if (sommet_est_bloc(&pile)) {
                        detruire_bloc(depiler_bloc(&pile));
                    } else {
                        depiler(&pile);
                    }
                    break;
                }
                case 'A':
                    {int ret = avance();
                    if (ret == VICTOIRE) return VICTOIRE;
                    if (ret == RATE)     return RATE;
                    break;
                }
                case 'G':
                    {gauche();
                    break;
                }
                case 'D':
                    {droite();
                    break;
                }
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
