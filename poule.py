from collections import defaultdict, Counter
#from posix import CLD_CONTINUED
from joueur import *
import random
from faker import Faker
from typing import List, Dict, Tuple, Optional
import itertools
import pandas as pd
import math

import joueur

# prévoir de faire un objet Poule comme étant une liste de liste de joueurs
class Poule:
    def __init__(self, nb_joueur: int) -> None:
        self.nb_joueurs = nb_joueur
        self.nb_gagnant = 0  
        self.nb_console=0
        self.name=""
        self.lieu=""
        self.joueurs: List[Joueur] = []

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
class PoolConfigurationGenerator: # cette classe est deprecated - A supprimer
    # Recompute a plan (N=15..40) that MINIMIZES matches (priorité poules de 3),
    # while enforcing PER-POULE constraint: winners_i <= size_i - 1
    # i.e., au moins 1 éliminé dans chaque poule (aucune poule "tout le monde passe").
    #
    # Constraints:
    # - Poules de 3..5 joueurs -> à changer pour des poules de 4, 5 et 6 en privilégiant les poules de 4 et 5
    # - P <= joueurs à éliminer  (au moins 1 perdant globalement)
    # - P <= Q                  (au moins 1 qualifié par poule)
    # - NEW: Somme max des qualifiés possible = sum(size_i - 1) >= Q
    #
    # Strategy:
    # - For each N, try M in {32,16,8} (largest first), pick feasible configs;
    # - Among feasible, minimize total matches; tie-breakers: more 3s, fewer 5s, more 4s, larger P;
    # - Compute winners-per-pool vector with cap size_i-1, distributing extra qualifiers to larger pools first;
    # - Output winners string like "2213" (order: larger pools first, then any tie-resolved order).
    
    def __init__(self):
        # génération du dataframe des configurations de poules possibles
        rows = [self.plan_for_N_with_caps(N) for N in range(15, 41)]
        self.df_caps = pd.DataFrame(rows)
        #plus tard nous définirons les différents paramètres pour générer des configurations de pool différentes suivant les priorités

    def matches_in_pool(self, n):
        return n * (n - 1) // 2

    def feasible_configs_with_caps(self, players: int, Q: int, eliminated: int) -> List[Tuple[Tuple[int, int, int, int], int, List[int], int]]:
        """
        Génère toutes les configurations de poules possibles pour un nombre donné de joueurs.
        
        Cette fonction trouve toutes les répartitions de joueurs en poules qui respectent les contraintes :
        - Chaque poule doit contenir entre 3 et 5 joueurs
        - Le nombre total de qualifiés possibles (somme des tailles de poules - 1) doit être >= Q
        - Le nombre de poules doit être compatible avec le nombre de joueurs à éliminer
        
        Args:
            players: Nombre total de joueurs à répartir en poules
            Q: Nombre de joueurs à qualifier pour le tableau principal
            eliminated: Nombre de joueurs à éliminer
            
        Returns:
            Liste triée des configurations possibles, chacune contenant (clé_tri, nb_poules, tailles_poules, total_matchs)
            Les configurations sont triées par priorité : moins de matchs, plus de poules de 3, moins de poules de 5
        """
        minP = math.ceil(players / 5)
        maxP = max(1, math.floor(players / 3))
        maxP = min(maxP, eliminated, Q)
        results = []
        
        for P in range(minP, maxP + 1):
            base = players // P
            r = players % P
            sizes = [base + 1] * r + [base] * (P - r)
            
            if not all(3 <= s <= 5 for s in sizes):
                continue
                
            # Per-pool cap feasibility: sum(size_i - 1) must cover Q
            if sum(s - 1 for s in sizes) < Q:
                continue
                
            # Objective
            c = Counter(sizes)
            pools3, pools4, pools5 = c.get(3, 0), c.get(4, 0), c.get(5, 0)
            totm = sum(self.matches_in_pool(s) for s in sizes)
            key = (totm, -pools3, pools5, -pools4, -P)
            results.append((key, P, sizes, totm))
            
        results.sort(key=lambda x: x[0])
        return results
    
    def assign_winners_with_caps(self, sizes, Q):
        """Return a per-pool winners list with sum=Q, each <= size-1, >=1.
        Strategy: start with 1 per pool, then give remaining to largest pools first (cap size-1)."""
        P = len(sizes)
        winners = [1] * P
        remaining = Q - P
        
        # Pools sorted by size desc, ties: keep stable order
        order = sorted(range(P), key=lambda i: sizes[i], reverse=True)
        
        while remaining > 0:
            progressed = False
            for i in order:
                cap = sizes[i] - 1
                if winners[i] < cap:
                    winners[i] += 1
                    remaining -= 1
                    progressed = True
                if remaining == 0:
                    break
            if not progressed:
                # Shouldn't happen due to feasibility check; break to avoid infinite loop
                break
        return winners

    def winners_string_from_list(self, winners):
        return "".join(str(x) for x in winners)

    def plan_for_N_with_caps(self, N: int) -> dict:
        """
        Génère un plan de tournoi optimal pour N joueurs inscrits.
        
        Cette fonction détermine la meilleure configuration de tournoi en testant différents
        tableaux principaux (M=32, 16, 8) et en optimisant la répartition en poules.
        
        Algorithme :
        1. Teste les tableaux principaux de 32, 16, puis 8 joueurs
        2. Pour chaque tableau, calcule le nombre de qualifiés nécessaires (Q)
        3. Détermine la configuration de poules optimale qui minimise les matchs
        4. Répartit les qualifiés entre les poules selon leur taille
        
        Paramètres fixes :
        - seeds = 4 : Nombre de joueurs têtes de série (directement qualifiés)
        - consolante = 1 : Nombre de places pour la consolante
        
        Args:
            N: Nombre total de joueurs inscrits au tournoi (15-40)
            
        Returns:
            Dictionnaire contenant la configuration optimale avec les clés :
            - "Inscrits (N)": Nombre total d'inscrits
            - "Tableau principal (M)": Taille du tableau principal (32, 16, 8)
            - "Joueurs en poules": Nombre de joueurs participant aux poules
            - "Qualifiés à prendre (Q)": Nombre de qualifiés à sélectionner
            - "Joueurs à éliminer": Nombre de joueurs éliminés en poules
            - "Nb de poules (P)": Nombre de poules
            - "Répartition des poules": Format "X×3, Y×4, Z×5 joueurs"
            - "Total matchs poules": Nombre total de matchs en poules
            - "Gagnants par poule": Format "221" (nombre de qualifiés par poule)
            
        Note:
            Si aucune configuration faisable n'est trouvée, retourne un dictionnaire
            avec des valeurs vides et une note explicative.
        """
        seeds = 4
        consolante = 1
        
        # Try M from largest to smallest
        for M in [32, 16, 8]:
            if (M == 32 and N < 17) or (M == 16 and N < 9):
                continue
                
            Q = M - (seeds + consolante)
            players = N - seeds
            eliminated = players - Q
            configs = self.feasible_configs_with_caps(players, Q, eliminated)
            
            if configs:
                _, P, sizes, totm = configs[0]
                winners = self.assign_winners_with_caps(sizes, Q)
                c = Counter(sizes)
                pools3, pools4, pools5 = c.get(3, 0), c.get(4, 0), c.get(5, 0)
                
                return {
                    "Inscrits (N)": N,
                    "Tableau principal (M)": M,
                    "Joueurs en poules": players,
                    "Qualifiés à prendre (Q)": Q,
                    "Joueurs à éliminer": eliminated,
                    "Nb de poules (P)": P,
                    "Répartition des poules (min matchs)": f"{pools3}×3, {pools4}×4, {pools5}×5 joueurs",
                    "Total matchs poules (min)": totm,
                    "Gagnants par poule (format 221)": self.winners_string_from_list(winners)
                }
        
        # No feasible config even with M=8
        return {
            "Inscrits (N)": N,
            "Tableau principal (M)": "",
            "Joueurs en poules": N - 4,
            "Qualifiés à prendre (Q)": "",
            "Joueurs à éliminer": "",
            "Nb de poules (P)": "",
            "Répartition des poules (min matchs)": "",
            "Total matchs poules (min)": "",
            "Gagnants par poule (format 221)": "",
            "Note": "Aucune configuration faisable (même avec caps par poule)"
        }
    
    def displayPoolFullConfigurations(self):
        """
        Affiche les configurations de poules possibles pour le nombre de joueurs inscrits.
        """
        print("in")
        print(self.df_caps)
    
    def get_pool_sizes_list(self, N: int) -> List[int]:
        """
        Retourne la liste des tailles de toutes les poules pour un nombre donné de joueurs.
        
        Cette méthode utilise la configuration optimale générée par plan_for_N_with_caps
        pour extraire les tailles individuelles de chaque poule et les retourner sous
        forme de liste.
        
        Args:
            N: Nombre total de joueurs inscrits au tournoi (15-40)
            
        Returns:
            Liste des tailles de poules. Par exemple :
            - Si configuration = "1×3, 2×4, 3×5 joueurs" → [3, 4, 4, 5, 5, 5]æ
            - Si aucune configuration faisable → []
            
        Example:
            >>> generator = PoolConfigurationGenerator()
            >>> generator.get_pool_sizes_list(25)
            [4, 4, 4, 5, 5]  # Exemple pour 25 joueurs
        """
        # Obtenir la configuration optimale pour N joueurs
        config = self.plan_for_N_with_caps(N)
        
        # Vérifier si une configuration faisable existe
        if not config.get("Nb de poules (P)") or config.get("Note"):
            return []
        
        # Extraire les informations de la configuration
        seeds = 4
        players_in_pools = N - seeds
        P = config["Nb de poules (P)"]
        
        # Recalculer les tailles de poules (même logique que dans plan_for_N_with_caps)
        base = players_in_pools // P
        remainder = players_in_pools % P
        
        # Créer la liste des tailles : les 'remainder' premières poules ont base+1 joueurs,
        # les autres ont 'base' joueurs
        pool_sizes = [base + 1] * remainder + [base] * (P - remainder)
        
        return pool_sizes
