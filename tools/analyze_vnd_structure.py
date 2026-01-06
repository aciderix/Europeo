#!/usr/bin/env python3
"""
Analyze VND structure from extracted hex data to understand scene and hotspot definitions.
Based on analysis of couleurs1.vnd (Euroland)
"""

import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

class VndAnalyzer:
    def __init__(self, txt_file: Path):
        self.txt_file = txt_file
        self.lines = []
        self.scenes = []
        self.current_scene = None
        self.current_hotspot = None

    def load(self):
        """Load the extracted text file"""
        with open(self.txt_file, 'r', encoding='utf-8', errors='ignore') as f:
            self.lines = f.readlines()
        print(f"Loaded {len(self.lines)} lines from {self.txt_file}")

    def parse_line(self, line: str) -> Tuple[str, str]:
        """Parse a line to extract offset and content"""
        # Format: @OFFSET: content or linenum→@OFFSET: content
        match = re.match(r'.*@([0-9A-F]+):\s*(.*)', line.strip())
        if match:
            return match.group(1), match.group(2)
        return None, line.strip()

    def is_background_bmp(self, content: str) -> Optional[str]:
        """Check if content is a background BMP (not rollover)"""
        # Background BMPs are full paths without "rollover" in them
        match = re.match(r'^([a-zA-Z\\]+\.bmp)$', content, re.IGNORECASE)
        if match and 'rollover' not in content.lower() and 'roll' not in content.lower():
            return match.group(1)
        return None

    def is_audio(self, content: str) -> Optional[str]:
        """Check if content is an audio file"""
        match = re.match(r'^([a-zA-Z0-9_\\]+\.wav)(\s+\d+)?$', content, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def is_font_definition(self, content: str) -> bool:
        """Check if content is a font definition"""
        # Format: size style #color Font Name
        return bool(re.match(r'^\d+\s+\d+\s+#[0-9a-fA-F]{6}\s+.+$', content))

    def is_hotspot(self, content: str) -> Optional[Dict]:
        """Check if content is a hotspot definition
        Format: X Y W H Layer Text
        """
        match = re.match(r'^(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)$', content)
        if match:
            return {
                'x': int(match.group(1)),
                'y': int(match.group(2)),
                'param3': int(match.group(3)),  # Not sure what this is
                'param4': int(match.group(4)),  # Not sure what this is
                'layer': int(match.group(5)),
                'text': match.group(6)
            }
        return None

    def is_video(self, content: str) -> Optional[Dict]:
        """Check if content is a video play command"""
        # Format: path\file.avi 1 [x1 y1 x2 y2]
        match = re.match(r'^([a-zA-Z0-9_\\]+\.avi)\s+(\d+)(?:\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+))?', content)
        if match:
            result = {
                'file': match.group(1),
                'param': int(match.group(2))
            }
            if match.group(3):
                result['rect'] = {
                    'x1': int(match.group(3)),
                    'y1': int(match.group(4)),
                    'x2': int(match.group(5)),
                    'y2': int(match.group(6))
                }
            return result
        return None

    def is_condition(self, content: str) -> Optional[Dict]:
        """Check if content is a condition"""
        # Format: variable op value then action [else action]
        match = re.match(r'^(\w+)\s*([<>=!]+)\s*(\d+)\s+then\s+(.+?)(?:\s+else\s+(.+))?$', content)
        if match:
            return {
                'variable': match.group(1),
                'operator': match.group(2),
                'value': int(match.group(3)),
                'then_action': match.group(4),
                'else_action': match.group(5)
            }
        return None

    def is_scene_navigation(self, content: str) -> Optional[int]:
        """Check if content is a scene navigation (e.g., 39i, 51j)"""
        match = re.match(r'^(\d+)[a-z]$', content)
        if match:
            return int(match.group(1))
        return None

    def analyze(self):
        """Analyze the VND structure"""
        scene_idx = 0
        in_data_section = False

        for i, line in enumerate(self.lines):
            offset, content = self.parse_line(line)

            if not content or content.startswith('=') or content.startswith('-'):
                continue

            # Skip header until we reach actual data
            if 'CHAÎNES EXTRAITES' in content or 'TOUTES LES' in content:
                in_data_section = True
                continue
            if not in_data_section and offset is None:
                continue

            # Check for background BMP (start of new scene)
            bmp = self.is_background_bmp(content)
            if bmp:
                # Save previous scene
                if self.current_scene:
                    self.scenes.append(self.current_scene)

                # Start new scene
                scene_idx += 1
                self.current_scene = {
                    'index': scene_idx,
                    'offset': offset,
                    'background': bmp,
                    'audio': None,
                    'hotspots': [],
                    'actions': [],
                    'conditions': []
                }
                self.current_hotspot = None
                continue

            # Check for audio (often precedes background)
            audio = self.is_audio(content)
            if audio:
                if self.current_scene:
                    self.current_scene['audio'] = audio
                continue

            # Check for hotspot
            if self.current_scene:
                hotspot = self.is_hotspot(content)
                if hotspot:
                    self.current_hotspot = hotspot
                    self.current_scene['hotspots'].append(hotspot)
                    continue

                # Check for video (action for current hotspot)
                video = self.is_video(content)
                if video:
                    if self.current_hotspot:
                        self.current_hotspot['video'] = video
                    else:
                        self.current_scene['actions'].append({'type': 'video', **video})
                    continue

                # Check for condition
                condition = self.is_condition(content)
                if condition:
                    self.current_scene['conditions'].append(condition)
                    continue

                # Check for scene navigation
                nav = self.is_scene_navigation(content)
                if nav is not None:
                    if self.current_hotspot:
                        self.current_hotspot['goto_scene'] = nav
                    self.current_hotspot = None
                    continue

        # Don't forget last scene
        if self.current_scene:
            self.scenes.append(self.current_scene)

        return self.scenes


def analyze_euroland():
    """Analyze Euroland (couleurs1) specifically"""
    txt_file = Path("/home/user/Europeo/vnd hexa extract/extracted_data_all/extracted_data_couleurs1.txt")

    analyzer = VndAnalyzer(txt_file)
    analyzer.load()
    scenes = analyzer.analyze()

    print(f"\n{'='*80}")
    print(f"EUROLAND SCENE ANALYSIS")
    print(f"{'='*80}")
    print(f"Total scenes found: {len(scenes)}")

    for scene in scenes:
        print(f"\n--- Scene {scene['index']} ---")
        print(f"  Background: {scene['background']}")
        if scene['audio']:
            print(f"  Audio: {scene['audio']}")
        print(f"  Hotspots: {len(scene['hotspots'])}")
        for hs in scene['hotspots']:
            text = hs.get('text', 'N/A')
            x, y = hs.get('x', 0), hs.get('y', 0)
            video = hs.get('video', {}).get('file', 'none')
            goto = hs.get('goto_scene', 'N/A')
            print(f"    [{x:4d},{y:4d}] '{text[:30]}...' -> video:{video}, goto:{goto}")

    # Save to JSON
    output_file = Path("/home/user/Europeo/Doc/euroland_scenes.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {output_file}")

    return scenes


if __name__ == '__main__':
    analyze_euroland()
