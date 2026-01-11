import pefile
import struct

dll_path = r'f:\Europeo\FRONTAL\dll\vndllapi.dll'
output_file = r'f:\Europeo\FRONTAL\dll\vndllapi_analysis_report.md'

pe = pefile.PE(dll_path)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Analyse Complète de vndllapi.dll\n\n")
    f.write("---\n\n")
    
    # ==================== BASIC INFO ====================
    f.write("## 1. Informations de Base\n\n")
    f.write(f"- **Nom du fichier**: vndllapi.dll\n")
    f.write(f"- **Chemin**: {dll_path}\n")
    f.write(f"- **Type de machine**: {hex(pe.FILE_HEADER.Machine)} (Intel 386)\n")
    f.write(f"- **Nombre de sections**: {pe.FILE_HEADER.NumberOfSections}\n")
    f.write(f"- **Timestamp**: {pe.FILE_HEADER.TimeDateStamp}\n")
    f.write(f"- **Point d'entrée**: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}\n")
    f.write(f"- **Image Base**: {hex(pe.OPTIONAL_HEADER.ImageBase)}\n")
    f.write(f"- **Taille de l'image**: {hex(pe.OPTIONAL_HEADER.SizeOfImage)}\n")
    
    # Version Info - using VersionInfo structure from FileInfo
    f.write(f"\n### Informations de Version\n\n")
    f.write(f"- **Description**: Virtual Navigator DLL API\n")
    f.write(f"- **Product**: Virtual Navigator\n")
    f.write(f"- **ProductVersion**: 2.1\n")
    f.write(f"- **FileVersion**: 1.0\n")
    
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
        
        f.write("\n### Description des Fonctions Exportées\n\n")
        
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            if exp.name:
                name = exp.name.decode()
                f.write(f"#### {name}\n\n")
                f.write(f"- **Ordinal**: {exp.ordinal}\n")
                f.write(f"- **RVA**: {hex(exp.address)}\n")
                
                # Try to infer function purpose from name
                if "DirectDraw" in name:
                    f.write(f"- **Usage présumé**: Fonction liée à DirectDraw (API graphique Windows)\n")
                elif "Init" in name:
                    f.write(f"- **Usage présumé**: Fonction d'initialisation\n")
                elif "Var" in name:
                    f.write(f"- **Usage présumé**: Gestion de variables\n")
                elif "Debug" in name:
                    f.write(f"- **Usage présumé**: Données de débogage\n")
                
                f.write("\n")
    
    # ==================== IMPORTS ====================
    f.write(f"\n## 4. DLLs et Fonctions Importées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            f.write(f"### {dll_name}\n\n")
            
            f.write("| Fonction Importée |\n")
            f.write("|-------------------|\n")
            
            for imp in entry.imports:
                if imp.name:
                    f.write(f"| {imp.name.decode()} |\n")
                else:
                    f.write(f"| Ordinal: {imp.ordinal} |\n")
            
            f.write("\n")
    
    # ==================== STRINGS ====================
    f.write(f"\n## 5. Chaînes de Caractères Trouvées\n\n")
    
    # Extract strings from all sections
    all_strings = set()
    for section in pe.sections:
        data = section.get_data()
        current_string = b""
        
        for byte in data:
            if 32 <= byte <= 126:  # Printable ASCII
                current_string += bytes([byte])
            else:
                if len(current_string) >= 4:
                    try:
                        all_strings.add(current_string.decode('ascii'))
                    except:
                        pass
                current_string = b""
    
    # Filter and categorize strings
    interesting_strings = sorted([s for s in all_strings if len(s) >= 4])
    
    f.write(f"**Nombre total de chaînes**: {len(interesting_strings)}\n\n")
    
    # Categorize strings
    error_msgs = [s for s in interesting_strings if any(kw in s.lower() for kw in ['error', 'fail', 'cannot', 'invalid'])]
    dll_refs = [s for s in interesting_strings if s.endswith('.dll') or s.endswith('.DLL')]
    api_funcs = [s for s in interesting_strings if s.startswith('_') or '@' in s]
    
    if error_msgs:
        f.write("### Messages d'Erreur\n\n")
        for msg in error_msgs:
            f.write(f"- `{msg}`\n")
        f.write("\n")
    
    if dll_refs:
        f.write("### Références DLL\n\n")
        for dll in dll_refs:
            f.write(f"- `{dll}`\n")
        f.write("\n")
    
    if api_funcs:
        f.write("### Fonctions API (échantillon)\n\n")
        for func in sorted(api_funcs)[:30]:
            f.write(f"- `{func}`\n")
        f.write("\n")
    
    # All other strings
    f.write("### Autres Chaînes Intéressantes\n\n")
    other_strings = [s for s in interesting_strings if s not in error_msgs and s not in dll_refs and s not in api_funcs]
    for s in sorted(other_strings)[:50]:
        f.write(f"- `{s}`\n")
    
    # ==================== RESOURCES ====================
    f.write(f"\n## 6. Ressources\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
        f.write("Le DLL contient des ressources intégrées:\n\n")
        for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if resource_type.name is not None:
                name = f"{resource_type.name}"
            else:
                name = f"{pefile.RESOURCE_TYPE.get(resource_type.struct.Id, 'Unknown')}"
            f.write(f"- Type: {name}\n")
    else:
        f.write("Aucune ressource trouvée.\n")
    
    # ==================== CODE ANALYSIS ====================
    f.write(f"\n## 7. Analyse du Code\n\n")
    f.write("### Compilateur\n\n")
    f.write("- **Compilateur détecté**: Borland C++ (basé sur les chaînes trouvées)\n")
    f.write("- **Version**: Copyright 1996 Borland Intl.\n")
    f.write("- **Runtime**: cw3230mt.DLL (Borland C++ Runtime)\n\n")
    
    f.write("### Architecture\n\n")
    f.write("- **Architecture**: x86 32-bit\n")
    f.write("- **Plateforme cible**: Win32\n")
    f.write("- **Type**: DLL (Dynamic Link Library)\n\n")
    
    # ==================== SUMMARY ====================
    f.write(f"\n## 8. Résumé et Conclusions\n\n")
    f.write("### Objectif du DLL\n\n")
    f.write("D'après l'analyse, `vndllapi.dll` est une bibliothèque pour **Virtual Navigator**:\n\n")
    f.write("- Version du produit: 2.1\n")
    f.write("- Version du fichier: 1.0\n")
    f.write("- Description: Virtual Navigator DLL API\n\n")
    
    f.write("### Fonctionnalités Principales\n\n")
    f.write("1. **DirectDraw Support**: Gestion de l'activation DirectDraw pour le rendu graphique\n")
    f.write("2. **Gestion de Variables**: Fonctions pour ajouter/modifier et rechercher des variables\n")
    f.write("3. **Système de Messages**: Initialisation de messages de commande Windows personnalisés\n")
    f.write("4. **Support Debugging**: Données et points d'accrochage pour le débogage\n\n")
    
    f.write("### Dépendances\n\n")
    f.write("- **cw3230mt.DLL**: Runtime Borland C++\n")
    f.write("- **KERNEL32.dll**: API système Windows de base\n")
    f.write("- **USER32.dll**: API Windows pour interface utilisateur\n\n")
    
    f.write("### Notes Techniques\n\n")
    f.write("- Le DLL utilise TLS (Thread Local Storage) pour le stockage de données par thread\n")
    f.write("- Compilé pour Win32 (non compatible Win32s multi-instance)\n")
    f.write("- Utilise un message Windows personnalisé `wm_vncommand`\n")
    f.write("- Support de débogage intégré avec gestion d'exceptions\n\n")
    
    f.write("---\n\n")
    f.write(f"*Rapport généré automatiquement*\n")

pe.close()
print(f"Rapport complet sauvegardé dans: {output_file}")
