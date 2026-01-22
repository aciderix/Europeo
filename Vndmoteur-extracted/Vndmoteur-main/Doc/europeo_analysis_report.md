# Analyse Complète de europeo.exe

---

## 1. Informations de Base

- **Nom du fichier**: europeo.exe
- **Nom interne**: vnruntim (Virtual Navigator Runtime)
- **Chemin**: f:\Europeo\FRONTAL\dll\europeo.exe
- **Taille**: 892928 octets (872 KB)
- **Type de machine**: 0x14c (Intel 386)
- **Nombre de sections**: 9
- **Timestamp**: 2442143541
- **Point d'entrée**: 0x1000
- **Image Base**: 0x400000
- **Subsystem**: GUI Application

### Informations de Version

- **Description**: Virtual Navigator Runtime
- **Product**: Virtual Navigator
- **ProductVersion**: 2.1
- **FileVersion**: 2.1
- **InternalName**: vnruntim
- **OriginalFilename**: vnruntim.exe

## 2. Sections du PE

| Nom | Offset Virtuel | Taille Virtuelle | Taille Brute | Caractéristiques |
|-----|----------------|-----------------|--------------|------------------|
| CODE | 0x1000 | 0x39000 | 0x38a00 | 0x60000020 |
| DATA | 0x3a000 | 0x15000 | 0x14c00 | 0xc0000040 |
| .tls | 0x4f000 | 0x1000 | 0x200 | 0xc0000040 |
| .rdata | 0x50000 | 0x1000 | 0x200 | 0x50000040 |
| .INIT | 0x51000 | 0x4000 | 0x3400 | 0x42000040 |
| .idata | 0x55000 | 0x2000 | 0x1200 | 0xc0000040 |
| .edata | 0x57000 | 0x1000 | 0x200 | 0x40000040 |
| .reloc | 0x58000 | 0x5000 | 0x4a00 | 0x50000040 |
| .rsrc | 0x5d000 | 0x7d000 | 0x7c600 | 0xd0000040 |

## 3. Fonctions Exportées

**Nombre total d'exports**: 3

| Ordinal | RVA | Nom de la Fonction |
|---------|-----|--------------------|
| 3 | 0x4ea1c | __DebuggerHookData |
| 2 | 0x1046 | __GetExceptDLLinfo |
| 1 | 0x3a06f | ___CPPdebugHook |

> Note: Ces exports sont typiques d'un exécutable compilé avec Borland C++, utilisés pour le débogage.

## 4. DLLs et Fonctions Importées

**Nombre total de DLLs importées**: 13

### Résumé des DLLs

| DLL | Nombre de Fonctions | Catégorie |
|-----|---------------------|----------|
| cw3230mt.DLL | 91 | Borland C++ Runtime |
| KERNEL32.dll | 28 | Système Windows de base |
| SHELL32.dll | 3 | Autre |
| bds52t.dll | 50 | Borland Libraries |
| USER32.dll | 46 | Interface graphique Windows |
| OWL52t.dll | 207 | Borland Libraries |
| GDI32.dll | 22 | Interface graphique Windows |
| WINMM.dll | 10 | Multimédia Windows |
| DDRAW.dll | 1 | DirectDraw (graphique) |
| VERSION.dll | 3 | Autre |
| ADVAPI32.dll | 11 | Autre |
| vndllapi.dll | 1 | Virtual Navigator API |
| OLE32.dll | 1 | Autre |

**Total de fonctions importées**: 474

### DLLs Clés

#### bds52t.dll

  Borland Data Structures - Bibliothèque de classes C++ de Borland

