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

# =====================================================================
# TABLEAUX (brackets-viewer) — principal & consolantes
# ---------------------------------------------------------------------
# À COLLER dans app.py, juste AVANT la ligne `@app.route('/')`.
# Réutilise AIRTABLE_TOKEN / BASE_ID déjà définis plus haut dans app.py.
#
# PRINCIPE (important) :
#   On N'INVENTE RIEN. On affiche l'état EXACT de la table Resultat.
#   - Chaque ligne Resultat = une position de départ (1..Taille_tableau),
#     liée à UN joueur fixe, avec les colonnes T_1_32..Finale à "V"/"P".
#   - Pour chaque tour, on lit la colonne correspondante TELLE QUELLE :
#       "V" -> ce joueur a gagné ce tour
#       "P" -> ce joueur a perdu ce tour
#       vide -> match pas encore joué -> l'emplacement reste vide
#   - Position sans joueur lié = BYE.
#   - La taille du tableau (Taille_tableau) fixe le tour de départ :
#     un tableau de 32 commence au 1/16 ; T_1_32 n'existe pas.
#
#   Au fur et à mesure que la table Resultat est remplie, le tableau
#   progresse tout seul : aucune propagation/déduction côté code.
# =====================================================================

# Colonnes de tour dans Resultat, de la plus large a la finale.
_COLONNES_TOUR = ["T_1_32", "T_1_16", "T_1_8", "T_1_4", "T_1_2", "Finale"]

# Taille de tableau -> colonne du 1er tour (identique a tournoi.py).
_PREMIER_TOUR_POUR_TAILLE = {
    64: "T_1_32", 32: "T_1_16", 16: "T_1_8", 8: "T_1_4", 4: "T_1_2", 2: "Finale",
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


def _positions_du_tour(positions_tour_precedent):
    """
    Regroupe les positions par paires : les positions 2k-1 et 2k du tour
    courant forment le match k. Renvoie la liste des paires (pos_a, pos_b).
    """
    paires = []
    for i in range(0, len(positions_tour_precedent), 2):
        paires.append(
            (positions_tour_precedent[i], positions_tour_precedent[i + 1])
        )
    return paires


def construire_payload_tableau(nom_tournoi):
    """
    Construit le payload brackets-viewer refletant l'ETAT ACTUEL de la
    table Resultat pour un tournoi (principal ou consolante). Lecture
    seule, aucune deduction : un tour non rempli reste vide.
    """
    table_tournoi, table_resultat, table_joueur = _tables_tableau()

    tournois = table_tournoi.all(formula=f"{{Nom}} = '{nom_tournoi}'")
    if not tournois:
        raise ValueError(f"Tournoi '{nom_tournoi}' introuvable.")
    tournoi = tournois[0]
    taille = tournoi["fields"].get("Taille_tableau")
    if not taille:
        raise ValueError(
            f"Le tournoi '{nom_tournoi}' n'a pas de Taille_tableau."
        )

    refs = table_resultat.all(formula=f"{{Tournoi}} = '{nom_tournoi}'")
    if not refs:
        raise ValueError(
            f"Aucun Resultat pour '{nom_tournoi}' : tableau non initialise."
        )

    # Une ligne Resultat par position -> index par Position.
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

    # participant.id = Position de depart (entier stable).
    participants = []
    for pos in sorted(par_position):
        liens = par_position[pos].get("Joueur") or []
        if not liens:
            continue  # bye : aucun participant a cette position
        participants.append({
            "id": pos,
            "tournament_id": 0,
            "name": noms_par_id.get(liens[0], par_position[pos].get("Ref", f"Pos {pos}")),
        })

    def joueur_a_position(pos):
        """id participant (=Position) si un joueur occupe cette place, sinon None (bye)."""
        f = par_position.get(pos, {})
        return pos if (f.get("Joueur") or []) else None

    def resultat_tour(pos, colonne):
        """'V', 'P' ou None, lu DIRECTEMENT dans Resultat (aucune deduction)."""
        return par_position.get(pos, {}).get(colonne)

    colonnes = _colonnes_actives(taille)

    # Positions vivantes du tour courant. Au 1er tour : 1..taille.
    # Aux tours suivants : la position du joueur marque "V" au tour
    # precedent (le vainqueur REEL ecrit dans Resultat). Sans "V" (match
    # pas encore joue), on reserve un emplacement VIDE (None) : l'arbre
    # reste dessine, l'emplacement se remplira a la saisie.
    positions_vivantes = list(range(1, taille + 1))

    matches, rounds = [], []
    match_id = 0

    for round_number, colonne in enumerate(colonnes, start=1):
        rounds.append({
            "id": round_number - 1, "number": round_number,
            "stage_id": 0, "group_id": 0,
        })

        positions_suivantes = []
        for numero_match, (pos_a, pos_b) in enumerate(
            _positions_du_tour(positions_vivantes), start=1
        ):
            id_a = joueur_a_position(pos_a) if pos_a is not None else None
            id_b = joueur_a_position(pos_b) if pos_b is not None else None

            res_a = resultat_tour(pos_a, colonne) if pos_a is not None else None
            res_b = resultat_tour(pos_b, colonne) if pos_b is not None else None

            # Termine seulement si un "V" est explicitement ecrit.
            termine = (res_a == "V") or (res_b == "V")
            status = 4 if termine else 2  # Completed / Ready

            def opp(pid, position, res):
                # pid None => bye (opponent = null pour brackets-viewer).
                if pid is None:
                    return None
                o = {"id": pid, "position": position}
                if res == "V":
                    o["result"] = "win"
                elif res == "P":
                    o["result"] = "loss"
                return o

            matches.append({
                "id": match_id, "number": numero_match,
                "stage_id": 0, "group_id": 0, "round_id": round_number - 1,
                "child_count": 0, "status": status,
                "opponent1": opp(id_a, pos_a, res_a),
                "opponent2": opp(id_b, pos_b, res_b),
            })
            match_id += 1

            # Position qui avance : celle du "V" explicite. Aucun "V" =>
            # emplacement reserve (None), aucun vainqueur invente.
            if res_a == "V":
                positions_suivantes.append(pos_a)
            elif res_b == "V":
                positions_suivantes.append(pos_b)
            else:
                positions_suivantes.append(None)

        positions_vivantes = positions_suivantes

    return {
        "participant": participants,
        "stage": [{
            "id": 0, "tournament_id": 0, "name": nom_tournoi,
            "type": "single_elimination", "number": 1,
            "settings": {"size": taille},
        }],
        "group": [{"id": 0, "stage_id": 0, "number": 1}],
        "round": rounds,
        "match": matches,
        "match_game": [],
    }


def _tournois_avec_resultats():
    """
    Tournois ayant AU MOINS une ligne dans Resultat (tableau initialise).
    On ne presente que ceux-la dans le menu du front.
    """
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
    """Payload brackets-viewer refletant l'etat actuel de Resultat."""
    try:
        data = construire_payload_tableau(nom_tournoi)
        return jsonify({"success": True, "data": data})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

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