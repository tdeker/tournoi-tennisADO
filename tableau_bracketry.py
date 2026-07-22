"""
Construction du payload bracketry (tableau principal / consolantes)
=====================================================================

Isole depuis app.py pour que ce dernier reste un fichier de ROUTES
Flask fines : toute la logique de lecture Airtable et de
transformation vers le format bracketry (sbachinin/bracketry) vit ici,
comme tournoi.py et score_provisionning.py sont deja des librairies
separees de app.py.

Ce fichier ne lit aucune variable d'environnement et ne garde aucun
etat entre deux appels : il prend api_key/base_id en parametre de
chaque fonction, exactement comme GestionnaireResultat (tournoi.py).

REGLES (rappel du cahier des charges) :
  - Utilise UNIQUEMENT les tables Tournoi et Resultat.
  - Tournoi.Taille_tableau determine le tour de depart :
      64 -> 1/32, 32 -> 1/16, 16 -> 1/8, 8 -> 1/4, 4 -> 1/2, 2 -> Finale.
  - On affiche l'AVANCEMENT REEL de Resultat, rien n'est simule :
      * 1er tour : match k = position (2k-1) vs position (2k).
      * une case sans joueur = BYE -> qualification automatique
        (UNIQUEMENT au 1er tour : voir le commentaire dans
        construire_payload_tableau, c'etait la source d'un bug ou les
        tours suivants se remplissaient en cascade jusqu'a la finale).
      * un tour est "termine" seulement quand chaque position encore
        en lice a "V" ou "P" ecrit dans la colonne de ce tour.
      * tant qu'un match n'a pas de "V" ecrit, l'emplacement du tour
        suivant reste VIDE (case blanche), aucun vainqueur invente.
  - Pas de scores dans l'affichage (evolution future).
  - Seuls les tournois presents dans Resultat sont proposes.

Format de sortie : celui attendu par bracketry (sbachinin/bracketry) :
    { "rounds": [{"name": str}, ...],
      "matches": [{"roundIndex": int, "order": int, "sides": [Side, ...]}, ...] }
    Side = {"title": str, "isWinner": bool} ; une side ABSENTE du
    tableau "sides" (objet vide {}) = BYE ou case pas encore
    determinee, rendue vide par bracketry.

Exemple d'utilisation depuis app.py :

    from tableau_bracketry import construire_payload_tableau, tournois_avec_resultats

    data = construire_payload_tableau(AIRTABLE_TOKEN, BASE_ID, "Consolante Hommes")
    tournois = tournois_avec_resultats(AIRTABLE_TOKEN, BASE_ID)
"""

from pyairtable import Api

_COLONNES_TOUR = ["T_1_32", "T_1_16", "T_1_8", "T_1_4", "T_1_2", "Finale"]
_PREMIER_TOUR_POUR_TAILLE = {
    64: "T_1_32", 32: "T_1_16", 16: "T_1_8", 8: "T_1_4", 4: "T_1_2", 2: "Finale",
}
# Nom de round affiche, dans le vocabulaire tennis (coherent avec les
# colonnes Resultat elles-memes).
_NOM_TOUR = {
    "T_1_32": "1/32", "T_1_16": "1/16", "T_1_8": "1/8",
    "T_1_4": "1/4", "T_1_2": "1/2", "Finale": "Finale",
}


def _tables_tableau(api_key, base_id):
    api = Api(api_key)
    return (
        api.table(base_id, "Tournoi"),
        api.table(base_id, "Resultat"),
        api.table(base_id, "Joueur"),
    )


def _colonnes_actives(taille_tableau):
    """Colonnes de tour reellement utilisees, du 1er tour a la finale."""
    premier = _PREMIER_TOUR_POUR_TAILLE.get(taille_tableau)
    if premier is None:
        raise ValueError(
            f"Taille_tableau={taille_tableau} non standard "
            f"(puissance de 2 entre 2 et 64 attendue)."
        )
    return _COLONNES_TOUR[_COLONNES_TOUR.index(premier):]


