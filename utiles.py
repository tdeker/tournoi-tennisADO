# tout ce qui est utile mais pas liéd directement à la création du tournoi
# import à partir de csv
import hashlib
from pyairtable import Api

NOMS_POULES_LEGENDES_HOMMES = [
    # Légendes historiques
    "Noah",       # Yannick Noah - Roland Garros 1983
    "Lacoste",    # René Lacoste - Les 4 Mousquetaires, 7 GC
    "Cochet",     # Henri Cochet - Les 4 Mousquetaires, 8 GC
    "Borotra",    # Jean Borotra - Les 4 Mousquetaires, 4 GC
    "Brugnon",    # Jacques Brugnon - Les 4 Mousquetaires (spécialiste double)
    "Petra",      # Yvon Petra - dernier vainqueur français à Wimbledon (1946)

    # Génération 80-90
    "Leconte",    # Henri Leconte - finaliste Roland Garros 1988
    "Forget",     # Guy Forget - Masters 1991, Coupe Davis
    "Pioline",    # Cédric Pioline - finaliste Wimbledon 1997 et US Open 1993
    "Santoro",    # Fabrice Santoro - "Le Magicien"

    # Génération 2000
    "Tsonga",     # Jo-Wilfried Tsonga - finaliste AO 2008, top 5 mondial
    "Monfils",    # Gaël Monfils - top 6 mondial, 12 titres ATP
    "Gasquet",    # Richard Gasquet - finaliste Wimbledon 2007
    "Simon",      # Gilles Simon - top 6 mondial

    # Génération actuelle
    "Humbert",    # Ugo Humbert - top 20 mondial
    "Fils",       # Arthur Fils - top 20 mondial, grande promesse
    "Mpetshi",    # Giovanni Mpetshi Perricard - 1er service mondial
    "Mannarino",  # Adrian Mannarino - vétéran top 50
    "Moutet",     # Corentin Moutet - jeu créatif
    "Gaston",     # Hugo Gaston - 3e set légendaire vs Thiem RG 2020
]
NOMS_POULES_LEGENDES_FEMMES = [
    # Légendes historiques
    "Lenglen",    # Suzanne Lenglen - 6 Wimbledon, "La Divine"
    "Mathieu",    # Simone Mathieu - 2x Roland Garros (1938-1939)

    # Génération 70-80
    "Dürr",       # Françoise Dürr - Roland Garros 1967
    "Loville",    # Régine Loville
    "Renaville",  # Annick Renaville

    # Génération 90-2000
    "Tauziat",    # Nathalie Tauziat - finaliste Wimbledon 1998
    "Halard",     # Julie Halard-Decugis
    "Coetzer",    # Amanda Coetzer... ← attention : sud-africaine, à remplacer
    "Mauresmo",   # Amélie Mauresmo - Wimbledon 2006, AO 2006, n°1 mondiale
    "Pierce",     # Mary Pierce - RG 2000, AO 1995

    # Génération 2000-2010
    "Rezai",      # Aravane Rezai - Rome 2010
    "Bartoli",    # Marion Bartoli - Wimbledon 2013
    "Cornet",     # Alizé Cornet - 18 ans consécutifs en Grand Chelem

    # Génération actuelle
    "Garcia",     # Caroline Garcia - WTA Finals 2022, n°1 mondiale
    "Ferro",      # Fiona Ferro
    "Burel",      # Clara Burel
    "Parry",      # Diane Parry
    "Dodin",      # Océane Dodin
    "Mladenovic", # Kristina Mladenovic - spécialiste double
]

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

def resetTable(monApi:Api, baseID:str, table:str) :
    maTableAEffacer = monApi.table(baseID,table)
    records = maTableAEffacer.all()
    ids = [record["id"] for record in records]
    return True