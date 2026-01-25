#!/usr/bin/env python3
"""
Validation VND - Structure confirmée par pseudo-code
"""
import struct
import json
import sys

def validate_vnd(vnd_path, json_path=None):
    """Valide structure VND"""
    
    with open(vnd_path, 'rb') as f:
        data = f.read(5000)
    
    print(f"=== VALIDATION {vnd_path} ===\n")
    
    # Validation structure connue (d'après analyse hex)
    # Config commence à offset 78 dans danem.vnd
    
    # Chercher config (largeur 640 ou 800)
    config_offset = None
    for i in range(50, 100):
        val = struct.unpack('<I', data[i:i+4])[0]
        if val == 640 or val == 800:
            config_offset = i
            break
    
    if not config_offset:
        print("❌ Config non trouvée")
        return None
    
    print(f"✓ Config trouvée à offset {config_offset}")
    config = struct.unpack('<5I', data[config_offset:config_offset+20])
    print(f"  Width:  {config[0]}")
    print(f"  Height: {config[1]}")
    print(f"  [2]:    {config[2]}")
    print(f"  [3]:    {config[3]}")
    print(f"  [4]:    {config[4]}")
    
    # Après config: Scene Count, EXIT_ID, INDEX_ID (3 × Word)
    meta_offset = config_offset + 20
    scene_count = struct.unpack('<H', data[meta_offset:meta_offset+2])[0]
    exit_id = struct.unpack('<H', data[meta_offset+2:meta_offset+4])[0]
    index_id = struct.unpack('<H', data[meta_offset+4:meta_offset+6])[0]
    
    print(f"\n✓ Scene Count (offset {meta_offset}): {scene_count}")
    print(f"✓ EXIT_ID (offset {meta_offset+2}): {exit_id}")
    print(f"✓ INDEX_ID (offset {meta_offset+4}): {index_id}")
    
    # Validation avec parser
    if json_path:
        try:
            with open(json_path) as f:
                parsed = json.load(f)
            
            print(f"\n=== COMPARAISON PARSER ===")
            parser_scenes = len(parsed['scenes'])
            print(f"Binaire: {scene_count} scènes")
            print(f"Parser:  {parser_scenes} scènes")
            if scene_count == parser_scenes:
                print("✅ MATCH!")
            else:
                print(f"❌ DIFFÉRENCE: {scene_count} vs {parser_scenes}")
        except:
            pass
    
    # Chercher première signature (scene marker)
    sigs_to_check = [0xFFFFFFF4, 0xFFFFFFDB]
    for sig in sigs_to_check:
        pos = data.find(struct.pack('<I', sig))
        if pos != -1:
            print(f"\n✓ Signature 0x{sig:08x} à offset {pos}")
            # objCount 2 bytes avant
            if pos >= 2:
                obj_count = struct.unpack('<H', data[pos-2:pos])[0]
                print(f"  objCount (scène 0): {obj_count}")
            break
    
    return {
        'config_offset': config_offset,
        'scene_count': scene_count,
        'exit_id': exit_id,
        'index_id': index_id
    }

if __name__ == '__main__':
    # Test sur danem et belge
    for vnd in ['danem/danem.vnd', 'belge/belge.vnd']:
        try:
            result = validate_vnd(vnd, vnd + '.parsed.json')
            print()
        except Exception as e:
            print(f"❌ Erreur sur {vnd}: {e}\n")
