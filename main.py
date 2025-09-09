from Poules import *

if __name__ == "__main__":
    print("debut")
    #myPossiblePools = PoolConfigurationGenerator()
    #myPossiblePools.displayPoolConfigurations()
    joueurs = creation_joueurs(16, 4)
    for joueur in joueurs:
        print(joueur.prenom + " " + joueur.nom + "-" + str(joueur.niveau) + "-" + str(joueur.age) + "-" + str(joueur.tete_de_serie))
    print("fin")
    # tester la génération de poules imposées
    tailles_poules = [4, 5, 3, 4]
    repartiteur = RepartiteurPoulesFixes(joueurs, tailles_poules)
    poules = repartiteur.repartir_par_backtracking()
    for poule in poules:
        print(poule)
    print("fin")