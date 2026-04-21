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
            "joueurs": [{"prenom": j.prenom, "nom": j.nom, "niveau": j.niveau} for j in joueurs]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/poules/genererOLD', methods=['POST'])
def generer_poules():
    try:
        load_dotenv()  # charge le fichier .env
        AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
        BASE_ID        = os.getenv("BASE_ID")
        monApiAT = Api(AIRTABLE_TOKEN)

        tableJoueur = monApiAT.table(BASE_ID, "Joueur")
        tablePoule = monApiAT.table(BASE_ID,"Poule")
        tablePoule_Joueur = monApiAT.table(BASE_ID,"Poule_Joueur")
        records = tableJoueur.all()
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
    
        return jsonify({"success": True, "message": "Poules générées"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def generer_poules():
    try:
        tableJoueur, tablePoule, tablePoule_Joueur = get_airtable_tables()
        
        # Votre logique existante de génération de poules
        records = tableJoueur.all()
        maListeDeJoueurs = records_to_joueurs(records)
        
        # Supprimer poules existantes
        tablePoule.batch_delete([r["id"] for r in tablePoule.all()])
        tablePoule_Joueur.batch_delete([r["id"] for r in tablePoule_Joueur.all()])
        
        # Séparer par sexe et générer
        # ... votre code ici ...
        
        return jsonify({"success": True, "message": "Poules générées"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 6000))
    app.run(host='0.0.0.0', port=port)