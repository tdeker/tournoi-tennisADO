"""
Sandbox : provisionnement complet de test (poules -> consolantes ->
principal), jusqu'a la Finale des trois etapes.

Enchaine, dans l'ordre :
  1. RAZ des champs de simulation (Poule_Joueur).
  2. Simulation des poules (Points, Est_qualifie).
  3. Simulation des declarations OK_consolante (majorite des perdants).
  4. Pour chaque CONSOLANTE (H/F) : RAZ des Resultat existants de ce
     tournoi (sinon d'anciennes lignes d'un run precedent s'accumulent
     a cote des nouvelles - c'est ce qui peut faire apparaitre
     plusieurs "V" en Finale), creation (1er tour), simulation
     COMPLETE jusqu'a la Finale, puis recuperation du vainqueur.
  5. Pour chaque PRINCIPAL (H/F) : le tournoi principal se joue APRES
     les consolantes - son vainqueur de consolante (meme sexe) est
     repeche et ajoute aux joueurs du principal (Origine="Consolante"
     dans Resultat), en plus des tetes de serie et des qualifies de
     poule. Meme RAZ + creation + simulation complete que pour les
     consolantes.

Taille_tableau (principal comme consolantes) est calculee AUTOMATIQUEMENT
a partir du nombre de joueurs (protege+autres+repeches pour le principal)
et ECRITE dans Airtable - rien a pre-remplir a la main.

Pour l'affichage sur le site admin (page Tableaux, bracketry), il
suffit ensuite que les Tournoi correspondants existent avec un Nom
identique aux constantes NOM_* ci-dessous et un Type coherent
("Principal" / "Consolante").
"""

import os
from dotenv import load_dotenv
from pyairtable import Api
from tournoi import GestionnaireResultat
from score_provisionning import ProvisionneurAirtable


# Noms (PK) des enregistrements Tournoi concernes. A AJUSTER si les
# tiens portent un nom different dans Airtable (ex: "Open Simple
# Messieurs" comme dans les exemples de tournoi.py) : c'est le seul
# endroit a modifier, tout le reste du script s'adapte automatiquement.
NOM_PRINCIPAL_HOMMES = "Principal Hommes"
NOM_PRINCIPAL_FEMMES = "Principal Femmes"
NOM_CONSOLANTE_HOMMES = "Consolante Hommes"
NOM_CONSOLANTE_FEMMES = "Consolante Femmes"

# Graine commune a toutes les etapes aleatoires : un run avec la meme
# graine reproduit exactement le meme tableau (utile pour deboguer un
# affichage). Mettre None pour un tirage different a chaque execution.
GRAINE = 75


load_dotenv()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")

api = Api(AIRTABLE_TOKEN)
table_poule_joueur = api.table(BASE_ID, "Poule_Joueur")
table_joueur = api.table(BASE_ID, "Joueur")

prov = ProvisionneurAirtable(api_key=AIRTABLE_TOKEN, base_id=BASE_ID)
gestionnaire = GestionnaireResultat(api_key=AIRTABLE_TOKEN, base_id=BASE_ID)


# ============================================================
# ETAPE 1 : poules (RAZ, champs, simulation des scores)
# ============================================================

# Repart d'un etat propre. Sans ca, OK_consolante resterait fige d'un
# run a l'autre (provisionner_ok_consolante ne touche pas par defaut
# aux enregistrements deja renseignes), et Est_qualifie/Points
# pourraient trainer une valeur d'un run precedent avant recalcul.
resultat_reinit = prov.reinitialiser_poule_joueur()
print(f"[1/5] Reinitialisation : {resultat_reinit['maj']} Poule_Joueur remis a vide.")

# Idempotent : s'assure que les champs necessaires existent dans
# Poule_Joueur. Sans risque si deja presents : ne recree rien.
prov.creer_champs_poule_joueur()

