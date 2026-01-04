#!/usr/bin/env python3
"""
VND Parser - Visual Novel Data file parser for Europeo
Format: VNFILE 2.13 by Sopra Multimedia

This parser extracts all data from VND files and converts them to JSON
for use in the React port.
"""

import struct
import json
import re
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class VNDParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()
        self.offset = 0
        self.text_content = self.data.decode('latin-1', errors='replace')

    def read_uint32(self) -> int:
        """Read 4-byte unsigned integer (little-endian)"""
        value = struct.unpack_from('<I', self.data, self.offset)[0]
        self.offset += 4
        return value

    def read_uint16(self) -> int:
        """Read 2-byte unsigned integer (little-endian)"""
        value = struct.unpack_from('<H', self.data, self.offset)[0]
        self.offset += 2
        return value

    def read_byte(self) -> int:
        """Read single byte"""
        value = self.data[self.offset]
        self.offset += 1
        return value

    def read_string(self) -> str:
        """Read length-prefixed string"""
        length = self.read_uint32()
        if length == 0 or length > 10000:
            return ''
        string = self.data[self.offset:self.offset + length].decode('latin-1', errors='replace')
        self.offset += length
        return string

    def skip(self, count: int):
        """Skip bytes"""
        self.offset += count

    def parse_header(self) -> Dict[str, Any]:
        """Parse VND file header"""
        self.offset = 5  # Skip initial flags

        header = {
            'magic': self.read_string(),
        }
        self.skip(4)
        header['version'] = self.read_string()
        self.skip(4)
        header['application'] = self.read_string()
        header['developer'] = self.read_string()
        header['id'] = self.read_string()
        header['registry_path'] = self.read_string()

        # Read dimensions
        header['width'] = self.read_uint16()
        self.skip(2)
        header['height'] = self.read_uint16()
        self.skip(10)

        # Resource DLL
        header['resource_dll'] = self.read_string()

        return header

    def parse_variables(self) -> List[Dict[str, Any]]:
        """Parse variable definitions from text content"""
        variables = []

        # Extract variable names from the text content
        # Variables are typically uppercase names at the start of the file
        # Look for patterns like "SACADOS", "JEU", "BIDON", etc.

        # Find all uppercase words that look like variable names
        var_pattern = r'\x00([A-Z][A-Z0-9_]{2,})\x00\x00\x00\x00'
        matches = re.findall(var_pattern, self.text_content)

        seen = set()
        for name in matches:
            if name not in seen and len(name) <= 20:
                variables.append({'name': name, 'value': 0})
                seen.add(name)

        return variables

    def extract_scenes_from_text(self) -> List[Dict[str, Any]]:
        """Extract scene information from text representation"""
        scenes = []
        current_scene = None

        # Find scene markers in the text
        # Scenes are typically separated by special patterns

        # Extract commands that reference files
        bmp_pattern = r'(\w+\.bmp)'
        wav_pattern = r'(\w+\.wav)'
        avi_pattern = r'(\w+\.avi)'
        htm_pattern = r'(\w+\.htm)'
        vnp_pattern = r'([\w\\./]+\.vnp)'

        # Find all file references
        bmps = set(re.findall(bmp_pattern, self.text_content, re.IGNORECASE))
        wavs = set(re.findall(wav_pattern, self.text_content, re.IGNORECASE))
        avis = set(re.findall(avi_pattern, self.text_content, re.IGNORECASE))
        htms = set(re.findall(htm_pattern, self.text_content, re.IGNORECASE))
        vnps = set(re.findall(vnp_pattern, self.text_content, re.IGNORECASE))

        return {
            'images': sorted(bmps),
            'audio': sorted(wavs),
            'videos': sorted(avis),
            'html': sorted(htms),
            'projects': sorted(vnps)
        }

    def extract_commands(self) -> List[str]:
        """Extract all command-like strings from the file"""
        commands = []

        # Command patterns
        patterns = [
            r'(scene\s+\d+)',
            r'(runprj\s+[\w\\./]+\.vnp\s+\d+)',
            r'(playavi\s+[\w./]+\.avi\s+[\d\s]+)',
            r'(playwav\s+[\w./]+\.wav\s+\d+)',
            r'(playhtml\s+[\w./]+\.htm\s+[\d\s]+)',
            r'(addbmp\s+\w+\s+[\w./\\]+\.bmp\s+[\d\s]+)',
            r'(delbmp\s+\w+)',
            r'(toolbar\s+[\w./\\]+\.bmp\s+[\d\s]+)',
            r'(set_var\s+\w+\s+\d+)',
            r'(inc_var\s+\w+\s+\d+)',
            r'(dec_var\s+\w+\s+\d+)',
            r'(rundll\s+[\w./\\]+\.dll)',
            r'(defcursor\s+[\w./\\]+\.cur)',
            r'(\w+\s*[=!<>]+\s*\d+\s+then\s+.+?)(?=\n|$)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, self.text_content, re.IGNORECASE)
            commands.extend(matches)

        return commands

    def extract_hotspot_coords(self) -> List[Tuple[int, int, int, int]]:
        """Extract hotspot coordinates"""
        # Hotspot coordinates appear as sequences of numbers
        # Format: x1 y1 x2 y2
        coords = []

        # Look for coordinate patterns in the binary data
        # This is a simplified approach
        pattern = r'(\d{2,3})\s+(\d{2,3})\s+(\d{2,3})\s+(\d{2,3})'
        matches = re.findall(pattern, self.text_content)

        for m in matches:
            x1, y1, x2, y2 = map(int, m)
            # Filter to reasonable screen coordinates
            if 0 <= x1 <= 640 and 0 <= y1 <= 480 and x1 < x2 and y1 < y2:
                coords.append((x1, y1, x2, y2))

        return coords

    def parse(self) -> Dict[str, Any]:
        """Parse complete VND file"""
        header = self.parse_header()
        variables = self.parse_variables()
        resources = self.extract_scenes_from_text()
        commands = self.extract_commands()

        return {
            'file': os.path.basename(self.filepath),
            'header': header,
            'variables': variables,
            'resources': resources,
            'commands': commands[:100],  # Limit for readability
            'total_commands': len(commands)
        }


def parse_vnp_file(filepath: str) -> Dict[str, Any]:
    """Parse VNP (Visual Novel Project) INI file"""
    config = {'file': os.path.basename(filepath)}

    with open(filepath, 'r', encoding='latin-1') as f:
        section = None
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                section = line[1:-1]
                config[section] = {}
            elif '=' in line and section:
                key, value = line.split('=', 1)
                config[section][key.strip()] = value.strip()

    return config


def analyze_project(base_dir: str) -> Dict[str, Any]:
    """Analyze complete Europeo project"""
    base_path = Path(base_dir)

    analysis = {
        'vnd_files': [],
        'vnp_files': [],
        'countries': [],
        'total_variables': set(),
        'all_resources': {
            'images': set(),
            'audio': set(),
            'videos': set(),
            'html': set()
        }
    }

    # Find all VND files
    for vnd_file in base_path.rglob('*.vnd'):
        try:
            parser = VNDParser(str(vnd_file))
            result = parser.parse()
            analysis['vnd_files'].append(result)

            # Collect variables
            for var in result['variables']:
                analysis['total_variables'].add(var['name'])

            # Collect resources
            for img in result['resources']['images']:
                analysis['all_resources']['images'].add(img)
            for wav in result['resources']['audio']:
                analysis['all_resources']['audio'].add(wav)
            for avi in result['resources']['videos']:
                analysis['all_resources']['videos'].add(avi)
            for htm in result['resources']['html']:
                analysis['all_resources']['html'].add(htm)

        except Exception as e:
            print(f"Error parsing {vnd_file}: {e}")

    # Find all VNP files
    for vnp_file in base_path.rglob('*.vnp'):
        try:
            result = parse_vnp_file(str(vnp_file))
            analysis['vnp_files'].append(result)
        except Exception as e:
            print(f"Error parsing {vnp_file}: {e}")

    # Identify countries from directory structure
    country_dirs = ['allem', 'angl', 'autr', 'belge', 'danem', 'ecosse',
                    'espa', 'finlan', 'france', 'grece', 'holl', 'irland',
                    'italie', 'portu', 'suede']

    for country in country_dirs:
        country_path = base_path / country
        if country_path.exists():
            analysis['countries'].append({
                'id': country,
                'has_vnd': (country_path / f"{country}.vnd").exists(),
                'has_vnp': (country_path / f"{country}.vnp").exists(),
            })

    # Convert sets to sorted lists for JSON
    analysis['total_variables'] = sorted(analysis['total_variables'])
    analysis['all_resources']['images'] = sorted(analysis['all_resources']['images'])
    analysis['all_resources']['audio'] = sorted(analysis['all_resources']['audio'])
    analysis['all_resources']['videos'] = sorted(analysis['all_resources']['videos'])
    analysis['all_resources']['html'] = sorted(analysis['all_resources']['html'])

    return analysis


def main():
    if len(sys.argv) < 2:
        print("Usage: python vnd_parser.py <file.vnd|directory>")
        print("\nExamples:")
        print("  python vnd_parser.py start.vnd")
        print("  python vnd_parser.py /path/to/Europeo")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isfile(path):
        if path.endswith('.vnd'):
            parser = VNDParser(path)
            result = parser.parse()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif path.endswith('.vnp'):
            result = parse_vnp_file(path)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    elif os.path.isdir(path):
        analysis = analyze_project(path)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    else:
        print(f"Error: {path} not found")
        sys.exit(1)


if __name__ == '__main__':
    main()
