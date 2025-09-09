from collections import defaultdict, Counter
import random
from faker import Faker
from typing import List, Dict, Tuple, Optional
import itertools


# prévoir de faire un objet Poule comme étant une liste de liste de joueurs
class Poule :
    def __init__(self) -> None:
            pass    

class Joueur:
    def __init__(self, name: str, age: int,niveau: int, seededPlayer: bool):
        self.prenom = name.split()[0] if len(name.split()) > 0 else ""
        self.nom = name.split()[-1] if len(name.split()) > 1 else name # attention il va y avoir des problèmes sur les noms de famille composés
        self.tete_de_serie = seededPlayer
        self.age = age
        self.niveau = niveau
    
    def __str__(self):
        return f"{self.nom} (Niveau {self.niveau})"
    
    def __repr__(self):
        return self.__str__()

# A supprimer
class Old_Joueur: 
    def __init__(self, nom: str, prenom: str, niveau: int):
        self.nom = nom
        self.prenom = prenom
        self.niveau = niveau
        self.nom_famille = nom.split()[0] if ' ' in nom else nom
    
    def __repr__(self):
        return f"{self.prenom} {self.nom} (N{self.niveau})"

class RepartiteurPoulesFixes:
    def __init__(self, joueurs: List[Joueur], tailles_poules: List[int]):
        self.joueurs = joueurs
        self.tailles_poules = tailles_poules
        self.nb_poules = len(tailles_poules)
        self.poules = [[] for _ in range(self.nb_poules)]
        
        # Vérification préalable
        if sum(tailles_poules) != len(joueurs):
            raise ValueError(f"Incompatibilité: {len(joueurs)} joueurs pour {sum(tailles_poules)} places")
    
    def est_poule_valide(self, poule: List[Joueur]) -> bool:
        """Vérifie si une poule respecte toutes les contraintes"""
        if not poule:
            return True
            
        # Contrainte de niveau
        niveaux = [j.niveau for j in poule]
        if max(niveaux) - min(niveaux) > 1:
            return False
        
        # Contrainte familiale
        familles = [j.nom for j in poule]
        if len(familles) != len(set(familles)):
            return False
            
        return True
    
    def peut_ajouter_joueur(self, joueur: Joueur, poule_idx: int) -> bool:
        """Vérifie si un joueur peut être ajouté à une poule donnée"""
        # Vérifier si la poule est pleine
        if len(self.poules[poule_idx]) >= self.tailles_poules[poule_idx]:
            return False
        
        # Tester la validité avec ce joueur ajouté
        poule_test = self.poules[poule_idx] + [joueur]
        return self.est_poule_valide(poule_test)
    
    def calculer_score_assignation(self, assignation: List[List[Joueur]]) -> float:
        """Calcule la qualité d'une assignation complète"""
        score_total = 0
        
        for poule in assignation:
            if not poule:
                continue
                
            niveaux = [j.niveau for j in poule]
            
            # Écart de niveau (à minimiser)
            ecart = max(niveaux) - min(niveaux)
            score_total += ecart
            
            # Variance des niveaux (à minimiser pour plus d'homogénéité)
            if len(niveaux) > 1:
                moyenne = sum(niveaux) / len(niveaux)
                variance = sum((n - moyenne)**2 for n in niveaux) / len(niveaux)
                score_total += variance * 0.1
        
        return score_total
    
    def repartir_par_backtracking(self) -> Optional[List[List[Joueur]]]:
        """Algorithme principal: backtracking avec optimisation"""
        
        # 1. Analyser les contraintes pour détecter l'impossibilité précoce
        if not self.verifier_faisabilite():
            return None
        
        # 2. Trier les joueurs par ordre de difficulté de placement
        joueurs_tries = self.trier_joueurs_par_difficulte()
        
        # 3. Backtracking avec élagage
        meilleure_solution = self.backtrack(joueurs_tries, 0)
        
        if meilleure_solution:
            self.poules = meilleure_solution
            return self.poules
        
        return None
    
    def verifier_faisabilite(self) -> bool:
        """Vérifications préliminaires de faisabilité"""
        
        # Vérifier les contraintes familiales
        familles = defaultdict(list)
        for joueur in self.joueurs:
            familles[joueur.nom].append(joueur)
        
        # Une famille ne peut pas avoir plus de membres que de poules
        for nom_famille, membres in familles.items():
            if len(membres) > self.nb_poules:
                print(f"❌ Impossible: Famille {nom_famille} a {len(membres)} membres pour {self.nb_poules} poules")
                return False
        
        # Vérifier la distribution des niveaux
        niveaux = Counter(j.niveau for j in self.joueurs)
        
        # Pour chaque niveau, vérifier qu'il peut être réparti
        for niveau, count in niveaux.items():
            # Calculer combien de places sont disponibles pour ce niveau
            places_compatibles = 0
            for taille in self.tailles_poules:
                # Dans le pire cas, une poule pourrait être remplie avec ce niveau ± 1
                places_compatibles += taille
            
            if count > places_compatibles:
                print(f"❌ Impossible: {count} joueurs niveau {niveau} pour {places_compatibles} places compatibles max")
                return False
        
        return True
    
    def trier_joueurs_par_difficulte(self) -> List[Joueur]:
        """Trie les joueurs par ordre de difficulté de placement"""
        
        # Compter les membres par famille
        familles = defaultdict(list)
        for joueur in self.joueurs:
            familles[joueur.nom].append(joueur)
        
        def calculer_difficulte(joueur):
            score_difficulte = 0
            
            # Plus une famille est nombreuse, plus c'est difficile
            taille_famille = len(familles[joueur.nom])
            score_difficulte += taille_famille * 10
            
            # Les niveaux extrêmes sont plus difficiles à placer
            if joueur.niveau == 1 or joueur.niveau == 5:
                score_difficulte += 5
            
            # Ajouter un peu d'aléatoire pour éviter les biais
            score_difficulte += random.random()
            
            return score_difficulte
        
        return sorted(self.joueurs, key=calculer_difficulte, reverse=True)
    
    def backtrack(self, joueurs: List[Joueur], index: int) -> Optional[List[List[Joueur]]]:
        """Algorithme de backtracking récursif"""
        
        # Cas de base: tous les joueurs sont placés
        if index >= len(joueurs):
            # Vérifier que toutes les poules ont la bonne taille
            for i, taille_requise in enumerate(self.tailles_poules):
                if len(self.poules[i]) != taille_requise:
                    return None
            
            # Retourner une copie de la solution
            return [poule[:] for poule in self.poules]
        
        joueur_actuel = joueurs[index]
        
        # Essayer de placer le joueur dans chaque poule
        for i in range(self.nb_poules):
            if self.peut_ajouter_joueur(joueur_actuel, i):
                # Placer le joueur
                self.poules[i].append(joueur_actuel)
                
                # Appel récursif
                solution = self.backtrack(joueurs, index + 1)
                if solution:
                    return solution
                
                # Backtrack: retirer le joueur
                self.poules[i].remove(joueur_actuel)
        
        # Aucune solution trouvée à ce niveau
        return None
    
    def repartir_par_recherche_locale(self) -> Optional[List[List[Joueur]]]:
        """Alternative: recherche locale avec redémarrages"""
        
        meilleure_solution = None
        meilleur_score = float('inf')
        
        # Essayer plusieurs configurations initiales
        for tentative in range(50):  # 50 tentatives maximum
            
            # Générer une solution initiale aléaoire (potentiellement invalide)
            self.generer_solution_initiale()
            
            # Améliorer par recherche locale
            solution_amelioree = self.ameliorer_solution_locale()
            
            if solution_amelioree:
                score = self.calculer_score_assignation(solution_amelioree)
                if score < meilleur_score:
                    meilleur_score = score
                    meilleure_solution = solution_amelioree
        
        if meilleure_solution:
            self.poules = meilleure_solution
            return self.poules
        
        return None
    
    def generer_solution_initiale(self):
        """Génère une solution initiale en respectant les tailles"""
        self.poules = [[] for _ in range(self.nb_poules)]
        joueurs_melanges = self.joueurs[:]
        random.shuffle(joueurs_melanges)
        
        # Répartir les joueurs selon les tailles requises
        index = 0
        for i, taille in enumerate(self.tailles_poules):
            self.poules[i] = joueurs_melanges[index:index + taille]
            index += taille
    
    def ameliorer_solution_locale(self, max_iterations=1000) -> Optional[List[List[Joueur]]]:
        """Améliore une solution par échanges locaux"""
        
        for iteration in range(max_iterations):
            amelioration = False
            
            # Essayer tous les échanges possibles entre poules
            for i in range(self.nb_poules):
                for j in range(i + 1, self.nb_poules):
                    # Essayer d'échanger des joueurs entre poules i et j
                    if len(self.poules[i]) > 0 and len(self.poules[j]) > 0:
                        for idx_a in range(len(self.poules[i])):
                            for idx_b in range(len(self.poules[j])):
                                joueur_a = self.poules[i][idx_a]
                                joueur_b = self.poules[j][idx_b]
                                
                                # Effectuer l'échange temporaire
                                self.poules[i][idx_a] = joueur_b
                                self.poules[j][idx_b] = joueur_a
                                
                                # Vérifier si les deux poules sont maintenant valides
                                if (self.est_poule_valide(self.poules[i]) and 
                                    self.est_poule_valide(self.poules[j])):
                                    amelioration = True
                                    break
                                else:
                                    # Annuler l'échange
                                    self.poules[i][idx_a] = joueur_a
                                    self.poules[j][idx_b] = joueur_b
                            
                            if amelioration:
                                break
                    
                    if amelioration:
                        break
                
                if amelioration:
                    break
            
            # Si aucune amélioration, vérifier si la solution est complètement valide
            if not amelioration:
                if self.solution_complete_valide():
                    return [poule[:] for poule in self.poules]
                else:
                    break
        
        return None
    
    def solution_complete_valide(self) -> bool:
        """Vérifie si la solution actuelle est complètement valide"""
        for i, poule in enumerate(self.poules):
            if len(poule) != self.tailles_poules[i]:
                return False
            if not self.est_poule_valide(poule):
                return False
        return True
    
    def afficher_resultats(self):
        """Affiche les résultats de la répartition"""
        print(f"\n=== RÉPARTITION EN {self.nb_poules} POULES DE TAILLES {self.tailles_poules} ===")
        
        for i, poule in enumerate(self.poules):
            niveaux = [j.niveau for j in poule] if poule else []
            niveau_min = min(niveaux) if niveaux else 0
            niveau_max = max(niveaux) if niveaux else 0
            
            print(f"\nPoule {i+1} ({len(poule)}/{self.tailles_poules[i]} joueurs) - Niveaux {niveau_min}-{niveau_max}:")
            for joueur in sorted(poule, key=lambda x: -x.niveau):
                print(f"  • {joueur}")


