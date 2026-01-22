# Europeo - Analyse pour Portage React

## Vue d'ensemble

**Europeo** est un jeu éducatif Visual Novel sur les pays européens, développé par **Sopra Multimedia** en Borland C++ avec la bibliothèque OWL (Object Windows Library) et DirectX 6.

---

## Architecture Originale

### Technologies utilisées
- **Langage**: Borland C++ (pas VB5 comme supposé initialement)
- **Framework UI**: Borland OWL 5.2 (owl52t.dll - 910 KB)
- **Graphiques**: DirectX 6 / DirectDraw
- **Format de données**: VND/VNP propriétaire (VNFILE 2.13)

### Fichiers clés
| Fichier | Rôle |
|---------|------|
| `frontal/europeo.exe` | Exécutable principal (868 KB) |
| `frontal/vndllapi.dll` | API du moteur Visual Novel |
| `frontal/vnoption.dll` | Gestion des options/dialogues |
| `VnStudio/vnresmod.dll` | Modificateur de ressources |
| `barre/Euro32.dll` | Convertisseur Euro |
| `barre/inv.dll` | Gestion de l'inventaire |

### Fonctions exportées (vndllapi.dll)
```
InitVNCommandMessage  - Initialise le système de messages
VNDLLVarFind          - Recherche une variable
VNDLLVarAddModify     - Ajoute/modifie une variable
DirectDrawEnabled     - Vérifie DirectDraw
```

---

## Format VND (Visual Novel Data)

### Structure du fichier
```
HEADER:
  Magic: "VNFILE"
  Version: "2.13"
  Application: "Europeo"
  Developer: "Sopra Multimedia"
  ID: "5D51F233"
  Registry: "SOFTWARE\SOPRA MULTIMEDIA\EUROPEO"

VARIABLES:
  Liste des variables globales du jeu

SCENES:
  Liste des scènes avec hotspots et commandes
```

### Format VNP (Visual Novel Project)
Fichier INI définissant les chemins des ressources:
```ini
[MAIN]
LIMITS=65535
PREFS=65535
DATFILE=france.vnd
WAV=digit\
MID=midi\
PAL=palette\
IMG8=img24\
IMG24=img24\
AVI=movie\
TXT=html\
```

---

## DSL (Domain-Specific Language) VND

### Commandes de navigation
| Commande | Description |
|----------|-------------|
| `scene N` | Change vers la scène N |
| `runprj path.vnp N` | Charge un projet VNP et va à la scène N |
| `hotspot N` | Active le hotspot N |

### Commandes multimédia
| Commande | Description |
|----------|-------------|
| `playavi file.avi mode x1 y1 x2 y2` | Joue une vidéo |
| `playwav file.wav mode` | Joue un son (1=once, 2=loop) |
| `playtext x y w h flags text` | Affiche du texte |
| `playhtml file.htm flags x y w h` | Affiche du contenu HTML |

### Commandes graphiques
| Commande | Description |
|----------|-------------|
| `addbmp name file.bmp flags x y` | Ajoute une image |
| `delbmp name` | Supprime une image |
| `toolbar path x1 y1 x2 y2` | Définit la barre d'outils |
| `defcursor file.cur` | Change le curseur |

### Commandes système
| Commande | Description |
|----------|-------------|
| `rundll path.dll` | Exécute une DLL (mini-jeux) |
| `closedll` | Ferme la DLL active |
| `closewav` | Arrête le son |

### Manipulation de variables
| Commande | Description |
|----------|-------------|
| `set_var variable value` | Définit une variable |
| `inc_var variable value` | Incrémente une variable |
| `dec_var variable value` | Décrémente une variable |

### Conditions
```
# Syntaxe simple
variable = value then command

# Avec else
variable = value then command1 else command2

# Opérateurs supportés
=, !=, <, >, >=, <=
```

### Exemples concrets
```
# Changer de pays
score 52
..\france\france.vnp 18

# Condition avec action
guitare = 0 then addbmp guitare guitare.bmp 0 1172 216
guitare = 0 then set_var guitare 1
guitare != 0 then delbmp guitare

# Mini-jeu prix
justeprixquestion = 0 then addbmp question rol\juste1.bmp 0 169 27
justeprixreponse = 5 then playwav applaud.wav 1 else playavi fermier3.avi 1

# Navigation vers pays
avion.avi 1
score 52
..\france\france.vnp 18
```

---

## Structure des scènes

Chaque scène contient:
1. **Image de fond** (background BMP)
2. **Hotspots** (zones cliquables avec coordonnées rectangulaires)
3. **Commandes d'entrée** (exécutées à l'entrée de scène)
4. **Événements de sortie** (déclenchés par les hotspots)
5. **Barre d'outils** (interface commune)

### Scènes spéciales
- `Intro` - Vidéo d'introduction du pays
- `Toolbar` - Barre de navigation (score, inventaire, etc.)

---

## Variables globales identifiées

### État du jeu
| Variable | Description |
|----------|-------------|
| `score` | Score du joueur |
| `sacados` | Sac à dos visible |
| `calc` | Calculatrice visible |
| `telephone` | Téléphone visible |
| `trans` | Transport visible |
| `fiole` | Niveau de la fiole (1-12) |

