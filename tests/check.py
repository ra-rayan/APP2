#!/usr/bin/env python3

import sys
import os
import time
import argparse
from pathlib import Path
from subprocess import (
    check_output,
    run,
    Popen,
    PIPE,
    DEVNULL,
    CalledProcessError,
    TimeoutExpired,
)
import re

from enum import Enum

from typing import List, Tuple, NamedTuple

TSTDIR = Path(__file__).parent
TSTFILE = TSTDIR / "LISEZMOI.txt"
# MAINFILE = TSTDIR.parent / "LISEZMOI.txt"
MAINFILE = Path("LISEZMOI.txt")


class ValgrindChoice(Enum):
    NO_VALGRIND = 0
    VALGRIND_QUIET = 1
    VALGRIND_NORMAL = 2


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--silent", "-q", action="store_true", help="Pass -silent to program"
    )
    parser.add_argument(
        "--no-interactive",
        "-I",
        action="store_false",
        dest="interactive",
        help="Do not offer to re-run failed tests",
    )

    parser.add_argument("lang", choices=["c", "py"], help="Language to test")
    parser.add_argument(
        "--mem",
        action="store_const",
        default=ValgrindChoice.NO_VALGRIND,
        const=ValgrindChoice.VALGRIND_NORMAL,
        help="Check memory leaks using Valgrind (C only)",
    )
    parser.add_argument(
        "--mem-quiet",
        action="store_const",
        default=ValgrindChoice.NO_VALGRIND,
        const=ValgrindChoice.VALGRIND_QUIET,
        dest="mem",
        help="Check memory leaks using Valgrind without printing details (C only)",
    )

    parser.add_argument(
        "--evaluate",
        "-e",
        action="store_true",
        help="Evaluation mode: outputs results in spreadsheet-friendly format",
    )


    args = parser.parse_args()
    if args.lang != "c" and args.mem != ValgrindChoice.NO_VALGRIND:
        parser.error("--mem can only be provided with C language")
    return args


RED = check_output(["tput", "setaf", "1"], text=True)
GREEN = check_output(["tput", "setaf", "2"], text=True)
ORANGE = check_output(["tput", "setaf", "3"], text=True)
BLUE = check_output(["tput", "setaf", "4"], text=True) + check_output(
    ["tput", "bold"], text=True
)
NORMAL = check_output(["tput", "sgr0"], text=True)


def color(text, color):
    return "{}{}{}".format(color, text, NORMAL)


COL = int(check_output(["tput", "cols"]))
COL -= 20
if COL > 60:
    COL = 60

TIMEOUT = 2  # seconds allowed to complete
TIMEOUT_VALGRIND = 5  # seconds allowed to complete


def failed_test(name, info, txtcolor):
    print("\r", " " * COL, color(info, txtcolor), end="")
    print("\r    Test " + color(name, ORANGE), end="")
    print("\r" + color("[-]", RED))


def passed_test(name):
    print("\r", " " * COL, color("[pass]", GREEN), end="")
    print("\r    Test " + color(name, ORANGE), end="")
    print("\r" + color("[+]", GREEN))


class ValgrindResult(NamedTuple):
    errors: int
    definitely_lost: int
    indirectly_lost: int
    possibly_lost: int

    @classmethod
    def without_leaks_nor_errors(cls):
        return cls(0, 0, 0, 0)

    @staticmethod
    def _to_bytes(val: int) -> str:
        units = [" B", "KB", "MB", "GB"]
        shifts = 0
        while val > 1000 and shifts < len(units):
            shifts += 1
            val //= 1000
        return f"{val:>3}{units[shifts]}"

    @classmethod
    def _format_figure_gen(cls, val: int, s: str, colorize: bool = False) -> str:
        if colorize:
            return color(s, RED if val > 0 else GREEN)
        return out


    @classmethod
    def _format_figure(cls, val: int, colorize: bool = False) -> str:
        out = str(val)
        return cls._format_figure_gen(val, out, colorize)

    @classmethod
    def _format_figure_size(cls, val: int, colorize: bool = False) -> str:
        out = cls._to_bytes(val)
        return cls._format_figure_gen(val, out, colorize)

    def __str__(self):
        return self.to_str(colorize=False)

    def __bool__(self):
        return not any(self)

    def to_str(self, colorize=True):
        return "ERRORS: {} | LOST: {} | IND: {} | MAYBE: {}".format(
            self._format_figure(self.errors, colorize=colorize),
            self._format_figure_size(self.definitely_lost, colorize=colorize),
            self._format_figure_size(self.indirectly_lost, colorize=colorize),
            self._format_figure_size(self.possibly_lost, colorize=colorize),
        )


