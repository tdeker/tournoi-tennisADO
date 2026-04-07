from poule import *
from itertools import zip_longest
import math

if __name__ == "__main__":
    nbInscris=27
    nbSeed=4
    print("debut")
    maListeDeJoueurs = creation_joueurs_avec_nom_famille(nbInscris,nbSeed) 
    for joueur in maListeDeJoueurs:
     print(joueur.prenom + " " + joueur.nom + "-" + str(joueur.niveau) + "-" + str(joueur.age) + "-" + str(joueur.tete_de_serie))  
    mesPoules = PoolConfigurationGeneratorByTristan(nbInscris,1)
    print(f'nombre de gagnant par poule:{mesPoules.get_winners_per_pool()}')
    print(mesPoules.get_pool_sizes_list())
    mesMatchsDePoules = RepartiteurPoulesFixes(maListeDeJoueurs, mesPoules.get_pool_sizes_list())
    mesMatchsDePoules.repartir_par_couts_TK(maListeDeJoueurs)
    mesMatchsDePoules.afficher_resultats()

## selectionner les gagnants au hasard pour chaque poule
## créer le tableau pour le premier tour 
## crééer le tableau pour la consolante (avec joueurs by)
## prévoir de faire une tableau de consolante en placant avantageusement ceux qui ont le plus de point = le moins de jeu perdus ou bien la différence entre le ngit statuombre de match perdu et le nomnre de match gagné
## Exporter les résultats dans un fichier excel
## exporter les résultats dans un fichier json
## afficher les résultats dans un tableau html
