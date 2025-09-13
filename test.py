from poule import *
from collections import defaultdict, Counter
from joueur import *
import random
from typing import List, Dict, Tuple, Optional
import itertools


if __name__ == "__main__":
    print("debut")
    joueurs = creation_joueurs(16, 0)
    for joueur in joueurs:
        print(joueur.prenom + " " + joueur.nom + "-" + str(joueur.niveau) + "-" + str(joueur.age) + "-" + str(joueur.tete_de_serie))
    print(f"Nombre total de joueurs: {len(joueurs)}")
    print("Distribution par niveau:")
    niveaux = Counter(j.niveau for j in joueurs)
    for niveau in sorted(niveaux.keys(), reverse=True):
        print(f"  Niveau {niveau}: {niveaux[niveau]} joueurs")
    
    # Tailles de poules fixes : 4, 5, 3, 4 (total = 16)
    tailles_poules = [4, 5, 3, 4]
    print(f"\nTailles de poules imposées: {tailles_poules}")
    
    # Répartition avec backtracking
    repartiteur = RepartiteurPoulesFixes(joueurs, tailles_poules)
    print("\n🔍 Tentative par backtracking...")
    poules = repartiteur.repartir_par_backtracking()
    
    if poules:
        print("✅ Solution trouvée par backtracking!")
        repartiteur.afficher_resultats()
    else:
        print("❌ Pas de solution par backtracking. Tentative par recherche locale...")
        poules = repartiteur.repartir_par_recherche_locale()
        
        if poules:
            print("✅ Solution trouvée par recherche locale!")
            repartiteur.afficher_resultats()
        else:
            print("❌ Aucune solution trouvée. Les contraintes sont trop restrictives.")
            quit()
    
    # Vérification des contraintes
    print(f"\n=== VÉRIFICATION DES CONTRAINTES ===")
    contraintes_ok = True
    
    for i, poule in enumerate(poules):
        print(f"\nPoule {i+1}:")
        
        # Vérifier la taille
        if len(poule) != tailles_poules[i]:
            print(f"  ❌ Taille incorrecte: {len(poule)} au lieu de {tailles_poules[i]}")
            contraintes_ok = False
        else:
            print(f"  ✅ Taille correcte: {len(poule)}")
        
        if poule:
            niveaux = [j.niveau for j in poule]
            familles = [j.nom for j in poule]
            
            # Vérifier contrainte de niveau
            ecart = max(niveaux) - min(niveaux)
            if ecart > 1:
                print(f"  ❌ Écart de niveau > 1: {min(niveaux)}-{max(niveaux)} (écart: {ecart})")
                contraintes_ok = False
            else:
                print(f"  ✅ Écart de niveau OK: {min(niveaux)}-{max(niveaux)} (écart: {ecart})")
            
            # Vérifier contrainte familiale
            if len(familles) != len(set(familles)):
                familles_dupliquees = [f for f in set(familles) if familles.count(f) > 1]
                print(f"  ❌ Familles en double: {familles_dupliquees}")
                contraintes_ok = False
            else:
                print(f"  ✅ Pas de conflit familial")
    
    if contraintes_ok:
        print(f"\n🎉 TOUTES LES CONTRAINTES SONT RESPECTÉES!")
    else:
        print(f"\n⚠️  Certaines contraintes ne sont pas respectées.")
    print("fin")