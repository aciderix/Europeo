# Analyse Détaillée du Code de Chargement VND

## Introduction

Ce document fournit une analyse complète du code assembleur des fonctions critiques qui chargent et parsent les fichiers VND.

## 1. TEventHandler::Dispatch - Routage d'Événements

**Adresse**: `0x0041A32B` (owl52t.dll)  
**Taille**: 15 instructions  
**Type d'appel**: Dispatch indirect via vtable

###  Code Assembleur Annoté

```asm
0x0041A32B:  push ebp                     ; Prologue de fonction
0x0041A32C:  mov ebp, esp                 ; Setup stack frame
0x0041A32E:  mov eax, [ebp+0xC]           ; EAX = TEventInfo* (2ème argument)
0x0041A331:  push [ebp+0x14]              ; Param 3: LPARAM
0x0041A334:  push [ebp+0x10]              ; Param 2: WPARAM
0x0041A337:  mov edx, [eax+0xC]           ; EDX = eventInfo->field3
0x0041A33A:  push [edx+0x14]              ; Param 1: eventInfo->field3->field5
0x0041A33D:  push [edx+0x10]              ; Param 0: eventInfo->field3->field4
0x0041A340:  push [edx+0xC]               ; Push eventInfo->field3->field3
0x0041A343:  push [eax+8]                 ; Push eventInfo->field2
0x0041A346:  mov eax, [eax+0xC]           ; EAX = eventInfo->field3
0x0041A349:  call [eax+8]                 ; CALL vtable[2] - Dispatch indirect!
0x0041A34C:  add esp, 0x18                ; Nettoie 6 params (6×4 = 24 = 0x18)
0x0041A34F:  pop ebp                      ; Epilogue
0x0041A350:  ret                          ; Retour
```

### Analyse

**Fonction**: Cette fonction fait partie du mécanisme de **dispatch polymorphique** C++.

**Mécanisme**:
1. Reçoit un objet `TEventInfo` avec information sur l'événement
2. Extrait plusieurs champs de la structure
3. **Appel indirect via vtable** à l'offset +8: `call [eax+8]`
   - Ceci permet le dispatch polymorphique vers la bonne fonction handler selon le type d'événement
4. Le handler appelé reçoit 6 paramètres extraits de `TEventInfo`

**Importance pour VND**: Quand un fichier VND est ouvert ou qu'une commande script est exécutée, c'est cette fonction qui route l'événement vers le bon handler (ex: `TFileDocument::Open`, `addbmp handler`, etc.)

---

## 2. ipstream::readWord32 - Lecture d'Entier 32-bit

**Adresse**: `0x00403C74` (bds52t.dll)  
**Taille**: 28 instructions  
**Appels**: `0x0040CBF2` (fonction bas-niveau de lecture)

### Code Assembleur Annoté

```asm
0x00403C74:  push ebp                     ; Prologue
0x00403C75:  mov ebp, esp
0x00403C77:  push ecx                     ; Espace local (4 bytes)
0x00403C78:  push ebx                     ; Sauvegarde EBX
0x00403C79:  mov ebx, [ebp+8]             ; EBX = this (ipstream*)

; VÉRIFICATION D'ERREUR
0x00403C7C:  mov eax, [ebx]               ; EAX = *this (vtable ou stream structure)
0x00403C7E:  cmp dword ptr [eax+8], 0     ; Vérifie error flag au offset +8
0x00403C82:  je 0x403C88                  ; Si pas d'erreur, continue
0x00403C84:  xor eax, eax                 ; Sinon, retourne 0
0x00403C86:  jmp 0x403CB2                 ; Sortie rapide

; LECTURE DE 4 BYTES
0x00403C88:  push 4                       ; Param 3: Nombre de bytes = 4
0x00403C8A:  lea edx, [ebp-4]             ; EDX = &buffer_local
0x00403C8D:  push edx                     ; Param 2: Adresse destination
0x00403C8E:  push [eax+4]                 ; Param 1: File handle (stream->fd)
0x00403C91:  call 0x40CBF2                ; APPEL fonction de lecture bas-niveau
                                          ; Probablement: fread(fd, buffer, 4)
0x00403C96:  add esp, 0xC                 ; Nettoie 3 params

; VÉRIFICATION DU RÉSULTAT
0x00403C99:  cmp eax, 4                   ; Vérifie si 4 bytes lus
0x00403C9C:  je 0x403CAF                  ; Si OK, retourne la valeur

; GESTION D'ERREUR DE LECTURE
0x00403C9E:  mov eax, [ebx]               ; Récupère stream structure
0x00403CA0:  mov edx, [eax+8]             ; EDX = error flags
0x00403CA3:  and edx, 0x80                ; Conserve bit 0x80 (EOF?)
0x00403CA9:  or edx, 2                    ; Ajoute flag 0x02 (READ ERROR)
0x00403CAC:  mov [eax+8], edx             ; Enregistre error state

; RETOUR
0x00403CAF:  mov eax, [ebp-4]             ; EAX = valeur lue (32-bit)
0x00403CB2:  pop ebx                      ; Epilogue
0x00403CB3:  pop ecx
0x00403CB4:  pop ebp
0x00403CB5:  ret
```

