#!/usr/bin/env python3
"""
VND Unified Parser - Combine toutes les méthodes d'extraction

Combine:
1. Type 2 rectangles (binaire) - zones cliquables simples
2. Pattern regex "X Y 125 365 layer text" - hotspots nommés
3. Type 105 polygons (binaire) - zones cliquables complexes

Produit un JSON complet avec TOUTES les zones interactives.
"""

import struct
import re
import json
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any

BASE_DIR = Path(__file__).parent.parent


@dataclass
class ClickableArea:
    """Zone cliquable unifiée"""
    id: int
    area_type: str  # 'rectangle' ou 'polygon'
    name: str = ""
    text_x: int = 0
    text_y: int = 0
    layer: int = 0
    # Rectangle coords
    x1: int = 0
    y1: int = 0
    x2: int = 0
    y2: int = 0
    # Polygon points
    points: List[Tuple[int, int]] = field(default_factory=list)
    # Associated data
    video: str = ""
    goto_scene: int = 0
    offset: int = 0

    def to_dict(self) -> dict:
        result = {
            'id': self.id,
            'type': self.area_type,
            'name': self.name,
            'layer': self.layer,
        }

        if self.area_type == 'rectangle':
            result['bbox'] = {
                'x1': self.x1, 'y1': self.y1,
                'x2': self.x2, 'y2': self.y2
            }
            result['center'] = {
                'x': (self.x1 + self.x2) // 2,
                'y': (self.y1 + self.y2) // 2
            }

        if self.area_type == 'polygon' and self.points:
            xs = [p[0] for p in self.points]
            ys = [p[1] for p in self.points]
            result['points'] = self.points
            result['bbox'] = {
                'x1': min(xs), 'y1': min(ys),
                'x2': max(xs), 'y2': max(ys)
            }
            result['center'] = {
                'x': sum(xs) // len(xs),
                'y': sum(ys) // len(ys)
            }

        if self.text_x or self.text_y:
            result['text_position'] = {'x': self.text_x, 'y': self.text_y}

        if self.video:
            result['video'] = self.video

        if self.goto_scene:
            result['goto_scene'] = self.goto_scene

        return result


@dataclass
class Scene:
    """Scène du jeu"""
    id: int
    background: str
    audio: str = ""
    clickable_areas: List[ClickableArea] = field(default_factory=list)


