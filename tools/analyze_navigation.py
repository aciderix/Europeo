#!/usr/bin/env python3
"""
Analyze VND navigation patterns to understand suffix meanings (i, d, f, h, j)
"""

import re
import struct
from collections import defaultdict

def analyze_vnd_navigation(vnd_path: str):
    with open(vnd_path, 'rb') as f:
        data = f.read()

    # Extract readable strings
    strings = []
    current = []
    for byte in data:
        if 32 <= byte <= 126:
            current.append(chr(byte))
        elif current:
            s = ''.join(current).strip()
            if len(s) > 3:
                strings.append(s)
            current = []

    # Find all navigation patterns
    nav_patterns = {
        'runprj': [],  # runprj project scene[suffix]
        'scene': [],   # scene number[suffix]
        'playavi': [], # playavi video params
    }

    # Pattern for runprj commands
    runprj_pattern = re.compile(r'runprj\s+([^\s]+\.vnp)\s+(\d+)([idfhj]?)', re.IGNORECASE)

    # Pattern for scene commands
    scene_pattern = re.compile(r'scene\s+(\d+)([idfhj]?)', re.IGNORECASE)

    # Pattern for playavi with video file
    playavi_pattern = re.compile(r'playavi\s+([^\s]+\.avi)\s+(\d+)\s*(.*)$', re.IGNORECASE)

    for s in strings:
        # Check runprj
        match = runprj_pattern.search(s)
        if match:
            nav_patterns['runprj'].append({
                'raw': s,
                'project': match.group(1),
                'scene': match.group(2),
                'suffix': match.group(3) or '(none)'
            })

        # Check scene
        match = scene_pattern.search(s)
        if match:
            nav_patterns['scene'].append({
                'raw': s,
                'scene': match.group(1),
                'suffix': match.group(2) or '(none)'
            })

        # Check playavi
        match = playavi_pattern.search(s)
        if match:
            nav_patterns['playavi'].append({
                'raw': s,
                'video': match.group(1),
                'param1': match.group(2),
                'rest': match.group(3)
            })

    return nav_patterns, strings

def print_analysis(vnd_path: str):
    print(f"Analyzing: {vnd_path}")
    print("=" * 80)

    nav_patterns, strings = analyze_vnd_navigation(vnd_path)

    # Count suffixes for runprj
    print("\n1. RUNPRJ Commands by Suffix:")
    print("-" * 40)
    suffix_counts = defaultdict(list)
    for item in nav_patterns['runprj']:
        suffix_counts[item['suffix']].append(item)

    for suffix, items in sorted(suffix_counts.items()):
        print(f"\n  Suffix '{suffix}': {len(items)} occurrences")
        for item in items[:5]:  # Show first 5 examples
            print(f"    - {item['project']} scene {item['scene']}")
        if len(items) > 5:
            print(f"    ... and {len(items) - 5} more")

    # Count suffixes for scene
    print("\n\n2. SCENE Commands by Suffix:")
    print("-" * 40)
    suffix_counts = defaultdict(list)
    for item in nav_patterns['scene']:
        suffix_counts[item['suffix']].append(item)

    for suffix, items in sorted(suffix_counts.items()):
        print(f"\n  Suffix '{suffix}': {len(items)} occurrences")
        scenes = set()
        for item in items:
            scenes.add(item['scene'])
        print(f"    Unique scenes: {sorted(scenes)[:20]}")

    # Show playavi patterns
    print("\n\n3. PLAYAVI Commands:")
    print("-" * 40)
    unique_videos = set()
    for item in nav_patterns['playavi']:
        video = item['video'].split('\\')[-1]
        unique_videos.add(video)

    print(f"  Unique videos: {len(unique_videos)}")
    for video in sorted(unique_videos)[:20]:
        print(f"    - {video}")

    # Find video → scene associations in context
    print("\n\n4. Video Navigation Context (looking for patterns):")
    print("-" * 40)

    # Search for patterns like "video.avi 1 → Ni" which indicates scene navigation
    video_nav_pattern = re.compile(r'([^\s\\]+\.avi)\s+\d+\s*[-→]?\s*(\d+)([idfhj])?', re.IGNORECASE)

    for s in strings:
        if '.avi' in s.lower() and any(c in s for c in 'idfhj'):
            print(f"    {s[:100]}")

    # Extract specific patterns from binary
    print("\n\n5. Binary Analysis - Video References with Suffixes:")
    print("-" * 40)

    with open(vnd_path, 'rb') as f:
        data = f.read()

    # Find patterns like "video.avi 1" followed by numbers with suffixes
    avi_refs = re.finditer(rb'([a-zA-Z0-9_]+\.avi)\s+(\d+)\s*(\d*)([idfhj]?)', data, re.IGNORECASE)

    for match in avi_refs:
        video = match.group(1).decode('latin-1')
        param1 = match.group(2).decode('latin-1')
        param2 = match.group(3).decode('latin-1') if match.group(3) else ''
        suffix = match.group(4).decode('latin-1') if match.group(4) else ''

        if suffix or param2:
            print(f"    {video} {param1} {param2}{suffix}")

    return nav_patterns

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        vnd_path = '/home/user/Europeo/couleurs1/couleurs1.vnd'
    else:
        vnd_path = sys.argv[1]

    print_analysis(vnd_path)
