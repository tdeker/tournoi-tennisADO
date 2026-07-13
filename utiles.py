# tout ce qui est utile mais pas liéd directement à la création du tournoi
# import à partir de csv
import hashlib
from pyairtable import Api

NOMS_POULES_LEGENDES_HOMMES = [
     # Superstars mondiales incontournables
    "Federer", "Nadal", "Djokovic", "Borg", "McEnroe", "Sampras", "Agassi",
    "Connors", "Lendl", "Becker", "Murray", "Wawrinka", "Alcaraz", "Sinner",
    # Stars françaises majeures (très connues en France)
    "Noah", "Tsonga", "Monfils", "Gasquet", "Leconte", "Forget", "Pioline",
    "Lacoste", "Simon", "Santoro",
    # Grands champions mondiaux très médiatisés
    "Edberg", "Wilander", "Courier", "Chang", "Ivanisevic", "Safin", "Hewitt",
    "Roddick", "DelPotro", "Medvedev", "Tsitsipas", "Zverev", "Thiem", "Rune",
    "Kyrgios", "Nishikori", "Dimitrov", "Berdych", "Cilic", "Ferrer",
    # Légendes historiques (très connues des amateurs)
    "Laver", "Ashe", "Nastase", "Vilas", "Kramer", "Gonzales", "Rosewall",
    "Emerson", "Newcombe", "Muster", "Kafelnikov", "Bruguera", "Moya", "Rios",
    # Génération actuelle (montante, suivie en France)
    "Humbert", "Fils", "Mpetshi", "Moutet", "Gaston", "Mannarino", "Fonseca",
    "Ruud", "Rublev", "Fritz", "Tiafoe", "Auger", "Shapovalov", "DeMinaur",
    "Musetti", "Draper", "Berrettini", "Hurkacz", "Khachanov", "Shelton",
    # Français connus des suiveurs
    "Grosjean", "Clement", "Paire", "Mahut", "Herbert", "Llodra", "Benneteau",
    "Chardy", "Mathieu", "Escude", "Cochet", "Borotra", "Brugnon", "Petra",
    # Champions mondiaux notables
    "Nalbandian", "Coria", "Gaudio", "Soderling", "Verdasco", "Almagro",
    "Robredo", "Ferrero", "Davydenko", "Ljubicic", "Gonzalez", "Baghdatis",
    "Krajicek", "Rafter", "Stich", "Corretja", "Costa", "Enqvist", "Philippoussis",
    # Anciens et spécialistes
    "Tilden", "Budge", "Trabert", "Segura", "Hoad", "Santana", "Roche",
    "Gerulaitis", "Tanner", "Orantes", "Ramirez", "Panatta", "Vilas2",
    "Smith", "Kodes", "Okker", "Gimeno", "Riessen", "Solomon", "Dibbs",
    # Top 50 / moins médiatisés
    "Bautista", "Schwartzman", "Goffin", "Pouille", "Coric", "Carreno",
    "Norrie", "Isner", "Raonic", "Querrey", "Sock", "Johnson", "Pospisil",
    "Dolgopolov", "Tomic", "Ramos", "Bublik", "Lehecka", "Cerundolo",
    # Joueurs récents / espoirs
    "Mensik", "Michelsen", "Nakashima", "Korda", "Paul", "Tien", "Diallo",
    "Etcheverry", "Baez", "Popyrin", "Kokkinakis", "Thompson", "Kecmanovic",
    "Lajovic", "Krajinovic", "Karatsev", "Kotov", "Safiullin", "Vukic",
    # Joueurs de complément
    "Munar", "Davidovich", "Carballes", "Garin", "Tabilo", "Jarry", "Borges",
    "Sousa", "Cuevas", "Klizan", "Kohlschreiber", "Struff", "Otte", "Mayer",
    "Hanfmann", "Altmaier", "Cressy", "Giron", "McDonald", "Opelka",
    "Eubanks", "Wolf", "Brooksby", "Basavareddy", "Tipsarevic", "Kudla",
    "Gilbert", "Mayotte", "Curren", "Krickstein", "Teltscher", "Clerc",
    "Higueras", "Arias", "Nystrom", "Jarryd", "Sundstrom", "Fibak",
    "Sedgman", "Patty", "Drobny", "Cooper", "Anderson", "Olmedo", "Fraser",
    "Stolle", "Kriek", "Mecir", "Gomez", "Kucera", "Medvedev2",
]
NOMS_POULES_LEGENDES_FEMMES = [
     # Superstars mondiales incontournables
    "WilliamsS", "WilliamsV", "Graf", "Navratilova", "Evert", "Sharapova",
    "Hingis", "Seles", "Henin", "Clijsters", "Mauresmo", "Swiatek", "Sabalenka",
    "Osaka", "Gauff",
    # Stars françaises (très connues en France)
    "Pierce", "Cornet", "Mladenovic", "Garcia", "Tauziat", "Bartoli",
    "Halard", "Testud", "Dechy", "Razzano",
    # Championnes mondiales très médiatisées
    "Capriati", "Davenport", "CourtMargaret", "King", "Goolagong", "Sabatini",
    "Sanchez", "Martinez", "Kuznetsova", "Ivanovic", "Jankovic", "Wozniacki",
    "Azarenka", "Halep", "Kvitova", "Muguruza", "Kerber", "Stosur",
    # Légendes historiques (connues des amateurs)
    "Lenglen", "Wills", "Connolly", "Gibson", "Bueno", "Wade", "Austin",
    "Mandlikova", "Novotna", "Schiavone", "Pennetta", "Pierce2", "Casals",
    # Génération actuelle (suivie en France)
    "Rybakina", "Jabeur", "Pegula", "Krejcikova", "Vondrousova", "Andreescu",
    "Raducanu", "Collins", "Ostapenko", "Kasatkina", "Bencic", "Mertens",
    "Andreeva", "Paolini", "Navarro", "Boulter", "Fernandez",
    # Championnes notables
    "Pliskova", "Svitolina", "Konta", "Keys", "Radwanska", "Bertens",
    "Kontaveit", "Vekic", "Sakkari", "Haddad", "Samsonova", "Alexandrova",
    "Anisimova", "Putintseva", "Cirstea", "Linette", "Kostyuk", "Vinci",
    # Françaises connues des suiveurs
    "Garcia2", "Parmentier", "Ferro", "Burel", "Dodin", "Paquet", "Kremer",
    "Loit", "Halard2", "Testud2",
    # Anciennes championnes
    "Zvereva", "Maleeva", "Garrison", "Sukova", "Smylie", "McNeil", "Paz",
    "Coetzer", "Spirlea", "Dragomir", "Wiesner", "Likhovtseva", "Petrova",
    "Zvonareva", "Dementieva", "Myskina", "Safina", "Sevastova", "Goerges",
    # Légendes plus anciennes
    "Marble", "Brough", "Hart", "Fry", "Hard", "Mortimer", "Truman",
    "Jones", "Richey", "Durr", "Turnbull", "Stove", "Barker", "Jausovec",
    "Ruzici", "Shriver", "Jordan", "Russell", "Lindqvist", "Bassett",
    # Joueuses récentes / espoirs
    "Shnaider", "Frech", "Bouzkova", "Yastremska", "Kalinskaya", "Bronzetti",
    "Cocciaretto", "Avanesyan", "Stearns", "Krueger", "Baptiste", "Townsend",
    "Noskova", "Muchova", "Siniakova", "Trevisan", "Giorgi", "Errani",
    # Joueuses de complément
    "Hantuchova", "Bouchard", "Wickmayer", "Flipkens", "VanUytvanck", "Minnen",
    "Kanepi", "Brengle", "Riske", "Mattek", "Rogers", "Dolehide", "Osorio",
    "Zidansek", "Juvan", "Schmiedlova", "Hradecka", "Bondar", "Sramkova",
    "Suarez", "Arruabarrena", "Sorribes", "Marino", "Abanda", "Davis",
    "Knapp", "Camerin", "Torro", "Galfi", "Udvardy", "Stollar", "Babos",
    "Jani", "Gorgodze", "Bartunkova", "Sherif", "Parks", "Tomljanovic",
    "Cibulkova", "Vandeweghe", "Schett", "Tauziat2", "Mauresmo2", "Errani2",
    "Pliskova2", "Sukova2", "Hana", "Kohde", "Potter", "Fernandez2",
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


