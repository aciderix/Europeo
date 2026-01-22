#!/usr/bin/env python3
"""
VND Binary Data Analyzer
========================

Analyzes the binary structure of VND files to decode:
- Text commands with binary metadata
- Polygon coordinate arrays
- Scene/object type identifiers
- Record structures

The VND format mixes plaintext commands with Little Endian binary data.
"""

import struct
import sys
from pathlib import Path


def read_uint32(data: bytes, offset: int) -> int:
    """Read Little Endian 32-bit unsigned integer"""
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<I', data, offset)[0]


def read_int32(data: bytes, offset: int) -> int:
    """Read Little Endian 32-bit signed integer"""
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<i', data, offset)[0]


def read_uint16(data: bytes, offset: int) -> int:
    """Read Little Endian 16-bit unsigned integer"""
    if offset + 2 > len(data):
        return 0
    return struct.unpack_from('<H', data, offset)[0]


def is_printable_range(data: bytes, start: int, length: int) -> bool:
    """Check if a range contains printable ASCII"""
    if start + length > len(data):
        return False
    for i in range(length):
        b = data[start + i]
        if not (32 <= b <= 126 or b in [0, 9, 10, 13]):
            return False
    return True


def extract_string(data: bytes, offset: int, max_len: int = 256) -> str:
    """Extract null-terminated or fixed-length string"""
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


def analyze_record(data: bytes, offset: int) -> dict:
    """Analyze a potential record structure"""
    record = {
        'offset': offset,
        'fields': []
    }

    # Read potential length/type fields
    for i in range(8):
        val = read_uint32(data, offset + i*4)
        record['fields'].append({
            'offset': offset + i*4,
            'value': val,
            'hex': f'0x{val:08x}'
        })

    return record


def find_polygon_data(data: bytes) -> list:
    """Find potential polygon coordinate arrays"""
    polygons = []

    i = 0
    while i < len(data) - 16:
        # Look for pattern: point_count (2-50), then followed by valid coordinates
        point_count = read_uint32(data, i)

        if 2 <= point_count <= 50:
            # Check if next values look like coordinates (0-2000 range typically)
            valid = True
            points = []

            for p in range(point_count):
                x_offset = i + 4 + p * 8
                y_offset = i + 4 + p * 8 + 4

                if x_offset + 8 > len(data):
                    valid = False
                    break

                x = read_int32(data, x_offset)
                y = read_int32(data, y_offset)

                # Reasonable coordinate range for 640x480 game
                if not (-100 <= x <= 1000 and -100 <= y <= 1000):
                    valid = False
                    break

                points.append((x, y))

            if valid and len(points) == point_count:
                # Additional validation: check for preceding type byte
                if i >= 4:
                    type_val = read_uint32(data, i - 4)
                    if type_val in [1, 2, 3, 4, 5]:  # Likely object type
                        polygons.append({
                            'offset': i,
                            'type': type_val,
                            'point_count': point_count,
                            'points': points,
                            'size': 4 + point_count * 8
                        })
                        i += 4 + point_count * 8
                        continue

        i += 1

    return polygons


def find_text_with_binary(data: bytes) -> list:
    """Find text commands with surrounding binary metadata"""
    results = []

    # Known command patterns
    commands = [
        b'scene ', b'hotspot ', b'score ', b'runprj ', b'playavi ',
        b'playwav ', b'addbmp ', b'delbmp ', b'set_var ', b'inc_var ',
        b' then ', b'playtext ', b'font '
    ]

    for cmd in commands:
        pos = 0
        while True:
            pos = data.find(cmd, pos)
            if pos == -1:
                break

            # Look back for binary prefix
            prefix_start = max(0, pos - 16)
            prefix = data[prefix_start:pos]

            # Extract text until binary data resumes
            text_end = pos
            while text_end < len(data):
                b = data[text_end]
                if b == 0 or (b < 32 and b not in [9, 10, 13]):
                    break
                text_end += 1

            text = data[pos:text_end].decode('latin-1', errors='replace')

            # Analyze prefix bytes
            prefix_values = []
            for i in range(0, len(prefix) - 3, 4):
                val = read_uint32(prefix, i)
                prefix_values.append(val)

            results.append({
                'offset': pos,
                'text': text.strip(),
                'prefix_offset': prefix_start,
                'prefix_values': prefix_values,
                'length': text_end - pos
            })

            pos = text_end + 1

    return results


