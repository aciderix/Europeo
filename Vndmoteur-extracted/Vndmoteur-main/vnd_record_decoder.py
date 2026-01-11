#!/usr/bin/env python3
"""
VND Record Decoder
==================

Decodes the binary record structure in VND files.

DISCOVERED STRUCTURE:
=====================

Each record in VND follows this pattern:
[TEXT_COMMAND] 01 00 00 00 [LENGTH] [TYPE] [DATA...]

Where:
- 01 00 00 00 = Record separator/marker
- LENGTH = uint32 LE, length of next field or record type indicator
- TYPE = uint32 LE, type of the next data
- DATA = varies based on type

For hotspots with polygons:
[hotspot_name] 00 00 00 [num_points] 00 00 00 [point_count] 00 00 00
  [x1] [y1] [x2] [y2] ... [xN] [yN]

Each coordinate is int32 LE.
"""

import struct
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class VNDRecord:
    offset: int
    record_type: int
    data_length: int
    text: str
    binary_data: bytes
    coordinates: List[Tuple[int, int]]


def read_uint32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<I', data, offset)[0]


def read_int32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<i', data, offset)[0]


def find_record_markers(data: bytes) -> List[int]:
    """Find all 01 00 00 00 markers"""
    markers = []
    pattern = b'\x01\x00\x00\x00'
    pos = 0
    while True:
        pos = data.find(pattern, pos)
        if pos == -1:
            break
        markers.append(pos)
        pos += 1
    return markers


def extract_text_before(data: bytes, offset: int, max_len: int = 100) -> str:
    """Extract printable text before an offset"""
    start = max(0, offset - max_len)
    result = []

    # Find start of text
    text_start = offset - 1
    while text_start > start:
        b = data[text_start]
        if 32 <= b <= 126:
            text_start -= 1
        else:
            text_start += 1
            break

    # Extract text
    for i in range(text_start, offset):
        b = data[i]
        if 32 <= b <= 126:
            result.append(chr(b))

    return ''.join(result)


def decode_coordinates(data: bytes, offset: int, count: int) -> List[Tuple[int, int]]:
    """Decode N coordinate pairs"""
    coords = []
    for i in range(count):
        x = read_int32(data, offset + i * 8)
        y = read_int32(data, offset + i * 8 + 4)
        coords.append((x, y))
    return coords


def analyze_record_at_marker(data: bytes, marker_offset: int) -> dict:
    """Analyze the structure at a record marker"""
    result = {
        'marker_offset': marker_offset,
        'text_before': extract_text_before(data, marker_offset),
        'values': [],
        'interpretation': None
    }

    # Read values after marker
    offset = marker_offset + 4
    for i in range(20):
        if offset + 4 > len(data):
            break
        val = read_uint32(data, offset)
        result['values'].append({
            'offset': offset,
            'value': val,
            'hex': f'0x{val:04x}'
        })
        offset += 4

    # Try to interpret
    if len(result['values']) >= 2:
        v1 = result['values'][0]['value']
        v2 = result['values'][1]['value']

        # Check if v1 looks like a length and next bytes are text
        if 1 < v1 < 100:
            text_offset = marker_offset + 4 + 8  # After marker + 2 uint32s
            text_bytes = data[text_offset:text_offset + v1]
            if all(32 <= b <= 126 or b == 0 for b in text_bytes):
                result['interpretation'] = {
                    'type': 'text_record',
                    'length': v1,
                    'subtype': v2,
                    'text': text_bytes.decode('latin-1').rstrip('\x00')
                }

    return result


def find_polygon_sequences(data: bytes) -> List[dict]:
    """Find sequences that look like polygon coordinate arrays"""
    polygons = []

    i = 0
    while i < len(data) - 40:
        # Look for pattern: small_num 00 00 00 small_num 00 00 00
        # followed by valid coordinate pairs

        n1 = read_uint32(data, i)
        n2 = read_uint32(data, i + 4)

        # Potential polygon: n2 is point count between 3-20
        if n1 < 10 and 3 <= n2 <= 30:
            # Check if following bytes look like coordinates
            coords = []
            valid = True

            for p in range(n2):
                x_off = i + 8 + p * 8
                y_off = i + 8 + p * 8 + 4

                if y_off + 4 > len(data):
                    valid = False
                    break

                x = read_int32(data, x_off)
                y = read_int32(data, y_off)

                # Valid screen coordinates (with some margin)
                if not (-50 <= x <= 800 and -50 <= y <= 600):
                    valid = False
                    break

                coords.append((x, y))

            if valid and len(coords) >= 3:
                # Look back for hotspot name
                name = extract_text_before(data, i - 4, 50)

                polygons.append({
                    'offset': i,
                    'type': n1,
                    'point_count': n2,
                    'points': coords,
                    'name': name,
                    'size': 8 + n2 * 8
                })
                i += 8 + n2 * 8
                continue

        i += 1

    return polygons


def decode_vnd_records(filepath: str):
    """Main decoder function"""
    with open(filepath, 'rb') as f:
        data = f.read()

    print(f"=== VND Record Decoder ===")
    print(f"File: {filepath}")
    print(f"Size: {len(data)} bytes")

    # Find record markers
    markers = find_record_markers(data)
    print(f"\nFound {len(markers)} record markers (01 00 00 00)")

    # Analyze records
    print("\n" + "="*70)
    print("RECORD ANALYSIS (first 50)")
    print("="*70)

    records = []
    for marker in markers[:50]:
        rec = analyze_record_at_marker(data, marker)
        records.append(rec)

        print(f"\n[0x{marker:04x}] Text: \"{rec['text_before'][-30:]}\"")
        print(f"  Values: {[v['value'] for v in rec['values'][:6]]}")

        if rec['interpretation']:
            interp = rec['interpretation']
            print(f"  => {interp['type']}: len={interp.get('length')} "
                  f"subtype={interp.get('subtype')} text=\"{interp.get('text', '')[:40]}\"")

    # Find polygons
    print("\n" + "="*70)
    print("POLYGON SEQUENCES")
    print("="*70)

    polygons = find_polygon_sequences(data)
    print(f"\nFound {len(polygons)} potential polygon sequences")

    for poly in polygons:
        print(f"\n[0x{poly['offset']:04x}] Name: \"{poly['name'][-20:]}\"")
        print(f"  Type: {poly['type']}, Points: {poly['point_count']}")
        print(f"  Coordinates: {poly['points']}")

        # Calculate bounding box
        if poly['points']:
            xs = [p[0] for p in poly['points']]
            ys = [p[1] for p in poly['points']]
            print(f"  BBox: ({min(xs)},{min(ys)}) - ({max(xs)},{max(ys)})")

    # Summary
    print("\n" + "="*70)
    print("STRUCTURE SUMMARY")
    print("="*70)

    # Count record types
    type_counts = {}
    for rec in records:
        if rec['interpretation']:
            t = rec['interpretation'].get('subtype', 0)
            type_counts[t] = type_counts.get(t, 0) + 1

    print("\nRecord subtypes found:")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  Type {t:3d}: {count:4d} occurrences")

    return records, polygons


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vnd_record_decoder.py <file.vnd>")
        sys.exit(1)

    decode_vnd_records(sys.argv[1])