### Analyse

**Fonction**: Lit exactement 4 bytes du stream et les retourne comme entier 32-bit.

**Mécanisme**:
1. **Vérification error state** avant lecture
2. **Appel à 0x0040CBF2** qui est probablement `fread()` ou équivalent Borland
3. **Vérification stricte** que 4 bytes ont bien été lus
4. **Gestion d'erreur** avec flags d'état:
   - Bit 0x80: EOF (end of file)
   - Bit 0x02: Read error

**Utilisation VND**: Cette fonction est appelée pour lire:
- Les 3 champs du header (3× readWord32)
- Les longueurs des strings length-prefixed (avant chaque string)

---

## 3. ipstream::readBytes - Lecture de Tableau de Bytes

**Adresse**: `0x00403B6C` (bds52t.dll)  
**Taille**: 29 instructions  
**Appels**: `0x0040CBF2` (même fonction bas-niveau)

### Code Assembleur Annoté

```asm
0x00403B6C:  push ebp                     ; Prologue
0x00403B6D:  mov ebp, esp
0x00403B6F:  push ebx                     ; Sauvegarde registres
0x00403B70:  push esi
0x00403B71:  push edi
0x00403B72:  mov esi, [ebp+0x10]          ; ESI = count (nombre de bytes)
0x00403B75:  mov ebx, [ebp+8]             ; EBX = this (ipstream*)
0x00403B78:  mov edi, [ebx]               ; EDI = *this (stream structure)

; VÉRIFICATION ERROR STATE
0x00403B7A:  cmp dword ptr [edi+8], 0     ; Vérifie error flag
0x00403B7E:  jne 0x403BA8                 ; Si erreur, sortie immédiate

; VÉRIFICATION COUNT > 0
0x00403B80:  test esi, esi                ; Test si count == 0
0x00403B82:  jbe 0x403BA8                 ; Si count <= 0, sortie

; LECTURE DES BYTES
0x00403B84:  push esi                     ; Param 3: count
0x00403B85:  push [ebp+0xC]               ; Param 2: buffer* (destination)
0x00403B88:  push [edi+4]                 ; Param 1: file handle
0x00403B8B:  call 0x40CBF2                ; CALL fread(fd, buffer, count)
0x00403B90:  add esp, 0xC                 ; Nettoie params

; VÉRIFICATION DU RÉSULTAT
0x00403B93:  cmp esi, eax                 ; Compare bytes demandés vs lus
0x00403B95:  je 0x403BA8                  ; Si égal, OK

; GESTION D'ERREUR
0x00403B97:  mov eax, [ebx]               ; Récupère stream structure
0x00403B99:  mov edx, [eax+8]             ; EDX = error flags
0x00403B9C:  and edx, 0x80                ; Conserve EOF flag
0x00403BA2:  or edx, 2                    ; Ajoute READ ERROR flag
0x00403BA5:  mov [eax+8], edx             ; Enregistre state

; RETOUR
0x00403BA8:  pop edi                      ; Epilogue
0x00403BA9:  pop esi
0x00403BAA:  pop ebx
0x00403BAB:  pop ebp
0x00403BAC:  ret
```

### Analyse

**Fonction**: Lit `count` bytes du stream dans un buffer.

**Mécanisme**:
1. **Double vérification**: error state ET count > 0
2. **Appel à 0x0040CBF2**: lecture bas-niveau de `count` bytes
3. **Vérification stricte**: nombre de bytes lus == nombre demandé
4. **Même gestion d'erreur** que readWord32

**Utilisation VND**: Cette fonction lit:
- La signature "VNFILE" (6 bytes)
- Les données des strings après avoir lu leur longueur
- Tout le contenu binaire du VND

---

## 4. Fonction Bas-Niveau: 0x0040CBF2

