from flask import Flask, jsonify, request
from flask_cors import CORS
from poule import *
from utiles import *
from itertools import zip_longest
import math
from dotenv import load_dotenv
import os
from pyairtable import Api
import hashlib
import sys
print("=" * 50, file=sys.stderr)
print("DEBUT DU CHARGEMENT DE APP.PY", file=sys.stderr)
print("=" * 50, file=sys.stderr)

try:
    print("Import Flask...", file=sys.stderr)
    from flask import Flask, jsonify, request
    print("✅ Flask OK", file=sys.stderr)
    
    print("Import CORS...", file=sys.stderr)
    from flask_cors import CORS
    print("✅ CORS OK", file=sys.stderr)
    
    print("Import poule...", file=sys.stderr)
    from poule import *
    print("✅ poule OK", file=sys.stderr)
    
    print("Import utiles...", file=sys.stderr)
    from utiles import *
    print("✅ utiles OK", file=sys.stderr)
    
    from itertools import zip_longest
    import math
    from dotenv import load_dotenv
    import os
    from pyairtable import Api
    import hashlib
    print("✅ Tous les imports OK", file=sys.stderr)
    
except Exception as e:
    print("=" * 50, file=sys.stderr)
    print(f"❌ ERREUR D'IMPORT: {e}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Charger les variables d'environnement
load_dotenv()

print("Création de l'app Flask...", file=sys.stderr)
app = Flask(__name__)
CORS(app)
print("✅ App Flask créée", file=sys.stderr)

# Configuration Airtable
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")

print(f"AIRTABLE_TOKEN présent: {AIRTABLE_TOKEN is not None}", file=sys.stderr)
print(f"BASE_ID présent: {BASE_ID is not None}", file=sys.stderr)

# ... reste de votre code exactement comme avant ...



# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration Airtable
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")

def get_airtable_tables():
    """Initialise et retourne les tables Airtable"""
    monApiAT = Api(AIRTABLE_TOKEN)
    tableJoueur = monApiAT.table(BASE_ID, "Joueur")
    tablePoule = monApiAT.table(BASE_ID, "Poule")
    tablePoule_Joueur = monApiAT.table(BASE_ID, "Poule_Joueur")
    return tableJoueur, tablePoule, tablePoule_Joueur

def records_to_joueurs(records) -> list:
    """Convertit les records Airtable en objets Joueur"""
    joueurs = []
    for record in records:
        f = record["fields"]
        joueur = Joueur(
            name=f.get("Prénom", ""),
            familyName=f.get("Nom", ""),
            sexe=f.get("Sexe", "M"),
            age=f.get("Age", 0),
            niveau=int(f.get("Niveau")),
            seededPlayer=f.get("Seed", False),
        )
        joueurs.append(joueur)
    return joueurs

@app.route('/')
def home():
    return jsonify({
        "message": "API de gestion des poules de tennis",
        "status": "active",
        "endpoints": {
            "/api/joueurs": "GET - Liste des joueurs",
            "/api/poules/generer": "POST - Générer les poules",
            "/api/poules": "GET - Voir les poules",
            "/api/poules/reset": "DELETE - Supprimer les poules"
        }
    })

@app.route('/api/joueurs', methods=['GET'])
def get_joueurs():
    try:
        tableJoueur, _, _ = get_airtable_tables()
        records = tableJoueur.all()
        joueurs = records_to_joueurs(records)
        
        return jsonify({
            "success": True,
            "count": len(joueurs),
            "joueurs": [
                {
                    "prenom": j.prenom, 
                    "nom": j.nom, 
                    "niveau": j.niveau,
                    "sexe": j.sexe,
                    "age": j.age
                } for j in joueurs
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/poules/generer', methods=['POST'])
def generer_poules():
    try:
        tableJoueur, tablePoule, tablePoule_Joueur = get_airtable_tables()
        
        records = tableJoueur.all()
        maListeDeJoueurs = records_to_joueurs(records)
        maListeDeJoueursFeminin = []
        maListeDeJoueursMasculin = []
        
        ### Effacer les poules créées précédemment
        records = tablePoule.all()
        ids = [record["id"] for record in records]
        if ids:
            tablePoule.batch_delete(ids)
        
        records = tablePoule_Joueur.all()
        ids = [record["id"] for record in records]
        if ids:
            tablePoule_Joueur.batch_delete(ids)
        
        ### Séparation par sexe - CORRECTION DE L'INDENTATION
        for joueurCourant in maListeDeJoueurs:
            print(f"{joueurCourant.prenom} {joueurCourant.nom} - Niveau: {joueurCourant.niveau} - Age: {joueurCourant.age} - Tête de série: {joueurCourant.tete_de_serie}")  
            if joueurCourant.sexe == "F":
                maListeDeJoueursFeminin.append(joueurCourant)
            else:
                maListeDeJoueursMasculin.append(joueurCourant)
        
        resultats = {"feminines": [], "masculines": []}
        
        ### Création des poules
        for monSexeCourant, maListeDeJoueurCourante, cle in zip(
            ["F", "M"], 
            [maListeDeJoueursFeminin, maListeDeJoueursMasculin],
            ["feminines", "masculines"]
        ):
            if len(maListeDeJoueurCourante) == 0:
                continue
                
            nbInscris = len(maListeDeJoueurCourante)
            maConfigurationPoule = PoolConfigurationGeneratorByTristan(nbInscris, 1)
            print(f'Nombre de gagnants par poule: {maConfigurationPoule.get_winners_per_pool()}')
            print(f'Tailles des poules: {maConfigurationPoule.get_pool_sizes_list()}')
            
            mesMatchsDePoules = RepartiteurPoulesFixes(
                maListeDeJoueurCourante, 
                maConfigurationPoule, 
                monSexeCourant
            )
            mesMatchsDePoules.repartir_par_couts_TK(maListeDeJoueurCourante)
            mesMatchsDePoules.afficher_resultats()
            
            ### Provisioning des Poules dans Airtable
            for i, unePoule in enumerate(mesMatchsDePoules.get_Poules(), start=0):
                print(f'Building Poule {unePoule.name}')
                tablePoule.create({
                    "Nom": str(unePoule.name),
                    "nb_gagnant": int(mesMatchsDePoules.nb_gagnants[i]),
                    "nb_joueurs": int(unePoule.nb_joueurs),
                    "lieu": str(unePoule.lieu),
                })
                
                poule_info = {
                    "nom": unePoule.name,
                    "nb_gagnant": mesMatchsDePoules.nb_gagnants[i],
                    "nb_joueurs": unePoule.nb_joueurs,
                    "joueurs": []
                }
                
                for unJoueur in unePoule.getJoueurs():
                    records = tableJoueur.all(formula=f"{{codejoueur}}='{unJoueur.code}'")
                    if not records:
                        raise ValueError(f"Joueur introuvable : {unJoueur.code}")
                    
                    tablePoule_Joueur.create({
                        "Poule": str(unePoule.name),
                        "CodeJoueur": [records[0]["id"]]
                    })
                    
                    poule_info["joueurs"].append({
                        "prenom": unJoueur.prenom,
                        "nom": unJoueur.nom,
                        "niveau": unJoueur.niveau
                    })
                
                resultats[cle].append(poule_info)
        
        return jsonify({
            "success": True, 
            "message": "Poules générées avec succès",
            "poules": resultats
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check pour Railway"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # ✅ CORRECTION : Utiliser la variable PORT de Railway
    port = int(os.environ.get('PORT', 5000))  # Changé de 6000 à 5000
    app.run(host='0.0.0.0', port=port, debug=False)