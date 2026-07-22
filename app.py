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
    """Convertit les records Airtable en objets Joueur (modèle joueur.py de la branche research)"""
    joueurs = []
    for record in records:
        f = record["fields"]
        joueur = Joueur(
            prenom=f.get("Prénom", ""),
            nom=f.get("Nom", ""),
            sexe=f.get("Sexe", "M"),
            age=f.get("Age", 0),
            niveau=int(f.get("Niveau")) if f.get("Niveau") is not None else 1,
            zone=int(f.get("Zone")) if f.get("Zone") is not None else 1,
            id=f.get("CodeJoueur", ""),
            tete_de_serie=f.get("Seed", False),
        )
        joueurs.append(joueur)
    return joueurs

#################################################
# =====================================================================
# TABLEAUX (bracketry) — principal & consolantes
# ---------------------------------------------------------------------
# A COLLER dans app.py, juste AVANT la ligne `@app.route('/')`.
# Reutilise AIRTABLE_TOKEN / BASE_ID deja definis plus haut dans app.py.
#
# REGLES (rappel du cahier des charges) :
#   - Utilise UNIQUEMENT les tables Tournoi et Resultat.
#   - Tournoi.Taille_tableau determine le tour de depart :
#       64 -> 1/32, 32 -> 1/16, 16 -> 1/8, 8 -> 1/4, 4 -> 1/2, 2 -> Finale.
#   - On affiche l'AVANCEMENT REEL de Resultat, rien n'est simule :
#       * 1er tour : match k = position (2k-1) vs position (2k).
#       * une case sans joueur = BYE -> qualification automatique.
#       * un tour est "termine" seulement quand chaque position encore
#         en lice a "V" ou "P" ecrit dans la colonne de ce tour.
#       * tant qu'un match n'a pas de "V" ecrit, l'emplacement du tour
#         suivant reste VIDE (case blanche), aucun vainqueur invente.
#   - Pas de scores dans l'affichage (evolution future).
#   - Seuls les tournois presents dans Resultat sont proposes.
#
# Format de sortie : celui attendu par bracketry (sbachinin/bracketry) :
#   { "rounds": [{"name": str}, ...],
#     "matches": [{"roundIndex": int, "order": int, "sides": [Side, ...]}, ...] }
#   Side = {"title": str, "isWinner": bool} ; une side ABSENTE du tableau
#   "sides" (longueur 1 au lieu de 2) = BYE, rendue vide par bracketry.
# =====================================================================

_COLONNES_TOUR = ["T_1_32", "T_1_16", "T_1_8", "T_1_4", "T_1_2", "Finale"]
_PREMIER_TOUR_POUR_TAILLE = {
    64: "T_1_32", 32: "T_1_16", 16: "T_1_8", 8: "T_1_4", 4: "T_1_2", 2: "Finale",
}
# Nom de round affiche, dans le vocabulaire tennis (coherent avec les
# colonnes Resultat elles-memes).
_NOM_TOUR = {
    "T_1_32": "1/32", "T_1_16": "1/16", "T_1_8": "1/8",
    "T_1_4": "1/4", "T_1_2": "1/2", "Finale": "Finale",
}


def _tables_tableau():
    api = Api(AIRTABLE_TOKEN)
    return (
        api.table(BASE_ID, "Tournoi"),
        api.table(BASE_ID, "Resultat"),
        api.table(BASE_ID, "Joueur"),
    )


def _colonnes_actives(taille_tableau):
    """Colonnes de tour reellement utilisees, du 1er tour a la finale."""
    premier = _PREMIER_TOUR_POUR_TAILLE.get(taille_tableau)
    if premier is None:
        raise ValueError(
            f"Taille_tableau={taille_tableau} non standard "
            f"(puissance de 2 entre 2 et 64 attendue)."
        )
    return _COLONNES_TOUR[_COLONNES_TOUR.index(premier):]