class RepartiteurPoulesFixes:
    def __init__(self, joueurs: List[Joueur], tailles_poules: List[int]):
        self.joueurs = joueurs
        self.tailles_poules = sorted(tailles_poules, reverse=True)
        self.nb_poules = len(tailles_poules)
        self.poules =[Poule(taille) for taille in self.tailles_poules]
        self.poids_niveau = 10      # Contrainte la plus importante
        self.poids_familial = 5     # Contrainte importante  
        self.poids_age = 1          # Contrainte d'équilibrage
        # Vérification préalable
        if sum(tailles_poules) != len(joueurs):
            raise ValueError(f"Incompatibilité: {len(joueurs)} joueurs pour {sum(tailles_poules)} places")

    def est_poule_valide(self, poule: Poule) -> bool:
        """Vérifie si une poule respecte toutes les contraintes"""
        if not poule:
            return True
            
        # Contrainte de niveau
        niveaux = [j.niveau for j in poule.getJoueurs()]
        if max(niveaux) - min(niveaux) > 1:
            return False
            
        # Contrainte familiale
        familles = [j.nom for j in poule.getJoueurs()]
        if len(familles) != len(set(familles)):
            return False
            
        return True

    ## DEBUT séquence de méthode pour calculer la répartition avec l'algorithme de Tristan   
            
    def age_moyen_poule(self, ma_poule: Poule) -> float:
        """Calcule l'âge moyen d'une poule"""
        if not ma_poule:
            return 100  # ou une valeur par défaut appropriée
        else:
            somme = sum(j.age for j in ma_poule.getJoueurs())
            return somme / ma_poule.nb_joueurs()

    def niveau_max_poule(self, ma_poule: List[Joueur]) -> int:
        """Trouve le niveau maximum dans une poule"""
        if not ma_poule:
            return 5  # renvoie le niveau maximum possible
        else:
            niveau_max = ma_poule.getJoueurs()[0].niveau
            for mon_joueur in ma_poule.getJoueurs():
                if mon_joueur.niveau > niveau_max:
                    niveau_max = mon_joueur.niveau
            return niveau_max
    def calculer_cout_pour_un_joueur_par_pool(self, joueur: Joueur, ma_poule: Poule) -> float:
        """
        Calcule le coût d'assignation avec priorisation des contraintes.
        Plus le coût est faible, meilleure est l'assignation.
        """
        cout_total = 0
       
        # 1. COÛT NIVEAU (priorité maximale)
        if ma_poule.nbJoueursPoule() > 0:
            niveaux_actuels = [j.niveau for j in ma_poule.getJoueurs()]
            niveau_min_actuel = min(niveaux_actuels)
            niveau_max_actuel = max(niveaux_actuels)
            
            # Nouveau min/max après ajout
            nouveau_min = min(niveau_min_actuel, joueur.niveau)
            nouveau_max = max(niveau_max_actuel, joueur.niveau)
            ecart_niveau = nouveau_max - nouveau_min
            
            # Pénalité exponentielle pour les écarts de niveau > 1
            if ecart_niveau > 1:
                cout_total += self.poids_niveau * (ecart_niveau - 1) ** 2
        
            # 2. COÛT FAMILIAL (priorité élevée)
            noms_actuels = [j.nom for j in ma_poule.getJoueurs()]
            if joueur.nom in noms_actuels:
                cout_total += self.poids_familial
            
            # 3. COÛT ÂGE (équilibrage)
            ages_actuels = [j.age for j in ma_poule.getJoueurs()]
            age_moyen_actuel = sum(ages_actuels) / len(ages_actuels)
            ecart_age = abs(joueur.age - age_moyen_actuel)
            cout_total += self.poids_age * ecart_age
            return cout_total
        else :
            return 15
    def trouver_poule_pour_un_joueur(self, mon_joueur: Joueur) -> Optional[int]:
        """Trouve la poule avec le coût le plus faible pour un joueur"""
        if not self.poules:
            return None
        
        couts = []
        indices_valides = []
        
        for i, ma_poule_actuelle in enumerate(self.poules):
            # Si la poule est pleine, on passe
            if ma_poule_actuelle.nbJoueursPoule() >= self.tailles_poules[i]:
                continue
            
            #cout = self.cout_poule_pour_un_joueur(ma_poule, mon_joueur)
            cout = self.calculer_cout_pour_un_joueur_par_pool(mon_joueur, ma_poule_actuelle)
            #print(cout)
            couts.append(cout)
            indices_valides.append(i)
        
        if not couts:
            return None

        # Retourner l'index de la poule avec le coût minimal
        min_index = couts.index(min(couts))
        return indices_valides[min_index]


    def reset_poule(self) :
        self.poules = [[] for _ in range(self.nb_poules)]

    def repartir_par_couts_TK(self, joueurs: List[Joueur]) -> bool:
        """Assigne les joueurs aux poules selon l'algorithme de coût"""
        # Trier les joueurs par âge et par niveau décroissant
        joueurs_tries = sorted(joueurs, key=lambda j: (-j.niveau, -j.age))
        
        # Parcourir les joueurs et assigner la poule la moins coûteuse par joueur
        for joueur in joueurs_tries:
            i = self.trouver_poule_pour_un_joueur(joueur)
            if i is not None:
                self.poules[i].ajouterJoueur(joueur)    
            else:
                # Impossible d'assigner ce joueur
                print(f"je ne peux pas assigner le joueur {joueur.prenom} {joueur.nom} à une poule")
                return False
        
        # Vérifier que tous les joueurs ont été assignés
        total_joueurs_assignes = sum(poule.nbJoueursPoule() for poule in self.poules)
        return total_joueurs_assignes == len(joueurs)

    ## FIN séquence de méthode pour calculer la répartition avec l'algorithme de Tristan    

    def afficher_resultats(self):
        """Affiche les résultats de la répartition"""
        print(f"\n=== RÉPARTITION EN {self.nb_poules} POULES DE TAILLES {self.tailles_poules} ===")
        
        for i, poule in enumerate(self.poules):
            niveaux = [j.niveau for j in poule.getJoueurs()] if poule.nbJoueursPoule() > 0 else []
            niveau_min = min(niveaux) if niveaux else 0
            niveau_max = max(niveaux) if niveaux else 0
            
            print(f"\nPoule {i+1} ({poule.nbJoueursPoule()}/{self.tailles_poules[i]} joueurs) - Niveaux {niveau_min}-{niveau_max}:")
            for joueur in sorted(poule.getJoueurs(), key=lambda x: -x.niveau):
                print(f"  • {joueur.prenom} {joueur.nom}- age : {joueur.age} - niveau : {joueur.niveau}")

    def exemple_joueurs_fixe():
        # Création des joueurs
        joueurs = [
            Joueur("Martin", "Pierre", 5,False),
            Joueur("Martin", "Paul", 4, False),  # Même famille que Pierre
            Joueur("Dupont", "Marie", 5,False),
            Joueur("Dubois", "Jean", 4,False),
            Joueur("Leroy", "Sophie", 4,False),
            Joueur("Bernard", "Luc", 3,False),
            Joueur("Thomas", "Anne", 3,False),
            Joueur("Petit", "Marc", 3,False),
            Joueur("Robert", "Julie", 2,False),
            Joueur("Richard", "Alex", 2,False),
            Joueur("Moreau", "Emma", 2,False),
            Joueur("Simon", "Tom", 1),False,
            Joueur("Michel", "Lisa", 1,False),
            Joueur("Garcia", "Hugo", 1,False),
            Joueur("Roux", "Clara", 1,False),
            Joueur("Roux", "Max", 2,False),  # Même famille que Clara
        ]
        
        print(f"Nombre total de joueurs: {len(joueurs)}")
        print("Distribution par niveau:")
        niveaux = Counter(j.niveau for j in joueurs)
        for niveau in sorted(niveaux.keys(), reverse=True):
            print(f"  Niveau {niveau}: {niveaux[niveau]} joueurs")
        
        # Tailles de poules fixes : 4, 5, 3, 4 (total = 16)
        tailles_poules = [4, 5, 3, 4]
        print(f"\nTailles de poules imposées: {tailles_poules}")
        
        # Répartition avec backtracking
        repartiteur = RepartiteurPoulesFixes(joueurs, tailles_poules)
        print("\n🔍 Tentative par backtracking...")
        poules = repartiteur.repartir_par_backtracking()
        
        if poules:
            print("✅ Solution trouvée par backtracking!")
            repartiteur.afficher_resultats()
        else:
            print("❌ Pas de solution par backtracking. Tentative par recherche locale...")
            poules = repartiteur.repartir_par_recherche_locale()
            
            if poules:
                print("✅ Solution trouvée par recherche locale!")
                repartiteur.afficher_resultats()
            else:
                print("❌ Aucune solution trouvée. Les contraintes sont trop restrictives.")
                return
        
        # Vérification des contraintes
        print(f"\n=== VÉRIFICATION DES CONTRAINTES ===")
        contraintes_ok = True
        
        for i, poule in enumerate(poules):
            print(f"\nPoule {i+1}:")
            
            # Vérifier la taille
            if len(poule) != tailles_poules[i]:
                print(f"  ❌ Taille incorrecte: {len(poule)} au lieu de {tailles_poules[i]}")
                contraintes_ok = False
            else:
                print(f"  ✅ Taille correcte: {len(poule)}")
            
            if poule:
                niveaux = [j.niveau for j in poule]
                familles = [j.nom for j in poule]
                
                # Vérifier contrainte de niveau
                ecart = max(niveaux) - min(niveaux)
                if ecart > 1:
                    print(f"  ❌ Écart de niveau > 1: {min(niveaux)}-{max(niveaux)} (écart: {ecart})")
                    contraintes_ok = False
                else:
                    print(f"  ✅ Écart de niveau OK: {min(niveaux)}-{max(niveaux)} (écart: {ecart})")
                
                # Vérifier contrainte familiale
                if len(familles) != len(set(familles)):
                    familles_dupliquees = [f for f in set(familles) if familles.count(f) > 1]
                    print(f"  ❌ Familles en double: {familles_dupliquees}")
                    contraintes_ok = False
                else:
                    print(f"  ✅ Pas de conflit familial")
        
        if contraintes_ok:
            print(f"\n🎉 TOUTES LES CONTRAINTES SONT RESPECTÉES!")
        else:
            print(f"\n⚠️  Certaines contraintes ne sont pas respectées.")

   