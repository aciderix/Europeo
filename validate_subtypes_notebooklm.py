#!/usr/bin/env python3
"""
Validation des subtypes 7, 11, 22, 25, 32 avec données NotebookLM
+ Investigation des 2 hotspots vides
"""

import json
from pathlib import Path
from typing import Dict, List, Any

# Mapping NotebookLM
SUBTYPE_MAPPING = {
    7: {
        'name': 'HOTSPOT',
        'description': 'Définition zone cliquable (script)',
        'opcode': 'g',
        'record_type': 'Définitions de variables'
    },
    11: {
        'name': 'PLAYWAV',
        'description': 'Lecture audio WAV',
        'opcode': 'k',
        'record_type': 'Fichiers audio WAV'
    },
    22: {
        'name': 'SET_VAR',
        'description': 'Affectation variable (variable = valeur)',
        'opcode': 'v',
        'record_type': 'Chemins multimédias (vidéos AVI secondaires)'
    },
    25: {
        'name': 'INVALIDATE',
        'description': 'Rafraîchissement/invalidation affichage',
        'opcode': 'y',
        'record_type': 'Instructions conditionnelles if X then Y'
    },
    32: {
        'name': 'UPDATE',
        'description': 'Mise à jour état moteur/affichage',
        'opcode': 'update',
        'record_type': 'Actions set_var ou playtext'
    }
}

