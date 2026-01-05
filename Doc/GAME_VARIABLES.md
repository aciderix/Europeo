# Variables du Jeu Europeo

Liste exhaustive de toutes les variables utilisées dans le jeu, extraites des fichiers VND.

---

## 1. Variables Système

### Navigation
| Variable | Type | Description |
|----------|------|-------------|
| `CPAYS` | int | Index du pays courant |
| `CMENU1` | int | État menu 1 |
| `CMENU2` | int | État menu 2 |
| `CMENU3` | int | État menu 3 |
| `LOC` | int | Localisation courante |
| `NON` | int | Variable temporaire de comptage |

### Progression
| Variable | Type | Valeurs | Description |
|----------|------|---------|-------------|
| `SCORE` | int | -∞ à +∞ | Score du joueur (peut être négatif!) |
| `FIOLE` | int | 0-12 | Niveau de remplissage de la fiole |
| `JEU` | int | 0-1 | Mode jeu actif |

---

## 2. Pays

Chaque pays a une variable indiquant s'il a été visité.

| Variable | Dossier | Description |
|----------|---------|-------------|
| `FRANCE` | france | France |
| `ALLEMAGNE` | allem | Allemagne |
| `ANGLETERRE` | angl | Angleterre |
| `AUTRICHE` | autr | Autriche |
| `BELGIQUE` | belge | Belgique |
| `DANEMARK` | danem | Danemark |
| `ECOSSE` | ecosse | Écosse |
| `ESPAGNE` | espa | Espagne |
| `FINLANDE` | finlan | Finlande |
| `GRECE` | grece | Grèce |
| `PAYSBAS` | holl | Pays-Bas (Hollande) |
| `IRLANDE` | irland | Irlande |
| `ITALIE` | italie | Italie |
| `PORTUGAL` | portu | Portugal |
| `SUEDE` | suede | Suède |
| `EUROLAND` | couleurs1 | Hub central |

**Valeurs :** `0` = non visité, `1` = visité/actif

---

## 3. Outils (Toolbar)

| Variable | Description | États |
|----------|-------------|-------|
| `CALC` | Calculatrice Euro | 0=inactive, 1=active |
| `TELEPHONE` | Téléphone (aide) | 0=inactive, 1=active |
| `SACADOS` | Inventaire (sac à dos) | 0=inactive, 1=active |
| `TRANS` | Transport (carte) | 0=inactive, 1=active |
| `ACTIVE` | État actif général | 0=inactive, 1=active |
| `FRANCS` | Mode francs/euros | 0=euros, 1=francs |

---

## 4. Objets Collectables (Inventaire)

Tous les objets suivent le même système :
- `0` = Non découvert
- `1` = Découvert/visible
- `2` = Dans l'inventaire (possédé)

### Objets généraux
| Variable | Description |
|----------|-------------|
| `TICKET` | Ticket d'entrée |
| `TICKET_A` | Ticket variante A |
| `PHOTO` | Photographie |
| `AP_PHOTO` | Appareil photo |
| `CHAMPAGNE` | Bouteille de champagne |
| `CHAMPAGNE2` | Deuxième champagne |
| `PARFUM` | Flacon de parfum |
| `PAIN` | Pain |
| `HELICE` | Hélice |
| `HARPON` | Harpon |
| `MASQUE` | Masque de plongée |
| `BALLON1` | Ballon |
| `BOUEE` | Bouée |
| `PALME` | Palmes |
| `BOUT_PLO` | Bouteille de plongée |
| `BOUT_EAU` | Bouteille d'eau |
| `RESSORT` | Ressort |

### Instruments de musique
| Variable | Description |
|----------|-------------|
| `GUITARE` | Guitare |
| `VIOLON` | Violon |
| `PARTITION` | Partition |
| `ORGUE` | Orgue |
| `CORNEMUSE` | Cornemuse |
| `CASTAGNETTE` | Castagnettes |
| `MUSIC` | Variable musique |

### Alimentation
| Variable | Description |
|----------|-------------|
| `PIZZA` | Pizza |
| `FROMAGE` | Fromage |
| `CHIANTI` | Bouteille de Chianti |
| `BOUTEILLE` | Bouteille générique |
| `OEUF` | Œuf |
| `DORADE` | Dorade |
| `MOULE` | Moule |
| `AIL` | Ail |
| `POIVROUGE` | Poivron rouge |
| `POIVJAUNE` | Poivron jaune |
| `OIGNON` | Oignon |
| `OLIVE` | Olive |
| `BOUILLON` | Bouillon |
| `FARINE` | Farine |
| `SALIERE` | Salière |
| `LEVURE` | Levure |
| `HUILE` | Huile |
| `ORGE` | Orge |
| `HOUBLON` | Houblon |
| `SIROP` | Sirop |
| `PATE` | Pâtes |

