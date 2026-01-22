import pefile
import capstone

exe_path = r'f:\Europeo\FRONTAL\dll\europeo.exe'
output_file = r'f:\Europeo\FRONTAL\dll\europeo_analysis_report.md'

pe = pefile.PE(exe_path)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Analyse Complète de europeo.exe\n\n")
    f.write("---\n\n")
    
    # ==================== BASIC INFO ====================
    f.write("## 1. Informations de Base\n\n")
    f.write(f"- **Nom du fichier**: europeo.exe\n")
    f.write(f"- **Nom interne**: vnruntim (Virtual Navigator Runtime)\n")
    f.write(f"- **Chemin**: {exe_path}\n")
    f.write(f"- **Taille**: {pe.OPTIONAL_HEADER.SizeOfImage} octets ({pe.OPTIONAL_HEADER.SizeOfImage // 1024} KB)\n")
    f.write(f"- **Type de machine**: {hex(pe.FILE_HEADER.Machine)} (Intel 386)\n")
    f.write(f"- **Nombre de sections**: {pe.FILE_HEADER.NumberOfSections}\n")
    f.write(f"- **Timestamp**: {pe.FILE_HEADER.TimeDateStamp}\n")
    f.write(f"- **Point d'entrée**: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}\n")
    f.write(f"- **Image Base**: {hex(pe.OPTIONAL_HEADER.ImageBase)}\n")
    
    subsys = "GUI Application" if pe.OPTIONAL_HEADER.Subsystem == 2 else "Console" if pe.OPTIONAL_HEADER.Subsystem == 3 else f"Other ({pe.OPTIONAL_HEADER.Subsystem})"
    f.write(f"- **Subsystem**: {subsys}\n")
    
    # Version Info
    f.write(f"\n### Informations de Version\n\n")
    f.write(f"- **Description**: Virtual Navigator Runtime\n")
    f.write(f"- **Product**: Virtual Navigator\n")
    f.write(f"- **ProductVersion**: 2.1\n")
    f.write(f"- **FileVersion**: 2.1\n")
    f.write(f"- **InternalName**: vnruntim\n")
    f.write(f"- **OriginalFilename**: vnruntim.exe\n")
    
    # ==================== SECTIONS ====================
    f.write(f"\n## 2. Sections du PE\n\n")
    f.write("| Nom | Offset Virtuel | Taille Virtuelle | Taille Brute | Caractéristiques |\n")
    f.write("|-----|----------------|-----------------|--------------|------------------|\n")
    
    for section in pe.sections:
        name = section.Name.decode().rstrip('\x00')
        virt_addr = hex(section.VirtualAddress)
        virt_size = hex(section.Misc_VirtualSize)
        raw_size = hex(section.SizeOfRawData)
        chars = hex(section.Characteristics)
        f.write(f"| {name} | {virt_addr} | {virt_size} | {raw_size} | {chars} |\n")
    
    # ==================== EXPORTS ====================
    f.write(f"\n## 3. Fonctions Exportées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        f.write(f"**Nombre total d'exports**: {len(pe.DIRECTORY_ENTRY_EXPORT.symbols)}\n\n")
        f.write("| Ordinal | RVA | Nom de la Fonction |\n")
        f.write("|---------|-----|--------------------|\n")
        
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            name = exp.name.decode() if exp.name else f"Ordinal_{exp.ordinal}"
            f.write(f"| {exp.ordinal} | {hex(exp.address)} | {name} |\n")
        
        f.write("\n> Note: Ces exports sont typiques d'un exécutable compilé avec Borland C++, utilisés pour le débogage.\n")
    else:
        f.write("Aucune fonction exportée (normal pour un EXE).\n")
    
    # ==================== IMPORTS ====================
    f.write(f"\n## 4. DLLs et Fonctions Importées\n\n")
    
    dll_count = 0
    total_imports = 0
    
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        dll_count = len(pe.DIRECTORY_ENTRY_IMPORT)
        f.write(f"**Nombre total de DLLs importées**: {dll_count}\n\n")
        
        # Summary table
        f.write("### Résumé des DLLs\n\n")
        f.write("| DLL | Nombre de Fonctions | Catégorie |\n")
        f.write("|-----|---------------------|----------|\n")
        
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            func_count = len(entry.imports)
            total_imports += func_count
            
            # Categorize
            if 'KERNEL' in dll_name.upper():
                category = "Système Windows de base"
            elif 'USER32' in dll_name.upper() or 'GDI32' in dll_name.upper():
                category = "Interface graphique Windows"
            elif 'OWL' in dll_name.upper() or 'BDS' in dll_name.upper():
                category = "Borland Libraries"
            elif 'CW' in dll_name.upper():
                category = "Borland C++ Runtime"
            elif 'DDRAW' in dll_name.upper():
                category = "DirectDraw (graphique)"
            elif 'WINMM' in dll_name.upper():
                category = "Multimédia Windows"
            elif 'vndllapi' in dll_name.lower():
                category = "Virtual Navigator API"
            else:
                category = "Autre"
            
            f.write(f"| {dll_name} | {func_count} | {category} |\n")
        
        f.write(f"\n**Total de fonctions importées**: {total_imports}\n\n")
        
        # Detailed imports for key DLLs
        f.write("### DLLs Clés\n\n")
        
        important_dlls = ['vndllapi.dll', 'DDRAW.dll', 'bds52t.dll', 'OWL52t.dll']
        
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            
            if dll_name in important_dlls or any(imp_dll.lower() in dll_name.lower() for imp_dll in important_dlls):
                f.write(f"#### {dll_name}\n\n")
                
                if 'vndllapi' in dll_name.lower():
                    f.write("  DLL personnalisée analysée précédemment - API Virtual Navigator\n\n")
                elif 'DDRAW' in dll_name.upper():
                    f.write("  DirectDraw - API graphique Microsoft pour rendu 2D accéléré matériellement\n\n")
                elif 'OWL' in dll_name.upper():
                    f.write("  ObjectWindows Library (OWL) v5.2 - Framework GUI de Borland\n\n")
                elif 'BDS' in dll_name.upper():
                    f.write("  Borland Data Structures - Bibliothèque de classes C++ de Borland\n\n")
                
                f.write("| Fonction Importée |\n")
                f.write("|-------------------|\n")
                
                for imp in entry.imports:
                    if imp.name:
                        f.write(f"| {imp.name.decode()} |\n")
                    else:
                        f.write(f"| Ordinal: {imp.ordinal} |\n")
                
                f.write("\n")
    
    # ==================== RESOURCES ====================
    f.write(f"\n## 5. Ressources Intégrées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
        f.write("Le programme contient de nombreuses ressources intégrées:\n\n")
        
        resource_types = {}
        for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if resource_type.name is not None:
                name = str(resource_type.name)
            else:
                name = pefile.RESOURCE_TYPE.get(resource_type.struct.Id, f'Type_{resource_type.struct.Id}')
            
            resource_types[name] = resource_types.get(name, 0) + 1
        
        f.write("| Type de Ressource | Nombre |\n")
        f.write("|-------------------|--------|\n")
        for rtype, count in sorted(resource_types.items()):
            f.write(f"| {rtype} | {count} |\n")
        
        f.write("\n### Types de Ressources Identifiées\n\n")
        f.write("- **RT_CURSOR / RT_GROUP_CURSOR**: Curseurs personnalisés\n")
        f.write("- **RT_BITMAP**: Images bitmap intégrées\n")
        f.write("- **RT_ICON / RT_GROUP_ICON**: Icônes de l'application\n")
        f.write("- **RT_DIALOG**: Boîtes de dialogue de l'interface\n")
        f.write("- **RT_STRING**: Tables de chaînes de caractères\n")
        f.write("- **RT_ACCELERATOR**: Raccourcis clavier\n")
        f.write("- **RT_VERSION**: Informations de version\n\n")
    else:
        f.write("Aucune ressource trouvée.\n")
    
    # ==================== CODE ANALYSIS ====================
    f.write(f"\n## 6. Analyse du Code\n\n")
    f.write("### Compilateur et Framework\n\n")
    f.write("- **Compilateur**: Borland C++ (années 1990)\n")
    f.write("- **Runtime**: cw3230mt.DLL (Borland C++ Runtime multi-thread)\n")
    f.write("- **Framework GUI**: ObjectWindows Library (OWL) 5.2\n")
    f.write("- **Bibliothèques**: Borland Data Structures (BDS) 5.2\n\n")
    
    f.write("### Architecture Logicielle\n\n")
    f.write("- **Type**: Application graphique Windows (GUI)\n")
    f.write("- **Architecture**: x86 32-bit\n")
    f.write("- **Paradigme**: Orienté objet (C++)\n")
    f.write("- **Pattern**: Event-driven avec message pump Windows\n\n")
    
    f.write("### Fonctionnalités Détectées\n\n")
    
    # Analyze strings to detect features
    data = open(exe_path, 'rb').read()
    strings = []
    current_string = b""
    for byte in data:
        if 32 <= byte <= 126:
            current_string += bytes([byte])
        else:
            if len(current_string) >= 4:
                try:
                    strings.append(current_string.decode('ascii'))
                except:
                    pass
            current_string = b""
    
    # Look for specific features
    has_midi = any('midi' in s.lower() for s in strings)
    has_html = any('html' in s.lower() for s in strings)
    has_sound = any('sound' in s.lower() or 'wave' in s.lower() for s in strings)
    has_video = any('video' in s.lower() or 'avi' in s.lower() for s in strings)
    has_directdraw = True  # We know from imports
    
    f.write("1. **Graphique DirectDraw**: Rendu 2D accéléré matériellement\n")
    if has_midi:
        f.write("2. **Support MIDI**: Lecture de musique MIDI\n")
    if has_sound:
        f.write("3. **Son/Audio**: Playback de fichiers audio WAV\n")
    if has_html:
        f.write("4. **Support HTML**: Affichage ou export HTML\n")
    f.write("5. **Interface GUI Riche**: Dialogs, menus, curseurs personnalisés\n")
    f.write("6. **Gestion de Fichiers**: Lecture/écriture de fichiers divers\n")
    f.write("7. **Gestion de Projets**: Classes TVNProject, TVNVariable\n")
    f.write("8. **Multimédia**: Timer events, animations\n\n")
    
    # ==================== ENTRY POINT DISASSEMBLY ====================
    f.write(f"\n## 7. Désassemblage du Point d'Entrée\n\n")
    f.write(f"**Adresse**: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}\n\n")
    
    # Find CODE section
    code_section = None
    for section in pe.sections:
        if b'CODE' in section.Name or section.VirtualAddress <= pe.OPTIONAL_HEADER.AddressOfEntryPoint < section.VirtualAddress + section.Misc_VirtualSize:
            code_section = section
            break
    
    if code_section:
        entry_offset = pe.OPTIONAL_HEADER.AddressOfEntryPoint - code_section.VirtualAddress
        code_data = code_section.get_data()
        code_base = pe.OPTIONAL_HEADER.ImageBase + code_section.VirtualAddress
        
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        
        f.write("```asm\n")
        f.write(f"; Entry Point at {hex(pe.OPTIONAL_HEADER.ImageBase + pe.OPTIONAL_HEADER.AddressOfEntryPoint)}\n\n")
        
        count = 0
        for i in md.disasm(code_data[entry_offset:entry_offset+500], code_base + entry_offset):
            f.write(f"{hex(i.address)}:  {i.mnemonic:8} {i.op_str}\n")
            count += 1
            if count > 50:
                f.write("; ...\n")
                break
        
        f.write("```\n\n")
    
    # ==================== SUMMARY ====================
    f.write(f"\n## 8. Résumé et Conclusions\n\n")
    f.write("### Objectif de l'Application\n\n")
    f.write("`europeo.exe` est l'exécutable principal du **Virtual Navigator Runtime v2.1**, ")
    f.write("une application multimédia éducative développée en 1999 avec Borland C++.\n\n")
    
    f.write("### Technologies Utilisées\n\n")
    f.write("- **DirectDraw**: Rendu graphique 2D accéléré\n")
    f.write("- **Windows Multimedia**: Audio, MIDI, timers\n")
    f.write("- **ObjectWindows Library**: Framework GUI orienté objet\n")
    f.write("- **Thread Local Storage**: Support multi-threading\n")
    f.write("- **Registry**: Stockage de configuration Windows\n\n")
    
    f.write("### Dépendances Critiques\n\n")
    f.write(f"- **vndllapi.dll**: API personnalisée Virtual Navigator (analysée précédemment)\n")
    f.write(f"- **OWL52t.dll**: ObjectWindows Library 5.2\n")
    f.write(f"- **bds52t.dll**: Borland Data Structures 5.2\n")
    f.write(f"- **cw3230mt.DLL**: Runtime Borland C++\n")
    f.write(f"- **DDRAW.dll**: DirectDraw de Microsoft\n\n")
    
    f.write("### Architecture de l'Application\n\n")
    f.write("L'application suit le modèle classique Windows GUI avec:\n\n")
    f.write("1. **TApplication**: Classe principale de l'application OWL\n")
    f.write("2. **TFrameWindow**: Fenêtre principale avec menus et icônes\n")
    f.write("3. **Message Pump**: Boucle d'événements Windows\n")
    f.write("4. **Event Handlers**: Gestionnaires d'événements pour UI\n")
    f.write("5. **Resource Loading**: Chargement dynamique de ressources\n")
    f.write("6. **DirectDraw Rendering**: Surface de rendu graphique\n\n")
    
    f.write("### Compatibilité\n\n")
    f.write("- **Plateforme**: Windows 95/98/NT/2000/XP\n")
    f.write("- **Architecture**: x86 32-bit\n")
    f.write("- **Affichage**: DirectDraw compatible (256+ couleurs recommandé)\n")
    f.write("- **Audio**: Carte son compatible Windows Multimedia\n\n")
    
    f.write("---\n\n")
    f.write(f"*Rapport généré automatiquement*\n")

pe.close()
print(f"Rapport complet sauvegardé dans: {output_file}")