# Simule les poules (round-robin) et ecrit Points/Est_qualifie.
prov.provisionner_points_poules(graine=GRAINE)
print("[1/5] Poules simulees (Points/Est_qualifie ecrits).")


# ============================================================
# ETAPE 2 : declarations OK_consolante (donnees de TEST uniquement -
# en conditions reelles c'est une declaration du joueur, jamais
# ecrite par un script). probabilite=0.7 -> une MAJORITE des perdants
# de poule choisissent de jouer la consolante.
# ============================================================

prov.provisionner_ok_consolante(graine=GRAINE, probabilite=0.8)
print("[2/5] OK_consolante simule (majorite des perdants inscrits).")


# ============================================================
# Helpers de selection des joueurs, par sexe
# ============================================================

def _joueurs_par_id():
    return {r["id"]: r["fields"] for r in table_joueur.all()}


def codes_consolante_par_sexe(sexe, joueurs_par_id):
    """
    Perdants de poule (Est_qualifie faux) ET ayant declare vouloir
    jouer la consolante (OK_consolante coche), pour un sexe donne.
    """
    codes = []
    for pj in table_poule_joueur.all():
        if pj["fields"].get("Est_qualifie"):
            continue
        if not pj["fields"].get("OK_consolante"):
            continue
        liens = pj["fields"].get("CodeJoueur") or []
        if not liens:
            continue
        joueur = joueurs_par_id.get(liens[0])
        if not joueur or joueur.get("Sexe") != sexe:
            continue
        codes.append(joueur.get("CodeJoueur"))
    return codes


def codes_qualifies_poule_par_sexe(sexe, joueurs_par_id):
    """
    Gagnants de poule (Est_qualifie coche), pour un sexe donne :
    ce sont les "autres_joueurs" du tableau principal (non proteges),
    places au hasard par initialiser_tableau_principal.
    """
    codes = []
    for pj in table_poule_joueur.all():
        if not pj["fields"].get("Est_qualifie"):
            continue
        liens = pj["fields"].get("CodeJoueur") or []
        if not liens:
            continue
        joueur = joueurs_par_id.get(liens[0])
        if not joueur or joueur.get("Sexe") != sexe:
            continue
        codes.append(joueur.get("CodeJoueur"))
    return codes


def codes_proteges_par_sexe(sexe, joueurs_par_id):
    """
    Tetes de serie (Joueur.Seed coche), pour un sexe donne : ce sont
    les "codes_proteges" du tableau principal, dans l'ORDRE ou ils
    doivent occuper les rangs 1, 2, 3... (le rang 1 et le rang 2 ne
    peuvent se rencontrer qu'en finale, etc.)

    Le schema Joueur n'a pas de champ de classement numerique dedie :
    on ordonne par Niveau croissant (1 = meilleur niveau), puis par
    Nom pour un ordre stable/deterministe en cas d'egalite. Si tu as
    un vrai classement (ranking), remplace ce tri par le tien.
    """
    proteges = [
        f for f in joueurs_par_id.values()
        if f.get("Sexe") == sexe and f.get("Seed")
    ]
    proteges.sort(key=lambda f: (f.get("Niveau") or "9", f.get("Nom") or ""))
    return [f.get("CodeJoueur") for f in proteges]


# ============================================================
# ETAPE 3 : CONSOLANTES - creation (1er tour) + simulation complete
# ============================================================

joueurs_par_id = _joueurs_par_id()

codes_conso_h = codes_consolante_par_sexe("H", joueurs_par_id)
codes_conso_f = codes_consolante_par_sexe("F", joueurs_par_id)
print(f"[3/5] Consolante Hommes : {len(codes_conso_h)} inscrit(s) -> {codes_conso_h}")
print(f"[3/5] Consolante Femmes : {len(codes_conso_f)} inscrit(s) -> {codes_conso_f}")

