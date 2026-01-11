#!/usr/bin/env python3
"""
Parser couleurs1.vnd - Version hiérarchique
Structure: Scènes → Zones cliquables → Textes/Actions

Élimine les duplications et respecte l'ordre du VND.
"""

import struct
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from collections import OrderedDict

VND_PATH = Path(__file__).parent.parent / 'couleurs1' / 'couleurs1.vnd'
OUTPUT_PATH = Path(__file__).parent.parent / 'couleurs1' / 'couleurs1_structured.json'


def read_uint32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<I', data, offset)[0]


def read_int32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<i', data, offset)[0]


class Couleurs1StructuredParser:
    """Parser hiérarchique pour couleurs1.vnd"""

    def __init__(self):
        with open(VND_PATH, 'rb') as f:
            self.data = f.read()
        self.text = self.data.decode('latin-1', errors='replace')
        print(f"Loaded: {len(self.data)} bytes")

    def parse_header(self) -> dict:
        """Parse l'en-tête"""
        def read_len_string(offset: int) -> Tuple[str, int]:
            length = read_uint32(self.data, offset)
            if length > 256:
                return "", offset + 4
            end = offset + 4
            while end < offset + 4 + length and self.data[end] != 0:
                end += 1
            return self.data[offset + 4:end].decode('latin-1'), offset + 4 + length

        header = {
            'signature': self.data[9:15].decode('latin-1'),
            'version': self.data[0x13:0x18].decode('latin-1').rstrip('\x00'),
        }

        offset = 0x1B
        header['project'], offset = read_len_string(offset)
        header['creator'], offset = read_len_string(offset)
        header['checksum'], offset = read_len_string(offset)

        offset += 8
        header['screen'] = {
            'width': read_uint32(self.data, offset),
            'height': read_uint32(self.data, offset + 4)
        }

        return header

    def find_all_elements_ordered(self) -> List[dict]:
        """Trouve TOUS les éléments dans l'ordre du fichier"""
        elements = []

        # 1. Backgrounds (scenes)
        for match in re.finditer(r'euroland\\(\w+\.bmp)', self.text, re.IGNORECASE):
            bg = match.group(1).lower()
            if 'roll' not in bg:
                elements.append({
                    'offset': match.start(),
                    'type': 'background',
                    'file': bg
                })

        # 2. Type 2 rectangles
        pos = 0
        while pos < len(self.data) - 20:
            marker = read_uint32(self.data, pos)
            if marker == 2:
                x1 = read_uint32(self.data, pos + 4)
                y1 = read_uint32(self.data, pos + 8)
                x2 = read_uint32(self.data, pos + 12)
                y2 = read_uint32(self.data, pos + 16)

                if (0 <= x1 <= 700 and 0 <= y1 <= 500 and
                    0 <= x2 <= 700 and 0 <= y2 <= 500 and
                    abs(x2 - x1) >= 5 and abs(y2 - y1) >= 5):
                    elements.append({
                        'offset': pos,
                        'type': 'rectangle',
                        'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2
                    })
                    pos += 20
                    continue
            pos += 1

        # 3. Type 105 polygons
        pos = 0
        while pos < len(self.data) - 12:
            marker = read_uint32(self.data, pos)
            if marker == 105:
                count = read_uint32(self.data, pos + 4)
                if 3 <= count <= 50:
                    points = []
                    valid = True
                    for j in range(count):
                        off = pos + 8 + j * 8
                        if off + 8 > len(self.data):
                            valid = False
                            break
                        x = read_int32(self.data, off)
                        y = read_int32(self.data, off + 4)
                        if not (-100 <= x <= 800 and -100 <= y <= 600):
                            valid = False
                            break
                        points.append([x, y])

                    if valid and points:
                        xs = [p[0] for p in points]
                        ys = [p[1] for p in points]
                        elements.append({
                            'offset': pos,
                            'type': 'polygon',
                            'points': points,
                            'bbox': {'x1': min(xs), 'y1': min(ys), 'x2': max(xs), 'y2': max(ys)},
                            'center': [sum(xs) // len(xs), sum(ys) // len(ys)]
                        })
                        pos += 8 + count * 8
                        continue
            pos += 1

        # 4. Hotspot texts (X Y 125 365 layer text)
        for match in re.finditer(r'(\d{1,3})\s+(\d{1,3})\s+125\s+365\s+(\d+)\s+([^\x00\r\n]+)', self.text):
            x, y = int(match.group(1)), int(match.group(2))
            if 0 <= x <= 640 and 0 <= y <= 480:
                elements.append({
                    'offset': match.start(),
                    'type': 'hotspot_text',
                    'text': match.group(4).strip(),
                    'x': x, 'y': y,
                    'layer': int(match.group(3))
                })

        # 5. Videos
        for match in re.finditer(r'euroland\\(\w+\.avi)', self.text, re.IGNORECASE):
            elements.append({
                'offset': match.start(),
                'type': 'video',
                'file': match.group(1).lower()
            })

        # 6. Audio
        for match in re.finditer(r'(?<!euroland\\)(\w+\.wav)', self.text, re.IGNORECASE):
            elements.append({
                'offset': match.start(),
                'type': 'audio',
                'file': match.group(1).lower()
            })

        # 7. Conditions
        for match in re.finditer(r'(\w+)\s*(=|!=|<|>|<=|>=)\s*(\d+)\s+then\s+(\w+)\s*([^\x00\n]*)', self.text):
            elements.append({
                'offset': match.start(),
                'type': 'condition',
                'variable': match.group(1),
                'operator': match.group(2),
                'value': int(match.group(3)),
                'action': match.group(4),
                'params': match.group(5).strip()[:80]
            })

        # 8. Navigations (scene X, runprj)
        for match in re.finditer(r'\bscene\s+(\d+)', self.text, re.IGNORECASE):
            elements.append({
                'offset': match.start(),
                'type': 'nav_scene',
                'target': int(match.group(1))
            })

        for match in re.finditer(r'runprj\s+([\w\\\.]+)\s+(\d+)', self.text, re.IGNORECASE):
            elements.append({
                'offset': match.start(),
                'type': 'nav_project',
                'project': match.group(1),
                'scene': int(match.group(2))
            })

        # Trier par offset
        elements.sort(key=lambda e: e['offset'])
        return elements

    def build_hierarchy(self, elements: List[dict]) -> List[dict]:
        """Construit la structure hiérarchique par scène"""
        scenes = []
        current_scene = None
        current_zone = None  # Zone cliquable courante (polygon/rectangle)

        # Index des polygons par offset pour déduplication
        polygon_map = {}
        for e in elements:
            if e['type'] == 'polygon':
                polygon_map[e['offset']] = e

        # Parcourir les éléments dans l'ordre
        for elem in elements:
            etype = elem['type']

            if etype == 'background':
                # Nouvelle scène
                current_scene = {
                    'id': len(scenes) + 1,
                    'background': elem['file'],
                    'offset': elem['offset'],
                    'audio': None,
                    'zones': [],  # Zones cliquables
                    'conditions': [],
                    'navigations': []
                }
                scenes.append(current_scene)
                current_zone = None

            elif etype == 'audio':
                if current_scene:
                    if not current_scene['audio']:
                        current_scene['audio'] = elem['file']

            elif etype == 'rectangle':
                if current_scene:
                    current_zone = {
                        'type': 'rectangle',
                        'offset': elem['offset'],
                        'bbox': {'x1': elem['x1'], 'y1': elem['y1'],
                                 'x2': elem['x2'], 'y2': elem['y2']},
                        'center': [(elem['x1'] + elem['x2']) // 2,
                                   (elem['y1'] + elem['y2']) // 2],
                        'texts': [],
                        'videos': [],
                        'actions': []
                    }
                    current_scene['zones'].append(current_zone)

            elif etype == 'polygon':
                if current_scene:
                    current_zone = {
                        'type': 'polygon',
                        'offset': elem['offset'],
                        'points': elem['points'],
                        'bbox': elem['bbox'],
                        'center': elem['center'],
                        'texts': [],
                        'videos': [],
                        'actions': []
                    }
                    current_scene['zones'].append(current_zone)

            elif etype == 'hotspot_text':
                if current_zone:
                    # Ajouter le texte à la zone courante
                    current_zone['texts'].append({
                        'text': elem['text'],
                        'x': elem['x'],
                        'y': elem['y'],
                        'layer': elem['layer']
                    })
                elif current_scene:
                    # Texte sans zone - créer une zone texte
                    text_zone = {
                        'type': 'text_only',
                        'offset': elem['offset'],
                        'texts': [{
                            'text': elem['text'],
                            'x': elem['x'],
                            'y': elem['y'],
                            'layer': elem['layer']
                        }],
                        'videos': [],
                        'actions': []
                    }
                    current_scene['zones'].append(text_zone)
                    current_zone = text_zone

            elif etype == 'video':
                if current_zone:
                    if elem['file'] not in current_zone['videos']:
                        current_zone['videos'].append(elem['file'])
                elif current_scene:
                    # Vidéo au niveau scène
                    if 'scene_videos' not in current_scene:
                        current_scene['scene_videos'] = []
                    current_scene['scene_videos'].append(elem['file'])

            elif etype == 'condition':
                if current_zone:
                    current_zone['actions'].append({
                        'type': 'condition',
                        'if': f"{elem['variable']} {elem['operator']} {elem['value']}",
                        'then': elem['action'],
                        'params': elem['params']
                    })
                elif current_scene:
                    current_scene['conditions'].append({
                        'if': f"{elem['variable']} {elem['operator']} {elem['value']}",
                        'then': elem['action'],
                        'params': elem['params']
                    })

            elif etype == 'nav_scene':
                if current_zone:
                    current_zone['actions'].append({
                        'type': 'goto_scene',
                        'target': elem['target']
                    })
                elif current_scene:
                    current_scene['navigations'].append({
                        'type': 'scene',
                        'target': elem['target']
                    })

            elif etype == 'nav_project':
                if current_zone:
                    current_zone['actions'].append({
                        'type': 'goto_project',
                        'project': elem['project'],
                        'scene': elem['scene']
                    })
                elif current_scene:
                    current_scene['navigations'].append({
                        'type': 'project',
                        'project': elem['project'],
                        'scene': elem['scene']
                    })

        return scenes

    def cleanup_scenes(self, scenes: List[dict]) -> List[dict]:
        """Nettoie et déduplique les scènes"""
        cleaned = []
        seen_backgrounds = set()

        for scene in scenes:
            bg = scene['background']

            # Fusionner les scènes avec le même background
            existing = None
            for c in cleaned:
                if c['background'] == bg:
                    existing = c
                    break

            if existing:
                # Fusionner les zones
                existing['zones'].extend(scene['zones'])
                existing['conditions'].extend(scene['conditions'])
                existing['navigations'].extend(scene['navigations'])
            else:
                cleaned.append(scene)

        # Réassigner les IDs
        for i, scene in enumerate(cleaned):
            scene['id'] = i + 1

            # Nettoyer les zones vides
            scene['zones'] = [z for z in scene['zones']
                             if z.get('texts') or z.get('videos') or z.get('actions')
                             or z['type'] in ['polygon', 'rectangle']]

            # Compter les stats
            scene['stats'] = {
                'zones': len(scene['zones']),
                'polygons': len([z for z in scene['zones'] if z['type'] == 'polygon']),
                'rectangles': len([z for z in scene['zones'] if z['type'] == 'rectangle']),
                'texts': sum(len(z.get('texts', [])) for z in scene['zones']),
                'conditions': len(scene['conditions'])
            }

        return cleaned

    def parse(self) -> dict:
        """Parse complet"""
        print("\nParsing couleurs1.vnd (hiérarchique)...")

        header = self.parse_header()
        print(f"  {header['project']} v{header['version']}")

        elements = self.find_all_elements_ordered()
        print(f"  Éléments trouvés: {len(elements)}")

        # Compter par type
        by_type = {}
        for e in elements:
            t = e['type']
            by_type[t] = by_type.get(t, 0) + 1

        for t, c in sorted(by_type.items()):
            print(f"    {t}: {c}")

        scenes = self.build_hierarchy(elements)
        print(f"  Scènes construites: {len(scenes)}")

        scenes = self.cleanup_scenes(scenes)
        print(f"  Scènes après nettoyage: {len(scenes)}")

        # Stats globales
        total_zones = sum(s['stats']['zones'] for s in scenes)
        total_polygons = sum(s['stats']['polygons'] for s in scenes)
        total_rects = sum(s['stats']['rectangles'] for s in scenes)
        total_texts = sum(s['stats']['texts'] for s in scenes)

        return {
            'file': 'couleurs1.vnd',
            'country': 'Euroland',
            'header': header,
            'stats': {
                'scenes': len(scenes),
                'total_zones': total_zones,
                'polygons': total_polygons,
                'rectangles': total_rects,
                'texts': total_texts
            },
            'scenes': scenes
        }


def main():
    parser = Couleurs1StructuredParser()
    data = parser.parse()

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"Sauvegardé: {OUTPUT_PATH}")
    print(f"{'=' * 60}")

    # Afficher quelques scènes
    print("\nExemple de scènes:")
    for scene in data['scenes'][:3]:
        print(f"\n  Scene {scene['id']}: {scene['background']}")
        print(f"    Zones: {scene['stats']['zones']} ({scene['stats']['polygons']} poly, {scene['stats']['rectangles']} rect)")
        if scene['zones']:
            z = scene['zones'][0]
            print(f"    Première zone: {z['type']}")
            if z.get('texts'):
                print(f"      Textes: {[t['text'][:30] for t in z['texts'][:2]]}")


if __name__ == '__main__':
    main()