### Vêtements et accessoires
| Variable | Description |
|----------|-------------|
| `COSTUME` | Costume |
| `BONNET` | Bonnet |
| `RUBAN` | Ruban |
| `LAINE` | Laine |
| `BOTTE` | Bottes |

### Outils et objets divers
| Variable | Description |
|----------|-------------|
| `LOUPE` | Loupe |
| `CISEAUX` | Ciseaux |
| `SCOTCH` | Scotch |
| `TOURNEVIS` | Tournevis |
| `PINCE` | Pince |
| `BURETTE` | Burette |
| `ALLUMETTE` | Allumettes |
| `TONDEUSE` | Tondeuse |
| `MASSE` | Masse |

### Clés
| Variable | Description |
|----------|-------------|
| `CLE` | Clé générique |
| `CLEJAUNE` | Clé jaune |
| `CLEROUGE` | Clé rouge |
| `CLEVERTE` | Clé verte |
| `DEJACLEJAUNE` | Déjà eu clé jaune |

### Objets spécifiques par pays
| Variable | Pays | Description |
|----------|------|-------------|
| `PIER_BERLIN` | Allemagne | Pierre du mur de Berlin |
| `ROUEDENT` | Allemagne | Roue dentée |
| `BUS` | Angleterre | Bus londonien |
| `SABOT1` | Pays-Bas | Sabot 1 |
| `SABOT2` | Pays-Bas | Sabot 2 |
| `TULIPEJAUNE` | Pays-Bas | Tulipe jaune |
| `CHEVAL` | Irlande | Cheval |
| `MARMOTTE` | Suisse/Autriche | Marmotte |
| `NESSIE` | Écosse | Monstre du Loch Ness |
| `PALETTE` | France | Palette de peintre |

---

## 5. Fioles par Pays

Variables indiquant la collecte des fioles spécifiques à chaque pays.

| Variable | Pays |
|----------|------|
| `FIOLE` | Compteur général (0-12) |
| `FIOLEOK` | Fiole validée |
| `FIOLEGRECE` | Fiole Grèce |
| `FIOLEGRECE2` | Fiole Grèce 2 |
| `FIOLEECOSSE` | Fiole Écosse |
| `FIOLEIRLANDE` | Fiole Irlande |
| `FIOLEESPAGNE` | Fiole Espagne |
| `FIOLEESPAGNE2` | Fiole Espagne 2 |
| `FIOLESUEDE` | Fiole Suède |
| `FIOLEFINLANDE` | Fiole Finlande |
| `FIOLEAUTRICHE` | Fiole Autriche |
| `FIOLEAUTR` | Fiole Autriche (alias) |
| `FIOLEPAYSBAS` | Fiole Pays-Bas |
| `FIOLEITALIE` | Fiole Italie |
| `FIOLEANGLETERRE` | Fiole Angleterre |
| `FIOLEVASE` | Fiole dans vase |

---

## 6. Bonus

| Variable | Description |
|----------|-------------|
| `BONUS1` | Bonus 1 |
| `BONUS2` | Bonus 2 |
| `BONUS3` | Bonus 3 |
| `BONUS4` | Bonus 4 |
| `BONUS5` | Bonus 5 |
| `BONUS6` | Bonus 6 |
| `BONUS7` | Bonus 7 |
| `BONUS8` | Bonus 8 |
| `BONUS9` | Bonus 9 |
| `BONUS14` | Bonus 14 |
| `BONUS15` | Bonus 15 |
| `BONUS16` | Bonus 16 |
| `BONUS18` | Bonus 18 |
| `BONUS19` | Bonus 19 |
| `BONUS20` | Bonus 20 |
| `BONUS22` | Bonus 22 |
| `BONUS23` | Bonus 23 |
| `BONUS24` | Bonus 24 |
| `BONUS25` | Bonus 25 |
| `BONUS26` | Bonus 26 |
| `BONUS29` | Bonus 29 |
| `BONUS30` | Bonus 30 |

---

## 7. Mini-jeux

### Juste Prix
| Variable | Description |
|----------|-------------|
| `JUSTEPRIX` | État du jeu |
| `JUSTEPRIXOBJ` | Objet à deviner |
| `JUSTEPRIXEURO` | Prix en euros |
| `JUSTEPRIXCLIC` | Nombre de clics |
| `JUSTEPRIX1` | Bouton 1€ |
| `JUSTEPRIX10` | Bouton 10€ |
| `JUSTEPRIX15` | Bouton 15€ |
| `JUSTEPRIX20` | Bouton 20€ |
| `JUSTEPRIX25` | Bouton 25€ |
| `JUSTEPRIX30` | Bouton 30€ |
| `JUSTEPRIX50` | Bouton 50€ |
| `JUSTEPRIX100` | Bouton 100€ |
| `JUSTEPRIXSCORE` | Score du jeu |
| `JUSTEPRIXQUESTION` | Question en cours |
| `JUSTEPRIXREPONSE` | Réponse donnée |
| `JUSTEPRIXOK` | Jeu terminé OK |

