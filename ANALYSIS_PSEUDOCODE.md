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

### 5. Auto-Génération Commande Type 6 (HOTSPOT_X)

**hotspot.cpp lignes 377-459**: Si le premier token de `HOTSPOT_X` > 0, le moteur **génère automatiquement** une commande `subtype=6`!

```cpp
if (v33 > 0) {  // v33 = premier token HOTSPOT_X
    sprintf(param, "%u", v33);
    CreateCommand(6, param);  // GOTO SCENE auto!
}
```

**Exemple INI**:
```ini
HOTSPOT_0 = 15, 5, 4, 100,100, 200,100, 200,200, 100,200
```
→ Génère automatiquement: `Command(subtype=6, param="15")` = **goto scene 15**!

### 6. Double Format de Scènes (scene.cpp)

Le moteur supporte **2 formats**:
- **Format INI** (texte) → parser `sub_417031`
- **Format VND binaire** → parser `sub_41721D`

Router (lignes 36-48):
```cpp
if (extension == "Ini")
    sub_417031(...);  // Parser INI
else
    sub_41721D(...);  // Parser binaire VND
```

---

## 🎯 Format Complet HOTSPOT_X (INI)

### Clés INI Parsées:

| Clé | Format | Description |
|-----|--------|-------------|
| `HSCUR_X` | `cursorId` | ID curseur (+100 offset) |
| `HSRGN_X` | `count,x1,y1,...,xN,yN` | Géométrie polygonale |
| `HSCMD_X` | Multiple lignes | Commandes hotspot |
| `HOTSPOT_X` | `id,cursor,count,x1,y1,...` | **Data principale + géométrie alt** |
| `HSVIDEO_X` | `filename.avi` | Fichier vidéo |
| `HSVIDEOFLAGS_X` | `flags` | Flags vidéo |
| `HSVIDEORECT_X` | `x,y,w,h` | Rectangle vidéo |

### HOTSPOT_X - Format Détaillé:

```
HOTSPOT_X = token1, token2, token3, [x1,y1, x2,y2, ..., xN,yN]
```

**Tokens**:
1. **token1 (id)**: Si > 0 → **génère auto Command(6, token1)**
2. **token2 (cursorId)**: Override cursorId (avec +100)
3. **token3 (pointCount)**: Nombre de points géométrie
4. **x1,y1, ... xN,yN**: Points (si pointCount > 1)

**Priorités**:
- Si `HOTSPOT_X` a géométrie (token3 > 1) → **écrase** `HSRGN_X`
- Si `HOTSPOT_X` token2 présent → **écrase** `HSCUR_X`

### Structure Mémoire Hotspot (offsets):

```c
struct Hotspot {
    void* vtable;           // +0
    // ...
    int cursorId;           // +45  (avec +100 offset)
    // ...
    int pointCount;         // +53
    Point* points;          // +57  (tableau dynamique)
    // ...
    CommandList commands;   // +2 (offset a1+2)
};
```

---

## 📝 Prochaines Étapes

1. ✅ Mapper tous les subtypes de commandes
2. ⬜ Analyser `sub_40A5CA` (parser logic if-then)
3. ✅ Documenter format complet HOTSPOT_X
4. ✅ Vérifier si cursorId +100 s'applique partout
5. ⬜ Explorer pseudo code complet pour EXIT_ID
6. ⬜ Analyser `sub_41721D` (parser binaire VND)

---

## 🔬 Parser Binaire VND (sub_41721D)

### Fonction Principale: sub_41721D

**Source**: `_common_functions.cpp.txt` lignes 9884-10023

**Signature**:
```cpp
int __cdecl sub_41721D(_DWORD *a1, const char *arglist, int a3, TGauge *a4)
```

**Paramètres**:
- `a1`: Pointeur vers structure Scene
- `arglist`: Chemin du fichier .vnd
- `a3`: Structure de configuration/version
- `a4`: Barre de progression (optionnel)

### Séquence de Parsing VND Binaire

