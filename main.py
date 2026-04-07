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
    exit()
   
       # On récupère la liste des listes de joueurs
    liste_de_poules = mesMatchsDePoules.poules 
  

    # Paramètres d'affichage
    NB_POULES = len(liste_de_poules)
    LARGEUR_COLONNE = 35  # Ajustez selon la longueur des noms composés

    # 1. Affichage des en-têtes (Poule 1, Poule 2...)
    header = "".join([f"Poule {i+1}".ljust(LARGEUR_COLONNE) for i in range(NB_POULES)])
    print(header)
    print("-" * (LARGEUR_COLONNE * NB_POULES))

    # 2. Affichage des joueurs ligne par ligne
    # zip_longest va grouper le 1er joueur de chaque poule, puis le 2ème, etc.
    for une_poule in zip_longest(*[p.getJoueurs() for p in liste_de_poules], fillvalue=None):
        ligne_texte = ""
        for joueur in une_poule.getJoueurs():
            if joueur is not None:
                # Ici on utilise le formatage de votre __repr__
                texte_joueur = str(joueur)
            else:
                texte_joueur = ""
            
            ligne_texte += texte_joueur.ljust(LARGEUR_COLONNE)
        
        print(ligne_texte)

    exit()


## selectionner les gagnants au hasard pour chaque poule
## créer le tableau pour le premier tour 
## crééer le tableau pour la consolante (avec joueurs by)
## prévoir de faire une tableau de consolante en placant avantageusement ceux qui ont le plus de point = le moins de jeu perdus ou bien la différence entre le nombre de match perdu et le nomnre de match gagné
## Exporter les résultats dans un fichier excel
## exporter les résultats dans un fichier json
## afficher les résultats dans un tableau html

print("fin")