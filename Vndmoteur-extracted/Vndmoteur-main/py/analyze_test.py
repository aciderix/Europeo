import pefile

exe_path = r'f:\Europeo\FRONTAL\dll\test.exe'
output_file = r'f:\Europeo\FRONTAL\dll\test_analysis_report.md'

pe = pefile.PE(exe_path)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Analyse Complète de test.exe\n\n")
    f.write("---\n\n")
    
    # ==================== BASIC INFO ====================
    f.write("## 1. Informations de Base\n\n")
    f.write(f"- **Nom du fichier**: test.exe\n")
    f.write(f"- **Chemin**: {exe_path}\n")
    f.write(f"- **Taille**: {pe.OPTIONAL_HEADER.SizeOfImage} octets ({pe.OPTIONAL_HEADER.SizeOfImage // 1024} KB)\n")
    f.write(f"- **Type de machine**: {hex(pe.FILE_HEADER.Machine)} (Intel 386)\n")
    f.write(f"- **Nombre de sections**: {pe.FILE_HEADER.NumberOfSections}\n")
    f.write(f"- **Timestamp**: {pe.FILE_HEADER.TimeDateStamp}\n")
    f.write(f"- **Point d'entrée**: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}\n")
    f.write(f"- **Image Base**: {hex(pe.OPTIONAL_HEADER.ImageBase)}\n")
    
    subsys = "GUI Application" if pe.OPTIONAL_HEADER.Subsystem == 2 else "Console" if pe.OPTIONAL_HEADER.Subsystem == 3 else f"Other ({pe.OPTIONAL_HEADER.Subsystem})"
    f.write(f"- **Subsystem**: {subsys}\n\n")
    
    # Try to get version info
    if hasattr(pe, 'FileInfo'):
        f.write("### Informations de Version\n\n")
        try:
            for fileinfo in pe.FileInfo:
                for entry in fileinfo:
                    if hasattr(entry, 'StringTable'):
                        for st in entry.StringTable:
                            for key, value in st.entries.items():
                                f.write(f"- **{key.decode()}**: {value.decode()}\n")
        except:
            f.write("Version info présente mais non parsable.\n")
        f.write("\n")
    
    # ==================== SECTIONS ====================
    f.write(f"\n## 2. Sections du PE\n\n")
    f.write("| Nom | Offset Virtuel | Taille Virtuelle | Taille Brute |\n")
    f.write("|-----|----------------|-----------------|-------------|\n")
    
    for section in pe.sections:
        name = section.Name.decode().rstrip('\x00')
        virt_addr = hex(section.VirtualAddress)
        virt_size = hex(section.Misc_VirtualSize)
        raw_size = hex(section.SizeOfRawData)
        f.write(f"| {name} | {virt_addr} | {virt_size} | {raw_size} |\n")
    
    # ==================== EXPORTS ====================
    f.write(f"\n## 3. Fonctions Exportées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        f.write(f"**Nombre total d'exports**: {len(pe.DIRECTORY_ENTRY_EXPORT.symbols)}\n\n")
        f.write("| Ordinal | RVA | Nom |\n")
        f.write("|---------|-----|-----|\n")
        
        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            name = exp.name.decode() if exp.name else f"Ordinal_{exp.ordinal}"
            f.write(f"| {exp.ordinal} | {hex(exp.address)} | {name} |\n")
    else:
        f.write("Aucune fonction exportée (normal pour un EXE de test).\n")
    
    # ==================== IMPORTS ====================
    f.write(f"\n## 4. DLLs et Fonctions Importées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        f.write(f"**Nombre de DLLs**: {len(pe.DIRECTORY_ENTRY_IMPORT)}\n\n")
        
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            f.write(f"### {dll_name}\n\n")
            f.write("| Fonction |\n")
            f.write("|----------|\n")
            
            for imp in entry.imports:
                if imp.name:
                    f.write(f"| {imp.name.decode()} |\n")
                else:
                    f.write(f"| Ordinal: {imp.ordinal} |\n")
            
            f.write("\n")
    else:
        f.write("Aucun import (très inhabituel).\n")
    
    # ==================== RESOURCES ====================
    f.write(f"\n## 5. Ressources\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
        f.write("Ressources présentes:\n\n")
        for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if resource_type.name is not None:
                name = str(resource_type.name)
            else:
                name = pefile.RESOURCE_TYPE.get(resource_type.struct.Id, f'Type_{resource_type.struct.Id}')
            f.write(f"- {name}\n")
    else:
        f.write("Aucune ressource intégrée.\n")
    
    # ==================== STRINGS ====================
    f.write(f"\n## 6. Chaînes de Caractères\n\n")
    
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
    
    interesting = [s for s in strings if len(s) >= 4 and len(s) < 100]
    
    f.write(f"**Nombre de chaînes**: {len(interesting)}\n\n")
    
    if interesting:
        f.write("Chaînes intéressantes (échantillon):\n\n")
        for s in interesting[:50]:
            f.write(f"- `{s}`\n")
    
    # ==================== SUMMARY ====================
    f.write(f"\n## 7. Résumé et Conclusions\n\n")
    
    f.write("### Nature de l'Exécutable\n\n")
    
    # Determine nature based on analysis
    total_size = pe.OPTIONAL_HEADER.SizeOfImage
    is_small = total_size < 100000  # < 100 KB
    
    if is_small:
        f.write("Cet exécutable est **petit et simple**, probablement:\n\n")
        f.write("- Un outil de test/diagnostic\n")
        f.write("- Un utilitaire de développement\n")
        f.write("- Un programme de démonstration\n\n")
    else:
        f.write("Cet exécutable est de taille moyenne/grande.\n\n")
    
    # Check subsystem
    if pe.OPTIONAL_HEADER.Subsystem == 3:
        f.write("**Type**: Application console\n\n")
    elif pe.OPTIONAL_HEADER.Subsystem == 2:
        f.write("**Type**: Application GUI Windows\n\n")
    
    f.write("---\n\n")
    f.write("*Rapport généré automatiquement*\n")

pe.close()
print(f"Rapport sauvegardé: {output_file}")
