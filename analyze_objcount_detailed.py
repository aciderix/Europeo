#!/usr/bin/env python3
"""
Analyse détaillée des objCount et hotspots réels
- Nombre de scènes annoncées (header) vs parsées
- objCount déclaré vs hotspots parsés par scène
- Contenu des hotspots sans géométrie (non-faux)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter

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

def analyze_hotspot(hotspot: Dict[str, Any]) -> Dict[str, Any]:
    """Analyse un hotspot en détail"""

    geometry = hotspot.get('geometry', {})
    point_count = geometry.get('pointCount', 0)
    has_geometry = point_count > 0

    commands = hotspot.get('commands', [])

    # Analyser les types de commandes
    command_types = []
    all_are_type_a = True
    has_non_type_a = False

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
            has_non_type_a = True
            command_types.append({
                'subtype': subtype,
                'name': f'Type_{subtype}',
                'param': cmd.get('param', '')
            })

    # Critères
    is_false_hotspot = not has_geometry and all_are_type_a and len(commands) > 0
    is_empty = not has_geometry and len(commands) == 0
    is_legitimate_no_geom = not has_geometry and has_non_type_a  # Hotspot légitime sans géométrie

    return {
        'has_geometry': has_geometry,
        'point_count': point_count,
        'command_count': len(commands),
        'command_types': command_types,
        'all_are_type_a': all_are_type_a,
        'has_non_type_a': has_non_type_a,
        'is_false_hotspot': is_false_hotspot,
        'is_empty': is_empty,
        'is_legitimate_no_geom': is_legitimate_no_geom
    }

def analyze_vnd_detailed(json_path: str) -> Dict[str, Any]:
    """Analyse détaillée d'un VND"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    header = data.get('header', {})
    scenes = data.get('scenes', [])

    # Header info
    header_scene_count = header.get('sceneCount', 'N/A')

    # Analyse par scène
    scene_analysis = []
    objcount_matches = 0
    objcount_mismatches = 0
    objcount_na = 0

    total_objcount_declared = 0
    total_hotspots_parsed = 0
    total_hotspots_with_geom = 0
    total_hotspots_no_geom = 0
    total_false_hotspots = 0
    total_legitimate_no_geom = 0
    total_empty_hotspots = 0

    legitimate_no_geom_examples = []

    for scene in scenes:
        scene_id = scene.get('sceneId', -1)
        scene_offset = scene.get('offset', 0)
        obj_count = scene.get('objCount', 'N/A')
        hotspots = scene.get('hotspots', [])

        hotspot_count = len(hotspots)

        # Analyser chaque hotspot
        scene_false = 0
        scene_geom = 0
        scene_no_geom = 0
        scene_legitimate_no_geom = 0
        scene_empty = 0

        for h_idx, hotspot in enumerate(hotspots):
            analysis = analyze_hotspot(hotspot)

            if analysis['has_geometry']:
                scene_geom += 1
                total_hotspots_with_geom += 1
            else:
                scene_no_geom += 1
                total_hotspots_no_geom += 1

            if analysis['is_false_hotspot']:
                scene_false += 1
                total_false_hotspots += 1

            if analysis['is_empty']:
                scene_empty += 1
                total_empty_hotspots += 1

            if analysis['is_legitimate_no_geom']:
                scene_legitimate_no_geom += 1
                total_legitimate_no_geom += 1
                if len(legitimate_no_geom_examples) < 10:  # Limiter exemples
                    legitimate_no_geom_examples.append({
                        'scene_id': scene_id,
                        'hotspot_id': h_idx,
                        'commands': analysis['command_types']
                    })

        # Comparer objCount
        if obj_count == 'N/A':
            objcount_na += 1
            match_status = 'N/A'
        elif obj_count == hotspot_count:
            objcount_matches += 1
            match_status = 'MATCH'
            total_objcount_declared += obj_count
        else:
            objcount_mismatches += 1
            match_status = f'MISMATCH ({obj_count} vs {hotspot_count})'
            total_objcount_declared += obj_count

        total_hotspots_parsed += hotspot_count

        scene_analysis.append({
            'scene_id': scene_id,
            'offset': f'0x{scene_offset:X}',
            'obj_count': obj_count,
            'hotspots_parsed': hotspot_count,
            'match_status': match_status,
            'with_geom': scene_geom,
            'no_geom': scene_no_geom,
            'false': scene_false,
            'legitimate_no_geom': scene_legitimate_no_geom,
            'empty': scene_empty
        })

    return {
        'vnd': os.path.basename(json_path),
        'header_scene_count': header_scene_count,
        'scenes_parsed': len(scenes),
        'objcount_matches': objcount_matches,
        'objcount_mismatches': objcount_mismatches,
        'objcount_na': objcount_na,
        'total_objcount_declared': total_objcount_declared,
        'total_hotspots_parsed': total_hotspots_parsed,
        'total_hotspots_with_geom': total_hotspots_with_geom,
        'total_hotspots_no_geom': total_hotspots_no_geom,
        'total_false_hotspots': total_false_hotspots,
        'total_legitimate_no_geom': total_legitimate_no_geom,
        'total_empty_hotspots': total_empty_hotspots,
        'scene_analysis': scene_analysis,
        'legitimate_no_geom_examples': legitimate_no_geom_examples
    }

