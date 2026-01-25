#!/usr/bin/env python3
"""
Analyse les hotspots du parser ACTUEL pour identifier lesquels sont en réalité
des Commands Type A ou Records Type B (faux hotspots)
"""

import json
import os
import struct
from pathlib import Path
from typing import Dict, List, Any, Optional

# Commands Type A (subtypes connus)
COMMAND_SUBTYPES_A = {
    0x00: 'QUIT',
    0x06: 'GOTO_SCENE',
    0x09: 'VIDEO',
    0x0A: 'CURSOR',
    0x10: 'DELAY',
    0x15: 'IF_THEN',
    0x1B: 'ADDBMP',
    0x1F: 'UNKNOWN_1F',
    0x26: 'PLAYTEXT',
    0x27: 'FONT',
    0x28: 'UNKNOWN_28',
    0x29: 'ADDTEXT',
    0x34: 'UNKNOWN_34',
}

def analyze_hotspot_commands(hotspot: Dict[str, Any]) -> Dict[str, Any]:
    """Analyse les commandes d'un hotspot pour détecter si c'est un faux hotspot"""

    geometry = hotspot.get('geometry', {})
    point_count = geometry.get('pointCount', 0)
    has_geometry = point_count > 0

    commands = hotspot.get('commands', [])

    # Analyser les types de commandes
    command_types = []
    all_are_type_a = True

    for cmd in commands:
        subtype = cmd.get('subtype', -1)
        if subtype in COMMAND_SUBTYPES_A:
            command_types.append({
                'subtype': subtype,
                'name': COMMAND_SUBTYPES_A[subtype],
                'param': cmd.get('param', '')
            })
        else:
            all_are_type_a = False

    # Critères de faux hotspot:
    # 1. Pas de géométrie
    # 2. Toutes les commandes sont de Type A
    is_false_hotspot = not has_geometry and all_are_type_a and len(commands) > 0

    # Type spécial: hotspot vide (ni géométrie ni commandes)
    is_empty = not has_geometry and len(commands) == 0

    return {
        'has_geometry': has_geometry,
        'point_count': point_count,
        'command_count': len(commands),
        'command_types': command_types,
        'all_are_type_a': all_are_type_a,
        'is_false_hotspot': is_false_hotspot,
        'is_empty': is_empty
    }

