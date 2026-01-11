#!/usr/bin/env python3
"""
Parser couleurs1.vnd v3 - Structure orientée jeu
Transforme la structure hiérarchique v2 en format jeu avec actions sémantiques
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


def clean_text(text: str) -> str:
    """Nettoie un texte des caractères de contrôle"""
    return text.rstrip('\x00\x01\x02\x03\x04').strip()


def make_id(text: str) -> str:
    """Convertit un texte en ID propre"""
    text = clean_text(text).lower()
    # Remplacer les caractères spéciaux
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


def parse_navigation(action: dict) -> dict:
    """Parse une action de navigation"""
    result = {}

    if action.get('type') == 'goto_scene':
        result['loadScene'] = f"scene_{action['target']}"
    elif action.get('type') == 'goto_project':
        project = action.get('project', '')
        # Extraire le nom du projet (ex: ..\\couleurs1\\couleurs1.vnp -> couleurs1)
        match = re.search(r'([^\\]+)\.vnp', project)
        if match:
            result['loadProject'] = match.group(1)
        if action.get('scene'):
            result['loadScene'] = f"scene_{action['scene']}"

    return result


def build_onclick(zone: dict) -> dict:
    """Construit l'objet onClick pour un hotspot"""
    on_click = {}

    # Vidéos
    videos = zone.get('videos', [])
    if videos:
        if len(videos) == 1:
            on_click['playVideo'] = videos[0]
        else:
            on_click['playVideos'] = videos

    # Navigations depuis les actions
    for action in zone.get('actions', []):
        nav = parse_navigation(action)
        on_click.update(nav)

    # Conditions
    conditions = [a for a in zone.get('actions', []) if a.get('type') == 'condition']
    if conditions:
        on_click['conditions'] = []
        for cond in conditions:
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

    # Premier texte comme texte de survol principal
    main_text = clean_text(texts[0].get('text', ''))
    if not main_text:
        return None

    on_hover = {'text': main_text}

    # Si plusieurs textes, les ajouter
    if len(texts) > 1:
        on_hover['additionalTexts'] = [
            clean_text(t['text']) for t in texts[1:]
            if clean_text(t.get('text', ''))
        ]

    return on_hover


def transform_zone_to_hotspot(zone: dict, scene_id: str, index: int) -> dict:
    """Transforme une zone v2 en hotspot format jeu"""

    # Générer l'ID
    texts = zone.get('texts', [])
    hint = clean_text(texts[0]['text']) if texts else None
    hotspot_id = make_id(hint) if hint else f"zone_{index}"

    hotspot = {
        'id': hotspot_id,
    }

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

    # onClick
    on_click = build_onclick(zone)
    if on_click:
        hotspot['onClick'] = on_click

    return hotspot


def transform_scene(scene: dict, scene_index: int) -> tuple:
    """Transforme une scène v2 en format jeu"""

    background = scene.get('background', f'scene_{scene_index}.bmp')
    scene_id = make_scene_id(background)

    game_scene = {
        'id': scene_id,
        'background': background,
    }

    # Audio si présent
    if scene.get('audio'):
        game_scene['music'] = scene['audio']

    # Transformer les zones en hotspots
    hotspots = []
    for i, zone in enumerate(scene.get('zones', [])):
        hotspot = transform_zone_to_hotspot(zone, scene_id, i)
        # Ne pas ajouter les hotspots vides (sans hover ni click)
        if hotspot.get('onHover') or hotspot.get('onClick'):
            hotspots.append(hotspot)

    game_scene['hotspots'] = hotspots

    return scene_id, game_scene


def transform_v2_to_game(v2_data: dict) -> dict:
    """Transforme la structure v2 en format jeu final"""

    scenes = {}
    main_scene_id = None

    for i, scene in enumerate(v2_data.get('scenes', [])):
        scene_id, game_scene = transform_scene(scene, i)

        # Éviter les doublons
        if scene_id in scenes:
            scene_id = f"{scene_id}_{i}"
            game_scene['id'] = scene_id

        scenes[scene_id] = game_scene

        # Identifier la scène principale (face.bmp)
        if 'face' in scene.get('background', '').lower():
            main_scene_id = scene_id

    # Construire la structure finale
    game = {
        'game': {
            'title': 'Euroland - Les Couleurs',
            'version': v2_data.get('header', {}).get('version', '2.136'),
            'screen': v2_data.get('header', {}).get('screen', {
                'width': 640,
                'height': 480
            }),
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
    v2_path = Path("/home/user/Europeo/couleurs1/couleurs1_structured.json")
    output_path = Path("/home/user/Europeo/couleurs1/couleurs1_game.json")

    if not v2_path.exists():
        print(f"Fichier v2 non trouvé: {v2_path}")
        print("Exécutez d'abord parse_couleurs1_v2.py")
        return

    print(f"Chargement de {v2_path.name}...")
    with open(v2_path, 'r', encoding='utf-8') as f:
        v2_data = json.load(f)

    print(f"Transformation en format jeu...")
    game_data = transform_v2_to_game(v2_data)

    # Stats
    scenes = game_data['game']['scenes']
    total_hotspots = sum(len(s['hotspots']) for s in scenes.values())
    print(f"  Scènes: {len(scenes)}")
    print(f"  Hotspots: {total_hotspots}")

    # Sauvegarder
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
        print(json.dumps(main_scene, indent=2, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()
