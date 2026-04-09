from pyairtable import Api

AIRTABLE_TOKEN = "patUgWdyAOP4lcUeb.5e64ecf450526591dc36b6a3c9dda130d159082384430efde4140dbd16c3cbaa"  # ton vrai token complet
BASE_ID = "appIRSMg6tqFzeMr5"


api = Api(AIRTABLE_TOKEN)
base = api.base(BASE_ID)
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
