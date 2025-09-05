#from matplotlib.patches import FancyBboxPatch
#import numpy as np
#import random
#from collections import defaultdict
#import math
from Claude import *
from collections import Counter,defaultdict
import math
import pandas as pd
#from ace_tools import display_dataframe_to_user
import random
from typing import List, Dict, Tuple


class Player:
    def __init__(self, name: str, age: int, level: int, seededPlayer: bool):

        self.level = level
        self.first_name = name.split()[0] if len(name.split()) > 0 else ""
        self.last_name = name.split()[-1] if len(name.split()) > 1 else name
        self.seeded_player = seededPlayer
        self.age = age
    
    def __str__(self):
        return f"{self.name} (Niveau {self.level})"
    
    def __repr__(self):
        return self.__str__()

class RoundRobin:
    def __init__(self, poolConfig :pd.DataFrame) -> None:
            self.myPossiblePools = poolConfig

    def __str__(self):   
        pass
    def __repr__(self):
        pass
    def nbPlayers(self) -> int:
        """
        Calcule le nombre de joueurs uniques dans le DataFrame self.players.
        
        Returns:
            Nombre de joueurs uniques basés sur la colonne 'name'
        """
        if hasattr(self, 'players') and self.players is not None:
            return len(self.players['name'].unique())
        else:
            return 0 
    def addPlayers(self, myPlayers : pd.DataFrame) :
        self.players = myPlayers

    def addPlayersFromCSV(self) :
        pass
    
    def generateRoundRobin(self) -> pd.DataFrame:
        """
        Génère un tableau de round-robin à partir d'un DataFrame de joueurs.
        
        Cette fonction crée un planning de matchs en round-robin en suivant ces étapes :
        1. Détermine le nombre de joueurs uniques via nbPlayers()
        2. Identifie la configuration de poules optimale via self.myPossiblePools
        3. Répartit les joueurs dans les poules selon la configuration
        4. Génère tous les matchs possibles dans chaque poule (round-robin)
        
        Algorithme :
        - À partir du nombre de joueurs, identifier le nombre de poules nécessaire via self.myPossiblePools
        - Répartir équitablement les joueurs dans les poules
            ON commence par les joueurs avec le meilleur rang (R), si il y a moins de joueurs de meilleur rang que de pool on les réparties à partir de la première poule, si il y a plus de joueur de meilleur rang que de pool, on répartie un joueur pzr pool puis on répartie 
            les joueurs restant 1 par 1 en commencant par la première pool jusqu'a ce qu'il n'y est plus de joeur de meilleur rang à classer.
            Ensuite on répartie les rang R-1 de la même manière, on s'assure à chque fois que dans la pool il y a, au maximum un ecart de 1, si possible.
            ainsi de suite jusqu'a réparties tous les joueurs en fonction de leur rang
        - Pour chaque poule, générer tous les matchs possibles (chaque joueur rencontre tous les autres)
        - Organiser les matchs en rounds pour éviter les conflits d'horaires
        
        Returns:
            DataFrame contenant les matchs du round-robin avec les colonnes :
            
        
        Raises:
            ValueError: Si aucun joueur n'est défini ou si la configuration de poules n'est pas trouvée
        """
        pass
#class TournamentGenerator:

class PoolConfigurationGenerator:
# Recompute a plan (N=15..40) that MINIMIZES matches (priorité poules de 3),
# while enforcing PER-POULE constraint: winners_i <= size_i - 1
# i.e., au moins 1 éliminé dans chaque poule (aucune poule "tout le monde passe").
#
# Constraints:
# - Poules de 3..5 joueurs
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

    def matches_in_pool(self,n):
        return n*(n-1)//2

    def feasible_configs_with_caps(self, players: int, Q: int, eliminated: int):
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
            sizes = [base + 1]*r + [base]*(P - r)
            if not all(3 <= s <= 5 for s in sizes):
                continue
        # Per-pool cap feasibility: sum(size_i - 1) must cover Q
            if sum(s - 1 for s in sizes) < Q:
                continue
        # Objective
            c = Counter(sizes)
            pools3, pools4, pools5 = c.get(3,0), c.get(4,0), c.get(5,0)
            totm = sum(self.matches_in_pool(s) for s in sizes)
            key = (totm, -pools3, pools5, -pools4, -P)
            results.append((key, P, sizes, totm))
        results.sort(key=lambda x: x[0])
        return results
    
    def assign_winners_with_caps(self,sizes, Q):
        """Return a per-pool winners list with sum=Q, each <= size-1, >=1.
        Strategy: start with 1 per pool, then give remaining to largest pools first (cap size-1)."""
        P = len(sizes)
        winners = [1]*P
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

    def winners_string_from_list(self,winners):
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
                pools3, pools4, pools5 = c.get(3,0), c.get(4,0), c.get(5,0)
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
    def displayPoolConfigurations(self):
        """
        Affiche les configurations de poules possibles pour le nombre de joueurs inscrits.
        """
        print("in")
        print(self.df_caps)


# class TournamentGenerator:
if __name__ == "__main__":
    print("debut")
    myPossiblePools = PoolConfigurationGenerator()
    myPossiblePools.displayPoolConfigurations()
    print("fin")