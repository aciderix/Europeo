# Analyse Pseudo-Code VnStudio

Analyse des fichiers de pseudo-code décompilé du moteur VnStudio.

---

## 📁 Fichiers Analysés

| Fichier | Lignes | Contenu |
|---------|--------|---------|
| `commands.cpp.txt` | 910 | Dispatcher commandes hotspot (49 types) |
| `hotspot.cpp.txt` | 472 | Parsing hotspots depuis fichiers .ini |
| `scene.cpp.txt` | 52 | Routing vers parsers de scène |

---

## 🎮 Structure Hotspot (hotspot.cpp.txt)

### Clés INI parsées (format TProfile):

```cpp
sprintf(buffer, "HSCUR_%u", hotspot_id);   // Cursor ID
sprintf(buffer, "HSRGN_%u", hotspot_id);   // Région (géométrie polygonale)
sprintf(buffer, "HSCMD_%u", hotspot_id);   // Commandes
sprintf(buffer, "HOTSPOT_%u", hotspot_id); // Data générale hotspot
sprintf(buffer, "HSVIDEO_%u", hotspot_id); // Vidéo AVI
```

### HSCUR - Cursor ID (lignes 97-103):

```cpp
TProfile::GetString(profile, buffer, str, 256, "");
cursorId = atol(str);

if (cursorId >= 0)
    cursorId += 100;  // Offset de +100 pour cursorId positifs!
else
    cursorId = 100;   // Défaut = 100
```

**Découverte**: Les cursorId dans le binaire sont **+100** par rapport aux IDs logiques!

### HSRGN - Géométrie Polygonale (lignes 104-193):

```cpp
TProfile::GetString(profile, "HSRGN_X", str, 256, "");

if (str[0]) {
    ptr = strtok(str, ",");  // Premier token = pointCount
    pointCount = atol(ptr);

    if (pointCount > 1) {
        // Allouer tableau de points
        points = new Point[pointCount];

        for (i = 0; i < pointCount; i++) {
            x_str = strtok(NULL, ",");
            x = atol(x_str);

            y_str = strtok(NULL, ",");
            y = atol(y_str);

            points[i].x = x;
            points[i].y = y;
        }
    }
}
```

**Format HSRGN**: `pointCount, x1,y1, x2,y2, ..., xN,yN`

### HOTSPOT - Data Principale (lignes 197-312):

```cpp
TProfile::GetString(profile, "HOTSPOT_X", str, 256, "");

if (str[0]) {
    token1 = strtok(str, ",");  // ID inconnu
    id_value = atol(token1);

    token2 = strtok(NULL, ",");  // Cursor override?
    cursorId = atol(token2) + 100;

    token3 = strtok(NULL, ",");  // Point count (géométrie alternative)
    altPointCount = atol(token3);

    if (altPointCount > 1) {
        // Parser géométrie alternative
        // ...
    }
}
```

**Format HOTSPOT**: `id, cursorId, pointCount, x1,y1, ..., xN,yN`

---

## ⚙️ Types de Commandes (commands.cpp.txt)

**Dispatcher principal** (ligne 152): `switch (*(_DWORD *)(a2 + 8))`
→ Le **subtype** de la commande est à l'offset +8 dans la structure

### Table Complète des Commandes (49 types):

| Subtype (Hex) | Subtype (Dec) | Ligne | Description |
|---------------|---------------|-------|-------------|
| 0x00 | 0 | 154 | Quit / Exit |
| 0x01 | 1 | 157 | Menu action (0x4E29) |
| 0x02 | 2 | 160 | Action (0x9D) |
| 0x03 | 3 | 163 | PostMessage (0x9F) |
| 0x04 | 4 | 181 | PostMessage (0xA0) |
| 0x05 | 5 | 199 | HandleMessage (0x9C) |
| **0x06** | **6** | **202** | **GOTO SCENE / INC_VAR / DEC_VAR** |
| 0x07 | 7 | 256 | Similaire à 6 (positif seulement) |
| 0x08 | 8 | 266 | String processing |
| 0x09 | 9 | 297 | String operation |
| 0x0A | 10 | 316 | String operation |
| 0x0B | 11 | 339 | String operation |
| 0x0C | 12 | 358 | ? |
| 0x0D | 13 | 375 | PlayHTML ? |
| 0x0E | 14 | 394 | ? |
| 0x0F | 15 | 395 | ? |
| 0x10 | 16 | 396 | ? |
| 0x11 | 17 | 412 | ? |
| 0x12 | 18 | 267 | String (same as 8) |
| 0x13 | 19 | 431 | ? |
| 0x14 | 20 | 438 | ? |
| **0x15** | **21** | **463** | **LOGIC / IF-THEN** |
| 0x16 | 22 | 488 | Logic variant |
| 0x17 | 23 | 503 | Logic variant |
| 0x18 | 24 | 522 | Logic variant |
| 0x19 | 25 | 541 | ? |
| 0x1A | 26 | 545 | ? |
| **0x1B** | **27** | **571** | **ADDBMP** |
| 0x1C | 28 | 598 | ? |
| 0x1D | 29 | 599 | ? |
| 0x1E | 30 | 600 | ? |
| 0x1F | 31 | 633 | ? |
| 0x20 | 32 | 673 | ? |
| **0x21** | **33** | **680** | **RUNPRJ** |
| 0x22 | 34 | 699 | ? |
| 0x23 | 35 | 729 | ? |
| 0x24 | 36 | 674 | ? |
| 0x25 | 37 | 675 | ? |
| **0x26** | **38** | **733** | **PLAYTEXT** |
| **0x27** | **39** | **750** | **FONT** |
| 0x28 | 40 | 765 | ? |
| 0x29 | 41 | 767 | ? |
| 0x2A | 42 | 601 | ? |
| 0x2B | 43 | 602 | ? |
| 0x2C | 44 | 603 | ? |
| 0x2D | 45 | 788 | ? |
| 0x2E | 46 | 840 | ? |
| 0x2F | 47 | 676 | ? |
| 0x30 | 48 | 677 | ? |

