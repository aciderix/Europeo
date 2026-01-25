#!/usr/bin/env python3
"""
Analyse le nombre de scènes annoncées dans le header VND vs parsées
"""

import struct
import json
from pathlib import Path
from typing import Dict, Any, Optional

def read_vnd_header(vnd_path: str) -> Optional[Dict[str, Any]]:
    """Lit le header d'un fichier VND pour extraire sceneCount"""

    try:
        with open(vnd_path, 'rb') as f:
            # Lire début du fichier
            data = f.read(200)

            # Trouver le config (devrait être à offset 78 normalement)
            # Mais peut varier selon la taille des strings de header

            # Chercher pattern Config (5 int32 consécutifs raisonnables)
            config_offset = None
            for i in range(50, 120, 4):
                if i + 20 > len(data):
                    break

                # Lire 5 int32
                values = struct.unpack('<5I', data[i:i+20])

                # Vérifier si c'est un config valide (width, height, ...)
                if 400 <= values[0] <= 1024 and 300 <= values[1] <= 768:
                    config_offset = i
                    break

            if not config_offset:
                return None

            # Lire config
            config = struct.unpack('<5I', data[config_offset:config_offset+20])

            # Scene Count devrait être à config_offset + 20
            scene_count_offset = config_offset + 20
            if scene_count_offset + 2 > len(data):
                return None

            scene_count = struct.unpack('<H', data[scene_count_offset:scene_count_offset+2])[0]

            # EXIT_ID à +22, INDEX_ID à +24
            exit_id = struct.unpack('<H', data[scene_count_offset+2:scene_count_offset+4])[0]
            index_id = struct.unpack('<H', data[scene_count_offset+4:scene_count_offset+6])[0]

            return {
                'config_offset': config_offset,
                'width': config[0],
                'height': config[1],
                'scene_count': scene_count,
                'exit_id': exit_id,
                'index_id': index_id
            }

    except Exception as e:
        return None

def analyze_scene_count_comparison(vnd_dir: str) -> Optional[Dict[str, Any]]:
    """Compare scene count header vs parsé"""

    # Trouver fichier VND
    vnd_files = list(Path(vnd_dir).glob('*.vnd'))
    if not vnd_files:
        return None

    vnd_path = str(vnd_files[0])

    # Lire header
    header = read_vnd_header(vnd_path)
    if not header:
        return None

    # Lire JSON parsé
    json_files = list(Path(vnd_dir).glob('*.json'))
    if not json_files:
        return None

    json_path = str(json_files[0])
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get('scenes', [])

    # Analyser types de scènes
    scene_types = {}
    for scene in scenes:
        scene_type = scene.get('sceneType', 'unknown')
        scene_types[scene_type] = scene_types.get(scene_type, 0) + 1

    header_count = header['scene_count']
    parsed_count = len(scenes)
    difference = parsed_count - header_count

    return {
        'vnd': vnd_dir,
        'header_scene_count': header_count,
        'parsed_scene_count': parsed_count,
        'difference': difference,
        'scene_types': scene_types,
        'width': header['width'],
        'height': header['height'],
        'exit_id': header['exit_id'],
        'index_id': header['index_id']
    }