class VndUnifiedParser:
    """Parser VND unifié combinant toutes les méthodes"""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()
        self.text_content = self.data.decode('latin-1', errors='replace')

    # ========== TYPE 2 RECTANGLES (binaire) ==========

    def find_type2_rectangles(self) -> List[Tuple[int, int, int, int, int]]:
        """Trouve tous les rectangles Type 2 : [02][x1][y1][x2][y2]"""
        rectangles = []
        pos = 0

        while pos < len(self.data) - 20:
            marker = struct.unpack_from('<I', self.data, pos)[0]

            if marker == 2:
                x1 = struct.unpack_from('<I', self.data, pos + 4)[0]
                y1 = struct.unpack_from('<I', self.data, pos + 8)[0]
                x2 = struct.unpack_from('<I', self.data, pos + 12)[0]
                y2 = struct.unpack_from('<I', self.data, pos + 16)[0]

                # Valider les coordonnées
                if (0 <= x1 <= 800 and 0 <= y1 <= 600 and
                    0 <= x2 <= 800 and 0 <= y2 <= 600 and
                    x1 != x2 and y1 != y2 and
                    abs(x2 - x1) >= 10 and abs(y2 - y1) >= 10):
                    rectangles.append((pos, x1, y1, x2, y2))
                    pos += 20
                    continue

            pos += 1

        return rectangles

    # ========== TYPE 105 POLYGONS (binaire) ==========

    def find_type105_polygons(self) -> List[Tuple[int, List[Tuple[int, int]]]]:
        """Trouve tous les polygones Type 105 : [105][count][coords...]"""
        polygons = []
        pos = 0

        while pos < len(self.data) - 12:
            marker = struct.unpack_from('<I', self.data, pos)[0]

            if marker == 105:
                count = struct.unpack_from('<I', self.data, pos + 4)[0]

                if 3 <= count <= 50:
                    points = []
                    valid = True

                    for j in range(count):
                        offset = pos + 8 + j * 8
                        if offset + 8 > len(self.data):
                            valid = False
                            break

                        x = struct.unpack_from('<i', self.data, offset)[0]
                        y = struct.unpack_from('<i', self.data, offset + 4)[0]

                        if not (-200 <= x <= 800 and -200 <= y <= 600):
                            valid = False
                            break

                        points.append((x, y))

                    if valid and points:
                        polygons.append((pos, points))
                        pos += 8 + count * 8
                        continue

            pos += 1

        return polygons

    # ========== PATTERN REGEX HOTSPOTS ==========

    def find_hotspot_texts(self) -> List[Tuple[int, str, int, int, int]]:
        """Pattern: X Y 125 365 layer text"""
        hotspots = []
        pattern = r'(\d{1,3})\s+(\d{1,3})\s+125\s+365\s+(\d+)\s+([^\x00\r\n]+)'

        for match in re.finditer(pattern, self.text_content):
            offset = match.start()
            x = int(match.group(1))
            y = int(match.group(2))
            layer = int(match.group(3))
            text = match.group(4).strip()

            if 0 <= x <= 640 and 0 <= y <= 480 and len(text) > 1:
                hotspots.append((offset, text, x, y, layer))

        return hotspots

    def find_font_records(self) -> List[int]:
        """Records de police (marqueurs de frontière)"""
        fonts = []
        pattern = r'(\d{1,2})\s+\d+\s+#[0-9A-Fa-f]{6}\s+[^\x00]+'

        for match in re.finditer(pattern, self.text_content):
            fonts.append(match.start())

        return sorted(fonts)

    # ========== MEDIA REFERENCES ==========

    def find_videos(self) -> List[Tuple[int, str]]:
        """Trouve les références vidéo"""
        videos = []
        for match in re.finditer(r'([\w]+\.avi)', self.text_content, re.IGNORECASE):
            videos.append((match.start(), match.group(1)))
        return videos

    def find_backgrounds(self) -> List[Tuple[int, str]]:
        """Trouve les images de fond"""
        backgrounds = []
        pattern = r'(?<![\\/:])(\w+\.bmp)(?!\w)'

        for match in re.finditer(pattern, self.text_content, re.IGNORECASE):
            name = match.group(1).lower()
            if 'roll' not in name and 'over' not in name:
                backgrounds.append((match.start(), match.group(1)))

        return backgrounds

    def find_scene_navigations(self) -> List[Tuple[int, int]]:
        """Trouve les navigations de scène (e.g., '39i')"""
        navigations = []
        pattern = r'(?<!\d)(\d{1,3})([a-z])(?!\w)'

        for match in re.finditer(pattern, self.text_content):
            scene_id = int(match.group(1))
            if 1 <= scene_id <= 200:
                navigations.append((match.start(), scene_id))

        return navigations

    def find_audio(self) -> List[Tuple[int, str]]:
        """Trouve les fichiers audio"""
        audio = []
        for match in re.finditer(r'([\w]+\.wav)', self.text_content, re.IGNORECASE):
            audio.append((match.start(), match.group(1)))
        return audio

    # ========== ASSOCIATION ==========

    def parse(self) -> Dict[str, Any]:
        """Parse complet et associe toutes les données"""
        # Extraire toutes les données
        type2_rects = self.find_type2_rectangles()
        type105_polys = self.find_type105_polygons()
        hotspot_texts = self.find_hotspot_texts()
        videos = self.find_videos()
        backgrounds = self.find_backgrounds()
        navigations = self.find_scene_navigations()
        font_records = self.find_font_records()
        audio_files = self.find_audio()

        print(f"  Type 2 rectangles: {len(type2_rects)}")
        print(f"  Type 105 polygons: {len(type105_polys)}")
        print(f"  Hotspot texts: {len(hotspot_texts)}")
        print(f"  Videos: {len(videos)}")
        print(f"  Backgrounds: {len(backgrounds)}")

        # Créer les scènes basées sur les backgrounds
        scenes = []
        backgrounds = sorted(backgrounds, key=lambda x: x[0])

        for i, (bg_offset, bg_name) in enumerate(backgrounds):
            scene = Scene(id=i + 1, background=bg_name)

            # Trouver l'audio associé (proche du background)
            for audio_offset, audio_name in audio_files:
                if bg_offset - 100 < audio_offset < bg_offset + 200:
                    scene.audio = audio_name
                    break

            scenes.append(scene)

        if not scenes:
            scenes = [Scene(id=1, background="unknown.bmp")]

        # Créer la liste unifiée des zones cliquables
        all_areas: List[ClickableArea] = []
        area_id = 0

        # 1. Ajouter les rectangles Type 2
        for rect_offset, x1, y1, x2, y2 in type2_rects:
            area = ClickableArea(
                id=area_id,
                area_type='rectangle',
                name=f"rect_{area_id}",
                x1=x1, y1=y1, x2=x2, y2=y2,
                offset=rect_offset
            )
            all_areas.append(area)
            area_id += 1

        # 2. Ajouter les hotspots texte avec leurs polygones associés
        def find_next_font(offset: int) -> int:
            for font_offset in font_records:
                if font_offset > offset:
                    return font_offset
            return offset + 2000

        for text_offset, text, x, y, layer in hotspot_texts:
            area = ClickableArea(
                id=area_id,
                area_type='polygon',  # Sera changé si pas de polygone
                name=text,
                text_x=x,
                text_y=y,
                layer=layer,
                offset=text_offset
            )

            # Chercher polygone associé
            next_font = find_next_font(text_offset)
            search_limit = min(next_font, text_offset + 1500)

            for poly_offset, points in type105_polys:
                if text_offset < poly_offset < search_limit:
                    area.points = points
                    break

            # Si pas de polygone, utiliser la position du texte comme rectangle
            if not area.points:
                area.area_type = 'text_only'
                area.x1 = x
                area.y1 = y
                area.x2 = x + 100  # Largeur par défaut
                area.y2 = y + 20   # Hauteur par défaut

            # Chercher vidéo associée
            for vid_offset, video in videos:
                if text_offset - 100 < vid_offset < search_limit:
                    area.video = video
                    break

            # Chercher navigation
            for nav_offset, goto in navigations:
                if text_offset < nav_offset < search_limit:
                    area.goto_scene = goto
                    break

            all_areas.append(area)
            area_id += 1

        # Associer les zones aux scènes par proximité
        for area in all_areas:
            assigned = False
            for scene in reversed(scenes):
                # Trouver le background de la scène
                for bg_offset, bg_name in backgrounds:
                    if bg_name == scene.background:
                        if bg_offset < area.offset:
                            scene.clickable_areas.append(area)
                            assigned = True
                            break
                if assigned:
                    break

            if not assigned and scenes:
                scenes[0].clickable_areas.append(area)

        # Construire le résultat
        result = {
            'file': self.filepath.name,
            'stats': {
                'type2_rectangles': len(type2_rects),
                'type105_polygons': len(type105_polys),
                'hotspot_texts': len(hotspot_texts),
                'total_clickable': len(all_areas),
                'scenes': len(scenes),
            },
            'scenes': []
        }

        for scene in scenes:
            scene_dict = {
                'id': scene.id,
                'background': scene.background,
                'audio': scene.audio,
                'hotspots': [area.to_dict() for area in scene.clickable_areas]
            }
            result['scenes'].append(scene_dict)

        return result


