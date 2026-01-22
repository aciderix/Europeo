#!/usr/bin/env python3
"""
Parser dédié pour couleurs1.vnd (Euroland)
Produit un JSON détaillé et facile à analyser pour le développement du moteur React.

Extrait:
- Header complet
- Variables du jeu
- Scènes avec backgrounds et audio
- Hotspots Type 2 (rectangles) et Type 38+105 (texte + polygones)
- Commandes conditionnelles
- Références média
"""

import struct
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict

VND_PATH = Path(__file__).parent.parent / 'couleurs1' / 'couleurs1.vnd'
OUTPUT_PATH = Path(__file__).parent.parent / 'couleurs1' / 'couleurs1_data.json'


def read_uint32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<I', data, offset)[0]


def read_int32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<i', data, offset)[0]


class Couleurs1Parser:
    """Parser spécialisé pour couleurs1.vnd"""

    def __init__(self):
        with open(VND_PATH, 'rb') as f:
            self.data = f.read()
        self.text = self.data.decode('latin-1', errors='replace')
        print(f"Loaded: {len(self.data)} bytes")

    # ==================== HEADER ====================

    def parse_header(self) -> dict:
        """Parse l'en-tête VND"""
        def read_string(offset: int, max_len: int = 256) -> Tuple[str, int]:
            end = offset
            while end < min(offset + max_len, len(self.data)) and self.data[end] != 0:
                end += 1
            return self.data[offset:end].decode('latin-1'), end

        def read_len_string(offset: int) -> Tuple[str, int]:
            length = read_uint32(self.data, offset)
            if length > 256:
                return "", offset + 4
            s, _ = read_string(offset + 4, length)
            return s, offset + 4 + length

        header = {}

        # Magic + signature
        header['magic'] = self.data[0:9].hex()
        header['signature'] = self.data[9:15].decode('latin-1')

        # Version
        header['version'], _ = read_string(0x13, 6)

        # Project, creator, checksum
        offset = 0x1B
        header['project'], offset = read_len_string(offset)
        header['creator'], offset = read_len_string(offset)
        header['checksum'], offset = read_len_string(offset)

        # Screen dimensions (après padding de 8 bytes)
        offset += 8
        header['screen'] = {
            'width': read_uint32(self.data, offset),
            'height': read_uint32(self.data, offset + 4),
            'depth': read_uint32(self.data, offset + 8)
        }

        return header

    # ==================== VARIABLES ====================

    def find_variables(self) -> List[str]:
        """Trouve les variables du jeu (noms en majuscules)"""
        variables = []
        # Pattern: mot en majuscules, probablement une variable
        seen = set()

        for match in re.finditer(r'\b([A-Z][A-Z0-9_]{2,20})\b', self.text):
            var = match.group(1)
            # Filtrer les faux positifs
            if var not in seen and var not in ['VNFILE', 'SOPRA', 'BMP', 'AVI', 'WAV', 'DLL']:
                seen.add(var)
                variables.append(var)

        return sorted(variables)

    # ==================== TYPE 2 RECTANGLES ====================

    def find_rectangles(self) -> List[dict]:
        """Trouve les rectangles Type 2"""
        rectangles = []
        pos = 0

        while pos < len(self.data) - 20:
            marker = read_uint32(self.data, pos)

            if marker == 2:
                x1 = read_uint32(self.data, pos + 4)
                y1 = read_uint32(self.data, pos + 8)
                x2 = read_uint32(self.data, pos + 12)
                y2 = read_uint32(self.data, pos + 16)

                # Valider
                if (0 <= x1 <= 700 and 0 <= y1 <= 500 and
                    0 <= x2 <= 700 and 0 <= y2 <= 500 and
                    abs(x2 - x1) >= 5 and abs(y2 - y1) >= 5):

                    rectangles.append({
                        'offset': f"0x{pos:04x}",
                        'x1': x1, 'y1': y1,
                        'x2': x2, 'y2': y2,
                        'width': abs(x2 - x1),
                        'height': abs(y2 - y1),
                        'center': [(x1 + x2) // 2, (y1 + y2) // 2]
                    })
                    pos += 20
                    continue

            pos += 1

        return rectangles

    # ==================== TYPE 105 POLYGONS ====================

    def find_polygons(self) -> List[dict]:
        """Trouve les polygones Type 105"""
        polygons = []
        pos = 0

        while pos < len(self.data) - 12:
            marker = read_uint32(self.data, pos)

            if marker == 105:
                count = read_uint32(self.data, pos + 4)

                if 3 <= count <= 50:
                    points = []
                    valid = True

                    for j in range(count):
                        offset = pos + 8 + j * 8
                        if offset + 8 > len(self.data):
                            valid = False
                            break

                        x = read_int32(self.data, offset)
                        y = read_int32(self.data, offset + 4)

                        if not (-100 <= x <= 800 and -100 <= y <= 600):
                            valid = False
                            break

                        points.append([x, y])

                    if valid and points:
                        xs = [p[0] for p in points]
                        ys = [p[1] for p in points]

                        polygons.append({
                            'offset': f"0x{pos:04x}",
                            'point_count': count,
                            'points': points,
                            'bbox': {
                                'x1': min(xs), 'y1': min(ys),
                                'x2': max(xs), 'y2': max(ys)
                            },
                            'center': [sum(xs) // len(xs), sum(ys) // len(ys)]
                        })
                        pos += 8 + count * 8
                        continue

            pos += 1

        return polygons

    # ==================== HOTSPOT TEXTS ====================

    def find_hotspot_texts(self) -> List[dict]:
        """Trouve les hotspots texte (pattern X Y 125 365 layer text)"""
        hotspots = []
        pattern = r'(\d{1,3})\s+(\d{1,3})\s+125\s+365\s+(\d+)\s+([^\x00\r\n]+)'

        for match in re.finditer(pattern, self.text):
            x = int(match.group(1))
            y = int(match.group(2))
            layer = int(match.group(3))
            text = match.group(4).strip()

            if 0 <= x <= 640 and 0 <= y <= 480 and len(text) > 0:
                hotspots.append({
                    'offset': f"0x{match.start():04x}",
                    'text': text,
                    'text_x': x,
                    'text_y': y,
                    'layer': layer
                })

        return hotspots

    # ==================== SCENES ====================

    def find_scenes(self) -> List[dict]:
        """Trouve les scènes (backgrounds BMP)"""
        scenes = []
        seen_bgs = set()

        # Pattern pour les BMP (pas les rollovers)
        pattern = r'euroland\\(\w+\.bmp)'

        for match in re.finditer(pattern, self.text, re.IGNORECASE):
            bg = match.group(1).lower()

            # Filtrer les rollovers et doublons
            if 'roll' not in bg and bg not in seen_bgs:
                seen_bgs.add(bg)
                scenes.append({
                    'id': len(scenes) + 1,
                    'offset': f"0x{match.start():04x}",
                    'background': bg,
                    'path': f"euroland/{bg}"
                })

        return scenes

    # ==================== MEDIA ====================

    def find_videos(self) -> List[dict]:
        """Trouve les vidéos AVI"""
        videos = []
        seen = set()

        pattern = r'euroland\\(\w+\.avi)'
        for match in re.finditer(pattern, self.text, re.IGNORECASE):
            video = match.group(1).lower()
            if video not in seen:
                seen.add(video)
                videos.append({
                    'offset': f"0x{match.start():04x}",
                    'file': video,
                    'path': f"euroland/{video}"
                })

        return videos

    def find_audio(self) -> List[dict]:
        """Trouve les fichiers audio WAV"""
        audio = []
        seen = set()

        for match in re.finditer(r'(\w+\.wav)', self.text, re.IGNORECASE):
            wav = match.group(1).lower()
            if wav not in seen:
                seen.add(wav)
                audio.append({
                    'offset': f"0x{match.start():04x}",
                    'file': wav
                })

        return audio

    # ==================== CONDITIONS ====================

    def find_conditions(self) -> List[dict]:
        """Trouve les commandes conditionnelles"""
        conditions = []

        # Pattern: variable op value then action
        pattern = r'(\w+)\s*(=|!=|<|>|<=|>=)\s*(\d+)\s+then\s+(\w+)\s*(.*?)(?=\x00|\n|$)'

        for match in re.finditer(pattern, self.text, re.IGNORECASE):
            conditions.append({
                'offset': f"0x{match.start():04x}",
                'variable': match.group(1),
                'operator': match.group(2),
                'value': int(match.group(3)),
                'action': match.group(4),
                'params': match.group(5).strip()[:50]  # Limiter la longueur
            })

        return conditions

    # ==================== NAVIGATION ====================

    def find_navigations(self) -> List[dict]:
        """Trouve les commandes de navigation"""
        navigations = []

        # scene X
        for match in re.finditer(r'\bscene\s+(\d+)', self.text, re.IGNORECASE):
            navigations.append({
                'type': 'scene',
                'offset': f"0x{match.start():04x}",
                'target': int(match.group(1))
            })

        # runprj
        for match in re.finditer(r'runprj\s+([\w\\\.]+)\s+(\d+)', self.text, re.IGNORECASE):
            navigations.append({
                'type': 'runprj',
                'offset': f"0x{match.start():04x}",
                'project': match.group(1),
                'scene': int(match.group(2))
            })

        return navigations

    # ==================== ASSOCIATION ====================

    def associate_hotspots_with_polygons(self, hotspots: List[dict], polygons: List[dict]) -> List[dict]:
        """Associe les hotspots texte avec leurs polygones"""
        # Convertir les offsets en int pour comparaison
        def offset_to_int(offset_str: str) -> int:
            return int(offset_str, 16)

        for hotspot in hotspots:
            hs_offset = offset_to_int(hotspot['offset'])

            # Chercher un polygone qui suit le hotspot (dans les 2000 bytes)
            for polygon in polygons:
                poly_offset = offset_to_int(polygon['offset'])

                if hs_offset < poly_offset < hs_offset + 2000:
                    hotspot['polygon'] = polygon
                    break

        return hotspots

    # ==================== MAIN PARSE ====================

    def parse(self) -> dict:
        """Parse complet de couleurs1.vnd"""
        print("\nParsing couleurs1.vnd...")

        header = self.parse_header()
        print(f"  Header: {header['project']} v{header['version']}")

        variables = self.find_variables()
        print(f"  Variables: {len(variables)}")

        rectangles = self.find_rectangles()
        print(f"  Type 2 rectangles: {len(rectangles)}")

        polygons = self.find_polygons()
        print(f"  Type 105 polygons: {len(polygons)}")

        hotspots = self.find_hotspot_texts()
        print(f"  Hotspot texts: {len(hotspots)}")

        # Associer hotspots et polygones
        hotspots = self.associate_hotspots_with_polygons(hotspots, polygons)
        with_poly = len([h for h in hotspots if 'polygon' in h])
        print(f"  Hotspots with polygon: {with_poly}")

        scenes = self.find_scenes()
        print(f"  Scenes (backgrounds): {len(scenes)}")

        videos = self.find_videos()
        print(f"  Videos: {len(videos)}")

        audio = self.find_audio()
        print(f"  Audio files: {len(audio)}")

        conditions = self.find_conditions()
        print(f"  Conditions: {len(conditions)}")

        navigations = self.find_navigations()
        print(f"  Navigations: {len(navigations)}")

        return {
            'file': 'couleurs1.vnd',
            'country': 'Euroland',
            'header': header,
            'stats': {
                'file_size': len(self.data),
                'variables': len(variables),
                'rectangles': len(rectangles),
                'polygons': len(polygons),
                'hotspots': len(hotspots),
                'hotspots_with_polygon': with_poly,
                'scenes': len(scenes),
                'videos': len(videos),
                'audio': len(audio),
                'conditions': len(conditions),
                'navigations': len(navigations)
            },
            'variables': variables[:50],  # Top 50
            'rectangles': rectangles,
            'polygons': polygons,
            'hotspots': hotspots,
            'scenes': scenes,
            'videos': videos,
            'audio': audio,
            'conditions': conditions[:100],  # Top 100
            'navigations': navigations
        }


def main():
    parser = Couleurs1Parser()
    data = parser.parse()

    # Sauvegarder
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"Sauvegardé: {OUTPUT_PATH}")
    print(f"{'=' * 60}")

    # Afficher un résumé
    print("\nRÉSUMÉ:")
    for key, value in data['stats'].items():
        print(f"  {key}: {value}")


if __name__ == '__main__':
    main()
