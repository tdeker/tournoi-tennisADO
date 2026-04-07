# tournoi-tennisADO
# POur la configuration des poules, prévoir des poul de 4 ou 5 si possibles
# refaire l'algo de poul epouravoir uniquement des poules de 4 et 5 joueurs -- impossible pour 11

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

# Exemples
for n in range(10, 100):
    print(n, "->", decomp_max_a(n))