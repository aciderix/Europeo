# Spécification du Format VND - Europeo

## Vue d'ensemble

Le format `.vnd` (Visual Novel Data) est un format binaire propriétaire utilisé par le moteur VnStudio de Sopra Multimedia pour le jeu éducatif Europeo (1999). Ce document détaille la structure et la logique du format pour permettre un portage fidèle en React.

---

## 1. Structure Générale

### 1.1 En-tête du fichier

```
Offset  | Contenu
--------|------------------
0x0009  | "VNFILE" (signature)
0x0013  | "2.13" (version)
0x001F  | "Europeo" (nom du projet)
0x002A  | "Sopra Multimedia" (éditeur)
0x003E  | "5D51F233" (checksum/ID)
```

### 1.2 Fichiers associés

Chaque pays a une structure de dossiers :
```
pays/
├── pays.vnd          # Données de scènes et logique
├── pays.vnp          # Projet (point d'entrée)
├── img24/            # Images 24-bit (backgrounds, sprites)
│   └── roll/         # Hotspots/éléments interactifs
├── movie/            # Vidéos AVI
├── digit/            # Sons WAV
└── html/             # Contenus HTML (encyclopédie)
```

---

## 2. Système de Scènes

### 2.1 Définition d'une scène

Une scène est composée de :
- **Background** : Image BMP plein écran (640x400 pixels zone de jeu)
- **Hotspots** : Éléments cliquables positionnés dynamiquement
- **Conditions** : Logique exécutée à l'entrée et lors des interactions
- **Audio** : Musique de fond et effets sonores

### 2.2 Navigation entre scènes

```
scene <numéro>                    # Change vers la scène N
runprj ..\pays\pays.vnp <scene>   # Change de pays et va à la scène
```

### 2.3 Exemple de flux

```
Scène 1 (Paris)
    ↓ [clic sur ticket]
Scène 13 (Tour Eiffel)
    ↓ [clic sur sortie]
Scène 4 (Carte de Paris)
    ↓ [clic sur gare]
runprj ..\angl\angleterre.vnp 69  → Angleterre
```

---

## 3. Système de Hotspots

### 3.1 Création de hotspot

```
addbmp <id> <fichier.bmp> <layer> <x> <y>
```

| Paramètre | Description |
|-----------|-------------|
| `id` | Identifiant unique du hotspot |
| `fichier.bmp` | Chemin vers l'image BMP |
| `layer` | Couche de rendu (0=normal, 6=UI/toolbar) |
| `x, y` | Coordonnées de positionnement |

**Exemple :**
```
addbmp laphoto roll\laphoto.bmp 0 66 196
```
Crée un hotspot "laphoto" à la position (66, 196).

### 3.2 Zone de clic

**IMPORTANT** : La zone cliquable est définie par les dimensions du BMP lui-même.
- Le BMP contient l'image de l'objet
- Ses dimensions définissent la hitbox
- Position = coin supérieur gauche

```
Hotspot "ticket" (50x30 pixels) à position (607, 115)
→ Zone cliquable : Rectangle(607, 115, 657, 145)
```

### 3.3 Suppression de hotspot

```
delbmp <id>
```

---

## 4. Système de Commandes

### 4.1 Commandes graphiques

| Commande | Syntaxe | Description |
|----------|---------|-------------|
| `addbmp` | `addbmp id fichier layer x y` | Ajoute une image/hotspot |
| `delbmp` | `delbmp id` | Supprime une image/hotspot |
| `playavi` | `playavi fichier 1 x y w h` | Joue une vidéo à position |
| `playtext` | `playtext x y w h 0 "texte"` | Affiche du texte |

### 4.2 Commandes audio

| Commande | Syntaxe | Description |
|----------|---------|-------------|
| `playwav` | `playwav fichier.wav mode` | Joue un son (mode: 1=once, 2=loop, 6=ambiance) |
| `closewav` | `closewav` | Arrête le son en cours |

### 4.3 Commandes de navigation

| Commande | Syntaxe | Description |
|----------|---------|-------------|
| `scene` | `scene N` | Change de scène |
| `runprj` | `runprj chemin.vnp N` | Change de projet/pays |
| `hotspot` | `hotspot N` | Active un hotspot spécifique |

### 4.4 Commandes de variables