def main():
    """Analyse tous les VND"""

    vnd_dirs = [
        'couleurs1', 'allem', 'autr', 'belge', 'danem',
        'ecosse', 'espa', 'finlan', 'france', 'grece', 'holl',
        'irland', 'italie', 'portu', 'suede', 'biblio', 'barre', 'frontal'
    ]

    results = []

    print("=" * 120)
    print("ANALYSE: NOMBRE DE SCÈNES - HEADER vs PARSÉ")
    print("=" * 120)
    print()

    for vnd_dir in vnd_dirs:
        if not Path(vnd_dir).exists():
            continue

        print(f"Analyse {vnd_dir}...", end=' ')
        result = analyze_scene_count_comparison(vnd_dir)

        if result:
            results.append(result)
            diff = result['difference']
            sign = '+' if diff >= 0 else ''
            print(f"✓ Header: {result['header_scene_count']}, Parsé: {result['parsed_scene_count']} ({sign}{diff})")
        else:
            print(f"⚠️ Échec lecture header")

    print()
    print("=" * 120)
    print("RÉSULTATS DÉTAILLÉS")
    print("=" * 120)
    print()

    # Tableau comparatif
    print(f"{'VND':<15} {'Header':>8} {'Parsé':>8} {'Diff':>6} {'Résolution':>12} {'EXIT_ID':>10} {'Types Scènes'}")
    print("-" * 120)

    for r in sorted(results, key=lambda x: abs(x['difference']), reverse=True):
        resolution = f"{r['width']}×{r['height']}"
        diff = r['difference']
        sign = '+' if diff >= 0 else ''

        # Top 3 types de scènes
        scene_types_sorted = sorted(r['scene_types'].items(), key=lambda x: x[1], reverse=True)
        types_str = ', '.join([f"{t}:{c}" for t, c in scene_types_sorted[:3]])

        print(f"{r['vnd']:<15} {r['header_scene_count']:>8} {r['parsed_scene_count']:>8} "
              f"{sign}{diff:>5} {resolution:>12} {r['exit_id']:>10} {types_str}")

    print()
    print("=" * 120)
    print("ANALYSE DES DIFFÉRENCES")
    print("=" * 120)
    print()

    # Grouper par type de différence
    exact_match = [r for r in results if r['difference'] == 0]
    more_parsed = [r for r in results if r['difference'] > 0]
    less_parsed = [r for r in results if r['difference'] < 0]

    print(f"**Match exact** (Header = Parsé): {len(exact_match)}")
    for r in exact_match:
        print(f"  - {r['vnd']}: {r['header_scene_count']} scènes")
    print()

    if more_parsed:
        print(f"**Plus de scènes parsées** (Parsé > Header): {len(more_parsed)}")
        for r in sorted(more_parsed, key=lambda x: x['difference'], reverse=True):
            print(f"  - {r['vnd']}: +{r['difference']} scènes parsées")
            print(f"    Header: {r['header_scene_count']}, Parsé: {r['parsed_scene_count']}")
            print(f"    Types: {dict(r['scene_types'])}")
        print()

    if less_parsed:
        print(f"**Moins de scènes parsées** (Parsé < Header): {len(less_parsed)}")
        for r in sorted(less_parsed, key=lambda x: x['difference']):
            print(f"  - {r['vnd']}: {r['difference']} scènes manquantes")
            print(f"    Header: {r['header_scene_count']}, Parsé: {r['parsed_scene_count']}")
            print(f"    Types: {dict(r['scene_types'])}")
        print()

    # Statistiques globales
    total_header = sum(r['header_scene_count'] for r in results)
    total_parsed = sum(r['parsed_scene_count'] for r in results)
    total_diff = total_parsed - total_header

    print("=" * 120)
    print("STATISTIQUES GLOBALES")
    print("=" * 120)
    print()

    print(f"Total scènes annoncées (header): {total_header}")
    print(f"Total scènes parsées: {total_parsed}")
    print(f"Différence globale: {total_diff:+d}")
    print()

    if total_diff > 0:
        print(f"**Scènes système détectées**: +{total_diff} scènes")
        print(f"  → Le parser détecte des scènes non comptées dans le header")
        print(f"  → Types probables: empty, toolbar, options, global_vars, credits, game_over")
    elif total_diff < 0:
        print(f"**Scènes manquantes**: {total_diff} scènes")
        print(f"  → Le parser ne détecte pas toutes les scènes annoncées")
        print(f"  → Possibles scènes filtrées ou parsing incomplet")
    else:
        print(f"✅ **Match parfait global**!")

    print()

    # Agréger tous les types de scènes
    all_scene_types = {}
    for r in results:
        for scene_type, count in r['scene_types'].items():
            all_scene_types[scene_type] = all_scene_types.get(scene_type, 0) + count

    print("**Distribution types de scènes (tous VND)**:")
    for scene_type, count in sorted(all_scene_types.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_parsed * 100
        print(f"  - {scene_type}: {count} ({pct:.1f}%)")
    print()

    # Sauvegarder résultats
    output_file = 'scene_count_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Résultats sauvegardés dans: {output_file}")
    print()

if __name__ == '__main__':
    main()
