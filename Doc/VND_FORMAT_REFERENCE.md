# VND Format Reference - Documentation Complète

## Vue d'Ensemble

Le format VND (Visual Novel Data) est utilisé par le moteur europeo.exe pour stocker les projets de visual novel interactifs.

---

## Structure du Projet (Fichier INI)

### Section [MAIN]

| Clé | Type | Description | Exemple |
|-----|------|-------------|---------|
| `AREAS` | int | Nombre de scènes/zones | `42` |
| `TITLE` | string | Titre du projet | `"Euroland"` |
| `INDEX_ID` | int | Offset de base pour navigation 'i' | `0` |
| `EXIT_ID` | int | ID de la scène de sortie | `1` |
| `NAME` | string | Nom affiché | `"Mon Projet"` |
| `BKCOLOR` | r,g,b | Couleur de fond par défaut | `"0,0,0"` |
| `BKTEXTURE` | int | ID texture de fond | `0` |
| `DEFCURSOR` | int | ID curseur par défaut | `100` |
| `CAPS` | int | Capacités/options du projet | `0` |

### Section [PREFS]

Préférences utilisateur sauvegardées.

### Section [LIMITS]

Limites du projet (zones accessibles, etc.)

---

## Structure d'une Scène (Section [AREA_n])

### Médias

| Clé | Type | Description | Défaut |
|-----|------|-------------|--------|
| `AVI` | string | Vidéo d'introduction | `""` |
| `SETAVI` | int | Flag: jouer la vidéo | `0` |
| `IMG` | string | Image de fond (.bmp) | `""` |
| `SETIMG` | int | Flag: afficher l'image | `0` |
| `SND` | string | Son ambiant (.wav) | `""` |
| `SETSND` | int | Flag: jouer le son | `0` |
| `MID` | string | Musique MIDI (.mid) | `""` |
| `SETMID` | int | Flag: jouer la musique | `0` |
| `PALETTE` | string | Fichier palette (.pal) | `""` |

### Texte HTML

| Clé | Type | Description | Défaut |
|-----|------|-------------|--------|
| `TXT` | string | Fichier texte HTML | `""` |
| `TXTRECT` | x,y,w,h | Rectangle d'affichage | `"0,0,0,0"` |
| `SETTXT` | int | Flag: afficher le texte | `0` |
| `TXTHREFOFFSET` | int | Offset pour les liens | `0` |

### Timer & Toolbar

| Clé | Type | Description | Défaut |
|-----|------|-------------|--------|
| `TIMER` | delay,scene | Timer automatique (ms, scène cible) | `"0,0"` |
| `TOOLBAR` | 5 ints | Configuration barre d'outils | `"0,0,0,0,0"` |

---

## Hotspots (Zones Cliquables)

### Compteur

| Clé | Description |
|-----|-------------|
| `NHOTSPOT` | Nombre de hotspots (ancien format) |
| `HSNUM` | Nombre de hotspots (nouveau format) |

### Par Hotspot (n = numéro)

| Clé | Type | Description |
|-----|------|-------------|
| `HOTSPOT_n` | coords | Définition de la zone (rect ou points) |
| `HSCMD_n` | string | Commande(s) à exécuter au clic |
| `HSRGN_n` | polygon | Région polygonale (npoints,x1,y1,x2,y2,...) |
| `HSCUR_n` | int | ID curseur au survol |
| `HSVIDEO_n` | string | Vidéo à jouer au clic |
| `HSVIDEOFLAGS_n` | int | Flags de lecture vidéo |
| `HSVIDEORECT_n` | rect | Zone d'affichage vidéo (x,y,w,h) |

---

## Types de Commandes (Command Types)

### Table des Commandes (switch case)