| Fonction Importée |
|-------------------|
| @TColor@LtBlue |
| @TColor@LtGray |
| @TColor@GetValue$xqv |
| @TMsgThread@PumpWaitingMessages$qv |
| @TPReadObjects@$bctr$qv |
| @TColor@White |
| @TColor@Black |
| @TProfile@GetInt$qpxci |
| @TProfile@GetString$qpxcpcuit1 |
| @TProfile@$bdtr$qv |
| @TProfile@WriteString$qpxct1 |
| @TRect@$brand$qrx5TRect |
| @TProfile@WriteInt$qpxci |
| @TProfile@$bctr$qpxct1 |
| @TRect@Offset$qii |
| @TStreamableBase@$bdtr$qv |
| @TRect@Normalize$qv |
| @TThread@$bdtr$qv |
| @TThread@Terminate$qv |
| @TSystem@SupportsThreads$qv |
| @TRect@Inflate$qii |
| @TUIMetric@CyDoubleClk |
| @TUIMetric@CyScreen |
| @TUIMetric@CxScreen |
| @TXBase@$bctr$qrx6string |
| @TXBase@$bdtr$qv |
| @TXBase@$bctr$qrx6TXBase |
| @TUIMetric@CxDoubleClk |
| @TRect@$bror$qrx5TRect |
| @TCmdLine@$bdtr$qv |
| @TCmdLine@NextToken$q4bool |
| @TCmdLine@$bctr$qpxc |
| @fpbase@close$qv |
| @$brsh$qr8ipstreamr6string |
| @$brsh$qr8ipstreamr5TRect |
| @$blsh$qr8opstreamrx6string |
| @TXBase@Throw$qv |
| @opstream@writeWord32$qul |
| @TXBase@InstanceCount |
| @TXBase@Clone$qv |
| @NColors$qus |
| @strnewdup$qpxcui |
| @pstream@$bdtr$qv |
| @opstream@writeBytes$qpxvui |
| @opstream@$bctr$qv |
| @ipstream@readWord32$qv |
| @ipstream@readWord$qv |
| @ipstream@readVersion$qv |
| @ipstream@readBytes$qpvui |
| @fpbase@open$qpxcii |

#### OWL52t.dll

  ObjectWindows Library (OWL) v5.2 - Framework GUI de Borland

