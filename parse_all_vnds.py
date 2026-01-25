#!/usr/bin/env python3
"""
Parse et analyse TOUS les fichiers VND du projet
"""

import json
import os
import subprocess
from pathlib import Path

VND_FILES = [
    'allem/allem.vnd',
    'angl/angleterre.vnd',
    'autr/autr.vnd',
    'barre/barre.vnd',
    'belge/belge.vnd',
    'biblio/biblio.vnd',
    'couleurs1/couleurs1.vnd',
    'danem/danem.vnd',
    'ecosse/ecosse.vnd',
    'espa/espa.vnd',
    'finlan/finlan.vnd',
    'france/france.vnd',
    'frontal/start.vnd',
    'grece/grece.vnd',
    'holl/holl.vnd',
    'irland/irland.vnd',
    'italie/italie.vnd',
    'portu/portu.vnd',
    'suede/suede.vnd',
]

def parse_vnd(vnd_file):
    """Parse un VND et retourne son analyse"""
    print(f"  Parsing {vnd_file}...", flush=True)
    
    # Parse le VND
    result = subprocess.run(
        ['python3', 'vnd_parser.py', vnd_file, '100'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return {'error': result.stderr, 'file': vnd_file}
    
    # Lire le JSON
    json_file = vnd_file.replace('.vnd', '.vnd.parsed.json')
    try:
        with open(json_file) as f:
            data = json.load(f)
    except:
        return {'error': 'JSON parse failed', 'file': vnd_file}
    
    header = data.get('header', {})
    scenes = data['scenes']
    
    # Analyser
    total_hotspots = 0
    total_with_geo = 0
    total_without_geo = 0
    scenes_with_init_logic = 0
    scenes_special = {'vnoption': 0, 'empty': 0, 'toolbar': 0, 'global_vars': 0}
    
    scene_details = []
    
    for scene in scenes:
        scene_type = scene.get('sceneType', 'unknown')
        
        # Compter les types spéciaux
        if scene_type in scenes_special:
            scenes_special[scene_type] += 1
        
        hotspots = scene['hotspots']
        init_commands = scene['initScript']['commands']
        
        with_geo = sum(1 for hs in hotspots if hs['geometry']['pointCount'] > 0)
        without_geo = len(hotspots) - with_geo
        
        total_hotspots += len(hotspots)
        total_with_geo += with_geo
        total_without_geo += without_geo
        
        if len(init_commands) > 0:
            scenes_with_init_logic += 1
        
        # Détails pour scènes problématiques
        if without_geo > 0 or (len(init_commands) > 0 and scene_type not in ['options', 'global_vars']):
            scene_details.append({
                'id': scene['id'],
                'offset': hex(scene['offset']),
                'type': scene_type,
                'objCount': scene.get('objCount', 'N/A'),
                'hotspots': len(hotspots),
                'without_geo': without_geo,
                'init_cmds': len(init_commands),
                'files': [f['filename'] for f in scene['files'][:2]]
            })
    
    return {
        'file': vnd_file,
        'header_scene_count': header.get('scene_count', 'N/A'),
        'parsed_scene_count': len(scenes),
        'total_hotspots': total_hotspots,
        'with_geo': total_with_geo,
        'without_geo': total_without_geo,
        'scenes_with_init_logic': scenes_with_init_logic,
        'scenes_special': scenes_special,
        'problematic_scenes': scene_details
    }

def main():
    print("="*80)
    print("ANALYSE COMPLÈTE DE TOUS LES FICHIERS VND")
    print("="*80)
    print()
    
    results = []
    
    for vnd in VND_FILES:
        if os.path.exists(vnd):
            result = parse_vnd(vnd)
            results.append(result)
        else:
            print(f"  ⚠️  {vnd} introuvable")
            results.append({'error': 'File not found', 'file': vnd})
    
    # Rapport global
    print("\n" + "="*80)
    print("RAPPORT GLOBAL")
    print("="*80)
    
    print(f"\n{'VND':<25} {'Header':<8} {'Parsed':<8} {'Hotspots':<10} {'Géo':<8} {'Sans Géo':<10} {'% Géo':<8} {'Status'}")
    print("-" * 120)
    
    total_files = 0
    total_ok = 0
    
    for r in results:
        if 'error' in r:
            status = f"❌ {r['error'][:20]}"
            print(f"{r['file']:<25} {'':<8} {'':<8} {'':<10} {'':<8} {'':<10} {'':<8} {status}")
        else:
            total_files += 1
            geo_pct = 100 * r['with_geo'] / r['total_hotspots'] if r['total_hotspots'] > 0 else 100
            status = '✅' if r['without_geo'] == 0 else '⚠️'
            if r['without_geo'] == 0:
                total_ok += 1
            
            print(f"{r['file']:<25} {str(r['header_scene_count']):<8} {r['parsed_scene_count']:<8} {r['total_hotspots']:<10} {r['with_geo']:<8} {r['without_geo']:<10} {geo_pct:>6.1f}% {status}")
    
    print()
    print(f"Total VND parsés: {total_files}")
    print(f"VND 100% géométrie: {total_ok}/{total_files} ({100*total_ok/total_files:.1f}%)")
    
    # Sauvegarder le rapport détaillé
    with open('VND_ANALYSIS_REPORT.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nRapport détaillé sauvegardé: VND_ANALYSIS_REPORT.json")
    
    # Scènes spéciales
    print("\n" + "="*80)
    print("TYPES DE SCÈNES SPÉCIALES (OK sans géométrie)")
    print("="*80)
    
    special_totals = {'vnoption': 0, 'empty': 0, 'toolbar': 0, 'global_vars': 0}
    for r in results:
        if 'scenes_special' in r:
            for k, v in r['scenes_special'].items():
                special_totals[k] += v
    
    print(f"  vnoption.dll (options): {special_totals['vnoption']} scènes")
    print(f"  Empty slots: {special_totals['empty']} scènes")
    print(f"  Toolbar: {special_totals['toolbar']} scènes")
    print(f"  Global vars: {special_totals['global_vars']} scènes")

if __name__ == '__main__':
    main()
