from poule import *
from itertools import zip_longest
import math
from dotenv import load_dotenv
import os
from pyairtable import Api


if __name__ == "__main__":
## Récupération des joueurs depuis Airtable
    load_dotenv()  # charge le fichier .env
    AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
    BASE_ID        = os.getenv("BASE_ID")
    print(BASE_ID)
    monApiAT = Api(AIRTABLE_TOKEN)
    tableJoueur = monApiAT.table(BASE_ID, "Joueur")
    records = tableJoueur.all()
    # Convertir en liste de Joueur
    def records_to_joueurs(records) -> list[Joueur]:
        joueurs = []
        for record in records:
            f = record["fields"]
            joueur = Joueur(
                name         = f.get("Prénom", ""),
                familyName   = f.get("Nom", ""),
                sexe         = f.get("Sexe", "M"),
                age          = f.get("Age", 0),
                niveau       = int(f.get("Niveau")),
                seededPlayer = f.get("Seed", False),
            )
            joueurs.append(joueur)
        return joueurs   
    maListeDeJoueurs = records_to_joueurs(records)

   ## Création et provisionning des Poules
    for joueur in maListeDeJoueurs:
     print(joueur.prenom + " " + joueur.nom + "-" + str(joueur.niveau) + "-" + str(joueur.age) + "-" + str(joueur.tete_de_serie))  
    nbInscris=len(maListeDeJoueurs)
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
## importer la liste des joueur depuis un fichier Excel ou csv
## chargement de la liste des joueurs dans supabase  avec les données d'entrée, le nombre de point et les adversaire
## Exporter les résultats dans un fichier excel
## exporter les résultats dans un fichier json
## afficher les résultats dans un tableau html
## faire un webservice en python avec flask et flask_restful
## faire le front end