def main():
    """Analyse détaillée de tous les VND"""

    # Liste des VND
    vnd_dirs = [
        'couleurs1', 'allem', 'angleterre', 'autr', 'belge', 'danem',
        'ecosse', 'espa', 'finlan', 'france', 'grece', 'holl',
        'irland', 'italie', 'portu', 'suede', 'biblio', 'barre', 'frontal'
    ]

    results = []

    print("=" * 120)
    print("ANALYSE DÉTAILLÉE OBJCOUNT ET HOTSPOTS")
    print("=" * 120)
    print()

    for vnd_dir in vnd_dirs:
        json_files = list(Path(vnd_dir).glob('*.json'))
        if not json_files:
            continue

        json_path = str(json_files[0])

        print(f"Analyse {json_path}...", end=' ')
        try:
            analysis = analyze_vnd_detailed(json_path)
            results.append(analysis)
            print(f"✓ {analysis['scenes_parsed']} scènes, {analysis['total_hotspots_parsed']} hotspots")
        except Exception as e:
            print(f"❌ ERREUR: {e}")

    print()
    print("=" * 120)
    print("1. SCÈNES: HEADER vs PARSÉ")
    print("=" * 120)
    print()

    print(f"{'VND':<20} {'Header':>10} {'Parsé':>10} {'Différence':>12}")
    print("-" * 120)

    for r in results:
        header = r['header_scene_count']
        parsed = r['scenes_parsed']
        diff = parsed - header if header != 'N/A' else 'N/A'
        print(f"{r['vnd']:<20} {str(header):>10} {parsed:>10} {str(diff):>12}")

    print()
    print("=" * 120)
    print("2. OBJCOUNT: DÉCLARÉ vs PARSÉ")
    print("=" * 120)
    print()

    print(f"{'VND':<20} {'Déclaré':>10} {'Parsé':>10} {'Match':>8} {'Mismatch':>10} {'N/A':>8}")
    print("-" * 120)

    for r in results:
        print(f"{r['vnd']:<20} {r['total_objcount_declared']:>10} {r['total_hotspots_parsed']:>10} "
              f"{r['objcount_matches']:>8} {r['objcount_mismatches']:>10} {r['objcount_na']:>8}")

    print()
    print("=" * 120)
    print("3. HOTSPOTS: GÉOMÉTRIE")
    print("=" * 120)
    print()

    print(f"{'VND':<20} {'Total':>8} {'Avec Géo':>10} {'Sans Géo':>10} {'% Géo':>8}")
    print("-" * 120)

    for r in sorted(results, key=lambda x: x['total_hotspots_with_geom']/(x['total_hotspots_parsed'] or 1), reverse=True):
        geom_percent = (r['total_hotspots_with_geom'] / r['total_hotspots_parsed'] * 100) if r['total_hotspots_parsed'] > 0 else 0
        print(f"{r['vnd']:<20} {r['total_hotspots_parsed']:>8} {r['total_hotspots_with_geom']:>10} "
              f"{r['total_hotspots_no_geom']:>10} {geom_percent:>7.1f}%")

    print()
    print("=" * 120)
    print("4. CLASSIFICATION HOTSPOTS SANS GÉOMÉTRIE")
    print("=" * 120)
    print()

    print(f"{'VND':<20} {'Sans Géo':>10} {'Faux':>8} {'Légitimes':>12} {'Vides':>8}")
    print("-" * 120)

    for r in results:
        print(f"{r['vnd']:<20} {r['total_hotspots_no_geom']:>10} {r['total_false_hotspots']:>8} "
              f"{r['total_legitimate_no_geom']:>12} {r['total_empty_hotspots']:>8}")

    # Totaux
    total_no_geom = sum(r['total_hotspots_no_geom'] for r in results)
    total_false = sum(r['total_false_hotspots'] for r in results)
    total_legit = sum(r['total_legitimate_no_geom'] for r in results)
    total_empty = sum(r['total_empty_hotspots'] for r in results)

    print("-" * 120)
    print(f"{'TOTAL':<20} {total_no_geom:>10} {total_false:>8} {total_legit:>12} {total_empty:>8}")

    print()
    print("=" * 120)
    print("5. LES 2.9% RESTANTS (APRÈS ÉLIMINATION FAUX HOTSPOTS)")
    print("=" * 120)
    print()

    remaining_no_geom = total_no_geom - total_false
    total_hotspots = sum(r['total_hotspots_parsed'] for r in results)
    remaining_percent = (remaining_no_geom / total_hotspots * 100) if total_hotspots > 0 else 0

    print(f"Total hotspots sans géométrie: {total_no_geom}")
    print(f"  - Faux hotspots (Type A): {total_false} ({total_false/total_no_geom*100:.1f}%)")
    print(f"  - Hotspots légitimes sans géométrie: {total_legit} ({total_legit/total_no_geom*100:.1f}%)")
    print(f"  - Hotspots vides: {total_empty} ({total_empty/total_no_geom*100:.1f}%)")
    print()
    print(f"**Après élimination des faux hotspots**:")
    print(f"  - Hotspots restants sans géométrie: {remaining_no_geom}")
    print(f"  - % du total: {remaining_percent:.1f}%")
    print()

    # Exemples de hotspots légitimes sans géométrie
    print("=" * 120)
    print("6. EXEMPLES: HOTSPOTS LÉGITIMES SANS GÉOMÉTRIE")
    print("=" * 120)
    print()

    print("Ces hotspots ont des commandes NON-Type A (subtypes inconnus ou non classifiés):")
    print()

    example_count = 0
    for r in results:
        if r['legitimate_no_geom_examples']:
            print(f"### {r['vnd']}:")
            for ex in r['legitimate_no_geom_examples'][:3]:
                cmd_names = []
                for ct in ex['commands']:
                    param_preview = ct['param'][:40] if ct['param'] else ''
                    cmd_names.append(f"{ct['name']} ({ct['subtype']}): '{param_preview}'")
                print(f"  Scene {ex['scene_id']}, Hotspot #{ex['hotspot_id']}:")
                for cmd in cmd_names:
                    print(f"    - {cmd}")
                example_count += 1
                if example_count >= 10:
                    break
            print()
            if example_count >= 10:
                break

    if total_legit == 0:
        print("Aucun hotspot légitime sans géométrie détecté.")
        print()
        print("**Conclusion**: Les 2.9% restants sont probablement:")
        print("  1. Hotspots vides (anomalies parsing)")
        print("  2. Hotspots avec commandes non reconnues")
        print("  3. Hotspots légitimes mais structure inhabituelle")
    else:
        print(f"**{total_legit} hotspots légitimes sans géométrie détectés**")
        print("Ces hotspots ont des commandes avec subtypes non documentés.")

    print()
    print("=" * 120)
    print("RÉSUMÉ FINAL")
    print("=" * 120)
    print()

    total_scenes_header = sum(r['header_scene_count'] for r in results if r['header_scene_count'] != 'N/A')
    total_scenes_parsed = sum(r['scenes_parsed'] for r in results)

    print(f"**Scènes**:")
    print(f"  - Header déclare: {total_scenes_header} scènes principales")
    print(f"  - Parser détecte: {total_scenes_parsed} scènes totales")
    print(f"  - Différence: +{total_scenes_parsed - total_scenes_header} scènes (système, empty, toolbar, etc.)")
    print()

    total_objcount = sum(r['total_objcount_declared'] for r in results)
    total_parsed = sum(r['total_hotspots_parsed'] for r in results)

    print(f"**Hotspots**:")
    print(f"  - objCount déclare: {total_objcount} hotspots")
    print(f"  - Parser détecte: {total_parsed} hotspots")
    print(f"  - Différence: {total_parsed - total_objcount} (gap recovery)")
    print()

    print(f"**Géométrie**:")
    total_with_geom = sum(r['total_hotspots_with_geom'] for r in results)
    print(f"  - Avec géométrie: {total_with_geom} ({total_with_geom/total_parsed*100:.1f}%)")
    print(f"  - Sans géométrie: {total_no_geom} ({total_no_geom/total_parsed*100:.1f}%)")
    print()

    print(f"**Classification sans géométrie**:")
    print(f"  - Faux hotspots (Type A): {total_false} ({total_false/total_no_geom*100:.1f}% des sans géo)")
    print(f"  - Légitimes: {total_legit} ({total_legit/total_no_geom*100:.1f}%)")
    print(f"  - Vides: {total_empty} ({total_empty/total_no_geom*100:.1f}%)")
    print()

    print(f"**Après Parser Type-Aware**:")
    print(f"  - Hotspots totaux: {total_parsed - total_false} (−{total_false} faux)")
    print(f"  - Avec géométrie: {total_with_geom} ({total_with_geom/(total_parsed-total_false)*100:.1f}%)")
    print(f"  - Sans géométrie: {remaining_no_geom} ({remaining_percent:.1f}%)")
    print()

    # Sauvegarder résultats
    output_file = 'objcount_detailed_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Résultats sauvegardés dans: {output_file}")
    print()

if __name__ == '__main__':
    main()