def creation_joueurs(nb_inscris: int, nb_seededPlayer: int) -> List[Joueur]:
    """
    Génère automatiquement une liste de joueurs.
    
    Args:
        nb_inscris (int): Nombre total de joueurs à créer
        nb_seededPlayer (int): Nombre de joueurs têtes de série (compris dans nb_inscris)
    
    Returns:
        List[Joueur]: Liste des joueurs générés
    
    Raises:
        ValueError: Si nb_seededPlayer > nb_inscris
    """
    if nb_seededPlayer > nb_inscris:
        raise ValueError("Le nombre de têtes de série ne peut pas être supérieur au nombre total d'inscrits")
    
    fake = Faker('fr_FR')  # Utilise les données françaises
    joueurs = []
    
    # Distribution des niveaux (plus de bas niveaux que de hauts niveaux)
    niveaux_poids = [40, 30, 20, 7, 3]  # Poids pour niveaux 1, 2, 3, 4, 5
    niveaux_choix = [1, 2, 3, 4, 5]
    
    # Créer les joueurs têtes de série (niveaux plus élevés)
    for i in range(nb_seededPlayer):
        name = fake.name()
        age = random.randint(7, 17)  # Âge entre 7 et 17 ans
        # Les têtes de série ont plus de chances d'avoir des niveaux élevés (3, 4, 5)
        niveau = random.choices([3, 4, 5], weights=[30, 40, 30])[0]
        joueur = Joueur(name, age, niveau, True)
        joueurs.append(joueur)
    
    # Créer les joueurs non têtes de série
    for i in range(nb_inscris - nb_seededPlayer):
        name = fake.name()
        age = random.randint(7, 17)  # Âge entre 7 et 17 ans
        # Distribution pondérée favorisant les bas niveaux (1, 2, 3)
        niveau = random.choices(niveaux_choix, weights=niveaux_poids)[0]
        joueur = Joueur(name, age, niveau, False)
        joueurs.append(joueur)
    
    # Mélanger la liste pour avoir un ordre aléatoire
    random.shuffle(joueurs)
    
    return joueurs



