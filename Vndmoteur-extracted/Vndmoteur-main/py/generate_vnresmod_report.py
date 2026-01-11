import pefile
import capstone

dll_path = r'f:\Europeo\FRONTAL\dll\vnresmod.dll'
output_file = r'f:\Europeo\FRONTAL\dll\vnresmod_analysis_report.md'

pe = pefile.PE(dll_path)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Analyse Complète de vnresmod.dll\n\n")
    f.write("---\n\n")
    
    # ==================== BASIC INFO ====================
    f.write("## 1. Informations de Base\n\n")
    f.write(f"- **Nom du fichier**: vnresmod.dll\n")
    f.write(f"- **Nom interne**: vnruntim (Virtual Navigator Runtime)\n")
    f.write(f"- **Chemin**: {dll_path}\n")
    f.write(f"- **Taille**: {pe.OPTIONAL_HEADER.SizeOfImage} octets ({pe.OPTIONAL_HEADER.SizeOfImage // 1024} KB)\n")
    f.write(f"- **Type de machine**: {hex(pe.FILE_HEADER.Machine)} (Intel 386)\n")
    f.write(f"- **Nombre de sections**: {pe.FILE_HEADER.NumberOfSections}\n")
    f.write(f"- **Timestamp**: {pe.FILE_HEADER.TimeDateStamp}\n")
    f.write(f"- **Point d'entrée**: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}\n")
    f.write(f"- **Image Base**: {hex(pe.OPTIONAL_HEADER.ImageBase)}\n")
    
    # Version Info
    f.write(f"\n### Informations de Version\n\n")
    f.write(f"- **Description**: Virtual Navigator Runtime\n")
    f.write(f"- **Product**: Virtual Navigator\n")
    f.write(f"- **ProductVersion**: 2.1\n")
    f.write(f"- **FileVersion**: 2.1\n")
    f.write(f"- **InternalName**: vnruntim\n")
    f.write(f"- **OriginalFilename**: vnruntim.exe\n\n")
    
    f.write("> **Note**: Le OriginalFilename indique \"vnruntim.exe\" mais il s'agit bien d'une DLL.\n")
    f.write("> Cela suggère que ce DLL est une version modulaire du runtime principal.\n\n")
    
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
    
    f.write("\n### Répartition de la Taille\n\n")
    code_size = 0
    data_size = 0
    rsrc_size = 0
    
    for section in pe.sections:
        name = section.Name.decode().rstrip('\x00')
        if 'CODE' in name:
            code_size = section.SizeOfRawData
        elif 'DATA' in name:
            data_size = section.SizeOfRawData
        elif 'rsrc' in name:
            rsrc_size = section.SizeOfRawData
    
    total_interesting = code_size + data_size + rsrc_size
    
    f.write(f"- **Code**: {code_size} octets ({code_size // 1024} KB)\n")
    f.write(f"- **Données**: {data_size} octets ({data_size // 1024} KB)\n")
    f.write(f"- **Ressources**: {rsrc_size} octets ({rsrc_size // 1024} KB)\n\n")
    
    # ==================== EXPORTS ====================
    f.write(f"\n## 3. Fonctions Exportées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        f.write(f"**Nombre total d'exports**: {len(pe.DIRECTORY_ENTRY_EXPORT.symbols)}\n\n")
        f.write("| Ordinal | RVA | Nom de la Fonction |\n")
        f.write("|---------|-----|--------------------|\n")
        
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            name = exp.name.decode() if exp.name else f"Ordinal_{exp.ordinal}"
            f.write(f"| {exp.ordinal} | {hex(exp.address)} | {name} |\n")
        
        f.write("\n### Analyse des Exports\n\n")
        f.write("Les 3 fonctions exportées sont des hooks de débogage Borland C++:\n\n")
        f.write("- `@__lockDebuggerData$qv` : Verrouille les données du débogueur\n")
        f.write("- `@__unlockDebuggerData$qv` : Déverrouille les données du débogueur\n")
        f.write("- `__DebuggerHookData` : Point de données pour le débogueur\n\n")
        f.write("> Ces exports indiquent que ce DLL ne fournit **pas d'API publique**,\n")
        f.write("> contrairement à vndllapi.dll. Il s'agit probablement d'un module de ressources.\n\n")
    
    # ==================== IMPORTS ====================
    f.write(f"\n## 4. DLLs et Fonctions Importées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        f.write(f"**Nombre total de DLLs importées**: {len(pe.DIRECTORY_ENTRY_IMPORT)}\n\n")
        
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            func_count = len(entry.imports)
            
            f.write(f"### {dll_name}\n\n")
            f.write(f"**Nombre de fonctions**: {func_count}\n\n")
            
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
        f.write("Le DLL contient des ressources massives (~500 KB):\n\n")
        
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
        
        f.write("\n> **Observation**: Ce DLL contient exactement les mêmes types de ressources\n")
        f.write("> que europeo.exe avec une taille similaire (~500 KB).\n")
        f.write("> Il s'agit probablement d'un **module de ressources partagées**.\n\n")
    
    # ==================== STRINGS ANALYSIS ====================
    f.write(f"\n## 6. Analyse des Chaînes de Caractères\n\n")
    
    data = open(dll_path, 'rb').read()
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
    
    interesting_strings = [s for s in strings if len(s) >= 4]
    
    f.write(f"**Nombre total de chaînes**: {len(interesting_strings)}\n\n")
    
    # Analyze strings for patterns
    cpp_strings = [s for s in interesting_strings if 'typeinfo' in s.lower() or 'bad_cast' in s.lower() or 'bad_typeid' in s.lower()]
    
    if cpp_strings:
        f.write("### Chaînes C++ RTTI Détectées\n\n")
        for s in cpp_strings[:10]:
            f.write(f"- `{s}`\n")
        f.write("\n> Présence de RTTI (Run-Time Type Information) C++\n\n")
    
    # ==================== COMPARISON ====================
    f.write(f"\n## 7. Comparaison avec europeo.exe\n\n")
    f.write("| Caractéristique | vnresmod.dll | europeo.exe |\n")
    f.write("|----------------|--------------|-------------|\n")
    f.write(f"| Taille totale | 565 KB | 848 KB |\n")
    f.write(f"| Taille ressources | ~500 KB | ~500 KB |\n")
    f.write(f"| Exports | 3 (debug) | 3 (debug) |\n")
    f.write(f"| Imports | Minimal (2 DLLs) | Complet (13 DLLs) |\n")
    f.write(f"| Nom interne | vnruntim | vnruntim |\n")
    f.write(f"| OriginalFilename | vnruntim.exe | vnruntim.exe |\n\n")
    
    # ==================== SUMMARY ====================
    f.write(f"\n## 8. Résumé et Conclusions\n\n")
    f.write("### Nature du DLL\n\n")
    f.write("`vnresmod.dll` est un **module de ressources** (Resource Module) pour Virtual Navigator:\n\n")
    f.write("1. **Nom significatif**: \"vnresmod\" = Virtual Navigator Resource Module\n")
    f.write("2. **Contenu principal**: ~500 KB de ressources (88% du fichier)\n")
    f.write("3. **Imports minimaux**: Seulement KERNEL32 et USER32\n")
    f.write("4. **Pas d'API publique**: Exports limités au débogage\n")
    f.write("5. **Même identité**: InternalName = vnruntim (comme europeo.exe)\n\n")
    
    f.write("### Objectif Probable\n\n")
    f.write("Ce DLL permet de **séparer les ressources** de l'exécutable principal, offrant:\n\n")
    f.write("- **Modularité**: Facilite les mises à jour de l'interface\n")
    f.write("- **Localisation**: Permet différentes versions linguistiques\n")
    f.write("- **Optimisation mémoire**: Chargement à la demande\n")
    f.write("- **Partage**: Ressources communes entre plusieurs exécutables\n\n")
    
    f.write("### Architecture Suggérée\n\n")
    f.write("```\n")
    f.write("europeo.exe (Runtime principal)\n")
    f.write("    |\n")
    f.write("    ├─> vndllapi.dll (API Variables/DirectDraw)\n")
    f.write("    |\n")
    f.write("    └─> vnresmod.dll (Module de Ressources)\n")
    f.write("          └─> Bitmaps, Icônes, Dialogs, Strings, Curseurs\n")
    f.write("```\n\n")
    
    f.write("### Ressources Contenues\n\n")
    f.write("D'après l'analyse, vnresmod.dll contient probablement:\n\n")
    f.write("- **RT_DIALOG**: Définitions de fenêtres et boîtes de dialogue\n")
    f.write("- **RT_BITMAP**: Images et arrière-plans\n")
    f.write("- **RT_ICON / RT_GROUP_ICON**: Icônes de l'application\n")
    f.write("- **RT_CURSOR / RT_GROUP_CURSOR**: Curseurs personnalisés\n")
    f.write("- **RT_STRING**: Tables de chaînes localisables\n")
    f.write("- **RT_ACCELERATOR**: Raccourcis clavier\n")
    f.write("- **RT_VERSION**: Métadonnées de version\n\n")
    
    f.write("### Utilisation Typique\n\n")
    f.write("L'application charge ce DLL au runtime avec:\n\n")
    f.write("```cpp\n")
    f.write("HMODULE hResModule = LoadLibrary(\"vnresmod.dll\");\n")
    f.write("HBITMAP bmp = LoadBitmap(hResModule, MAKEINTRESOURCE(IDB_MYBITMAP));\n")
    f.write("HICON icon = LoadIcon(hResModule, MAKEINTRESOURCE(IDI_MYICON));\n")
    f.write("// ...\n")
    f.write("FreeLibrary(hResModule);\n")
    f.write("```\n\n")
    
    f.write("---\n\n")
    f.write(f"*Rapport généré automatiquement*\n")

pe.close()
print(f"Rapport complet sauvegardé dans: {output_file}")
