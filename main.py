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

    # mettre dans les poules uniquement les joueurs non tetes de série lesquels intégrent directement le tournoi principal
    repartiteur = RepartiteurPoulesFixes([j for j in mes_joueurs if j.tete_de_serie == False], tailles_poules)
    #mes_poules = repartiteur.repartir_par_backtracking()
    mes_poules = repartiteur.repartir_par_recherche_locale()
    for poule in mes_poules:
        print(mes_poules)

## Simulation des gagnants de la poule et de la consolante
joueurs_tete_de_serie = [j for j in mes_joueurs if j.tete_de_serie]
joueurs_standard = [j for j in mes_joueurs if not j.tete_de_serie]

## selectionner les gagnants au hasard pour chaque poule
## créer le tableau pour le premier tour 
    
print("fin")