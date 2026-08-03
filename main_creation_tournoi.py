"""
Création des tableaux de consolante (Hommes / Femmes), puis - une fois
chaque consolante TERMINÉE - création du tableau principal correspondant.

IMPORTANT : ce script ne génère ni ne simule aucune donnée. Il lit
Poule_Joueur.Est_qualifie et Poule_Joueur.OK_consolante tels qu'ils
sont réellement dans Airtable (renseignés par le déroulement réel des
poules et la déclaration des joueurs) - aucun appel à
provisionner_points_poules / provisionner_ok_consolante / 
reinitialiser_poule_joueur ici : ces méthodes sont réservées à la
génération de jeux de données de TEST, elles écraseraient de vraies
données si on les appelait sur une base en conditions réelles.

Logique :
  1) Pour chaque sexe, vérifie que TOUTES les poules le concernant sont
     terminées (nb_gagnant == nombre de membres avec Est_qualifie
     coché, poule par poule). Si non, la consolante de ce sexe n'est
     pas créée.
  2) Construit le tableau de consolante correspondant à partir des
     non-qualifiés ayant coché OK_consolante - idempotent à relancer
     tant que le tableau n'existe pas encore (remplir_consolante crée
     les enregistrements Resultat, il ne les recrée pas s'ils existent
     déjà - à toi de ne pas relancer deux fois sur le même tournoi).
  3) Pour chaque sexe, vérifie si SA consolante est terminée (un
     vainqueur déterminé - Finale="V" sur un Resultat de ce Tournoi).
     Si oui, construit le tableau principal correspondant :
       - protégés : têtes de série (Joueur.Seed), qu'elles aient joué
         une poule ou non (les seeds sont hors-poule par conception),
         triées par Niveau décroissant ;
       - autres : qualifiés de poule non tête de série (Est_qualifie),
         PLUS le repêché - l'unique vainqueur de la consolante de ce
         sexe, qui entre SANS statut protégé (tiré au sort comme les
         autres) mais reste soumis à la règle anti-collision
         familiale au 1er tour, comme n'importe quel autre joueur de
         cette liste.
"""

import os
from dotenv import load_dotenv
from pyairtable import Api
from tournoi import GestionnaireResultat

load_dotenv()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")

api = Api(AIRTABLE_TOKEN)
table_poule_joueur = api.table(BASE_ID, "Poule_Joueur")
table_joueur = api.table(BASE_ID, "Joueur")
table_poule = api.table(BASE_ID, "Poule")

gestionnaire = GestionnaireResultat(api_key=AIRTABLE_TOKEN, base_id=BASE_ID)

GRAINE = 42  # reproductibilité du tirage au sort / de la réparation familiale


def poules_terminees_par_sexe(sexe):
    """
    True si TOUTES les poules comportant au moins un joueur du sexe
    donné sont terminées : une poule est terminée quand exactement
    nb_gagnant de ses membres ont Est_qualifie coché (ce champ est
    renseigné à la main par les organisateurs au fil des vrais
    résultats - son décompte est donc le signal direct que la poule
    est bouclée, pas besoin de compter les matchs un par un).

    Si aucune poule ne comporte de joueur de ce sexe, renvoie True
    (rien ne bloque - de toute façon codes_non_qualifies_par_sexe
    renverra une liste vide et la création de tableau sera sautée).
    """
    poules_par_id = {p["id"]: p["fields"] for p in table_poule.all()}
    joueurs_par_id = {r["id"]: r["fields"] for r in table_joueur.all()}

    membres_par_poule = {}
    for pj in table_poule_joueur.all():
        liens_poule = pj["fields"].get("Poule") or []
        liens_joueur = pj["fields"].get("CodeJoueur") or []
        if not liens_poule or not liens_joueur:
            continue
        joueur = joueurs_par_id.get(liens_joueur[0])
        if not joueur or joueur.get("Sexe") != sexe:
            continue
        membres_par_poule.setdefault(liens_poule[0], []).append(pj["fields"])

    for poule_id, membres in membres_par_poule.items():
        nb_gagnant = poules_par_id.get(poule_id, {}).get("nb_gagnant")
        if nb_gagnant is None:
            continue  # poule introuvable/mal configurée : on ne bloque pas dessus
        nb_qualifies = sum(1 for m in membres if m.get("Est_qualifie"))
        if nb_qualifies != nb_gagnant:
            return False

    return True


def codes_non_qualifies_par_sexe(sexe):
    """
    CodeJoueur des joueurs NON qualifiés (Est_qualifie décoché ou vide)
    ET ayant déclaré vouloir jouer la consolante (OK_consolante coché),
    pour un sexe donné ("H" ou "F", selon Joueur.Sexe).
    """
    joueurs_par_id = {r["id"]: r["fields"] for r in table_joueur.all()}

    codes = []
    for pj in table_poule_joueur.all():
        if pj["fields"].get("Est_qualifie"):
            continue
        if not pj["fields"].get("OK_consolante"):
            continue

        liens_joueur = pj["fields"].get("CodeJoueur") or []
        if not liens_joueur:
            continue

        joueur = joueurs_par_id.get(liens_joueur[0])
        if not joueur or joueur.get("Sexe") != sexe:
            continue

        codes.append(joueur.get("CodeJoueur"))

    return codes


def _niveau_int(joueur_fields):
    """Convertit Niveau (single select, potentiellement str) en int, 0 si absent/invalide."""
    try:
        return int(joueur_fields.get("Niveau", 0))
    except (TypeError, ValueError):
        return 0