### Pays visités (0=non, 1=oui)
`allemagne`, `france`, `angleterre`, `autriche`, `belgique`, `danemark`, `ecosse`, `espagne`, `finlande`, `grece`, `paysbas`, `irlande`, `italie`, `portugal`, `suede`, `euroland`

### Objets collectables (~100 objets)
`guitare`, `pier_berlin`, `houblon`, `orge`, `bouee`, `masque`, `harpon`, `photo`, `piece`, `raquette`, `ciseaux`, `pizza`, `costume`, `loupe`, `palme`, etc.

### États des fioles par pays
`fiolegrece`, `fioleecosse`, `fioleirlande`, `fioleespagne`, `fiolesuede`, `fiolefinlande`, `fioleautriche`, `fiolepaysbas`, `fioleitalie`, `fioleangleterre`

---

## Inventaire des ressources

| Type | Quantité | Format |
|------|----------|--------|
| Images BMP | 1,339 | 24-bit BMP |
| Vidéos AVI | 392 | AVI |
| Sons WAV | 220 | WAV |
| HTML | 224 | HTML éducatif |
| Curseurs | 100 | CUR |
| Projets VND | 19 | Données scènes |
| Projets VNP | 20 | Config chemins |

### Taille par pays
| Pays | Taille | Contenu principal |
|------|--------|-------------------|
| couleurs1 | 131 MB | Hub central, mini-jeux |
| biblio | 56 MB | Encyclopédie |
| angl | 55 MB | Angleterre |
| italie | 52 MB | Italie |
| ecosse | 36 MB | Écosse |
| grece | 34 MB | Grèce |
| france | 30 MB | France |

---

## Architecture React Proposée

### Structure des fichiers
```
src/
├── engine/
│   ├── VNParser.ts         # Parseur de fichiers VND
│   ├── VNProjectLoader.ts  # Chargeur de projets VNP
│   ├── ScriptInterpreter.ts # Interpréteur de commandes
│   └── types.ts            # Types TypeScript
├── store/
│   ├── gameStore.ts        # État global (Zustand/Redux)
│   ├── variables.ts        # Variables du jeu
│   └── inventory.ts        # Inventaire
├── components/
│   ├── Game/
│   │   ├── Scene.tsx       # Conteneur de scène
│   │   ├── Hotspot.tsx     # Zone cliquable
│   │   ├── Background.tsx  # Image de fond
│   │   └── Toolbar.tsx     # Barre d'outils
│   ├── Media/
│   │   ├── VideoPlayer.tsx # Lecteur vidéo
│   │   ├── AudioPlayer.tsx # Lecteur audio
│   │   └── HtmlViewer.tsx  # Afficheur HTML
│   ├── UI/
│   │   ├── Score.tsx       # Affichage score
│   │   ├── Inventory.tsx   # Inventaire
│   │   └── Calculator.tsx  # Convertisseur Euro
│   └── MiniGames/
│       ├── JustePrix.tsx   # Jeu du juste prix
│       ├── Memory.tsx      # Memory (Écosse)
│       └── Wheel.tsx       # Roue (roue.dll)
├── hooks/
│   ├── useGameEngine.ts    # Hook principal
│   ├── useAudio.ts         # Gestion audio
│   └── useVideo.ts         # Gestion vidéo
├── assets/
│   └── [Ressources converties]
└── data/
    └── [VND parsés en JSON]
```

### Étapes de portage

#### Phase 1: Parser VND (Priorité haute)
1. Implémenter le parseur binaire VND
2. Extraire les variables, scènes et commandes
3. Convertir en format JSON exploitable

#### Phase 2: Moteur de base
1. Système de variables globales
2. Machine à états pour les scènes
3. Interpréteur de conditions

#### Phase 3: Rendu
1. Composant Scene avec hotspots
2. Système de layers (background, sprites, UI)
3. Gestion des curseurs personnalisés

#### Phase 4: Multimédia
1. Conversion BMP → PNG/WebP
2. Conversion AVI → MP4/WebM
3. Conversion WAV → MP3/OGG
4. Lecteurs React pour chaque type

#### Phase 5: Mini-jeux
1. Recréer la logique des DLLs en JavaScript
2. Convertisseur Euro (Euro32.dll)
3. Inventaire (inv.dll)
4. Jeux spécifiques par pays

---

## Prochaines étapes recommandées

1. **Créer un parseur VND en TypeScript** pour extraire les données
2. **Convertir les assets** (BMP→PNG, AVI→MP4, WAV→MP3)
3. **Créer un prototype** avec un seul pays (ex: France)
4. **Implémenter le moteur** de base progressivement
5. **Ajouter les pays** un par un

---

## Notes techniques

### Encodage texte
Les fichiers utilisent l'encodage Windows-1252 (Latin-1). Les accents français sont présents.

### Coordonnées
Le jeu utilise une résolution de **640x480**. Les coordonnées des hotspots sont absolues.

### Score
Le score est global et peut devenir négatif. Si `score < 0`, le joueur est renvoyé vers `couleurs1.vnp` (hub).

### DRM original
Le jeu nécessitait le CD original. Cette protection peut être ignorée pour le portage.
