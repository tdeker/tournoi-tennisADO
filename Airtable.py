"""
Gestion du tableau de tournoi (Airtable / pyairtable)
======================================================

Deux fonctions "métier" :
  - initialiser_tableau_principal(...) : place les joueurs sélectionnés
    pour le tableau principal de sorte qu'ils se rencontrent le plus
    tard possible (seeding classique).
  - remplir_consolante(...) : place les joueurs de la consolante en
    triant par nombre de points (table Poule_Joueur) ; les joueurs avec
    le plus de points héritent automatiquement des "byes".

Les deux fonctions s'appuient sur la MÊME classe TableauBracket, qui
encapsule l'algorithme générique de placement (le seul point commun
entre les deux cas est "comment répartir des joueurs triés dans un
tableau d'élimination directe" - le critère de tri, lui, diffère).

Installation :
    pip install pyairtable

Variables d'environnement attendues :
    AIRTABLE_API_KEY
    AIRTABLE_BASE_ID
"""

import math
import os
from pyairtable import Api

# --- Configuration -----------------------------------------------------

AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
BASE_ID = os.environ["AIRTABLE_BASE_ID"]

api = Api(AIRTABLE_API_KEY)
table_joueur = api.table(BASE_ID, "Joueur")
table_poule_joueur = api.table(BASE_ID, "Poule_Joueur")
table_tournoi = api.table(BASE_ID, "Tournoi")
table_resultat = api.table(BASE_ID, "Resultat")


# --- Cœur de l'algorithme : placement en tableau ------------------------

class TableauBracket:
    """
    Encapsule l'algorithme de placement en tableau à élimination
    directe, réutilisé aussi bien pour le tableau principal que pour
    la consolante.

    Important : le "rang" manipulé ici est un simple RANG DE TRI
    algorithmique (la position d'un joueur dans la liste triée passée
    en entrée) - ce n'est PAS le statut officiel "Seed" (tête de
    série) de la table Joueur, qui n'a de sens que pour le tableau
    principal. Pour le principal, l'appelant peut trier sa liste en
    mettant les têtes de série officielles en tête ; pour la
    consolante, le tri se fait par points, et il n'y a pas de tête de
    série - seulement des rangs 1, 2, 3... issus de ce tri.

    Le placement respecte la règle sportive standard :
        - rang 1 et rang 2 sont aux deux extrémités du tableau
          (ils ne peuvent se rencontrer qu'en finale) ;
        - rang 3/4 sont chacun dans le quart opposé à 1 et 2 ;
        - et ainsi de suite récursivement.

    S'il y a moins de joueurs que de places, les places restantes sont
    des "BYE". Grâce à la symétrie de l'algorithme, ces BYE se
    retrouvent automatiquement face aux joueurs les mieux classés
    restants (rang 1 en premier, puis 2, puis 3...) : c'est exactement
    la règle demandée ("le plus de points en face des byes" pour la
    consolante), il n'y a pas de logique supplémentaire à écrire pour
    ça.
    """

    def __init__(self, joueurs_tries, taille_tableau=None):
        """
        joueurs_tries  : liste de dict (enregistrements Airtable),
                         TRIÉE du meilleur au moins bon.
        taille_tableau : taille du tableau (puissance de 2). Si None,
                         on prend la puissance de 2 immédiatement
                         supérieure au nombre de joueurs.
        """
        self.joueurs_tries = joueurs_tries
        self.nb_joueurs = len(joueurs_tries)
        self.taille_tableau = taille_tableau or self._taille_puissance_2(self.nb_joueurs)

        if self.nb_joueurs > self.taille_tableau:
            raise ValueError(
                f"{self.nb_joueurs} joueurs pour un tableau de "
                f"{self.taille_tableau} places : le tableau est trop petit."
            )

    @staticmethod
    def _taille_puissance_2(n):
        if n <= 1:
            return 1
        return 2 ** math.ceil(math.log2(n))

    @staticmethod
    def generer_ordre_placement(taille):
        """
        Retourne une liste de longueur `taille` où l'élément d'indice i
        (0-based) donne le rang de tri (1-based) qui occupe la
        position i du tableau, selon la règle standard décrite
        ci-dessus. Ce rang fait référence à la position du joueur dans
        la liste triée fournie à TableauBracket, pas à un statut Seed.
        """
        ordre = [1]
        while len(ordre) < taille:
            n = len(ordre)
            nouveau = []
            for rang in ordre:
                nouveau.append(rang)
                nouveau.append(2 * n + 1 - rang)
            ordre = nouveau
        return ordre

    def calculer_positions(self):
        """
        Retourne une liste de dict :
            [{"position": 1, "rang": 1, "joueur": {...} ou None}, ...]
        joueur=None signifie un BYE (aucun joueur réel à ce rang).
        """
        ordre_placement = self.generer_ordre_placement(self.taille_tableau)
        positions = []
        for i, rang in enumerate(ordre_placement, start=1):
            joueur = (
                self.joueurs_tries[rang - 1]
                if rang <= self.nb_joueurs
                else None
            )
            positions.append(
                {"position": i, "rang": rang, "joueur": joueur}
            )
        return positions


# --- Récupération des données Airtable ----------------------------------

def recuperer_tournoi(nom_tournoi):
    records = table_tournoi.all(formula=f"{{Nom}} = '{nom_tournoi}'")
    if not records:
        raise ValueError(f"Tournoi '{nom_tournoi}' introuvable.")
    return records[0]


