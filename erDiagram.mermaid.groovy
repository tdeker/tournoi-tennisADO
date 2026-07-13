erDiagram
  Joueur ||--o{ Poule_Joueur : "participe"
  Poule ||--o{ Poule_Joueur : "contient"
  Joueur ||--o{ Resultat : "obtient"
  Tournoi ||--o{ Resultat : "comporte"
  Tournoi |o--o| Tournoi : "consolante alimente"
  Tournoi ||--o{ Match : "programme"
  Joueur |o--o{ Match : "dispute"
  Match |o--o| Match : "qualifie pour"

  Joueur {
    string CodeJoueur PK "Identifiant joueur"
    string Nom
    string Prenom
    string Niveau "Single select 1-5"
    date Date_de_naissance
    number Age "Formule calculee depuis Date_de_naissance"
    string Email
    string Sexe "Single select H, F"
    boolean Seed "Tete de serie du tableau principal"
    string Zone "Single select 1-5"
    link Participations FK "-> Poule_Joueur, lien inverse"
    link Resultats FK "-> Resultat, lien inverse"
    link Matchs_Joueur_1 FK "-> Match, lien inverse"
    link Matchs_Joueur_2 FK "-> Match, lien inverse"
    link Matchs_gagnes FK "-> Match, lien inverse de Vainqueur"
  }

  Poule_Joueur {
    number CodePouleJoueur PK "Autonumber"
    link CodeJoueur FK "-> Joueur"
    link Poule FK "-> Poule"
    number Points
    number Victoires
    number Defaites
    number Matchs_joues
    boolean Est_qualifie "Case a cocher"
    string Zone_joueur "Lookup CodeJoueur.Zone"
    string Niveau_joueur "Lookup CodeJoueur.Niveau"
    string Prenom_joueur "Lookup CodeJoueur.Prenom"
    string Nom_joueur "Lookup CodeJoueur.Nom"
    string Nom_poule "Lookup Poule.Nom"
  }

  Poule {
    string Nom PK
    number nb_gagnant "Nb de qualifies pour le principal"
    number nb_joueurs
    string lieu
    number nb_match
    number Cout
    link Participants FK "-> Poule_Joueur, lien inverse"
  }

  Tournoi {
    string Nom PK
    string Type "Principal ou Consolante"
    string Sexe "Homme, Femme, Mixte"
    number Taille_tableau "Puissance de 2, 64 max"
    link Tournoi_principal FK "-> Tournoi, rempli si Type=Consolante"
    link Resultats FK "-> Resultat, lien inverse"
    link Matchs FK "-> Match, lien inverse"
  }

  Resultat {
    string Ref PK "NomTournoi-Position"
    link Joueur FK "-> Joueur, vide = bye"
    link Tournoi FK "-> Tournoi"
    string Origine "Seed, Poule, Consolante"
    number Position "1 a Taille_tableau, fixe"
    string T_1_32 "V ou P"
    string T_1_16 "V ou P"
    string T_1_8 "V ou P"
    string T_1_4 "V ou P"
    string T_1_2 "V ou P"
    string Finale "V ou P"
  }

  Match {
    string Code PK
    link Tournoi FK "-> Tournoi"
    string Tour "1/32 a Finale"
    number Numero "Numero du match dans le tour"
    link Joueur_1 FK "-> Joueur"
    link Joueur_2 FK "-> Joueur"
    link Vainqueur FK "-> Joueur"
    string Score
    datetime Date_heure
    string Terrain
    link Match_suivant FK "-> Match"
    link Matchs_precedents FK "-> Match, lien inverse de Match_suivant"
  }