```cpp
// 1. Ouverture fichier (lignes 9914-9936)
fpbase::open(&v18, arglist, 129, filebuf::openprot);
if ((v18[2] & 0x86) != 0)  // Erreur d'ouverture
    return 0;

// 2. Validation Magic String (lignes 9939-9944)
operator>>(&v21, v17);  // Lire string
if (string::compare(v17, "VnFile") != 0)  // Doit être "VnFile"
    return 0;

// 3. Initialisation scène (ligne 9946)
sub_416FCD((int)a1);

// 4. Lecture config (ligne 9947)
sub_4053B3((int)&v21, (void ***)a3);

// 5. Version par défaut (lignes 9948-9949)
if (!*(_DWORD *)(a3 + 4))
    *(_DWORD *)(a3 + 4) = 0x20000;

// 6. Lecture nombre de hotspots (ligne 9950)
Word = ipstream::readWord(&v21);  // Word = nombre de hotspots!

if (Word > 0) {
    // 7. Lecture données scène (lignes 9953-9966)
    operator>>(&v21, (char *)a1 + 49);  // String à offset +49

    if (*(_DWORD *)(a3 + 4) >= 0x2000D)
        operator>>(&v21, (char *)a1 + 53);  // String à offset +53

    sub_416781((int)a1 + 29, (int)&v21, a3);  // Lire file table

    if (*(_DWORD *)(a3 + 4) >= 0x2000B)
        // Lire structure à offset +73

    if (*(_DWORD *)(a3 + 4) >= 0x2000B)
        *(_DWORD *)((char *)a1 + 69) = ipstream::readWord(&v21);

    *(_DWORD *)((char *)a1 + 61) = ipstream::readWord(&v21);  // EXIT_ID!
    *(_DWORD *)((char *)a1 + 65) = ipstream::readWord(&v21);  // INDEX_ID

    if (*(_DWORD *)(a3 + 4) >= 0x2000A)
        operator>>(&v21, (char *)a1 + 57);  // String à offset +57

    if (*(_DWORD *)(a3 + 4) >= 0x2000A)
        sub_4066A1((_DWORD *)((char *)a1 + 94), &v21, a3);

    // 8. Expansion tableau (lignes 9968-9981)
    v13 = Word + 1;
    sub_406954((int)(a1 + 1), ..., 0);  // Allouer Word+1 slots

    // 9. Lecture hotspots (lignes 9984-9999)
    for (i = 0; i < Word; ++i) {
        v15 = operator new(0x99u);  // 153 bytes par hotspot
        if (v15) {
            sub_41526B(v15, (int)&v21, a3);  // Parser hotspot
            v7 = (int)v15;
        }
        sub_426399((int)(a1 + 1), v7);  // Ajouter à collection

        if (a4)
            TGauge::StepIt(a4);  // MAJ progress bar
    }
}

// 10. Fermeture et retour (lignes 10001-10009)
fpbase::close(&v18);
return 1;  // Succès
```

### Structure Scène (offsets découverts)

```c
struct Scene {
    void* vtable;               // +0
    void* unknown1;             // +4
    // ...
    void* fileTablePtr;         // +29 (file table structure)
    string unknown_str1;        // +49
    string unknown_str2;        // +53 (version >= 0x2000D)
    string unknown_str3;        // +57 (version >= 0x2000A)
    int EXIT_ID;                // +61 ← EXIT_ID stocké ici!
    int INDEX_ID;               // +65
    int unknown_word;           // +69 (version >= 0x2000B)
    // ... +73, +94
};
```

**EXIT_ID trouvé**: Stocké à l'offset **+61** de la structure Scene, lu depuis le fichier VND binaire!

### Lecture File Table: sub_416781

**Source**: lignes 9676-9695

```cpp
void __cdecl sub_416781(int a1, int a2, int a3)
{
    if (*(_DWORD *)(a3 + 4) >= 0x2000D) {
        string::string(&v6);

        // Lire 3 strings
        v3 = operator>>(a2, &v6);      // String cryptée
        v4 = operator>>(v3, a1 + 8);   // String offset +8
        operator>>(v4, a1 + 12);       // String offset +12

        // Décrypter avec "Password" key
        string::string(&v5, "Password");
        sub_405557((int)&v5, &v6, (string *)(a1 + 4));  // Décrypter → offset +4

        string::~string(&v5);
        string::~string(&v6);
    }
}
```

**Format File Table**:
- Version >= 0x2000D
- 1 string cryptée (décryptée avec clé "Password" → offset +4)
- 2 strings en clair (offsets +8, +12)

### Lecture Hotspot: sub_41526B + sub_4161FA