| Commande | Syntaxe | Description |
|----------|---------|-------------|
| `set_var` | `set_var variable valeur` | Définit une variable |
| `inc_var` | `inc_var variable valeur` | Incrémente (peut être négatif) |
| `dec_var` | `dec_var variable valeur` | Décrémente |

### 4.5 Commandes spéciales

| Commande | Syntaxe | Description |
|----------|---------|-------------|
| `rundll` | `rundll fichier.dll` | Exécute une DLL (mini-jeu) |
| `score` | `score 6 x y w h 0 <score>` | Affiche le score |

---

## 5. Système de Conditions

### 5.1 Syntaxe générale

```
variable opérateur valeur then action [else action_alternative]
```

### 5.2 Opérateurs

| Opérateur | Description |
|-----------|-------------|
| `=` | Égal |
| `!=` | Différent |
| `<` | Inférieur |
| `>` | Supérieur |

### 5.3 Exemples

```
# Simple condition
ticket = 1 then scene 13

# Avec else
painok = 0 then scene 9 else scene 29

# Condition sur score
score < 0 then runprj ..\couleurs1\couleurs1.vnp 54

# Affichage conditionnel
parfum != 0 then addbmp parfum roll\parf1.bmp 0 321 166

# Incrémentation conditionnelle
champagne = 2 then inc_var score 5
```

### 5.4 Pattern de comptage d'inventaire

Le jeu utilise un pattern récurrent pour compter les objets :
```
non 0                              # Initialise compteur
clerouge = 2 then inc_var non 1    # Si objet possédé, +1
ballon1 = 2 then inc_var non 1
bouee = 2 then inc_var non 1
...
non = 0 then playavi anim1.avi ... # Animation si aucun objet
non = 1 then playavi anim99.avi ...# Animation alternative
```

---

## 6. Système de Variables

### 6.1 Variables globales (persistantes)

Ces variables persistent entre les scènes et les pays :

#### États des pays visités
```
FRANCE, ALLEMAGNE, ANGLETERRE, AUTRICHE, BELGIQUE,
DANEMARK, ECOSSE, ESPAGNE, FINLANDE, GRECE,
IRLANDE, ITALIE, PAYSBAS, PORTUGAL, SUEDE
```
Valeurs : `0` = non visité, `1` = en cours/visité

#### Outils de la barre
```
CALC        # Calculatrice (0=inactive, 1=active)
TELEPHONE   # Téléphone
SACADOS     # Inventaire (sac à dos)
TRANS       # Transport
ACTIVE      # État actif
```

#### Progression
```
SCORE       # Score du joueur (peut être négatif!)
FIOLE       # Niveau de remplissage (1-12)
BONUS1-30   # Bonus collectés
OCCUPE1-12  # États d'occupation
```

### 6.2 Variables d'objets (inventaire)

Chaque objet a 3 états :
- `0` = Non découvert
- `1` = Découvert/visible
- `2` = Dans l'inventaire (possédé)

```
# Objets collectables (100+)
TICKET, PHOTO, CHAMPAGNE, PARFUM, PAIN, HELICE,
HARPON, MASQUE, BALLON1, BOUEE, PALME, GUITARE,
VIOLON, PARTITION, FROMAGE, CHIANTI, PIZZA, etc.
```

### 6.3 Variables de quêtes/mini-jeux

```
# Juste Prix
JUSTEPRIXOBJ, JUSTEPRIXEURO, JUSTEPRIXCLIC
JUSTEPRIX1, JUSTEPRIX10, JUSTEPRIX15...
JUSTEPRIXSCORE, JUSTEPRIXOK

# Course de lévriers
LEVRIERNUMERO, LEVRIERPARI, LEVRIERRESULTAT

# Pain (boulangerie)
PAINOK, EAUPAIN, FARINE, LEVURE, SALIERE

# Peintre
PEINTRE, PEINTRE1, SCOREPEINTRE, PALETTE
```

### 6.4 Variables de contrôle

```
NON         # Variable temporaire de comptage
LOC         # Localisation courante
CPAYS       # Pays courant
CMENU1-3    # États de menu
```

---

## 7. Barre d'outils (Toolbar)

### 7.1 Structure

La barre d'outils occupe la zone 0-640 x 400-480 (bas de l'écran).