| Fonction Importée |
|-------------------|
| @TGdiObject@RefAdd$qpv16TGdiObject@TType |
| @TGdiObject@$bdtr$qv |
| @TDC@SelectObject$qrx4TPen |
| @TGdiBase@CheckValid$qui |
| @TGauge@StepIt$qv |
| @TDC@ScaleWindowExt$qiiiip5TSize |
| @TApplication@SetMainWindow$qp12TFrameWindow |
| @TGauge@SetValue$qi |
| @TGauge@SetStep$qi |
| @TDC@ScaleViewportExt$qiiiip5TSize |
| @TGauge@SetRange$qii |
| @TGauge@$bctr$qp7TWindowip7TModule |
| @TDC@SaveDC$xqv |
| @TApplication@Run$qv |
| @TApplication@Dispatch$qr24TEventHandler@TEventInfouil |
| @TFrameWindow@SetupWindow$qv |
| @TFrameWindow@SetMenu$qp7HMENU__ |
| @TDC@RestoreFont$qv |
| @TFrameWindow@SetIconSm$qp7TModule6TResId |
| @TFrameWindow@SetIcon$qp7TModule6TResId |
| @TDC@RestoreDC$qi |
| @TApplication@ProcessMsg$qr6tagMSG |
| @TFrameWindow@SetDocTitle$qpxci |
| @TFrameWindow@SetClientWindow$qp7TWindow |
| @TDC@RestoreBrush$qv |
| @TFrameWindow@RemoveChild$qp7TWindow |
| @TFrameWindow@PreProcessMsg$qr6tagMSG |
| @TDC@ResetDCA$qr12_devicemodeA |
| @TApplication@ProcessAppMsg$qr6tagMSG |
| @TApplication@CanClose$qv |
| @B_U_U_U_Dispatch$qr7GENERICM7GENERICquiuiui$4booluil |
| @TFrameWindow@IdleAction$ql |
| @TFrameWindow@HoldFocusHWnd$qp6HWND__t1 |
| @TDC@OffsetViewportOrg$qrx6TPointp6TPoint |
| @TFrameWindow@GetCommandTarget$qv |
| @TFrameWindow@GetClientWindow$qv |
| @TDC@GrayStringA$qrx6TBrushpqqsp5HDC__li$ipxcirx5TRect |
| @TApplication@PreProcessMenu$qp7HMENU__ |
| @v_WPARAM_Dispatch$qr7GENERICM7GENERICqui$vuil |
| @v_U_U_W_Dispatch$qr7GENERICM7GENERICquiuiui$vuil |
| @v_U_U_U_Dispatch$qr7GENERICM7GENERICquiuiui$vuil |
| @v_U_POINT_Dispatch$qr7GENERICM7GENERICquir6TPoint$vuil |
| @TFrameWindow@EvCommandEnable$qr15TCommandEnabler |
| @TDC@GetDeviceCaps$xqi |
| @v_POINTER_Dispatch$qr7GENERICM7GENERICqpv$vuil |
| @v_MdiActivate_Dispatch$qr7GENERICM7GENERICquiui$vuil |
| @TFrameWindow@EvCommand$quip6HWND__ui |
| @v_Dispatch$qr7GENERICM7GENERICqv$vuil |
| @v_B_U_Dispatch$qr7GENERICM7GENERICq4boolui$vuil |
| @TFrameWindow@CleanupWindow$qv |
| @TDC@GetAttributeHDC$xqv |
| @TApplication@MessageLoop$qv |
| @TApplication@$bdtr$qv |
| @U_U_U_U_Dispatch$qr7GENERICM7GENERICquiuiui$uiuil |
| @TXGdi@Raise$quipv |
| @TFrameWindow@AssignMenu$q6TResId |
| @TWindowDC@$bdtr$qv |
| @TWindow@WindowProc$quiuil |
| @TFrameWindow@$bdtr$qv |
| @TDC@ExtTextOutA$qiiuspx5TRectpxcipxi |
| @TWindow@TransferData$q18TTransferDirection |
| @TWindow@Transfer$qpv18TTransferDirection |
| @TFrameWindow@$bctr$qp7TWindowpxct14boolp7TModule |
| @TWindow@ShowWindow$qi |
| @TWindow@SetupWindow$qv |
| @TFont@$bctr$qrx5TFont |
| @TDC@DrawTextA$qpxcirx5TRectus |
| @TApplication@MessageBox$qp6HWND__pxct2ui |
| @TWindow@SetWindowPos$qp6HWND__iiiiui |
| @TWindow@SetParent$qp7TWindow |
| @TFont@$bctr$qpxciiiiiucucucucucucucuc |
| @TWindow@SetDocTitle$qpxci |
| @TWindow@SetCursor$qp7TModule6TResId |
| @TFont@$bctr$qpx11tagLOGFONTA |
| @TDC@$bdtr$qv |
| @TWindow@SetCaption$qpxc |
| @TDC@$bctr$qp5HDC__ |
| @TApplication@$bctr$qpxcrp7TModulep14TAppDictionary |
| @TWindow@RouteCommandEnable$qp6HWND__r15TCommandEnabler |
| @B_LPARAM_Dispatch$qr7GENERICM7GENERICql$4booluil |
| @TWindow@RemoveChild$qp7TWindow |
| @TApplication@InitInstance$qv |
| @B_B_Dispatch$qr7GENERICM7GENERICq4bool$4booluil |
| @B_I2_Dispatch$qr7GENERICM7GENERICqi$4booluil |
| @TWindow@PreProcessMsg$qr6tagMSG |
| @TApplication@InitHPrevInstance |
| @TDib@$bctr$qpxc |
| @TWindow@Paint$qr3TDC4boolr5TRect |
| @TCreatedDC@$bdtr$qv |
| @TWindow@Init$qp7TWindowpxcp7TModule |
| @TWindow@IdleAction$ql |
| @TDib@$bctr$qp11HINSTANCE__6TResId |
| @TWindow@HoldFocusHWnd$qp6HWND__t1 |
| @TWindow@HandleMessage$quiuil |
| @TDialog@SetupWindow$qv |
| @TControl@$bdtr$qv |
| @TWindow@GetWindowRect$xqr5TRect |
| @TWindow@GetWindowClass$qr12tagWNDCLASSA |
| @TDialog@PreProcessMsg$qr6tagMSG |
| @TWindow@GetClientRect$xqr5TRect |
| @TWindow@GetClassNameA$qv |
| @TDialog@IdleAction$ql |
| @TClientDC@$bctr$qp6HWND__ |
| @TWindow@ForwardMessage$qp6HWND__4bool |
| @TDialog@GetWindowClass$qr12tagWNDCLASSA |
| @TWindow@Execute$qv |
| @TWindow@EvVScroll$quiuip6HWND__ |
| @TDialog@GetClassNameA$qv |
| @TCheckBox@SetCheck$qui |
| @TApplication@InitHInstance |
| @TWindow@EvSize$quir5TSize |
| @TWindow@EvNotify$quir7TNotify |
| @TWindow@EvHScroll$quiuip6HWND__ |
| @TWindow@EvCommandEnable$qr15TCommandEnabler |
| @TDialog@Execute$qv |
| @TCheckBox@$bdtr$qv |
| @TWindow@EvCommand$quip6HWND__ui |
| @TWindow@DoExecute$qv |
| @TDialog@EvInitDialog$qp6HWND__ |
| @TWindow@Dispatch$qr24TEventHandler@TEventInfouil |
| @TWindow@Destroy$qi |
| @TDialog@DoExecute$qv |
| @TCheckBox@$bctr$qp7TWindowip9TGroupBoxp7TModule |
| @TApplication@InitCmdShow |
| @TWindow@DefaultProcessing$qv |
| @TWindow@DefWindowProcA$quiuil |
| @TDialog@DoCreate$qv |
| @TWindow@Create$qv |
| @TDialog@DialogFunction$quiuil |
| @TWindow@CloseWindow$qi |
| @TButton@$bdtr$qv |
| @TWindow@CleanupWindow$qv |
| @TDialog@Destroy$qi |
| @TWindow@ChildWithId$xqi |
| @TApplication@InitApplication$qv |
| @TWindow@CanClose$qv |
| @I32_Dispatch$qr7GENERICM7GENERICqv$uluil |
| @TDialog@Create$qv |
| @TWindow@$bdtr$qv |
| @TBrush@$bdtr$qv |
| @TWindow@$bctr$qv |
| @TDialog@CloseWindow$qi |
| @TWindow@$bctr$qp7TWindowpxcp7TModule |
| @TUIHandle@Paint$xqr3TDC |
| @TDialog@$bdtr$qv |
| @TUIHandle@HitTest$xqrx6TPoint |
| @TBrush@$bctr$qrx7TBitmap |
| @TUIHandle@GetCursorId$q16TUIHandle@TWhere |
| @TDialog@$bctr$qp7TWindow6TResIdp7TModule |
| @TUIHandle@$bctr$qrx5TRectuii |
| @TBrush@$bctr$qrx6TColor |
| @TStatic@$bctr$qp7TWindowiuip7TModule |
| @TApplication@IdleAction$ql |
| @TScreenDC@$bctr$qv |
| @TWindow@PerformCreate$qi |
| @TDC@TextOutA$qiipxci |
| @TDib@$bdtr$qv |
| @TWindow@Register$qv |
| @I32_WPARAM_LPARAM_Dispatch$qr7GENERICM7GENERICquil$luil |
| @HandleGlobalException$qr4xmsgpct2 |
| @TRegion@$bdtr$qv |
| @TRegion@$bctr$qpx6TPointii |
| @TDC@TabbedTextOutA$qrx6TPointpxciipxiir5TSize |
| @TPopupMenu@$bctr$qp7HMENU__11TAutoDelete |
| @TWindow@SendMessageA$quiuil |
| @TPopupMenu@$bctr$q11TAutoDelete |
| @TDC@SetWindowOrg$qrx6TPointp6TPoint |
| @TBitmap@Create$qrx4TDibrx8TPalette |
| @TPen@$bctr$qrx6TColorii |
| @TPalette@$bctr$qpx15tagPALETTEENTRYi |
| @TDC@SetWindowExt$qrx5TSizep5TSize |
| @TPalette@$bctr$qp10HPALETTE__11TAutoDelete |
| @TPaintDC@$bdtr$qv |
| @TDC@SetViewportOrg$qrx6TPointp6TPoint |
| @TBitmap@$bdtr$qv |
| @TApplication@GetInitCmdLine$qv |
| @TPaintDC@$bctr$qp6HWND__ |
| @TModule@SetName$qpxc |
| @TDC@SetViewportExt$qrx5TSizep5TSize |
| @TModule@LoadStringA$xqui |
| @TModule@Error$qr4xmsguiui |
| @TDC@SetTextColor$qrx6TColor |
| @TBitmap@$bctr$qv |
| @TModule@Error$qi |
| @TModule@$bdtr$qv |
| @TDC@SetMapMode$qi |
| @TModule@$bctr$qpxcp11HINSTANCE__ |
| @TDC@SetBkColor$qrx6TColor |
| @TModule@$bctr$qpxc4boolt2 |
| @TBitmap@$bctr$qrx3TDCii4bool |
| @B_Dispatch$qr7GENERICM7GENERICqv$4booluil |
| @TMenu@GetMenuItemID$xqi |
| @TDC@SelectStockObject$qi |
| @TMenu@$bdtr$qv |
| @B_WPARAM_Dispatch$qr7GENERICM7GENERICqui$4booluil |
| @TDC@SelectObject$qrx8TPalette4bool |
| @TMenu@$bctr$qp7HMENU__11TAutoDelete |
| @TApplication@TermInstance$qi |
| @TMemoryDC@SelectObject$qrx7TBitmap |
| @TApplication@EnableCtl3d$q4bool |
| @TMemoryDC@RestoreBitmap$qv |
| @TMemoryDC@$bdtr$qv |
| @TDC@SelectObject$qrx6TBrush |
| @TMemoryDC@$bctr$qrx3TDC |
| @TLayoutWindow@$bdtr$qv |
| @TDC@SelectObject$qrx5TFont |
| @TApplication@Start$qv |