def construire_payload_tableau(nom_tournoi):
    """
    Construit le payload bracketry refletant l'ETAT ACTUEL de la table
    Resultat pour un tournoi (principal ou consolante). Lecture seule,
    aucune deduction : un tour non rempli reste vide, une position sans
    joueur est un BYE qualifie d'office.
    """
    table_tournoi, table_resultat, table_joueur = _tables_tableau()

    tournois = table_tournoi.all(formula=f"{{Nom}} = '{nom_tournoi}'")
    if not tournois:
        raise ValueError(f"Tournoi '{nom_tournoi}' introuvable.")
    taille = tournois[0]["fields"].get("Taille_tableau")
    if not taille:
        raise ValueError(f"Le tournoi '{nom_tournoi}' n'a pas de Taille_tableau.")

    refs = table_resultat.all(formula=f"{{Tournoi}} = '{nom_tournoi}'")
    if not refs:
        raise ValueError(f"Aucun Resultat pour '{nom_tournoi}' : tableau non initialise.")

    # Une ligne Resultat par position de depart -> index par Position.
    par_position = {}
    for r in refs:
        pos = r["fields"].get("Position")
        if pos is not None:
            par_position[pos] = r["fields"]

    # Resolution des noms de joueurs lies (Resultat.Joueur = lien).
    ids_joueurs = set()
    for f in par_position.values():
        for jid in (f.get("Joueur") or []):
            ids_joueurs.add(jid)

    noms_par_id = {}
    if ids_joueurs:
        for j in table_joueur.all():
            if j["id"] in ids_joueurs:
                f = j["fields"]
                prenom = f.get("Prénom", "")
                noms_par_id[j["id"]] = f"{prenom} {f.get('Nom', '')}".strip()

    def nom_joueur(pos):
        liens = par_position.get(pos, {}).get("Joueur") or []
        if not liens:
            return None  # BYE : aucun joueur a cette position
        return noms_par_id.get(liens[0], par_position[pos].get("Ref", f"Pos {pos}"))

    def resultat_tour(pos, colonne):
        """'V', 'P' ou None, lu DIRECTEMENT dans Resultat (aucune deduction)."""
        return par_position.get(pos, {}).get(colonne)

    colonnes = _colonnes_actives(taille)

    # positions_vivantes[i] = position (int) occupant la ieme place du
    # tour courant, ou None si ce n'est pas encore determine (le match
    # precedent n'a pas de "V" ecrit). Au 1er tour : 1..taille.
    positions_vivantes = list(range(1, taille + 1))

    rounds = [{"name": _NOM_TOUR[c]} for c in colonnes]
    matches = []

    for round_index, colonne in enumerate(colonnes):
        positions_suivantes = []
        for ordre, i in enumerate(range(0, len(positions_vivantes), 2)):
            pos_a = positions_vivantes[i]
            pos_b = positions_vivantes[i + 1]

            nom_a = nom_joueur(pos_a) if pos_a is not None else None
            nom_b = nom_joueur(pos_b) if pos_b is not None else None

            res_a = resultat_tour(pos_a, colonne) if pos_a is not None else None
            res_b = resultat_tour(pos_b, colonne) if pos_b is not None else None

            # BYE : une seule des deux places a un joueur -> qualification
            # d'office (aucun "V" a ecrire pour que ce soit vrai : au 1er
            # tour, tournoi.py ecrit deja "V" pour les byes ; on le traite
            # aussi explicitement ici par securite).
            bye = (nom_a is None) != (nom_b is None)
            if bye:
                if nom_a is not None:
                    res_a = "V"
                else:
                    res_b = "V"

            # sides[0] = position haute (pos_a), sides[1] = position basse
            # (pos_b), toujours dans cet ordre. Un objet vide {} pour la
            # place BYE est traite par bracketry comme une case vide
            # (is_non_empty_object -> false), donc le rendu haut/bas
            # respecte la position reelle dans le tableau.
            side_a = {"title": nom_a, "isWinner": res_a == "V"} if nom_a is not None else {}
            side_b = {"title": nom_b, "isWinner": res_b == "V"} if nom_b is not None else {}
            sides = [side_a, side_b]

            matches.append({
                "roundIndex": round_index,
                "order": ordre,
                "sides": sides,
            })

            if res_a == "V":
                positions_suivantes.append(pos_a)
            elif res_b == "V":
                positions_suivantes.append(pos_b)
            else:
                positions_suivantes.append(None)  # pas encore determine

        positions_vivantes = positions_suivantes

    return {"rounds": rounds, "matches": matches}


def _tournois_avec_resultats():
    """Tournois ayant AU MOINS une ligne dans Resultat (tableau initialise)."""
    table_tournoi, table_resultat, _ = _tables_tableau()

    refs_liees = set()
    for r in table_resultat.all(fields=["Tournoi"]):
        val = r["fields"].get("Tournoi")
        if not val:
            continue
        for v in (val if isinstance(val, list) else [val]):
            refs_liees.add(v)

    tournois = []
    for t in table_tournoi.all():
        f = t["fields"]
        if t["id"] in refs_liees or f.get("Nom") in refs_liees:
            tournois.append({
                "nom": f.get("Nom"),
                "type": f.get("Type"),
                "sexe": f.get("Sexe"),
                "taille": f.get("Taille_tableau"),
            })
    return tournois