| Case | Commande | Description |
|------|----------|-------------|
| 0 | `quit` | Quitter l'application |
| 1 | `about` | Afficher À propos |
| 2 | `prefs` | Préférences |
| 3 | `prev` | Scène précédente |
| 4 | `next` | Scène suivante |
| 5 | `zoom` | Zoom |
| **6** | **`scene`** | **Navigation vers scène** |
| 7 | `hotspot` | Définir hotspot |
| 8 | `tiptext` | Texte d'info-bulle |
| 9 | `playavi` | Jouer vidéo AVI |
| 10 | `playbmp` | Afficher bitmap |
| 11 | `playwav` | Jouer son WAV |
| 12 | `playmid` | Jouer MIDI |
| 13 | `playhtml` | Afficher HTML |
| 14 | `zoomin` | Zoom avant |
| 15 | `zoomout` | Zoom arrière |
| 16 | `pause` | Pause |
| 17 | `exec` | Exécuter programme |
| 18 | `explore` | Ouvrir explorateur |
| 19 | `playcda` | Jouer CD Audio |
| 20 | `playseq` | Jouer séquence |
| 21 | `if` | Condition |
| 22 | `set_var` | Définir variable |
| 23 | `inc_var` | Incrémenter variable |
| 24 | `dec_var` | Décrémenter variable |
| 25 | `invalidate` | Invalider affichage |
| 26 | `defcursor` | Définir curseur |
| 27 | `addbmp` | Ajouter bitmap |
| 28 | `delbmp` | Supprimer bitmap |
| 29 | `showbmp` | Afficher bitmap |
| 30 | `hidebmp` | Cacher bitmap |
| 31 | `runprj` | Charger autre projet |
| 32 | `update` | Mettre à jour |
| 33 | `rundll` | Exécuter DLL |
| 34 | `msgbox` | Boîte de message |
| 35 | `playcmd` | Jouer commande |
| 36 | `closewav` | Fermer WAV |
| 37 | `closedll` | Fermer DLL |
| 38 | `playtext` | Jouer texte |
| 39 | `font` | Définir police |
| 40 | `rem` | Commentaire |
| 41 | `addtext` | Ajouter texte |
| 42 | `delobj` | Supprimer objet |
| 43 | `showobj` | Afficher objet |
| 44 | `hideobj` | Cacher objet |
| 45 | `load` | Charger sauvegarde |
| 46 | `save` | Sauvegarder |
| 47 | `closeavi` | Fermer AVI |
| 48 | `closemid` | Fermer MIDI |

---

## Suffixes de Navigation (Commande scene)

### Suffixes Confirmés

| Suffixe | Nom | Calcul | Exemple |
|---------|-----|--------|---------|
| `i` | Index | `INDEX_ID + n` | `5i` → scène INDEX_ID+5 |
| `d` | Direct | `n` directement | `13d` → scène 13 |
| `+` | Relatif+ | `current + n` | `+1` → scène suivante |
| `-` | Relatif- | `current - n` | `-1` → scène précédente |
| _(none)_ | Défaut | Probablement direct | `4` → scène 4 |

### Suffixes Non Confirmés

| Suffixe | Hypothèse | Contexte observé |
|---------|-----------|------------------|
| `j` | Jump/Jeu | Avec condition `jeu = 1` |
| `h` | ? | Avec condition `score < 0` |
| `f` | ? | Avec condition `score < 0` |

---

## Structure Binaire VND

### En-tête (sub_41721D)

```
Offset  Size  Description
------  ----  -----------
0x00    var   Signature "VNFILE" (string)
+?      2     Version/Scene count (word)
```

### Propriétés Projet (lues après signature)

L'ordre de lecture dépend de la version:

```c
// Si version > 0:
operator>>(stream, &project[49]);      // Title string
if (version >= 0x2000D)
    operator>>(stream, &project[53]);  // Autre string
sub_416781(&project[29], stream, ctx); // Paramètres projet
if (version >= 0x2000B)
    read_array(&project[73], stream);  // Limites/options
if (version >= 0x2000B)
    project[69] = readWord(stream);    // CAPS
project[61] = readWord(stream);        // EXIT_ID
project[65] = readWord(stream);        // INDEX_ID
if (version >= 0x2000A)
    operator>>(stream, &project[57]);  // NAME
if (version >= 0x2000A)
    read_variables(&project[94]);      // Variables initiales
```

### Structure TVNScene (0x99 = 153 bytes)

```c
struct TVNScene {
    void*   vtable;           // +0
    int     unknown;          // +4
    string  name;             // +8  (nom de la scène)
    // ... padding ...
    string  img_path;         // +32 (IMG)
    string  avi_path;         // +36 (AVI)
    string  snd_path;         // +40 (SND)
    string  mid_path;         // +44 (MID)
    string  txt_path;         // +48 (TXT)
    string  palette_path;     // +52 (PALETTE)
    int     txtrect[4];       // +60: x,y,w,h
    int     set_txt;          // +80
    int     set_avi;          // +84
    int     set_img;          // +88
    int     set_snd;          // +92
    int     set_mid;          // +96
    int     flags;            // +104
    void*   commands;         // +109 (tableau de commandes)
    void*   hotspots;         // +113 (tableau de hotspots)
    int     hotspot_count;    // +117
    // ...
    void*   timer;            // +145 (objet timer si défini)
    void*   toolbar;          // +149 (objet toolbar si défini)
};
```

