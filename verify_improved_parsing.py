#!/usr/bin/env python3
"""
Vérifie que le parsing amélioré a bien appliqué les nouvelles classifications
"""

import json
from pathlib import Path
from collections import Counter

VND_FILES = [
    'couleurs1/couleurs1.vnd.parsed.json',
    'allem/allem.vnd.parsed.json',
    'autr/autr.vnd.parsed.json',
    'belge/belge.vnd.parsed.json',
    'danem/danem.vnd.parsed.json',
    'ecosse/ecosse.vnd.parsed.json',
    'espa/espa.vnd.parsed.json',
    'finlan/finlan.vnd.parsed.json',
    'france/france.vnd.parsed.json',
    'grece/grece.vnd.parsed.json',
    'holl/holl.vnd.parsed.json',
    'irland/irland.vnd.parsed.json',
    'italie/italie.vnd.parsed.json',
    'portu/portu.vnd.parsed.json',
    'suede/suede.vnd.parsed.json',
    'biblio/biblio.vnd.parsed.json',
    'barre/barre.vnd.parsed.json',
    'frontal/start.vnd.parsed.json',
]

def analyze_json(json_path: str):
    """Analyse un JSON parsé"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get('scenes', [])

    # Compter par type
    type_counts = Counter()
    toolbar_scenes = []
    transition_scenes = []
    unknown_scenes = []

    for scene in scenes:
        scene_type = scene.get('sceneType', 'unknown')
        type_counts[scene_type] += 1

        # Collecter exemples
        if scene_type == 'toolbar':
            toolbar_scenes.append({
                'id': scene.get('id', -1),
                'files': [f.get('filename', '') for f in scene.get('files', [])][:3]
            })

        if scene_type == 'transition':
            transition_scenes.append({
                'id': scene.get('id', -1),
                'offset': f"0x{scene.get('offset', 0):X}"
            })

        if scene_type == 'unknown':
            unknown_scenes.append({
                'id': scene.get('id', -1),
                'files': [f.get('filename', '') for f in scene.get('files', [])][:3]
            })

    return {
        'vnd': Path(json_path).parent.name,
        'total_scenes': len(scenes),
        'type_counts': dict(type_counts),
        'toolbar_scenes': toolbar_scenes,
        'transition_scenes': transition_scenes,
        'unknown_scenes': unknown_scenes
    }

def main():
    """Vérifie le parsing amélioré"""

    print("=" * 100)
    print("VÉRIFICATION PARSING AMÉLIORÉ")
    print("=" * 100)
    print()

    all_results = []
    all_types = Counter()

    for json_path in VND_FILES:
        if not Path(json_path).exists():
            continue

        result = analyze_json(json_path)
        all_results.append(result)

        # Agréger types
        for scene_type, count in result['type_counts'].items():
            all_types[scene_type] += count

    # Afficher distribution globale
    print("DISTRIBUTION GLOBALE DES TYPES DE SCÈNES")
    print("-" * 100)
    print()

    total_scenes = sum(all_types.values())

    for scene_type, count in sorted(all_types.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_scenes * 100
        print(f"  {scene_type:<15} {count:>4} ({pct:>5.1f}%)")

    print(f"\n  {'TOTAL':<15} {total_scenes:>4}\n")

    # Scènes toolbar (améliorations fleche.cur)
    print("=" * 100)
    print("SCÈNES TOOLBAR (fleche.cur → toolbar)")
    print("=" * 100)
    print()

    toolbar_total = all_types.get('toolbar', 0)
    print(f"Total scènes toolbar: {toolbar_total}")
    print()

    toolbar_with_fleche = 0
    for r in all_results:
        if r['toolbar_scenes']:
            print(f"{r['vnd']}: {len(r['toolbar_scenes'])} scènes toolbar")
            for scene in r['toolbar_scenes'][:3]:
                files_str = ', '.join(scene['files'])
                print(f"  - Scene #{scene['id']}: {files_str}")
                if 'fleche.cur' in files_str:
                    toolbar_with_fleche += 1
            print()

    print(f"Scènes toolbar avec fleche.cur: {toolbar_with_fleche}")
    print()

    # Scènes transition (nouveau type)
    print("=" * 100)
    print("SCÈNES TRANSITION (nouveau type détecté)")
    print("=" * 100)
    print()

    transition_total = all_types.get('transition', 0)
    print(f"Total scènes transition: {transition_total}")
    print()

    for r in all_results:
        if r['transition_scenes']:
            print(f"{r['vnd']}: {len(r['transition_scenes'])} scènes transition")
            for scene in r['transition_scenes'][:3]:
                print(f"  - Scene #{scene['id']} @ {scene['offset']}")
            print()

    # Scènes unknown (devrait être 0 maintenant)
    print("=" * 100)
    print("SCÈNES UNKNOWN (devrait être 0 après améliorations)")
    print("=" * 100)
    print()

    unknown_total = all_types.get('unknown', 0)

    if unknown_total == 0:
        print("✅ PARFAIT! Aucune scène unknown détectée.")
    else:
        print(f"⚠️  {unknown_total} scènes unknown restantes:")
        print()

        for r in all_results:
            if r['unknown_scenes']:
                print(f"{r['vnd']}: {len(r['unknown_scenes'])} scènes unknown")
                for scene in r['unknown_scenes'][:3]:
                    files_str = ', '.join(scene['files'])
                    print(f"  - Scene #{scene['id']}: {files_str}")
                print()

    print()

    # Comparaison avant/après
    print("=" * 100)
    print("COMPARAISON AVANT/APRÈS")
    print("=" * 100)
    print()

    print("AVANT (investigation):")
    print("  - unknown: 23 scènes (fleche.cur non classifiées)")
    print("  - transition: 0 scènes (non détectées)")
    print("  - toolbar: ~17 scènes (sans fleche.cur)")
    print()

    print("APRÈS (parsing amélioré):")
    print(f"  - unknown: {unknown_total} scènes")
    print(f"  - transition: {transition_total} scènes (+{transition_total})")
    print(f"  - toolbar: {toolbar_total} scènes (+{toolbar_with_fleche} fleche.cur)")
    print()

    if unknown_total == 0 and transition_total > 0 and toolbar_total > 23:
        print("✅ AMÉLIORATIONS APPLIQUÉES AVEC SUCCÈS!")
    else:
        print("⚠️  Vérifier les classifications")

    print()

if __name__ == '__main__':
    main()
