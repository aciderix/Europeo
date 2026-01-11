# Analyse Complète de vnresmod.dll

---

## 1. Informations de Base

- **Nom du fichier**: vnresmod.dll
- **Nom interne**: vnruntim (Virtual Navigator Runtime)
- **Chemin**: f:\Europeo\FRONTAL\dll\vnresmod.dll
- **Taille**: 598016 octets (584 KB)
- **Type de machine**: 0x14c (Intel 386)
- **Nombre de sections**: 7
- **Timestamp**: 101852981
- **Point d'entrée**: 0x1000
- **Image Base**: 0x400000

### Informations de Version

- **Description**: Virtual Navigator Runtime
- **Product**: Virtual Navigator
- **ProductVersion**: 2.1
- **FileVersion**: 2.1
- **InternalName**: vnruntim
- **OriginalFilename**: vnruntim.exe

> **Note**: Le OriginalFilename indique "vnruntim.exe" mais il s'agit bien d'une DLL.
> Cela suggère que ce DLL est une version modulaire du runtime principal.


## 2. Sections du PE

| Nom | Offset Virtuel | Taille Virtuelle | Taille Brute | Caractéristiques |
|-----|----------------|-----------------|--------------|------------------|
| CODE | 0x1000 | 0xa000 | 0x9800 | 0x60000020 |
| DATA | 0xb000 | 0x6000 | 0x2600 | 0xc0000040 |
| TLS | 0x11000 | 0x1000 | 0x200 | 0xc0000040 |
| .idata | 0x12000 | 0x1000 | 0x600 | 0xc0000040 |
| .edata | 0x13000 | 0x1000 | 0x200 | 0x40000040 |
| .reloc | 0x14000 | 0x1000 | 0xa00 | 0x50000040 |
| .rsrc | 0x15000 | 0x7d000 | 0x7c600 | 0xd0000040 |

### Répartition de la Taille

- **Code**: 38912 octets (38 KB)
- **Données**: 9728 octets (9 KB)
- **Ressources**: 509440 octets (497 KB)


## 3. Fonctions Exportées

**Nombre total d'exports**: 3

| Ordinal | RVA | Nom de la Fonction |
|---------|-----|--------------------|
| 2 | 0x1754 | @__lockDebuggerData$qv |
| 3 | 0x177c | @__unlockDebuggerData$qv |
| 1 | 0xb1b8 | __DebuggerHookData |

### Analyse des Exports

Les 3 fonctions exportées sont des hooks de débogage Borland C++:

- `@__lockDebuggerData$qv` : Verrouille les données du débogueur
- `@__unlockDebuggerData$qv` : Déverrouille les données du débogueur
- `__DebuggerHookData` : Point de données pour le débogueur

> Ces exports indiquent que ce DLL ne fournit **pas d'API publique**,
> contrairement à vndllapi.dll. Il s'agit probablement d'un module de ressources.


## 4. DLLs et Fonctions Importées

**Nombre total de DLLs importées**: 2

### KERNEL32.dll

**Nombre de fonctions**: 43

| Fonction Importée |
|-------------------|
| GetFileAttributesA |
| EnterCriticalSection |
| ExitProcess |
| CloseHandle |
| GetACP |
| GetCPInfo |
| GetCurrentThreadId |
| GetDateFormatA |
| GetEnvironmentStrings |
| CreateFileA |
| GetFileType |
| GetLastError |
| GetLocalTime |
| GetModuleFileNameA |
| GetModuleHandleA |
| GetProcAddress |
| GetStartupInfoA |
| GetStdHandle |
| GetStringTypeW |
| GetVersion |
| FreeEnvironmentStringsA |
| GlobalMemoryStatus |
| InitializeCriticalSection |
| LeaveCriticalSection |
| LocalAlloc |
| LocalFree |
| MultiByteToWideChar |
| RaiseException |
| RtlUnwind |
| SetConsoleCtrlHandler |
| SetFilePointer |
| SetHandleCount |
| TlsAlloc |
| TlsFree |
| TlsGetValue |
| TlsSetValue |
| UnhandledExceptionFilter |
| VirtualAlloc |
| VirtualFree |
| VirtualQuery |
| WideCharToMultiByte |
| WriteFile |
| GetVersionExA |