def analyze_vnd_json(json_path: str) -> Dict[str, Any]:
    """Analyse un fichier JSON parsé pour identifier les faux hotspots"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get('scenes', [])

    total_hotspots = 0
    hotspots_with_geom = 0
    hotspots_no_geom = 0
    false_hotspots = 0
    empty_hotspots = 0

    false_hotspot_details = []

    for scene in scenes:
        scene_id = scene.get('sceneId', -1)
        scene_offset = scene.get('offset', 0)
        hotspots = scene.get('hotspots', [])

        for h_idx, hotspot in enumerate(hotspots):
            analysis = analyze_hotspot_commands(hotspot)

            total_hotspots += 1

            if analysis['has_geometry']:
                hotspots_with_geom += 1
            else:
                hotspots_no_geom += 1

            if analysis['is_false_hotspot']:
                false_hotspots += 1
                false_hotspot_details.append({
                    'scene_id': scene_id,
                    'scene_offset': f"0x{scene_offset:X}",
                    'hotspot_id': h_idx,
                    'command_types': analysis['command_types']
                })

            if analysis['is_empty']:
                empty_hotspots += 1

    geom_percent = (hotspots_with_geom / total_hotspots * 100) if total_hotspots > 0 else 0.0
    false_percent = (false_hotspots / total_hotspots * 100) if total_hotspots > 0 else 0.0

    return {
        'total_hotspots': total_hotspots,
        'with_geometry': hotspots_with_geom,
        'without_geometry': hotspots_no_geom,
        'geometry_percent': geom_percent,
        'false_hotspots': false_hotspots,
        'false_percent': false_percent,
        'empty_hotspots': empty_hotspots,
        'false_hotspot_details': false_hotspot_details
    }

def main():
    """Analyse tous les VND parsés pour identifier les faux hotspots"""

    # Liste des VND
    vnd_dirs = [
        'couleurs1', 'allem', 'angleterre', 'autr', 'belge', 'danem',
        'ecosse', 'espa', 'finlan', 'france', 'grece', 'holl',
        'irland', 'italie', 'portu', 'suede', 'biblio', 'barre', 'frontal'
    ]

    results = []

    print("=" * 100)
    print("ANALYSE FAUX HOTSPOTS - PARSER ACTUEL")
    print("=" * 100)
    print()

    for vnd_dir in vnd_dirs:
        # Chercher le fichier JSON parsé
        json_files = list(Path(vnd_dir).glob('*.json'))
        if not json_files:
            continue

        # Prendre le premier JSON trouvé
        json_path = str(json_files[0])

        print(f"Analyse {json_path}...", end=' ')
        try:
            analysis = analyze_vnd_json(json_path)
            results.append({
                'vnd': vnd_dir,
                'json_file': os.path.basename(json_path),
                **analysis
            })
            print(f"✓ {analysis['total_hotspots']} hotspots, {analysis['false_hotspots']} faux ({analysis['false_percent']:.1f}%)")
        except Exception as e:
            print(f"❌ ERREUR: {e}")

    print()
    print("=" * 100)
    print("RÉSULTATS GLOBAUX")
    print("=" * 100)
    print()

    # Tableau récapitulatif
    print(f"{'VND':<15} {'Hotspots':>10} {'% Géom':>8} {'Faux':>8} {'% Faux':>8} {'Vides':>8}")
    print("-" * 100)

    for r in sorted(results, key=lambda x: x['false_percent'], reverse=True):
        print(f"{r['vnd']:<15} {r['total_hotspots']:>10} "
              f"{r['geometry_percent']:>7.1f}% {r['false_hotspots']:>8} "
              f"{r['false_percent']:>7.1f}% {r['empty_hotspots']:>8}")

    print("-" * 100)

    # Totaux
    total_hotspots = sum(r['total_hotspots'] for r in results)
    total_with_geom = sum(r['with_geometry'] for r in results)
    total_without_geom = sum(r['without_geometry'] for r in results)
    total_false = sum(r['false_hotspots'] for r in results)
    total_empty = sum(r['empty_hotspots'] for r in results)

    overall_geom_percent = (total_with_geom / total_hotspots * 100) if total_hotspots > 0 else 0.0
    overall_false_percent = (total_false / total_hotspots * 100) if total_hotspots > 0 else 0.0

    print(f"{'TOTAL':<15} {total_hotspots:>10} "
          f"{overall_geom_percent:>7.1f}% {total_false:>8} "
          f"{overall_false_percent:>7.1f}% {total_empty:>8}")

    print()
    print("=" * 100)
    print("ANALYSE DÉTAILLÉE")
    print("=" * 100)
    print()

    print(f"Total hotspots: {total_hotspots}")
    print(f"  - Avec géométrie: {total_with_geom} ({overall_geom_percent:.1f}%)")
    print(f"  - Sans géométrie: {total_without_geom} ({100-overall_geom_percent:.1f}%)")
    print()
    print(f"Faux hotspots détectés: {total_false} ({overall_false_percent:.1f}%)")
    print(f"  → Commands Type A mal classifiés comme hotspots")
    print()
    print(f"Hotspots vides: {total_empty}")
    print(f"  → Ni géométrie ni commandes (anomalies parsing)")
    print()

    # VND les plus problématiques
    print("🔴 TOP 5 VND AVEC LE PLUS DE FAUX HOTSPOTS:")
    print()
    for r in sorted(results, key=lambda x: x['false_hotspots'], reverse=True)[:5]:
        print(f"{r['vnd']}: {r['false_hotspots']}/{r['total_hotspots']} faux hotspots ({r['false_percent']:.1f}%)")

        # Afficher exemples de faux hotspots
        if r['false_hotspot_details']:
            examples = r['false_hotspot_details'][:3]
            for ex in examples:
                cmd_names = [f"{ct['name']} ({ct['subtype']})" for ct in ex['command_types']]
                print(f"  - Scene {ex['scene_id']}, Hotspot #{ex['hotspot_id']}: {', '.join(cmd_names)}")
            if len(r['false_hotspot_details']) > 3:
                print(f"  ... +{len(r['false_hotspot_details'])-3} autres")
        print()

    # Sauvegarder résultats JSON
    output_file = 'false_hotspots_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Résultats sauvegardés dans: {output_file}")
    print()

    # Estimation impact Type-Aware
    print("=" * 100)
    print("IMPACT ATTENDU PARSER TYPE-AWARE")
    print("=" * 100)
    print()

    print(f"Parser ACTUEL:")
    print(f"  - Total hotspots: {total_hotspots}")
    print(f"  - Hotspots avec géométrie: {total_with_geom} ({overall_geom_percent:.1f}%)")
    print(f"  - Hotspots sans géométrie: {total_without_geom} ({100-overall_geom_percent:.1f}%)")
    print()
    print(f"Parser TYPE-AWARE (estimation):")
    print(f"  - Total hotspots: {total_hotspots - total_false} (−{total_false} faux hotspots)")
    print(f"  - Hotspots avec géométrie: {total_with_geom} ({total_with_geom/(total_hotspots-total_false)*100:.1f}%)")
    print(f"  - Hotspots sans géométrie: {total_without_geom - total_false} ({(total_without_geom-total_false)/(total_hotspots-total_false)*100:.1f}%)")
    print()
    print(f"Amélioration:")
    print(f"  - Faux hotspots éliminés: {total_false}")
    print(f"  - Qualité géométrie: {overall_geom_percent:.1f}% → {total_with_geom/(total_hotspots-total_false)*100:.1f}% (+{total_with_geom/(total_hotspots-total_false)*100 - overall_geom_percent:.1f}%)")
    print()

if __name__ == '__main__':
    main()
