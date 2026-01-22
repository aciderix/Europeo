import pefile

dll_path = r'f:\Europeo\FRONTAL\dll\Euro32.dll'
output_file = r'f:\Europeo\FRONTAL\dll\Euro32_analysis_report.md'

pe = pefile.PE(dll_path)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Analyse Complète de Euro32.dll\n\n")
    f.write("---\n\n")
    
    # Basic info
    f.write("## 1. Informations de Base\n\n")
    f.write(f"- **Nom du fichier**: Euro32.dll\n")
    f.write(f"- **Chemin**: {dll_path}\n")
    f.write(f"- **Taille**: {pe.OPTIONAL_HEADER.SizeOfImage} octets ({pe.OPTIONAL_HEADER.SizeOfImage // 1024} KB)\n")
    f.write(f"- **Type de machine**: {hex(pe.FILE_HEADER.Machine)} (Intel 386)\n")
    f.write(f"- **Nombre de sections**: {pe.FILE_HEADER.NumberOfSections}\n")
    f.write(f"- **Timestamp**: {pe.FILE_HEADER.TimeDateStamp}\n")
    f.write(f"- **Point d'entrée**: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}\n\n")
    
    # Version
    f.write("### Informations de Version\n\n")
    try:
        version_found = False
        if hasattr(pe, 'FileInfo'):
            for fileinfo in pe.FileInfo:
                for entry in fileinfo:
                    if hasattr(entry, 'StringTable'):
                        for st in entry.StringTable:
                            for key, value in st.entries.items():
                                f.write(f"- **{key.decode()}**: {value.decode()}\n")
                                version_found = True
        if not version_found:
            f.write("Version info non disponible.\n")
    except:
        f.write("Version info non parsable.\n")
    
    f.write("\n")
    
    # Exports
    f.write("## 2. Fonctions Exportées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        exports = pe.DIRECTORY_ENTRY_EXPORT.symbols
        f.write(f"**Nombre total d'exports**: {len(exports)}\n\n")
        
        if len(exports) > 0:
            f.write("| Ordinal | RVA | Nom |\n")
            f.write("|---------|-----|-----|\n")
            
            for exp in exports[:50]:
                name = exp.name.decode() if exp.name else f"Ordinal_{exp.ordinal}"
                f.write(f"| {exp.ordinal} | {hex(exp.address)} | {name} |\n")
            
            if len(exports) > 50:
                f.write(f"\n... et {len(exports) - 50} autres fonctions\n")
    else:
        f.write("Aucune fonction exportée.\n")
    
    f.write("\n")
    
    # Imports
    f.write("## 3. DLLs Importées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        f.write(f"**Nombre de DLLs**: {len(pe.DIRECTORY_ENTRY_IMPORT)}\n\n")
        
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            f.write(f"### {dll_name}\n\n")
            f.write(f"**Fonctions**: {len(entry.imports)}\n\n")
            
            # Sample
            sample = min(20, len(entry.imports))
            for imp in entry.imports[:sample]:
                if imp.name:
                    f.write(f"- {imp.name.decode()}\n")
            if len(entry.imports) > sample:
                f.write(f"\n... et {len(entry.imports) - sample} autres\n")
            f.write("\n")
    
    # Strings
    f.write("## 4. Chaînes de Caractères\n\n")
    
    data = open(dll_path, 'rb').read()
    strings = []
    current_string = b""
    for byte in data:
        if 32 <= byte <= 126:
            current_string += bytes([byte])
        else:
            if len(current_string) >= 5:
                try:
                    strings.append(current_string.decode('ascii'))
                except:
                    pass
            current_string = b""
    
    interesting = [s for s in strings if len(s) >= 5 and len(s) < 100]
    f.write(f"**Nombre de chaînes**: {len(interesting)}\n\n")
    
    if interesting:
        f.write("Échantillon:\n\n")
        for s in interesting[:50]:
            f.write(f"- `{s}`\n")
    
    f.write("\n")
    
    # Summary
    f.write("## 5. Résumé et Conclusions\n\n")
    
    # Determine nature
    is_custom = True
    compiler = "Unknown"
    
    # Check for Borland
    if any('Borland' in s for s in interesting):
        compiler = "Borland C++"
    
    f.write("### Nature du Composant\n\n")
    f.write("`Euro32.dll` est un **composant personnalisé** de Virtual Navigator.\n\n")
    
    if compiler != "Unknown":
        f.write(f"- **Compilateur**: {compiler}\n")
    
    f.write("\n### Rôle Probable\n\n")
    f.write("D'après le nom et le contexte:\n\n")
    f.write("- Composant spécifique à l'application \"Europeo\"/Virtual Navigator\n")
    f.write("- Version 32-bit (d'où le nom Euro32)\n")
    f.write("- Pourrait contenir la logique métier principale ou des fonctionnalités spécifiques\n\n")
    
    f.write("---\n\n")
    f.write("*Rapport généré automatiquement*\n")

pe.close()
print(f"Rapport sauvegardé: {output_file}")
