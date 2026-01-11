#!/usr/bin/env python3
"""
VND Deep Decoder
================

Analyse approfondie des structures binaires Little Endian dans les fichiers VND.
Focus sur:
- Types de records (1-100+)
- Structures de scènes
- Associations événements/hotspots
"""

import struct
import sys
from collections import defaultdict


def read_uint32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<I', data, offset)[0]


def read_int32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<i', data, offset)[0]


def read_uint16(data: bytes, offset: int) -> int:
    if offset + 2 > len(data):
        return 0
    return struct.unpack_from('<H', data, offset)[0]


def hexdump(data: bytes, offset: int, length: int) -> str:
    """Generate hexdump from offset"""
    result = []
    for i in range(length):
        if offset + i >= len(data):
            break
        result.append(f"{data[offset + i]:02x}")
    return ' '.join(result)


def extract_string(data: bytes, offset: int, max_len: int = 100) -> str:
    """Extract printable string"""
    result = []
    for i in range(max_len):
        if offset + i >= len(data):
            break
        b = data[offset + i]
        if b == 0:
            break
        if 32 <= b <= 126:
            result.append(chr(b))
        else:
            break
    return ''.join(result)


def find_all_record_separators(data: bytes) -> list:
    """Find all 01 00 00 00 markers with context"""
    separators = []
    pattern = b'\x01\x00\x00\x00'
    pos = 0
    while True:
        pos = data.find(pattern, pos)
        if pos == -1:
            break

        # Read values after separator
        val1 = read_uint32(data, pos + 4)  # Length or type
        val2 = read_uint32(data, pos + 8)  # Subtype

        separators.append({
            'offset': pos,
            'val1': val1,
            'val2': val2
        })
        pos += 1

    return separators


def analyze_record_types(data: bytes) -> dict:
    """Categorize all record types found"""
    separators = find_all_record_separators(data)

    type_examples = defaultdict(list)

    for sep in separators:
        val1 = sep['val1']
        val2 = sep['val2']

        # Skip clearly wrong patterns (huge values)
        if val1 > 10000 or val2 > 10000:
            continue

        # Check if there's text after the header
        text_offset = sep['offset'] + 12
        text = extract_string(data, text_offset, 60)

        # Check for coordinates pattern after header
        has_coords = False
        coord_check_offset = sep['offset'] + 12
        if coord_check_offset + 16 <= len(data):
            x1 = read_int32(data, coord_check_offset)
            y1 = read_int32(data, coord_check_offset + 4)
            x2 = read_int32(data, coord_check_offset + 8)
            y2 = read_int32(data, coord_check_offset + 12)
            if -100 <= x1 <= 800 and -100 <= y1 <= 600 and -100 <= x2 <= 800 and -100 <= y2 <= 600:
                has_coords = True

        record = {
            'offset': sep['offset'],
            'length': val1,
            'type': val2,
            'text': text[:50],
            'has_coords': has_coords,
            'hex': hexdump(data, sep['offset'], 24)
        }

        # Categorize by type (val2)
        if val2 < 100 and len(type_examples[val2]) < 5:
            type_examples[val2].append(record)

    return type_examples


def find_scene_boundaries(data: bytes) -> list:
    """Find scene definition boundaries"""
    scenes = []

    # Look for "scene " text pattern
    pos = 0
    while True:
        pos = data.find(b'scene ', pos)
        if pos == -1:
            break

        # Extract scene number
        text = extract_string(data, pos + 6, 20)
        scene_num = ''.join(c for c in text if c.isdigit() or c.isalpha())[:10]

        # Look backwards for record separator
        sep_offset = None
        for i in range(16, 100, 4):
            check_pos = pos - i
            if check_pos >= 0 and data[check_pos:check_pos+4] == b'\x01\x00\x00\x00':
                sep_offset = check_pos
                break

        scenes.append({
            'text_offset': pos,
            'scene_id': scene_num,
            'separator_offset': sep_offset,
            'context_before': hexdump(data, max(0, pos - 20), 20)
        })

        pos += 1

    return scenes