def gagnant_consolante(nom_tournoi_consolante):
    """
    CodeJoueur du vainqueur de la consolante (celui dont Finale="V"
    dans Resultat pour ce Tournoi), ou None si le tournoi n'existe pas,
    n'a pas de résultats, ou n'est pas encore terminé.
    """
    resultats = gestionnaire.table_resultat.all(
        formula=f"{{Tournoi}} = '{nom_tournoi_consolante}'"
    )
    gagnant = next((r for r in resultats if r["fields"].get("Finale") == "V"), None)
    if gagnant is None:
        return None

    liens_joueur = gagnant["fields"].get("Joueur") or []
    if not liens_joueur:
        return None

    joueur = table_joueur.get(liens_joueur[0])
    return joueur["fields"].get("CodeJoueur") if joueur else None


def consolante_terminee(nom_tournoi_consolante):
    """
    Une consolante est terminée dès qu'un vainqueur est déterminé
    (Finale="V" sur un enregistrement Resultat de ce Tournoi).
    """
    return gagnant_consolante(nom_tournoi_consolante) is not None


def codes_qualifies_par_sexe(sexe, nom_consolante):
    """
    Retourne (codes_proteges, codes_autres) pour le tableau principal :

    - codes_proteges : TOUTES les têtes de série de ce sexe
      (Joueur.Seed coché), qu'elles aient joué une poule ou non - les
      seeds sont par conception hors-poule (voir CreationPoules :
      "places réservées dans le tableau, hors poules"), donc on les
      cherche directement dans Joueur, pas via Poule_Joueur. Triées
      par Niveau décroissant faute de Points de poule pour les
      départager (à adapter si un vrai classement de seeding existe).

    - codes_autres : qualifiés de poule non tête de série
      (Est_qualifie coché dans Poule_Joueur), PLUS le repêché - le
      vainqueur de la consolante de ce sexe, qui entre dans le tableau
      SANS statut protégé (tiré au sort comme les autres) mais reste
      soumis à la règle anti-collision familiale au 1er tour, comme
      tout le monde dans cette liste.
    """
    joueurs_par_id = {r["id"]: r["fields"] for r in table_joueur.all()}

    codes_deja_vus = set()
    proteges_avec_niveau = []
    autres = []

    # 1) Seeds : protégés d'office, indépendamment d'une poule jouée.
    for joueur in joueurs_par_id.values():
        if joueur.get("Sexe") == sexe and joueur.get("Seed"):
            code = joueur.get("CodeJoueur")
            proteges_avec_niveau.append((_niveau_int(joueur), code))
            codes_deja_vus.add(code)

    # 2) Qualifiés de poule, hors seeds déjà comptés ci-dessus.
    for pj in table_poule_joueur.all():
        if not pj["fields"].get("Est_qualifie"):
            continue
        liens_joueur = pj["fields"].get("CodeJoueur") or []
        if not liens_joueur:
            continue
        joueur = joueurs_par_id.get(liens_joueur[0])
        if not joueur or joueur.get("Sexe") != sexe:
            continue
        code = joueur.get("CodeJoueur")
        if code in codes_deja_vus:
            continue  # déjà seed
        autres.append(code)
        codes_deja_vus.add(code)

    # 3) Repêché = vainqueur de la consolante de ce sexe, non protégé.
    code_repeche = gagnant_consolante(nom_consolante)
    if code_repeche and code_repeche not in codes_deja_vus:
        autres.append(code_repeche)
        codes_deja_vus.add(code_repeche)

    proteges_avec_niveau.sort(key=lambda t: t[0], reverse=True)
    codes_proteges = [code for _, code in proteges_avec_niveau]
    return codes_proteges, autres


# --- 1) Tableaux de consolante (Hommes, Femmes) --------------------------

for sexe, nom_consolante in (("H", "Consolante Hommes"), ("F", "Consolante Femmes")):
    if not poules_terminees_par_sexe(sexe):
        print(f"{nom_consolante} : poules ({sexe}) pas toutes terminées, tableau non créé.")
        continue

    codes = codes_non_qualifies_par_sexe(sexe)
    print(f"{nom_consolante} : {len(codes)} joueur(s) -> {codes}")
    if codes:
        gestionnaire.remplir_consolante(nom_consolante, codes, graine=GRAINE)
    else:
        print(f"{nom_consolante} : aucun inscrit, tableau non créé.")

print("Tableaux de consolante à jour dans Resultat.\n")

# --- 2) Tableau principal, uniquement si la consolante du sexe correspondant
#        est terminée ------------------------------------------------------

for sexe, nom_consolante, nom_principal in (
    ("H", "Consolante Hommes", "Principal Hommes"),
    ("F", "Consolante Femmes", "Principal Femmes"),
):
    if not consolante_terminee(nom_consolante):
        print(f"{nom_principal} : {nom_consolante} pas encore terminée, tableau non créé.")
        continue

    codes_proteges, codes_autres = codes_qualifies_par_sexe(sexe, nom_consolante)
    print(f"{nom_principal} : {len(codes_proteges)} protégé(s), {len(codes_autres)} autre(s) (dont repêché)")
    gestionnaire.initialiser_tableau_principal(
        nom_principal, codes_proteges, codes_autres, graine=GRAINE
    )
    print(f"{nom_principal} créé dans Resultat.")