**Adresse**: `0x0040CBF2` (bds52t.dll)  
**Type**: Wrapper autour de `fread()` C standard library

### Signature Déduite

```c
int __cdecl function_0x40CBF2(void* file_handle, void* buffer, size_t count);
```

**Paramètres**:
- `file_handle`: Handle du fichier ouvert
- `buffer`: Destination des données
- `count`: Nombre de bytes à lire

**Retour**: Nombre de bytes effectivement lus

Cette fonction est **le point d'entrée bas-niveau** pour toutes les opérations de lecture du VND.

---

## 5. Flux Complet de Chargement VND

### Diagramme avec Adresses Exactes

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Événement Utilisateur (Clic, Menu)                       │
└────────────────────────┬────── ───────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. TEventHandler::Dispatch @ 0x0041A32B                     │
│    owl52t.dll - Routage polymorphique                       │
│    → Appel indirect via vtable[2]                           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. TFileDocument::InStream / fpbase::open                   │
│    Ouvre fichier .vnd → crée ipstream object                │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Parse Header (12 bytes)                                  │
│    FOR i = 0 TO 2:                                           │
│      field[i] = ipstream::readWord32() @ 0x00403C74          │
│        → call 0x0040CBF2(fd, buffer, 4)                      │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Find "VNFILE" (6 bytes)                                  │
│    LOOP until found:                                         │
│      ipstream::readBytes(buffer, 6) @ 0x00403B6C             │
│        → call 0x0040CBF2(fd, buffer, 6)                      │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Parse Length-Prefixed Strings                            │
│    FOR each field (Version, App, Symbols, Metadata):        │
│      length = ipstream::readWord32() @ 0x00403C74            │
│        → call 0x0040CBF2(fd, &length, 4)                     │
│      data = ipstream::readBytes(buffer, length) @ 0x00403B6C │
│        → call 0x0040CBF2(fd, buffer, length)                 │
│                                                               │
│    Reads:                                                    │
│      - Version (4 bytes): "2.13"                             │
│      - Application (54 bytes)                                │
│      - Symbol Table (4096 bytes): 200+ variable names        │
│      - Metadata (541 bytes): 13+ vars + resources            │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Parse Script Section                                     │
│    Read remaining bytes as ASCII text                        │
│    (Commands: if/then/addbmp/playavi/etc)                   │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. Execute Script                                            │
│    TEventHandler::Dispatch routes commands to handlers      │
│    → addbmp → UI handler                                     │
│    → playavi → Video handler                                 │
│    → etc.                                                    │
└─────────────────────────────────────────────────────────────┘
```

## 6. Structures de Données Reconstituées

### ipstream Object (Borland C++ stream)

```c
struct ipstream {
    void* vtable;           // +0x00: Virtual function table
    void* file_handle;      // +0x04: File descriptor/handle
    uint32_t error_flags;   // +0x08: Error state
                            //   Bit 0x80: EOF
                            //   Bit 0x02: Read error
    // ... autres champs
};
```

### TEventInfo Object (OWL Event structure)

```c
struct TEventInfo {
    void* vtable;           // +0x00: Virtual table
    void* field1;           // +0x04
    void* field2;           // +0x08: Event specific data
    void* field3;           // +0x0C: Pointer to nested structure
    // field3 contains:
    //   +0x0C: param1
    //   +0x10: param2
    //   +0x14: param3
};
```

## 7. Conclusion

**Découverte Principale**: Le chargement VND utilise un mécanisme en 2 couches:

1. **Couche haute** (ipstream - Borland C++):
   - `readWord32()` @ 0x00403C74
   - `readBytes()` @ 0x00403B6C
   - Gestion d'erreur, buffering

2. **Couche basse** (fonction 0x0040CBF2):
   - Wrapper autour de `fread()`
   - Lecture brute des bytes

**Mécanisme exact**:
- Toute lecture VND passe par `0x0040CBF2`
- Les fonctions `readWord32` et `readBytes` sont des **wrappers sûrs** avec vérification d'erreur
- Le format VND est parsé **séquentiellement** avec des lectures length-prefixed
- Dispatch polymorphique via vtables pour router les événements

**Adresses Clés**:
- Event Router: `0x0041A32B` (owl52t.dll)
- Read Int32: `0x00403C74` (bds52t.dll)
- Read Bytes: `0x00403B6C` (bds52t.dll)
- Low-Level Read: `0x0040CBF2` (bds52t.dll)