def find_event_markers(data: bytes) -> list:
    """Find EV_ONCLICK, EV_ONFOCUS markers"""
    events = []

    event_patterns = [
        (b'EV_ONCLICK', 'ONCLICK'),
        (b'EV_ONFOCUS', 'ONFOCUS'),
        (b'EV_ONINIT', 'ONINIT'),
        (b'EV_AFTERINIT', 'AFTERINIT')
    ]

    for pattern, name in event_patterns:
        pos = 0
        while True:
            pos = data.find(pattern, pos)
            if pos == -1:
                break

            # Look for associated command
            text_after = extract_string(data, pos + len(pattern), 100)

            events.append({
                'offset': pos,
                'type': name,
                'text_after': text_after[:60],
                'context_before': hexdump(data, max(0, pos - 16), 16)
            })

            pos += 1

    return events


def find_hotspot_structures(data: bytes) -> list:
    """Find complete hotspot definitions with polygons"""
    hotspots = []

    pos = 0
    while True:
        pos = data.find(b'hotspot ', pos)
        if pos == -1:
            break

        # Extract hotspot definition
        line_end = data.find(b'\x00', pos)
        if line_end == -1:
            line_end = pos + 100

        line = data[pos:min(line_end, pos + 200)].decode('latin-1', errors='replace')

        # Look for polygon data after the text
        # Pattern: [name] 00 00 00 [type:u32] 00 00 00 [count:u32] 00 00 00 [coords...]
        search_start = pos + len(line)

        # Find potential point count (3-30 range)
        found_polygon = None
        for offset in range(search_start, min(search_start + 50, len(data) - 40)):
            potential_count = read_uint32(data, offset)
            if 3 <= potential_count <= 30:
                # Validate as polygon
                coords = []
                valid = True
                for i in range(potential_count):
                    x = read_int32(data, offset + 4 + i * 8)
                    y = read_int32(data, offset + 4 + i * 8 + 4)
                    if not (-100 <= x <= 800 and -100 <= y <= 600):
                        valid = False
                        break
                    coords.append((x, y))

                if valid:
                    found_polygon = {
                        'count': potential_count,
                        'coords': coords,
                        'offset': offset
                    }
                    break

        hotspots.append({
            'text_offset': pos,
            'definition': line.strip()[:80],
            'polygon': found_polygon
        })

        pos += 1

    return hotspots


def analyze_binary_patterns(data: bytes) -> dict:
    """Statistical analysis of binary patterns"""

    # Analyze 4-byte aligned values
    value_positions = defaultdict(list)
    for i in range(0, len(data) - 3, 4):
        val = read_uint32(data, i)
        if val < 100:  # Focus on small values (types)
            value_positions[val].append(i)

    # Find common value sequences
    sequences = defaultdict(int)
    for i in range(0, len(data) - 11, 4):
        seq = (read_uint32(data, i), read_uint32(data, i + 4), read_uint32(data, i + 8))
        if all(v < 100 for v in seq):
            sequences[seq] += 1

    return {
        'value_counts': {k: len(v) for k, v in value_positions.items()},
        'common_sequences': sorted(sequences.items(), key=lambda x: -x[1])[:20]
    }