**sub_41526B** (constructeur, lignes 8971-9012):
```cpp
_DWORD *__cdecl sub_41526B(_DWORD *a1, int a2, int a3)
{
    // Initialiser structure hotspot (153 bytes = 0x99)
    *a1 = &off_442DA4;
    string::string(a1 + 2);
    sub_414A70(a1);

    // Initialiser 6 strings
    string::string(a1 + 8);
    string::string(a1 + 9);
    string::string(a1 + 10);
    string::string(a1 + 11);
    string::string(a1 + 12);
    string::string(a1 + 13);

    a1[26] = 1;

    // Allouer tableau
    v3 = operator new[](4u);
    *(_DWORD *)(a1 + 113) = _vector_new_ldtc_(v3, 4u, 1u, 1u, ...);
    *(_DWORD *)(a1 + 117) = 1;

    // Initialiser autres offsets
    *(_DWORD *)(a1 + 121) = 0;
    *(_DWORD *)(a1 + 125) = 2;
    *(_DWORD *)(a1 + 129) = 2;

    sub_415560(a1);  // Init valeurs par défaut

    // Appeler lecteur binaire (polymorphisme)
    (*(void (__cdecl **)(_DWORD *, int, int))(*a1 + 4))(a1, a2, a3);

    return a1;
}
```

**sub_4161FA** (lecteur binaire hotspot, lignes 9506-9607):
```cpp
int __cdecl sub_4161FA(_DWORD *a1, ipstream *a2, int a3)
{
    sub_4159C4(a1);  // Clear

    if (*(_DWORD *)(a3 + 4) == 0x20000) {
        // Format ancien (version 0x20000)
        (*(void (__cdecl **)(_DWORD *, ipstream *))(*a1 + 16))(a1, a2);
    }
    else if (*(_DWORD *)(a3 + 4) >= 0x2000A) {
        // Format moderne (version >= 0x2000A)

        // 1. Lire base hotspot
        sub_414CA1(a1, (int)a2);

        // 2. Lire 6 strings + 6 words
        v3 = operator>>(a2, a1 + 9);
        v9 = operator>>(v3, a1 + 8);
        a1[21] = ipstream::readWord(v9);

        v10 = operator>>(v9, a1 + 10);
        a1[22] = ipstream::readWord(v10);

        v11 = operator>>(v10, a1 + 11);
        a1[23] = ipstream::readWord(v11);

        v12 = operator>>(v11, a1 + 12);
        a1[24] = ipstream::readWord(v12);

        v13 = operator>>(v12, a1 + 13);
        a1[25] = ipstream::readWord(v13);

        v14 = operator>>(v13, a1 + 16);
        a1[20] = ipstream::readWord(v14);

        // 3. Bloc conditionnel 1 (lignes 9545-9581)
        if (ipstream::readWord32(a2)) {
            v17 = operator new(0x29u);  // 41 bytes
            // ... init structure ...
            (*(void (__cdecl **)(_DWORD *, ipstream *, int))(*v17 + 33 + 16))(v17, a2, a3);
            *(_DWORD *)(a1 + 145) = v17;  // Stocker à offset +145
        }

        // 4. Bloc conditionnel 2 (lignes 9582-9604)
        Word = ipstream::readWord(a2);
        if (Word) {
            v15 = operator new(0x20u);  // 32 bytes
            // ... init structure ...
            (*(void (__cdecl **)(_DWORD *, ipstream *, int))(*v15 + 8))(v15, a2, a3);
            *(_DWORD *)(a1 + 149) = v15;  // Stocker à offset +149

            if (Word < 0)
                *(_DWORD *)(*v15 + 8) = -Word;
        }
    }

    // 5. Lire commandes (ligne 9606)
    return (*(int (__cdecl **)(_DWORD *, ipstream *, int))(*(_DWORD *)(a1 + 141) + 20))(a1 + 26, a2, a3);
}
```

**sub_414CA1** (lecteur base hotspot, lignes 8710-8722):
```cpp
int __cdecl sub_414CA1(_DWORD *a1, int a2)
{
    v2 = operator>>(a2, a1 + 2);         // String à offset +2
    ipstream::readBytes(v2, a1 + 4, 4u); // 4 bytes binaires à offset +4
    a1[5] = ipstream::readWord(v2);      // Word à offset +5
    a1[3] = ipstream::readWord(v2);      // Word à offset +3
    a1[1] = ipstream::readWord(v2);      // Word à offset +1
    return result;
}
```

### Structure Hotspot Binaire (153 bytes = 0x99)

