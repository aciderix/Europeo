# Questions Ouvertes sur le Format VND

Document de recherche pour identifier et résoudre les zones d'ombre du format VND.

---

## 1. Navigation - Suffixes Mystérieux

### Q1.1: Suffixe `j` - Signification ?
**Contexte**: Observé avec condition `jeu = 1`
**Statut**: ⚠️ Hypothèse non confirmée
**Hypothèse**: Probablement "Jump" conditionnel ou lié au mode "jeu"

### Q1.2: Suffixe `h` - Signification ?
**Contexte**: Observé avec condition `score < 0`
**Statut**: ⚠️ Non résolu
**Hypothèse**: Peut-être "High score" ou navigation conditionnelle

### Q1.3: Suffixe `f` - Signification ?
**Contexte**: Observé avec condition `score < 0`
**Statut**: ⚠️ Non résolu
**Hypothèse**: Peut-être "Fail" ou "False" pour échec

### Q1.4: Comment INDEX est-il calculé ?
**Statut**: ✅ Partiellement résolu
**Réponse**: INDEX_ID est lu depuis le fichier VND (offset 65). La navigation `Ni` = `INDEX_ID + N`

### Q1.5: Navigation sans suffixe - Comportement ?
**Statut**: ✅ Résolu
**Réponse**: Sans suffixe = navigation directe (équivalent à `d`)

---

## 2. Hotspots

### Q2.1: HSVIDEOFLAGS - Quels flags existent ?
**Statut**: ✅ Partiellement résolu
**Réponse**:
- Lu comme entier (`TProfile::GetInt`)
- Format dans commande: `" %u %i %i %i %i"` = flags + rect(x,y,w,h)
- Probablement un bitmask, valeurs exactes non confirmées

### Q2.2: Structure binaire d'un hotspot ?
**Statut**: ✅ Partiellement résolu
**Réponse**: Clés INI par hotspot:
- `HOTSPOT_n` - coordonnées (rect)
- `HSCMD_n` - commandes
- `HSRGN_n` - région polygonale
- `HSCUR_n` - ID curseur
- `HSVIDEO_n` - chemin vidéo
- `HSVIDEOFLAGS_n` - flags vidéo (int)
- `HSVIDEORECT_n` - rect vidéo (x,y,w,h)

### Q2.3: HSRGN polygones - Limites ?
**Statut**: ⚠️ Non confirmé
**Réponse**: Format `npoints,x1,y1,x2,y2,...` - pas de limite trouvée dans le code

---

## 3. Interface

### Q3.1: TOOLBAR - Que représentent les 5 entiers ?
**Statut**: ✅ Résolu
**Réponse**:
```c
// sub_414D03
TOOLBAR=btn1,btn2,btn3,btn4,btn5
// Stockés dans a1[3] à a1[7]
// Si au moins un > 0, la toolbar est créée
```
Probablement des IDs de boutons ou états (visible/enabled)

### Q3.2: TXTHREFOFFSET - Fonctionnement ?
**Statut**: ✅ Résolu
**Réponse**:
```c
a1[20] = TProfile::GetInt("TXTHREFOFFSET", 0);
```
Offset ajouté aux numéros de liens HTML pour mapper vers des hotspots/commandes.
Ex: Si TXTHREFOFFSET=100 et lien href="#3", déclenche hotspot 103

### Q3.3: CAPS - Valeurs possibles ?
**Statut**: ⚠️ Partiellement résolu
**Réponse**: Lu avec `readWord()` si version >= 0x2000B
Stocké à offset 69 du projet. Bitmask de capacités, valeurs exactes inconnues.

---

## 4. Commandes

### Q4.1: if + commande - Chaînage ?
**Statut**: ✅ Résolu
**Réponse**: Format découvert (sub_40A5CA):
```
if condition then commande1; commande2 else commande3
```
- Recherche "then" et "else" dans la chaîne
- Condition parsée par sub_40A2FE → (variable, valeur, opérateur)
- Commandes "then" stockées dans a1[5..8]
- Commandes "else" stockées dans a1[9..12]

