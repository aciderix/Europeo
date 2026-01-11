#!/usr/bin/env python3
"""
Parser couleurs1.vnd v3 - Structure orientée jeu avec scene IDs
Extrait les liens hotspot → scene à partir du binaire
"""

import json
import re
import struct
from pathlib import Path
from typing import Dict, List, Any, Optional


def clean_text(text: str) -> str:
    """Nettoie un texte des caractères de contrôle"""
    return text.rstrip('\x00\x01\x02\x03\x04').strip()


def make_id(text: str) -> str:
    """Convertit un texte en ID propre"""
    text = clean_text(text).lower()
    text = re.sub(r'[àâä]', 'a', text)
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[îï]', 'i', text)
    text = re.sub(r'[ôö]', 'o', text)
    text = re.sub(r'[ùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text[:30] if text else None


def make_scene_id(background: str) -> str:
    """Convertit un nom de fichier en ID de scène"""
    name = background.lower().replace('.bmp', '').replace('.jpg', '')
    return make_id(name) or "unknown"


class SceneMapper:
    """Mappe les numéros de scène aux backgrounds"""

    def __init__(self, vnd_path: str):
        with open(vnd_path, 'rb') as f:
            self.data = f.read()

        self.scene_map = {}  # scene_num -> background
        self.bg_to_num = {}  # background -> scene_num
        self._build_scene_map()
        self._extract_video_scene_links()

    def _build_scene_map(self):
        """Construit le mapping numéro de scène → background"""
        # Trouver tous les backgrounds dans l'ordre
        pattern = rb'euroland\\([a-z0-9_]+\.bmp)'
        seen = set()
        bgs = []

        for m in re.finditer(pattern, self.data, re.I):
            bg = m.group(1).decode().lower()
            # Ignorer les transitions et doublons
            if bg not in seen and not bg.startswith('trans'):
                seen.add(bg)
                bgs.append((m.start(), bg))

        # Trier par offset et numéroter (1-based)
        bgs.sort()
        for i, (offset, bg) in enumerate(bgs, 1):
            self.scene_map[i] = bg
            self.bg_to_num[bg] = i

    def _extract_video_scene_links(self):
        """Extrait les liens vidéo → scene_id"""
        self.video_to_scene = {}

        # Pattern: xxx.avi suivi de " 1" puis scene ID "Xi"
        for m in re.finditer(rb'([a-z0-9_]+\.avi)\s+1', self.data, re.I):
            video = m.group(1).decode().lower()
            # Chercher le scene ID dans les 30 octets suivants
            after = self.data[m.end():m.end()+30]
            scene_match = re.search(rb'([0-9]+)i', after)
            if scene_match:
                scene_num = int(scene_match.group(1))
                self.video_to_scene[video] = scene_num

    def get_scene_for_video(self, video: str) -> Optional[int]:
        """Retourne le numéro de scène pour une vidéo"""
        video_lower = video.lower()
        return self.video_to_scene.get(video_lower)

    def get_background_for_scene(self, scene_num: int) -> Optional[str]:
        """Retourne le background pour un numéro de scène"""
        return self.scene_map.get(scene_num)

    def get_scene_id_for_video(self, video: str) -> Optional[str]:
        """Retourne l'ID de scène (nom du background) pour une vidéo"""
        scene_num = self.get_scene_for_video(video)
        if scene_num:
            bg = self.get_background_for_scene(scene_num)
            if bg:
                return make_scene_id(bg)
        return None


def build_onclick(zone: dict, scene_mapper: SceneMapper) -> dict:
    """Construit l'objet onClick pour un hotspot avec les liens de scène"""
    on_click = {}

    # Vidéos
    videos = zone.get('videos', [])
    if videos:
        video = videos[0]
        on_click['playVideo'] = video

        # Trouver la scène cible
        target_scene = scene_mapper.get_scene_id_for_video(video)
        if target_scene:
            on_click['loadScene'] = target_scene

    # Navigations depuis les actions
    for action in zone.get('actions', []):
        if action.get('type') == 'goto_scene':
            scene_num = action.get('target')
            bg = scene_mapper.get_background_for_scene(scene_num)
            if bg:
                on_click['loadScene'] = make_scene_id(bg)
        elif action.get('type') == 'goto_project':
            project = action.get('project', '')
            match = re.search(r'([^\\]+)\.vnp', project)
            if match:
                on_click['loadProject'] = match.group(1)
            if action.get('scene'):
                on_click['targetSceneNum'] = action['scene']

    # Conditions simplifiées (pas toutes les conditions)
    conditions = [a for a in zone.get('actions', []) if a.get('type') == 'condition']
    important_conditions = [c for c in conditions if 'bonus' in c.get('if', '') or 'score' in c.get('if', '')]
    if important_conditions:
        on_click['conditions'] = []
        for cond in important_conditions[:3]:  # Max 3 conditions
            cond_obj = {
                'if': cond.get('if', ''),
                'then': cond.get('then', ''),
            }
            if cond.get('params'):
                cond_obj['params'] = clean_text(cond['params'])
            on_click['conditions'].append(cond_obj)

    return on_click


def build_onhover(zone: dict) -> Optional[dict]:
    """Construit l'objet onHover pour un hotspot"""
    texts = zone.get('texts', [])
    if not texts:
        return None

    main_text = clean_text(texts[0].get('text', ''))
    if not main_text:
        return None

    on_hover = {'text': main_text}

    if len(texts) > 1:
        additional = [clean_text(t['text']) for t in texts[1:] if clean_text(t.get('text', ''))]
        if additional:
            on_hover['additionalTexts'] = additional

    return on_hover


def transform_zone_to_hotspot(zone: dict, scene_id: str, index: int, scene_mapper: SceneMapper) -> dict:
    """Transforme une zone v2 en hotspot format jeu"""

    texts = zone.get('texts', [])
    hint = clean_text(texts[0]['text']) if texts else None
    hotspot_id = make_id(hint) if hint else f"zone_{index}"

    hotspot = {'id': hotspot_id}

    # Shape et coordonnées
    zone_type = zone.get('type', 'unknown')
    if zone_type == 'polygon':
        hotspot['shape'] = 'polygon'
        if zone.get('points'):
            hotspot['points'] = zone['points']
        if zone.get('bbox'):
            bbox = zone['bbox']
            hotspot['bounds'] = {
                'x': bbox.get('x1', 0),
                'y': bbox.get('y1', 0),
                'width': bbox.get('x2', 0) - bbox.get('x1', 0),
                'height': bbox.get('y2', 0) - bbox.get('y1', 0)
            }
    elif zone_type == 'rectangle':
        hotspot['shape'] = 'rectangle'
        if zone.get('bounds'):
            bounds = zone['bounds']
            hotspot['bounds'] = {
                'x': bounds.get('x1', 0),
                'y': bounds.get('y1', 0),
                'width': bounds.get('x2', 0) - bounds.get('x1', 0),
                'height': bounds.get('y2', 0) - bounds.get('y1', 0)
            }

    # onHover
    on_hover = build_onhover(zone)
    if on_hover:
        hotspot['onHover'] = on_hover

    # onClick avec liens de scène
    on_click = build_onclick(zone, scene_mapper)
    if on_click:
        hotspot['onClick'] = on_click

    return hotspot


def transform_scene(scene: dict, scene_index: int, scene_mapper: SceneMapper) -> tuple:
    """Transforme une scène v2 en format jeu"""

    background = scene.get('background', f'scene_{scene_index}.bmp')
    scene_id = make_scene_id(background)
    scene_num = scene_mapper.bg_to_num.get(background.lower(), scene_index)

    game_scene = {
        'id': scene_id,
        'sceneNum': scene_num,
        'background': background,
    }

    if scene.get('audio'):
        game_scene['music'] = scene['audio']

    hotspots = []
    for i, zone in enumerate(scene.get('zones', [])):
        hotspot = transform_zone_to_hotspot(zone, scene_id, i, scene_mapper)
        if hotspot.get('onHover') or hotspot.get('onClick'):
            hotspots.append(hotspot)

    game_scene['hotspots'] = hotspots

    return scene_id, game_scene


def transform_v2_to_game(v2_data: dict, scene_mapper: SceneMapper) -> dict:
    """Transforme la structure v2 en format jeu final"""

    scenes = {}
    main_scene_id = None

    for i, scene in enumerate(v2_data.get('scenes', [])):
        scene_id, game_scene = transform_scene(scene, i, scene_mapper)

        if scene_id in scenes:
            scene_id = f"{scene_id}_{i}"
            game_scene['id'] = scene_id

        scenes[scene_id] = game_scene

        if 'face' in scene.get('background', '').lower():
            main_scene_id = scene_id

    # Afficher le mapping vidéo → scène
    print("\n=== Mapping vidéo → scène ===")
    for video, scene_num in sorted(scene_mapper.video_to_scene.items()):
        bg = scene_mapper.get_background_for_scene(scene_num)
        scene_id = make_scene_id(bg) if bg else f"scene_{scene_num}"
        print(f"  {video} → scene {scene_num} ({scene_id})")

    game = {
        'game': {
            'title': 'Euroland - Les Couleurs',
            'version': v2_data.get('header', {}).get('version', '2.136'),
            'screen': v2_data.get('header', {}).get('screen', {'width': 640, 'height': 480}),
            'assets': {
                'mainBackground': 'face.bmp',
                'music': 'music.wav'
            },
            'variables': {
                'score': 0,
                'money': 0
            },
            'inventory': [],
            'mainScene': main_scene_id or list(scenes.keys())[0] if scenes else 'main',
            'scenes': scenes
        }
    }

    return game


def main():
    vnd_path = Path("/home/user/Europeo/couleurs1/couleurs1.vnd")
    v2_path = Path("/home/user/Europeo/couleurs1/couleurs1_structured.json")
    output_path = Path("/home/user/Europeo/couleurs1/couleurs1_game.json")

    if not vnd_path.exists():
        print(f"VND non trouvé: {vnd_path}")
        return

    if not v2_path.exists():
        print(f"JSON v2 non trouvé: {v2_path}")
        return

    print(f"Chargement du mapper de scènes...")
    scene_mapper = SceneMapper(str(vnd_path))

    print(f"\n=== Mapping scène → background ===")
    for num, bg in sorted(scene_mapper.scene_map.items())[:15]:
        print(f"  Scene {num:2} = {bg}")
    print(f"  ... ({len(scene_mapper.scene_map)} scènes total)")

    print(f"\nChargement de {v2_path.name}...")
    with open(v2_path, 'r', encoding='utf-8') as f:
        v2_data = json.load(f)

    print(f"Transformation en format jeu...")
    game_data = transform_v2_to_game(v2_data, scene_mapper)

    scenes = game_data['game']['scenes']
    total_hotspots = sum(len(s['hotspots']) for s in scenes.values())
    print(f"\n  Scènes: {len(scenes)}")
    print(f"  Hotspots: {total_hotspots}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(game_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Sauvegardé: {output_path}")
    print(f"{'='*60}")

    # Afficher la scène principale
    main_id = game_data['game']['mainScene']
    if main_id in scenes:
        print(f"\nScène principale ({main_id}):")
        main_scene = scenes[main_id]
        # Afficher seulement les hotspots avec loadScene
        for h in main_scene['hotspots'][:6]:
            print(f"\n  {h['id']}:")
            if h.get('onHover'):
                print(f"    onHover: {h['onHover'].get('text', '')[:40]}")
            if h.get('onClick'):
                oc = h['onClick']
                if oc.get('playVideo'):
                    print(f"    playVideo: {oc['playVideo']}")
                if oc.get('loadScene'):
                    print(f"    loadScene: {oc['loadScene']}")


if __name__ == "__main__":
    main()