---

## 🔍 Analyse Détaillée Commandes Clés

### case 6 (0x06): GOTO SCENE / INC_VAR / DEC_VAR

**Code** (lignes 202-254):

```cpp
case 6:
    if (param_string_length > 0) {
        // Créer objet de type numeric
        v122 = new(9);

        // Parser la string comme int
        v3 = sub_407FE5(param_string, 0);  // atoi
        v122[4] = v3;  // Stocker la valeur

        // Vérifier le premier caractère
        first_char = param_string[0];

        is_relative = false;
        if (first_char == '+' || first_char == '-')  // 0x2B ou 0x2D
            is_relative = true;

        v122[8] = is_relative;  // Flag relatif/absolu

        // Envoyer message au moteur
        if (validate(v122)) {
            PostMessageA(window, MSG_CUSTOM, cmd_subtype, v122);
        }
    }
    break;
```

**Fonctionnement**:
- Parse le paramètre comme **entier**
- Vérifie si le param commence par `+` ou `-`
  - **OUI** → mode relatif (inc/dec var ou offset scène)
  - **NON** → mode absolu (goto scene X)
- Exemple params:
  - `"3"` → goto scène 3
  - `"+1"` → inc_var ou scène suivante
  - `"-5"` → dec_var ou scène -5

### case 0x15 (21 decimal): LOGIC / IF-THEN

**Code** (lignes 463-486):

```cpp
case 0x15:  // 21 decimal
    if (param_string_length > 0) {
        // Parser l'expression logique
        sub_40A5CA(logic_struct, param_string);

        // Évaluer la condition
        if (logic_struct[4] && evaluate_condition(logic_struct)) {
            // Exécuter l'action
            TWindow::HandleMessage(window, MSG_CUSTOM, cmd_subtype, logic_struct);
        }
    }
    break;
```

**Fonctionnement**:
- Parse une expression de type: `VAR OP VALUE then ACTION`
- Exemple: `"score < 0 then runprj ..\couleurs1\couleurs1.vnp 54"`
- `sub_40A5CA` = parser logique complexe
- Évalue la condition puis exécute l'action si vraie

---

## 📊 Structure Commande en Mémoire

D'après l'analyse du switch:

```c
struct Command {
    void* vtable;           // +0  (polymorphisme)
    void* unknown;          // +4
    int   subtype;          // +8  ← Utilisé dans le switch!
    string param;           // +12 (std::string)
};
```

**Offset +8 = subtype de la commande** (case du switch)

---

## 🎯 Mapping Commandes VND ↔ Pseudo-Code

| VND Subtype | Nom Fonctionnel | Case | Description |
|-------------|-----------------|------|-------------|
| 0 | quit | 0x00 | Quitter / Exit |
| 3 | ? | 0x03 | PostMessage |
| 6 | scene / inc_var / dec_var | **0x06** | Navigation scène |
| 21 | if_then | **0x15** | Logic conditionnelle |
| 27 | addbmp | **0x1B** | Afficher image BMP |
| 38 | playtext | **0x26** | Afficher texte |
| 39 | font | **0x27** | Définir police |

---

## 🚨 Découvertes Importantes

### 1. CursorId Offset

**Tous les cursorId ont +100 d'offset!**

```cpp
if (cursorId >= 0)
    cursorId += 100;
```

- VND binaire: cursorId = **105**
- Valeur logique: cursorId = **5**

### 2. Format HSRGN (Géométrie)

```
HSRGN_X = pointCount, x1,y1, x2,y2, ..., xN,yN
```

Séparateur: **virgule** (`,`)

### 3. Command Subtype

Le **switch dispatcher** utilise l'offset **+8** de la structure Command pour router vers le bon handler.

### 4. Goto Scene vs Inc/Dec Var

**Même subtype (6)**, différenciation par le préfixe:
- `"3"` → goto scene 3
- `"+1"` → relative (+1)
- `"-5"` → relative (-5)

---

## 📝 Prochaines Étapes

1. ✅ Mapper tous les subtypes de commandes
2. ⬜ Analyser `sub_40A5CA` (parser logic)
3. ⬜ Documenter format complet HOTSPOT_X
4. ⬜ Vérifier si cursorId +100 s'applique partout
5. ⬜ Explorer pseudo code complet pour EXIT_ID

---

**Génér

é**: 2026-01-23
**Source**: Infos/Code_Reconstruit_V2/{commands,hotspot,scene}.cpp.txt
