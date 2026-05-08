# prévoir de faire un objet Poule comme étant une liste de liste de joueurs
from __future__ import annotations
from collections import defaultdict, Counter
#from posix import CLD_CONTINUED
from utiles import NOMS_POULES_LEGENDES_FEMMES, NOMS_POULES_LEGENDES_HOMMES
from joueur import *
import random
from faker import Faker
from typing import List, Dict, Tuple, Optional
import itertools
import math
from typing import List
import statistics
import joueur
from copy import deepcopy


class Poule:
    def __init__(self, nb_joueur: int) -> None:
        # ── attributs originaux ──────────────────
        self.nb_joueurs  = nb_joueur
        self.nb_gagnant  = 0
        self.nb_console  = 0
        self.name        = ""
        self.lieu        = ""
        self.joueurs: List[Joueur] = []

        # ── validation ajoutée ───────────────────
        assert 3 <= nb_joueur <= 5, f"Capacité invalide : {nb_joueur} (attendu 3-5)"

    # ════════════════════════════════════════════
    #  Méthodes originales (inchangées)
    # ════════════════════════════════════════════

    def nbJoueursPoule(self) -> int:
        return len(self.joueurs)

    def taillePoule(self) -> int:
        return self.nb_joueurs

    def nbGagnantsPoule(self) -> int:
        return self.nb_gagnant

    def nomPoule(self) -> str:
        return self.name

    def lieuPoule(self) -> str:
        return self.lieu

    def definirNomPoule(self, nom: str) -> None:
        self.name = nom.strip()

    def definirLieuPoule(self, lieu: str) -> None:
        self.lieu = lieu.strip()

    def definirNbConsole(self, nb_console: int) -> None:
        if nb_console < 0:
            raise ValueError("Le nombre de consoles ne peut pas être négatif")
        self.nb_console = nb_console

    def definirNbGagnantsPoule(self, nb_gagnant: int) -> None:
        if nb_gagnant < 0:
            raise ValueError("Le nombre de gagnants ne peut pas être négatif")
        if nb_gagnant > self.nb_joueurs:
            raise ValueError("Le nombre de gagnants ne peut pas dépasser la taille de la poule")
        self.nb_gagnant = nb_gagnant

    def ajouterJoueur(self, joueur: Joueur) -> bool:
        if self.estComplete():
            return False
        self.joueurs.append(joueur)
        return True

    def retirerJoueur(self, joueur: Joueur) -> bool:
        if joueur not in self.joueurs:
            return False
        self.joueurs.remove(joueur)
        return True

    def getJoueurs(self) -> List[Joueur]:
        return list(self.joueurs)

    def nbJoueursInscrits(self) -> int:
        return len(self.joueurs)

    def placesRestantes(self) -> int:
        return self.nb_joueurs - len(self.joueurs)

    def estComplete(self) -> bool:
        return len(self.joueurs) >= self.nb_joueurs

    def resetJoueurs(self) -> None:
        self.joueurs.clear()

    def __repr__(self) -> str:
        return (
            f"Poule(nom='{self.name}', taille={self.nb_joueurs}, "
            f"inscrits={len(self.joueurs)}, gagnants={self.nb_gagnant})"
        )

    # ════════════════════════════════════════════
    #  Propriétés ajoutées pour l'aalgorithme d'allocation des joueurs dans les poules
    # ════════════════════════════════════════════

    @property
    def capacite(self) -> int:
        """Alias de nb_joueurs — utilisé par AllocationJoueur."""
        return self.nb_joueurs

    @property
    def est_pleine(self) -> bool:
        """Alias de estComplete() — utilisé par AllocationJoueur."""
        return self.estComplete()

    @property
    def est_vide(self) -> bool:
        return len(self.joueurs) == 0

    @property
    def taille(self) -> int:
        """Alias de nbJoueursInscrits() — utilisé par AllocationJoueur."""
        return len(self.joueurs)

    @property
    def niveaux_presents(self) -> set[int]:
        return {j.niveau for j in self.joueurs}

    @property
    def age_moyen(self) -> float | None:
        return statistics.mean(j.age for j in self.joueurs) if self.joueurs else None

    def taux_zone(self, zone: int) -> float:
        if not self.joueurs:
            return 0.0
        return sum(1 for j in self.joueurs if j.zone == zone) / self.taille

    def nb_doublons_niveau(self, niveau: int) -> int:
        return sum(1 for j in self.joueurs if j.niveau == niveau)

    def a_meme_famille(self, joueur: Joueur) -> bool:
        return any(j.nom_famille == joueur.nom_famille for j in self.joueurs)
   
