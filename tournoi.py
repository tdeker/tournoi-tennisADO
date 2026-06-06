import math
from joueur import *
import math
import random
from typing import List, Optional, Tuple

class Tournoi() :
    import random
from typing import List, Optional, Tuple

class Joueur:
    def __init__(self, name: str, age: int, niveau: int, seededPlayer: bool):
        self.prenom = name.split()[0] if len(name.split()) > 0 else ""
        self.nom = name.split()[-1] if len(name.split()) > 1 else name
        self.tete_de_serie = seededPlayer
        self.age = age
        self.niveau = niveau

    def __repr__(self):
        tag = " (TS)" if self.tete_de_serie else ""
        return f"{self.prenom} {self.nom}{tag}[niv={self.niveau}]"


class Tournoi:
    def __init__(self, joueurs: List[Joueur]):
        self.tetes_de_serie = [j for j in joueurs if j.tete_de_serie]
        self.autres_joueurs = [j for j in joueurs if not j.tete_de_serie]
        self.liste_joueur = joueurs

    # -------------------- scoring --------------------
    @staticmethod
    def calculer_cout(j1: Joueur, j2: Joueur) -> int:
        return (
            abs(j1.niveau - j2.niveau) * 2
            + abs(j1.age - j2.age)
            + (100 if j1.nom.strip().lower() == j2.nom.strip().lower() else 0)
        )

    # -------------------- utilitaires --------------------
    @staticmethod
    def _next_power_of_two(n: int) -> int:
        return 1 if n <= 1 else 1 << (n - 1).bit_length()

    @staticmethod
    def _seed_positions(n: int) -> List[int]:
        """Retourne l'ordre de placement des seeds (1-indexé) pour retarder leurs confrontations."""
        def build(m: int) -> List[int]:
            if m == 1:
                return [1]
            prev = build(m // 2)
            res = []
            for p in prev:
                res.append(p)
                res.append(m + 1 - p)
            return res
        return build(n)

    @staticmethod
    def _match_indices(taille: int) -> List[Tuple[int, int]]:
        return [(i, i + 1) for i in range(0, taille, 2)]

    # -------------------- ÉTAPE 1 : placer les têtes de série --------------------
    def placer_tetes_de_serie(self, taille: int) -> Tuple[List[Optional[Joueur]], List[Joueur]]:
        """
        Crée un plateau de taille 'taille' et y place les têtes de série
        selon l'ordre standard. Retourne (plateau, tetes_ordonnees).
        """
        plateau: List[Optional[Joueur]] = [None] * taille
        tetes = sorted(self.tetes_de_serie, key=lambda j: j.niveau, reverse=True)
        positions = self._seed_positions(taille)  # 1-indexé
        for i, j in enumerate(tetes):
            if i >= taille:
                break
            plateau[positions[i] - 1] = j
        return plateau, tetes

    # -------------------- ÉTAPE 2 : distribuer les BYES aux meilleures seeds --------------------
    def attribuer_byes_aux_meilleures_tetes(
        self,
        plateau: List[Optional[Joueur]],
        matchs: List[Tuple[int, int]],
        tetes_ordonnees: List[Joueur],
        nb_byes: int
    ) -> Tuple[List[Tuple[int, Joueur, int]], int]:
        """
        Identifie les matchs avec exactement 1 seed et 1 case vide, puis place
        des byes (None) d'abord pour les meilleures seeds tant qu'il reste des byes.
        Retourne (slots_restants_1seed, nb_byes_restant)
        où slots_restants_1seed = [(m_idx, seed_j, empty_pos), ...]
        """
        # Liste initiale des slots 1-seed
        slots_1seed = []
        for m_idx, (a, b) in enumerate(matchs):
            A, B = plateau[a], plateau[b]
            if (A is not None and A.tete_de_serie and B is None):
                slots_1seed.append((m_idx, A, b))
            elif (B is not None and B.tete_de_serie and A is None):
                slots_1seed.append((m_idx, B, a))

        if nb_byes <= 0 or not slots_1seed:
            return slots_1seed, nb_byes

        # Rang de seed (1 = meilleure)
        rank = {j: i + 1 for i, j in enumerate(tetes_ordonnees)}

        # Trier slots par rang de la seed (meilleure d'abord)
        slots_tries = sorted(slots_1seed, key=lambda t: rank.get(t[1], 10**9))

        # Donner des byes tant que possible
        pris = set()
        for m_idx, seed_j, empty_pos in slots_tries:
            if nb_byes <= 0:
                break
            # Laisser la case vide = bye
            pris.add((m_idx, seed_j, empty_pos))
            nb_byes -= 1

        # Slots restants (ceux qui n'ont PAS reçu de bye)
        slots_restants = [s for s in slots_1seed if s not in pris]
        return slots_restants, nb_byes

    # -------------------- ÉTAPE 3 : matrice de coût contre les slots à 1 seed --------------------
    def construire_matrice_cout(
        self,
        autres: List[Joueur],
        slots_1seed: List[Tuple[int, Joueur, int]]
    ) -> List[List[int]]:
        """
        Construit la matrice des coûts C où C[i][k] = coût entre 'autres[i]' et la seed du slot k.
        slots_1seed contient des tuples (m_idx, seed_joueur, empty_pos).
        """
        mat = []
        for j in autres:
            ligne = []
            for (_, seed_j, _pos) in slots_1seed:
                ligne.append(self.calculer_cout(j, seed_j))
            mat.append(ligne)
        return mat

    # -------------------- ÉTAPE 4 : affecter non-seeds aux slots 1-seed (glouton) --------------------
    def affecter_autres_glouton(
        self,
        autres: List[Joueur],
        slots_1seed: List[Tuple[int, Joueur, int]],
        mat_cout: List[List[int]]
    ) -> Tuple[List[Tuple[int, int, Joueur]], List[Joueur]]:
        """
        Heuristique gloutonne:
        on trie toutes les paires (joueur i, slot k) par coût croissant
        et on prend sans conflits.
        Retourne (affectations, autres_restants)
        où affectations = [(m_idx, empty_pos, joueur), ...]
        """
        if not autres or not slots_1seed:
            return [], autres[:]

        candidats = []
        for i, joueur in enumerate(autres):
            for k, (m_idx, _seed_j, empty_pos) in enumerate(slots_1seed):
                candidats.append((mat_cout[i][k], i, k, m_idx, empty_pos))
        candidats.sort(key=lambda x: x[0])

        joueurs_pris = set()
        slots_pris = set()
        affectations = []
        for _c, i, k, m_idx, empty_pos in candidats:
            if i in joueurs_pris or k in slots_pris:
                continue
            affectations.append((m_idx, empty_pos, autres[i]))
            joueurs_pris.add(i)
            slots_pris.add(k)

        autres_restants = [j for idx, j in enumerate(autres) if idx not in joueurs_pris]
        return affectations, autres_restants

    # -------------------- ÉTAPE 5 : apparier les autres entre eux (matchs sans seed) --------------------
    def apparier_autres_min_cout(
        self,
        autres: List[Joueur],
        nb_byes_restants: int,
        nb_matchs_0seed: int
    ) -> List[Tuple[Optional[Joueur], Optional[Joueur]]]:
        """
        Crée jusqu'à 'nb_matchs_0seed' paires (j1, j2) en min-coût glouton.
        Ajoute des None (byes restants) si nécessaire pour compléter.
        """
        paires: List[Tuple[Optional[Joueur], Optional[Joueur]]] = []
        restants = autres[:]

        # Glouton: à chaque étape, prendre la meilleure paire
        while len(paires) < nb_matchs_0seed and len(restants) >= 2:
            best = None  # (cout, i, j)
            for i in range(len(restants)):
                for j in range(i + 1, len(restants)):
                    c = self.calculer_cout(restants[i], restants[j])
                    if best is None or c < best[0]:
                        best = (c, i, j)
            _, i, j = best
            b = restants.pop(j)
            a = restants.pop(i)
            paires.append((a, b))

        # S'il reste un joueur non appairé et on a encore de la place
        if len(paires) < nb_matchs_0seed and len(restants) == 1:
            # Ce joueur prend un bye si disponible, sinon il restera à placer vide
            bye = None if nb_byes_restants > 0 else None
            paires.append((restants.pop(), bye))
            nb_byes_restants = max(0, nb_byes_restants - 1)

        # Compléter avec des byes si on n'a pas atteint nb_matchs_0seed
        while len(paires) < nb_matchs_0seed:
            # Deux byes si possible, sinon (None, None) quand même pour boucher le trou
            left = None if nb_byes_restants > 0 else None
            if nb_byes_restants > 0:
                nb_byes_restants -= 1
            right = None if nb_byes_restants > 0 else None
            if nb_byes_restants > 0:
                nb_byes_restants -= 1
            paires.append((left, right))

        return paires

    # -------------------- Orchestrateur --------------------
    def generer_tableau_premier_tour_min_cout(
        self, seed_random: Optional[int] = None
    ) -> List[Tuple[Optional[Joueur], Optional[Joueur]]]:
        """
        1) Place les têtes de série.
        2) Donne les byes d'abord aux meilleures têtes.
        3) Affecte les autres joueurs aux matchs 1-seed (min-coût glouton).
        4) Apparier les joueurs restants sur les matchs 0-seed (min-coût glouton).
        """
        if seed_random is not None:
            random.seed(seed_random)

        total = len(self.liste_joueur)
        taille = self._next_power_of_two(total)
        nb_byes = taille - total

        # Étape 1
        plateau, tetes_ordonnees = self.placer_tetes_de_serie(taille)
        matchs = self._match_indices(taille)

        # Étape 2
        slots_1seed, nb_byes = self.attribuer_byes_aux_meilleures_tetes(
            plateau, matchs, tetes_ordonnees, nb_byes
        )

        # Préparer listes de matchs 0-seed
        matchs_0seed = []
        for m_idx, (a, b) in enumerate(matchs):
            A, B = plateau[a], plateau[b]
            if A is None and B is None:
                matchs_0seed.append((m_idx, a, b))

        # Étape 3 : matrice de coût contre seeds
        autres = self.autres_joueurs[:]
        mat_cout = self.construire_matrice_cout(autres, slots_1seed)

        # Étape 4 : affectation gloutonne (matchs à 1 seed)
        affectations_1seed, autres_restants = self.affecter_autres_glouton(
            autres, slots_1seed, mat_cout
        )
        for m_idx, pos, j in affectations_1seed:
            plateau[pos] = j  # on remplit le slot vide du match

        # Étape 5 : apparier les autres (matchs sans seed)
        paires_0seed = self.apparier_autres_min_cout(
            autres_restants, nb_byes_restants=nb_byes, nb_matchs_0seed=len(matchs_0seed)
        )
        for (m_info, pair) in zip(matchs_0seed, paires_0seed):
            _m_idx, a, b = m_info
            j0, j1 = pair
            plateau[a] = j0
            plateau[b] = j1

        # Sortie matches (tuples)
        matches_out: List[Tuple[Optional[Joueur], Optional[Joueur]]] = []
        for i in range(0, taille, 2):
            matches_out.append((plateau[i], plateau[i + 1]))
        return matches_out


# ------------------------- Exemple d'utilisation -------------------------
if __name__ == "__main__":
    joueurs = [
        Joueur("Alice Dupont", 28, 95, True),
        Joueur("Bob Martin", 31, 90, True),
        Joueur("Chloé Bernard", 22, 85, True),
        Joueur("David Leroy", 26, 80, True),
        Joueur("Eva Morel", 24, 70, False),
        Joueur("Franck Simon", 29, 68, False),
        Joueur("Gilles Petit", 33, 66, False),
        Joueur("Hugo Garcia", 21, 60, False),
        Joueur("Inès Robin", 23, 55, False),
        Joueur("Jules Robert", 27, 50, False),
    ]

    t = Tournoi(joueurs)
    tableau = t.generer_tableau_premier_tour_min_cout(seed_random=42)
    for i, (a, b) in enumerate(tableau, start=1):
        print(f"Match {i:02d} : {a}  vs  {b}")

    
    