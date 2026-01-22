#!/usr/bin/env python3

"""
VND Deep Decoder
================
Analyse approfondie des structures binaires Little Endian dans les fichiers VND.
UPDATED: Based on VND Binary Format Specification Rev. 2

Focus sur:
- Types de records (0-105)
- Structures de scènes
- Hotspots (Type 2 rectangles + Type 38/105 polygones)
- Association correcte Type 38 + Type 105
"""

import struct
import sys
from collections import defaultdict

# ... [keep existing helper methods] ...

def parse_type2_rectangles(data: bytes) -> list:
    """Find all Type 2 rectangular clickable zones - NEW

    Binary format: [02:u32] [x1:u32] [y1:u32] [x2:u32] [y2:u32]
    """
    rectangles = []
    pos = 0

    while pos < len(data) - 20:
        if read_uint32(data, pos) == 2:
            x1 = read_uint32(data, pos + 4)
            y1 = read_uint32(data, pos + 8)
            x2 = read_uint32(data, pos + 12)
            y2 = read_uint32(data, pos + 16)

            # Validate coordinates
            if (-100 <= x1 <= 2000 and -100 <= y1 <= 1000 and 
                -100 <= x2 <= 2000 and -100 <= y2 <= 1000):
                rectangles.append({
                    'offset': pos,
                    'x1': x1, 'y1': y1,
                    'x2': x2, 'y2': y2,
                    'width': x2 - x1,
                    'height': y2 - y1
                })
                pos += 20
                continue
        pos += 1

    return rectangles

def parse_type38_hotspots(data: bytes) -> list:
    """Find all Type 38 hotspot text definitions - NEW

    Format in record: [SEPARATOR:01] [LENGTH] [TYPE:38] [TEXT:"X Y W H layer name"]
    """
    hotspots = []
    separators = find_all_record_separators(data)

    for sep in separators:
        if sep['val2'] == 38:  # Type 38
            offset = sep['offset']
            length = sep['val1']

            # Extract text data
            text_offset = offset + 12
            if text_offset + length <= len(data):
                try:
                    text = data[text_offset:text_offset + length].decode('latin-1').strip('\x00')
                    parts = text.split(None, 5)

                    if len(parts) >= 6:
                        hotspots.append({
                            'offset': offset,
                            'x': int(parts[0]),
                            'y': int(parts[1]),
                            'width': int(parts[2]),
                            'height': int(parts[3]),
                            'layer': int(parts[4]),
                            'name': parts[5],
                            'text_end_offset': text_offset + length
                        })
                except (ValueError, UnicodeDecodeError):
                    pass

    return hotspots

def parse_type105_polygons(data: bytes) -> list:
    """Find all Type 105 polygon definitions - CORRECTED

    IMPORTANT: Type 105 has NO [length] field!
    Binary format: [TYPE:105] [COUNT:u32] [x1:i32][y1:i32]...[xN:i32][yN:i32]
    """
    polygons = []
    pos = 0

    while pos < len(data) - 12:
        type_marker = read_uint32(data, pos)

        if type_marker == 105:
            point_count = read_uint32(data, pos + 4)

            # Validate point count
            if 3 <= point_count <= 30:
                coords_size = point_count * 8
                if pos + 8 + coords_size <= len(data):
                    # Extract coordinates
                    coords = []
                    valid = True
                    offset_coords = pos + 8

                    for i in range(point_count):
                        x = read_int32(data, offset_coords + i * 8)
                        y = read_int32(data, offset_coords + i * 8 + 4)

                        # Validate screen coordinates
                        if not (-100 <= x <= 2000 and -100 <= y <= 1000):
                            valid = False
                            break

                        coords.append((x, y))

                    if valid:
                        polygons.append({
                            'offset': pos,
                            'point_count': point_count,
                            'coords': coords,
                            'end_offset': offset_coords + coords_size
                        })
                        pos = offset_coords + coords_size
                        continue

        pos += 1

    return polygons

def associate_hotspots_polygons(hotspots: list, polygons: list) -> list:
    """Associate Type 38 hotspots with Type 105 polygons - NEW

    Rule: A Type 105 polygon belongs to the Type 38 that IMMEDIATELY precedes it
    """
    associated = []

    for hotspot in hotspots:
        text_end = hotspot['text_end_offset']

        # Find polygon immediately after (within 50 bytes for padding)
        matching_polygon = None

        for polygon in polygons:
            if text_end <= polygon['offset'] <= text_end + 50:
                matching_polygon = polygon
                break

        associated.append({
            **hotspot,
            'polygon': matching_polygon
        })

    return associated

