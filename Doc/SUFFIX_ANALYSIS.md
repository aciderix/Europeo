# VND Navigation Suffix Analysis

## Découvertes Confirmées

### Structure Binaire
Après une vidéo de navigation (`video.avi 1`), on trouve:
```
01 00 00 00  <- Séparateur
06 00 00 00  <- Type 6 (référence de scène)
01 00 00 00  <- Longueur
XX XX        <- Numéro + suffixe (ex: "5i", "39i", "13d")
```

### Mappings Vidéo → Scène Extraits
| Vidéo | Cible | Type |
|-------|-------|------|
| bibliobis.avi | 4 | Sans suffixe |
| bankbis.avi | 3i | Index |
| home2.avi | 5i | Index |
| profbis.avi | 6i | Index |
| musee.avi | 7i | Index |
| fontaine.avi | 39i | Index |
| vuemusee.avi | 10 | Sans suffixe |
| depart.avi → espa.vnp | 13d | Direct |
| depart.avi → ecosse.vnp | 33d | Direct |
| depart.avi → france.vnp | 18 | Sans suffixe |

### ⚠️ CORRECTION IMPORTANTE (Janvier 2026)

**Les lettres après les nombres ne sont PAS des modificateurs de transition !**
Ce sont des **OPCODES SÉPARÉS** qui s'exécutent après que le nombre a été consommé comme paramètre.

### Système d'Opcodes TVNApplication

Le dispatcher `sub_43177D` utilise un switch sur les indices de commande.
Les lettres a-z correspondent aux indices 1-26, les codes numériques commencent à 27.

**Conversion lettre → index**: `index = char - 'a' + 1` (donc 'f' = 6, 'h' = 8, etc.)

### Table des Opcodes (Vérifiée dans le pseudo-code)

| Lettre | Index | Fonction | Description |
|--------|-------|----------|-------------|
| a–d | 1–4 | Messages fenêtre | PostMessageA / HandleMessage (UI système) |
| e | 5 | UI interne | Message 0x9C (mise à jour UI) |
| **f** | **6** | `sub_4268F8` | **Saut/changement de scène** |
| g | 7 | `sub_426B62` | Exécution de scripts avec arguments |
| h | 8 | `sub_426D33` | Tooltips / bulles d'aide |
| i | 9 | `sub_42703A` | Images (chargement, attributs, coords) |
| j | 10 | `sub_4275F6` | Bitmaps (transparence/palettes) |
| k | 11 | `sub_427B56` | Audio WAV |
| l | 12 | `sub_427C42` | Musique MIDI |
| m | 13 | `sub_427D34` | Chargement texte / segments script |
| p | 16 | `sub_405010` | Pause (Sleep) |
| q,r | 17–18 | `sub_427FAE` | Fichiers externes (ShellExecuteA) |
| s | 19 | `sub_427EFF` | CD-Audio |
| u | 21 | Callback | Gestion fenêtres |
| v,w,x | 22–24 | Variables | Manipulation via dword_44ECCE |
| y | 25 | InvalidateRect | Rafraîchissement écran |
| z | 26 | `sub_428154` | Chargement curseurs .cur |

### Codes Numériques (27+)

| Code | Fonction | Description |
|------|----------|-------------|
| 27 | `sub_428373` | Hotspots (zones cliquables) |
| 28–30 | `sub_428E06` | Visibilité images/boutons |
| **31** | `sub_42908F` | **Chargement scène (nouveau .vnd)** |
| 33 | DLL | Extensions VNCreateDLLWindow |
| 35 | Dialogues | Boîtes interactives |
| 39 | Police | TFont (nom, taille, styles) |
| 41 | Hypertexte | Texte riche avec liens |
| 45 | Sauvegarde | Écriture .sav (VNSAVFILE) |
| 46 | Chargement | Lecture .sav |

### Mécanisme de Parsing (Corrigé)

**Format du flux VND**: `[Valeur Numérique][Lettre Opcode]`

```c
// Exemple: "54h" dans le flux VND
//
// Étape 1: sub_407ED3 tokenise le flux
// Étape 2: atol("54h") retourne 54, pointeur avance sur 'h'
// Étape 3: La lettre 'h' est lue comme prochain opcode
// Étape 4: Dispatcher case 8 → sub_426D33(param=54) = Tooltip

// Donc "54h" signifie:
//   1. Charger la valeur 54 comme paramètre
//   2. Exécuter l'opcode 'h' (Tooltips) avec ce paramètre

// Et "54f" signifie:
//   1. Charger la valeur 54 comme paramètre
//   2. Exécuter l'opcode 'f' (Saut scène) → aller à la scène 54
```

**Ce n'est PAS**: "scène 54 avec transition fade"
**C'est**: "paramètre 54, puis exécuter opcode f (saut de scène)"

### Classes Trouvées dans europeo.exe
- `TVNIndexDependant` @ 0x004104ab
- `TVNVariable`, `TVNVariableArray`
- `TVNScene`, `TVNSceneParms`
- `TVNCommand`, `TVNProjectParms`

### Messages d'Erreur
- "Invalid index. There is no scene at %i." @ resources
- "Aucune scene %i n'existe." @ vnresmod.dll

