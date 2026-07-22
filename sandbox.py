"""
Sandbox : création des 2 tournois de consolante (Hommes / Femmes).

Utilise Poule_Joueur.Est_qualifie (calculé par provisioning.py, voir
prov.provisionner_points_poules) pour déterminer qui n'est PAS qualifié
pour le principal, puis délègue le placement dans le tableau à
tournoi.py (GestionnaireResultat.remplir_consolante).
"""

import os
from dotenv import load_dotenv
from pyairtable import Api
from tournoi import GestionnaireResultat
from score_provisionning import ProvisionneurAirtable
   


load_dotenv()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")

api = Api(AIRTABLE_TOKEN)
table_poule_joueur = api.table(BASE_ID, "Poule_Joueur")
table_joueur = api.table(BASE_ID, "Joueur")

prov = ProvisionneurAirtable(
        api_key=AIRTABLE_TOKEN,
        base_id=BASE_ID,
    )

# Etape -1 : repart d'un etat propre. Sans ca, OK_consolante resterait
# fige d'un run a l'autre (provisionner_ok_consolante ne touche pas par
# defaut aux enregistrements deja renseignes), et Est_qualifie/Points
# pourraient trainer une valeur d'un run precedent avant recalcul.
resultat_reinit = prov.reinitialiser_poule_joueur()
print(f"Reinitialisation : {resultat_reinit['maj']} Poule_Joueur remis a vide.")

# Etape 0 (idempotente) : s'assure que les champs necessaires existent
# dans Poule_Joueur (Victoires/Defaites/Points/Matchs_joues/Est_qualifie/
# OK_consolante). Sans risque si deja presents : ne recree rien.
prov.creer_champs_poule_joueur()

# Etape 1 : simule les poules (round-robin) et ecrit Points/Est_qualifie.
prov.provisionner_points_poules(graine=42)

# Etape 2 (donnees de TEST uniquement - en conditions reelles OK_consolante
# est une declaration du joueur, jamais ecrite par un script) : simule qui,
# parmi les perdants de poule, souhaite jouer la consolante. Sans cet appel,
# OK_consolante reste vide pour tout le monde et codes_non_qualifies_par_sexe
# ci-dessous renverrait des listes vides.
prov.provisionner_ok_consolante(graine=42)


def codes_non_qualifies_par_sexe(sexe):
    """
    Retourne la liste des CodeJoueur des joueurs NON qualifiés
    (Est_qualifie décoché ou vide) ET ayant déclaré vouloir jouer la
    consolante (OK_consolante coché), pour un sexe donné ("H" ou "F",
    selon Joueur.Sexe).
    """
    joueurs_par_id = {r["id"]: r["fields"] for r in table_joueur.all()}

    codes = []
    for pj in table_poule_joueur.all():
        if pj["fields"].get("Est_qualifie"):
            continue  # qualifié -> va au principal, pas à la consolante
        if not pj["fields"].get("OK_consolante"):
            continue  # n'a pas souhaité jouer la consolante

        liens_joueur = pj["fields"].get("CodeJoueur") or []
        if not liens_joueur:
            continue

        joueur = joueurs_par_id.get(liens_joueur[0])
        if not joueur or joueur.get("Sexe") != sexe:
            continue

        codes.append(joueur.get("CodeJoueur"))

    return codes


gestionnaire = GestionnaireResultat(api_key=AIRTABLE_TOKEN, base_id=BASE_ID)

codes_h = codes_non_qualifies_par_sexe("H")
codes_f = codes_non_qualifies_par_sexe("F")

print(f"Consolante Hommes : {len(codes_h)} joueur(s) -> {codes_h}")
print(f"Consolante Femmes : {len(codes_f)} joueur(s) -> {codes_f}")

# Garde : remplir_consolante suppose au moins 1 joueur (TableauBracket ne
# sait pas construire un tableau vide). Avec la simulation aleatoire de
# OK_consolante, une liste vide reste possible (peu de perdants, ou
# probabilite d'opt-in defavorable) - on l'evite proprement plutot que de
# laisser planter le script.
if codes_h:
    gestionnaire.remplir_consolante("Consolante Hommes", codes_h, graine=42)
else:
    print("Consolante Hommes : aucun inscrit, tableau non cree.")

if codes_f:
    gestionnaire.remplir_consolante("Consolante Femmes", codes_f, graine=42)
else:
    print("Consolante Femmes : aucun inscrit, tableau non cree.")

print("Tableaux de consolante créés dans Resultat.")