```
toolbar ..\..\barre\images\barre.bmp 6 0 400 640 480
```

### 7.2 Éléments de la toolbar

| Élément | Position | Fonction |
|---------|----------|----------|
| Score | (15-160, 410-470) | Affichage du score |
| Transport | (122-163, 400) | Voyager entre pays |
| Calculatrice | (246-281, 400-403) | Euro32.dll |
| Téléphone | (179-316, 400) | Aide/indices |
| Inventaire | (338-384, 400) | Inv.dll - sac à dos |
| Fiole | (141-197, 451-461) | Progression (f1-f12.bmp) |
| Drapeau pays | (400-452, 400-407) | Pays actuel |
| Ordinateur | (553-564, 408) | Options |
| Flèche | (499, 407) | Navigation |

### 7.3 Affichage conditionnel

```
# Fiole de progression (12 niveaux)
fiole = 1 then addbmp fiole ..\..\barre\images\f1.bmp 6 197 461
fiole = 2 then addbmp fiole ..\..\barre\images\f2.bmp 6 196 461
...
fiole = 12 then addbmp fiole ..\..\barre\images\f12.bmp 6 196 461

# Drapeau du pays actuel
france = 1 then addbmp info ..\..\barre\images\p_france.bmp 6 452 400
allemagne = 1 then addbmp info ..\..\barre\images\p_all.bmp 6 452 400
```

---

## 8. Mini-jeux (DLLs)

### 8.1 DLLs identifiées

| DLL | Fonction |
|-----|----------|
| `euro32.dll` | Calculatrice de conversion Euro/Francs |
| `inv.dll` | Gestionnaire d'inventaire |
| `pepe.dll` | Mini-jeu Pépé René |
| `frog.dll` | Mini-jeu grenouille |
| `vnoption.dll` | Options du jeu |
| `vnresmod.dll` | Module de ressources |

### 8.2 Intégration

```
calc = 1 then rundll ..\barre\euro32.dll
sacados = 1 then rundll ..\barre\inv.dll
```

---

## 9. Formats de fichiers

### 9.1 Images (.bmp)

