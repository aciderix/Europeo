#!/usr/bin/env python3
"""
Parser Type-Aware FINAL - Test complet sur tous les VND
Reclassifie les hotspots en éliminant les faux (Commands Type A uniquement)
"""

import json
from pathlib import Path
from typing import Dict, List, Any

# Commands Type A - Tous les subtypes connus qui ne devraient PAS créer de hotspots
COMMAND_TYPE_A = {
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

# Subtypes système validés (légitimes sans géométrie)
SYSTEM_SUBTYPES = {
    0x07: 'HOTSPOT',      # Zones scriptées
    0x0B: 'PLAYWAV',      # Audio
    0x16: 'SET_VAR',      # Variables
    0x19: 'INVALIDATE',   # Rafraîchissement
    0x20: 'UPDATE',       # Mise à jour
}

def classify_hotspot(hotspot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classifie un hotspot selon logique Type-Aware:
    - VALID: Hotspot légitime (avec géométrie OU commandes système)
    - FALSE: Faux hotspot (sans géométrie + uniquement Commands Type A)
    - EMPTY: Hotspot vide (anomalie)
    """

    geometry = hotspot.get('geometry', {})
    point_count = geometry.get('pointCount', 0)
    has_geometry = point_count > 0

    commands = hotspot.get('commands', [])

    # Analyser commandes
    has_type_a_only = True
    has_system_cmd = False
    has_other_cmd = False

    for cmd in commands:
        subtype = cmd.get('subtype', -1)

        if subtype in SYSTEM_SUBTYPES:
            has_system_cmd = True
            has_type_a_only = False
        elif subtype not in COMMAND_TYPE_A:
            has_other_cmd = True
            has_type_a_only = False
        # else: c'est Type A

    # Classification
    if has_geometry:
        # Hotspot avec géométrie = toujours VALID
        classification = 'VALID'
        reason = 'Has geometry'
    elif len(commands) == 0:
        # Pas de géométrie, pas de commandes = EMPTY (anomalie)
        classification = 'EMPTY'
        reason = 'No geometry, no commands'
    elif has_type_a_only:
        # Pas de géométrie, uniquement Type A = FALSE (faux hotspot)
        classification = 'FALSE'
        reason = 'No geometry, only Type A commands'
    elif has_system_cmd or has_other_cmd:
        # Pas de géométrie mais commandes système/autres = VALID (système)
        classification = 'VALID'
        reason = 'System commands (PLAYWAV, SET_VAR, etc.)'
    else:
        # Cas bizarre
        classification = 'UNKNOWN'
        reason = 'Unknown case'

    return {
        'classification': classification,
        'reason': reason,
        'has_geometry': has_geometry,
        'point_count': point_count,
        'command_count': len(commands),
        'has_system_cmd': has_system_cmd,
        'has_type_a_only': has_type_a_only
    }

def analyze_vnd_type_aware(json_path: str) -> Dict[str, Any]:
    """Analyse un VND avec logique Type-Aware"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get('scenes', [])

    # Compteurs
    total_hotspots = 0
    valid_hotspots = 0
    false_hotspots = 0
    empty_hotspots = 0

    valid_with_geom = 0
    valid_system = 0

    false_examples = []
    system_examples = []

    for scene in scenes:
        hotspots = scene.get('hotspots', [])

        for h_idx, hotspot in enumerate(hotspots):
            total_hotspots += 1

            result = classify_hotspot(hotspot)

            if result['classification'] == 'VALID':
                valid_hotspots += 1
                if result['has_geometry']:
                    valid_with_geom += 1
                else:
                    valid_system += 1
                    if len(system_examples) < 5:
                        system_examples.append({
                            'scene_id': scene.get('sceneId', -1),
                            'hotspot_id': h_idx,
                            'reason': result['reason']
                        })

            elif result['classification'] == 'FALSE':
                false_hotspots += 1
                if len(false_examples) < 5:
                    # Récupérer types de commandes
                    cmd_types = []
                    for cmd in hotspot.get('commands', []):
                        st = cmd.get('subtype', -1)
                        name = COMMAND_TYPE_A.get(st, f'Type_{st}')
                        cmd_types.append(f'{name}({st})')

                    false_examples.append({
                        'scene_id': scene.get('sceneId', -1),
                        'hotspot_id': h_idx,
                        'commands': ', '.join(cmd_types[:3])
                    })

            elif result['classification'] == 'EMPTY':
                empty_hotspots += 1

    return {
        'vnd': Path(json_path).parent.name,
        'total_hotspots': total_hotspots,
        'valid_hotspots': valid_hotspots,
        'valid_with_geom': valid_with_geom,
        'valid_system': valid_system,
        'false_hotspots': false_hotspots,
        'empty_hotspots': empty_hotspots,
        'false_examples': false_examples,
        'system_examples': system_examples
    }

def main():
    """Test parser Type-Aware sur tous les VND"""

    vnd_dirs = [
        'couleurs1', 'allem', 'autr', 'belge', 'danem',
        'ecosse', 'espa', 'finlan', 'france', 'grece', 'holl',
        'irland', 'italie', 'portu', 'suede', 'biblio', 'barre', 'frontal'
    ]

    results = []

    print("=" * 120)
    print("PARSER TYPE-AWARE - TEST FINAL SUR TOUS LES VND")
    print("=" * 120)
    print()
    print("Légende:")
    print("  - VALID: Hotspots légitimes (géométrie OU commandes système)")
    print("  - FALSE: Faux hotspots (sans géométrie + uniquement Commands Type A)")
    print("  - EMPTY: Hotspots vides (anomalies)")
    print()

    for vnd_dir in vnd_dirs:
        json_files = list(Path(vnd_dir).glob('*.json'))
        if not json_files:
            continue

        json_path = str(json_files[0])

        print(f"Analyse {vnd_dir}...", end=' ')
        try:
            result = analyze_vnd_type_aware(json_path)
            results.append(result)
            print(f"✓ {result['total_hotspots']} hotspots → {result['valid_hotspots']} VALID, {result['false_hotspots']} FALSE")
        except Exception as e:
            print(f"❌ ERREUR: {e}")

    print()
    print("=" * 120)
    print("RÉSULTATS COMPARATIFS: AVANT vs APRÈS")
    print("=" * 120)
    print()

    # Tableau comparatif
    print(f"{'VND':<15} {'Total':>7} {'AVANT':>15} {'APRÈS':>15} {'Faux':>7} {'Vides':>7} {'Amélioration':>12}")
    print(f"{'':15} {'':7} {'(% Géo)':>15} {'(% Valid)':>15} {'':>7} {'':>7}")
    print("-" * 120)

    for r in sorted(results, key=lambda x: x['false_hotspots'], reverse=True):
        total = r['total_hotspots']
        valid = r['valid_hotspots']
        false_hs = r['false_hotspots']
        empty = r['empty_hotspots']

        # AVANT = hotspots avec géométrie seulement
        geom_only = r['valid_with_geom']
        before_pct = (geom_only / total * 100) if total > 0 else 0

        # APRÈS = hotspots VALID (géométrie + système)
        after_pct = (valid / total * 100) if total > 0 else 0

        improvement = after_pct - before_pct

        print(f"{r['vnd']:<15} {total:>7} {before_pct:>7.1f}% ({geom_only:>3}) "
              f"{after_pct:>7.1f}% ({valid:>3}) {false_hs:>7} {empty:>7} "
              f"{improvement:>+6.1f}%")

    print("-" * 120)

    # Totaux
    total_all = sum(r['total_hotspots'] for r in results)
    total_valid = sum(r['valid_hotspots'] for r in results)
    total_geom = sum(r['valid_with_geom'] for r in results)
    total_system = sum(r['valid_system'] for r in results)
    total_false = sum(r['false_hotspots'] for r in results)
    total_empty = sum(r['empty_hotspots'] for r in results)

    before_pct_all = (total_geom / total_all * 100) if total_all > 0 else 0
    after_pct_all = (total_valid / total_all * 100) if total_all > 0 else 0
    improvement_all = after_pct_all - before_pct_all

    print(f"{'TOTAL':<15} {total_all:>7} {before_pct_all:>7.1f}% ({total_geom:>3}) "
          f"{after_pct_all:>7.1f}% ({total_valid:>3}) {total_false:>7} {total_empty:>7} "
          f"{improvement_all:>+6.1f}%")

    print()
    print("=" * 120)
    print("ANALYSE DÉTAILLÉE")
    print("=" * 120)
    print()

    print(f"**AVANT (Parser actuel)**:")
    print(f"  Total hotspots: {total_all}")
    print(f"  Avec géométrie: {total_geom} ({before_pct_all:.1f}%)")
    print(f"  Sans géométrie: {total_all - total_geom} ({100 - before_pct_all:.1f}%)")
    print()

    print(f"**APRÈS (Parser Type-Aware)**:")
    print(f"  Total hotspots VALID: {total_valid}")
    print(f"    - Avec géométrie: {total_geom} ({total_geom/total_valid*100:.1f}%)")
    print(f"    - Système (PLAYWAV, SET_VAR, etc.): {total_system} ({total_system/total_valid*100:.1f}%)")
    print(f"  Faux hotspots éliminés: {total_false} ({total_false/total_all*100:.1f}%)")
    print(f"  Anomalies (vides): {total_empty} ({total_empty/total_all*100:.1f}%)")
    print()

    print(f"**AMÉLIORATION GLOBALE**: {before_pct_all:.1f}% → {after_pct_all:.1f}% ({improvement_all:+.1f}%)")
    print()

    # VND parfaits
    perfect = [r for r in results if r['false_hotspots'] == 0 and r['empty_hotspots'] == 0]
    if perfect:
        print(f"✅ **VND PARFAITS** (0 faux hotspots, 0 anomalies): {len(perfect)}")
        for r in perfect:
            print(f"   - {r['vnd']}: {r['valid_hotspots']}/{r['total_hotspots']} VALID "
                  f"({r['valid_with_geom']} géométrie + {r['valid_system']} système)")
        print()

    # Top problématiques
    problematic = [r for r in results if r['false_hotspots'] > 10]
    if problematic:
        print(f"🔴 **VND PROBLÉMATIQUES** (>10 faux hotspots): {len(problematic)}")
        for r in sorted(problematic, key=lambda x: x['false_hotspots'], reverse=True):
            pct_false = r['false_hotspots'] / r['total_hotspots'] * 100
            print(f"   - {r['vnd']}: {r['false_hotspots']} faux ({pct_false:.1f}%)")

            # Afficher exemples
            if r['false_examples']:
                for ex in r['false_examples'][:2]:
                    print(f"      Scene {ex['scene_id']}, Hotspot #{ex['hotspot_id']}: {ex['commands']}")
        print()

    # Hotspots système
    system_total = sum(r['valid_system'] for r in results)
    if system_total > 0:
        print(f"🔧 **HOTSPOTS SYSTÈME** (légitimes sans géométrie): {system_total}")
        vnd_with_system = [r for r in results if r['valid_system'] > 0]
        for r in sorted(vnd_with_system, key=lambda x: x['valid_system'], reverse=True)[:5]:
            print(f"   - {r['vnd']}: {r['valid_system']} hotspots système")
            for ex in r['system_examples'][:2]:
                print(f"      Scene {ex['scene_id']}, Hotspot #{ex['hotspot_id']}: {ex['reason']}")
        print()

    # Sauvegarder résultats
    output_file = 'type_aware_final_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Résultats sauvegardés dans: {output_file}")
    print()

if __name__ == '__main__':
    main()
