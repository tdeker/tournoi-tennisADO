from poule import *
from utiles import *
from itertools import zip_longest
import math
from dotenv import load_dotenv
import os
from pyairtable import Api


if __name__ == "__main__":

    load_dotenv()  # charge le fichier .env
    AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
    BASE_ID        = os.getenv("BASE_ID")
    monApiAT = Api(AIRTABLE_TOKEN)
    tableJoueur = monApiAT.table(BASE_ID, "Joueur")
    tablePoule = monApiAT.table(BASE_ID, "Poule")
    tablePoule_Joueur = monApiAT.table(BASE_ID, "Poule_Joueur")

    records = tableJoueur.all()

    # Dictionnaire pour retrouver l'ID Airtable d'un joueur à partir de son CodeJoueur
    # (évite de refaire un tableJoueur.all() à chaque joueur dans la boucle plus bas)
    joueur_id_par_code = {
        record["fields"].get("CodeJoueur"): record["id"]
        for record in records
        if record["fields"].get("CodeJoueur")
    }

    def records_to_joueurs(records) -> list[Joueur]:
        joueurs = []
        for record in records:
            f = record["fields"]
            joueur = Joueur(
                prenom        = f.get("Prénom", ""),
                nom           = f.get("Nom", ""),
                sexe          = f.get("Sexe", "M"),
                age           = f.get("Age", 0),
                niveau        = int(f.get("Niveau")) if f.get("Niveau") is not None else None,
                zone          = int(f.get("Zone"))   if f.get("Zone")   is not None else None,
                tete_de_serie = f.get("Seed", False),
                id            = f.get("CodeJoueur", ""),
            )
            joueurs.append(joueur)
        return joueurs

    maListeDeJoueurs = records_to_joueurs(records)

    # Listes pour les poules : non têtes de série
    feminin_poules:  List[Joueur] = []  # tous les joueurs non tête de série féminin
    masculin_poules: List[Joueur] = []  # tous les joueurs non tête de série masculin
    # Listes pour le tournoi principal : têtes de série
    feminin_qualifies:  List[Joueur] = []
    masculin_qualifies: List[Joueur] = []

    for joueurCourant in maListeDeJoueurs:
        if joueurCourant.sexe == "F":
            if joueurCourant.tete_de_serie:
                feminin_qualifies.append(joueurCourant)
            else:
                feminin_poules.append(joueurCourant)
        else:  # "M"
            if joueurCourant.tete_de_serie:
                masculin_qualifies.append(joueurCourant)
            else:
                masculin_poules.append(joueurCourant)

    print(f"Féminines non têtes de série : {len(feminin_poules)}")
    print(f"Féminines têtes de série     : {len(feminin_qualifies)}")
    print(f"Masculins non têtes de série : {len(masculin_poules)}")
    print(f"Masculins têtes de série     : {len(masculin_qualifies)}")

    ### Effacer les poules créées précédemment
    records_poule = tablePoule.all()
    ids = [record["id"] for record in records_poule]
    if ids:
        tablePoule.batch_delete(ids)

    records_poule_joueur = tablePoule_Joueur.all()
    ids = [record["id"] for record in records_poule_joueur]
    if ids:
        tablePoule_Joueur.batch_delete(ids)

    for monSexeCourant, maListeDeJoueurCourante in zip(["F", "M"], [feminin_poules, masculin_poules]):
        nbInscris = len(maListeDeJoueurCourante)
        maConfigurationPoule = CreationPoules(nbInscris, 1, monSexeCourant)  # bug 1
        print(f'nombres de joueurs et nombre de gagnant par poule: {maConfigurationPoule.get_pool_sizes_and_winners()}')
        #print(maConfigurationPoule.get_pool_sizes())                               # bug 2
        mesPoules = maConfigurationPoule.poules
        mesMatchsDePoules = AllocationJoueur(poules=mesPoules, joueurs=maListeDeJoueurCourante)
        mesMatchsDePoules.allouer()
        mesMatchsDePoules.afficher_resultat()

        for i, unePoule in enumerate(mesMatchsDePoules.poules, start=0):
            print(f'Building Poule {unePoule.name}')
            poule_record = tablePoule.create({
                "Nom"        : str(unePoule.name),
                "nb_gagnant" : int(unePoule.nb_gagnant),
                "nb_joueurs" : int(unePoule.nb_joueurs),
                "lieu"       : str(unePoule.lieu),
                "Cout"       : int(mesMatchsDePoules._cout_poule(unePoule))
            })
            poule_at_id = poule_record["id"]

            # On prépare tous les liens Poule_Joueur pour cette poule
            # et on les envoie en une seule requête groupée
            liens_a_creer = []
            for unJoueur in unePoule.getJoueurs():
                print(f'ajout du joueur : {unJoueur.prenom, unJoueur.nom}  dans la poule : {unePoule.name}')

                joueur_at_id = joueur_id_par_code.get(unJoueur.id)
                if joueur_at_id is None:
                    raise ValueError(f"Joueur introuvable : {unJoueur.id}")

                liens_a_creer.append({
                    "Poule"     : [poule_at_id],
                    "CodeJoueur": [joueur_at_id]
                })

            if liens_a_creer:
                tablePoule_Joueur.batch_create(liens_a_creer)


## tester la répartition avec la liste des joueurs de 2025 pour voir si OK
## selectionner les gagnants au hasard pour chaque poule
## créer le tableau pour le premier tour
## crééer le tableau pour la consolante (avec joueurs by)
## prévoir de faire une tableau de consolante en placant avantageusement ceux qui ont le plus de point = le moins de jeu perdus ou bien la différence entre le nombre de match perdu et le nombre de match gagné
## importer la liste des joueur depuis un fichier Excel ou csv
## chargement de la liste des joueurs dans supabase  avec les données d'entrée, le nombre de point et les adversaire
## Exporter les résultats dans un fichier excel
## exporter les résultats dans un fichier json
## afficher les résultats dans un tableau html
## faire un webservice en python avec flask et flask_restful
## faire le front end