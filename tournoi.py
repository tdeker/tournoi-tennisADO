"""
Gestion du tableau de tournoi (Airtable / pyairtable)
======================================================

Fusion de tableau_tournoi.py et de l'ancien tournoi.py :
  - paradigme retenu : PROTECTION DES SEEDS (les joueurs protégés se
    rencontrent le plus tard possible, les autres sont tirés au sort) ;
  - repris de l'ancien tournoi.py : la DÉTECTION DE FAMILLE, basée sur
    le champ Nom de la table Joueur - deux joueurs portant le même Nom
    ne doivent pas se rencontrer au 1er tour. Ici c'est une contrainte
    dure appliquée après le tirage au sort (échanges de positions),
    et non plus une pénalité dans une fonction de coût.

Ce fichier est une LIBRAIRIE : il ne lit aucune variable
d'environnement et ne se connecte pas tout seul à Airtable. Le fichier
principal (main) instancie GestionnaireResultat avec la clé API et le
Base ID, puis appelle ses méthodes.

Architecture :
  - TableauBracket : algorithme PUR de placement en tableau (aucune
    dépendance à Airtable, testable isolément).
  - corriger_conflits_familiaux : fonction PURE de réparation d'un
    placement pour éviter les rencontres familiales au 1er tour.
  - GestionnaireResultat : couche d'accès à Airtable, expose les deux
    fonctions métier :
        - initialiser_tableau_principal(...)
        - remplir_consolante(...)

Exemple d'utilisation depuis un fichier principal :

    from tournoi import GestionnaireResultat

    gestionnaire = GestionnaireResultat(
        api_key="patXXXXXXXXXXXXXX",
        base_id="appXXXXXXXXXXXXXX",
    )

    gestionnaire.initialiser_tableau_principal(
        "Open Simple Messieurs",
        codes_proteges=["J001", "J014", "J022", "J030"],   # ordre = rang
        codes_autres_joueurs=["J045", "J051", "J058"],     # tirés au sort
        graine=None,  # entier (ex: 42) pour un tirage reproductible
    )

    gestionnaire.remplir_consolante(
        "Open Simple Messieurs - Consolante",
        ["J060", "J061", "J062", "J063", "J064"],
    )

Installation :
    pip install pyairtable
"""

import math
import random
import warnings

from pyairtable import Api


# --- Cœur de l'algorithme : placement en tableau (pas d'Airtable ici) ----

class TableauBracket:
    """
    Encapsule l'algorithme de placement en tableau à élimination
    directe, réutilisé aussi bien pour le tableau principal que pour
    la consolante. Ne dépend d'aucune donnée Airtable : elle prend en
    entrée une simple liste déjà triée.

    Important : le "rang" manipulé ici est un simple RANG DE TRI
    algorithmique (la position d'un joueur dans la liste triée passée
    en entrée) - ce n'est PAS le statut officiel "Seed" (tête de
    série) de la table Joueur, qui n'a de sens que pour le tableau
    principal. Pour le principal, l'appelant place les joueurs
    protégés en tête de liste ; pour la consolante, le tri se fait
    par points.

    Le placement respecte la règle sportive standard :
        - rang 1 et rang 2 sont aux deux extrémités du tableau
          (ils ne peuvent se rencontrer qu'en finale) ;
        - rang 3/4 sont chacun dans le quart opposé à 1 et 2 ;
        - et ainsi de suite récursivement.

    S'il y a moins de joueurs que de places, les places restantes sont
    des "BYE". Grâce à la symétrie de l'algorithme, ces BYE se
    retrouvent automatiquement face aux joueurs les mieux classés
    restants (rang 1 en premier, puis 2, puis 3...) : aucune logique
    supplémentaire n'est nécessaire pour attribuer les byes.

    NB : la liste renvoyée par generer_ordre_placement se lit
    "la position i est occupée par le rang ordre[i]" (position->rang).
    L'utiliser dans l'autre sens (rang->position) produirait des
    appariements incorrects dès que le nombre de joueurs classés
    dépasse la moitié du tableau (ex: rang 1 contre rang 5 au 1er
    tour) - c'était un bug de l'ancienne implémentation.
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
        position i du tableau (lecture : position -> rang).
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
        Les positions 2k-1 et 2k (1-based) forment le match k du
        1er tour.
        """
        ordre_placement = self.generer_ordre_placement(self.taille_tableau)
        positions = []
        for i, rang in enumerate(ordre_placement, start=1):
            joueur = (
                self.joueurs_tries[rang - 1]
                if rang <= self.nb_joueurs
                else None
            )
            positions.append({"position": i, "rang": rang, "joueur": joueur})
        return positions


# --- Détection de famille (reprise de l'ancien tournoi.py) ----------------

