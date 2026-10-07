#!/usr/bin/env python3
#
# Script de test de performances.
# A lancer depuis le repertoire de travail principal de l'APP ainsi:
#
# Pour la version C :
# ./tests/performance/perf.py c
#
# Pour la version python :
# ./tests/performance/perf.py c
#

import sys
import os
import subprocess
import json
import argparse

from drawgraph import drawgraph

DEBUG=False
# DEBUG=True
TIMEOUT = 10

def debug(*args):
    if (DEBUG):
        print("".join(args))

c_prog = 'main'
c_prefix = './'
py_prog = 'main.py'
py_prefix = 'python3 '

prog = None


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description = """
Tests de performance pour l'APP2. Le choix du langage se fait en ligne de commande:

    c   (pour tester l'implementation C)
    py  (pour tester l'implementation Python)
    gen (pour générer des fichiers de tests)

Il est possible de tester une seule suite de tests de performance parmi: base,long,nested,memfree,piiile
Par défault, toutes les suites de tests sont lancées.

ATTENTION : l'affichage dans vos programmes peut prendre beaucoup
de temps. Désactivez vos affichages ('print') en commentant les
lignes concernées, ou mieux en les mettant dans des blocs conditionnels.

En python:
         if not curiosity.silent_mode:
             <mettre ici votre code d'affichage>

En C:
         if (! silent_mode) {
             <mettre ici votre code d'affichage>
         }

Il faut également désactiver les attentes clavier (messages type
"Appuyer sur entrée pour continuer...") en enlevant la ligne "debug = true"
de la fonction ``interprete''.

"""
    )

    parser.add_argument(
        "--timeout", "-t",
        type=int,
        help="Change timeout",
        default=TIMEOUT
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Debug mode",
    )

    parser.add_argument("lang", choices=["c", "py", "gen"], help="Langage à tester")
    parser.add_argument("suite",
                        choices=["base", "long", "nested", "memfree", "piiile"],
                        help="suite de tests de performance",
                        default=None,
                        nargs='?'
                        )

    args = parser.parse_args()

    return args



if __name__ == "__main__":
    # if len (sys.argv) == 1:
        # help()

    gen = False

    args = parse_args()

    DEBUG = args.debug
    TIMEOUT = args.timeout

    if args.lang == "c":
        prog = c_prog
        prefix = c_prefix
        options = " -silent "
    elif args.lang == "py":
        prog = py_prog
        prefix = py_prefix
        options = " -ascii -silent "
    elif args.lang == "gen":
        gen = True
    else:
        print ("Erreur: mauvais argument", args.lang)

    to_test = args.suite


if prog and not os.path.exists(prog):
    print ("Erreur: impossible de trouver le programme '" + prog + "'")
    print ("Ce scrit est a lancer depuis le répertoire principal de travail de l'APP ainsi:")
    print ("./tests/performance/perf.py <c ou py>")
    exit(1)


perfdir=os.path.dirname(sys.argv[0])

# genprog = "./" + perfdir + "/gen-test.py"
genprog = os.path.join(perfdir, "gen-test.py")


time = subprocess.check_output("which -a time | grep -v shell | tail -n 1", shell=True)
time = time.decode().rstrip()
# timecmd = " time -f '\tTemps: %es  Mémoire max: %MKb' "
timecmd = time + " -f '%e;%M' "

timeoutcmd = "timeout " + str(TIMEOUT) + "s "

def run_test(mode, message):
    msg =  "Running tests mode " + mode + " " + message
    print ("*" * len(msg))
    print (msg)

    size_curves = []
    temps_curves = []
    memoire_curves = []
    size = 1000
    size_max = 10000000

    tmppipe=os.popen("mktemp --tmpdir -u $USER.XXXXXXXXX.fifo").read().strip()
    debug("Pipe is", tmppipe)
    os.system("mkfifo -m 600 " + tmppipe)

    ret = None
    while ret == None and size < size_max:
        print ("Size ", "{:10}".format(size))


        if gen :
            f = "> perfs/test" + mode + str(size) + ".test"
        else:
            f = " > " + tmppipe + " &"

        # os.system("mkfifo /tmp/fifo")
        generation = "python3 " + genprog + " -s " + str(size) + " -m " + mode + f
        result = os.system(generation)
        debug("Executed: " + generation + " with result " + str(result))

        if not gen:

            command = timecmd + timeoutcmd + prefix + prog + options + " " + tmppipe + " >/dev/null"

            try:
                debug("Executing: ", command)
                result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
                result = result.decode().rstrip()
                parts = result.split(';', 2)
                temps = parts[0]
                memoire = str(int(parts[1]) / (1024*1024))
                print ("\tTemps: {}s  Mémoire max: {:.2f} GB".format(temps, float(memoire)))

                size_curves.append(size)
                temps_curves.append(float(temps))
                memoire_curves.append(float(memoire))
            except subprocess.CalledProcessError as e:
                debug (f"Error, return code {e.returncode}")
                if e.returncode == 1:
                    ret = "Erreur programme"
                elif e.returncode == 124:
                    ret = "Timeout after "+ str(TIMEOUT) +" seconds"
                elif e.returncode == 127:
                    ret = f"Command not found: {prog}"
                elif e.returncode == 134:
                    ret = "Assertion Failed"
                elif e.returncode == 139:
                    ret = "Segmentation Fault"
                else:
                    ret = f"Unexpected error {e.returncode} and {e=}"
            except KeyboardInterrupt:
                print ("Interruption clavier")
                ret = "Interrupted"

        size*=2

    os.remove(tmppipe)

    if ret != None:
        print ("Problem with last size:", ret)
    drawgraph(size_curves, temps_curves, memoire_curves, mode)

all_tests = {
    "base": "(très long sans blocs)",
    "long": "(très long, beaucoup de blocs)",
    "nested": "(très long, beaucoup de blocs imbriqués)",
    "memfree": "(boucle exécutée de nombreuses fois)",
    "piiile": "(très grande pile)",
    }


if __name__ == "__main__":
    try:
        if to_test:
            if not to_test in all_tests:
                print ("Type de test inconnu:", to_test)
                print ("Allowed tests:")
                print (json.dumps(all_tests,indent=4))
                exit (1)
            run_test (to_test, all_tests[to_test])
        else:
            for t in all_tests:
                run_test (t, all_tests[t])
    except KeyboardInterrupt:
        print("Interrupted twice, aborting...")
        exit(1)