class CheckValgrindOutput:
    DEF_LOST_RE = re.compile(
        r"\sdefinitely lost: (?P<lost>[0-9,]+) bytes in (?P<blocks>[0-9,]+) blocks"
    )
    IND_LOST_RE = re.compile(
        r"\sindirectly lost: (?P<lost>[0-9,]+) bytes in (?P<blocks>[0-9,]+) blocks"
    )
    POSS_LOST_RE = re.compile(
        r"\spossibly lost: (?P<lost>[0-9,]+) bytes in (?P<blocks>[0-9,]+) blocks"
    )

    ERR_SUMM_RE = re.compile(
        r"\sERROR SUMMARY: ([0-9,]+) errors"
    )

    CLEAN_STR = "All heap blocks were freed -- no leaks are possible"

    class BadValgrindOutput(Exception):
        pass

    def _apply_re(self, stderr: str, rex: re.Pattern) -> Tuple[int, int]:
        res = rex.search(stderr)
        if res:
            return (
                int(res.group("lost").replace(",", "")),
                int(res.group("blocks").replace(",", "")),
            )
        raise self.BadValgrindOutput("Bad valgrind output")

    def __call__(self, stderr: str) -> ValgrindResult:
        merrors = self.ERR_SUMM_RE.search(stderr)
        if not merrors:
            raise self.BadValgrindOutput("Bad valgrind output")

        errors = int(merrors.groups()[0])
        if  errors == 0 and self.CLEAN_STR in stderr:
            return ValgrindResult.without_leaks_nor_errors()

        return ValgrindResult(
            errors,
            self._apply_re(stderr, self.DEF_LOST_RE)[0],
            self._apply_re(stderr, self.IND_LOST_RE)[0],
            self._apply_re(stderr, self.POSS_LOST_RE)[0],
        )


check_valgrind_output = CheckValgrindOutput()


def do_test(test_name, args) -> bool:
    use_valgrind = False
    capture_output = False
    silent = args.silent
    if args.mem != ValgrindChoice.NO_VALGRIND:
        use_valgrind = True
        capture_output = True


    main_prg="./main" if args.lang == "c" else "./main.py"
    main_cmd=main_prg if args.lang == "c" else "python3 " + main_prg + " -ascii"

    if not Path(main_prg).exists():
        print(f"Erreur: le programme principal {main_prg} n'a pas été trouvé")
        exit(1)

    test_file = TSTDIR / (test_name + ".test")

    if not test_file.exists():
        print(f"Erreur: le fichier de test {test_file} n'a pas été trouvé")
        exit(1)

    # using 'yes' command to cancel all keypresses waiting
    command = 'yes | {valgrind} {main} {silent} "{test}"'.format(
        valgrind="valgrind" if use_valgrind else "",
        main=main_cmd,
        silent="-silent" if silent else "",
        test=test_file,
    )

    print("\r    Test " + color(test_name, ORANGE), end="")
    try:
        run_result = run(
            command,
            shell=True,
            check=True,
            timeout=TIMEOUT_VALGRIND if use_valgrind else TIMEOUT,
            stdout=PIPE if capture_output else DEVNULL,
            stderr=PIPE if capture_output else DEVNULL,
            text=capture_output,
        )
        if use_valgrind:
            if args.mem == ValgrindChoice.VALGRIND_NORMAL:
                print(run_result.stderr)

            vg_out = check_valgrind_output(run_result.stderr)
            if not vg_out:
                if vg_out.errors > 0:
                    failed_test(test_name, "[ERRORS]", RED)
                else:
                    failed_test(test_name, "[LEAK]", ORANGE)
                out = vg_out.to_str(colorize=True)
                print(" " * 8 + out)
                return False

    except KeyboardInterrupt:
        failed_test(test_name, "[INTERRUPTED]", ORANGE)
        time.sleep(0.3)  # to allow double ctrl-C to stop whole script
        return False

    except TimeoutExpired:
        failed_test(test_name, "[TIMEOUT]", RED)
        return False

    except CalledProcessError as e:
        if e.returncode == 1:
            failed_test(test_name, "[FAIL]", RED)
        elif e.returncode == 2:
            failed_test(test_name, "[TRICHE]", RED)
        elif e.returncode == 127:
            failed_test(test_name, "[PROGRAM NOT FOUND]", RED)
        elif e.returncode == 134:
            failed_test(test_name, "[ASSERTION]", RED)
        elif e.returncode == 139:
            failed_test(test_name, "[SEGFAULT]", RED)
        else:
            failed_test(test_name, f"[SOME PROBLEM {e.returncode}]", RED)
        return False

    else:
        passed_test(test_name)
        return True

