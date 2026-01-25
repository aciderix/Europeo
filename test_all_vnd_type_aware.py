#!/usr/bin/env python3
"""
Test parser Type-Aware sur TOUS les VND (19 fichiers)
Compare résultats avec parser actuel
"""

import struct
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# ============================================================================
# CONSTANTES
# ============================================================================

VND_SIGNATURES = [
    0xFFFFFFDB,  # couleurs1
    0xFFFFFFF4,  # danem, belge
    0xFFFFFFF5,  # allem
    0xFFFFFFB7,  # angleterre
    0xFFFFFFE4,  # france
    0xFFFFFFE2,  # italie
    0xFFFFFFE8,  # belge (autre)
    0xFFFFFFD9,  # autre
]

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

# Records Type B (type_id connus)
RECORD_TYPES_B = {
    0x00: 'Metadata',
    0x01: 'SceneRef',
    0x02: 'ClickableZone',
    0x03: 'Score',
    0x04: 'Unknown04',
    0x05: 'Unknown05',
    0x06: 'Unknown06',
    0x07: 'VarDef',
    0x08: 'Unknown08',
}

# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class CommandA:
    """Command Type A"""
    subtype: int
    subtype_name: str
    param: str
    size: int
    offset: int

@dataclass
class RecordB:
    """Record Type B"""
    type_id: int
    type_name: str
    value: int
    param: int
    string: str
    size: int
    offset: int

@dataclass
class ParsedHotspot:
    """Hotspot parsé"""
    hotspot_id: int
    cursor_id: int
    point_count: int
    has_geometry: bool
    commands: int
    offset: int

@dataclass
class ParsedScene:
    """Scène parsée avec Type-Aware"""
    scene_id: int
    offset: int
    has_signature: bool
    signature: Optional[int]
    file_count: int
    files: List[str]
    obj_count: Optional[int]
    hotspots: List[ParsedHotspot]
    hotspots_no_geom: int
    commands_a: List[CommandA]
    records_b: List[RecordB]
    gap_size: int
    scene_type: str

@dataclass
class VndAnalysis:
    """Analyse complète d'un VND"""
    filename: str
    total_scenes: int
    scenes_with_signature: int
    scenes_without_signature: int
    total_hotspots: int
    hotspots_with_geometry: int
    hotspots_without_geometry: int
    geometry_percent: float
    total_commands_a: int
    total_records_b: int
    total_gap_bytes: int
    scenes: List[ParsedScene]

# ============================================================================
# PARSER TYPE-AWARE
# ============================================================================

def read_pascal_string(data: bytes, offset: int) -> Tuple[str, int]:
    """Lit une string Pascal (4 bytes length + data)"""
    if offset + 4 > len(data):
        return "", 0
    str_len = struct.unpack('<I', data[offset:offset+4])[0]
    if str_len > 1000 or offset + 4 + str_len > len(data):
        return "", 0
    try:
        string = data[offset+4:offset+4+str_len].decode('cp1252', errors='ignore')
        return string, 4 + str_len
    except:
        return "", 0

def try_parse_command_a(data: bytes, offset: int) -> Optional[CommandA]:
    """Tente de parser un Command Type A"""
    if offset + 8 > len(data):
        return None

    try:
        subtype = struct.unpack('<I', data[offset:offset+4])[0]

        # Vérifier si c'est un subtype connu
        if subtype not in COMMAND_SUBTYPES_A:
            return None

        str_len = struct.unpack('<I', data[offset+4:offset+8])[0]
        if str_len > 1000 or offset + 8 + str_len > len(data):
            return None

        param = data[offset+8:offset+8+str_len].decode('cp1252', errors='ignore')

        return CommandA(
            subtype=subtype,
            subtype_name=COMMAND_SUBTYPES_A[subtype],
            param=param,
            size=8 + str_len,
            offset=offset
        )
    except:
        return None

def try_parse_record_b(data: bytes, offset: int) -> Optional[RecordB]:
    """Tente de parser un Record Type B"""
    if offset + 16 > len(data):
        return None

    try:
        value = struct.unpack('<I', data[offset:offset+4])[0]
        type_id = struct.unpack('<I', data[offset+4:offset+8])[0]
        param = struct.unpack('<I', data[offset+8:offset+12])[0]
        str_len = struct.unpack('<I', data[offset+12:offset+16])[0]

        # Vérifier validité
        if type_id > 0x69:  # Max type_id documenté
            return None
        if str_len > 1000 or offset + 16 + str_len > len(data):
            return None

        string = data[offset+16:offset+16+str_len].decode('cp1252', errors='ignore')

        type_name = RECORD_TYPES_B.get(type_id, f'Unknown{type_id:02X}')

        return RecordB(
            type_id=type_id,
            type_name=type_name,
            value=value,
            param=param,
            string=string,
            size=16 + str_len,
            offset=offset
        )
    except:
        return None