def _nom_famille(entry):
    """Nom normalisé du joueur d'une entrée de positions (None si bye)."""
    joueur = entry["joueur"]
    if joueur is None:
        return None
    return joueur["fields"].get("Nom", "").strip().lower() or None


def corriger_conflits_familiaux(positions, indices_echangeables, rng):
    """
    Répare un placement pour éviter que deux joueurs portant le même
    Nom (même famille) se rencontrent au 1er tour.

    - positions : liste renvoyée par TableauBracket.calculer_positions()
      (modifiée EN PLACE : seuls les joueurs bougent, les champs
      position/rang restent attachés aux emplacements).
    - indices_echangeables : indices (0-based) de `positions` dont le
      joueur peut être déplacé. Les joueurs protégés et les joueurs
      face à un bye n'en font pas partie : on ne touche ni aux rangs
      protégés ni à l'attribution des byes.
    - rng : instance de random.Random (pour un choix d'échange
      reproductible avec la même graine).

    Stratégie : pour chaque paire du 1er tour en conflit, on tente
    d'échanger l'un de ses joueurs échangeables avec un autre joueur
    échangeable ailleurs dans le tableau, en vérifiant que l'échange
    ne crée pas de nouveau conflit dans les deux paires touchées.

    Retourne la liste des conflits restants (paires insolubles, par
    exemple une famille plus nombreuse que les possibilités
    d'échange) : [(entry_a, entry_b), ...]. À l'appelant de décider
    quoi en faire (ici : warning).
    """

    def conflit(i_pair):
        a, b = positions[i_pair], positions[i_pair + 1]
        na, nb = _nom_famille(a), _nom_famille(b)
        return na is not None and na == nb

    def debut_de_paire(idx):
        return idx - (idx % 2)

    for _ in range(2):  # deux passes suffisent en pratique
        changement = False
        for i in range(0, len(positions), 2):
            if not conflit(i):
                continue
            resolu = False
            for idx in (i, i + 1):
                if idx not in indices_echangeables:
                    continue
                candidats = [k for k in indices_echangeables if debut_de_paire(k) != i]
                rng.shuffle(candidats)
                for k in candidats:
                    positions[idx]["joueur"], positions[k]["joueur"] = (
                        positions[k]["joueur"], positions[idx]["joueur"]
                    )
                    if not conflit(i) and not conflit(debut_de_paire(k)):
                        resolu = True
                        changement = True
                        break
                    # échange annulé : il crée un autre conflit
                    positions[idx]["joueur"], positions[k]["joueur"] = (
                        positions[k]["joueur"], positions[idx]["joueur"]
                    )
                if resolu:
                    break
        if not changement:
            break

    return [
        (positions[i], positions[i + 1])
        for i in range(0, len(positions), 2)
        if conflit(i)
    ]


# --- Couche d'accès Airtable ----------------------------------------------

