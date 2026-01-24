#!/usr/bin/env python3
"""
Analyse complète de tous les fichiers VND
"""

import json
import os
import sys
from pathlib import Path

def analyze_vnd(vnd_file, max_scenes=100):
    """Parse et analyse un fichier VND"""
    # Parse le VND
    os.system(f'python3 vnd_parser.py "{vnd_file}" {max_scenes} >/dev/null 2>&1')
    
    # Lire le JSON
    json_file = vnd_file.replace('.vnd', '.vnd.parsed.json')
    with open(json_file) as f:
        data = json.load(f)
    
    header = data.get('header', {})
    scenes = data['scenes']
    
    report = {
        'file': vnd_file,
        'header_scene_count': header.get('scene_count', 'N/A'),
        'parsed_scene_count': len(scenes),
        'scenes': []
    }
    
    total_hotspots = 0
    total_with_geo = 0
    total_without_geo = 0
    scenes_with_init_logic = 0
    
    for scene in scenes:
        scene_id = scene['id']
        offset = scene['offset']
        obj_count = scene.get('objCount', 'N/A')
        hotspots = scene['hotspots']
        init_commands = scene['initScript']['commands']
        files = scene['files']
        
        # Analyser les hotspots
        hotspot_details = []
        with_geo = 0
        without_geo = 0
        
        for i, hs in enumerate(hotspots):
            total_hotspots += 1
            cmd_count = len(hs['commands'])
            point_count = hs['geometry']['pointCount']
            has_geo = point_count > 0
            
            if has_geo:
                with_geo += 1
                total_with_geo += 1
            else:
                without_geo += 1
                total_without_geo += 1
                
            hotspot_details.append({
                'id': i,
                'commands': cmd_count,
                'has_geometry': has_geo,
                'point_count': point_count
            })
        
        # Vérifier si initScript a de la logique (anormal)
        has_init_logic = len(init_commands) > 0
        if has_init_logic:
            scenes_with_init_logic += 1
        
        # Fichiers
        file_list = [f['filename'] for f in files[:5]]
        if len(files) > 5:
            file_list.append(f'(+{len(files)-5} more)')
        
        scene_info = {
            'id': scene_id,
            'offset': hex(offset),
            'obj_count': obj_count,
            'hotspots_parsed': len(hotspots),
            'hotspots_with_geo': with_geo,
            'hotspots_without_geo': without_geo,
            'init_commands': len(init_commands),
            'has_init_logic': has_init_logic,
            'files': file_list,
            'hotspot_details': hotspot_details
        }
        
        report['scenes'].append(scene_info)
    
    report['total_hotspots'] = total_hotspots
    report['total_with_geo'] = total_with_geo
    report['total_without_geo'] = total_without_geo
    report['scenes_with_init_logic'] = scenes_with_init_logic
    
    return report

def print_report(report):
    """Affiche le rapport d'analyse"""
    print(f"\n{'='*80}")
    print(f"VND: {report['file']}")
    print(f"{'='*80}")
    print(f"Header déclare: {report['header_scene_count']} scènes")
    print(f"Parser détecte: {report['parsed_scene_count']} scènes")
    print(f"Total hotspots: {report['total_hotspots']} ({report['total_with_geo']} avec géo, {report['total_without_geo']} sans géo)")
    print(f"Scènes avec InitScript Logic: {report['scenes_with_init_logic']}")
    
    if report['total_without_geo'] > 0:
        print(f"\n⚠️  PROBLÈME: {report['total_without_geo']} hotspots SANS géométrie!")
    
    print(f"\n{'Scene':<6} {'Offset':<8} {'objCount':<10} {'HS parsed':<10} {'Avec Geo':<10} {'Sans Geo':<10} {'Init':<6} {'Files'}")
    print("-" * 120)
    
    for scene in report['scenes']:
        obj_count_str = str(scene['obj_count'])
        init_mark = '⚠️' if scene['has_init_logic'] else ''
        geo_mark = '❌' if scene['hotspots_without_geo'] > 0 else '✓'
        
        files_str = ', '.join(scene['files'][:2])
        if len(scene['files']) > 2:
            files_str += '...'
        
        print(f"#{scene['id']:<5} {scene['offset']:<8} {obj_count_str:<10} {scene['hotspots_parsed']:<10} {scene['hotspots_with_geo']:<10} {scene['hotspots_without_geo']:<10} {scene['init_commands']:<4}{init_mark:<2} {files_str}")
        
        # Détails des hotspots sans géométrie
        if scene['hotspots_without_geo'] > 0:
            for hs in scene['hotspot_details']:
                if not hs['has_geometry']:
                    print(f"  └─ Hotspot #{hs['id']}: {hs['commands']} commandes, 0 points")

if __name__ == '__main__':
    vnd_files = [
        'couleurs1/couleurs1.vnd',
        'danem/danem.vnd',
        'belge/belge.vnd',
    ]
    
    all_reports = []
    
    for vnd in vnd_files:
        if os.path.exists(vnd):
            print(f"\nAnalyse de {vnd}...")
            report = analyze_vnd(vnd)
            all_reports.append(report)
            print_report(report)
        else:
            print(f"⚠️  {vnd} introuvable")
    
    # Résumé final
    print(f"\n{'='*80}")
    print("RÉSUMÉ GLOBAL")
    print(f"{'='*80}")
    
    for report in all_reports:
        geo_percent = 100 * report['total_with_geo'] / report['total_hotspots'] if report['total_hotspots'] > 0 else 0
        status = '✅' if report['total_without_geo'] == 0 else '❌'
        print(f"{status} {report['file']}: {report['parsed_scene_count']} scènes, {report['total_hotspots']} hotspots, {geo_percent:.1f}% avec géométrie")
