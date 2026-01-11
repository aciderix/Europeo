# Analyse Complète de bds52t.dll

---

## 1. Informations de Base

- **Nom du fichier**: bds52t.dll
- **Nom complet**: Borland Data Structures 5.2 (Thread-safe)
- **Chemin**: f:\Europeo\FRONTAL\dll\bds52t.dll
- **Taille**: 102400 octets (100 KB)
- **Type de machine**: 0x14c (Intel 386)
- **Nombre de sections**: 7
- **Timestamp**: 1496588914
- **Point d'entrée**: 0x1000

### Informations de Version

- **CompanyName**: Borland International
- **FileDescription**: BIDS Class Library
- **FileVersion**: 5.04
- **InternalName**: BIDS Class Library
- **LegalCopyright**: Copyright Borland International 1993, 1996
- **ProductName**: Borland C++ 5.2
- **ProductVersion**: $Revision:   5.9  $

## 2. Sections du PE

| Nom | Taille Virtuelle | Taille Brute |
|-----|------------------|-------------|
| CODE | 0xc000 | 0xc000 |
| DATA | 0x3000 | 0x2600 |
| TLS | 0x1000 | 0x200 |
| .idata | 0x2000 | 0x1200 |
| .edata | 0x4000 | 0x3800 |
| .reloc | 0x1000 | 0xc00 |
| .rsrc | 0x1000 | 0x400 |

## 3. Fonctions Exportées

**Nombre total d'exports**: 398

### Classes et Composants Principaux

BDS 5.2 expose **44 classes principales**:

- **** - 32 méthodes
- **GetDiagEnabled** - 1 méthodes
- **GetDiagLevel** - 1 méthodes
- **NBits** - 1 méthodes
- **NColors** - 1 méthodes
- **Sqrt** - 1 méthodes
- **TBinarySearchTreeBase** - 6 méthodes
- **TBinaryTreeExternalIteratorBase** - 4 méthodes
- **TBinaryTreeInternalIteratorBase** - 1 méthodes
- **TBinaryTreeKiller** - 1 méthodes
- **TCmdLine** - 4 méthodes
- **TColor** - 4 méthodes
- **TCountedSemaphore** - 1 méthodes
- **TDate** - 29 méthodes
- **TEventSemaphore** - 1 méthodes
- **TFile** - 6 méthodes
- **TFileDroplet** - 3 méthodes
- **TFileName** - 24 méthodes
- **TFileNameIterator** - 3 méthodes
- **TMsgThread** - 10 méthodes

... et 24 autres classes

### Échantillon de Fonctions Exportées

| Fonction |
|----------|
| `@$blsh$qr7ostreamrx11TFileStatus` |
| `@$blsh$qr7ostreamrx5TDate` |
| `@$blsh$qr7ostreamrx5TRect` |
| `@$blsh$qr7ostreamrx5TSize` |
| `@$blsh$qr7ostreamrx5TTime` |
| `@$blsh$qr7ostreamrx6TPoint` |
| `@$blsh$qr7ostreamrx6TResId` |
| `@$blsh$qr7ostreamrx7TPointF` |
| `@$blsh$qr7ostreamrx7TPointL` |
| `@$blsh$qr8opstreamrx5TDate` |
| `@$blsh$qr8opstreamrx5TRect` |
| `@$blsh$qr8opstreamrx5TSize` |
| `@$blsh$qr8opstreamrx5TTime` |
| `@$blsh$qr8opstreamrx6TPoint` |
| `@$blsh$qr8opstreamrx6TResId` |
| `@$blsh$qr8opstreamrx6string` |
| `@$blsh$qr8opstreamrx7TPointF` |
| `@$blsh$qr8opstreamrx7TPointL` |
| `@$brsh$qr7istreamr5TRect` |
| `@$brsh$qr7istreamr5TSize` |
| `@$brsh$qr7istreamr6TPoint` |
| `@$brsh$qr7istreamr7TPointF` |
| `@$brsh$qr7istreamr7TPointL` |
| `@$brsh$qr8ipstreamr5TDate` |
| `@$brsh$qr8ipstreamr5TRect` |
| `@$brsh$qr8ipstreamr5TSize` |
| `@$brsh$qr8ipstreamr5TTime` |
| `@$brsh$qr8ipstreamr6TPoint` |
| `@$brsh$qr8ipstreamr6TResId` |
| `@$brsh$qr8ipstreamr6string` |

... et 368 autres fonctions

## 4. DLLs Importées

**Nombre de DLLs**: 5

### cw3230mt.DLL

**Fonctions importées**: 93

| Fonction |
|----------|
| @xmsg@$bdtr$qv |
| @setfill$qi |
| __sopen |
| __ErrorExit |
| @string@$bctr$qrx6string |
| @setw$qi |
| _findfirst |
| __startupd |
| __daylight |
| __ErrorMessage |
| @strstreambuf@$bdtr$qv |
| @string@$bctr$qv |
| @string@$bctr$qc |
| @streambuf@$bdtr$qv |
| _memcpy |

... et 78 autres

### KERNEL32.dll