class GestionnaireResultat:
    """
    À instancier depuis le fichier principal avec les identifiants
    Airtable. Toutes les opérations sur la table Resultat (tableau
    principal, consolante) passent par une instance de cette classe.

        gestionnaire = GestionnaireResultat(api_key="...", base_id="...")
        gestionnaire.initialiser_tableau_principal(...)
        gestionnaire.remplir_consolante(...)
    """

    def __init__(self, api_key, base_id):
        self.api = Api(api_key)
        self.base_id = base_id
        self.table_joueur = self.api.table(base_id, "Joueur")
        self.table_poule_joueur = self.api.table(base_id, "Poule_Joueur")
        self.table_tournoi = self.api.table(base_id, "Tournoi")
        self.table_resultat = self.api.table(base_id, "Resultat")

    # --- Récupération des données Airtable ---

    def _recuperer_tournoi(self, nom_tournoi):
        records = self.table_tournoi.all(formula=f"{{Nom}} = '{nom_tournoi}'")
        if not records:
            raise ValueError(f"Tournoi '{nom_tournoi}' introuvable.")
        return records[0]

    def _recuperer_joueurs_par_codes(self, codes_joueurs):
        """
        Récupère les enregistrements Joueur pour une liste de
        CodeJoueur. L'ordre renvoyé par l'API n'étant pas garanti, on
        ré-ordonne nous-mêmes selon la liste fournie en entrée.
        """
        if not codes_joueurs:
            return []
        formule = "OR(" + ",".join(f"{{CodeJoueur}} = '{c}'" for c in codes_joueurs) + ")"
        records = self.table_joueur.all(formula=formule)
        par_code = {r["fields"]["CodeJoueur"]: r for r in records}
        manquants = [c for c in codes_joueurs if c not in par_code]
        if manquants:
            raise ValueError(f"Joueurs introuvables dans la table Joueur : {manquants}")
        return [par_code[c] for c in codes_joueurs]

    def _recuperer_points_joueur(self, code_joueur):
        """
        Additionne les Points de Poule_Joueur pour un joueur donné.

        Conforme au schéma : Poule_Joueur possède un champ de liaison
        'CodeJoueur' (FK -> Joueur) et un champ numérique 'Points'.
        Dans une formule Airtable, {CodeJoueur} sur un champ lié
        renvoie le champ primaire de l'enregistrement lié (le
        CodeJoueur du joueur), donc la comparaison directe fonctionne.
        """
        records = self.table_poule_joueur.all(formula=f"{{CodeJoueur}} = '{code_joueur}'")
        return sum(r["fields"].get("Points", 0) for r in records)

    # --- Gestion des conflits familiaux ---

    @staticmethod
    def _indices_echangeables(positions, nb_proteges):
        """
        Indices des emplacements dont le joueur peut être déplacé par
        la réparation familiale : joueur présent, non protégé
        (rang > nb_proteges), et dont l'adversaire n'est pas un bye
        (pour ne pas modifier l'attribution des byes).
        L'adversaire d'un indice pair est l'indice impair suivant et
        réciproquement : idx ^ 1.
        """
        return {
            idx
            for idx, p in enumerate(positions)
            if p["joueur"] is not None
            and p["rang"] > nb_proteges
            and positions[idx ^ 1]["joueur"] is not None
        }

    @staticmethod
    def _signaler_conflits(conflits, contexte):
        for a, b in conflits:
            warnings.warn(
                f"[{contexte}] Conflit familial insoluble au 1er tour : "
                f"{a['joueur']['fields'].get('Nom')} (position {a['position']}) "
                f"vs {b['joueur']['fields'].get('Nom')} (position {b['position']})."
            )

    # --- Fonctions métier ---

    def initialiser_tableau_principal(
        self, nom_tournoi, codes_proteges, codes_autres_joueurs, graine=None
    ):
        """
        Initialise la table Resultat pour le TABLEAU PRINCIPAL.

        - nom_tournoi : Nom (PK) du Tournoi tel que défini dans la
          table Tournoi.
        - codes_proteges : liste ORDONNÉE des joueurs "protégés"
          (têtes de série + joueurs pour lesquels on souhaite une
          rencontre la plus tardive possible). Le 1er de la liste
          occupe le rang 1, le 2e le rang 2, etc. : les deux premiers
          ne peuvent se rencontrer qu'en finale, les quatre premiers
          qu'en demi-finale, et ainsi de suite.
        - codes_autres_joueurs : les autres joueurs sélectionnés,
          placés au HASARD dans les positions restantes (pratique
          standard de tirage au sort en tournoi).
        - graine : optionnel. Si fourni (ex: graine=42), le tirage au
          sort ET la réparation familiale sont reproductibles d'une
          exécution à l'autre ; sinon ils diffèrent à chaque fois.

        Deux garanties supplémentaires :
        - Les byes tombent automatiquement face aux protégés, dans
          l'ordre de la liste (rang 1 d'abord).
        - Deux joueurs portant le même Nom (famille) ne se rencontrent
          pas au 1er tour, dans la mesure du possible : le placement
          aléatoire est réparé par échanges entre non-protégés. Si un
          conflit est insoluble, un warning est émis et le placement
          est conservé tel quel.
        """
        tournoi = self._recuperer_tournoi(nom_tournoi)
        taille_tableau = tournoi["fields"]["Taille_tableau"]

        doublons = set(codes_proteges) & set(codes_autres_joueurs)
        if doublons:
            raise ValueError(
                f"Joueurs présents dans les deux listes : {sorted(doublons)}"
            )

        proteges = self._recuperer_joueurs_par_codes(codes_proteges)
        autres = self._recuperer_joueurs_par_codes(codes_autres_joueurs)

        rng = random.Random(graine)
        rng.shuffle(autres)

        joueurs_ordonnes = proteges + autres
        bracket = TableauBracket(joueurs_ordonnes, taille_tableau)
        positions = bracket.calculer_positions()

        # Réparation familiale : seuls les non-protégés qui ne sont
        # pas face à un bye peuvent être déplacés.
        echangeables = self._indices_echangeables(positions, nb_proteges=len(proteges))
        conflits = corriger_conflits_familiaux(positions, echangeables, rng)
        self._signaler_conflits(conflits, contexte=nom_tournoi)

        # Origine conforme au schéma ("Seed, Poule, Consolante") :
        # "Seed" pour les têtes de série officielles (champ Seed=True
        # sur Joueur), "Poule" pour les qualifiés issus des poules.
        def origine_joueur(joueur):
            return "Seed" if joueur["fields"].get("Seed") else "Poule"

        return self._ecrire_resultats(positions, tournoi, origine_joueur)

    def remplir_consolante(self, nom_tournoi_consolante, codes_joueurs_consolante, graine=None):
        """
        Initialise la table Resultat pour la CONSOLANTE.

        - nom_tournoi_consolante : Nom (PK) du Tournoi "consolante"
          (celui dont le champ Tournoi_principal pointe vers le
          principal).
        - codes_joueurs_consolante : les joueurs qui basculent en
          consolante (à fournir par l'appelant).
        - graine : optionnel, pour une réparation familiale
          reproductible.

        Le tri se fait automatiquement par NOMBRE DE POINTS (champ
        Points de Poule_Joueur), du plus élevé au plus faible : ce
        sont donc les joueurs avec le plus de points qui héritent des
        byes en priorité (propriété naturelle de TableauBracket).

        La détection de famille s'applique aussi : les échanges ne
        touchent jamais aux joueurs face à un bye, pour préserver la
        règle "le plus de points face aux byes".
        """
        tournoi = self._recuperer_tournoi(nom_tournoi_consolante)
        taille_tableau = tournoi["fields"].get("Taille_tableau")  # None -> auto

        joueurs = self._recuperer_joueurs_par_codes(codes_joueurs_consolante)
        for j in joueurs:
            j["_points"] = self._recuperer_points_joueur(j["fields"]["CodeJoueur"])
        joueurs.sort(key=lambda j: j["_points"], reverse=True)

        bracket = TableauBracket(joueurs, taille_tableau)
        positions = bracket.calculer_positions()

        # Réparation familiale : en consolante, aucun joueur n'est
        # "protégé" (nb_proteges=0), mais les joueurs face à un bye
        # restent intouchables (exclus par _indices_echangeables).
        rng = random.Random(graine)
        echangeables = self._indices_echangeables(positions, nb_proteges=0)
        conflits = corriger_conflits_familiaux(positions, echangeables, rng)
        self._signaler_conflits(conflits, contexte=nom_tournoi_consolante)

        return self._ecrire_resultats(positions, tournoi, lambda joueur: "Consolante")

    # Colonne Resultat du 1er tour, selon la taille du tableau
    # (convention tennis : T_1_32 = tableau de 64, ..., Finale = tableau de 2)
    _COLONNES_PREMIER_TOUR = {
        64: "T_1_32",
        32: "T_1_16",
        16: "T_1_8",
        8: "T_1_4",
        4: "T_1_2",
        2: "Finale",
    }

    @classmethod
    def _colonne_premier_tour(cls, taille_tableau):
        colonne = cls._COLONNES_PREMIER_TOUR.get(taille_tableau)
        if colonne is None:
            raise ValueError(
                f"Taille de tableau {taille_tableau} non standard (attendu "
                f"une puissance de 2 entre 2 et 64) : impossible de "
                f"déterminer la colonne du 1er tour dans Resultat."
            )
        return colonne

    def _ecrire_resultats(self, positions, tournoi_record, origine_joueur):
        """
        Crée les enregistrements Resultat, un par position du tableau
        (y compris les BYE, pour garder une trace complète et
        pouvoir ensuite générer les matchs du 1er tour
        automatiquement).

        - origine_joueur : fonction joueur -> str, qui renvoie la
          valeur du champ Origine pour ce joueur, parmi les valeurs
          du schéma ("Seed", "Poule", "Consolante").
        - Pour les BYE (position sans joueur), le champ Origine est
          laissé vide : aucune des valeurs autorisées du schéma ne
          correspond, et l'absence de lien Joueur suffit à identifier
          un bye.

        Résultat du 1er tour : quand un joueur est exempté (bye), il
        gagne automatiquement sans jouer - sa colonne du 1er tour
        (voir _colonne_premier_tour) est donc renseignée à "V" dès la
        création de l'enregistrement. Les vrais matchs (deux joueurs
        réels face à face) n'ont pas encore de résultat, leur colonne
        du 1er tour reste vide. Les positions 2k-1 et 2k forment le
        match k du 1er tour (voir TableauBracket.calculer_positions).
        """
        nom_tournoi = tournoi_record["fields"]["Nom"]
        colonne_tour = self._colonne_premier_tour(len(positions))

        nouveaux_records = []
        for i in range(0, len(positions), 2):
            p_a, p_b = positions[i], positions[i + 1]
            joueur_a, joueur_b = p_a["joueur"], p_b["joueur"]
            bye = (joueur_a is None) != (joueur_b is None)  # un seul des deux présent

            for p in (p_a, p_b):
                joueur = p["joueur"]
                champs = {
                    "Ref": f"{nom_tournoi}-{p['position']:03d}",
                    "Position": p["position"],
                    "Tournoi": [tournoi_record["id"]],
                }
                if joueur:
                    champs["Joueur"] = [joueur["id"]]
                    champs["Origine"] = origine_joueur(joueur)
                    if bye:
                        champs[colonne_tour] = "V"
                nouveaux_records.append(champs)

        return self.table_resultat.batch_create(nouveaux_records)