### Course de lévriers
| Variable | Description |
|----------|-------------|
| `LEVRIERNUMERO` | Numéro du lévrier parié |
| `LEVRIERPARI` | Montant du pari |
| `LEVRIERRESULTAT` | Résultat de la course |

### Boulangerie (Pain)
| Variable | Description |
|----------|-------------|
| `PAINOK` | Pain réussi |
| `EAUPAIN` | Eau pour pain |

### Bière
| Variable | Description |
|----------|-------------|
| `BIEREOK` | Bière réussie |
| `BIERESO` | Bière sortie |
| `EAUBIERE` | Eau pour bière |

### Peintre
| Variable | Description |
|----------|-------------|
| `PEINTRE` | État peintre |
| `PEINTRE1` | Peintre variante |
| `SCOREPEINTRE` | Score du mini-jeu |

### Questions/Réponses
| Variable | Description |
|----------|-------------|
| `QUESTION` | Question en cours |
| `REPONSE` | Réponse donnée |
| `GRECQUESTION` | Question Grèce |
| `GRECREPONSE` | Réponse Grèce |
| `NOTE` | Note obtenue |
| `MAUVAISENOTE` | Mauvaise note |

### Sous-marin
| Variable | Description |
|----------|-------------|
| `SOUSMARINOK` | Sous-marin terminé |
| `SOUSMARINOK2` | Sous-marin 2 terminé |

### 7 Erreurs
| Variable | Description |
|----------|-------------|
| `ERREUR7OK` | 7 erreurs terminé |
| `ERREUR7OK2` | 7 erreurs 2 terminé |
| `ERREUR7D1` - `ERREUR7D7` | Différences 1-7 trouvées |

---

## 8. États d'occupation

| Variable | Description |
|----------|-------------|
| `OCCUPE` | État occupé général |
| `OCCUPE1` - `OCCUPE12` | États d'occupation 1-12 |

---

## 9. Personnages

| Variable | Description |
|----------|-------------|
| `PEPE` | Pépé René (France) |
| `DRUIDE` | Druide |
| `PASTEUR` | Pasteur |
| `COLOMB` | Christophe Colomb |
| `BEETHOVEN` | Beethoven |
| `VINCI` | Léonard de Vinci |
| `FROG` | Grenouille |
| `PUNK` | Punk |
| `LAPIN` | Lapin |
| `TEMPSLAPIN` | Temps du lapin |
| `LAPINSORTIE` | Lapin sorti |
| `NAINOK` | Nain terminé |

---

## 10. Variables spéciales

### Plongée
| Variable | Description |
|----------|-------------|
| `PLONGE` | État plongée |
| `HARPON` | Harpon |
| `MASQUE` | Masque |
| `PALME` | Palmes |
| `BOUEE` | Bouée |
| `BOUT_PLO` | Bouteille plongée |

### Commerce
| Variable | Description |
|----------|-------------|
| `POGNON` | Argent |
| `MILLEEURO` | 1000 euros |

### Divers
| Variable | Description |
|----------|-------------|
| `DICO` | Dictionnaire |
| `EXPO` | Exposition |
| `CAPITALE` | Capitale |
| `MENU` | Menu |
| `CARTETOUR` | Carte de tour |
| `PORTESECRETE` | Porte secrète |
| `BOITE` | Boîte |
| `NUMERO` | Numéro |
| `CPHOTO` | Compteur photo |

---

## 11. Variables de test

| Variable | Description |
|----------|-------------|
| `DELPHITEST1` | Test Delphi 1 |
| `DELPHITEST2` | Test Delphi 2 |
| `BIDON` | Variable bidon |

---

## 12. Valeurs initiales recommandées

```typescript
const initialGameState = {
  // Système
  score: 100,      // Score de départ
  fiole: 0,        // Fiole vide

  // Tous les pays à 0 (non visités)
  countries: Object.fromEntries(
    ['france', 'allemagne', 'angleterre', ...].map(c => [c, 0])
  ),

  // Outils actifs par défaut
  tools: {
    calc: 1,
    telephone: 1,
    sacados: 1,
    trans: 1,
    active: 0,
  },

  // Inventaire vide (tous les objets à 0)
  inventory: {},

  // Bonus non collectés
  bonus: {},

  // Variables de quêtes à 0
  quests: {},
};
```

---

*Liste des variables extraite des fichiers VND d'Europeo*
*Version 1.0 - Janvier 2025*