#### DDRAW.dll

  DirectDraw - API graphique Microsoft pour rendu 2D accéléré matériellement

| Fonction Importée |
|-------------------|
| DirectDrawCreate |

#### vndllapi.dll

  DLL personnalisée analysée précédemment - API Virtual Navigator

| Fonction Importée |
|-------------------|
| InitVNCommandMessage |


## 5. Ressources Intégrées

Le programme contient de nombreuses ressources intégrées:

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

### Types de Ressources Identifiées

- **RT_CURSOR / RT_GROUP_CURSOR**: Curseurs personnalisés
- **RT_BITMAP**: Images bitmap intégrées
- **RT_ICON / RT_GROUP_ICON**: Icônes de l'application
- **RT_DIALOG**: Boîtes de dialogue de l'interface
- **RT_STRING**: Tables de chaînes de caractères
- **RT_ACCELERATOR**: Raccourcis clavier
- **RT_VERSION**: Informations de version


## 6. Analyse du Code

### Compilateur et Framework

- **Compilateur**: Borland C++ (années 1990)
- **Runtime**: cw3230mt.DLL (Borland C++ Runtime multi-thread)
- **Framework GUI**: ObjectWindows Library (OWL) 5.2
- **Bibliothèques**: Borland Data Structures (BDS) 5.2