### USER32.dll

**Nombre de fonctions**: 2

| Fonction Importée |
|-------------------|
| MessageBoxA |
| EnumThreadWindows |


## 5. Ressources Intégrées

Le DLL contient des ressources massives (~500 KB):

| Type de Ressource | Nombre |
|-------------------|--------|
| RT_ACCELERATOR | 1 |
| RT_BITMAP | 1 |
| RT_CURSOR | 1 |
| RT_DIALOG | 1 |
| RT_GROUP_CURSOR | 1 |
| RT_GROUP_ICON | 1 |
| RT_ICON | 1 |
| RT_STRING | 1 |
| RT_VERSION | 1 |

> **Observation**: Ce DLL contient exactement les mêmes types de ressources
> que europeo.exe avec une taille similaire (~500 KB).
> Il s'agit probablement d'un **module de ressources partagées**.


## 6. Analyse des Chaînes de Caractères

**Nombre total de chaînes**: 4840

### Chaînes C++ RTTI Détectées

- `typeinfo *`
- `Bad_typeid`
- `Bad_cast`
- `typeinfo`

> Présence de RTTI (Run-Time Type Information) C++


## 7. Comparaison avec europeo.exe

| Caractéristique | vnresmod.dll | europeo.exe |
|----------------|--------------|-------------|
| Taille totale | 565 KB | 848 KB |
| Taille ressources | ~500 KB | ~500 KB |
| Exports | 3 (debug) | 3 (debug) |
| Imports | Minimal (2 DLLs) | Complet (13 DLLs) |
| Nom interne | vnruntim | vnruntim |
| OriginalFilename | vnruntim.exe | vnruntim.exe |


## 8. Résumé et Conclusions

### Nature du DLL

`vnresmod.dll` est un **module de ressources** (Resource Module) pour Virtual Navigator:

1. **Nom significatif**: "vnresmod" = Virtual Navigator Resource Module
2. **Contenu principal**: ~500 KB de ressources (88% du fichier)
3. **Imports minimaux**: Seulement KERNEL32 et USER32
4. **Pas d'API publique**: Exports limités au débogage
5. **Même identité**: InternalName = vnruntim (comme europeo.exe)

### Objectif Probable

Ce DLL permet de **séparer les ressources** de l'exécutable principal, offrant:

- **Modularité**: Facilite les mises à jour de l'interface
- **Localisation**: Permet différentes versions linguistiques
- **Optimisation mémoire**: Chargement à la demande
- **Partage**: Ressources communes entre plusieurs exécutables

### Architecture Suggérée

```
europeo.exe (Runtime principal)
    |
    ├─> vndllapi.dll (API Variables/DirectDraw)
    |
    └─> vnresmod.dll (Module de Ressources)
          └─> Bitmaps, Icônes, Dialogs, Strings, Curseurs
```

### Ressources Contenues

D'après l'analyse, vnresmod.dll contient probablement:

- **RT_DIALOG**: Définitions de fenêtres et boîtes de dialogue
- **RT_BITMAP**: Images et arrière-plans
- **RT_ICON / RT_GROUP_ICON**: Icônes de l'application
- **RT_CURSOR / RT_GROUP_CURSOR**: Curseurs personnalisés
- **RT_STRING**: Tables de chaînes localisables
- **RT_ACCELERATOR**: Raccourcis clavier
- **RT_VERSION**: Métadonnées de version

### Utilisation Typique

L'application charge ce DLL au runtime avec:

```cpp
HMODULE hResModule = LoadLibrary("vnresmod.dll");
HBITMAP bmp = LoadBitmap(hResModule, MAKEINTRESOURCE(IDB_MYBITMAP));
HICON icon = LoadIcon(hResModule, MAKEINTRESOURCE(IDI_MYICON));
// ...
FreeLibrary(hResModule);
```

---

*Rapport généré automatiquement*
