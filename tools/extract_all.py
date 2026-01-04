#!/usr/bin/env python3
"""
Extract all game data from Europeo VND files to JSON
for use in the React port.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Country mappings
COUNTRIES = {
    'allem': {'name': 'Allemagne', 'name_en': 'Germany'},
    'angl': {'name': 'Angleterre', 'name_en': 'England'},
    'autr': {'name': 'Autriche', 'name_en': 'Austria'},
    'belge': {'name': 'Belgique', 'name_en': 'Belgium'},
    'danem': {'name': 'Danemark', 'name_en': 'Denmark'},
    'ecosse': {'name': 'Écosse', 'name_en': 'Scotland'},
    'espa': {'name': 'Espagne', 'name_en': 'Spain'},
    'finlan': {'name': 'Finlande', 'name_en': 'Finland'},
    'france': {'name': 'France', 'name_en': 'France'},
    'grece': {'name': 'Grèce', 'name_en': 'Greece'},
    'holl': {'name': 'Pays-Bas', 'name_en': 'Netherlands'},
    'irland': {'name': 'Irlande', 'name_en': 'Ireland'},
    'italie': {'name': 'Italie', 'name_en': 'Italy'},
    'portu': {'name': 'Portugal', 'name_en': 'Portugal'},
    'suede': {'name': 'Suède', 'name_en': 'Sweden'},
}


def parse_vnd_text(filepath: str) -> Dict[str, Any]:
    """Parse VND file and extract all readable content"""
    with open(filepath, 'rb') as f:
        data = f.read()

    text = data.decode('latin-1', errors='replace')

    result = {
        'file': os.path.basename(filepath),
        'path': filepath,
        'variables': [],
        'scenes': [],
        'resources': {
            'images': [],
            'audio': [],
            'videos': [],
            'html': [],
            'cursors': []
        },
        'commands': [],
        'navigation': []
    }

    # Extract variables
    var_pattern = r'\x00([A-Z][A-Z0-9_]{2,20})\x00\x00\x00\x00'
    seen_vars = set()
    for match in re.finditer(var_pattern, text):
        name = match.group(1)
        if name not in seen_vars and len(name) <= 20:
            result['variables'].append(name)
            seen_vars.add(name)

    # Extract file references
    result['resources']['images'] = sorted(set(re.findall(r'(\w+\.bmp)', text, re.I)))
    result['resources']['audio'] = sorted(set(re.findall(r'(\w+\.wav)', text, re.I)))
    result['resources']['videos'] = sorted(set(re.findall(r'(\w+\.avi)', text, re.I)))
    result['resources']['html'] = sorted(set(re.findall(r'(\w+\.htm)', text, re.I)))
    result['resources']['cursors'] = sorted(set(re.findall(r'(\w+\.cur)', text, re.I)))

    # Extract scene changes
    scene_pattern = r'scene\s+(\d+)'
    result['scenes'] = sorted(set(int(m) for m in re.findall(scene_pattern, text, re.I)))

    # Extract navigation to other projects
    nav_pattern = r'(\.\.[\\/][\w\\/]+\.vnp)\s+(\d+)'
    for match in re.finditer(nav_pattern, text):
        result['navigation'].append({
            'target': match.group(1).replace('\\', '/'),
            'scene': int(match.group(2))
        })

    # Extract conditional commands
    cond_pattern = r'(\w+)\s*(=|!=|<|>|<=|>=)\s*(\d+)\s+then\s+([^\n]+)'
    for match in re.finditer(cond_pattern, text, re.I):
        result['commands'].append({
            'type': 'conditional',
            'variable': match.group(1),
            'operator': match.group(2),
            'value': int(match.group(3)),
            'action': match.group(4).strip()[:100]  # Limit length
        })

    # Extract hotspot definitions (coordinates)
    # Look for patterns like: i X1 Y1 X2 Y2 (where i is a small number)
    hotspot_pattern = r'[idl]\s{2,}(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})'
    hotspots = []
    for match in re.finditer(hotspot_pattern, text):
        x1, y1, x2, y2 = map(int, match.groups())
        if 0 <= x1 < 640 and 0 <= y1 < 480 and x1 < x2 and y1 < y2:
            hotspots.append({'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2})
    result['hotspots'] = hotspots[:50]  # Limit

    # Limit commands for JSON size
    result['commands'] = result['commands'][:100]

    return result


def parse_vnp_file(filepath: str) -> Dict[str, str]:
    """Parse VNP configuration file"""
    config = {}
    try:
        with open(filepath, 'r', encoding='latin-1') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('['):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    return config


def extract_country_data(base_path: Path, country_id: str) -> Dict[str, Any]:
    """Extract all data for a country module"""
    country_path = base_path / country_id

    if not country_path.exists():
        return None

    country_info = COUNTRIES.get(country_id, {'name': country_id, 'name_en': country_id})

    data = {
        'id': country_id,
        'name': country_info['name'],
        'name_en': country_info['name_en'],
        'vnd': None,
        'vnp': None,
        'assets': {
            'images': [],
            'audio': [],
            'videos': [],
            'html': []
        }
    }

    # Parse VND file
    vnd_file = country_path / f"{country_id}.vnd"
    if vnd_file.exists():
        data['vnd'] = parse_vnd_text(str(vnd_file))

    # Parse VNP file
    vnp_file = country_path / f"{country_id}.vnp"
    if vnp_file.exists():
        data['vnp'] = parse_vnp_file(str(vnp_file))

    # List actual assets on disk
    img_path = country_path / 'img24'
    if img_path.exists():
        data['assets']['images'] = sorted([f.name for f in img_path.glob('*.bmp')])

    digit_path = country_path / 'digit'
    if digit_path.exists():
        data['assets']['audio'] = sorted([f.name for f in digit_path.glob('*.wav')])

    movie_path = country_path / 'movie'
    if movie_path.exists():
        data['assets']['videos'] = sorted([f.name for f in movie_path.glob('*.avi')])

    html_path = country_path / 'html'
    if html_path.exists():
        data['assets']['html'] = sorted([f.name for f in html_path.glob('*.htm')])

    return data


def extract_all_data(base_path: str) -> Dict[str, Any]:
    """Extract complete game data"""
    base = Path(base_path)

    game_data = {
        'metadata': {
            'title': 'Europeo',
            'developer': 'Sopra Multimedia',
            'format_version': 'VNFILE 2.13',
            'resolution': {'width': 640, 'height': 480}
        },
        'countries': {},
        'special_modules': {},
        'global_variables': set(),
        'all_resources': {
            'images': set(),
            'audio': set(),
            'videos': set(),
            'html': set()
        }
    }

    # Extract country data
    for country_id in COUNTRIES.keys():
        country_data = extract_country_data(base, country_id)
        if country_data:
            game_data['countries'][country_id] = country_data

            # Collect global variables
            if country_data['vnd']:
                game_data['global_variables'].update(country_data['vnd']['variables'])

    # Extract special modules
    special_modules = ['frontal', 'couleurs1', 'barre', 'biblio']
    for module in special_modules:
        module_path = base / module
        if module_path.exists():
            vnd_files = list(module_path.glob('*.vnd'))
            if vnd_files:
                game_data['special_modules'][module] = {
                    'vnd': parse_vnd_text(str(vnd_files[0]))
                }
                if game_data['special_modules'][module]['vnd']:
                    game_data['global_variables'].update(
                        game_data['special_modules'][module]['vnd']['variables']
                    )

    # Convert sets to sorted lists
    game_data['global_variables'] = sorted(game_data['global_variables'])

    return game_data


def main():
    base_path = Path(__file__).parent.parent

    print("Extracting Europeo game data...")
    game_data = extract_all_data(str(base_path))

    # Save to JSON
    output_path = base_path / 'tools' / 'game_data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(game_data, f, indent=2, ensure_ascii=False, default=list)

    print(f"Saved to {output_path}")

    # Print summary
    print(f"\nSummary:")
    print(f"  Countries: {len(game_data['countries'])}")
    print(f"  Special modules: {len(game_data['special_modules'])}")
    print(f"  Global variables: {len(game_data['global_variables'])}")

    # List countries
    print(f"\nCountries extracted:")
    for country_id, data in game_data['countries'].items():
        scenes = len(data['vnd']['scenes']) if data['vnd'] else 0
        print(f"  {data['name']}: {scenes} scenes")


if __name__ == '__main__':
    main()