### Record Type 6 (Scene Reference)

```
01 00 00 00  <- Séparateur
06 00 00 00  <- Type 6 (scene)
XX 00 00 00  <- Longueur de la string
[string]     <- Numéro + suffixe (ex: "35i", "7d")
```

### Format Palette (VNPALETTE)

```
Offset  Size  Description
------  ----  -----------
0x00    var   Signature "VNPALETTE" (string)
+?      2     Nombre de couleurs (word)
+?      4*N   Entrées RGBA (4 bytes par couleur)
```

---

## Interface DLL

### Exports Requis

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `VNSetDLLArguments` | `void __stdcall (char* args)` | Passer arguments |
| `VNCreateDLLWindow` | `HWND __stdcall (...)` | Créer fenêtre |
| `VNDestroyDLLWindow` | `bool __stdcall (int)` | Détruire fenêtre |

---

## Fichiers de Sauvegarde

### Format VNSAVFILE

```
Offset  Description
------  -----------
0x00    Signature "VNSAVFILE" (9 bytes)
+9      String: chemin du projet
+?      Word: numéro de la scène courante
+?      Variables (tableau):
        - Word: nombre de variables
        - Pour chaque variable:
          - String: nom
          - Valeur
+?      État de l'interface (TWindow)
```

### Fonctions Clés
- `sub_406345` - Charge les variables depuis le fichier
- `sub_40650B` - Sauvegarde les variables dans le fichier
- `dword_44ECCE` - Tableau global des variables en mémoire

---

## Système de Conditions (if)

### Opérateurs de Comparaison

| Code | Opérateur | Description |
|------|-----------|-------------|
| 1 | `==` | Égal |
| 2 | `!=` | Différent |
| 3 | `>` | Supérieur |
| 4 | `<` | Inférieur |
| 5 | `>=` | Supérieur ou égal |
| 6 | `<=` | Inférieur ou égal |

### Format de Condition

```
Format: "variable opérateur valeur"
Exemple: "score >= 10"
         "jeu == 1"
         "vie != 0"
```

### Implémentation (sub_40A479)

```c
switch (operator_code) {
    case 1: result = (a == b); break;  // ==
    case 2: result = (a != b); break;  // !=
    case 3: result = (a > b);  break;  // >
    case 4: result = (a < b);  break;  // <
    case 5: result = (a >= b); break;  // >=
    case 6: result = (a <= b); break;  // <=
}
```

---

## Système de Variables

### Commandes de Variables

| Case | Commande | Opération |
|------|----------|-----------|
| 22 | `set_var` | `variable = valeur` |
| 23 | `inc_var` | `variable += valeur` |
| 24 | `dec_var` | `variable -= valeur` |

### Structure Variable

```c
struct TVNVariable {
    char* name;      // Nom de la variable
    int   value;     // Valeur entière
};
```

---

## Système de Curseurs

### Curseur par Défaut

Défini dans `[MAIN]` avec `DEFCURSOR=100`

### IDs de Curseurs Système

| ID | Description |
|----|-------------|
| 1-4 | Curseurs directionnels |
| 98 | Curseur standard |
| 99 | Curseur alternatif |
| 105 | Curseur spécial |
| 32512 | Curseur système (IDC_ARROW) |

### Chargement de Curseur Personnalisé

```c
// Depuis fichier .cur
LoadCursorFromFileA(filename);

// Depuis ressources
LoadCursorA(hInstance, MAKEINTRESOURCE(id + 1000));
```

---

## Timer Automatique

### Format INI

```ini
TIMER=delay,scene_target
```

- `delay` : Délai en millisecondes (>= 0)
- `scene_target` : ID de la scène cible (> 0)

### Exemple

```ini
TIMER=5000,10    ; Après 5 secondes, aller à la scène 10
TIMER=0,0        ; Pas de timer (désactivé)
```

### Implémentation

