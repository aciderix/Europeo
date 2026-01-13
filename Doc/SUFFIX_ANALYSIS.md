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

### Suffixes Identifiés (COMPLET - Janvier 2026)

**Découverte clé**: Les suffixes sont des **opcodes de mise en scène** passés à la fonction de rendu `sub_434070`.
Le parsing utilise `atol()` via `sub_407FE5` qui s'arrête au premier caractère non-numérique.

| Suffixe | Fonction Pseudo-Code | Action du Moteur |
|---------|---------------------|------------------|
| `i` | `sub_4268F8` | **Immediate** - Saut immédiat, court-circuite les transitions |
| `d` | `sub_433236` | **Droite/Direct** - Direction droite du balayage |
| `f` | `sub_434070` + `sub_41CCDD` | **Fade** - Fondu via manipulation de palette |
| `l` | `sub_41DB36` (StretchBlt) | **Lent** - Transition lente, ajuste le pas du BitBlt |
| `j` | `sub_40B990` (Case 35) | **Jump/Join** - Interaction utilisateur, suspend les autres processus |
| `k` | `sub_4314E0` | **Keyboard** - Attente de validation (Entrée ou clic) |
| `e` | `sub_425165` | **Entrance** - Point d'entrée, exécute scripts de config |
| `h` | `sub_43177D` (Case 31) | **Horizontal** - Wipe horizontal ou activation timer |
| `g` | `sub_433236` | **Gauche** - Direction gauche du balayage |
| `+` / `-` | Navigation relative | Scene courante ± n |

**Mécanisme technique**:
```c
// sub_407FE5 - Parsing du numéro de scène
int scene_num = atol("16l");  // → 16 (atol s'arrête à 'l')
char suffix = remaining;       // → 'l'
// Le suffixe modifie le comportement de sub_434070 (rendu)
```

### Classes Trouvées dans europeo.exe
- `TVNIndexDependant` @ 0x004104ab
- `TVNVariable`, `TVNVariableArray`
- `TVNScene`, `TVNSceneParms`
- `TVNCommand`, `TVNProjectParms`

### Messages d'Erreur
- "Invalid index. There is no scene at %i." @ resources
- "Aucune scene %i n'existe." @ vnresmod.dll

## Hypothèses

### INDEX vs ID de Scène
- **Index (`i`)**: Position dans un tableau de scènes (0-based ou 1-based?)
- **Direct (`d`)**: ID unique de la scène dans le projet

### Navigation Cross-Projet
Les suffixes `d` sont systématiquement utilisés pour les références vers d'autres fichiers `.vnp`:
- `..\espa\espa.vnp 13d`
- `..\ecosse\ecosse.vnp 33d`

Cela suggère que `d` = "Direct scene ID" qui fonctionne entre projets.

### Navigation Interne
Les suffixes `i` sont utilisés pour la navigation interne dans le même projet:
- `home2.avi → 5i` (vers maison.bmp)
- `bankbis.avi → 3i` (vers banque.bmp)

## Questions Résolues (Janvier 2026)

1. ✅ **Comment l'INDEX est-il calculé?**
   → `INDEX_ID` lu depuis le VND (offset 65), navigation `Ni` = `INDEX_ID + N`

2. ✅ **Quelle est la différence entre `h`, `f`, `j`?**
   → Ce sont des **opcodes de présentation** pour le moteur de rendu:
   - `h` = Horizontal wipe / timer activation
   - `f` = Fade (fondu via palette)
   - `j` = Jump/Join (interaction utilisateur, suspend les processus)

3. ✅ **Pourquoi certaines navigations n'ont pas de suffixe?**
   → Sans suffixe = transition par défaut du moteur

4. ✅ **Comment les suffixes sont-ils parsés?**
   → `sub_407FE5` utilise `atol()` qui s'arrête au premier caractère non-numérique.
   Le suffixe est passé à `sub_434070` (fonction de rendu) pour modifier le comportement.

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

## Prochaines Étapes

1. ~~Analyser le code de `TVNIndexDependant` pour comprendre l'indexation~~
2. ~~Trouver les opérateurs de comparaison pour les conditions~~
3. Tracer l'exécution avec un débogueur pour voir la logique exacte
4. Comparer les mappings avec les résultats réels du jeu
5. Implémenter le parseur React basé sur ces découvertes