def recuperer_joueurs_par_codes(codes_joueurs):
    """
    Récupère les enregistrements Joueur pour une liste de CodeJoueur.
    L'ordre renvoyé par l'API n'étant pas garanti, on ré-ordonne
    nous-mêmes selon la liste fournie en entrée.
    """
    if not codes_joueurs:
        return []
    formule = "OR(" + ",".join(f"{{CodeJoueur}} = '{c}'" for c in codes_joueurs) + ")"
    records = table_joueur.all(formula=formule)
    par_code = {r["fields"]["CodeJoueur"]: r for r in records}
    manquants = [c for c in codes_joueurs if c not in par_code]
    if manquants:
        raise ValueError(f"Joueurs introuvables dans la table Joueur : {manquants}")
    return [par_code[c] for c in codes_joueurs]


def recuperer_points_joueur(code_joueur):
    """
    Additionne les points de Poule_Joueur pour un joueur donné.

    Hypothèse : la table Poule_Joueur possède un champ 'CodeJoueur' qui
    référence le joueur (champ lookup ou texte selon ta config Airtable
    réelle) - à renommer ici si le champ s'appelle différemment chez
    toi (ex: 'Joueur' si c'est un champ de liaison direct).
    """
    records = table_poule_joueur.all(formula=f"{{CodeJoueur}} = '{code_joueur}'")
    return sum(r["fields"].get("Points", 0) for r in records)


# --- Fonctions métier -----------------------------------------------------

def initialiser_tableau_principal(nom_tournoi, codes_joueurs_selectionnes):
    """
    Initialise la table Resultat pour le TABLEAU PRINCIPAL.

    - nom_tournoi : Nom (PK) du Tournoi tel que défini dans la table Tournoi.
    - codes_joueurs_selectionnes : liste de CodeJoueur, déjà TRIÉE du
      mieux classé au moins bien classé (tête de série n°1 en premier).

    Hypothèse : la SÉLECTION des joueurs pour le principal (qui rentre,
    qui ne rentre pas) est déjà faite en amont, selon ta logique
    propre (ex: Seed=True puis complément par Niveau/classement). Cette
    fonction se charge uniquement du PLACEMENT dans le tableau, pas de
    la sélection elle-même. Adapte le tri de la liste en entrée selon
    ton critère de sélection.
    """
    tournoi = recuperer_tournoi(nom_tournoi)
    taille_tableau = tournoi["fields"]["Taille_tableau"]

    joueurs = recuperer_joueurs_par_codes(codes_joueurs_selectionnes)
    bracket = TableauBracket(joueurs, taille_tableau)
    positions = bracket.calculer_positions()

    return _ecrire_resultats(positions, tournoi, origine="Principal")


def remplir_consolante(nom_tournoi_consolante, codes_joueurs_consolante):
    """
    Initialise la table Resultat pour la CONSOLANTE.

    - nom_tournoi_consolante : Nom (PK) du Tournoi "consolante"
      (celui dont le champ Tournoi_principal pointe vers le principal).
    - codes_joueurs_consolante : les joueurs qui basculent en
      consolante (non retenus pour le principal, ou éliminés au 1er
      tour, selon ton format - à fournir par l'appelant).

    Contrairement au principal (tri fourni par l'appelant selon le
    classement officiel), ici le tri se fait automatiquement par
    NOMBRE DE POINTS (table Poule_Joueur), du plus élevé au plus
    faible : ce sont donc les joueurs avec le plus de points qui
    héritent des byes en priorité (propriété naturelle de
    TableauBracket, voir sa docstring).
    """
    tournoi = recuperer_tournoi(nom_tournoi_consolante)
    taille_tableau = tournoi["fields"].get("Taille_tableau")  # None -> auto

    joueurs = recuperer_joueurs_par_codes(codes_joueurs_consolante)
    for j in joueurs:
        j["_points"] = recuperer_points_joueur(j["fields"]["CodeJoueur"])
    joueurs.sort(key=lambda j: j["_points"], reverse=True)

    bracket = TableauBracket(joueurs, taille_tableau)
    positions = bracket.calculer_positions()

    return _ecrire_resultats(positions, tournoi, origine="Consolante")


def _ecrire_resultats(positions, tournoi_record, origine):
    """
    Crée les enregistrements Resultat, un par position du tableau
    (y compris les BYE, pour garder une trace complète et pouvoir
    ensuite générer les matchs du 1er tour automatiquement).
    """
    nouveaux_records = []
    for p in positions:
        joueur = p["joueur"]
        champs = {
            "Ref": f"{tournoi_record['fields']['Nom']}-{origine}-{p['position']:03d}",
            "Origine": origine if joueur else "BYE",
            "Position": p["position"],
            "Tournoi": [tournoi_record["id"]],
        }
        if joueur:
            champs["Joueur"] = [joueur["id"]]
        nouveaux_records.append(champs)

    return table_resultat.batch_create(nouveaux_records)


# --- Exemple d'utilisation -------------------------------------------------

if __name__ == "__main__":
    # 1) Tableau principal : liste déjà triée (tête de série 1 en premier)
    joueurs_principal = ["J001", "J014", "J022", "J030", "J045", "J051"]
    initialiser_tableau_principal("Open Simple Messieurs", joueurs_principal)

    # 2) Consolante : liste brute, le tri par points est fait par la fonction
    joueurs_consolante = ["J060", "J061", "J062", "J063", "J064"]
    remplir_consolante("Open Simple Messieurs - Consolante", joueurs_consolante)