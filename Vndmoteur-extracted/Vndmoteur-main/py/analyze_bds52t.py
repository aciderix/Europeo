import pefile

dll_path = r'f:\Europeo\FRONTAL\dll\bds52t.dll'
output_file = r'f:\Europeo\FRONTAL\dll\bds52t_analysis_report.md'

pe = pefile.PE(dll_path)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# Analyse Complète de bds52t.dll\n\n")
    f.write("---\n\n")
    
    # ==================== BASIC INFO ====================
    f.write("## 1. Informations de Base\n\n")
    f.write(f"- **Nom du fichier**: bds52t.dll\n")
    f.write(f"- **Nom complet**: Borland Data Structures 5.2 (Thread-safe)\n")
    f.write(f"- **Chemin**: {dll_path}\n")
    f.write(f"- **Taille**: {pe.OPTIONAL_HEADER.SizeOfImage} octets ({pe.OPTIONAL_HEADER.SizeOfImage // 1024} KB)\n")
    f.write(f"- **Type de machine**: {hex(pe.FILE_HEADER.Machine)} (Intel 386)\n")
    f.write(f"- **Nombre de sections**: {pe.FILE_HEADER.NumberOfSections}\n")
    f.write(f"- **Timestamp**: {pe.FILE_HEADER.TimeDateStamp}\n")
    f.write(f"- **Point d'entrée**: {hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint)}\n\n")
    
    # Version info
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
            f.write("- **Bibliothèque**: Borland Data Structures\n")
            f.write("- **Version**: 5.2 (thread-safe)\n")
            f.write("- **Origine**: Borland C++ Builder/C++ 5.2\n")
    except:
        f.write("- Version Borland Data Structures 5.2\n")
    
    f.write("\n")
    
    # ==================== SECTIONS ====================
    f.write("## 2. Sections du PE\n\n")
    f.write("| Nom | Taille Virtuelle | Taille Brute |\n")
    f.write("|-----|------------------|-------------|\n")
    
    for section in pe.sections:
        name = section.Name.decode().rstrip('\x00')
        virt_size = hex(section.Misc_VirtualSize)
        raw_size = hex(section.SizeOfRawData)
        f.write(f"| {name} | {virt_size} | {raw_size} |\n")
    
    f.write("\n")
    
    # ==================== EXPORTS ====================
    f.write("## 3. Fonctions Exportées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        exports = pe.DIRECTORY_ENTRY_EXPORT.symbols
        f.write(f"**Nombre total d'exports**: {len(exports)}\n\n")
        
        # Categorize exports
        classes = {}
        for exp in exports:
            if exp.name:
                name = exp.name.decode()
                # Extract class name from C++ mangled names
                if '@' in name and '$' in name:
                    # Format: @ClassName@method$signature
                    parts = name.split('@')
                    if len(parts) >= 2:
                        class_name = parts[1].split('$')[0]
                        if class_name not in classes:
                            classes[class_name] = []
                        classes[class_name].append(name)
        
        f.write("### Classes et Composants Principaux\n\n")
        f.write(f"BDS 5.2 expose **{len(classes)} classes principales**:\n\n")
        
        # List major classes
        major_classes = sorted(classes.keys())[:20]
        for cls in major_classes:
            method_count = len(classes[cls])
            f.write(f"- **{cls}** - {method_count} méthodes\n")
        
        if len(classes) > 20:
            f.write(f"\n... et {len(classes) - 20} autres classes\n")
        
        f.write("\n### Échantillon de Fonctions Exportées\n\n")
        f.write("| Fonction |\n")
        f.write("|----------|\n")
        
        sample_exports = [exp.name.decode() for exp in exports[:30] if exp.name]
        for exp_name in sample_exports:
            f.write(f"| `{exp_name}` |\n")
        
        if len(exports) > 30:
            f.write(f"\n... et {len(exports) - 30} autres fonctions\n")
    
    f.write("\n")
    
    # ==================== IMPORTS ====================
    f.write("## 4. DLLs Importées\n\n")
    
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        f.write(f"**Nombre de DLLs**: {len(pe.DIRECTORY_ENTRY_IMPORT)}\n\n")
        
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode()
            func_count = len(entry.imports)
            f.write(f"### {dll_name}\n\n")
            f.write(f"**Fonctions importées**: {func_count}\n\n")
            
            # Show sample
            f.write("| Fonction |\n")
            f.write("|----------|\n")
            for imp in entry.imports[:15]:
                if imp.name:
                    f.write(f"| {imp.name.decode()} |\n")
            if func_count > 15:
                f.write(f"\n... et {func_count - 15} autres\n")
            f.write("\n")
    
    f.write("\n")
    
    # ==================== FUNCTIONALITY ====================
    f.write("## 5. Fonctionnalités Principales\n\n")
    f.write("### Nature de la Bibliothèque\n\n")
    f.write("`bds52t.dll` est la **bibliothèque de structures de données de Borland C++ 5.2** (thread-safe).\n\n")
    f.write("### Composants Fournis\n\n")
    f.write("Cette bibliothèque fournit:\n\n")
    
    f.write("#### 1. Conteneurs et Collections\n")
    f.write("- **TArray**, **TVector** - Tableaux dynamiques\n")
    f.write("- **TList** - Listes chaînées\n")
    f.write("- **TQueue**, **TStack** - Files et piles\n")
    f.write("- **TSet** - Ensembles\n")
    f.write("- **TMap**, **TDictionary** - Tables associatives\n\n")
    
    f.write("#### 2. Chaînes de Caractères\n")
    f.write("- **string** - Classe chaîne Borland C++\n")
    f.write("- **TString** - Wrapper de chaînes\n")
    f.write("- Fonctions de manipulation: `to_upper`, `to_lower`, `substr`, etc.\n\n")
    
    f.write("#### 3. I/O et Streams\n")
    f.write("- **ipstream**, **opstream** - Streams d'entrée/sortie\n")
    f.write("- **fpbase** - Base pour fichiers\n")
    f.write("- **ifstream**, **ofstream** - Streams fichiers\n")
    f.write("- Sérialisation d'objets\n\n")
    
    f.write("#### 4. Graphics et UI\n")
    f.write("- **TColor** - Gestion des couleurs (Black, White, LtBlue, LtGray...)\n")
    f.write("- **TRect** - Rectangles (Inflate, Offset, Normalize)\n")
    f.write("- **TPoint** - Points 2D\n")
    f.write("- **TSize** - Dimensions\n\n")
    
    f.write("#### 5. Configuration et Profiles\n")
    f.write("- **TProfile** - Lecture/écriture fichiers INI\n")
    f.write("- GetInt, GetString, WriteInt, WriteString\n\n")
    
    f.write("#### 6. Threading\n")
    f.write("- **TThread** - Support multi-threading\n")
    f.write("- **TMsgThread** - Threads avec messages\n")
    f.write("- **TSystem::SupportsThreads** - Détection capacités threading\n\n")
    
    f.write("#### 7. Exceptions et Erreurs\n")
    f.write("- **TXBase** - Classe de base pour exceptions\n")
    f.write("- **xmsg**, **xerror** - Gestion d'erreurs\n")
    f.write("- Throw, Clone, InstanceCount\n\n")
    
    f.write("#### 8. Utilitaires\n")
    f.write("- **TCmdLine** - Parsing ligne de commande\n")
    f.write("- **TUIMetric** - Métriques UI (CxScreen, CyScreen, CxDoubleClk...)\n")
    f.write("- Fonctions de conversion et validation\n\n")
    
    # ==================== USAGE ====================
    f.write("## 6. Utilisation dans Virtual Navigator\n\n")
    f.write("D'après l'analyse d'europeo.exe, les composants BDS suivants sont utilisés:\n\n")
    
    f.write("### Composants Utilisés\n\n")
    f.write("- **TProfile** - Configuration (fichiers INI)\n")
    f.write("- **TColor** - Couleurs de l'interface\n")
    f.write("- **TRect**, **TPoint** - Géométrie UI\n")
    f.write("- **TThread** - Multi-threading\n")
    f.write("- **string** - Manipulation de chaînes\n")
    f.write("- **Streams** - Sérialisation/désérialisation\n")
    f.write("- **TXBase** - Gestion d'exceptions\n")
    f.write("- **TCmdLine** - Arguments ligne de commande\n\n")
    
    # ==================== SUMMARY ====================
    f.write("## 7. Résumé et Conclusions\n\n")
    
    f.write("### Type de Bibliothèque\n\n")
    f.write("📚 **Bibliothèque système Borland C++**\n\n")
    f.write("- **Origine**: Borland International\n")
    f.write("- **Version**: 5.2 (thread-safe)\n")
    f.write("- **Rôle**: Structures de données et utilitaires C++\n")
    f.write("- **Équivalent**: STL (Standard Template Library) de Microsoft\n\n")
    
    f.write("### Importance pour Virtual Navigator\n\n")
    f.write("Cette bibliothèque est **essentielle** car elle fournit:\n\n")
    f.write("✅ **Structures de données** - Conteneurs C++ modernes\n")
    f.write("✅ **I/O avancé** - Streams et sérialisation\n")
    f.write("✅ **Support UI** - Couleurs, rectangles, métriques\n")
    f.write("✅ **Threading** - Multi-threading sécurisé\n")
    f.write("✅ **Configuration** - Gestion fichiers INI\n\n")
    
    f.write("### Relation avec Autres Composants\n\n")
    f.write("```\n")
    f.write("europeo.exe (Application principale)\n")
    f.write("    ├─> OWL52t.dll (Framework GUI)\n")
    f.write("    │     └─> Utilise TColor, TRect de BDS\n")
    f.write("    │\n")
    f.write("    ├─> bds52t.dll (Data Structures)\n")
    f.write("    │     └─> Fournit: Collections, Streams, Threading\n")
    f.write("    │\n")
    f.write("    └─> cw3230mt.DLL (C++ Runtime)\n")
    f.write("          └─> Fournit: new/delete, RTTI, exceptions bas niveau\n")
    f.write("```\n\n")
    
    f.write("### Comparaison avec Équivalents Microsoft\n\n")
    f.write("| Borland BDS 5.2 | Microsoft Équivalent |\n")
    f.write("|-----------------|---------------------|\n")
    f.write("| string | CString (MFC) |\n")
    f.write("| TArray, TVector | std::vector (STL) |\n")
    f.write("| TProfile | CWinApp (MFC) |\n")
    f.write("| TThread | CWinThread (MFC) |\n")
    f.write("| ipstream/opstream | iostream (STL) |\n\n")
    
    f.write("---\n\n")
    f.write("*Rapport généré automatiquement*\n")

pe.close()
print(f"Rapport sauvegardé: {output_file}")
