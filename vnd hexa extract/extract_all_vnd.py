#!/usr/bin/env python3
"""
Extracteur batch - Génère un extracted_data.txt pour chaque fichier .vnd
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_complete_structure(filepath, output_txt_file, output_json_file):
    """Analyse complète et extraction de toutes les données pour UN fichier"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    print(f"\n📦 Traitement de: {filepath.name} ({len(data)} bytes)")
    
    # 1. Extraire toutes les chaînes ASCII
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
    
    # 2. Regrouper par type de contenu
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
    
    # 3. Rechercher les variables spécifiques
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
        "BELGIQUE", "BONUS", "VINCI", "BEETHOVEN", "CHAMPAGNE", "BIERE"
    ]
    
    found_vars = defaultdict(list)
    
    for var in target_vars:
        for offset, string in strings_dict.items():
            if var.lower() in string.lower():
                found_vars[var].append((offset, string))
    
    # 4. Sauvegarder dans un fichier JSON
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
    
    with open(output_json_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # 5. Créer un fichier texte lisible
    with open(output_txt_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"EXTRACTION COMPLÈTE DU FICHIER: {filepath.name}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"INFORMATIONS DU FICHIER:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Nom:              {filepath.name}\n")
        f.write(f"Taille:           {len(data):,} bytes\n")
        f.write(f"Chaînes extraites: {len(strings_dict)}\n")
        f.write(f"Variables:        {len(set(variables))}\n")
        f.write(f"Conditions:       {len(conditions)}\n")
        f.write(f"Commandes:        {len(commands)}\n\n")
        
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
        
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("VARIABLES SPÉCIFIQUES TROUVÉES:\n")
        f.write("=" * 80 + "\n")
        for var in sorted(found_vars.keys()):
            if found_vars[var]:
                f.write(f"\n🎯 {var}:\n")
                for offset, string in found_vars[var][:10]:
                    f.write(f"  @{offset:08X}: {string[:100]}\n")
    
    return {
        'filename': filepath.name,
        'size': len(data),
        'strings_count': len(strings_dict),
        'variables_count': len(set(variables)),
        'conditions_count': len(conditions)
    }

def process_all_vnd_files():
    """Traite tous les fichiers .vnd et génère un extracted_data.txt pour chacun"""
    
    # Trouver tous les fichiers .vnd
    vnd_files = sorted(Path('.').glob('*.vnd'))
    
    print("=" * 80)
    print("🎮 EXTRACTION COMPLÈTE - TOUS LES MODULES EUROPEO")
    print("=" * 80)
    print(f"\n📦 Fichiers .vnd trouvés: {len(vnd_files)}\n")
    
    all_stats = []
    
    # Créer un dossier pour les résultats
    output_dir = Path('extracted_data_all')
    output_dir.mkdir(exist_ok=True)
    
    # Traiter chaque fichier
    for vnd_file in vnd_files:
        try:
            # Générer les noms de fichiers de sortie
            base_name = vnd_file.stem  # nom sans extension
            output_txt = output_dir / f"extracted_data_{base_name}.txt"
            output_json = output_dir / f"extracted_data_{base_name}.json"
            
            # Extraire les données
            stats = analyze_complete_structure(vnd_file, output_txt, output_json)
            all_stats.append(stats)
            
            print(f"  ✅ {vnd_file.name}")
            print(f"     → {output_txt.name}")
            print(f"     → {output_json.name}")
            
        except Exception as e:
            print(f"  ❌ Erreur avec {vnd_file.name}: {e}")
    
    # Créer un fichier index
    index_file = output_dir / "INDEX.txt"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("INDEX DES FICHIERS EXTRAITS\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total de fichiers traités: {len(all_stats)}\n\n")
        
        f.write("FICHIERS GÉNÉRÉS:\n")
        f.write("-" * 80 + "\n")
        
        for stats in sorted(all_stats, key=lambda x: x['size'], reverse=True):
            base_name = Path(stats['filename']).stem
            f.write(f"\n📄 {stats['filename']}\n")
            f.write(f"   Taille:    {stats['size']:,} bytes\n")
            f.write(f"   Chaînes:   {stats['strings_count']}\n")
            f.write(f"   Variables: {stats['variables_count']}\n")
            f.write(f"   Fichiers générés:\n")
            f.write(f"     - extracted_data_{base_name}.txt\n")
            f.write(f"     - extracted_data_{base_name}.json\n")
        
        total_size = sum(s['size'] for s in all_stats)
        total_strings = sum(s['strings_count'] for s in all_stats)
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("STATISTIQUES GLOBALES\n")
        f.write("=" * 80 + "\n")
        f.write(f"Taille totale:     {total_size:,} bytes\n")
        f.write(f"Chaînes totales:   {total_strings:,}\n")
        f.write(f"Fichiers générés:  {len(all_stats) * 2} ({len(all_stats)} .txt + {len(all_stats)} .json)\n")
    
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ")
    print("=" * 80)
    print(f"\n✅ {len(all_stats)} modules traités avec succès")
    print(f"📁 Tous les fichiers sont dans: {output_dir}")
    print(f"\nFichiers générés:")
    print(f"  - {len(all_stats)} fichiers .txt (extracted_data_*.txt)")
    print(f"  - {len(all_stats)} fichiers .json (extracted_data_*.json)")
    print(f"  - 1 fichier INDEX.txt")
    
    print("\n" + "=" * 80)
    print("✅ EXTRACTION TERMINÉE!")
    print("=" * 80)

if __name__ == "__main__":
    process_all_vnd_files()