def decode_complete_structure(filepath: str):
    """Main decoder with complete analysis"""
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"=" * 80)
    print(f"VND DEEP DECODER - {filepath}")
    print(f"Size: {len(data)} bytes")
    print(f"=" * 80)

    # 1. Record Types
    print("\n" + "=" * 80)
    print("RECORD TYPES (by subtype value)")
    print("=" * 80)

    type_examples = analyze_record_types(data)
    for type_id in sorted(type_examples.keys()):
        examples = type_examples[type_id]
        print(f"\n--- Type {type_id} ({len(examples)} examples) ---")
        for ex in examples[:3]:
            print(f"  [0x{ex['offset']:04x}] len={ex['length']:3d} text=\"{ex['text'][:40]}\"")
            print(f"    hex: {ex['hex']}")

    # 2. Scene Boundaries
    print("\n" + "=" * 80)
    print("SCENE DEFINITIONS")
    print("=" * 80)

    scenes = find_scene_boundaries(data)
    print(f"\nFound {len(scenes)} scene references")
    for scene in scenes[:20]:
        print(f"  [0x{scene['text_offset']:04x}] scene {scene['scene_id']}")
        if scene['separator_offset']:
            print(f"    separator at 0x{scene['separator_offset']:04x}")
        print(f"    before: {scene['context_before']}")

    # 3. Event Markers
    print("\n" + "=" * 80)
    print("EVENT MARKERS")
    print("=" * 80)

    events = find_event_markers(data)
    print(f"\nFound {len(events)} event markers")
    for event in events[:15]:
        print(f"  [0x{event['offset']:04x}] {event['type']}")
        print(f"    after: \"{event['text_after'][:50]}\"")
        print(f"    before: {event['context_before']}")

    # 4. Hotspot Structures
    print("\n" + "=" * 80)
    print("HOTSPOT STRUCTURES")
    print("=" * 80)

    hotspots = find_hotspot_structures(data)
    print(f"\nFound {len(hotspots)} hotspot definitions")
    for hs in hotspots[:15]:
        print(f"\n  [0x{hs['text_offset']:04x}] {hs['definition'][:60]}")
        if hs['polygon']:
            poly = hs['polygon']
            print(f"    Polygon at 0x{poly['offset']:04x}: {poly['count']} points")
            print(f"    Coords: {poly['coords'][:4]}...")

    # 5. Binary Patterns
    print("\n" + "=" * 80)
    print("BINARY PATTERN ANALYSIS")
    print("=" * 80)

    patterns = analyze_binary_patterns(data)

    print("\nMost common small values (0-99):")
    sorted_counts = sorted(patterns['value_counts'].items(), key=lambda x: -x[1])
    for val, count in sorted_counts[:25]:
        print(f"  {val:3d}: {count:5d} occurrences")

    print("\nCommon 3-value sequences:")
    for seq, count in patterns['common_sequences'][:10]:
        print(f"  {seq}: {count} occurrences")

    # 6. Detailed structure at key offsets
    print("\n" + "=" * 80)
    print("DETAILED BYTE ANALYSIS AT KEY OFFSETS")
    print("=" * 80)

    # First scene
    if scenes:
        scene = scenes[0]
        print(f"\nFirst scene 'scene {scene['scene_id']}' at 0x{scene['text_offset']:04x}")
        start = max(0, scene['text_offset'] - 40)
        print("Bytes before:")
        for i in range(0, 40, 16):
            offset = start + i
            hex_str = hexdump(data, offset, 16)
            # Try to interpret as uint32s
            vals = [read_uint32(data, offset + j) for j in range(0, 16, 4)]
            print(f"  0x{offset:04x}: {hex_str}")
            print(f"         u32: {vals}")

    # First hotspot with polygon
    hotspots_with_poly = [h for h in hotspots if h['polygon']]
    if hotspots_with_poly:
        hs = hotspots_with_poly[0]
        print(f"\nFirst hotspot with polygon at 0x{hs['text_offset']:04x}")
        print(f"Definition: {hs['definition'][:60]}")
        poly = hs['polygon']
        print(f"\nPolygon structure at 0x{poly['offset']:04x}:")
        print(f"  Point count: {poly['count']}")
        print(f"  Raw bytes: {hexdump(data, poly['offset'], 40)}")
        print(f"  Coordinates: {poly['coords']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vnd_deep_decoder.py <file.vnd>")
        sys.exit(1)

    decode_complete_structure(sys.argv[1])
