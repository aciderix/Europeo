#!/usr/bin/env python3
"""
VND Complete Parser - Version complète basée sur les spécifications Rev. 2
Extrait TOUS les types de hotspots et données de scènes

Types supportés:
- Type 2: Rectangles cliquables [02][x1][y1][x2][y2]
- Type 38: Définitions texte hotspot "X Y W H layer name"
- Type 105: Polygones [105][count][coords...] (PAS de champ length!)

Règle d'association: Type 105 appartient au Type 38 qui le précède immédiatement
"""

import struct
import os
import json
import glob
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional
from pathlib import Path


def read_uint32(data: bytes, offset: int) -> int:
    """Lit un entier 32-bit Little Endian"""
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<I', data, offset)[0]


def read_int32(data: bytes, offset: int) -> int:
    """Lit un entier signé 32-bit Little Endian"""
    if offset + 4 > len(data):
        return 0
    return struct.unpack_from('<i', data, offset)[0]


def read_string(data: bytes, offset: int, max_len: int = 256) -> str:
    """Lit une chaîne null-terminée"""
    end = offset
    while end < min(offset + max_len, len(data)) and data[end] != 0:
        end += 1
    try:
        return data[offset:end].decode('latin-1')
    except:
        return ""


@dataclass
class VNDHeader:
    """En-tête du fichier VND"""
    signature: str = ""
    version: str = ""
    project_name: str = ""
    creator: str = ""
    checksum: str = ""
    screen_width: int = 640
    screen_height: int = 480
    color_depth: int = 16
    dll_path: str = ""


@dataclass
class Rectangle:
    """Zone rectangulaire cliquable (Type 2)"""
    x1: int
    y1: int
    x2: int
    y2: int
    offset: int = 0

    @property
    def width(self) -> int:
        return abs(self.x2 - self.x1)

    @property
    def height(self) -> int:
        return abs(self.y2 - self.y1)

    @property
    def center(self) -> Tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)


