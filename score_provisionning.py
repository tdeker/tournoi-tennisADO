"""
Provisioning de données de test pour Airtable
==============================================

Librairie pour préparer la base Airtable avec des données de TEST
cohérentes. Comme tournoi.py, ce fichier ne lit aucune variable
d'environnement : le fichier principal instancie ProvisionneurAirtable
avec la clé API et le Base ID.

Champs couverts dans Poule_Joueur (noms conformes au schéma), ÉCRITS
dans Airtable : Victoires, Defaites, Matchs_joues, Points, Est_qualifie.
OK_consolante est aussi CRÉÉ par creer_champs_poule_joueur(), mais
n'est JAMAIS écrit automatiquement en dehors de
provisionner_ok_consolante() (données de test) : c'est une déclaration
du joueur (souhait de jouer la consolante), pas un résultat calculé -
en conditions réelles, il doit être renseigné par le joueur ou
l'organisateur, pas par un script.

Règles appliquées (règlement des poules) :
  - Match de poule = 5 jeux gagnants, sans avantage.
  - Match gagné = 1 point, match perdu = 0 point.
  - nb_gagnant (champ Poule) qualifiés par poule pour le principal
    (2, ou 3 pour les poules de 5-6) - les autres vont en consolante
    s'ils le souhaitent.

Barème Points : victoire = points_victoire + bonus de niveau, défaite
= points_defaite (pas de bonus). Le bonus de niveau, pour une
victoire, vaut max(0, Niveau_adversaire - Niveau_joueur) - récompense
les victoires contre plus fort que soi (Niveau 5 = le plus fort).
Attention : ce bonus peut faire qu'un joueur avec MOINS de victoires
brutes ait plus de Points qu'un autre (ex: 1 victoire contre un
niveau 5 quand on est niveau 1 vaut 1+4=5 points, plus que 3 victoires
à 1 point chacune contre des adversaires de même niveau) - c'est un
choix de règlement assumé, pas un effet de bord.

Cascade de départage en cas d'égalité de Points (du plus au moins
déterminant) :
  1. Points (bonus de niveau déjà inclus)
  2. Confrontation directe entre les joueurs encore à égalité
     (mini-classement sur les seuls matchs qui les opposaient)
  3. Jeux perdus, le moins possible, sur l'ensemble de la poule
  4. Différentiel de jeux (gagnés - perdus), sur l'ensemble de la poule
  5. Tirage au sort - dernier recours, mais le SEUL qui garantit une
     résolution : aucun critère statistique ne peut mathématiquement
     exclure une égalité totale. Le tirage au sort tranche par
     construction.

Étape actuelle du provisioning (Match et Set_tournoi viendront plus
tard) : les jeux et résultats détaillés par match sont simulés pour
appliquer CORRECTEMENT cette cascade, mais cette donnée n'est PAS
écrite dans Airtable (pas de champ dédié pour l'instant - elle
reviendra en rollup depuis Set_tournoi le jour où cette table sera
provisionnée). Conséquence pratique : simulation et détermination des
qualifiés doivent se faire dans le MÊME appel, d'où provisionner_points_poules(),
le point d'entrée recommandé pour tout faire d'un coup.

Est_qualifie est un champ STOCKÉ (pas une formule) : sa valeur de
départ est écrite par provisionner_points_poules() / ecrire_qualifies(), mais
librement corrigeable à la main dans Airtable ensuite (un champ
formule interdirait cette correction manuelle).

Les noms des champs sont configurables à l'instanciation si ta base
utilise d'autres intitulés.

Exemple d'utilisation depuis un fichier principal :

    from provisioning import ProvisionneurAirtable

    prov = ProvisionneurAirtable(
        api_key="patXXXXXXXXXXXXXX",
        base_id="appXXXXXXXXXXXXXX",
    )
    prov.creer_champs_poule_joueur()
    prov.provisionner_points_poules(graine=42)

Installation :
    pip install pyairtable
"""

import random
from itertools import groupby

from pyairtable import Api


