#!/usr/bin/env python3
"""
Parse ALL VND files to extract complete game structure.
Generates a unified game_data.json for the React engine.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image

BASE_DIR = Path(__file__).parent.parent
VND_EXTRACT_DIR = BASE_DIR / "vnd hexa extract" / "extracted_data_all"
OUTPUT_DIR = BASE_DIR / "Doc"

# Map VND file names to country folders and display names
VND_MAPPING = {
    'couleurs1': {'folder': 'couleurs1', 'name': 'Euroland', 'subfolder': 'euroland'},
    'france': {'folder': 'france', 'name': 'France', 'subfolder': ''},
    'allem': {'folder': 'allem', 'name': 'Allemagne', 'subfolder': ''},
    'angleterre': {'folder': 'angl', 'name': 'Angleterre', 'subfolder': ''},
    'autr': {'folder': 'autr', 'name': 'Autriche', 'subfolder': ''},
    'belge': {'folder': 'belge', 'name': 'Belgique', 'subfolder': ''},
    'danem': {'folder': 'danem', 'name': 'Danemark', 'subfolder': ''},
    'ecosse': {'folder': 'ecosse', 'name': 'Écosse', 'subfolder': ''},
    'espa': {'folder': 'espa', 'name': 'Espagne', 'subfolder': ''},
    'finlan': {'folder': 'finlan', 'name': 'Finlande', 'subfolder': ''},
    'grece': {'folder': 'grece', 'name': 'Grèce', 'subfolder': ''},
    'holl': {'folder': 'holl', 'name': 'Pays-Bas', 'subfolder': ''},
    'irland': {'folder': 'irland', 'name': 'Irlande', 'subfolder': ''},
    'italie': {'folder': 'italie', 'name': 'Italie', 'subfolder': ''},
    'portu': {'folder': 'portu', 'name': 'Portugal', 'subfolder': ''},
    'suede': {'folder': 'suede', 'name': 'Suède', 'subfolder': ''},
    'biblio': {'folder': 'biblio', 'name': 'Bibliothèque', 'subfolder': ''},
    'barre': {'folder': 'barre', 'name': 'Barre outils', 'subfolder': ''},
    'start': {'folder': 'frontal', 'name': 'Démarrage', 'subfolder': ''},
}


class VndParser:
    """Parse a single VND extracted text file"""

    def __init__(self, vnd_id: str, txt_path: Path):
        self.vnd_id = vnd_id
        self.txt_path = txt_path
        self.mapping = VND_MAPPING.get(vnd_id, {'folder': vnd_id, 'name': vnd_id, 'subfolder': ''})
        self.lines = []
        self.scenes = []
        self.variables = []
        self.rollover_images = {}  # name -> {path, x, y, width, height}

    def load(self):
        """Load the text file"""
        with open(self.txt_path, 'r', encoding='utf-8', errors='ignore') as f:
            self.lines = f.readlines()
        return self

    def parse_line(self, line: str) -> Tuple[Optional[str], str]:
        """Parse a line to extract offset and content"""
        match = re.match(r'.*@([0-9A-F]+):\s*(.*)', line.strip())
        if match:
            return match.group(1), match.group(2)
        return None, line.strip()

    def get_rollover_dimensions(self, image_path: str) -> Tuple[int, int]:
        """Get dimensions of a rollover image"""
        # Try to find the image file
        folder = self.mapping['folder']
        subfolder = self.mapping.get('subfolder', '')

        # Normalize path
        image_path = image_path.replace('\\', '/')

        # Try different possible locations
        possible_paths = [
            BASE_DIR / folder / "img24" / subfolder / image_path,
            BASE_DIR / folder / "img24" / image_path,
            BASE_DIR / folder / image_path,
        ]

        for path in possible_paths:
            if path.exists():
                try:
                    img = Image.open(path)
                    return img.size
                except:
                    pass

        return (50, 50)  # Default size

    def parse(self) -> Dict:
        """Parse the VND and extract structure"""
        current_scene = None
        current_hotspot = None
        scene_idx = 0
        in_data_section = False

        for line in self.lines:
            offset, content = self.parse_line(line)

            if not content or content.startswith('=') or content.startswith('-'):
                continue

            # Skip header
            if 'CHAÎNES' in content or 'EXTRAITES' in content:
                in_data_section = True
                continue
            if not in_data_section and offset is None:
                continue

            # Detect background BMP (new scene)
            if re.match(r'^[\w\\]+\.bmp$', content, re.IGNORECASE):
                if 'rollover' not in content.lower() and 'roll' not in content.lower():
                    # Save previous scene
                    if current_scene:
                        self.scenes.append(current_scene)

                    scene_idx += 1
                    current_scene = {
                        'id': scene_idx,
                        'background': content,
                        'audio': None,
                        'hotspots': [],
                        'conditions': [],
                        'actions': []
                    }
                    current_hotspot = None
                    continue

            # Detect audio
            if re.match(r'^[\w\\]+\.wav(\s+\d+)?$', content, re.IGNORECASE):
                audio = re.match(r'^([\w\\]+\.wav)', content).group(1)
                if current_scene:
                    current_scene['audio'] = audio
                continue

            # Detect hotspot text (format: X Y param param layer Text)
            hotspot_match = re.match(r'^(\d+)\s+(\d+)\s+\d+\s+\d+\s+(\d+)\s+(.+)$', content)
            if hotspot_match and current_scene:
                x, y = int(hotspot_match.group(1)), int(hotspot_match.group(2))
                layer = int(hotspot_match.group(3))
                text = hotspot_match.group(4)

                current_hotspot = {
                    'text_x': x,
                    'text_y': y,
                    'layer': layer,
                    'text': text,
                    'actions': []
                }
                current_scene['hotspots'].append(current_hotspot)
                continue

            # Detect addbmp (clickable image)
            addbmp_match = re.match(
                r'(?:.*then\s+)?addbmp\s+(\w+)\s+([\w\\/.]+\.bmp)\s+(\d+)\s+(\d+)\s+(\d+)',
                content, re.IGNORECASE
            )
            if addbmp_match:
                name = addbmp_match.group(1)
                img_path = addbmp_match.group(2)
                layer = int(addbmp_match.group(3))
                x, y = int(addbmp_match.group(4)), int(addbmp_match.group(5))

                # Get image dimensions
                width, height = self.get_rollover_dimensions(img_path)

                self.rollover_images[name] = {
                    'image': img_path,
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'layer': layer
                }
                continue

            # Detect video (action)
            video_match = re.match(r'^([\w\\]+\.avi)\s+(\d+)(?:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+))?', content)
            if video_match and current_hotspot:
                video = {
                    'type': 'video',
                    'file': video_match.group(1),
                }
                if video_match.group(3):
                    video['rect'] = {
                        'x1': int(video_match.group(3)),
                        'y1': int(video_match.group(4)),
                        'x2': int(video_match.group(5)),
                        'y2': int(video_match.group(6))
                    }
                current_hotspot['actions'].append(video)
                continue

            # Detect scene navigation (e.g., "39i", "51j")
            nav_match = re.match(r'^(\d+)[a-z]$', content)
            if nav_match and current_hotspot:
                current_hotspot['goto_scene'] = int(nav_match.group(1))
                current_hotspot = None
                continue

            # Detect condition
            cond_match = re.match(r'^(\w+)\s*([<>=!]+)\s*(\d+)\s+then\s+(.+?)(?:\s+else\s+(.+))?$', content)
            if cond_match and current_scene:
                condition = {
                    'variable': cond_match.group(1),
                    'operator': cond_match.group(2),
                    'value': int(cond_match.group(3)),
                    'then': cond_match.group(4),
                    'else': cond_match.group(5)
                }
                current_scene['conditions'].append(condition)
                continue

            # Detect runprj (load another VND)
            runprj_match = re.match(r'.*runprj\s+([\w\\/.]+\.vnp)\s*(\d+)?', content)
            if runprj_match and current_hotspot:
                current_hotspot['actions'].append({
                    'type': 'runprj',
                    'file': runprj_match.group(1),
                    'scene': int(runprj_match.group(2)) if runprj_match.group(2) else None
                })
                continue

        # Don't forget last scene
        if current_scene:
            self.scenes.append(current_scene)

        return {
            'id': self.vnd_id,
            'name': self.mapping['name'],
            'folder': self.mapping['folder'],
            'scenes': self.scenes,
            'rollover_images': self.rollover_images,
            'scene_count': len(self.scenes),
            'hotspot_count': sum(len(s['hotspots']) for s in self.scenes)
        }


def parse_all_vnds():
    """Parse all VND files and generate unified game data"""
    results = {}

    print("=" * 70)
    print("PARSING ALL VND FILES")
    print("=" * 70)

    for txt_file in sorted(VND_EXTRACT_DIR.glob("extracted_data_*.txt")):
        # Extract VND ID from filename
        vnd_id = txt_file.stem.replace('extracted_data_', '')

        if vnd_id not in VND_MAPPING:
            print(f"Skipping unknown VND: {vnd_id}")
            continue

        print(f"\nParsing: {vnd_id}")
        parser = VndParser(vnd_id, txt_file)
        parser.load()
        data = parser.parse()

        print(f"  Scenes: {data['scene_count']}")
        print(f"  Hotspots: {data['hotspot_count']}")
        print(f"  Rollover images: {len(data['rollover_images'])}")

        results[vnd_id] = data

    # Save results
    output_file = OUTPUT_DIR / "complete_game_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total VNDs parsed: {len(results)}")
    print(f"Total scenes: {sum(r['scene_count'] for r in results.values())}")
    print(f"Total hotspots: {sum(r['hotspot_count'] for r in results.values())}")
    print(f"\nOutput saved to: {output_file}")

    return results


if __name__ == '__main__':
    parse_all_vnds()