def parse_hotspot(data: bytes, offset: int, hotspot_id: int) -> Optional[ParsedHotspot]:
    """Parse un hotspot (153 bytes)"""
    if offset + 153 > len(data):
        return None

    try:
        # Lire cursor_id (offset +100)
        cursor_id = struct.unpack('<I', data[offset+100:offset+104])[0]

        # Lire point_count (offset +104)
        point_count = struct.unpack('<I', data[offset+104:offset+108])[0]

        # Valider point_count
        if point_count > 20:
            return None

        # Compter commandes (offset +26, structure complexe)
        command_count = 0
        # Simplification: vérifier si des bytes non-nuls existent
        cmd_region = data[offset+26:offset+100]
        if any(b != 0 for b in cmd_region):
            command_count = 1  # Au moins une commande

        return ParsedHotspot(
            hotspot_id=hotspot_id,
            cursor_id=cursor_id,
            point_count=point_count,
            has_geometry=point_count > 0,
            commands=command_count,
            offset=offset
        )
    except:
        return None

def find_signatures(data: bytes) -> List[Tuple[int, int]]:
    """Trouve toutes les signatures 0xFFFFFFxx dans le fichier"""
    signatures = []
    for i in range(len(data) - 4):
        value = struct.unpack('<I', data[i:i+4])[0]
        if (value & 0xFFFFFF00) == 0xFFFFFF00:
            signatures.append((i, value))
    return signatures

def parse_gap_type_aware(data: bytes, start: int, end: int) -> Tuple[List[CommandA], List[RecordB]]:
    """Parse un gap avec logique Type-Aware"""
    commands_a = []
    records_b = []

    offset = start
    while offset < end:
        # Essayer Command Type A
        cmd = try_parse_command_a(data, offset)
        if cmd:
            commands_a.append(cmd)
            offset += cmd.size
            continue

        # Essayer Record Type B
        rec = try_parse_record_b(data, offset)
        if rec:
            records_b.append(rec)
            offset += rec.size
            continue

        # Aucune structure reconnue, avancer de 1 byte
        offset += 1

    return commands_a, records_b

