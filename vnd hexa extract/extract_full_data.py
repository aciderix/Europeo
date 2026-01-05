#!/usr/bin/env python3
"""
Extracteur complet de données .vnd
Extrait toutes les chaînes et structures de données dans un format lisible
"""

import struct
import json
from pathlib import Path
from collections import defaultdict

def analyze_complete_structure(filepath):
    """Analyse complète et extraction de toutes les données"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"📦 Fichier: {filepath} ({len(data)} bytes)\n")
    
    # 1. Extraire toutes les chaînes ASCII
    print("=" * 80)
    print("🔤 EXTRACTION DE TOUTES LES CHAÎNES")
    print("=" * 80 + "\n")
    
    strings_dict = {}
    current_string = []
    start_offset = 0
    
    for i, byte in enumerate(data):
        if 32 <= byte < 127 or byte in (9, 10, 13):
            if not current_string:
                start_offset = i
            current_string.append(chr(byte))
        else:
            if len(current_string) >= 3:
                string = ''.join(current_string).strip()
                if string and len(string) >= 3:
                    strings_dict[start_offset] = string
            current_string = []
    
    # Afficher toutes les chaînes
    for offset in sorted(strings_dict.keys()):
        string = strings_dict[offset]
        print(f"@{offset:08X} ({offset:7d}): {string}")
    
    print(f"\n📊 Total: {len(strings_dict)} chaînes extraites\n")
    
    # 2. Regrouper par type de contenu
    print("=" * 80)
    print("📋 CLASSIFICATION DES CHAÎNES")
    print("=" * 80 + "\n")
    
    variables = []
    conditions = []
    commands = []
    values = []
    
    for offset, string in strings_dict.items():
        if '=' in string and 'then' in string.lower():
            conditions.append(string)
        elif any(cmd in string.lower() for cmd in ['inc_var', 'dec_var', 'hotspot', 'scene', 'playavi', 'playtext']):
            commands.append(string)
        elif string.replace('_', '').replace('-', '').isalnum() and len(string) > 3:
            variables.append(string)
        else:
            values.append(string)
    
    print(f"🎯 Variables ({len(variables)}):")
    for var in sorted(set(variables))[:100]:
        print(f"  - {var}")
    
    print(f"\n⚙️  Conditions ({len(conditions)}):")
    for cond in conditions[:50]:
        print(f"  - {cond}")
    
    print(f"\n🎬 Commandes ({len(commands)}):")
    for cmd in commands[:50]:
        print(f"  - {cmd}")
    
    # 3. Rechercher les patterns de données structurées
    print("\n" + "=" * 80)
    print("🔍 RECHERCHE DES VARIABLES SPÉCIFIQUES")
    print("=" * 80 + "\n")
    
    target_vars = [
        "JUSTEPRIX", "PAIN", "HELICE", "HARPON", "MASQUE", "BOUT_PLO", "BALLON",
        "PLONGE", "GRECQUESTION", "GRECREPONSE", "FIOLEGRECE", "SCORE",
        "CARTETOUR", "BUS", "LEVRIERNU", "LEVRIERPARI", "LEVRIERRESULTAT",
        "RUBAN", "PARFUM", "PEPE", "CASTAGNETTE", "DANSE", "TICKET",
        "MATH", "ORGUE", "PALETTE", "PEINTRE", "HOTTE", "FROG", "CPHOTO",
        "FIOLEVASE", "ROUEDENT", "VIOLON", "MARMOTTE", "MUSIC", "FIOLEAUTR",
        "PARTITION", "ORGE", "TONDEUSE", "SIROP", "LEVURE", "TRANS",
        "ALLEMAGNE", "FIOLE", "FRANCE", "ITALIE", "ANGLETERRE", "ECOSSE",
        "IRLANDE", "ESPAGNE", "SUEDE", "FINLANDE", "AUTRICHE", "PAYSBAS",
        "BELGIQUE"
    ]
    
    found_vars = defaultdict(list)
    
    for var in target_vars:
        for offset, string in strings_dict.items():
            if var.lower() in string.lower():
                found_vars[var].append((offset, string))
    
    for var in sorted(found_vars.keys()):
        print(f"\n🎯 {var}:")
        for offset, string in found_vars[var][:10]:
            print(f"  @{offset:08X}: {string[:100]}")
    
    # 4. Sauvegarder tout dans un fichier JSON
    output_data = {
        'file_info': {
            'name': str(filepath),
            'size': len(data),
            'total_strings': len(strings_dict)
        },
        'all_strings': {f"{k:08X}": v for k, v in strings_dict.items()},
        'variables': sorted(set(variables)),
        'conditions': conditions,
        'commands': commands,
        'found_variables': {k: [(f"{o:08X}", s) for o, s in v] for k, v in found_vars.items()}
    }
    
    output_file = Path('extracted_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Données exportées vers: {output_file}")
    
    # 5. Créer un fichier texte lisible
    text_file = Path('extracted_data.txt')
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("EXTRACTION COMPLÈTE DU FICHIER .VND\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("TOUTES LES CHAÎNES EXTRAITES:\n")
        f.write("-" * 80 + "\n")
        for offset in sorted(strings_dict.keys()):
            f.write(f"@{offset:08X}: {strings_dict[offset]}\n")
        
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("VARIABLES TROUVÉES:\n")
        f.write("=" * 80 + "\n")
        for var in sorted(set(variables)):
            f.write(f"  - {var}\n")
        
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("CONDITIONS ET LOGIQUE:\n")
        f.write("=" * 80 + "\n")
        for cond in sorted(set(conditions)):
            f.write(f"  {cond}\n")
    
    print(f"📝 Données exportées vers: {text_file}")
    
    return output_data

if __name__ == "__main__":
    filepath = Path("allem.vnd")
    
    if not filepath.exists():
        print(f"❌ Fichier non trouvé: {filepath}")
        exit(1)
    
    data = analyze_complete_structure(filepath)
    
    print("\n" + "=" * 80)
    print("✅ EXTRACTION TERMINÉE!")
    print("=" * 80)
    print("\nFichiers créés:")
    print("  📄 extracted_data.json - Toutes les données en JSON")
    print("  📄 extracted_data.txt  - Toutes les données en texte lisible")
