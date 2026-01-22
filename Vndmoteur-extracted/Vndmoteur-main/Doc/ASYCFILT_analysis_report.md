# Analyse de ASYCFILT.DLL

---

## 1. Informations de Base

- **Nom du fichier**: ASYCFILT.DLL
- **Chemin**: f:\Europeo\FRONTAL\dll\ASYCFILT.DLL
- **Taille**: 131072 octets (128 KB)
- **Type de machine**: 0x14c
- **Timestamp**: 889890280
- **Point d'entrée**: 0x10a60
- **Image Base**: 0x7f7a0000

### Informations de Version

- **CompanyName**: Microsoft Corporation
- **FileDescription**: Microsoft OLE 2.20  for Windows NT(TM) and Windows 95(TM) Operating Systems
- **FileVersion**: 2.20.4122
- **InternalName**: ASYCFILT.DLL
- **LegalCopyright**: Copyright © Microsoft Corp. 1993-1996.
- **LegalTrademarks**: Microsoft® is a registered trademark of Microsoft Corporation. Windows NT(TM) and Windows 95(TM) are trademarks of Microsoft Corporation.
- **ProductName**: Microsoft OLE 2.20  for Windows NT(TM) and Windows 95(TM) Operating Systems
- **ProductVersion**: 2.20.4122
- **Comments**: Microsoft OLE 2.20  for Windows NT(TM) and Windows 95(TM) Operating Systems

## 2. Fonctions Exportées

**Nombre total d'exports**: 2

Échantillon des exports (20 premiers):

| Ordinal | Nom |
|---------|-----|
| 1 | DllCanUnloadNow |
| 2 | FilterCreateInstance |

## 3. DLLs Importées

**Nombre de DLLs**: 4

- ole32.dll (1 fonctions)
- USER32.dll (1 fonctions)
- GDI32.dll (15 fonctions)
- KERNEL32.dll (56 fonctions)

## 4. Identification

### Nature du Fichier

`ASYCFILT.DLL` est un **fichier système Windows standard**.

**Nom complet**: Active Template Library (ATL) Async Filter

**Rôle**: Bibliothèque OLE Automation utilisée pour:
- Marshalling de données entre processus
- Conversion de types de données OLE/COM
- Support pour Automation (IDispatch)
- Gestion de VARIANT et SAFEARRAY

### Pourquoi Inclus avec Virtual Navigator?

Ce fichier est probablement inclus pour garantir la compatibilité:

1. **Déploiement**: Assure la présence des dépendances nécessaires
2. **Compatibilité**: Version spécifique requise par l'application
3. **Indépendance**: Évite les problèmes si le fichier système est absent ou incompatible
4. **Windows 95/98**: Ces systèmes pouvaient ne pas avoir ce fichier par défaut

## 5. Utilisation dans Virtual Navigator

Ce DLL est probablement utilisé pour:

- **Visual Basic 5.0**: test.exe (VB) nécessite ASYCFILT.DLL pour l'Automation
- **OLE/COM**: Support pour les objets ActiveX ou contrôles OLE
- **Scripting**: Si Virtual Navigator supporte un langage de script
- **Interopérabilité**: Communication entre composants COM

## 6. Résumé

### Type de Fichier

📦 **Fichier système Microsoft Windows**

- **Origine**: Microsoft Corporation
- **Technologie**: OLE Automation / COM
- **Rôle**: Bibliothèque système, pas un composant personnalisé

### Dans le Contexte Virtual Navigator

Ce fichier est:
- ✅ **Nécessaire** pour l'exécution de test.exe (Visual Basic)
- ✅ **Standard** - Aucune modification, fichier Microsoft original
- ✅ **Requis** pour la compatibilité OLE/COM sur Windows 95/98

### Recommandation

> Ce fichier est un composant système Windows standard redistribué avec l'application.
> Il n'est **pas nécessaire de l'analyser en détail** car il s'agit d'un fichier Microsoft
> non modifié, contrairement aux composants personnalisés (vndllapi.dll, europeo.exe, etc.).

---

*Rapport généré automatiquement*
