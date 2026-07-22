## tournoi-tennisADO
Pour la configuration des poules, prévoir des poul de 4 ou 5 si possibles
refaire l'algo de poul epouravoir uniquement des poules de 4 et 5 joueurs -- impossible pour 11

def decomp_max_a(n):
    """
    Retourne (a, b) maximisant a tel que n = 4a + 5b, a,b entiers >= 0.
    Renvoie None s'il n'y a pas de solution.
    """
    b = n % 4              # plus petit b compatible (b ≡ n mod 4)
    a_num = n - 5 * b
    if a_num < 0:
        return None        # pas de solution (ex: n = 11)
    a = a_num // 4
    if 4 * a + 5 * b == n:
        return a, b
    return None

## Exemples
for n in range(10, 100):
    print(n, "->", decomp_max_a(n))

## 25/01
l'algo de création de Poule qui maximise les poules de 4 est correcte, après est ce que cela est vraiment opprotun de faire des poules de 4 mettre peut un paramètre pour maximiser les nombrede poules de 5
## 8/05
changement de l'algorithme d'allocation des joueurs dans les poules avec les nouvelles demandes de l'équipe Tennis
A faire: gérer les tête de série lors du chargement des données dans l'objet Joueurs et supprimer les tetes de série de l'allocation des poules
problème sur la création des poules: le nombre de gagnant est mal répartie et les poules ne sont pas nomées
## 13/07 
Penser à déployer les variables d'environnement sur railway (nb de repéchés)