class PoolConfigurationGeneratorByTristan:
    def __init__(self, nb_joueur: int, nb_console: int = 1):
        self.nb_joueurs = nb_joueur
        self.nb_console=nb_console
        self.nb_joueur_poules = self.nb_joueurs - self.nb_console
        self.poules = self.__creation_poules_vides() #création de la liste de poule vide
    def nb_poule(self) -> int:  
        if self.nb_joueurs < 1:
            raise ValueError("n doit être >= 1")    
        return len(self.poules)
    def nb_gagnant(self) -> int: #attention il faut au moins 1 gagnant par poule, donc le nombre de gagnant doit être supérieur aux nombres de poules
        if self.nb_joueurs < 1:
          raise ValueError("n doit être >= 1")
        return 1 << (self.nb_joueurs.bit_length() - 1)  # équivalent à 2**floor(log2(n))
    def matches_in_pool(self, n):
        return n * (n - 1) // 2
    def display_poules(self) -> None:
        for i,poule in enumerate(self.poules, start=1):
            print(f'Poule {i}: {poule.nbJoueursPoule()} joueurs')
    def __creation_poules_vides(self) -> List[Poule]:
        """
        Retourne (a, b) maximisant a tel que n = 4a + 5b, a,b entiers >= 0.
        Renvoie None s'il n'y a pas de solution.
        a est le nombre de poules de 4 joueurs et b est le nombre de poules de 5 joueurs
        le seule cas qui ne fonctionne pas est le nombre de joueurs = 11, c'est le nombre de 
        """
        n=self.nb_joueurs
        if n==11:
             # pas de solution (ex: n = 11) * proposer une solution avec des poules de 3 joueurs
            a=2
            b=0
            c=1
        else :
            b = n % 4              # plus petit b compatible (b ≡ n mod 4)
            a_num = n - 5 * b
            a = a_num // 4
            c=0
 
        #création de la liste des poules possibles
        liste_poules = []
        for i in range(a):
            p=Poule(4)
            liste_poules.append(p)
        for i in range(b):
            p=Poule(5)
            liste_poules.append(p)
        for i in range(c):
            p=Poule(3)
            liste_poules.append(p)
        return liste_poules

        return None
    def get_pool_sizes_list (self) -> List[int]:
        """
        Retourne la liste des tailles de toutes les poules pour le nombre de joueurs inscrits.
        """
        myPools =self.__creation_poules_vides()
        return [p.taillePoule() for p in myPools]

    def get_winners_per_pool(self) -> List[int]:
        """
        Distribue les places en priorité absolue aux plus grandes poules.
        Ordre de priorité : Poules de 5 > Poules de 4 > Poules de 3.
        """
        total_poules = self.nb_poule()
        if total_poules == 0:
            return []

        # 1. Calcul de la cible (ex: 16 qualifiés)
        # Assurez-vous que cette méthode existe et renvoie bien une puissance de 2
        cible_qualifies = self.nb_gagnant()
        
        # 2. Distribution de base
        nb_base = cible_qualifies // total_poules
        reste = cible_qualifies % total_poules
        
        # 3. Initialisation de la liste des résultats avec la base
        # On crée une liste de résultats alignée sur l'ordre actuel de self.poules
        resultats = [nb_base] * total_poules

        # 4. TRI DE PRIORITÉ
        # On récupère les indices des poules, mais on les trie par la taille de la poule associée
        # reverse=True permet d'avoir les 5 en premier, puis les 4, puis les 3
        indices_prioritaires = sorted(
            range(total_poules), 
            key=lambda i: self.poules[i].nbJoueursPoule(), 
            reverse=True
        )
        
        # 5. Distribution du reste (les points bonus)
        # On parcourt les indices dans l'ordre de priorité (les plus grandes poules d'abord)
        for i in range(reste):
            idx = indices_prioritaires[i]
            resultats[idx] += 1
            
        # 6. Mise à jour interne des objets
        for i, nb in enumerate(resultats):
            self.poules[i].nb_gagnant = nb
            
        return resultats

