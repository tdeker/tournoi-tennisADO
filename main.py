from poule import *
import math

if __name__ == "__main__":
    print("debut")
    myPossiblePools = PoolConfigurationGenerator()
    myPossiblePools.displayPoolFullConfigurations()
    print(myPossiblePools.get_pool_sizes_list(23))
    mes_joueurs = creation_joueurs(23, 4)
    for joueur in mes_joueurs:
        print(joueur.prenom + " " + joueur.nom + "-" + str(joueur.niveau) + "-" + str(joueur.age) + "-" + str(joueur.tete_de_serie))
    # tester la génération de poules imposées
    tailles_poules = myPossiblePools.get_pool_sizes_list(23)
    ma_configuration_poule = myPossiblePools.plan_for_N_with_caps(23)
    print(f"le nombre de gagnant par poule:{ma_configuration_poule['Gagnants par poule (format 221)']}") 
    # ajouter une méthode qui calcul le nombre de gagant par poule 
    ## Simulation des gagnants de la poule et de la consolante
    joueurs_tete_de_serie = [j for j in mes_joueurs if j.tete_de_serie]
    joueurs_standard = [j for j in mes_joueurs if not j.tete_de_serie]
    print(f"joueurs non tête de série{joueurs_standard}")
    print(f"joueurs têtes de série : {joueurs_tete_de_serie}")
    # mettre dans les poules uniquement les joueurs non tetes de série lesquels intégrent directement le tournoi principal
    repartiteur = RepartiteurPoulesFixes( joueurs_standard, tailles_poules)
    mes_poules = repartiteur.repartir_par_backtracking()
    #mes_poules = repartiteur.repartir_par_recherche_locale()
    for i,poule in enumerate(mes_poules, start=1):
        print(f'Poule {i}: {poule}')


## selectionner les gagnants au hasard pour chaque poule
## créer le tableau pour le premier tour 
## crééer le tableau pour la consolante (avec joueurs by)
## prévoir de faire une tableau de consolante en placant avantageusement ceux qui ont le plus de point = le moins de jeu perdus ou bien la différence entre le nombre de match perdu et le nomnre de match gagné
    
print("fin")