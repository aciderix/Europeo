#!/usr/bin/env python3
"""
Investigation complète:
1. 3 VND avec -1 scène (belge, ecosse, italie)
2. Classification des 23 scènes "unknown"
3. Vérification VND avec +N scènes (biblio, irland, autr, suede)
"""

import json
import struct
from pathlib import Path
from typing import Dict, List, Any, Optional

def analyze_scene_type(scene: Dict[str, Any]) -> str:
    """Analyse et améliore la classification d'une scène"""

    files = scene.get('files', [])
    hotspots = scene.get('hotspots', [])
    obj_count = scene.get('objCount', 'N/A')
    has_signature = scene.get('config', {}).get('foundSignature') is not None

    # Convertir files en strings si ce sont des dicts
    files_str = []
    for f in files:
        if isinstance(f, dict):
            files_str.append(f.get('name', ''))
        else:
            files_str.append(str(f))

    # Empty slot
    if len(files_str) == 1 and files_str[0] == 'Empty':
        return 'empty'

    # Global vars (Scene 0)
    if len(files_str) > 50:
        return 'global_vars'

    # Options
    if any('vnoption' in f.lower() for f in files_str if f):
        return 'options'

    # Toolbar
    if len(files_str) == 1 and 'Toolbar' in files_str[0]:
        return 'toolbar'

    if len(files_str) == 1 and 'fleche.cur' in files_str[0]:
        return 'toolbar'

    # Credits
    if any('credit' in f.lower() for f in files_str if f):
        return 'credits'

    # Game over
    if any('perdu' in f.lower() or 'gagne' in f.lower() for f in files_str if f):
        return 'game_over'

    # Intro/Outro
    if any('intro' in f.lower() or 'title' in f.lower() for f in files_str if f):
        return 'intro'

    if any('outro' in f.lower() or 'ending' in f.lower() for f in files_str if f):
        return 'outro'

    # Menu
    if any('menu' in f.lower() for f in files_str if f):
        return 'menu'

    # Map/Navigation
    if any('map' in f.lower() or 'carte' in f.lower() for f in files_str if f):
        return 'map'

    # Transition
    if len(files_str) == 0 and len(hotspots) == 0:
        return 'transition'

    # Game (défaut)
    return 'game'

def find_missing_scene(vnd_path: str, json_path: str, header_count: int, parsed_count: int) -> Dict[str, Any]:
    """Cherche la scène manquante dans un VND"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get('scenes', [])

    # Chercher signatures dans le binaire
    with open(vnd_path, 'rb') as f:
        vnd_data = f.read()

    signatures_in_binary = []
    for i in range(len(vnd_data) - 4):
        value = struct.unpack('<I', vnd_data[i:i+4])[0]
        if (value & 0xFFFFFF00) == 0xFFFFFF00:
            signatures_in_binary.append((i, value))

    # Signatures parsées
    signatures_parsed = []
    for scene in scenes:
        sig = scene.get('config', {}).get('foundSignature')
        if sig:
            offset = scene.get('offset', 0)
            signatures_parsed.append((offset, sig))

    # Chercher signatures manquantes
    missing_signatures = []
    for bin_offset, bin_sig in signatures_in_binary:
        found = False
        for parsed_offset, parsed_sig in signatures_parsed:
            # Tolérance ±100 bytes
            if abs(bin_offset - parsed_offset) < 100:
                found = True
                break

        if not found:
            missing_signatures.append((bin_offset, bin_sig))

    # Chercher empty slots non détectés
    empty_pattern = bytes([0x05, 0x00, 0x00, 0x00, 0x45, 0x6D, 0x70, 0x74, 0x79])  # "Empty"
    empty_slots_binary = []
    pos = 0
    while pos < len(vnd_data):
        pos = vnd_data.find(empty_pattern, pos)
        if pos == -1:
            break
        empty_slots_binary.append(pos)
        pos += 1

    empty_slots_parsed = sum(1 for s in scenes if s.get('files', []) == ['Empty'])

    return {
        'vnd': Path(vnd_path).stem,
        'header_count': header_count,
        'parsed_count': parsed_count,
        'missing': header_count - parsed_count,
        'signatures_in_binary': len(signatures_in_binary),
        'signatures_parsed': len(signatures_parsed),
        'missing_signatures': missing_signatures,
        'empty_slots_binary': len(empty_slots_binary),
        'empty_slots_parsed': empty_slots_parsed,
        'scenes': scenes
    }

def reclassify_unknown_scenes(json_path: str) -> Dict[str, Any]:
    """Reclassifie les scènes unknown"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get('scenes', [])

    unknown_scenes = []
    reclassified = {}

    for idx, scene in enumerate(scenes):
        current_type = scene.get('sceneType', 'unknown')

        if current_type == 'unknown':
            # Reclassifier
            new_type = analyze_scene_type(scene)

            unknown_scenes.append({
                'index': idx,
                'offset': f"0x{scene.get('offset', 0):X}",
                'old_type': current_type,
                'new_type': new_type,
                'files': scene.get('files', [])[:5],
                'hotspots': len(scene.get('hotspots', [])),
                'obj_count': scene.get('objCount', 'N/A')
            })

            reclassified[new_type] = reclassified.get(new_type, 0) + 1

    return {
        'vnd': Path(json_path).parent.name,
        'total_unknown': len(unknown_scenes),
        'reclassified': reclassified,
        'scenes': unknown_scenes
    }