# Garde : remplir_consolante suppose au moins 1 joueur (TableauBracket
# ne sait pas construire un tableau vide). Avec la simulation
# aleatoire d'OK_consolante, une liste vide reste possible.
#
# Le principal se joue APRES les consolantes : le vainqueur de chaque
# consolante est repeche dans le tableau principal du meme sexe (voir
# ETAPE 4). On le recupere ici, juste apres l'avoir simule.
vainqueur_consolante = {"H": None, "F": None}

for nom_tournoi, sexe, codes in (
    (NOM_CONSOLANTE_HOMMES, "H", codes_conso_h),
    (NOM_CONSOLANTE_FEMMES, "F", codes_conso_f),
):
    if not codes:
        print(f"[3/5] {nom_tournoi} : aucun inscrit, tableau non cree.")
        continue
    try:
        raz = gestionnaire.reinitialiser_resultat(nom_tournoi)
        if raz["supprimes"]:
            print(f"[3/5] {nom_tournoi} : {raz['supprimes']} ancien(s) Resultat supprime(s).")
        gestionnaire.remplir_consolante(nom_tournoi, codes, graine=GRAINE)
        resultat = gestionnaire.simuler_tableau_jusqua_la_finale(nom_tournoi, graine=GRAINE)
        vainqueur_consolante[sexe] = gestionnaire.code_vainqueur(nom_tournoi)
        print(f"[3/5] {nom_tournoi} : tableau cree et simule jusqu'a la Finale "
              f"({resultat['maj']} resultats ecrits). "
              f"Vainqueur -> {vainqueur_consolante[sexe]} (repeche au principal).")
    except ValueError as e:
        print(f"[3/5] {nom_tournoi} : ECHEC ({e}).")


# ============================================================
# ETAPE 4 : PRINCIPAL - creation (1er tour) + simulation complete
# ============================================================
# Comme pour la consolante, Taille_tableau est desormais calculee
# automatiquement (prochaine puissance de 2 au-dessus du nombre total
# de joueurs : proteges + qualifies de poule + repeches de consolante)
# et ecrite dans Airtable par initialiser_tableau_principal - rien a
# pre-remplir a la main sur le Tournoi.

for nom_tournoi, sexe in (
    (NOM_PRINCIPAL_HOMMES, "H"),
    (NOM_PRINCIPAL_FEMMES, "F"),
):
    codes_proteges = codes_proteges_par_sexe(sexe, joueurs_par_id)
    codes_autres = codes_qualifies_poule_par_sexe(sexe, joueurs_par_id)
    codes_repechage = [vainqueur_consolante[sexe]] if vainqueur_consolante[sexe] else []
    print(f"[4/5] {nom_tournoi} : {len(codes_proteges)} protege(s), "
          f"{len(codes_autres)} qualifie(s) de poule, "
          f"{len(codes_repechage)} repeche(s) de consolante.")

    if not codes_proteges and not codes_autres and not codes_repechage:
        print(f"[4/5] {nom_tournoi} : aucun joueur, tableau non cree.")
        continue

    try:
        raz = gestionnaire.reinitialiser_resultat(nom_tournoi)
        if raz["supprimes"]:
            print(f"[4/5] {nom_tournoi} : {raz['supprimes']} ancien(s) Resultat supprime(s).")
        gestionnaire.initialiser_tableau_principal(
            nom_tournoi, codes_proteges, codes_autres,
            codes_repechage_consolante=codes_repechage, graine=GRAINE
        )
        resultat = gestionnaire.simuler_tableau_jusqua_la_finale(nom_tournoi, graine=GRAINE)
        print(f"[4/5] {nom_tournoi} : tableau cree et simule jusqu'a la Finale "
              f"({resultat['maj']} resultats ecrits).")
    except ValueError as e:
        print(f"[4/5] {nom_tournoi} : ECHEC ({e}).")


print("\n[5/5] Termine. Ouvre la page Tableaux du site admin pour verifier l'affichage.")