## Hypothèses

### Interprétation des Données VND

Dans les dumps comme `couleurs1.vnd`, quand on voit:
- `54h` → Paramètre 54, puis opcode 'h' (Tooltip)
- `54f` → Paramètre 54, puis opcode 'f' (Saut scène 54)
- `13d` → Paramètre 13, puis opcode 'd' (Message fenêtre)

### Navigation Cross-Projet (runprj)
Pour `runprj ..\espa\espa.vnp 13d`:
1. Charge le projet `espa.vnp`
2. Paramètre 13 stocké
3. Opcode 'd' exécuté (message fenêtre)

### Navigation Interne (scene)
Pour `scene 5i`:
1. Paramètre 5 extrait
2. Opcode 'i' (case 9) → `sub_42703A` = chargement d'image

## Questions Résolues (Janvier 2026)

1. ✅ **Comment l'INDEX est-il calculé?**
   → `INDEX_ID` lu depuis le VND (offset 65), navigation `Ni` = `INDEX_ID + N`

2. ✅ **Quelle est la différence entre `h`, `f`, `i`, `l`?**
   → Ce sont des **opcodes différents** du dispatcher `sub_43177D`:
   - `f` (6) = `sub_4268F8` → Saut de scène
   - `h` (8) = `sub_426D33` → Tooltips/bulles d'aide
   - `i` (9) = `sub_42703A` → Chargement d'images
   - `l` (12) = `sub_427C42` → Musique MIDI

3. ✅ **Pourquoi certaines navigations n'ont pas de suffixe?**
   → Sans suffixe = le nombre seul sert de paramètre pour la commande courante (scene, runprj, etc.)

4. ✅ **Comment les "suffixes" sont-ils parsés?**
   → `sub_407FE5` utilise `atol()` qui extrait le nombre et s'arrête à la lettre.
   La lettre est ensuite lue comme **prochain opcode** par le parseur de flux.

   **⚠️ CORRECTION**: Les lettres ne sont PAS des modificateurs du nombre,
   mais des opcodes séparés qui s'exécutent après.

## Analyse du Pseudo Code (IDA Pro)

### Fonctions Clés Identifiées

| Fonction | Rôle |
|----------|------|
| `sub_41721D` | Charge un fichier VND complet, lit "VNFILE" signature |
| `sub_417031` | Charge un fichier INI de projet |
| `sub_40D6F4` | Lit une commande du stream (type + paramètre string) |
| `sub_407FE5` | Convertit string en nombre avec `atol()` |
| `sub_40B990` | Switch géant des types de commandes (case 6 = scene) |
| `sub_41526B` | Crée un objet TVNScene |
| `sub_410AF6` | Validation de scène (`*scene > 0`) |

### Structure des Commandes (commands.cpp)

Pour le type 6 (scene):
```c
case 6:  // Scene command
    scene_num = sub_407FE5(param_string, 0);  // atol()
    is_relative = (param_string[0] == '+' || param_string[0] == '-');
    // Structure: {vtable, scene_num, is_relative}
```

### Variables du Projet

Depuis l'INI (lu par `sub_417031`):
- `INDEX_ID` → offset 65 du projet = Index de départ
- `EXIT_ID` → offset 61 du projet = Scène de sortie
- `AREAS` → nombre de zones/scènes

### Logique de Navigation Probable

1. Si suffixe `i` (Index):
   - `scene_target = INDEX_ID + parsed_number`

2. Si suffixe `d` (Direct):
   - `scene_target = parsed_number` (ID absolu)

3. Si `+` ou `-`:
   - `scene_target = current_scene +/- parsed_number`

4. Sans suffixe:
   - Comportement par défaut (probablement direct)

### Structure VND (sub_41721D)

```
1. Signature "VNFILE" (6 bytes)
2. Version (word)
3. Project properties:
   - Title (string @ offset 49)
   - INDEX_ID (@ offset 65)
   - EXIT_ID (@ offset 61)
4. Scene count (word)
5. Pour chaque scène:
   - Création via sub_41526B (0x99 bytes each)
   - Ajout au tableau de scènes
```

## Découvertes Additionnelles (Janvier 2026)

### Opérateurs de Comparaison (sub_40A479)

La fonction `sub_40A479` gère les comparaisons dans les conditions `if`:

```c
switch (operator_code) {
    case 1: result = (a == b);  // ==
    case 2: result = (a != b);  // !=
    case 3: result = (a > b);   // >
    case 4: result = (a < b);   // <
    case 5: result = (a >= b);  // >=
    case 6: result = (a <= b);  // <=
}
```

Table des opérateurs string à `dword_43BA24`, initialisée avec `asc_43F8FD` ("=").

### Format des Conditions

Les conditions sont parsées par `sub_40A5CA` en format:
```
"variable opérateur valeur"
```
Exemple: `"score >= 10"`, `"jeu == 1"`

### Système de Variables Global

- `dword_44ECCE` = Tableau global des variables en mémoire
- `sub_406345` = Charge variables depuis fichier VNSAVFILE
- `sub_40650B` = Sauvegarde variables vers fichier VNSAVFILE

