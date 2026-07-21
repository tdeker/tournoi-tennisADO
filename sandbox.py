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
#prov.creer_champs_poule_joueur()
#prov.provisionner_points_poules(graine=42)

# remplir aléatoirement les points des poules
prov.provisionner_points_poules(graine=42)

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

gestionnaire.remplir_consolante("Consolante Hommes", codes_h, graine=42)
gestionnaire.remplir_consolante("Consolante Femmes", codes_f, graine=42)

print("Tableaux de consolante créés dans Resultat.")



