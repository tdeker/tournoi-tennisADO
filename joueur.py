from collections import defaultdict, Counter
import random
from dataclasses import dataclass, field
from typing import Literal
from faker import Faker
from typing import List, Dict, Tuple, Optional, Literal
from utiles import *
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Joueur:
    prenom:        str
    nom:           str
    sexe:          Literal["M", "F"]
    age:           int
    niveau:        int                  # 1 à 5  (5 = meilleur)
    zone:          int                  # 1 à 5
    tete_de_serie: bool = False
    nom_famille:   str  = field(init=False)  # calculé automatiquement
    id:          str  = field(init=False)  # calculé automatiqu
    def __post_init__(self):
        # Champs calculés (pas passés en paramètre)
        self.nom_famille = self.nom
        self.id        = generate_player_id(self.prenom, self.nom)

        # Validations
        assert 1 <= self.niveau <= 5,  f"Niveau invalide : {self.niveau}"
        assert 1 <= self.zone   <= 4,  f"Zone invalide : {self.zone}"
        assert self.age > 0,           f"Âge invalide : {self.age}"

    def __repr__(self):
        return f"{self.prenom} {self.nom} (N{self.niveau} Z{self.zone}, {self.age} ans)"


def generate_player_id(first_name: str, last_name: str, existing_ids: set = None) -> str:
    """
    Génère un code joueur basé sur le hash MD5 du nom et prénom.
    Format : J-XXXX (4 caractères hex en majuscules)
    Gère les collisions (homonymes) avec un suffixe numérique.
    """
    if existing_ids is None:
        existing_ids = set()

    # Hash MD5 du nom+prénom en minuscules (insensible à la casse)
    raw = f"{first_name.lower()}{last_name.lower()}"
    hash_hex = hashlib.md5(raw.encode()).hexdigest()
    base_code = f"J-{hash_hex[:4].upper()}"

    # Gestion des collisions
    code = base_code
    suffix = 1
    while code in existing_ids:
        code = f"{base_code}-{suffix}"
        suffix += 1

    return code
def creation_joueurs_avec_nom_famille(nb_inscris: int, nb_seededPlayer: int) -> List[Joueur]:
    """
    Génère automatiquement une liste de joueurs avec possibilité d'avoir des familles.
    
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
    niveaux_poids = [30, 30, 20, 15, 5]  # Poids pour niveaux 1, 2, 3, 4, 5
    niveaux_choix = [1, 2, 3, 4, 5]
    
    # Déterminer le nombre de familles (environ 10-20% des joueurs peuvent être en famille)
    nb_familles = random.randint(1, max(1, nb_inscris // 7))
    
    # Générer les noms de famille pour les familles
    noms_familles = []
    for _ in range(nb_familles):

        nom_famille = fake.last_name()
        # Chaque famille aura 2-3 membres
        nb_membres = random.choice([2, 2, 3])  # Plus de chance d'avoir 2 membres
        noms_familles.extend([nom_famille] * nb_membres)
    
    # S'assurer qu'on ne dépasse pas le nombre total de joueurs
    noms_familles = noms_familles[:min(len(noms_familles), nb_inscris)]
    nb_joueurs_famille = len(noms_familles)
    nb_joueurs_uniques = nb_inscris - nb_joueurs_famille
    
    # Créer les joueurs de familles
    for i, nom_famille in enumerate(noms_familles):
        sexe = fake.random_element(["M", "F"])
        age = random.randint(7, 17)
        zone = random.randint(1, 4)
        if sexe == "M":
            prenom = fake.first_name_male()   # ← prénom masculin garanti
        else:
            prenom = fake.first_name_female() # ← prénom féminin garant
        
       

        # Déterminer si c'est une tête de série
        is_seeded = i < nb_seededPlayer
        
        if is_seeded:
            # Les têtes de série ont plus de chances d'avoir des niveaux élevés (3, 4, 5)
            niveau = random.choices([3, 4, 5], weights=[30, 40, 30])[0]
        else:
            # Distribution pondérée favorisant les bas niveaux (1, 2, 3)
            niveau = random.choices(niveaux_choix, weights=niveaux_poids)[0]
        
        joueur = Joueur(prenom, nom_famille,sexe, age, niveau,zone, is_seeded)
        joueurs.append(joueur)
    
    # Créer les joueurs restants (noms uniques)
    nb_seeded_restants = max(0, nb_seededPlayer - nb_joueurs_famille)
    
    # Créer les têtes de série restantes
    for i in range(nb_seeded_restants):
        sexe = fake.random_element(["M", "F"])
        nom=fake.last_name()
        if sexe == "M":
            prenom = fake.first_name_male()   # ← prénom masculin garanti
        else:
            prenom = fake.first_name_female() # ← prénom féminin garanti
        age = random.randint(7, 17)
        niveau = random.choices([3, 4, 5], weights=[30, 40, 30])[0]
        zone = random.randint(1, 4)
        joueur = Joueur(prenom,nom,sexe, age, niveau,zone, True)
        joueurs.append(joueur)
    
    # Créer les joueurs non têtes de série restants
    nb_non_seeded_restants = nb_joueurs_uniques - nb_seeded_restants
    for i in range(nb_non_seeded_restants):
        sexe = fake.random_element(["M", "F"])
        zone = random.randint(1, 4)
        nom=fake.last_name()
        if sexe == "M":
            prenom = fake.first_name_male()   # ← prénom masculin garanti
        else:
            prenom = fake.first_name_female() # ← prénom féminin garanti
        age = random.randint(7, 17)
        niveau = random.choices(niveaux_choix, weights=niveaux_poids)[0]
        joueur = Joueur(prenom,nom,sexe, age, niveau,zone, False)
        joueurs.append(joueur)
    
    # Mélanger la liste pour avoir un ordre aléatoire
    random.shuffle(joueurs)
    
    return joueurs
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
def creer_nouvelle_liste_joueur_dans_airtable(nbInscris, nbSeed,AIRTABLE_TOKEN,BASE_ID) :
    monApiAT = Api(AIRTABLE_TOKEN)   
    tableJoueur = monApiAT.table(BASE_ID, "Joueur")
    maListeDeJoueurs = creation_joueurs_avec_nom_famille(nbInscris,nbSeed) 
    frecords_existants = tableJoueur.all()
    ids_a_supprimer = [record["id"] for record in frecords_existants]
    if ids_a_supprimer:
     tableJoueur.batch_delete(ids_a_supprimer)

    # 2. Création des nouveaux joueurs
    tableJoueur.batch_create([
      {
        "Nom"         : str(monJoueur.nom),
        "Prénom"      : str(monJoueur.prenom),
        "Sexe"        : str(monJoueur.sexe),
        "Niveau"      : str(monJoueur.niveau),
        "Age"         : int(monJoueur.age),
        "Seed"        : bool(monJoueur.tete_de_serie),
        "Zone"        : str(monJoueur.zone),
        "CodeJoueur"  : str(monJoueur.id)
    }
     for monJoueur in maListeDeJoueurs
    ])


