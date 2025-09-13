from collections import defaultdict, Counter
import random
from faker import Faker
from typing import List, Dict, Tuple, Optional


class Joueur:
    def __init__(self, name: str, age: int,niveau: int, seededPlayer: bool):
        self.prenom = name.split()[0] if len(name.split()) > 0 else ""
        self.nom = name.split()[-1] if len(name.split()) > 1 else name # attention il va y avoir des problèmes sur les noms de famille composés
        self.tete_de_serie = seededPlayer
        self.age = age
        self.niveau = niveau

    def __repr__(self):
        return f"{self.prenom} {self.nom} (N{self.niveau})"


# A supprimer
class Old_Joueur: 
    def __init__(self, nom: str, prenom: str, niveau: int):
        self.nom = nom
        self.prenom = prenom
        self.niveau = niveau
        self.nom_famille = nom.split()[0] if ' ' in nom else nom
    
    def __repr__(self):
        return f"{self.prenom} {self.nom} (N{self.niveau})"


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


