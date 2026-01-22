# Analyse Complète de Euro32.dll

---

## 1. Informations de Base

- **Nom du fichier**: Euro32.dll
- **Chemin**: f:\Europeo\FRONTAL\dll\Euro32.dll
- **Taille**: 569344 octets (556 KB)
- **Type de machine**: 0x14c (Intel 386)
- **Nombre de sections**: 7
- **Timestamp**: 708992537
- **Point d'entrée**: 0x521e4

### Informations de Version

- **CompanyName**: SOPRA
- **FileDescription**: Eutoconverter EcCalc
- **FileVersion**: 1.0.0.0
- **InternalName**: 
- **LegalCopyright**: 
- **LegalTrademarks**: SOPRA - EuroConverter
- **OriginalFilename**: 
- **ProductName**: 
- **ProductVersion**: 1.0.7
- **Comments**: DLL
- **Copiright**: 1998, SOPRA

## 2. Fonctions Exportées

**Nombre total d'exports**: 2

| Ordinal | RVA | Nom |
|---------|-----|-----|
| 2 | 0x51fdc | VNCreateDLLWindow |
| 1 | 0x51ffc | VNDestroyDLLWindow |

## 3. DLLs Importées

**Nombre de DLLs**: 14

### kernel32.dll

**Fonctions**: 36

- GetCurrentThreadId
- DeleteCriticalSection
- LeaveCriticalSection
- EnterCriticalSection
- InitializeCriticalSection
- VirtualFree
- VirtualAlloc
- LocalFree
- LocalAlloc
- InterlockedDecrement
- InterlockedIncrement
- VirtualQuery
- WideCharToMultiByte
- MultiByteToWideChar
- lstrlenA
- lstrcpyA
- LoadLibraryExA
- GetThreadLocale
- GetStartupInfoA
- GetModuleFileNameA

... et 16 autres

### user32.dll

**Fonctions**: 3

- GetKeyboardType
- LoadStringA
- MessageBoxA

### advapi32.dll

**Fonctions**: 3

- RegQueryValueExA
- RegOpenKeyExA
- RegCloseKey

### oleaut32.dll

**Fonctions**: 7

- VariantChangeTypeEx
- VariantCopyInd
- VariantClear
- SysStringLen
- SysFreeString
- SysReAllocStringLen
- SysAllocStringLen

### kernel32.dll

**Fonctions**: 7

- TlsSetValue
- TlsGetValue
- TlsFree
- TlsAlloc
- LocalFree
- LocalAlloc
- GetModuleFileNameA

### advapi32.dll

**Fonctions**: 3

- RegQueryValueExA
- RegOpenKeyExA
- RegCloseKey

### kernel32.dll

**Fonctions**: 57

- lstrcpyA
- WritePrivateProfileStringA
- WriteFile
- WaitForSingleObject
- VirtualQuery
- VirtualAlloc
- Sleep
- SizeofResource
- SetThreadLocale
- SetFilePointer
- SetEvent
- SetErrorMode
- SetEndOfFile
- ReadFile
- MulDiv
- LockResource
- LoadResource
- LoadLibraryA
- LeaveCriticalSection
- InitializeCriticalSection

... et 37 autres

### gdi32.dll

**Fonctions**: 68

- UnrealizeObject
- StretchBlt
- SetWindowOrgEx
- SetWinMetaFileBits
- SetViewportOrgEx
- SetTextColor
- SetStretchBltMode
- SetROP2
- SetPixel
- SetEnhMetaFileBits
- SetDIBColorTable
- SetBrushOrgEx
- SetBkMode
- SetBkColor
- SelectPalette
- SelectObject
- SaveDC
- RestoreDC
- Rectangle
- RectVisible

... et 48 autres

### user32.dll

**Fonctions**: 151

- WindowFromPoint
- WinHelpA
- WaitMessage
- UpdateWindow
- UnregisterClassA
- UnhookWindowsHookEx
- TranslateMessage
- TranslateMDISysAccel
- TrackPopupMenu
- SystemParametersInfoA
- ShowWindow
- ShowScrollBar
- ShowOwnedPopups
- ShowCursor
- SetWindowRgn
- SetWindowsHookExA
- SetWindowPos
- SetWindowPlacement
- SetWindowLongA
- SetTimer

... et 131 autres

### ole32.dll

**Fonctions**: 1

- IsEqualGUID

### comctl32.dll

**Fonctions**: 23

- ImageList_GetImageInfo
- ImageList_SetIconSize
- ImageList_GetIconSize
- ImageList_Read
- ImageList_GetDragImage
- ImageList_DragShowNolock
- ImageList_SetDragCursorImage
- ImageList_DragMove
- ImageList_DragLeave
- ImageList_DragEnter
- ImageList_EndDrag
- ImageList_BeginDrag
- ImageList_Remove
- ImageList_DrawEx
- ImageList_Replace
- ImageList_Draw
- ImageList_GetBkColor
- ImageList_SetBkColor
- ImageList_ReplaceIcon
- ImageList_Add

... et 3 autres

### vndllapi.dll

**Fonctions**: 1

- InitVNCommandMessage

### ecleng32.dll

**Fonctions**: 1

- ece010

### eccalc32.dll

**Fonctions**: 1

- ECIsAGoodCurrency

## 4. Chaînes de Caractères

**Nombre de chaînes**: 4283

Échantillon:

- `This program must be run under Win32`
- ``DATA`
- `.idata`
- `.edata`
- `P.reloc`
- `P.rsrc`
- `Boolean`
- `False`
- `Integer`
- `Double`
- `String`
- `TObject`
- `TObject`
- `System`
- `IUnknown`
- `System`
- `TInterfacedObject`
- `SVWUQ`
- `Z]_^[`
- `YZ]_^[`
- `w;;t$`
- `SVWUQ`
- `Z]_^[`
- `YZ]_^[`
- `"h0DE`
- `YZ]_^[`
- `UhD"@`
- `_^[YY]`
- `_^[Y]`
- `YZ]_^[`
- `Uh}&@`
- `_^[Y]`
- `UhU+@`
- `SOFTWARE\Borland\Delphi\RTL`
- `FPUMaskValue`
- `_^[YY]`
- `PPRTj`
- `Ph:1@`
- `Pho2@`
- `ZTUWVSPRTj`
- `t=HtN`
- `Uhj5@`
- `Portions Copyright (c) 1983,97 Borland`
- `t-Rf;`
- `t f;J`
- `t1SVW`
- `UWVSj`
- `r*PRf`
- `Software\Borland\Locales`
- `Software\Borland\Delphi\Locales`

## 5. Résumé et Conclusions

### Nature du Composant

`Euro32.dll` est un **composant personnalisé** de Virtual Navigator.

- **Compilateur**: Borland C++

### Rôle Probable

D'après le nom et le contexte:

- Composant spécifique à l'application "Europeo"/Virtual Navigator
- Version 32-bit (d'où le nom Euro32)
- Pourrait contenir la logique métier principale ou des fonctionnalités spécifiques

---

*Rapport généré automatiquement*