**Fonctions importées**: 52

| Fonction |
|----------|
| GetWindowsDirectoryA |
| GetCurrentThreadId |
| GetVersionExA |
| GetVersion |
| GetCurrentThread |
| GetTempPathA |
| ExitThread |
| GetCurrentProcess |
| GetTempFileNameA |
| DuplicateHandle |
| GetSystemInfo |
| lstrcmpA |
| CreateDirectoryA |
| CloseHandle |
| WriteProfileStringA |

... et 37 autres

### COMDLG32.dll

**Fonctions importées**: 1

| Fonction |
|----------|
| GetFileTitleA |

### USER32.dll

**Fonctions importées**: 7

| Fonction |
|----------|
| WaitMessage |
| TranslateMessage |
| PostQuitMessage |
| PeekMessageA |
| MsgWaitForMultipleObjects |
| GetSysColor |
| DispatchMessageA |

### SHELL32.dll

**Fonctions importées**: 2

| Fonction |
|----------|
| DragQueryPoint |
| DragQueryFileA |


## 5. Fonctionnalités Principales

### Nature de la Bibliothèque

`bds52t.dll` est la **bibliothèque de structures de données de Borland C++ 5.2** (thread-safe).

### Composants Fournis

Cette bibliothèque fournit:

#### 1. Conteneurs et Collections
- **TArray**, **TVector** - Tableaux dynamiques
- **TList** - Listes chaînées
- **TQueue**, **TStack** - Files et piles
- **TSet** - Ensembles
- **TMap**, **TDictionary** - Tables associatives

#### 2. Chaînes de Caractères
- **string** - Classe chaîne Borland C++
- **TString** - Wrapper de chaînes
- Fonctions de manipulation: `to_upper`, `to_lower`, `substr`, etc.

#### 3. I/O et Streams
- **ipstream**, **opstream** - Streams d'entrée/sortie
- **fpbase** - Base pour fichiers
- **ifstream**, **ofstream** - Streams fichiers
- Sérialisation d'objets

#### 4. Graphics et UI
- **TColor** - Gestion des couleurs (Black, White, LtBlue, LtGray...)
- **TRect** - Rectangles (Inflate, Offset, Normalize)
- **TPoint** - Points 2D
- **TSize** - Dimensions

#### 5. Configuration et Profiles
- **TProfile** - Lecture/écriture fichiers INI
- GetInt, GetString, WriteInt, WriteString

#### 6. Threading
- **TThread** - Support multi-threading
- **TMsgThread** - Threads avec messages
- **TSystem::SupportsThreads** - Détection capacités threading

#### 7. Exceptions et Erreurs
- **TXBase** - Classe de base pour exceptions
- **xmsg**, **xerror** - Gestion d'erreurs
- Throw, Clone, InstanceCount

#### 8. Utilitaires
- **TCmdLine** - Parsing ligne de commande
- **TUIMetric** - Métriques UI (CxScreen, CyScreen, CxDoubleClk...)
- Fonctions de conversion et validation

## 6. Utilisation dans Virtual Navigator

D'après l'analyse d'europeo.exe, les composants BDS suivants sont utilisés:

### Composants Utilisés

- **TProfile** - Configuration (fichiers INI)
- **TColor** - Couleurs de l'interface
- **TRect**, **TPoint** - Géométrie UI
- **TThread** - Multi-threading
- **string** - Manipulation de chaînes
- **Streams** - Sérialisation/désérialisation
- **TXBase** - Gestion d'exceptions
- **TCmdLine** - Arguments ligne de commande

## 7. Résumé et Conclusions

### Type de Bibliothèque

📚 **Bibliothèque système Borland C++**

- **Origine**: Borland International
- **Version**: 5.2 (thread-safe)
- **Rôle**: Structures de données et utilitaires C++
- **Équivalent**: STL (Standard Template Library) de Microsoft

### Importance pour Virtual Navigator

Cette bibliothèque est **essentielle** car elle fournit:

✅ **Structures de données** - Conteneurs C++ modernes
✅ **I/O avancé** - Streams et sérialisation
✅ **Support UI** - Couleurs, rectangles, métriques
✅ **Threading** - Multi-threading sécurisé
✅ **Configuration** - Gestion fichiers INI

### Relation avec Autres Composants

```
europeo.exe (Application principale)
    ├─> OWL52t.dll (Framework GUI)
    │     └─> Utilise TColor, TRect de BDS
    │
    ├─> bds52t.dll (Data Structures)
    │     └─> Fournit: Collections, Streams, Threading
    │
    └─> cw3230mt.DLL (C++ Runtime)
          └─> Fournit: new/delete, RTTI, exceptions bas niveau
```

### Comparaison avec Équivalents Microsoft

| Borland BDS 5.2 | Microsoft Équivalent |
|-----------------|---------------------|
| string | CString (MFC) |
| TArray, TVector | std::vector (STL) |
| TProfile | CWinApp (MFC) |
| TThread | CWinThread (MFC) |
| ipstream/opstream | iostream (STL) |

---

*Rapport généré automatiquement*
