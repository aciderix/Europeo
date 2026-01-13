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

### Suffixes Identifiés
| Suffixe | Signification Probable | Preuve |
|---------|------------------------|--------|
| `i` | **Index** - Navigation par INDEX | Classe `TVNIndexDependant` dans europeo.exe |
| `d` | **Direct** - Navigation par ID de scène | Utilisé pour projets externes (.vnp) |
| `j` | **Jump** - Saut spécial? | Utilisé avec `jeu = 1` conditions |
| `h` | Inconnu | Utilisé avec `score < 0` conditions |
| `f` | Inconnu | Utilisé avec `score < 0` conditions |

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

## Questions Ouvertes

1. Comment l'INDEX est-il calculé? (ordre de définition dans VND? ordre alphabétique? table explicite?)
2. Quelle est la différence entre `h`, `f`, `j`?
3. Pourquoi certaines navigations n'ont pas de suffixe?

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

## Prochaines Étapes

1. ~~Analyser le code de `TVNIndexDependant` pour comprendre l'indexation~~
2. Tracer l'exécution avec un débogueur pour voir la logique exacte
3. Comparer les mappings avec les résultats réels du jeu
4. Implémenter le parseur React basé sur ces découvertes