def parse_vnd_type_aware(filepath: str) -> VndAnalysis:
    """Parse un VND avec logique Type-Aware"""
    with open(filepath, 'rb') as f:
        data = f.read()

    filename = os.path.basename(filepath)
    scenes = []

    # Trouver toutes les signatures
    all_signatures = find_signatures(data)

    scene_id = 0
    offset = 0

    # Chercher Scene 0 (global_vars) si elle existe
    # Pattern: file table avec >50 fichiers avant première signature
    if all_signatures:
        first_sig_offset = all_signatures[0][0]
        # Scanner de 0x60 à première signature
        for i in range(0x60, min(first_sig_offset, 0x200), 4):
            str_val, str_size = read_pascal_string(data, i)
            if str_val == "VNFILE" or "vnresmod" in str_val.lower():
                # Compter fichiers
                file_offset = i
                files = []
                while file_offset < first_sig_offset:
                    f_str, f_size = read_pascal_string(data, file_offset)
                    if f_size == 0 or not f_str:
                        break
                    files.append(f_str)
                    file_offset += f_size
                    if len(files) > 300:  # Limite sécurité
                        break

                if len(files) > 50:  # Seuil global_vars
                    scenes.append(ParsedScene(
                        scene_id=scene_id,
                        offset=i,
                        has_signature=False,
                        signature=None,
                        file_count=len(files),
                        files=files[:10],  # Limiter output
                        obj_count=None,
                        hotspots=[],
                        hotspots_no_geom=0,
                        commands_a=[],
                        records_b=[],
                        gap_size=0,
                        scene_type='global_vars'
                    ))
                    scene_id += 1
                    offset = file_offset
                break

    # Parser scènes avec signatures
    for sig_offset, sig_value in all_signatures:
        if sig_offset < offset:
            continue

        # Lire config (5 int32 après signature)
        if sig_offset + 24 > len(data):
            continue

        config = struct.unpack('<5I', data[sig_offset+4:sig_offset+24])

        # Lire objCount (Word après config)
        if sig_offset + 26 > len(data):
            continue
        obj_count = struct.unpack('<H', data[sig_offset+24:sig_offset+26])[0]

        # Chercher file table avant signature
        file_table_offset = sig_offset - 100
        files = []
        for i in range(max(0, sig_offset - 500), sig_offset, 4):
            f_str, f_size = read_pascal_string(data, i)
            if f_str and f_size > 0:
                test_files = []
                test_offset = i
                while test_offset < sig_offset:
                    tf, ts = read_pascal_string(data, test_offset)
                    if not tf or ts == 0:
                        break
                    test_files.append(tf)
                    test_offset += ts
                    if len(test_files) > 100:
                        break

                if test_files and test_offset <= sig_offset + 10:
                    files = test_files
                    file_table_offset = i
                    break

        # Parser hotspots (après objCount)
        hotspots = []
        hotspot_offset = sig_offset + 26
        for h_id in range(obj_count):
            hotspot = parse_hotspot(data, hotspot_offset, h_id)
            if hotspot:
                hotspots.append(hotspot)
            hotspot_offset += 153

        # Calculer gap jusqu'à prochaine signature
        next_sig_offset = len(data)
        for next_sig, _ in all_signatures:
            if next_sig > sig_offset:
                next_sig_offset = next_sig
                break

        gap_start = hotspot_offset
        gap_end = next_sig_offset
        gap_size = max(0, gap_end - gap_start)

        # Parser gap avec Type-Aware
        commands_a, records_b = parse_gap_type_aware(data, gap_start, gap_end)

        # Déterminer type de scène
        scene_type = 'game'
        if len(files) == 1:
            if files[0] == 'Empty':
                scene_type = 'empty'
            elif files[0] == 'Toolbar':
                scene_type = 'toolbar'
            elif 'fleche.cur' in files[0]:
                scene_type = 'toolbar'
        if any('vnoption' in f for f in files):
            scene_type = 'options'
        if any('credit' in f.lower() for f in files):
            scene_type = 'credits'
        if any('perdu' in f or 'gagne' in f for f in files):
            scene_type = 'game_over'

        hotspots_no_geom = sum(1 for h in hotspots if not h.has_geometry)

        scenes.append(ParsedScene(
            scene_id=scene_id,
            offset=sig_offset,
            has_signature=True,
            signature=sig_value,
            file_count=len(files),
            files=files[:5],  # Limiter output
            obj_count=obj_count,
            hotspots=hotspots,
            hotspots_no_geom=hotspots_no_geom,
            commands_a=commands_a,
            records_b=records_b,
            gap_size=gap_size,
            scene_type=scene_type
        ))
        scene_id += 1
        offset = hotspot_offset

    # Statistiques
    total_hotspots = sum(len(s.hotspots) for s in scenes)
    hotspots_with_geom = sum(sum(1 for h in s.hotspots if h.has_geometry) for s in scenes)
    hotspots_without_geom = total_hotspots - hotspots_with_geom
    geom_percent = (hotspots_with_geom / total_hotspots * 100) if total_hotspots > 0 else 0.0

    total_commands_a = sum(len(s.commands_a) for s in scenes)
    total_records_b = sum(len(s.records_b) for s in scenes)
    total_gap_bytes = sum(s.gap_size for s in scenes)

    scenes_with_sig = sum(1 for s in scenes if s.has_signature)
    scenes_without_sig = len(scenes) - scenes_with_sig

    return VndAnalysis(
        filename=filename,
        total_scenes=len(scenes),
        scenes_with_signature=scenes_with_sig,
        scenes_without_signature=scenes_without_sig,
        total_hotspots=total_hotspots,
        hotspots_with_geometry=hotspots_with_geom,
        hotspots_without_geometry=hotspots_without_geom,
        geometry_percent=geom_percent,
        total_commands_a=total_commands_a,
        total_records_b=total_records_b,
        total_gap_bytes=total_gap_bytes,
        scenes=scenes
    )

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Teste tous les VND avec parser Type-Aware"""

    # Liste des VND à tester
    vnd_files = [
        'couleurs1/couleurs1.vnd',
        'allem/allem.vnd',
        'angleterre/angleterre.vnd',
        'autr/autr.vnd',
        'belge/belge.vnd',
        'danem/danem.vnd',
        'ecosse/ecosse.vnd',
        'espa/espa.vnd',
        'finlan/finlan.vnd',
        'france/france.vnd',
        'grece/grece.vnd',
        'holl/holl.vnd',
        'irland/irland.vnd',
        'italie/italie.vnd',
        'portu/portu.vnd',
        'suede/suede.vnd',
        'biblio/biblio.vnd',
        'barre/barre.vnd',
        'frontal/start.vnd',
    ]

    results = []

    print("=" * 80)
    print("TEST PARSER TYPE-AWARE - TOUS LES VND")
    print("=" * 80)
    print()

    for vnd_path in vnd_files:
        if not os.path.exists(vnd_path):
            print(f"⚠️  {vnd_path} - FICHIER INTROUVABLE")
            continue

        print(f"Parsing {vnd_path}...", end=' ')
        try:
            analysis = parse_vnd_type_aware(vnd_path)
            results.append(analysis)
            print(f"✓ {analysis.total_scenes} scènes, {analysis.total_hotspots} hotspots ({analysis.geometry_percent:.1f}% géométrie)")
        except Exception as e:
            print(f"❌ ERREUR: {e}")

    print()
    print("=" * 80)
    print("RÉSULTATS GLOBAUX")
    print("=" * 80)
    print()

    # Tableau récapitulatif
    print(f"{'VND':<20} {'Scènes':>7} {'Hotspots':>9} {'% Géo':>7} {'Cmds A':>8} {'Recs B':>8} {'Gap KB':>8}")
    print("-" * 80)

    for r in sorted(results, key=lambda x: x.geometry_percent, reverse=True):
        print(f"{r.filename:<20} {r.total_scenes:>7} {r.total_hotspots:>9} "
              f"{r.geometry_percent:>6.1f}% {r.total_commands_a:>8} {r.total_records_b:>8} "
              f"{r.total_gap_bytes/1024:>7.1f} KB")

    print("-" * 80)

    # Totaux
    total_scenes = sum(r.total_scenes for r in results)
    total_hotspots = sum(r.total_hotspots for r in results)
    total_with_geom = sum(r.hotspots_with_geometry for r in results)
    total_without_geom = sum(r.hotspots_without_geometry for r in results)
    total_commands_a = sum(r.total_commands_a for r in results)
    total_records_b = sum(r.total_records_b for r in results)

    overall_geom_percent = (total_with_geom / total_hotspots * 100) if total_hotspots > 0 else 0.0

    print(f"{'TOTAL':<20} {total_scenes:>7} {total_hotspots:>9} "
          f"{overall_geom_percent:>6.1f}% {total_commands_a:>8} {total_records_b:>8}")

    print()
    print("=" * 80)
    print("ANALYSE DÉTAILLÉE")
    print("=" * 80)
    print()

    print(f"Total scènes parsées: {total_scenes}")
    print(f"Total hotspots: {total_hotspots}")
    print(f"  - Avec géométrie: {total_with_geom} ({total_with_geom/total_hotspots*100:.1f}%)")
    print(f"  - Sans géométrie: {total_without_geom} ({total_without_geom/total_hotspots*100:.1f}%)")
    print()
    print(f"Total Commands Type A détectés: {total_commands_a}")
    print(f"Total Records Type B détectés: {total_records_b}")
    print()

    # VND parfaits (100% géométrie)
    perfect = [r for r in results if r.geometry_percent == 100.0]
    if perfect:
        print(f"✅ VND PARFAITS (100% géométrie): {len(perfect)}")
        for r in perfect:
            print(f"   - {r.filename}: {r.total_hotspots} hotspots")
        print()

    # VND problématiques (<90% géométrie)
    problematic = [r for r in results if r.geometry_percent < 90.0]
    if problematic:
        print(f"🔴 VND PROBLÉMATIQUES (<90% géométrie): {len(problematic)}")
        for r in sorted(problematic, key=lambda x: x.geometry_percent):
            print(f"   - {r.filename}: {r.geometry_percent:.1f}% ({r.hotspots_without_geometry}/{r.total_hotspots} sans géo)")
        print()

    # Sauvegarder résultats JSON
    output_file = 'type_aware_all_vnd_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([asdict(r) for r in results], f, indent=2, ensure_ascii=False)

    print(f"Résultats sauvegardés dans: {output_file}")
    print()

if __name__ == '__main__':
    main()