# Exemple d'utilisation avec tailles fixes
def exemple_joueurs_aleatoires():
    joueurs = creation_joueurs(20, 4)
    print("Liste des joueurs générés (7-17 ans, niveaux 1-5) :")
    print("=" * 60)
    
    # Afficher les têtes de série
    print("🏆 TÊTES DE SÉRIE :")
    tetes_de_serie = [j for j in joueurs if j.tete_de_serie]
    for joueur in sorted(tetes_de_serie, key=lambda x: x.niveau, reverse=True):
        print(f"  {joueur} - {joueur.age} ans")
    
    print("\n👥 AUTRES JOUEURS :")
    autres_joueurs = [j for j in joueurs if not j.tete_de_serie]
    for joueur in sorted(autres_joueurs, key=lambda x: x.niveau, reverse=True):
        print(f"  {joueur} - {joueur.age} ans")
    
    print(f"\nTotal : {len(joueurs)} joueurs ({len(tetes_de_serie)} têtes de série)")
    
    # Statistiques sur la distribution des niveaux
    niveaux_stats = {}
    for niveau in range(1, 6):
        count = sum(1 for j in joueurs if j.niveau == niveau)
        niveaux_stats[niveau] = count
    
    print("\n📊 RÉPARTITION PAR NIVEAU :")
    for niveau in sorted(niveaux_stats.keys(), reverse=True):
        count = niveaux_stats[niveau]
        pourcentage = (count / len(joueurs)) * 100
        print(f"  Niveau {niveau}: {count} joueurs ({pourcentage:.1f}%)")

def exemple_joueurs_fixe():
    # Création des joueurs
    joueurs = [
        Joueur("Martin", "Pierre", 5),
        Joueur("Martin", "Paul", 4),  # Même famille que Pierre
        Joueur("Dupont", "Marie", 5),
        Joueur("Dubois", "Jean", 4),
        Joueur("Leroy", "Sophie", 4),
        Joueur("Bernard", "Luc", 3),
        Joueur("Thomas", "Anne", 3),
        Joueur("Petit", "Marc", 3),
        Joueur("Robert", "Julie", 2),
        Joueur("Richard", "Alex", 2),
        Joueur("Moreau", "Emma", 2),
        Joueur("Simon", "Tom", 1),
        Joueur("Michel", "Lisa", 1),
        Joueur("Garcia", "Hugo", 1),
        Joueur("Roux", "Clara", 1),
        Joueur("Roux", "Max", 2),  # Même famille que Clara
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