def analyze_extra_scenes(json_path: str, header_count: int) -> Dict[str, Any]:
    """Analyse les scènes supplémentaires dans les VND avec +N"""

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scenes = data.get('scenes', [])

    # Classifier toutes les scènes
    type_distribution = {}
    for scene in scenes:
        scene_type = analyze_scene_type(scene)
        type_distribution[scene_type] = type_distribution.get(scene_type, 0) + 1

    # Identifier scènes supplémentaires (au-delà du header)
    extra_scenes = []

    # Si on a plus de scènes que le header, les dernières sont probablement extras
    if len(scenes) > header_count:
        # Mais attention: le header compte les "game" principales
        # Donc on liste toutes les scènes non-game comme "extras"
        for idx, scene in enumerate(scenes):
            scene_type = analyze_scene_type(scene)
            if scene_type != 'game':
                extra_scenes.append({
                    'index': idx,
                    'type': scene_type,
                    'files': scene.get('files', [])[:3],
                    'offset': f"0x{scene.get('offset', 0):X}"
                })

    return {
        'vnd': Path(json_path).parent.name,
        'header_count': header_count,
        'parsed_count': len(scenes),
        'extra_count': len(scenes) - header_count,
        'type_distribution': type_distribution,
        'extra_scenes': extra_scenes[:10]  # Limiter à 10 exemples
    }