class AllocationJoueur:
    """
    Paramètres
    ----------
    poules   : liste de Poule vides (capacité 3–5 chacune)
    joueurs  : liste de Joueur à affecter
 
    Utilisation
    -----------
    >>> alloc = AllocationJoueur(poules, joueurs)
    >>> alloc.allouer()
    >>> alloc.afficher_resultat()
    >>> score = alloc.score_global()
    """
 
    # Poids des critères
    W_GEO     = 40   # géographie homogène    (priorité 1)
    W_NIVEAU  = 30   # niveaux hétérogènes    (priorité 2)
    W_FAMILLE = 50   # contrainte famille     (priorité 3, quasi-dure)
    W_AGE     = 10   # âge homogène           (priorité 4)
 
    ECART_AGE_MAX = 10  # écart d'âge normalisateur (en années)
 
    def __init__(self, poules: list[Poule], joueurs: list[Joueur]):
        capacite_totale = sum(p.capacite for p in poules)
        if len(joueurs) > capacite_totale:
            raise ValueError(
                f"Trop de joueurs ({len(joueurs)}) "
                f"pour la capacité totale des poules ({capacite_totale})."
            )
       # self.poules  = [deepcopy(p) for p in poules] #    a faire si je ne fveux pas que l'objets Poule soit modifier en déhors de l'objet AllocationJoueur
       self.poules= poules
       self.joueurs = list(joueurs)
       self._nb_swaps = 0
 
    # ─────────────────────────────────────────
    #  Calcul de coût (sur liste de référence)
    # ─────────────────────────────────────────
 
    def _cout_geo(self, joueur: Joueur, joueurs_ref: list[Joueur]) -> float:
        """Priorité 1 — Géographie homogène."""
        if not joueurs_ref:
            return 0.0
        taux = sum(1 for j in joueurs_ref if j.zone == joueur.zone) / len(joueurs_ref)
        return self.W_GEO * (1 - taux)
 
    def _cout_niveau(self, joueur: Joueur, joueurs_ref: list[Joueur],
                     capacite: int) -> float:
        """Priorité 2 — Niveaux hétérogènes. Bonus si tous les niveaux sont couverts."""
        if not joueurs_ref:
            return 0.0
        doublons = sum(1 for j in joueurs_ref if j.niveau == joueur.niveau)
        c = self.W_NIVEAU * (doublons / len(joueurs_ref))
 
        # Bonus : le joueur complète l'ensemble des niveaux cibles
        niveaux_presents = {j.niveau for j in joueurs_ref}
        niveaux_cibles   = set(range(1, min(6, capacite + 1)))
        if (niveaux_presents | {joueur.niveau}) >= niveaux_cibles:
            c -= 5
 
        return max(0.0, c)
 
    def _cout_famille(self, joueur: Joueur, joueurs_ref: list[Joueur]) -> float:
        """Priorité 3 — Contrainte famille (quasi-dure)."""
        if any(j.nom_famille == joueur.nom_famille for j in joueurs_ref):
            return float(self.W_FAMILLE)
        return 0.0
 
    def _cout_age(self, joueur: Joueur, joueurs_ref: list[Joueur]) -> float:
        """Priorité 4 — Âge homogène."""
        if not joueurs_ref:
            return 0.0
        age_moy = statistics.mean(j.age for j in joueurs_ref)
        ecart   = abs(joueur.age - age_moy) / self.ECART_AGE_MAX
        return self.W_AGE * min(ecart, 1.0)
 
    def _cout_joueur_dans_poule(self, joueur: Joueur, poule: Poule,
                                 exclure_id: int = -1) -> float:
        """
        Coût d'un joueur vis-à-vis des autres membres de la poule.
        exclure_id : id à ignorer dans la poule (utile pour les swaps).
        """
        ref = [j for j in poule.joueurs if j.id != exclure_id and j.id != joueur.id]
        return (
            self._cout_geo(joueur, ref)
            + self._cout_niveau(joueur, ref, poule.capacite)
            + self._cout_famille(joueur, ref)
            + self._cout_age(joueur, ref)
        )
 
    def cout(self, joueur: Joueur, poule: Poule) -> float:
        """
        Coût d'affectation d'un joueur dans une poule (poule non modifiée).
        Retourne inf si la poule est pleine.
        """
        if poule.est_pleine:
            return float('inf')
        ref = list(poule.joueurs)
        return (
            self._cout_geo(joueur, ref)
            + self._cout_niveau(joueur, ref, poule.capacite)
            + self._cout_famille(joueur, ref)
            + self._cout_age(joueur, ref)
        )
 
    # ─────────────────────────────────────────
    #  Coût d'une poule complète
    # ─────────────────────────────────────────
 
    def _cout_poule(self, poule: Poule) -> float:
        """Coût total = somme des coûts de chaque joueur vis-à-vis des autres."""
        total = 0.0
        for joueur in poule.joueurs:
            total += self._cout_joueur_dans_poule(joueur, poule)
        return total
 
    def _cout_global(self) -> float:
        return sum(self._cout_poule(p) for p in self.poules)
 
    # ─────────────────────────────────────────
    #  Tri des joueurs par difficulté de placement
    # ─────────────────────────────────────────
 
    def _difficulte(self, joueur: Joueur) -> float:
        """
        Les joueurs les plus difficiles à placer passent en premier :
        famille nombreuse, niveau rare, zone isolée.
        """
        n = len(self.joueurs)
        nb_meme_niveau  = sum(1 for j in self.joueurs if j.niveau       == joueur.niveau)
        nb_meme_famille = sum(1 for j in self.joueurs if j.nom_famille  == joueur.nom_famille)
        nb_meme_zone    = sum(1 for j in self.joueurs if j.zone         == joueur.zone)
 
        return (1 / nb_meme_niveau) + (nb_meme_famille / n) + (1 / nb_meme_zone)
 
    # ─────────────────────────────────────────
    #  Phase 1 : Greedy
    # ─────────────────────────────────────────
 
    def _greedy(self) -> None:
        """Affecte chaque joueur dans la poule de coût minimum."""
        joueurs_tries = sorted(self.joueurs, key=self._difficulte, reverse=True)
 
        for joueur in joueurs_tries:
            meilleure_poule = None
            meilleur_cout   = float('inf')
 
            for poule in self.poules:
                c = self.cout(joueur, poule)
                if c < meilleur_cout:
                    meilleur_cout   = c
                    meilleure_poule = poule
 
            if meilleure_poule is None:
                raise RuntimeError(
                    f"Impossible de placer {joueur} : toutes les poules sont pleines."
                )
            meilleure_poule.joueurs.append(joueur)
 
    # ─────────────────────────────────────────
    #  Phase 2 : Optimisation par swaps 2-opt
    # ─────────────────────────────────────────
 
    def _swap_local(self) -> int:
        """
        Échange des paires de joueurs entre deux poules différentes
        si le swap améliore le coût global. Répète jusqu'à stabilité.
        """
        nb_swaps = 0
        ameliore = True
 
        while ameliore:
            ameliore = False
 
            for p1, p2 in itertools.combinations(self.poules, 2):
                for i in range(len(p1.joueurs)):
                    for k in range(len(p2.joueurs)):
                        j1 = p1.joueurs[i]
                        j2 = p2.joueurs[k]
 
                        cout_avant = self._cout_poule(p1) + self._cout_poule(p2)
 
                        # Effectue le swap
                        p1.joueurs[i] = j2
                        p2.joueurs[k] = j1
 
                        cout_apres = self._cout_poule(p1) + self._cout_poule(p2)
 
                        if cout_apres < cout_avant - 1e-6:
                            # Swap bénéfique → on le conserve
                            nb_swaps += 1
                            ameliore  = True
                        else:
                            # Pas d'amélioration → on annule
                            p1.joueurs[i] = j1
                            p2.joueurs[k] = j2
 
        return nb_swaps
 
    # ─────────────────────────────────────────
    #  Point d'entrée principal
    # ─────────────────────────────────────────
 
    def allouer(self) -> None:
        """Lance l'algorithme complet : greedy + optimisation par swaps."""
        for p in self.poules:
            p.joueurs = []
 
        self._greedy()
        self._nb_swaps = self._swap_local()
 
    # ─────────────────────────────────────────
    #  Score global et diagnostics
    # ─────────────────────────────────────────
 
    def score_global(self) -> float:
        """Coût global de l'allocation (plus bas = meilleur)."""
        return self._cout_global()
 
    def diagnostics(self) -> dict:
        """Rapport détaillé de la qualité de l'allocation."""
        rapport = {}
        for poule in self.poules:
            zones    = [j.zone   for j in poule.joueurs]
            niveaux  = [j.niveau for j in poule.joueurs]
            ages     = [j.age    for j in poule.joueurs]
            familles = [j.nom_famille for j in poule.joueurs]
 
            zone_dom      = max(set(zones), key=zones.count) if zones else None
            taux_zone_dom = zones.count(zone_dom) / len(zones) if zones else 0
 
            rapport[f"Poule_{poule.id}"] = {
                "nb_joueurs"          : poule.taille,
                "niveaux"             : sorted(niveaux),
                "niveaux_uniques"     : len(set(niveaux)) == len(niveaux),
                "zones"               : zones,
                "taux_zone_dominante" : round(taux_zone_dom, 2),
                "age_moyen"           : round(statistics.mean(ages), 1) if ages else None,
                "ecart_type_age"      : round(statistics.stdev(ages), 1) if len(ages) > 1 else 0,
                "collision_famille"   : len(familles) != len(set(familles)),
                "cout_poule"          : round(self._cout_poule(poule), 2),
            }
        rapport["score_global"] = round(self.score_global(), 2)
        rapport["nb_swaps"]     = self._nb_swaps
        return rapport
 
    # ─────────────────────────────────────────
    #  Affichage console
    # ─────────────────────────────────────────
 
    def diagnostics(self) -> dict:
        rapport = {}
        for i, poule in enumerate(self.poules, start=1):  # ← on génère un index
            zones    = [j.zone   for j in poule.joueurs]
            niveaux  = [j.niveau for j in poule.joueurs]
            ages     = [j.age    for j in poule.joueurs]
            familles = [j.nom_famille for j in poule.joueurs]

            zone_dom      = max(set(zones), key=zones.count) if zones else None
            taux_zone_dom = zones.count(zone_dom) / len(zones) if zones else 0

            cle = poule.name if poule.name else f"Poule_{i}"  # ← nom ou index

            rapport[cle] = {
                "nb_joueurs"          : poule.taille,
                "niveaux"             : sorted(niveaux),
                "niveaux_uniques"     : len(set(niveaux)) == len(niveaux),
                "zones"               : zones,
                "taux_zone_dominante" : round(taux_zone_dom, 2),
                "age_moyen"           : round(statistics.mean(ages), 1) if ages else None,
                "ecart_type_age"      : round(statistics.stdev(ages), 1) if len(ages) > 1 else 0,
                "collision_famille"   : len(familles) != len(set(familles)),
                "cout_poule"          : round(self._cout_poule(poule), 2),
            }
        rapport["score_global"] = round(self.score_global(), 2)
        rapport["nb_swaps"]     = self._nb_swaps
        return rapport

    def afficher_resultat(self) -> None:
        print("=" * 62)
        print("  RÉSULTAT DE L'ALLOCATION")
        print("=" * 62)

        for i, poule in enumerate(self.poules, start=1):  # ← index à la place de poule.id
            label = poule.name if poule.name else f"Poule {i}"
            print(f"\n📋 {label}  ({poule.taille}/{poule.capacite} joueurs)")
            print(f"   {'Joueur':<26} {'Niv':>4} {'Zone':>5} {'Âge':>5}  Famille")
            print(f"   {'-'*57}")
            for j in sorted(poule.joueurs, key=lambda x: x.niveau):
                print(f"   {j.prenom+' '+j.nom:<26} {j.niveau:>4} {j.zone:>5}"
                    f" {j.age:>5}  {j.nom_famille}")
            print(f"   → Coût poule : {self._cout_poule(poule):.1f}")

        diag = self.diagnostics()
        print(f"\n{'='*62}")
        print(f"  Score global : {diag['score_global']}"
            f"  |  Swaps effectués : {diag['nb_swaps']}")
        print("=" * 62)

        for i, poule in enumerate(self.poules, start=1):
            cle = poule.name if poule.name else f"Poule_{i}"
            d   = diag[cle]
            if d["collision_famille"]:
                print(f"⚠️  {cle} : collision de famille détectée !")
            if not d["niveaux_uniques"]:
                print(f"⚠️  {cle} : doublons de niveau (inévitable si > 5 joueurs).")
    
 