NAME_RE = re.compile(
    r"^Nom([1-9]) - prénom([1-9])\s:\s(.*)$"
)

def get_names():
    names = []
    print(f"Récupération des noms des membres du binôme depuis {MAINFILE}")
    try:
        with MAINFILE.open("r") as f:
            name_num = 0
            for line in f.readlines():
                res = NAME_RE.match(line)
                if res:
                    name_num += 1
                    x = res.group(1)
                    y = res.group(2)

                    if x != y:
                        print("Erreur: numéros de binôme différents entre nom et prénom sur la ligne suivante:", file=sys.stderr)
                        print("\t", line, sep='', file=sys.stderr)
                        exit(1)
                    if int(x) != name_num:
                        print(f"Erreur: numéro de binôme est {x} mais devrait être {name_num} sur la ligne suivante:", file=sys.stderr)
                        print("\t", line, sep='', file=sys.stderr)
                        exit(1)
                    if name_num == 3:
                        print(f"Attention: trinôme détecté. Les trinômes ne sont autorisés qu'exceptionnellement.", file=sys.stderr)
                        print(f"           assurez-vous de bien avoir l'accord de votre enseignant", file=sys.stderr)
                        print(f"           (appuyez sur 'Entrée' pour continuer tout de même)", file=sys.stderr, end='')
                        input()

                    if name_num > 3:
                        print(f"Erreur: trop de personnes dans le binôme.", file=sys.stderr)
                        print("\t", line, sep='', file=sys.stderr)
                        exit(1)

                    nom = res.group(3)
                    print("Binôme", name_num, ":", nom)
                    names.append(nom)
    except FileNotFoundError:
        print(f"Attention: fichier {MAINFILE} non trouvé. Merci de le joindre au")
        print(f"           rendu et d'y renseigner les noms du binôme.", file=sys.stderr)
        print(f"           (appuyez sur 'Entrée' pour continuer tout de même)", file=sys.stderr, end='')
        input()


    if "...." in names:
        print(f"Attention: noms de binômes non renseignés dans {MAINFILE}")
        print(f"           mettez les noms des membres du binôme pour suppprimer")
        print(f"           ce message")
        print(f"           (appuyez sur 'Entrée' pour continuer tout de même)", file=sys.stderr, end='')
        input()
    return names


bareme = [
    # (None, 'Acte I'),  ## do not actually put to avoid having two blank lines at beginning
    ('simple', 4),

    (None, 'Acte II'),
    ('calculs', 6),

    (None, 'Acte III'),
    ('mesures', None),
    ('marques', None),
    ('marques-et-mesures', None),
    ('copie', 8),

    (None, 'Acte IV'),
    ('if', 10),
    ('if-non-depile', 11),
    ('empile', 12),
    ('imbrique', 14),

    (None, 'Acte V'),
    ('exec', None),
    ('echanges', None),
    ('clones', (1,'add')),

    ('compteur', None),
    ('boucle', None),
    ('boucle-sans-pile', (1,'add')),

    (None, 'line-skip'),

    ('rotations', (0.5, 'add')),

    ('ifignore', None),
    ('boucle-if', None),
    ('boucle-clone', None),
    ('langton', (0.5, 'add')),

    (None, 'line-skip'),
    (None, 'line-skip'),
    (None, 'MANUAL'),
    (None, 'MANUAL'),
    (None, 'line-skip'),
    (None, {'c':'MANUAL', 'py':'n/a'}),

    (None, 'Acte Challenges'),
    ('mysterieuZe', (0.4,'challenge')),
    ('labyrinthe', (0.3, 'challenge')),
    ('surprise', (0.3, 'challenge')),
]

