from collections import defaultdict, Counter
import random
import hashlib
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
    id:            str  # = field(init=False)  
    tete_de_serie: bool = False
    lieu_vacances: str  = ""            # utilisé pour élargir la détection de famille
    nom_famille:   str  = field(init=False)  # calculé automatiquement
    def __post_init__(self):
        # Champs calculés (pas passés en paramètre)
        self.nom_famille = self.nom
        #self.id        = generate_player_id(self.prenom, self.nom) # pour le moment je ne génère pas de code joueur

        # Validations
        assert 1 <= self.niveau <= 5,  f"Niveau invalide : {self.niveau}"
        assert 1 <= self.zone   <= 5,  f"Zone invalide : {self.zone}"
        assert self.age > 0,           f"Âge invalide : {self.age}"

    def __repr__(self):
        return f"{self.prenom} {self.nom} (N{self.niveau} Z{self.zone}, {self.age} ans)"


def sont_de_la_meme_famille(a: "Joueur", b: "Joueur") -> bool:
    """
    Deux joueurs sont considérés de la même famille s'ils partagent le
    même nom de famille OU le même lieu de vacances (les deux
    critères sont des indices indépendants, l'un ou l'autre suffit -
    ce n'est pas un ET). Comparaison normalisée (espaces superflus
    retirés, insensible à la casse) pour tolérer les écarts de
    saisie ; ne détecte pas les fautes de frappe ("St Tropez" vs
    "Saint-Tropez" restent différents) - à uniformiser en amont si
    besoin, idéalement via une liste de lieux prédéfinie plutôt que
    du texte libre.
    """
    nom_a = (a.nom_famille or "").strip().lower()
    nom_b = (b.nom_famille or "").strip().lower()
    lieu_a = (a.lieu_vacances or "").strip().lower()
    lieu_b = (b.lieu_vacances or "").strip().lower()

    meme_nom = bool(nom_a) and nom_a == nom_b
    meme_lieu = bool(lieu_a) and lieu_a == lieu_b
    return meme_nom or meme_lieu


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

    # Pool de lieux de vacances pour le jeu de données de test : une
    # partie des joueurs en déclare un (au hasard, y compris entre
    # joueurs SANS lien de parenté, exprès - c'est justement le cas
    # que la règle élargie "même famille = même nom OU même lieu de
    # vacances" doit détecter), les autres n'en déclarent aucun
    # (champ optionnel, laissé vide).
    LIEUX_VACANCES = ["Biarritz", "Deauville", "Cassis", "La Baule", "Saint-Tropez", "Arcachon"]

    def _tirer_lieu_vacances() -> str:
        return random.choice(LIEUX_VACANCES) if random.random() < 0.4 else ""

    # Suivi des id déjà attribués, pour garantir l'unicité (bug pré-existant :
    # l'ancien code ne générait jamais d'id réel, le 7e argument positionnel
    # de Joueur() était censé être tete_de_serie mais atterrissait dans id).
    ids_utilises: set = set()

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
        
        id_joueur = generate_player_id(prenom, nom_famille, ids_utilises)
        ids_utilises.add(id_joueur)
        joueur = Joueur(prenom, nom_famille, sexe, age, niveau, zone, id_joueur, tete_de_serie=is_seeded, lieu_vacances=_tirer_lieu_vacances())
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
        id_joueur = generate_player_id(prenom, nom, ids_utilises)
        ids_utilises.add(id_joueur)
        joueur = Joueur(prenom, nom, sexe, age, niveau, zone, id_joueur, tete_de_serie=True, lieu_vacances=_tirer_lieu_vacances())
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
        id_joueur = generate_player_id(prenom, nom, ids_utilises)
        ids_utilises.add(id_joueur)
        joueur = Joueur(prenom, nom, sexe, age, niveau, zone, id_joueur, tete_de_serie=False, lieu_vacances=_tirer_lieu_vacances())
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
        "CodeJoueur"  : str(monJoueur.id),
        "Lieu_vacances": str(monJoueur.lieu_vacances),
    }
     for monJoueur in maListeDeJoueurs
    ])