```c
struct Hotspot {
    void* vtable;               // +0
    int word1;                  // +1  (readWord)
    string str1;                // +2  (operator>>)
    int word2;                  // +3  (readWord)
    byte data[4];               // +4  (readBytes 4)
    int word3;                  // +5  (readWord)
    // ... +6, +7
    string str2;                // +8  (operator>>)
    string str3;                // +9  (operator>>)
    string str4;                // +10 (operator>>)
    string str5;                // +11 (operator>>)
    string str6;                // +12 (operator>>)
    string str7;                // +13 (operator>>)
    // ... +16
    int word4;                  // +20 (readWord)
    int word5;                  // +21 (readWord)
    int word6;                  // +22 (readWord)
    int word7;                  // +23 (readWord)
    int word8;                  // +24 (readWord)
    int word9;                  // +25 (readWord)
    int flag;                   // +26
    CommandList commands;       // offset +26 (variable)
    // ... +113, +117, +121, +125, +129
    void* conditional1;         // +145 (si readWord32 != 0)
    void* conditional2;         // +149 (si readWord != 0)
};
```

### Format Binaire VND Complet

```
┌─────────────────────────────────────┐
│ Magic String: "VnFile"              │ operator>> (std::string)
├─────────────────────────────────────┤
│ Config (sub_4053B3)                 │ varies
├─────────────────────────────────────┤
│ Hotspot Count (Word)                │ 2 bytes (little endian)
├─────────────────────────────────────┤
│ Scene String 1                      │ operator>> (offset +49)
├─────────────────────────────────────┤
│ Scene String 2 (v >= 0x2000D)       │ operator>> (offset +53)
├─────────────────────────────────────┤
│ File Table (sub_416781)             │
│   - Encrypted string                │ operator>> + decrypt
│   - String 2                        │ operator>>
│   - String 3                        │ operator>>
├─────────────────────────────────────┤
│ Unknown Word (v >= 0x2000B)         │ readWord (offset +69)
├─────────────────────────────────────┤
│ EXIT_ID                             │ readWord (offset +61) ← IMPORTANT!
├─────────────────────────────────────┤
│ INDEX_ID                            │ readWord (offset +65)
├─────────────────────────────────────┤
│ Scene String 3 (v >= 0x2000A)       │ operator>> (offset +57)
├─────────────────────────────────────┤
│ Unknown Data (v >= 0x2000A)         │ sub_4066A1 (offset +94)
├─────────────────────────────────────┤
│ ┌─ HOTSPOT 0 ─────────────────────┐ │
│ │ String (offset +2)               │ │ operator>>
│ │ 4 bytes binary (offset +4)       │ │ readBytes
│ │ Word (offset +5)                 │ │ readWord
│ │ Word (offset +3)                 │ │ readWord
│ │ Word (offset +1)                 │ │ readWord
│ │ 6 × (String + Word)              │ │ offsets +8..+13, +21..+25
│ │ Word at offset +20               │ │ readWord
│ │ Optional: Word32 conditional     │ │ if != 0: read struct (41 bytes)
│ │ Optional: Word conditional       │ │ if != 0: read struct (32 bytes)
│ │ Commands (offset +26)            │ │ variable length
│ └─────────────────────────────────┘ │
│ ┌─ HOTSPOT 1 ─────────────────────┐ │
│ │ ... (même format) ...            │ │
│ └─────────────────────────────────┘ │
│ ...                                 │
│ ┌─ HOTSPOT N-1 ───────────────────┐ │
│ │ ... (même format) ...            │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Codes Version

| Code Hex | Code Dec | Fonctionnalités |
|----------|----------|-----------------|
| 0x20000  | 131072   | Format ancien (hotspot reader différent) |
| 0x2000A  | 131082   | + Scene string 3, sub_4066A1, hotspot format moderne |
| 0x2000B  | 131083   | + Unknown word offset +69, structure offset +73 |
| 0x2000D  | 131085   | + Scene string 2, file table cryptée |

### Découvertes Importantes

1. **EXIT_ID** est stocké dans le fichier VND à l'offset +61 de la structure Scene (ligne 9961)
2. **Magic String** = `"VnFile"` (ligne 9941)
3. **Hotspot Count** lu en premier (ligne 9950) pour allouer les structures
4. **File Table** peut être cryptée (clé "Password") si version >= 0x2000D
5. **Hotspot size** = 153 bytes (0x99) alloués pour chaque hotspot
6. **Versions multiples** supportées avec lecture conditionnelle
7. **Structures conditionnelles** dans hotspots (offsets +145 et +149) selon flags

---

**Généré**: 2026-01-23
**Mis à jour**: 2026-01-23 (ajout parser binaire VND complet)
**Source**: Infos/Code_Reconstruit_V2/{commands,hotspot,scene,_common_functions}.cpp.txt
