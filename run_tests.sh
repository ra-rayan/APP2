#!/bin/bash
# usage : ./run_tests.sh                     (tous les tests de tests/*.test)
#         ./run_tests.sh tests/a.test ...    (seulement ceux-là)

make -s || { echo "Compilation échouée"; exit 1; }

if [ $# -gt 0 ]; then
    fichiers=("$@")
else
    fichiers=(tests/*.test)
fi

reussis=()
rates=()

for f in "${fichiers[@]}"; do
    # yes "" répond aux "Appuyer sur entrée", timeout évite les boucles infinies
    sortie=$(yes "" | timeout 10 ./main "$f" 2>&1)
    code=$?

    nb_cartes=$(echo "$sortie" | grep -c "Lecture de la map")
    nb_ok=$(echo "$sortie" | grep -c "passée avec succès")

    if [ $code -ne 124 ] && [ "$nb_ok" -eq "$nb_cartes" ]; then
        reussis+=("$f")
    else
        rates+=("$f")
    fi
done

echo
echo "=== Réussis (${#reussis[@]}) ==="
printf '  %s\n' "${reussis[@]}"
echo "=== Ratés (${#rates[@]}) ==="
printf '  %s\n' "${rates[@]}"