def construire_payload_tableau(api_key, base_id, nom_tournoi):
    """
    Construit le payload bracketry refletant l'ETAT ACTUEL de la table
    Resultat pour un tournoi (principal ou consolante). Lecture seule,
    aucune deduction : un tour non rempli reste vide, une position sans
    joueur au 1er tour est un BYE qualifie d'office.
    """
    table_tournoi, table_resultat, table_joueur = _tables_tableau(api_key, base_id)

    tournois = table_tournoi.all(formula=f"{{Nom}} = '{nom_tournoi}'")
    if not tournois:
        raise ValueError(f"Tournoi '{nom_tournoi}' introuvable.")
    taille = tournois[0]["fields"].get("Taille_tableau")
    if not taille:
        raise ValueError(f"Le tournoi '{nom_tournoi}' n'a pas de Taille_tableau.")

    refs = table_resultat.all(formula=f"{{Tournoi}} = '{nom_tournoi}'")
    if not refs:
        raise ValueError(f"Aucun Resultat pour '{nom_tournoi}' : tableau non initialise.")

    # Une ligne Resultat par position de depart -> index par Position.
    par_position = {}
    for r in refs:
        pos = r["fields"].get("Position")
        if pos is not None:
            par_position[pos] = r["fields"]

    # Resolution des noms de joueurs lies (Resultat.Joueur = lien).
    ids_joueurs = set()
    for f in par_position.values():
        for jid in (f.get("Joueur") or []):
            ids_joueurs.add(jid)

    noms_par_id = {}
    if ids_joueurs:
        for j in table_joueur.all():
            if j["id"] in ids_joueurs:
                f = j["fields"]
                prenom = f.get("Prénom", "")
                noms_par_id[j["id"]] = f"{prenom} {f.get('Nom', '')}".strip()

    def nom_joueur(pos):
        liens = par_position.get(pos, {}).get("Joueur") or []
        if not liens:
            return None  # BYE : aucun joueur a cette position
        return noms_par_id.get(liens[0], par_position[pos].get("Ref", f"Pos {pos}"))

    def resultat_tour(pos, colonne):
        """'V', 'P' ou None, lu DIRECTEMENT dans Resultat (aucune deduction)."""
        return par_position.get(pos, {}).get(colonne)

    colonnes = _colonnes_actives(taille)

    # positions_vivantes[i] = position (int) occupant la ieme place du
    # tour courant, ou None si ce n'est pas encore determine (le match
    # precedent n'a pas de "V" ecrit). Au 1er tour : 1..taille.
    positions_vivantes = list(range(1, taille + 1))

    rounds = [{"name": _NOM_TOUR[c]} for c in colonnes]
    matches = []

    for round_index, colonne in enumerate(colonnes):
        positions_suivantes = []
        for ordre, i in enumerate(range(0, len(positions_vivantes), 2)):
            pos_a = positions_vivantes[i]
            pos_b = positions_vivantes[i + 1]

            nom_a = nom_joueur(pos_a) if pos_a is not None else None
            nom_b = nom_joueur(pos_b) if pos_b is not None else None

            res_a = resultat_tour(pos_a, colonne) if pos_a is not None else None
            res_b = resultat_tour(pos_b, colonne) if pos_b is not None else None

            # BYE : une seule des deux places a un joueur -> qualification
            # d'office. Un VRAI bye n'existe QU'AU 1er TOUR (round_index
            # == 0) : c'est une propriete structurelle du placement
            # (TableauBracket), ecrite en "V" par tournoi.py des la
            # creation de Resultat. A partir du 2e tour, une position
            # sans joueur determine (nom_x is None) signifie seulement
            # que le match precedent de cette branche n'a PAS ENCORE ete
            # joue - ce n'est pas un bye, et ne doit surtout pas
            # declencher une victoire automatique (sinon un joueur passe
            # par bye au 1er tour se retrouve "vainqueur fantome" de
            # tous les tours suivants, en cascade jusqu'a la finale).
            bye = round_index == 0 and (nom_a is None) != (nom_b is None)
            if bye:
                if nom_a is not None:
                    res_a = "V"
                else:
                    res_b = "V"

            # sides[0] = position haute (pos_a), sides[1] = position basse
            # (pos_b), toujours dans cet ordre. Un objet vide {} pour la
            # place BYE (ou pas encore determinee) est traite par
            # bracketry comme une case vide (is_non_empty_object ->
            # false), donc le rendu haut/bas respecte la position reelle
            # dans le tableau.
            side_a = {"title": nom_a, "isWinner": res_a == "V"} if nom_a is not None else {}
            side_b = {"title": nom_b, "isWinner": res_b == "V"} if nom_b is not None else {}
            sides = [side_a, side_b]

            matches.append({
                "roundIndex": round_index,
                "order": ordre,
                "sides": sides,
            })

            if res_a == "V":
                positions_suivantes.append(pos_a)
            elif res_b == "V":
                positions_suivantes.append(pos_b)
            else:
                positions_suivantes.append(None)  # pas encore determine

        positions_vivantes = positions_suivantes

    return {"rounds": rounds, "matches": matches}


def tournois_avec_resultats(api_key, base_id):
    """Tournois ayant AU MOINS une ligne dans Resultat (tableau initialise)."""
    table_tournoi, table_resultat, _ = _tables_tableau(api_key, base_id)

    refs_liees = set()
    for r in table_resultat.all(fields=["Tournoi"]):
        val = r["fields"].get("Tournoi")
        if not val:
            continue
        for v in (val if isinstance(val, list) else [val]):
            refs_liees.add(v)

    tournois = []
    for t in table_tournoi.all():
        f = t["fields"]
        if t["id"] in refs_liees or f.get("Nom") in refs_liees:
            tournois.append({
                "nom": f.get("Nom"),
                "type": f.get("Type"),
                "sexe": f.get("Sexe"),
                "taille": f.get("Taille_tableau"),
            })
    return tournois