@dataclass
class Polygon:
    """Zone polygonale cliquable (Type 105)"""
    point_count: int
    points: List[Tuple[int, int]]
    offset: int = 0

    @property
    def bounding_box(self) -> Tuple[int, int, int, int]:
        if not self.points:
            return (0, 0, 0, 0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def center(self) -> Tuple[int, int]:
        if not self.points:
            return (0, 0)
        return (
            sum(p[0] for p in self.points) // len(self.points),
            sum(p[1] for p in self.points) // len(self.points)
        )


@dataclass
class Hotspot:
    """Zone interactive complète"""
    id: int
    hotspot_type: int  # 2 = rectangle, 38 = text+polygon
    name: str = ""
    text_x: int = 0
    text_y: int = 0
    text_w: int = 0
    text_h: int = 0
    layer: int = 0
    rectangle: Optional[Rectangle] = None
    polygon: Optional[Polygon] = None
    offset: int = 0

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour JSON"""
        result = {
            'id': self.id,
            'type': 'rectangle' if self.hotspot_type == 2 else 'polygon',
            'name': self.name,
            'layer': self.layer,
            'offset': self.offset,
        }

        if self.rectangle:
            result['clickable_area'] = {
                'type': 'rectangle',
                'x1': self.rectangle.x1,
                'y1': self.rectangle.y1,
                'x2': self.rectangle.x2,
                'y2': self.rectangle.y2,
                'width': self.rectangle.width,
                'height': self.rectangle.height,
                'center': list(self.rectangle.center)
            }

        if self.polygon:
            bbox = self.polygon.bounding_box
            result['clickable_area'] = {
                'type': 'polygon',
                'point_count': self.polygon.point_count,
                'points': self.polygon.points,
                'bbox': {'x1': bbox[0], 'y1': bbox[1], 'x2': bbox[2], 'y2': bbox[3]},
                'center': list(self.polygon.center)
            }

        if self.hotspot_type == 38:
            result['text_position'] = {
                'x': self.text_x,
                'y': self.text_y,
                'w': self.text_w,
                'h': self.text_h
            }

        return result


@dataclass
class Scene:
    """Scène du jeu"""
    id: int
    name: str = ""
    background: str = ""
    audio: str = ""
    hotspots: List[Hotspot] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'background': self.background,
            'audio': self.audio,
            'hotspots': [h.to_dict() for h in self.hotspots]
        }


class VNDCompleteParser:
    """Parser VND complet basé sur les spécifications Rev. 2"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data: bytes = b''
        self.header: Optional[VNDHeader] = None
        self.hotspots: List[Hotspot] = []
        self.scenes: List[Scene] = []
        self.variables: List[str] = []
        self.records: List[dict] = []

    def load(self):
        """Charge le fichier VND"""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()
        print(f"Loaded {len(self.data)} bytes from {self.filepath}")

    def parse_header(self) -> int:
        """Parse l'en-tête VND, retourne l'offset après l'en-tête"""
        # Magic bytes (9 bytes)
        magic = self.data[0:9]

        # Signature "VNFILE" at offset 9
        signature = read_string(self.data, 9, 6)
        if signature != "VNFILE":
            print(f"Warning: Invalid signature '{signature}'")

        # Version at 0x13
        version = read_string(self.data, 0x13, 6)

        # Project name (length-prefixed at 0x1B)
        offset = 0x1B
        name_len = read_uint32(self.data, offset)
        offset += 4
        project_name = read_string(self.data, offset, name_len)
        offset += name_len

        # Creator
        creator_len = read_uint32(self.data, offset)
        offset += 4
        creator = read_string(self.data, offset, creator_len)
        offset += creator_len

        # Checksum
        checksum_len = read_uint32(self.data, offset)
        offset += 4
        checksum = read_string(self.data, offset, checksum_len)
        offset += checksum_len

        # Skip padding
        offset += 8

        # Screen dimensions
        screen_width = read_uint32(self.data, offset)
        screen_height = read_uint32(self.data, offset + 4)
        color_depth = read_uint32(self.data, offset + 8)
        offset += 24  # Skip flags too

        # DLL path
        dll_len = read_uint32(self.data, offset)
        offset += 4
        dll_path = read_string(self.data, offset, dll_len)
        offset += dll_len

        self.header = VNDHeader(
            signature=signature,
            version=version,
            project_name=project_name,
            creator=creator,
            checksum=checksum,
            screen_width=screen_width if 0 < screen_width < 10000 else 640,
            screen_height=screen_height if 0 < screen_height < 10000 else 480,
            color_depth=color_depth if 0 < color_depth < 100 else 16,
            dll_path=dll_path
        )

        return offset

    def find_type2_rectangles(self) -> List[Rectangle]:
        """Trouve tous les rectangles Type 2"""
        rectangles = []
        pos = 0

        while pos < len(self.data) - 20:
            type_marker = read_uint32(self.data, pos)

            if type_marker == 2:
                x1 = read_uint32(self.data, pos + 4)
                y1 = read_uint32(self.data, pos + 8)
                x2 = read_uint32(self.data, pos + 12)
                y2 = read_uint32(self.data, pos + 16)

                # Valider les coordonnées
                if (0 <= x1 <= 800 and 0 <= y1 <= 600 and
                    0 <= x2 <= 800 and 0 <= y2 <= 600 and
                    x1 != x2 and y1 != y2):
                    rectangles.append(Rectangle(
                        x1=x1, y1=y1, x2=x2, y2=y2, offset=pos
                    ))
                    pos += 20
                    continue

            pos += 1

        return rectangles

    def find_type105_polygons(self) -> List[Polygon]:
        """Trouve tous les polygones Type 105"""
        polygons = []
        pos = 0

        while pos < len(self.data) - 12:
            type_marker = read_uint32(self.data, pos)

            if type_marker == 105:
                point_count = read_uint32(self.data, pos + 4)

                # Valider le nombre de points
                if 3 <= point_count <= 30:
                    coords_size = point_count * 8
                    if pos + 8 + coords_size <= len(self.data):
                        points = []
                        valid = True

                        for i in range(point_count):
                            x = read_int32(self.data, pos + 8 + i * 8)
                            y = read_int32(self.data, pos + 8 + i * 8 + 4)

                            if not (-100 <= x <= 2000 and -100 <= y <= 1000):
                                valid = False
                                break

                            points.append((x, y))

                        if valid:
                            polygons.append(Polygon(
                                point_count=point_count,
                                points=points,
                                offset=pos
                            ))
                            pos += 8 + coords_size
                            continue

            pos += 1

        return polygons

    def find_type38_records(self) -> List[dict]:
        """Trouve tous les records Type 38 (définitions texte hotspot)"""
        records = []
        pos = 0

        while pos < len(self.data) - 16:
            # Chercher le séparateur 01 00 00 00
            separator = read_uint32(self.data, pos)

            if separator == 1:
                length = read_uint32(self.data, pos + 4)
                record_type = read_uint32(self.data, pos + 8)

                if record_type == 38 and 10 < length < 200:
                    text_start = pos + 12
                    if text_start + length <= len(self.data):
                        try:
                            text = self.data[text_start:text_start + length].decode('latin-1').strip('\x00')
                            parts = text.split(None, 5)

                            if len(parts) >= 5:
                                records.append({
                                    'offset': pos,
                                    'text_end': text_start + length,
                                    'x': int(parts[0]),
                                    'y': int(parts[1]),
                                    'w': int(parts[2]),
                                    'h': int(parts[3]),
                                    'layer': int(parts[4]) if len(parts) > 4 else 0,
                                    'name': parts[5] if len(parts) > 5 else "",
                                    'raw': text
                                })
                        except (ValueError, UnicodeDecodeError):
                            pass

            pos += 1

        return records

    def associate_hotspots(self):
        """Associe les Type 38 avec leurs Type 105 et crée les hotspots"""
        rectangles = self.find_type2_rectangles()
        polygons = self.find_type105_polygons()
        type38_records = self.find_type38_records()

        hotspot_id = 0

        # Créer les hotspots rectangulaires (Type 2)
        for rect in rectangles:
            self.hotspots.append(Hotspot(
                id=hotspot_id,
                hotspot_type=2,
                name=f"rect_{hotspot_id}",
                rectangle=rect,
                offset=rect.offset
            ))
            hotspot_id += 1

        # Créer les hotspots Type 38 et associer les polygones
        for record in type38_records:
            hotspot = Hotspot(
                id=hotspot_id,
                hotspot_type=38,
                name=record['name'],
                text_x=record['x'],
                text_y=record['y'],
                text_w=record['w'],
                text_h=record['h'],
                layer=record['layer'],
                offset=record['offset']
            )

            # Chercher un polygone Type 105 qui suit immédiatement
            text_end = record['text_end']
            for polygon in polygons:
                # Le polygone doit être juste après (avec padding possible)
                if text_end <= polygon.offset <= text_end + 50:
                    hotspot.polygon = polygon
                    break

            self.hotspots.append(hotspot)
            hotspot_id += 1

        # Statistiques
        rect_count = len([h for h in self.hotspots if h.hotspot_type == 2])
        poly_count = len([h for h in self.hotspots if h.hotspot_type == 38 and h.polygon])
        text_only = len([h for h in self.hotspots if h.hotspot_type == 38 and not h.polygon])

        print(f"\nHotspots trouvés:")
        print(f"  - Type 2 (rectangles): {rect_count}")
        print(f"  - Type 38 avec polygone: {poly_count}")
        print(f"  - Type 38 sans polygone: {text_only}")
        print(f"  - Total: {len(self.hotspots)}")

    def find_media_references(self) -> dict:
        """Trouve les références média (images, sons, vidéos)"""
        media = {
            'backgrounds': [],
            'audio': [],
            'video': []
        }

        # Chercher les patterns de fichiers
        text = self.data.decode('latin-1', errors='ignore')

        import re

        # Images BMP
        for match in re.finditer(r'[\w\\]+\.bmp', text, re.IGNORECASE):
            path = match.group()
            if path not in media['backgrounds']:
                media['backgrounds'].append(path)

        # Audio WAV
        for match in re.finditer(r'[\w\\]+\.wav', text, re.IGNORECASE):
            path = match.group()
            if path not in media['audio']:
                media['audio'].append(path)

        # Vidéo AVI
        for match in re.finditer(r'[\w\\]+\.avi', text, re.IGNORECASE):
            path = match.group()
            if path not in media['video']:
                media['video'].append(path)

        return media

    def find_variables(self) -> List[str]:
        """Trouve les variables du jeu"""
        variables = []
        pos = 0

        # Les variables sont des chaînes en majuscules dans la table des ressources
        text = self.data.decode('latin-1', errors='ignore')

        import re
        # Pattern: mot en majuscules de 3+ caractères
        for match in re.finditer(r'\b[A-Z][A-Z0-9_]{2,}\b', text):
            var = match.group()
            if var not in variables and var not in ['VNFILE', 'SOPRA', 'MULTIMEDIA']:
                variables.append(var)

        return variables[:100]  # Limiter à 100 premières

    def parse(self):
        """Parse complet du fichier"""
        self.load()

        print("\n" + "=" * 60)
        print(f"Parsing: {os.path.basename(self.filepath)}")
        print("=" * 60)

        # Header
        header_end = self.parse_header()
        print(f"\nHeader:")
        print(f"  Project: {self.header.project_name}")
        print(f"  Version: {self.header.version}")
        print(f"  Creator: {self.header.creator}")
        print(f"  Screen: {self.header.screen_width}x{self.header.screen_height}")

        # Hotspots
        self.associate_hotspots()

        # Media
        media = self.find_media_references()
        print(f"\nMédia:")
        print(f"  - Backgrounds: {len(media['backgrounds'])}")
        print(f"  - Audio: {len(media['audio'])}")
        print(f"  - Video: {len(media['video'])}")

        # Variables
        self.variables = self.find_variables()
        print(f"\nVariables: {len(self.variables)}")

    def to_json(self) -> dict:
        """Exporte en JSON"""
        media = self.find_media_references()

        return {
            'file': os.path.basename(self.filepath),
            'header': {
                'project': self.header.project_name,
                'version': self.header.version,
                'creator': self.header.creator,
                'screen': {
                    'width': self.header.screen_width,
                    'height': self.header.screen_height,
                    'depth': self.header.color_depth
                }
            },
            'hotspots': [h.to_dict() for h in self.hotspots],
            'media': media,
            'variables': self.variables[:50],
            'stats': {
                'total_hotspots': len(self.hotspots),
                'rectangles': len([h for h in self.hotspots if h.hotspot_type == 2]),
                'polygons': len([h for h in self.hotspots if h.polygon]),
                'text_only': len([h for h in self.hotspots if h.hotspot_type == 38 and not h.polygon])
            }
        }


def parse_all_vnd_files(base_path: str) -> dict:
    """Parse tous les fichiers VND dans les sous-dossiers"""
    results = {}

    # Trouver tous les fichiers .vnd
    vnd_files = glob.glob(os.path.join(base_path, '**', '*.vnd'), recursive=True)

    print(f"\nTrouvé {len(vnd_files)} fichiers VND")

    for vnd_path in vnd_files:
        try:
            parser = VNDCompleteParser(vnd_path)
            parser.parse()

            # Extraire le nom du pays/dossier
            rel_path = os.path.relpath(vnd_path, base_path)
            country = os.path.dirname(rel_path) or os.path.splitext(os.path.basename(vnd_path))[0]

            results[country] = parser.to_json()

        except Exception as e:
            print(f"Erreur parsing {vnd_path}: {e}")

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        # Par défaut, parser tous les VND du projet Europeo
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        print("=" * 60)
        print("VND COMPLETE PARSER - Basé sur spécifications Rev. 2")
        print("=" * 60)
        print(f"\nBase path: {base_path}")

        results = parse_all_vnd_files(base_path)

        # Sauvegarder le JSON
        output_path = os.path.join(base_path, 'Doc', 'game_data_complete.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n{'=' * 60}")
        print(f"Résultats sauvegardés dans: {output_path}")
        print(f"{'=' * 60}")

        # Résumé
        total_hotspots = sum(r['stats']['total_hotspots'] for r in results.values())
        total_rect = sum(r['stats']['rectangles'] for r in results.values())
        total_poly = sum(r['stats']['polygons'] for r in results.values())

        print(f"\nRésumé global:")
        print(f"  - Pays/régions: {len(results)}")
        print(f"  - Total hotspots: {total_hotspots}")
        print(f"  - Rectangles (Type 2): {total_rect}")
        print(f"  - Polygones (Type 105): {total_poly}")

    else:
        # Parser un seul fichier
        parser = VNDCompleteParser(sys.argv[1])
        parser.parse()

        # Afficher le JSON
        print("\n" + "=" * 60)
        print("JSON OUTPUT")
        print("=" * 60)
        print(json.dumps(parser.to_json(), indent=2, ensure_ascii=False))
