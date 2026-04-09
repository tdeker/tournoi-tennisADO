from pyairtable import Api
from joueur import *
AIRTABLE_TOKEN = "patUgWdyAOP4lcUeb.5e64ecf450526591dc36b6a3c9dda130d159082384430efde4140dbd16c3cbaa"  # ton vrai token complet
BASE_ID = "appIRSMg6tqFzeMr5"

api = Api(AIRTABLE_TOKEN)

# provisionning des joueurs dans la table des joueurs
TableJoueur = api.table(BASE_ID,"Joueur")
## suppression des enregistrements préalabelement produit
# Récupérer tous les IDs et les supprimer
records = TableJoueur.all()
ids = [record["id"] for record in records]
TableJoueur.batch_delete(ids)

print(f"✅ {len(ids)} enregistrements supprimés")
## Création de la liste des joueurs inscrit
nbInscris=27
nbSeed=4
print("debut")
maListeDeJoueurs = creation_joueurs_avec_nom_famille(nbInscris,nbSeed) 

for monJoueur in maListeDeJoueurs :
    TableJoueur.create({
        "Nom" : str(monJoueur.nom),
        "Prénom" : str(monJoueur.prenom),
        "Sexe" : str(monJoueur.sexe),
        "Niveau" : str(monJoueur.niveau),
        "Age" : int(monJoueur.age),
        "Seed" :bool(monJoueur.tete_de_serie),
    })



exit()
## Création de la table des joueurs

"""
# ─────────────────────────────────────────
# JOUEUR
# ─────────────────────────────────────────
base.create_table(
    name="Joueur",
    fields=[
        {"name": "Nom",               "type": "singleLineText"},
        {"name": "Prénom",            "type": "singleLineText"},
        {"name": "Classement",        "type": "singleSelect", "options": {
            "choices": [
                {"name": "N1"}, {"name": "N2"}, {"name": "N3"},
                {"name": "N4"}, {"name": "N5"}
            ]
        }},
        {"name": "Date de naissance", "type": "date", "options": {
            "dateFormat": {"name": "iso"}
        }},
        {"name": "Email",             "type": "email"},
    ]
)
print("✅ Table Joueur créée")

# ─────────────────────────────────────────
# TOURNOI
# ─────────────────────────────────────────
base.create_table(
    name="Tournoi",
    fields=[
        {"name": "Nom",        "type": "singleLineText"},
        {"name": "Date début", "type": "date", "options": {"dateFormat": {"name": "iso"}}},
        {"name": "Date fin",   "type": "date", "options": {"dateFormat": {"name": "iso"}}},
        {"name": "Lieu",       "type": "singleLineText"},
    ]
)
print("✅ Table Tournoi créée")

# ─────────────────────────────────────────
# POULE
# ─────────────────────────────────────────
base.create_table(
    name="Poule",
    fields=[
        {"name": "Nom",     "type": "singleLineText"},
        {"name": "Numéro",  "type": "number", "options": {"precision": 0}},
    ]
)
print("✅ Table Poule créée")
base.create_table(
    name="Poule_Joueur",
    fields=[
        {"name": "Nom",           "type": "singleLineText"},  # ← champ primaire obligatoire
        {"name": "Tête de série", "type": "checkbox", "options": {
            "icon": "check", "color": "greenBright"
        }},
    ]
)
"""

# ─────────────────────────────────────────
# POULE_JOUEUR
# ─────────────────────────────────────────
base.create_table(
    name="Poule_Joueur",
    fields=[
        {"name": "Nom",           "type": "singleLineText"},  # ← champ primaire obligatoire
        {"name": "Tête de série", "type": "checkbox", "options": {
            "icon": "check", "color": "greenBright"
        }},
    ]
)