def analyze_structure_at(data: bytes, offset: int, count: int = 20) -> None:
    """Print detailed analysis of bytes at offset"""
    print(f"\n=== Structure at 0x{offset:04x} ===")

    for i in range(count):
        if offset + i*4 >= len(data):
            break

        val = read_uint32(data, offset + i*4)
        signed = read_int32(data, offset + i*4)

        # Check if it could be a string
        str_val = extract_string(data, offset + i*4, 20)

        print(f"  +{i*4:3d} (0x{offset + i*4:04x}): "
              f"u32={val:10d} (0x{val:08x})  "
              f"i32={signed:10d}  "
              f"str=\"{str_val[:15]}\"" if len(str_val) > 2 else "")


def analyze_scene_records(data: bytes) -> list:
    """Find and analyze scene record patterns"""
    scenes = []

    # Look for pattern: scene number followed by text command
    i = 0
    while i < len(data) - 100:
        # Check for 0x01 0x00 0x00 0x00 marker (common record separator)
        if data[i:i+4] == b'\x01\x00\x00\x00':
            # Read next few uint32 values
            val1 = read_uint32(data, i+4)
            val2 = read_uint32(data, i+8)

            # Check if val1 or val2 could be text length
            if 1 < val1 < 200 and is_printable_range(data, i+12, min(val1, 50)):
                text = extract_string(data, i+12, val1)
                if text:
                    scenes.append({
                        'offset': i,
                        'marker': 1,
                        'length': val1,
                        'type': val2,
                        'text': text
                    })
        i += 1

    return scenes


def main():
    if len(sys.argv) < 2:
        print("Usage: python vnd_binary_analyzer.py <file.vnd>")
        print("\nAnalyzes binary data structures in VND files")
        sys.exit(1)

    filepath = sys.argv[1]
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"=== VND Binary Analyzer ===")
    print(f"File: {filepath}")
    print(f"Size: {len(data)} bytes")

    # 1. Find text with binary metadata
    print("\n" + "="*70)
    print("TEXT COMMANDS WITH BINARY METADATA")
    print("="*70)

    text_records = find_text_with_binary(data)
    for rec in text_records[:30]:
        print(f"\n[0x{rec['offset']:04x}] {rec['text'][:60]}")
        if rec['prefix_values']:
            print(f"  Prefix values: {rec['prefix_values']}")

    # 2. Find polygon data
    print("\n" + "="*70)
    print("POLYGON COORDINATE ARRAYS")
    print("="*70)

    polygons = find_polygon_data(data)
    for poly in polygons[:20]:
        print(f"\n[0x{poly['offset']:04x}] Type={poly['type']} Points={poly['point_count']}")
        print(f"  Coordinates: {poly['points'][:5]}...")

    # 3. Analyze scene records
    print("\n" + "="*70)
    print("SCENE/RECORD STRUCTURES")
    print("="*70)

    scenes = analyze_scene_records(data)
    for scene in scenes[:30]:
        print(f"[0x{scene['offset']:04x}] len={scene['length']:3d} type={scene['type']:3d} "
              f"text=\"{scene['text'][:40]}\"")

    # 4. Statistical analysis
    print("\n" + "="*70)
    print("BINARY PATTERN ANALYSIS")
    print("="*70)

    # Count 4-byte values
    value_counts = {}
    for i in range(0, len(data) - 3, 4):
        val = read_uint32(data, i)
        if val < 1000:  # Focus on small values (likely types/counts)
            value_counts[val] = value_counts.get(val, 0) + 1

    print("\nMost common small values (likely types/lengths):")
    for val, count in sorted(value_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {val:5d} (0x{val:04x}): {count:4d} occurrences")

    # 5. Look at specific interesting offsets
    print("\n" + "="*70)
    print("DETAILED STRUCTURE ANALYSIS")
    print("="*70)

    # Find first occurrence of "scene" or "hotspot"
    scene_pos = data.find(b'scene ')
    if scene_pos > 0:
        analyze_structure_at(data, max(0, scene_pos - 32), 15)

    hotspot_pos = data.find(b'hotspot ')
    if hotspot_pos > 0:
        analyze_structure_at(data, max(0, hotspot_pos - 32), 15)


if __name__ == "__main__":
    main()