def generate_from_file(filename):
    with filename.open("r") as f:
        for line in f.readlines():
            if line.startswith("-"):
                test = line[1:].strip()
                yield test,None
            elif "Acte" in line:

                print(color("\n" + line + "=================", BLUE))


def generate_from_bareme(bareme):
    global evaluation
    for test_name, info in bareme:
        if test_name == None:
            if type(info) == dict:
                evaluation.append(info[args.lang])
            elif info == 'line-skip':
                evaluation.append("")
            elif info.startswith("Acte"):
                evaluation.append("")
                evaluation.append("")
            else:
                evaluation.append(info)
            continue

        yield test_name, info


evaluation = None
last_passed = None
has_failure = None
has_success = None
failed_milestone = None

def init_evaluation():
    global evaluation, has_failure, has_success, failed_milestone
    evaluation = []
    has_failure = False
    has_success = False
    failed_milestone = None

def add_evaluation(test, result, info):
    global evaluation, last_passed, has_failure, has_success, failed_milestone

    if result:
        res = '+'
        has_success = True
    else:
        res = '-'
        has_failure = True

    if info == None:
        evaluation.append(res)
        return


    if type(info) == int:
        if not result:
            if has_success:
                evaluation.append(f"{res} but some success before") # need to investigate manually
            else:
                evaluation.append(res)
            failed_milestone = len(evaluation)-1

        elif has_success and has_failure:
            evaluation.append(f"{res} but previous failed") # need to investigate manually

        else:
            assert has_success
            assert not has_failure

            # otherwise, success on this test: verify previous was also correct
            if failed_milestone == None:
                if last_passed != None:
                    # replace previous and keep only this grade
                    evaluation[last_passed] = '+'
                evaluation.append(str(info))
                last_passed = len(evaluation)-1

            else:
                was_last = evaluation[last_passed]
                evaluation.append("CORRECT but previous failed") # need to investigate manually

    else:
        assert type(info) == tuple
        grade, typ = info

        if not has_success:
            evaluation.append('-')

        elif not has_failure:
            evaluation.append(str(grade))

        else:
            evaluation.append(f"{res} and/but not all correct") # need to investigate manually


    # reset for next group of tests
    has_failure = False
    has_success = False



def show_evaluation(names):
    global evaluation

    print(f"Résultats pour {names} à copier dans un tableur:")
    res = '\n'.join(evaluation)
    print(res)
    os.system(f"echo '{res}' | xclip -i -sel c")
    print("<has been put into the clipboard>")





args = None

def main():
    global args
    args = parse_args()

    if args.mem == ValgrindChoice.VALGRIND_QUIET:
        args.silent = True

    failed: List[str] = []

    names = get_names()

    print(f"Répertoire de test: {TSTDIR}")
    print(f"Récupération des fichiers de tests depuis {TSTFILE}")

    test_num = -1
    res = []

    if args.evaluate:
        tests = generate_from_bareme(bareme)
        init_evaluation()
    else:
        tests = generate_from_file(TSTFILE)

    for test,info in tests:
        passed = do_test(test, args)

        if not passed:
            failed.append(test)

        if args.evaluate:
            add_evaluation(test, passed, info)

    print("Finished testing")

    if failed:
        print("************")
        print(color(" Failed tests: " + " ".join(failed), RED))
        print("************")

    if args.interactive:
        for t in failed:
            print("Press <q> to quit the tests")
            print("Press <r> to restart test '" + color(t, RED) + "' with output")
            print("(then press <q> to continue)")
            print("Press any other key to check the next failed test")
            key = input()
            if key == "r":
                out = run(
                    "yes | {} {} 2>&1 | less".format(
                        "./main" if args.lang == "c" else "python3 ./main.py -ascii",
                        TSTDIR / (t + ".test"),
                    ),
                    shell=True,
                )
                linecolor = ORANGE if out.returncode != 0 else GREEN
                print(color(f"-- Exited with status {out.returncode} --", linecolor))
            if key == "q":
                break

    if args.evaluate:
        show_evaluation(names)


if __name__ == "__main__":
    main()