### Architecture Logicielle

- **Type**: Application graphique Windows (GUI)
- **Architecture**: x86 32-bit
- **Paradigme**: Orienté objet (C++)
- **Pattern**: Event-driven avec message pump Windows

### Fonctionnalités Détectées

1. **Graphique DirectDraw**: Rendu 2D accéléré matériellement
2. **Support MIDI**: Lecture de musique MIDI
3. **Son/Audio**: Playback de fichiers audio WAV
4. **Support HTML**: Affichage ou export HTML
5. **Interface GUI Riche**: Dialogs, menus, curseurs personnalisés
6. **Gestion de Fichiers**: Lecture/écriture de fichiers divers
7. **Gestion de Projets**: Classes TVNProject, TVNVariable
8. **Multimédia**: Timer events, animations


## 7. Désassemblage du Point d'Entrée

**Adresse**: 0x1000

```asm
; Entry Point at 0x401000

0x401000:  mov      eax, dword ptr [0x43a063]
0x401005:  shl      eax, 2
0x401008:  mov      dword ptr [0x43a067], eax
0x40100d:  push     edi
0x40100e:  push     ecx
0x40100f:  xor      eax, eax
0x401011:  mov      edi, 0x44ec00
0x401016:  mov      ecx, 0x44ed0c
0x40101b:  cmp      ecx, edi
0x40101d:  jbe      0x401024
0x40101f:  sub      ecx, edi
0x401021:  cld      
0x401022:  rep stosb byte ptr es:[edi], al
0x401024:  pop      ecx
0x401025:  pop      edi
0x401026:  push     0
0x401028:  call     0x40353f
0x40102d:  pop      ecx
0x40102e:  push     0x43a02c
0x401033:  push     0
0x401035:  call     0x439030
0x40103a:  mov      dword ptr [0x43a06b], eax
0x40103f:  push     0
0x401041:  jmp      0x438ece
0x401046:  jmp      0x4035da
0x40104b:  xor      eax, eax
0x40104d:  mov      al, byte ptr [0x43a058]
0x401052:  ret      
0x401053:  mov      eax, dword ptr [0x43a06b]
0x401058:  ret      
0x401059:  int3     
0x40105a:  mov      ecx, 0xb0
0x40105f:  or       ecx, ecx
0x401061:  je       0x40109c
0x401063:  cmp      dword ptr [0x43a063], 0
0x40106a:  jae      0x401076
0x40106c:  mov      eax, 0xe2
0x401071:  call     0x401059
0x401076:  push     0xb0
0x40107b:  push     0x40
0x40107d:  call     0x439012
0x401082:  or       eax, eax
0x401084:  jne      0x401090
0x401086:  mov      eax, 0xe2
0x40108b:  call     0x401059
0x401090:  push     eax
0x401091:  push     dword ptr [0x43a063]
0x401097:  call     0x438fca
0x40109c:  ret      
0x40109d:  mov      ecx, 0xb0
0x4010a2:  or       ecx, ecx
; ...
```