class ProvisionneurAirtable:
    """
    Prépare la base Airtable avec des données de test cohérentes.

    - api_key / base_id : identifiants Airtable, fournis par le main.
    - champ_* : noms des colonnes dans Poule_Joueur / Poule, à adapter
      aux intitulés réels de ta base si besoin.
    """

    def __init__(
        self,
        api_key,
        base_id,
        champ_victoires="Victoires",
        champ_defaites="Defaites",
        champ_points="Points",
        champ_matchs_joues="Matchs_joues",
        champ_qualifie="Est_qualifie",
        champ_ok_consolante="OK_consolante",
    ):
        self.api = Api(api_key)
        self.base_id = base_id
        self.table_poule_joueur = self.api.table(base_id, "Poule_Joueur")
        self.table_poule = self.api.table(base_id, "Poule")
        self.champ_victoires = champ_victoires
        self.champ_defaites = champ_defaites
        self.champ_points = champ_points
        self.champ_matchs_joues = champ_matchs_joues
        self.champ_qualifie = champ_qualifie
        self.champ_ok_consolante = champ_ok_consolante

    # --- Création des champs (API de schéma) ---

    def creer_champs_poule_joueur(self):
        """
        Crée dans Poule_Joueur les champs Victoires, Defaites,
        Matchs_joues (nombre entier), Est_qualifie et OK_consolante
        (case à cocher), s'ils n'existent pas déjà.

        Est_qualifie et OK_consolante sont des champs STOCKÉS (pas des
        formules) : Est_qualifie a une valeur de départ calculée par
        ecrire_qualifies() ; OK_consolante matérialise le souhait du
        joueur de jouer la consolante s'il n'est pas qualifié pour le
        principal - une déclaration du joueur, pas un calcul, donc
        purement manuelle (aucune méthode ne l'écrit automatiquement,
        sauf provisionner_ok_consolante() pour du jeu de données de
        test - voir sa docstring).

        Prérequis : le token Airtable doit avoir le scope
        'schema.bases:write' (à cocher lors de la création du
        personal access token). Sans ce scope, l'API renvoie une
        erreur 403.

        Retourne la liste des noms de champs effectivement créés
        (vide si tous existaient déjà).
        """
        schema = self.table_poule_joueur.schema()
        existants = {champ.name for champ in schema.fields}

        crees = []
        champs_nombre = (self.champ_victoires, self.champ_defaites, self.champ_matchs_joues)
        for nom in champs_nombre:
            if nom in existants:
                continue
            self.table_poule_joueur.create_field(
                nom, "number", options={"precision": 0}
            )
            crees.append(nom)

        champs_checkbox = (self.champ_qualifie, self.champ_ok_consolante)
        for nom in champs_checkbox:
            if nom in existants:
                continue
            self.table_poule_joueur.create_field(
                nom,
                "checkbox",
                options={"icon": "check", "color": "greenBright"},
            )
            crees.append(nom)

        return crees

    # --- Simulation (round-robin, jeux et matchs non persistés) ---

    @staticmethod
    def _niveau_joueur(record, champ_niveau_lookup="Niveau_joueur"):
        """
        Extrait le Niveau (int) d'un enregistrement Poule_Joueur, via
        le lookup Niveau_joueur (Lookup CodeJoueur.Niveau). Les champs
        lookup Airtable renvoient une liste même pour un lien simple,
        d'où le dépaquetage. Retourne None si absent/non renseigné.
        """
        valeur = record["fields"].get(champ_niveau_lookup)
        if isinstance(valeur, list):
            valeur = valeur[0] if valeur else None
        if valeur is None:
            return None
        try:
            return int(valeur)
        except (TypeError, ValueError):
            return None

    def _simuler_poules(self, rng, points_victoire, points_defaite):
        """
        Simule un round-robin par poule (chaque paire de joueurs joue
        un match à 5 jeux gagnants, sans avantage). MÉTHODE INTERNE,
        aucune écriture Airtable ici.

        - rng : instance de random.Random déjà initialisée (avec ou
          sans graine) - partagée avec le tirage au sort du départage
          dans provisionner_points_poules(), pour que toute la génération
          d'une exécution reste dans un seul flux aléatoire cohérent.

        Retourne (par_poule, stats, resultats_matchs) où :
          - par_poule : {id_poule: [enregistrements Poule_Joueur]}
          - stats : {id_poule_joueur: {"victoires", "defaites",
            "matchs_joues", "points", "jeux_perdus", "jeux_gagnes",
            "bonus_niveau"}}
          - resultats_matchs : {id_poule: {frozenset({id1, id2}): id_gagnant}}
            résultat de chaque match individuel, utilisé pour la
            confrontation directe lors du départage.

        bonus_niveau : cumul, sur les seules VICTOIRES du joueur, de
        max(0, Niveau_adversaire - Niveau_joueur) - récompense les
        victoires contre plus fort que soi (Niveau 5 = le plus fort).
        Sert uniquement de critère de départage (voir _classer_poule),
        jamais additionné à Points.

        Aucune de ces données de jeu/match n'est écrite dans Airtable
        (voir docstring du module) : elle n'existe qu'en mémoire, le
        temps de cet appel.
        """
        JEUX_POUR_GAGNER = 5

        records = self.table_poule_joueur.all()

        par_poule = {}
        for record in records:
            liens_poule = record["fields"].get("Poule") or []
            if liens_poule:
                par_poule.setdefault(liens_poule[0], []).append(record)

        stats = {}
        resultats_matchs = {}
        for poule_id, membres in par_poule.items():
            n = len(membres)
            victoires = {m["id"]: 0 for m in membres}
            jeux_gagnes = {m["id"]: 0 for m in membres}
            jeux_perdus = {m["id"]: 0 for m in membres}
            bonus_niveau = {m["id"]: 0 for m in membres}
            niveaux = {m["id"]: self._niveau_joueur(m) for m in membres}
            matchs_poule = {}

            # Round-robin : un match par paire, score tiré au sort
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = membres[i], membres[j]
                    gagnant, perdant = (a, b) if rng.random() < 0.5 else (b, a)
                    jeux_perdant = rng.randint(0, JEUX_POUR_GAGNER - 1)

                    victoires[gagnant["id"]] += 1
                    jeux_gagnes[gagnant["id"]] += JEUX_POUR_GAGNER
                    jeux_perdus[gagnant["id"]] += jeux_perdant

                    jeux_gagnes[perdant["id"]] += jeux_perdant
                    jeux_perdus[perdant["id"]] += JEUX_POUR_GAGNER

                    niveau_g = niveaux[gagnant["id"]]
                    niveau_p = niveaux[perdant["id"]]
                    if niveau_g is not None and niveau_p is not None:
                        bonus_niveau[gagnant["id"]] += max(0, niveau_p - niveau_g)

                    matchs_poule[frozenset((a["id"], b["id"]))] = gagnant["id"]

            resultats_matchs[poule_id] = matchs_poule

            for m in membres:
                v = victoires[m["id"]]
                d = (n - 1) - v
                stats[m["id"]] = {
                    "victoires": v,
                    "defaites": d,
                    "matchs_joues": n - 1,
                    # Points inclut le bonus de niveau (voir docstring
                    # du module) : chaque victoire vaut points_victoire
                    # + son bonus d'écart de niveau ; chaque défaite
                    # vaut points_defaite (pas de bonus sur défaite).
                    "points": v * points_victoire + d * points_defaite + bonus_niveau[m["id"]],
                    "jeux_gagnes": jeux_gagnes[m["id"]],
                    "jeux_perdus": jeux_perdus[m["id"]],
                    "bonus_niveau": bonus_niveau[m["id"]],
                }

        return par_poule, stats, resultats_matchs

    # --- Génération des valeurs (écrit V/D/Matchs_joues/Points) ---

    def generer_victoires_defaites(
        self,
        graine=None,
        mettre_a_jour_points=True,
        points_victoire=1,
        points_defaite=0,
    ):
        """
        Remplit Victoires / Defaites / Matchs_joues (et Points si
        mettre_a_jour_points=True) pour tous les enregistrements de
        Poule_Joueur, en simulant un round-robin par poule.

        N'écrit aucun champ de jeu. Si tu as besoin du départage
        complet dans la FOULÉE de cette génération, utilise
        provisionner_points_poules(...) plutôt que d'enchaîner cette méthode
        avec calculer_qualifies() : les jeux et résultats de matchs
        n'existent qu'en mémoire le temps de cet appel-ci et ne
        peuvent donc pas être relus séparément ensuite.

        Retourne un dict récapitulatif :
            {"maj": <nb mis à jour>, "poules": <nb de poules>}
        """
        rng = random.Random(graine)
        par_poule, stats, _ = self._simuler_poules(rng, points_victoire, points_defaite)

        mises_a_jour = []
        for id_, r in stats.items():
            champs = {
                self.champ_victoires: r["victoires"],
                self.champ_defaites: r["defaites"],
                self.champ_matchs_joues: r["matchs_joues"],
            }
            if mettre_a_jour_points:
                champs[self.champ_points] = r["points"]
            mises_a_jour.append({"id": id_, "fields": champs})

        if mises_a_jour:
            self.table_poule_joueur.batch_update(mises_a_jour)

        return {"maj": len(mises_a_jour), "poules": len(par_poule)}

    # --- Départage : cascade garantissant l'absence d'ex aequo ---

    @staticmethod
    def _regrouper_par_cle(membres, cle):
        """Trie par cle (desc) puis regroupe les valeurs identiques,
        en conservant l'ordre relatif des groupes."""
        membres_tries = sorted(membres, key=cle, reverse=True)
        return [list(g) for _, g in groupby(membres_tries, key=cle)]

    def _classer_poule(self, membres, stats_par_id, matchs_poule, rng):
        """
        Retourne le classement complet de la poule (liste d'ids, du
        meilleur au moins bon), en appliquant la cascade de départage
        documentée en tête de module. Chaque étage ne s'applique
        qu'aux joueurs encore à égalité à l'étage précédent.

        Le dernier étage (tirage au sort) garantit qu'aucune égalité
        ne subsiste jamais dans le résultat final.
        """
        ids = [m["id"] for m in membres]
        classement_final = []

        # Étage 1 : Points (inclut déjà le bonus de niveau)
        for groupe_points in self._regrouper_par_cle(ids, lambda i: stats_par_id[i]["points"]):
            if len(groupe_points) == 1:
                classement_final.extend(groupe_points)
                continue

            # Étage 2 : confrontation directe (mini-classement entre
            # les seuls joueurs de ce groupe, sur leurs matchs mutuels)
            victoires_directes = {i: 0 for i in groupe_points}
            for a in groupe_points:
                for b in groupe_points:
                    if a >= b:
                        continue
                    gagnant = matchs_poule.get(frozenset((a, b)))
                    if gagnant is not None:
                        victoires_directes[gagnant] += 1

            for groupe_directe in self._regrouper_par_cle(groupe_points, lambda i: victoires_directes[i]):
                if len(groupe_directe) == 1:
                    classement_final.extend(groupe_directe)
                    continue

                # Étage 3 : jeux perdus (le moins possible -> clé négative)
                for groupe_jp in self._regrouper_par_cle(
                    groupe_directe, lambda i: -stats_par_id[i]["jeux_perdus"]
                ):
                    if len(groupe_jp) == 1:
                        classement_final.extend(groupe_jp)
                        continue

                    # Étage 4 : différentiel de jeux (gagnés - perdus)
                    for groupe_diff in self._regrouper_par_cle(
                        groupe_jp,
                        lambda i: stats_par_id[i]["jeux_gagnes"] - stats_par_id[i]["jeux_perdus"],
                    ):
                        if len(groupe_diff) == 1:
                            classement_final.extend(groupe_diff)
                            continue

                        # Étage 5 : tirage au sort - résout TOUJOURS,
                        # par construction (aucune notion d'égalité
                        # possible dans un mélange aléatoire).
                        melange = groupe_diff[:]
                        rng.shuffle(melange)
                        classement_final.extend(melange)

        assert len(classement_final) == len(ids)
        return classement_final

    def calculer_qualifies(self, donnees_departage=None):
        """
        Calcule, SANS RIEN ÉCRIRE dans Airtable, quels joueurs sont
        qualifiés pour le tableau principal : pour chaque poule, les
        nb_gagnant premiers du classement (voir _classer_poule, cascade
        Points -> confrontation directe -> jeux perdus -> différentiel
        de jeux -> tirage au sort) sont qualifiés.

        - donnees_departage : optionnel, tuple (stats_par_id,
          resultats_matchs, rng) fourni automatiquement par
          provisionner_points_poules() pour un départage complet. Sans ce
          paramètre (appel isolé de calculer_qualifies), le départage
          se limite au champ Points lu dans Airtable - les ex æquo
          éventuels restent en ordre arbitraire (à corriger à la main
          via Est_qualifie si besoin).

        Retourne un dict {id_poule_joueur: bool}.
        """
        poules = {p["id"]: p for p in self.table_poule.all()}
        records = self.table_poule_joueur.all()

        par_poule = {}
        for record in records:
            liens_poule = record["fields"].get("Poule") or []
            if liens_poule:
                par_poule.setdefault(liens_poule[0], []).append(record)

        resultat = {}

        if donnees_departage is not None:
            stats_par_id, resultats_matchs, rng = donnees_departage
            for poule_id, membres in par_poule.items():
                poule = poules.get(poule_id)
                nb_gagnant = (poule or {}).get("fields", {}).get("nb_gagnant", 0)
                matchs_poule = resultats_matchs.get(poule_id, {})
                classement = self._classer_poule(membres, stats_par_id, matchs_poule, rng)
                for rang, id_ in enumerate(classement, start=1):
                    resultat[id_] = rang <= nb_gagnant
            return resultat

        # Repli : pas de données de départage, on ne dispose que de
        # Points tel que stocké dans Airtable.
        for poule_id, membres in par_poule.items():
            poule = poules.get(poule_id)
            nb_gagnant = (poule or {}).get("fields", {}).get("nb_gagnant", 0)
            classement = sorted(
                membres, key=lambda m: m["fields"].get(self.champ_points, 0), reverse=True
            )
            for rang, m in enumerate(classement, start=1):
                resultat[m["id"]] = rang <= nb_gagnant
        return resultat

    def ecrire_qualifies(self, donnees_departage=None):
        """
        Calcule (via calculer_qualifies) puis ÉCRIT Est_qualifie dans
        Poule_Joueur pour tous les enregistrements concernés.

        Attention : cette méthode ÉCRASE la valeur actuelle du champ,
        y compris une correction manuelle que tu aurais faite dans
        Airtable après un précédent appel.

        Retourne un dict {"qualifies": n, "non_qualifies": m}.
        """
        qualifies_par_id = self.calculer_qualifies(donnees_departage)

        mises_a_jour = [
            {"id": id_, "fields": {self.champ_qualifie: qualifie}}
            for id_, qualifie in qualifies_par_id.items()
        ]
        if mises_a_jour:
            self.table_poule_joueur.batch_update(mises_a_jour)

        nb_qualifies = sum(1 for q in qualifies_par_id.values() if q)
        return {
            "qualifies": nb_qualifies,
            "non_qualifies": len(qualifies_par_id) - nb_qualifies,
        }

    # --- Point d'entrée recommandé ---

    def provisionner_points_poules(
        self,
        graine=None,
        points_victoire=1,
        points_defaite=0,
    ):
        """
        Fait tout en une fois, dans le BON ORDRE, avec un départage
        complet et garanti sans ex aequo : simule le round-robin,
        écrit Victoires / Defaites / Matchs_joues / Points, PUIS
        détermine et écrit Est_qualifie en appliquant la cascade de
        départage (confrontation directe -> jeux perdus -> différentiel
        de jeux -> tirage au sort) sur les données simulées à l'instant
        (en mémoire, jamais persistées).

        C'est le point d'entrée à utiliser plutôt que d'enchaîner
        generer_victoires_defaites() et ecrire_qualifies() séparément,
        car ces deux appels séparés perdraient l'information de jeux
        et de matchs nécessaire au départage complet.

        Retourne {"maj": n, "poules": p, "qualifies": q, "non_qualifies": nq}.
        """
        rng = random.Random(graine)
        par_poule, stats, resultats_matchs = self._simuler_poules(
            rng, points_victoire, points_defaite
        )

        mises_a_jour_stats = []
        for id_, r in stats.items():
            mises_a_jour_stats.append({
                "id": id_,
                "fields": {
                    self.champ_victoires: r["victoires"],
                    self.champ_defaites: r["defaites"],
                    self.champ_matchs_joues: r["matchs_joues"],
                    self.champ_points: r["points"],
                },
            })

        if mises_a_jour_stats:
            self.table_poule_joueur.batch_update(mises_a_jour_stats)

        res_qualif = self.ecrire_qualifies((stats, resultats_matchs, rng))

        return {
            "maj": len(mises_a_jour_stats),
            "poules": len(par_poule),
            **res_qualif,
        }

    # --- Provisioning de test pour OK_consolante ---

    def provisionner_ok_consolante(self, graine=None, probabilite=0.7, ecraser=False):
        """
        Coche aléatoirement OK_consolante pour du jeu de données de
        TEST - ce champ matérialise normalement une déclaration du
        joueur (via un formulaire d'inscription, une case cochée à la
        main dans Airtable...), donc aucune autre méthode de cette
        librairie ne l'écrit automatiquement.

        - probabilite : probabilité qu'un joueur coche OK_consolante
          (défaut 0.7, arbitraire - juste pour obtenir un jeu de test
          exploitable).
        - ecraser : si False (défaut), ne touche PAS aux
          enregistrements où OK_consolante est déjà renseigné (True
          ou False explicitement) - pour ne pas écraser une vraie
          déclaration de joueur lors d'un re-provisioning partiel. Si
          True, retire cette protection et recoche tout au hasard.

        Ne s'applique qu'aux joueurs NON qualifiés (Est_qualifie
        falsy) : peu importe la valeur pour un joueur déjà qualifié,
        il va au principal quoi qu'il arrive.

        Retourne {"maj": n}.
        """
        rng = random.Random(graine)
        records = self.table_poule_joueur.all()

        mises_a_jour = []
        for r in records:
            if r["fields"].get(self.champ_qualifie):
                continue
            if not ecraser and self.champ_ok_consolante in r["fields"]:
                continue
            mises_a_jour.append({
                "id": r["id"],
                "fields": {self.champ_ok_consolante: rng.random() < probabilite},
            })

        if mises_a_jour:
            self.table_poule_joueur.batch_update(mises_a_jour)

        return {"maj": len(mises_a_jour)}