### Format Fichier Sauvegarde

```
VNSAVFILE (signature 9 bytes)
+ String: chemin projet
+ Word: scène courante
+ Word: nombre de variables
+ Pour chaque variable: nom (string) + valeur
+ État interface TWindow
```

### Timer Automatique

Format INI: `TIMER=delay,scene_target`
- Parsing: `sscanf(buffer, "%i,%i", &delay, &scene)`
- Condition: `scene > 0 && delay >= 0`
- Implémentation: `SetTimer(hwnd, 1, delay, NULL)`

### Curseurs

- `DEFCURSOR` dans [MAIN] définit le curseur par défaut
- Curseurs personnalisés chargés via `LoadCursorFromFileA`
- IDs système: 98, 99, 105, 1-4 (directionnels)

## Fonctions Techniques Utiles

### sub_41DB36 - Rendu Bitmap avec Masque

```c
// Line 16161 - Rendu avec masque de transparence
// Utilisé pour afficher des sprites avec transparence
char sub_41DB36(int a1, TDC *a2, int x, int y, int w, int h)
{
  TMemoryDC *memDC = new TMemoryDC(a2);
  // Double-blit avec ROP codes:
  // 0x8800C6 = SRCAND (masque)
  // 0xEE0086 = SRCPAINT (sprite)
  // 0xCC0020 = SRCCOPY (copie directe)
}
```

### sub_41CCDD - Chargement Palette

```c
// Line 15756 - Gestion des palettes VNPALETTE
// Utilisé pour les images 8-bit indexées
```

## Flux de Données Corrigé: Opcode Parser

```
┌─────────────────────────────────────────────────────────────┐
│  1. Flux VND brut: "54h" ou "16l"                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. sub_407FE5: atol("54h") → 54                           │
│     Le pointeur de lecture avance après le nombre          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Parseur lit le caractère suivant: 'h'                  │
│     Calcul index: 'h' - 'a' + 1 = 8                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. sub_43177D (Dispatcher) case 8:                        │
│     → sub_426D33(window, param=54) = Tooltips              │
└─────────────────────────────────────────────────────────────┘

Autres exemples:
  "54f" → case 6  → sub_4268F8 (saut scène 54)
  "16l" → case 12 → sub_427C42 (MIDI piste 16)
  "5i"  → case 9  → sub_42703A (image ID 5)
```

## Implémentation React (Corrigée)

```typescript
// Le parsing doit comprendre que les lettres sont des OPCODES séparés

interface VNDCommand {
  opcode: string;      // 'f', 'h', 'i', 'l', etc.
  parameter: number;   // Valeur numérique précédente
}

// Parser de flux VND
function parseVNDStream(stream: string): VNDCommand[] {
  const commands: VNDCommand[] = [];
  let i = 0;

  while (i < stream.length) {
    // Extraire le nombre
    let numStr = '';
    while (i < stream.length && /\d/.test(stream[i])) {
      numStr += stream[i++];
    }
    const param = numStr ? parseInt(numStr, 10) : 0;

    // Extraire l'opcode (lettre suivante)
    if (i < stream.length && /[a-z]/i.test(stream[i])) {
      commands.push({
        opcode: stream[i++],
        parameter: param
      });
    }
  }
  return commands;
}

// Dispatcher React
const OPCODE_HANDLERS: Record<string, (param: number) => void> = {
  'f': (scene) => navigateToScene(scene),     // Saut scène
  'h': (id) => showTooltip(id),               // Tooltip
  'i': (id) => loadImage(id),                 // Image
  'j': (id) => loadBitmap(id),                // Bitmap
  'k': (id) => playWav(id),                   // Audio WAV
  'l': (id) => playMidi(id),                  // MIDI
  'p': (ms) => sleep(ms),                     // Pause
  // etc.
};

function executeCommand(cmd: VNDCommand) {
  const handler = OPCODE_HANDLERS[cmd.opcode];
  if (handler) {
    handler(cmd.parameter);
  }
}
```

## Résumé Final (Corrigé)

| Question | Réponse Correcte |
|----------|------------------|
| Que sont les "suffixes" ? | Des **OPCODES** séparés, pas des modificateurs |
| Comment sont-ils parsés ? | `atol()` extrait le nombre, la lettre est le prochain opcode |
| Que fait `f` ? | Opcode 6 → `sub_4268F8` = Saut de scène |
| Que fait `h` ? | Opcode 8 → `sub_426D33` = Tooltips |
| Que fait `i` ? | Opcode 9 → `sub_42703A` = Chargement image |
| Que fait `l` ? | Opcode 12 → `sub_427C42` = Musique MIDI |
| Que fait `k` ? | Opcode 11 → `sub_427B56` = Audio WAV |

## Prochaines Étapes

1. ~~Analyser le code de `TVNIndexDependant` pour comprendre l'indexation~~
2. ~~Trouver les opérateurs de comparaison pour les conditions~~
3. ~~Comprendre le système d'opcodes TVNApplication~~
4. Implémenter le parseur VND→React basé sur le dispatcher d'opcodes
5. Tester les mappings avec le jeu original pour validation
