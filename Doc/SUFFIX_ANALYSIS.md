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

## Prochaines Étapes

1. Analyser le code de `TVNIndexDependant` pour comprendre l'indexation
2. Tracer l'exécution avec un débogueur pour voir la logique exacte
3. Comparer les mappings avec les résultats réels du jeu