def main():
    """Investigation complète"""

    print("=" * 120)
    print("INVESTIGATION COMPLÈTE - VND AVEC DIFFÉRENCES")
    print("=" * 120)
    print()

    # 1. VND avec -1 scène
    print("=" * 120)
    print("1. VND AVEC -1 SCÈNE (MANQUANTE)")
    print("=" * 120)
    print()

    missing_vnd = [
        ('belge', 28),
        ('ecosse', 42),
        ('italie', 36)
    ]

    for vnd_name, header_count in missing_vnd:
        vnd_path = f"{vnd_name}/{vnd_name}.vnd"
        json_path = f"{vnd_name}/{vnd_name}.vnd.parsed.json"

        if not Path(vnd_path).exists() or not Path(json_path).exists():
            print(f"⚠️ {vnd_name}: Fichiers manquants")
            continue

        print(f"### {vnd_name}.vnd")
        result = find_missing_scene(vnd_path, json_path, header_count, header_count - 1)

        print(f"Header déclare: {result['header_count']} scènes")
        print(f"Parser trouve: {result['parsed_count']} scènes")
        print(f"**Manquant: {result['missing']} scène**")
        print()

        print(f"Signatures dans binaire: {result['signatures_in_binary']}")
        print(f"Signatures parsées: {result['signatures_parsed']}")
        print()

        if result['missing_signatures']:
            print(f"⚠️ **{len(result['missing_signatures'])} signatures manquantes détectées**:")
            for offset, sig in result['missing_signatures'][:5]:
                print(f"  - Offset 0x{offset:X}: Signature 0x{sig:08X}")
            print()
        else:
            print("✅ Toutes les signatures ont été parsées")
            print()

        print(f"Empty slots dans binaire: {result['empty_slots_binary']}")
        print(f"Empty slots parsés: {result['empty_slots_parsed']}")

        if result['empty_slots_binary'] != result['empty_slots_parsed']:
            diff = result['empty_slots_binary'] - result['empty_slots_parsed']
            print(f"⚠️ **{diff} empty slots manquants**")
        else:
            print("✅ Tous les empty slots détectés")

        print()
        print("-" * 120)
        print()

    # 2. Classification scènes unknown
    print("=" * 120)
    print("2. RECLASSIFICATION DES SCÈNES UNKNOWN")
    print("=" * 120)
    print()

    vnd_dirs = [
        'couleurs1', 'allem', 'autr', 'belge', 'danem',
        'ecosse', 'espa', 'finlan', 'france', 'grece', 'holl',
        'irland', 'italie', 'portu', 'suede', 'biblio', 'barre', 'frontal'
    ]

    all_reclassified = {}
    total_unknown = 0

    for vnd_dir in vnd_dirs:
        json_path = f"{vnd_dir}/{vnd_dir}.vnd.parsed.json"
        if not Path(json_path).exists():
            continue

        result = reclassify_unknown_scenes(json_path)

        if result['total_unknown'] > 0:
            total_unknown += result['total_unknown']
            print(f"### {result['vnd']}")
            print(f"Scènes unknown: {result['total_unknown']}")
            print(f"Reclassification:")
            for new_type, count in sorted(result['reclassified'].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {new_type}: {count}")

            # Afficher exemples
            for scene in result['scenes'][:3]:
                print(f"    Scene #{scene['index']} @ {scene['offset']}: {scene['old_type']} → {scene['new_type']}")
                print(f"      Files: {scene['files']}")
            print()

            # Agréger
            for new_type, count in result['reclassified'].items():
                all_reclassified[new_type] = all_reclassified.get(new_type, 0) + count

    print("-" * 120)
    print(f"**TOTAL: {total_unknown} scènes unknown reclassifiées**")
    print()
    print("Distribution après reclassification:")
    for new_type, count in sorted(all_reclassified.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {new_type}: {count}")
    print()

    # 3. VND avec +N scènes
    print("=" * 120)
    print("3. VND AVEC +N SCÈNES (SUPPLÉMENTAIRES)")
    print("=" * 120)
    print()

    extra_vnd = [
        ('biblio', 0),
        ('irland', 3),
        ('autr', 24),
        ('suede', 2),
        ('couleurs1', 31)
    ]

    for vnd_name, header_count in extra_vnd:
        json_path = f"{vnd_name}/{vnd_name}.vnd.parsed.json"

        if not Path(json_path).exists():
            print(f"⚠️ {vnd_name}: JSON manquant")
            continue

        result = analyze_extra_scenes(json_path, header_count)

        print(f"### {result['vnd']}.vnd")
        print(f"Header: {result['header_count']}, Parsé: {result['parsed_count']} (+{result['extra_count']})")
        print()
        print("Distribution types:")
        for scene_type, count in sorted(result['type_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {scene_type}: {count}")
        print()

        if result['extra_scenes']:
            print(f"Exemples scènes supplémentaires (au-delà du header):")
            for scene in result['extra_scenes'][:5]:
                print(f"  - Scene #{scene['index']} @ {scene['offset']}: {scene['type']}")
                print(f"    Files: {scene['files']}")
        print()
        print("-" * 120)
        print()

    print("=" * 120)
    print("CONCLUSION")
    print("=" * 120)
    print()

    print("1. **VND avec -1 scène**: Investigation signatures + empty slots")
    print("2. **Scènes unknown**: Reclassification automatique effectuée")
    print("3. **VND avec +N scènes**: Distribution types analysée")
    print()

if __name__ == '__main__':
    main()