### Q4.2: msgbox - Format des paramètres ?
**Statut**: ✅ Résolu
**Réponse** (sub_40AEB4):
```
msgbox "texte" param1 param2 param3 param4 param5 "string2" param6
```
Structure:
- offset +4: string (texte principal)
- offset +8,12,16,20: 4 ints (type, style, etc.)
- offset +24: word
- offset +26: string secondaire
- offset +30: int

### Q4.3: font - Paramètres complets ?
**Statut**: ✅ Résolu
**Réponse** (sub_40B2B4):
```
font taille style #RRGGBB "nom_police"
```
Structure:
- a1[1]: taille (int)
- a1[2]: style (int, ex: bold=1, italic=2)
- a1[3]: couleur (TColor, format #RRGGBB)
- a1[4]: string nom de police

### Q4.4: playseq - Format de séquence ?
**Statut**: ⚠️ Non résolu
**Réponse**: Seule référence trouvée: `aSequencer = "sequencer"`
Probablement pour jouer des séquences d'actions/animations

### Q4.5: addbmp - Paramètres de positionnement ?
**Statut**: ✅ Résolu
**Réponse** (sub_40955C):
```
addbmp "chemin.bmp" id x y w h "nom_objet"
```
Structure:
- a1+8: string (chemin image)
- a1+1: string (nom objet)
- a1[2]: ID
- a1[3]: x
- a1[4]: y
- a1[5]: w
- a1[6]: h
- a1+7: string (autre)

### Q4.6: runprj - Passage de variables ?
**Statut**: ✅ Partiellement résolu
**Réponse** (sub_409E89):
```
runprj "chemin.vnp" arguments
```
- a1+1: string (chemin projet)
- a1+2: string (arguments)
Les variables ne semblent pas être transférées automatiquement.

### Q4.7: rundll - Format complet des arguments ?
**Statut**: ✅ Résolu
**Réponse**: Même structure que runprj (sub_409E89):
```
rundll "chemin.dll" arguments
```
La DLL doit exporter: VNSetDLLArguments, VNCreateDLLWindow, VNDestroyDLLWindow

---

## 5. Médias

### Q5.1: Formats vidéo supportés ?
**Statut**: ⚠️ Partiellement résolu
**Réponse**: AVI principalement (extension .avi dans le code)
Utilise probablement Video for Windows (VFW) - codecs système

### Q5.2: playcda - CD Audio ?
**Statut**: ⚠️ Non résolu
**Réponse**: Pas de référence MCI trouvée. Peut-être désactivé ou non implémenté dans cette version.

---

## 6. Système

### Q6.1: Versions VND - Fonctionnalités ?
**Statut**: ✅ Résolu
**Réponse** (sub_41721D):
| Version | Fonctionnalité débloquée |
|---------|--------------------------|
| > 0 | Format binaire VND |
| >= 0x2000A | NAME, Variables initiales |
| >= 0x2000B | Limites/options, CAPS |
| >= 0x2000D | String supplémentaire |

### Q6.2: Événements - Déclenchement ?
**Statut**: ⚠️ Partiellement résolu
**Réponse**: Seule référence trouvée: `aEvOnfocus = "EV_ONFOCUS"`
Autres événements (ONCLICK, ONINIT, AFTERINIT) mentionnés mais non trouvés dans le code.

### Q6.3: Variables initiales dans VND ?
**Statut**: ✅ Résolu
**Réponse**: Oui, si version >= 0x2000A:
```c
if (version >= 0x2000A)
    read_variables(&project[94]);
```

---

## Résumé

| Catégorie | Résolues | Partielles | Non résolues |
|-----------|----------|------------|--------------|
| Navigation | 2 | 0 | 3 |
| Hotspots | 2 | 1 | 0 |
| Interface | 2 | 1 | 0 |
| Commandes | 5 | 1 | 1 |
| Médias | 0 | 1 | 1 |
| Système | 2 | 1 | 0 |
| **Total** | **13** | **5** | **5** |

### Questions toujours ouvertes:
1. Suffixes `j`, `h`, `f` - signification exacte
2. playseq - format de séquence
3. playcda - CD Audio
4. CAPS - valeurs du bitmask
5. Événements ONCLICK, ONINIT, AFTERINIT

