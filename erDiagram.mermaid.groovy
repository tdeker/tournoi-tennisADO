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
    string CodeJoueur PK
    string Nom
    string Prenom
    string Niveau
    date DateDeNaissance
    string Email
    string Sexe
    number Age
    boolean Seed
    string Zone
    string PouleJoueur
}
  Poule {
    string Nom PK
    number nb_gagnant
    number nb_joueurs
    string lieu
    number nb_match
    number Cout
  }
  Poule_Joueur {
    link Joueur FK
    link Poule FK
    string Classement_poule
    number nb_points
  }

  Tournoi {
    string Nom PK
    string Type "Principal ou Consolante"
    string Sexe
    number Taille_tableau
    link Tournoi_principal FK
  }


  Resultat {
    string Ref PK
    link Joueur FK
    link Tournoi FK
    string Origine "Seed, Poule, Consolante"
    number Position "1 a N, fixe"
    string T_1_64 "V ou P"
    string T_1_32 "V ou P"
    string T_1_16 "V ou P"
    string T_1_8 "V ou P"
    string T_1_4 "V ou P"
    string T_1_2 "V ou P"
    string Finale "V ou P"
  }
  Match {
    string Code PK
    link Tournoi FK
    string Tour "1/32 a Finale"
    number Numero
    link Joueur_1 FK
    link Joueur_2 FK
    link Vainqueur FK
    string Score
    datetime Date_heure
    string Terrain
    link Match_suivant FK
  }