def analyze_subtype_usage(json_path: str) -> Dict[str, Any]:
    """Analyse l'utilisation des subtypes 7, 11, 22, 25, 32"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get('scenes', [])

    subtype_examples = {7: [], 11: [], 22: [], 25: [], 32: []}
    empty_hotspots = []

    for scene in scenes:
        scene_id = scene.get('sceneId', -1)
        hotspots = scene.get('hotspots', [])

        for h_idx, hotspot in enumerate(hotspots):
            geometry = hotspot.get('geometry', {})
            point_count = geometry.get('pointCount', 0)
            commands = hotspot.get('commands', [])

            # Chercher hotspots vides
            if point_count == 0 and len(commands) == 0:
                empty_hotspots.append({
                    'vnd': Path(json_path).parent.name,
                    'scene_id': scene_id,
                    'hotspot_id': h_idx,
                    'offset': hotspot.get('offset', 0)
                })

            # Chercher subtypes d'intérêt
            for cmd in commands:
                subtype = cmd.get('subtype', -1)
                if subtype in [7, 11, 22, 25, 32]:
                    param = cmd.get('param', '')

                    # Collecter contexte
                    other_commands = []
                    for c in commands:
                        if c != cmd:
                            s = c.get('subtype', -1)
                            other_commands.append({
                                'subtype': s,
                                'param': c.get('param', '')[:30]
                            })

                    subtype_examples[subtype].append({
                        'vnd': Path(json_path).parent.name,
                        'scene_id': scene_id,
                        'hotspot_id': h_idx,
                        'param': param,
                        'param_len': len(param),
                        'other_commands': other_commands[:3]  # Limiter contexte
                    })

    return {
        'vnd': Path(json_path).parent.name,
        'subtype_examples': subtype_examples,
        'empty_hotspots': empty_hotspots
    }

def main():
    """Validation subtypes et investigation hotspots vides"""

    vnd_dirs = [
        'couleurs1', 'allem', 'autr', 'belge', 'danem',
        'ecosse', 'espa', 'finlan', 'france', 'grece', 'holl',
        'irland', 'italie', 'portu', 'suede', 'biblio', 'barre', 'frontal'
    ]

    all_results = []

    for vnd_dir in vnd_dirs:
        json_files = list(Path(vnd_dir).glob('*.json'))
        if not json_files:
            continue

        json_path = str(json_files[0])
        result = analyze_subtype_usage(json_path)
        all_results.append(result)

    print("=" * 100)
    print("VALIDATION SUBTYPES 7, 11, 22, 25, 32 (NotebookLM)")
    print("=" * 100)
    print()

    # Agréger tous les exemples par subtype
    aggregated = {7: [], 11: [], 22: [], 25: [], 32: []}
    all_empty = []

    for r in all_results:
        for subtype in [7, 11, 22, 25, 32]:
            aggregated[subtype].extend(r['subtype_examples'][subtype])
        all_empty.extend(r['empty_hotspots'])

    # Analyser chaque subtype
    for subtype in [7, 11, 22, 25, 32]:
        mapping = SUBTYPE_MAPPING[subtype]
        examples = aggregated[subtype]

        print(f"### SUBTYPE {subtype} (0x{subtype:02X}) - {mapping['name']}")
        print(f"**Description**: {mapping['description']}")
        print(f"**Opcode**: {mapping['opcode']}")
        print(f"**Type enregistrement**: {mapping['record_type']}")
        print()
        print(f"**Occurrences détectées**: {len(examples)}")

        if examples:
            # Analyser paramètres
            params = [e['param'] for e in examples]
            empty_params = sum(1 for p in params if p == '')
            non_empty_params = sum(1 for p in params if p != '')

            print(f"  - Paramètres vides: {empty_params}")
            print(f"  - Paramètres non-vides: {non_empty_params}")
            print()

            # Distribution par VND
            vnd_counts = {}
            for e in examples:
                vnd_counts[e['vnd']] = vnd_counts.get(e['vnd'], 0) + 1

            print(f"**Distribution par VND**:")
            for vnd, count in sorted(vnd_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {vnd}: {count}×")
            print()

            # Exemples de paramètres
            print(f"**Exemples de paramètres**:")
            unique_params = list(set(params))[:10]
            for p in unique_params:
                if p:
                    print(f"  - '{p[:60]}'")
                else:
                    print(f"  - (vide)")
            print()

            # Contexte (autres commandes)
            print(f"**Contexte (autres commandes dans le hotspot)**:")
            for ex in examples[:3]:
                print(f"  {ex['vnd']} Scene {ex['scene_id']}, Hotspot #{ex['hotspot_id']}:")
                print(f"    Type {subtype}: '{ex['param'][:40]}'")
                for cmd in ex['other_commands']:
                    print(f"    + Type {cmd['subtype']}: '{cmd['param']}'")
                print()
        else:
            print("  → Aucune occurrence détectée")
            print()

        print("-" * 100)
        print()

    # Investigation hotspots vides
    print("=" * 100)
    print("INVESTIGATION: HOTSPOTS VIDES (ni géométrie ni commandes)")
    print("=" * 100)
    print()

    print(f"**Total détecté**: {len(all_empty)} hotspots vides")
    print()

    if all_empty:
        for empty in all_empty:
            print(f"### {empty['vnd']} - Scene {empty['scene_id']}, Hotspot #{empty['hotspot_id']}")
            print(f"Offset: 0x{empty['offset']:X}")
            print()

            # Lire le JSON pour plus de détails
            json_path = f"{empty['vnd']}/{empty['vnd']}.vnd.parsed.json"
            if Path(json_path).exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                scene = None
                for s in data.get('scenes', []):
                    if s.get('sceneId') == empty['scene_id']:
                        scene = s
                        break

                if scene:
                    print(f"**Scene #{empty['scene_id']} contexte**:")
                    print(f"  - Offset: 0x{scene.get('offset', 0):X}")
                    print(f"  - Type: {scene.get('sceneType', 'unknown')}")
                    print(f"  - Fichiers: {scene.get('files', [])[:5]}")
                    print(f"  - objCount: {scene.get('objCount', 'N/A')}")
                    print(f"  - Total hotspots: {len(scene.get('hotspots', []))}")
                    print()

                    # Afficher hotspot vide
                    hotspot = scene['hotspots'][empty['hotspot_id']]
                    print(f"**Hotspot #{empty['hotspot_id']} détails**:")
                    print(f"  - Index: {hotspot.get('index', -1)}")
                    print(f"  - Offset: 0x{hotspot.get('offset', 0):X}")
                    print(f"  - Geometry: {hotspot.get('geometry', {})}")
                    print(f"  - Commands: {hotspot.get('commands', [])}")
                    print()

            print("-" * 100)
            print()
    else:
        print("✅ Aucun hotspot vide détecté!")

    print()
    print("=" * 100)
    print("CONCLUSION")
    print("=" * 100)
    print()

    print("**Validation NotebookLM**:")
    print()
    for subtype in [7, 11, 22, 25, 32]:
        mapping = SUBTYPE_MAPPING[subtype]
        count = len(aggregated[subtype])
        if count > 0:
            status = "✅ VALIDÉ"
        else:
            status = "⚠️ Non observé"
        print(f"  {status} - Type {subtype} ({mapping['name']}): {count} occurrences")
    print()

    if len(all_empty) > 0:
        print(f"**Hotspots vides**: {len(all_empty)} détectés → Anomalies à investiguer")
    else:
        print(f"**Hotspots vides**: 0 → Aucune anomalie")

if __name__ == '__main__':
    main()