@app.route('/api/tournois', methods=['GET'])
def list_tournois():
    """Tournois AYANT des resultats (menu deroulant du front)."""
    try:
        return jsonify({"success": True, "tournois": _tournois_avec_resultats()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/tableau/<path:nom_tournoi>', methods=['GET'])
def get_tableau(nom_tournoi):
    """Payload bracketry refletant l'etat actuel de Resultat."""
    try:
        data = construire_payload_tableau(nom_tournoi)
        return jsonify({"success": True, "data": data})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


################################################

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
                    "age": j.age,
                    "zone": j.zone,
                    "tete_de_serie": j.tete_de_serie
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

        # Dictionnaire pour retrouver l'ID Airtable d'un joueur à partir de son CodeJoueur
        # (évite de refaire un tableJoueur.all() à chaque joueur dans la boucle plus bas)
        joueur_id_par_code = {
            record["fields"].get("CodeJoueur"): record["id"]
            for record in records
            if record["fields"].get("CodeJoueur")
        }

        ### Effacer les poules créées précédemment
        records_poule = tablePoule.all()
        ids = [record["id"] for record in records_poule]
        if ids:
            tablePoule.batch_delete(ids)

        records_poule_joueur = tablePoule_Joueur.all()
        ids = [record["id"] for record in records_poule_joueur]
        if ids:
            tablePoule_Joueur.batch_delete(ids)

        ### Séparation par sexe ET par statut :
        ### les têtes de série sont qualifiées directement (elles ne passent pas par les poules)
        feminin_poules, masculin_poules = [], []
        feminin_qualifies, masculin_qualifies = [], []

        for joueurCourant in maListeDeJoueurs:
            print(f"{joueurCourant.prenom} {joueurCourant.nom} - Niveau: {joueurCourant.niveau} - "
                  f"Zone: {joueurCourant.zone} - Tête de série: {joueurCourant.tete_de_serie}")
            if joueurCourant.sexe == "F":
                (feminin_qualifies if joueurCourant.tete_de_serie else feminin_poules).append(joueurCourant)
            else:
                (masculin_qualifies if joueurCourant.tete_de_serie else masculin_poules).append(joueurCourant)

        print(f"Féminines non têtes de série : {len(feminin_poules)}")
        print(f"Féminines têtes de série     : {len(feminin_qualifies)}")
        print(f"Masculins non têtes de série : {len(masculin_poules)}")
        print(f"Masculins têtes de série     : {len(masculin_qualifies)}")

        resultats = {"feminines": [], "masculines": []}
        qualifies_directs = {
            "feminines": [{"prenom": j.prenom, "nom": j.nom, "niveau": j.niveau} for j in feminin_qualifies],
            "masculines": [{"prenom": j.prenom, "nom": j.nom, "niveau": j.niveau} for j in masculin_qualifies],
        }

        ### Création des poules (nouvel algo : CreationPoules + AllocationJoueur, branche research)
        NB_REPECHES_F = int(os.getenv("NB_REPECHES_CONSOLANTE_F", "0"))
        NB_REPECHES_H = int(os.getenv("NB_REPECHES_CONSOLANTE_H", "0"))

        for monSexeCourant, maListeDeJoueurCourante, maListeDeQualifiesCourante, cle, nbRepechesCourant in zip(
            ["F", "M"],
            [feminin_poules, masculin_poules],
            [feminin_qualifies, masculin_qualifies],
            ["feminines", "masculines"],
            [NB_REPECHES_F, NB_REPECHES_H]
        ):
            if len(maListeDeJoueurCourante) == 0:
                continue

            nbInscris = len(maListeDeJoueurCourante)
            nbSeeds   = len(maListeDeQualifiesCourante)
            maConfigurationPoule = CreationPoules(
                nbInscris, 1, monSexeCourant, nb_seeds=nbSeeds, nb_repeches=nbRepechesCourant
            )
            print(f'Tailles et gagnants par poule : {maConfigurationPoule.get_pool_sizes_and_winners()}')

            mesPoules = maConfigurationPoule.poules
            mesMatchsDePoules = AllocationJoueur(poules=mesPoules, joueurs=maListeDeJoueurCourante)
            mesMatchsDePoules.allouer()
            mesMatchsDePoules.afficher_resultat()

            ### Provisionning des Poules dans Airtable
            for unePoule in mesMatchsDePoules.poules:
                print(f'Building Poule {unePoule.name}')
                poule_record = tablePoule.create({
                    "Nom": str(unePoule.name),
                    "nb_gagnant": int(unePoule.nb_gagnant),
                    "nb_joueurs": int(unePoule.nb_joueurs),
                    "lieu": str(unePoule.lieu),
                    "Cout": int(mesMatchsDePoules._cout_poule(unePoule)),
                })
                poule_at_id = poule_record["id"]

                poule_info = {
                    "nom": unePoule.name,
                    "nb_gagnant": unePoule.nb_gagnant,
                    "nb_joueurs": unePoule.nb_joueurs,
                    "cout": round(mesMatchsDePoules._cout_poule(unePoule), 1),
                    "joueurs": []
                }

                # On prépare tous les liens Poule_Joueur pour cette poule
                # et on les envoie en une seule requête groupée
                liens_a_creer = []
                for unJoueur in unePoule.getJoueurs():
                    joueur_at_id = joueur_id_par_code.get(unJoueur.id)
                    if joueur_at_id is None:
                        raise ValueError(f"Joueur introuvable : {unJoueur.id}")

                    liens_a_creer.append({
                        "Poule": [poule_at_id],
                        "CodeJoueur": [joueur_at_id]
                    })

                    poule_info["joueurs"].append({
                        "prenom": unJoueur.prenom,
                        "nom": unJoueur.nom,
                        "niveau": unJoueur.niveau,
                        "zone": unJoueur.zone,
                    })

                if liens_a_creer:
                    tablePoule_Joueur.batch_create(liens_a_creer)

                resultats[cle].append(poule_info)

        return jsonify({
            "success": True,
            "message": "Poules générées avec succès",
            "qualifies_directs": qualifies_directs,
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