## 8. Résumé et Conclusions

### Objectif de l'Application

`europeo.exe` est l'exécutable principal du **Virtual Navigator Runtime v2.1**, une application multimédia éducative développée en 1999 avec Borland C++.

### Technologies Utilisées

- **DirectDraw**: Rendu graphique 2D accéléré
- **Windows Multimedia**: Audio, MIDI, timers
- **ObjectWindows Library**: Framework GUI orienté objet
- **Thread Local Storage**: Support multi-threading
- **Registry**: Stockage de configuration Windows

### Dépendances Critiques

- **vndllapi.dll**: API personnalisée Virtual Navigator (analysée précédemment)
- **OWL52t.dll**: ObjectWindows Library 5.2
- **bds52t.dll**: Borland Data Structures 5.2
- **cw3230mt.DLL**: Runtime Borland C++
- **DDRAW.dll**: DirectDraw de Microsoft

### Architecture de l'Application

L'application suit le modèle classique Windows GUI avec:

1. **TApplication**: Classe principale de l'application OWL
2. **TFrameWindow**: Fenêtre principale avec menus et icônes
3. **Message Pump**: Boucle d'événements Windows
4. **Event Handlers**: Gestionnaires d'événements pour UI
5. **Resource Loading**: Chargement dynamique de ressources
6. **DirectDraw Rendering**: Surface de rendu graphique

### Compatibilité

- **Plateforme**: Windows 95/98/NT/2000/XP
- **Architecture**: x86 32-bit
- **Affichage**: DirectDraw compatible (256+ couleurs recommandé)
- **Audio**: Carte son compatible Windows Multimedia

---

*Rapport généré automatiquement*