```c
// Parsing
sscanf(buffer, "%i,%i", &delay, &scene_target);
if (scene_target > 0 && delay >= 0) {
    SetTimer(hwnd, 1, delay, NULL);
}
```

---

## Barre d'Outils (Toolbar)

### Format INI

```ini
TOOLBAR=btn1,btn2,btn3,btn4,btn5
```

5 valeurs entières définissant les boutons de la barre d'outils.

---

## HTML Supporté

### Tags Reconnus

| Tag | Description |
|-----|-------------|
| `<BR>` | Saut de ligne |
| `<P>` | Paragraphe |
| `<B>` | Gras |
| `<I>` | Italique |
| `<U>` | Souligné |
| `<H1>`-`<H6>` | Titres |
| `<OL>` | Liste ordonnée |
| `<UL>` | Liste non ordonnée |
| `<LI>` | Élément de liste |
| `<PRE>` | Texte préformaté |
| `<FONT>` | Police (color, size, face) |
| `<A HREF>` | Lien cliquable |

### Liens HTML

Les liens `<A HREF="...">` peuvent déclencher des commandes VND via `TXTHREFOFFSET`.

---

## Classes C++ (depuis europeo.exe)

| Classe | Description |
|--------|-------------|
| `TVNApplication` | Application principale |
| `TVNScene` | Scène individuelle |
| `TVNSceneArray` | Tableau de scènes |
| `TVNSceneParms` | Paramètres de scène |
| `TVNCommand` | Commande VND |
| `TVNVariable` | Variable de jeu |
| `TVNVariableArray` | Tableau de variables |
| `TVNIndexDependant` | Navigation par index |
| `TVNProjectParms` | Paramètres projet |

---

## Événements

| Événement | Description |
|-----------|-------------|
| `EV_ONFOCUS` | Au focus |
| `EV_ONCLICK` | Au clic |
| `EV_ONINIT` | À l'initialisation |
| `EV_AFTERINIT` | Après initialisation |

---

## Notes d'Implémentation React

### Priorités de Parsing

1. Lire signature VNFILE et version
2. Parser les propriétés projet (INDEX_ID crucial)
3. Charger chaque scène avec ses médias
4. Mapper les hotspots et leurs commandes
5. Implémenter la logique de navigation avec suffixes

### Gestion des Suffixes

```javascript
function resolveSceneTarget(param, currentScene, indexId) {
  const num = parseInt(param);
  const suffix = param.replace(/[0-9+-]/g, '');

  if (param.startsWith('+')) return currentScene + num;
  if (param.startsWith('-')) return currentScene - num;
  if (suffix === 'i') return indexId + num;
  if (suffix === 'd') return num;
  return num; // défaut
}
```

### Gestion des Conditions

```javascript
const OPERATORS = {
  1: (a, b) => a === b,  // ==
  2: (a, b) => a !== b,  // !=
  3: (a, b) => a > b,    // >
  4: (a, b) => a < b,    // <
  5: (a, b) => a >= b,   // >=
  6: (a, b) => a <= b,   // <=
};

function evaluateCondition(condition, variables) {
  // Format: "variable operator value"
  const match = condition.match(/(\w+)\s*(==|!=|>=|<=|>|<)\s*(\d+)/);
  if (!match) return false;

  const [, varName, op, value] = match;
  const varValue = variables[varName] || 0;
  const numValue = parseInt(value);

  const opCode = { '==': 1, '!=': 2, '>': 3, '<': 4, '>=': 5, '<=': 6 }[op];
  return OPERATORS[opCode](varValue, numValue);
}
```

### Gestion des Variables

```javascript
class VariableManager {
  constructor() {
    this.variables = {};
  }

  set(name, value) { this.variables[name] = value; }
  get(name) { return this.variables[name] || 0; }
  inc(name, value = 1) { this.variables[name] = this.get(name) + value; }
  dec(name, value = 1) { this.variables[name] = this.get(name) - value; }

  // Pour sauvegarde/chargement
  serialize() { return JSON.stringify(this.variables); }
  deserialize(data) { this.variables = JSON.parse(data); }
}
```

### Gestion du Timer

```javascript
function setupSceneTimer(scene, onTimerEnd) {
  const { timer } = scene; // Format: "delay,target"
  if (!timer) return null;

  const [delay, target] = timer.split(',').map(Number);
  if (target <= 0 || delay < 0) return null;

  return setTimeout(() => onTimerEnd(target), delay);
}
```