def analyze_record_types_detailed(data: bytes) -> dict:
    """Enhanced record type analysis with corrections from spec - UPDATED"""
    separators = find_all_record_separators(data)
    type_categorization = defaultdict(list)

    record_type_names = {
        0: "Metadata/Empty",
        1: "Primary Scene Reference",
        2: "Rectangular Clickable Zone",  # CORRECTED
        3: "Score/Value",
        5: "Game State (jeu)",
        6: "Scene Number",
        7: "Variable Definition",
        8: "Cancel/Activate State",
        9: "Occupied State",
        10: "Cursor/Rollover",
        11: "Audio WAV",
        12: "Audio WAV 2",
        15: "Block Structure",
        17: "Sound Effects (Path)",
        19: "Project Reference",
        20: "Video Home/Museum",
        21: "Video Departure",
        22: "Video Secondary Location",
        23: "Video Scene-specific",
        24: "Video Bibliothèque",
        26: "Font Definition",
        38: "Hotspot Text Definition",  # CORRECTED
        105: "Polygonal Clickable Zone"  # NEW
    }

    for sep in separators:
        record_type = sep['val2']
        if record_type in record_type_names and len(type_categorization[record_type]) < 3:
            text = extract_string(data, sep['offset'] + 12, 60)
            type_categorization[record_type].append({
                'offset': sep['offset'],
                'length': sep['val1'],
                'text': text,
                'name': record_type_names[record_type]
            })

    return dict(type_categorization)

def decode_complete_structure(filepath: str):
    """Main decoder with complete analysis - UPDATED"""
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"=" * 80)
    print(f"VND DEEP DECODER - {filepath}")
    print(f"Size: {len(data)} bytes")
    print(f"Based on VND Binary Format Specification Rev. 2")
    print(f"=" * 80)

    # 1. Type 2 Rectangles
    print("\n" + "=" * 80)
    print("TYPE 2 - RECTANGULAR CLICKABLE ZONES")
    print("=" * 80)
    rectangles = parse_type2_rectangles(data)
    print(f"\nFound {len(rectangles)} Type 2 rectangles")
    for rect in rectangles[:10]:
        print(f" [0x{rect['offset']:04x}] ({rect['x1']},{rect['y1']}) -> ({rect['x2']},{rect['y2']}) size={rect['width']}x{rect['height']}")

    # 2. Type 38 Hotspots
    print("\n" + "=" * 80)
    print("TYPE 38 - HOTSPOT TEXT DEFINITIONS")
    print("=" * 80)
    type38_hotspots = parse_type38_hotspots(data)
    print(f"\nFound {len(type38_hotspots)} Type 38 hotspot definitions")
    for hs in type38_hotspots[:10]:
        print(f" [0x{hs['offset']:04x}] {hs['x']},{hs['y']} {hs['width']}x{hs['height']} layer={hs['layer']} name=\"{hs['name'][:30]}\"")

    # 3. Type 105 Polygons
    print("\n" + "=" * 80)
    print("TYPE 105 - POLYGONAL CLICKABLE ZONES")
    print("=" * 80)
    polygons = parse_type105_polygons(data)
    print(f"\nFound {len(polygons)} Type 105 polygons")
    for poly in polygons[:10]:
        print(f" [0x{poly['offset']:04x}] {poly['point_count']} points: {poly['coords'][:3]}...")

    # 4. Association Type 38 + Type 105
    print("\n" + "=" * 80)
    print("ASSOCIATED HOTSPOTS (Type 38 + Type 105)")
    print("=" * 80)
    associated = associate_hotspots_polygons(type38_hotspots, polygons)
    with_polygon = [h for h in associated if h['polygon']]
    without_polygon = [h for h in associated if not h['polygon']]

    print(f"\nType 38 hotspots WITH polygon: {len(with_polygon)}")
    print(f"Type 38 hotspots WITHOUT polygon: {len(without_polygon)}")

    print("\nExamples with polygon:")
    for hs in with_polygon[:5]:
        print(f" [0x{hs['offset']:04x}] \"{hs['name'][:30]}\"")
        if hs['polygon']:
            print(f"    -> Polygon at 0x{hs['polygon']['offset']:04x}: {hs['polygon']['point_count']} points")

    # 5. Record Types Summary
    print("\n" + "=" * 80)
    print("RECORD TYPES SUMMARY (CORRECTED)")
    print("=" * 80)
    type_details = analyze_record_types_detailed(data)
    for type_id in sorted(type_details.keys()):
        examples = type_details[type_id]
        print(f"\nType {type_id:3d} - {examples[0]['name']}")
        for ex in examples[:2]:
            print(f"  [0x{ex['offset']:04x}] len={ex['length']:3d} text=\"{ex['text'][:40]}\"")

    # 6. Statistics
    print("\n" + "=" * 80)
    print("HOTSPOT STATISTICS")
    print("=" * 80)
    print(f"Type 2 rectangles: {len(rectangles)}")
    print(f"Type 38 hotspots: {len(type38_hotspots)}")
    print(f"  - With Type 105 polygon: {len(with_polygon)}")
    print(f"  - Without polygon: {len(without_polygon)}")
    print(f"Type 105 orphan polygons: {len(polygons) - len(with_polygon)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vnd_deep_decoder.py <file.vnd>")
        sys.exit(1)

    decode_complete_structure(sys.argv[1])
