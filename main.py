from poule import *
from utiles import *
from itertools import zip_longest
import math
from dotenv import load_dotenv
import os
from pyairtable import Api
import hashlib
import json


if __name__ == "__main__":
    """
    ## Test de nouvels évolutions sans impacter le code
    ### Création de la list des joueurs
        joueurs = [
            Joueur(prenom="Alice",   nom="Martin",   sexe="F", age=25, niveau=5, zone=1, tete_de_serie=True),
            Joueur(prenom="Bob",     nom="Martin",   sexe="M", age=27, niveau=3, zone=1),  # même famille qu'Alice
            Joueur(prenom="Claire",  nom="Dupont",   sexe="F", age=30, niveau=4, zone=2),
            Joueur(prenom="David",   nom="Dupont",   sexe="M", age=28, niveau=2, zone=2),  # même famille que Claire
            Joueur(prenom="Eva",     nom="Leblanc",  sexe="F", age=24, niveau=1, zone=1),
            Joueur(prenom="Frank",   nom="Moreau",   sexe="M", age=35, niveau=5, zone=3, tete_de_serie=True),
            Joueur(prenom="Grace",   nom="Simon",    sexe="F", age=33, niveau=3, zone=3),
            Joueur(prenom="Hugo",    nom="Bernard",  sexe="M", age=40, niveau=2, zone=4),
            Joueur(prenom="Iris",    nom="Thomas",   sexe="F", age=38, niveau=4, zone=4),
            Joueur(prenom="Jules",   nom="Richard",  sexe="M", age=22, niveau=1, zone=5),
            Joueur(prenom="Karen",   nom="Petit",    sexe="F", age=29, niveau=5, zone=2, tete_de_serie=True),
            Joueur(prenom="Leo",     nom="Robert",   sexe="M", age=32, niveau=2, zone=3),
            Joueur(prenom="Marie",   nom="Bernard",  sexe="F", age=41, niveau=3, zone=4),  # même famille qu'Hugo
            Joueur(prenom="Nathan",  nom="Leroy",    sexe="M", age=19, niveau=1, zone=5),
            Joueur(prenom="Olivia",  nom="Girard",   sexe="F", age=26, niveau=4, zone=1),
            Joueur(prenom="Paul",    nom="Leroy",    sexe="M", age=21, niveau=2, zone=5),  # même famille que Nathan
            Joueur(prenom="Sophie",  nom="Moreau",   sexe="F", age=36, niveau=4, zone=3),  # même famille que Frank
        ]
    
        ### Création de la liste des poules
        nbInscris = len(joueurs)
        maConfigurationPoule = PoolConfigurationGeneratorByTristan(nbInscris,1)
        print(f'nombre de gagnant par poule:{maConfigurationPoule.get_winners_per_pool()}')
        print(maConfigurationPoule.get_pool_sizes_list())
        ### Allocation des joueurs dans les poules
        poules = maConfigurationPoule.poules
        alloc = AllocationJoueur(poules=poules, joueurs=joueurs)
        alloc.allouer()
        alloc.afficher_resultat()
        print("\n📊 Diagnostics détaillés :")
        print(json.dumps(alloc.diagnostics(), indent=2, ensure_ascii=False))

        exit()
    """
    load_dotenv()  # charge le fichier .env
    AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
    BASE_ID        = os.getenv("BASE_ID")
    monApiAT = Api(AIRTABLE_TOKEN)   
    tableJoueur = monApiAT.table(BASE_ID, "Joueur")
    tablePoule = monApiAT.table(BASE_ID,"Poule")
    tablePoule_Joueur = monApiAT.table(BASE_ID,"Poule_Joueur")


    records = tableJoueur.all()
    
    def records_to_joueurs(records) -> list[Joueur]:
        joueurs = []
        for record in records:
            f = record["fields"]
            joueur = Joueur(
                prenom       = f.get("Prénom", ""),
                nom          = f.get("Nom", ""),
                sexe         = f.get("Sexe", "M"),
                age          = f.get("Age", 0),
                niveau       = int(f.get("Niveau")) if f.get("Niveau") is not None else None,
                zone         = int(f.get("Zone"))   if f.get("Zone")   is not None else None,
                tete_de_serie = f.get("Seed", False),
                id           = f.get("CodeJoueur", "")
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

   ### Création des poules et allocation des joueurs aux poules
    for joueurCourant in maListeDeJoueurs:
      print(joueurCourant.prenom + " " + joueurCourant.nom + "-" + str(joueurCourant.niveau) + "-" + str(joueurCourant.age) + "-" + str(joueurCourant.tete_de_serie))  
      if joueurCourant.sexe == "F" :
       maListeDeJoueursFeminin.append(joueurCourant)
      else :
       maListeDeJoueursMasculin.append(joueurCourant)



    for monSexeCourant, maListeDeJoueurCourante in zip(["F", "M"], [maListeDeJoueursFeminin, maListeDeJoueursMasculin]):
        nbInscris = len(maListeDeJoueurCourante)
        maConfigurationPoule = CreationPoules(nbInscris, 1, monSexeCourant)  # bug 1
        print(f'nombre de gagnant par poule: {maConfigurationPoule.get_winners_per_pool()}')
        print(maConfigurationPoule.get_pool_sizes())                               # bug 2
        mesPoules = maConfigurationPoule.poules
        mesMatchsDePoules = AllocationJoueur(poules=mesPoules, joueurs=maListeDeJoueurCourante)
        mesMatchsDePoules.allouer()
        mesMatchsDePoules.afficher_resultat()

    # Provisioning Airtable
    for unePoule in mesMatchsDePoules.poules:
        print(f'Building Poule {unePoule.name}')

        poule_record = tablePoule.create({           # bug 4 : on garde l'ID retourné
            "Nom":        str(unePoule.name),
            "nb_gagnant": int(unePoule.nb_gagnant),
            "nb_joueurs": int(unePoule.nb_joueurs),
            "lieu":       str(unePoule.lieu),
        })
        poule_at_id = poule_record["id"]

        for unJoueur in unePoule.getJoueurs():
            # bug 5 : recherche par airtable_id stocké à l'import
            joueur_records = tableJoueur.all(
                formula=f"{{codejoueur}}='{unJoueur.id}'"
            )
            if not joueur_records:
                raise ValueError(f"Joueur introuvable en AT : {unJoueur.prenom} {unJoueur.nom}")

            tablePoule_Joueur.create({
                "Poule":       [poule_at_id],             # linked record → liste d'IDs
                "CodeJoueur":  [joueur_records[0]["id"]]
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