- Format : BMP Windows 24-bit
- Résolution backgrounds : 640x400 pixels
- Hotspots : Tailles variables (forme = zone de clic)
- Transparence : Magenta (#FF00FF) = transparent

### 9.2 Vidéos (.avi)

- Format : AVI (Video for Windows)
- Codec : Indeo ou Cinepak (typique de l'époque)
- Usage : Animations de personnages, cinématiques

### 9.3 Sons (.wav)

- Format : WAV PCM
- Types : Effets sonores, musiques d'ambiance, dialogues

### 9.4 HTML

- Contenu encyclopédique
- Affiché dans une fenêtre intégrée

---

## 10. Mapping pour React

### 10.1 Structure de données recommandée

```typescript
interface Scene {
  id: number;
  background: string;           // Chemin BMP
  music?: string;               // Son d'ambiance
  hotspots: Hotspot[];
  onEnter: Condition[];         // Conditions à l'entrée
}

interface Hotspot {
  id: string;
  image: string;                // Chemin BMP
  position: { x: number; y: number };
  layer: number;
  conditions: Condition[];      // Actions au clic
}

interface Condition {
  variable: string;
  operator: '=' | '!=' | '<' | '>';
  value: number;
  thenAction: Action;
  elseAction?: Action;
}

type Action =
  | { type: 'scene'; target: number }
  | { type: 'runprj'; project: string; scene: number }
  | { type: 'addbmp'; id: string; image: string; x: number; y: number }
  | { type: 'delbmp'; id: string }
  | { type: 'playavi'; file: string; x: number; y: number; w: number; h: number }
  | { type: 'playwav'; file: string; mode: number }
  | { type: 'set_var'; variable: string; value: number }
  | { type: 'inc_var'; variable: string; value: number }
  | { type: 'dec_var'; variable: string; value: number }
  | { type: 'rundll'; dll: string }
  | { type: 'playtext'; text: string; x: number; y: number };
```

### 10.2 GameState

```typescript
interface GameState {
  currentCountry: string;
  currentScene: number;
  score: number;
  fiole: number;                // 0-12

  // Pays visités
  countries: Record<string, boolean>;

  // Objets (0=inconnu, 1=vu, 2=possédé)
  inventory: Record<string, 0 | 1 | 2>;

  // Outils actifs
  tools: {
    calc: boolean;
    telephone: boolean;
    sacados: boolean;
    trans: boolean;
  };

  // Variables de quêtes
  quests: Record<string, number>;

  // Bonus collectés
  bonus: Record<string, boolean>;
}
```

### 10.3 Moteur de conditions

```typescript
function evaluateCondition(
  condition: Condition,
  state: GameState
): boolean {
  const value = getVariable(condition.variable, state);
  switch (condition.operator) {
    case '=': return value === condition.value;
    case '!=': return value !== condition.value;
    case '<': return value < condition.value;
    case '>': return value > condition.value;
  }
}

function executeAction(action: Action, state: GameState): GameState {
  switch (action.type) {
    case 'scene':
      return { ...state, currentScene: action.target };
    case 'inc_var':
      return updateVariable(state, action.variable, v => v + action.value);
    // ... autres actions
  }
}
```

---

## 11. Liste des pays et fichiers

| Pays | Dossier | Fichier VND | Scènes estimées |
|------|---------|-------------|-----------------|
| Démarrage | frontal | start.vnd | ~5 |
| France | france | france.vnd | ~35 |
| Allemagne | allem | allem.vnd | ~30 |
| Angleterre | angl | angleterre.vnd | ~32 |
| Autriche | autr | autr.vnd | ~28 |
| Belgique | belge | belge.vnd | ~28 |
| Danemark | danem | danem.vnd | ~20 |
| Écosse | ecosse | ecosse.vnd | ~26 |
| Espagne | espa | espa.vnd | ~30 |
| Finlande | finlan | finlan.vnd | ~18 |
| Grèce | grece | grece.vnd | ~24 |
| Pays-Bas | holl | holl.vnd | ~22 |
| Irlande | irland | irland.vnd | ~24 |
| Italie | italie | italie.vnd | ~26 |
| Portugal | portu | portu.vnd | ~26 |
| Suède | suede | suede.vnd | ~22 |
| Barre d'outils | barre | barre.vnd | UI |
| Hub/Euroland | couleurs1 | couleurs1.vnd | Hub central |
| Bibliothèque | biblio | biblio.vnd | Encyclopédie |

---

## 12. Workflow de portage

### Phase 1 : Parser VND → JSON
1. Extraire toutes les chaînes (déjà fait)
2. Parser les conditions et actions
3. Identifier les scènes et leurs contenus
4. Générer un JSON structuré par pays

### Phase 2 : Convertir les assets
1. BMP → PNG (avec gestion transparence magenta)
2. WAV → MP3/OGG (compression web)
3. AVI → MP4/WebM (codec moderne)

### Phase 3 : Implémenter le moteur React
1. GameEngine : État global et évaluation des conditions
2. SceneRenderer : Affichage des scènes et hotspots
3. HotspotManager : Gestion des clics et zones
4. ToolbarComponent : Barre d'outils fixe
5. MiniGameManager : Intégration des mini-jeux

### Phase 4 : Recréer les mini-jeux
1. Calculatrice Euro (déjà fait !)
2. Inventaire (sac à dos)
3. Mini-jeux spécifiques (Pépé, grenouille, etc.)

---

## Annexe A : Patterns récurrents

### Pattern d'entrée de scène
```
# Son d'ambiance
france.wav

# Background
paris2.bmp

# Vérification game over
score < 0 then runprj ..\couleurs1\couleurs1.vnp 54

# Configuration police
18 0 #ffffff Comic sans MS

# Textes descriptifs
playtext x y w h 0 "Description"
```

### Pattern de hotspot interactif
```
# Condition au clic
parfum = 0 then playtext 200 230 375 365 0 Un flacon de parfum
parfum = 0 then set_var parfum 1
parfum = 0 then addbmp parfum roll\parfum.bmp 0 321 166
```

### Pattern de personnage animé
```
non 0
[liste de conditions pour compter les objets]
non = 0 then playavi personnage1.avi 1 x y w h
non != 0 then playavi personnage99.avi 1 x y w h
```

---

*Document généré pour le portage React d'Europeo*
*Version 1.0 - Janvier 2025*
