from poule import *
from utiles import *
from itertools import zip_longest
import math
from dotenv import load_dotenv
import os
from pyairtable import Api
import hashlib



if __name__ == "__main__":
## Récupération des joueurs depuis Airtable
    load_dotenv()  # charge le fichier .env
    AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
    BASE_ID        = os.getenv("BASE_ID")
    monApiAT = Api(AIRTABLE_TOKEN)
    tableJoueur = monApiAT.table(BASE_ID, "Joueur")
    tablePoule = monApiAT.table(BASE_ID,"Poule")
    tablePoule_Joueur = monApiAT.table(BASE_ID,"Poule_Joueur")

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
    maListeDeJoueursFeminin: List[Joueur] = []
    maListeDeJoueursMasculin: List[Joueur] = []
   ### Effacer les poules créées précédement
    records = tablePoule.all()
    ids = [record["id"] for record in records]
    tablePoule.batch_delete(ids)
    records = tablePoule_Joueur.all()
    ids = [record["id"] for record in records]
    tablePoule_Joueur.batch_delete(ids)
   ### Création des poules
    for joueurCourant in maListeDeJoueurs:
      print(joueurCourant.prenom + " " + joueurCourant.nom + "-" + str(joueurCourant.niveau) + "-" + str(joueurCourant.age) + "-" + str(joueurCourant.tete_de_serie))  
      if joueurCourant.sexe == "F" :
       maListeDeJoueursFeminin.append(joueurCourant)
      else :
       maListeDeJoueursMasculin.append(joueurCourant)

    for monSexeCourant, maListeDeJoueurCourante in zip(["F", "M"], [maListeDeJoueursFeminin, maListeDeJoueursMasculin]):
      nbInscris=len(maListeDeJoueurCourante)
      maConfigurationPoule = PoolConfigurationGeneratorByTristan(nbInscris,1)
      print(f'nombre de gagnant par poule:{maConfigurationPoule.get_winners_per_pool()}')
      print(maConfigurationPoule.get_pool_sizes_list())
      mesMatchsDePoules = RepartiteurPoulesFixes(maListeDeJoueurCourante, maConfigurationPoule,monSexeCourant)
      mesMatchsDePoules.repartir_par_couts_TK(maListeDeJoueurCourante)
      mesMatchsDePoules.afficher_resultats()
    ### Provisionning des Poules dans Airtable
    #### Provisionning des poules des joueurs dans les poules
      for i, unePoule in enumerate(mesMatchsDePoules.get_Poules(), start=0):
          print(f'Building Poule {unePoule.name}')
          tablePoule.create({
              "Nom" : str(unePoule.name),
              "nb_gagnant" : int(mesMatchsDePoules.nb_gagnants[i]),
              "nb_joueurs" : int(unePoule.nb_joueurs),
              "lieu" : str(unePoule.lieu),
          })
          for unJoueur in unePoule.getJoueurs():
            records = tableJoueur.all(formula=f"{{codejoueur}}='{unJoueur.code}'")
            if not records:
                raise ValueError(f"Joueur introuvable : {unJoueur.code}")
            tablePoule_Joueur.create({
              "Poule" : str(unePoule.name),
              "CodeJoueur" : [records[0]["id"]]
          })



## tester la répartition avec la liste des joueurs de 2025 pour voir si OK
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