def parse_all_countries() -> Dict[str, Any]:
    """Parse tous les pays"""
    vnd_folders = {
        'couleurs1': 'Euroland',
        'france': 'France',
        'allem': 'Allemagne',
        'angl': 'Angleterre',
        'autr': 'Autriche',
        'belge': 'Belgique',
        'danem': 'Danemark',
        'ecosse': 'Écosse',
        'espa': 'Espagne',
        'finlan': 'Finlande',
        'grece': 'Grèce',
        'holl': 'Pays-Bas',
        'irland': 'Irlande',
        'italie': 'Italie',
        'portu': 'Portugal',
        'suede': 'Suède',
        'biblio': 'Bibliothèque',
        'barre': 'Barre outils',
        'frontal': 'Démarrage',
    }

    all_data = {
        'game': 'Europeo',
        'version': '2.0',
        'resolution': {'width': 640, 'height': 480},
        'countries': {}
    }

    print("=" * 70)
    print("VND UNIFIED PARSER - Rectangles + Polygons + Hotspots")
    print("=" * 70)

    total_rects = 0
    total_polys = 0
    total_hotspots = 0

    for folder, name in sorted(vnd_folders.items()):
        vnd_path = BASE_DIR / folder / f"{folder}.vnd"

        if folder == 'angl':
            vnd_path = BASE_DIR / 'angl' / 'angleterre.vnd'
        elif folder == 'frontal':
            vnd_path = BASE_DIR / 'frontal' / 'start.vnd'

        if not vnd_path.exists():
            print(f"\n{name}: VND not found")
            continue

        print(f"\n{name} ({folder}):")

        try:
            parser = VndUnifiedParser(vnd_path)
            data = parser.parse()

            all_data['countries'][folder] = {
                'name': name,
                'folder': folder,
                **data
            }

            total_rects += data['stats']['type2_rectangles']
            total_polys += data['stats']['type105_polygons']
            total_hotspots += data['stats']['hotspot_texts']

        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'=' * 70}")
    print("RÉSUMÉ GLOBAL")
    print(f"{'=' * 70}")
    print(f"  Type 2 rectangles: {total_rects}")
    print(f"  Type 105 polygons: {total_polys}")
    print(f"  Hotspots texte:    {total_hotspots}")
    print(f"  Pays:              {len(all_data['countries'])}")

    return all_data


def main():
    data = parse_all_countries()

    output_path = BASE_DIR / 'Doc' / 'game_data_unified.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSauvegardé: {output_path}")

    # Copier aussi pour l'app React
    react_path = BASE_DIR / 'react-app' / 'public' / 'assets' / 'game_data_unified.json'
    with open(react_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Copié pour React: {react_path}")


if __name__ == '__main__':
    main()
