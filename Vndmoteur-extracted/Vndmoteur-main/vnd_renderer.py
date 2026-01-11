#!/usr/bin/env python3
"""
VND Scene Renderer - Correct HTML/SVG Visualization
====================================================

Based on proven binary format from vnd_polygon_parser.py:
- Type 105 (0x69): Polygon records
- Type 38 (0x26): Hotspot text records

Usage:
    python vnd_renderer.py couleurs1.vnd
"""

import sys
import os
import struct
import re
import json
import webbrowser
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict


@dataclass
class Polygon:
    """Clickable polygon area - PROVEN FORMAT"""
    offset: int
    points: List[Tuple[int, int]]

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        if not self.points:
            return (0, 0, 0, 0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def center(self) -> Tuple[int, int]:
        bbox = self.bbox
        return ((bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2)

    @property
    def svg_points(self) -> str:
        return " ".join(f"{x},{y}" for x, y in self.points)


@dataclass
class Hotspot:
    """Hotspot with text and polygon"""
    offset: int
    text: str
    text_x: int
    text_y: int
    layer: int
    polygon: Optional[Polygon] = None
    type_id: int = 38


@dataclass
class StringRecord:
    """Generic string record"""
    offset: int
    type_id: int
    text: str


class VNDRenderer:
    """Render VND scenes using correct binary format"""

    RECORD_TYPE_POLYGON = 105  # 0x69
    RECORD_TYPE_HOTSPOT = 38   # 0x26

    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.data = f.read()
        self.text_content = self.data.decode('latin-1', errors='replace')
        self.polygons: List[Polygon] = []
        self.hotspots: List[Hotspot] = []
        self.strings: List[StringRecord] = []

    def find_polygons(self) -> List[Polygon]:
        """Find all polygon records (type 105) - PROVEN FORMAT"""
        polygons = []
        i = 0

        while i < len(self.data) - 8:
            record_type = struct.unpack_from('<I', self.data, i)[0]

            if record_type == self.RECORD_TYPE_POLYGON:
                count = struct.unpack_from('<I', self.data, i + 4)[0]

                if 3 <= count <= 50:
                    points = []
                    valid = True

                    for j in range(count):
                        offset = i + 8 + j * 8
                        if offset + 8 > len(self.data):
                            valid = False
                            break

                        x = struct.unpack_from('<i', self.data, offset)[0]
                        y = struct.unpack_from('<i', self.data, offset + 4)[0]

                        # Validate coordinates (screen range with margin)
                        if not (-200 <= x <= 2000 and -200 <= y <= 1000):
                            valid = False
                            break

                        points.append((x, y))

                    if valid and points:
                        polygons.append(Polygon(offset=i, points=points))
                        i += 8 + count * 8
                        continue

            i += 1

        return polygons

    def find_hotspot_texts(self) -> List[Hotspot]:
        """Find hotspot text records (pattern: X Y 125 365 layer text)"""
        hotspots = []

        # Pattern: X Y 125 365 layer text
        pattern = r'(\d{1,4})\s+(\d{1,3})\s+125\s+365\s+(\d+)\s+([^\x00\r\n]+)'

        for match in re.finditer(pattern, self.text_content):
            offset = match.start()
            x = int(match.group(1))
            y = int(match.group(2))
            layer = int(match.group(3))
            text = match.group(4).strip()

            # Filter valid coordinates and text
            if 0 <= x <= 2000 and 0 <= y <= 600 and len(text) > 1 and len(text) < 100:
                hotspots.append(Hotspot(
                    offset=offset,
                    text=text,
                    text_x=x,
                    text_y=y,
                    layer=layer
                ))

        return hotspots

    def find_strings(self) -> List[StringRecord]:
        """Find all string records [type:u32][length:u32][text]"""
        strings = []
        i = 0

        while i < len(self.data) - 8:
            r_type = struct.unpack_from('<I', self.data, i)[0]
            length = struct.unpack_from('<I', self.data, i + 4)[0]

            # Skip polygons (handled separately)
            if r_type == self.RECORD_TYPE_POLYGON:
                count = length
                if 3 <= count <= 50:
                    i += 8 + count * 8
                    continue

            # String record
            if 1 <= length <= 500 and i + 8 + length <= len(self.data):
                s_bytes = self.data[i + 8:i + 8 + length]
                if all(32 <= b <= 126 or 160 <= b <= 255 for b in s_bytes):
                    text = s_bytes.decode('latin-1', errors='ignore')
                    strings.append(StringRecord(offset=i, type_id=r_type, text=text))
                    i += 8 + length
                    continue

            i += 1

        return strings

    def associate_hotspots_polygons(self):
        """Associate hotspots with their nearest following polygon"""
        for hotspot in self.hotspots:
            # Find the first polygon after this hotspot
            for polygon in self.polygons:
                if polygon.offset > hotspot.offset and polygon.offset < hotspot.offset + 2000:
                    hotspot.polygon = polygon
                    break

    def parse(self):
        """Parse the VND file"""
        self.polygons = self.find_polygons()
        self.hotspots = self.find_hotspot_texts()
        self.strings = self.find_strings()
        self.associate_hotspots_polygons()

    def generate_html(self) -> str:
        """Generate interactive HTML visualization"""

        # Determine canvas size
        max_x = 640
        max_y = 480
        for poly in self.polygons:
            bbox = poly.bbox
            max_x = max(max_x, bbox[2] + 50)
            max_y = max(max_y, bbox[3] + 50)

        # Color palette
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8B500', '#00CED1', '#FF69B4', '#32CD32', '#FFD700'
        ]

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>VND Renderer - {os.path.basename(self.filepath)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 15px;
        }}
        h1 {{ color: #4ECDC4; margin-bottom: 5px; font-size: 1.5em; }}
        .stats {{ color: #888; margin-bottom: 10px; font-size: 0.9em; }}
        .container {{ display: flex; gap: 15px; }}
        .scene-view {{
            background: #16213e;
            border-radius: 8px;
            padding: 10px;
            overflow: auto;
            max-height: 90vh;
        }}
        .info-panel {{
            background: #16213e;
            border-radius: 8px;
            padding: 12px;
            width: 320px;
            max-height: 90vh;
            overflow-y: auto;
        }}
        .hotspot-list {{ list-style: none; }}
        .hotspot-item {{
            padding: 6px 10px;
            margin: 3px 0;
            background: #0f3460;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
        }}
        .hotspot-item:hover {{ background: #1a4a7a; }}
        .hotspot-item.active {{ background: #4ECDC4; color: #1a1a2e; }}
        .hotspot-item.no-poly {{ opacity: 0.5; font-style: italic; }}
        .polygon {{
            fill-opacity: 0.35;
            stroke-width: 2;
            cursor: pointer;
            transition: all 0.15s;
        }}
        .polygon:hover {{ fill-opacity: 0.6; stroke-width: 3; }}
        .polygon.selected {{ fill-opacity: 0.7; stroke-width: 4; }}
        .label {{
            font-size: 10px;
            fill: white;
            text-shadow: 1px 1px 2px black, -1px -1px 2px black;
            pointer-events: none;
        }}
        #details {{
            margin-top: 10px;
            padding: 10px;
            background: #0f3460;
            border-radius: 4px;
            font-size: 0.85em;
        }}
        .detail-row {{ margin: 4px 0; }}
        .detail-label {{ color: #4ECDC4; }}
        code {{ background: #1a1a2e; padding: 2px 5px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>🎮 VND Scene Renderer</h1>
    <div class="stats">
        {os.path.basename(self.filepath)} |
        {len(self.data):,} bytes |
        {len(self.polygons)} polygons |
        {len(self.hotspots)} hotspots |
        {sum(1 for h in self.hotspots if h.polygon)} linked
    </div>

    <div class="container">
        <div class="scene-view">
            <svg id="scene" width="{min(max_x, 1920)}" height="{min(max_y, 600)}"
                 style="background: #2d2d44; border: 1px solid #4ECDC4;">

                <!-- Grid -->
                <defs>
                    <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
                        <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#3a3a5a" stroke-width="0.5"/>
                    </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)"/>

                <!-- All Polygons (without hotspot association) -->
                <g id="orphan-polygons">
'''

        # Draw orphan polygons (not linked to hotspots)
        linked_offsets = {h.polygon.offset for h in self.hotspots if h.polygon}
        orphan_idx = 0
        for poly in self.polygons:
            if poly.offset not in linked_offsets:
                color = '#666666'
                html += f'''
                    <polygon class="polygon orphan"
                             points="{poly.svg_points}"
                             fill="{color}" stroke="{color}"
                             data-offset="{poly.offset}"
                             onclick="selectOrphan({orphan_idx})"/>
'''
                orphan_idx += 1

        html += '''
                </g>

                <!-- Hotspot Polygons -->
                <g id="hotspot-polygons">
'''

        # Draw hotspot polygons
        for i, hs in enumerate(self.hotspots):
            if hs.polygon:
                color = colors[i % len(colors)]
                center = hs.polygon.center
                label = hs.text[:12] if len(hs.text) > 12 else hs.text

                html += f'''
                    <g class="hotspot-group" data-index="{i}">
                        <polygon class="polygon"
                                 id="poly-{i}"
                                 points="{hs.polygon.svg_points}"
                                 fill="{color}" stroke="{color}"
                                 onclick="selectHotspot({i})"/>
                        <text class="label" x="{center[0]}" y="{center[1]}"
                              text-anchor="middle">{label}</text>
                    </g>
'''

        html += '''
                </g>
            </svg>
        </div>

        <div class="info-panel">
            <strong>🎯 Hotspots ({} with polygons)</strong>
            <ul class="hotspot-list">
'''.format(sum(1 for h in self.hotspots if h.polygon))

        # Hotspot list
        for i, hs in enumerate(self.hotspots):
            poly_class = '' if hs.polygon else 'no-poly'
            poly_info = f"✓" if hs.polygon else "✗"
            html += f'''
                <li class="hotspot-item {poly_class}" data-index="{i}" onclick="selectHotspot({i})">
                    {poly_info} {hs.text[:30]}
                </li>
'''

        html += '''
            </ul>

            <div id="details">
                <em>Click a hotspot or polygon to see details</em>
            </div>
        </div>
    </div>

    <script>
        const hotspots = ''' + self._hotspots_to_json() + ''';
        const polygons = ''' + self._polygons_to_json() + ''';

        function selectHotspot(index) {
            // Clear previous selection
            document.querySelectorAll('.hotspot-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.polygon').forEach(el => el.classList.remove('selected'));

            // Select new
            const items = document.querySelectorAll('.hotspot-item');
            if (items[index]) items[index].classList.add('active');

            const poly = document.getElementById('poly-' + index);
            if (poly) poly.classList.add('selected');

            // Show details
            const hs = hotspots[index];
            let html = '<div class="detail-row"><span class="detail-label">Text:</span> ' + hs.text + '</div>';
            html += '<div class="detail-row"><span class="detail-label">Position:</span> (' + hs.text_x + ', ' + hs.text_y + ')</div>';
            html += '<div class="detail-row"><span class="detail-label">Layer:</span> ' + hs.layer + '</div>';
            html += '<div class="detail-row"><span class="detail-label">Offset:</span> <code>0x' + hs.offset.toString(16) + '</code></div>';

            if (hs.polygon) {
                html += '<div class="detail-row"><span class="detail-label">Polygon:</span> ' + hs.polygon.length + ' points</div>';
                html += '<div class="detail-row"><span class="detail-label">BBox:</span> (' +
                        hs.bbox.join(', ') + ')</div>';
            }

            document.getElementById('details').innerHTML = html;

            // Scroll into view
            if (poly) poly.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        function selectOrphan(index) {
            document.getElementById('details').innerHTML =
                '<div class="detail-row"><span class="detail-label">Orphan Polygon</span></div>' +
                '<div class="detail-row">Points: ' + polygons[index].points.length + '</div>';
        }
    </script>
</body>
</html>
'''
        return html

    def _hotspots_to_json(self) -> str:
        """Convert hotspots to JSON"""
        result = []
        for hs in self.hotspots:
            item = {
                'text': hs.text,
                'text_x': hs.text_x,
                'text_y': hs.text_y,
                'layer': hs.layer,
                'offset': hs.offset,
                'polygon': hs.polygon.points if hs.polygon else None,
                'bbox': list(hs.polygon.bbox) if hs.polygon else None
            }
            result.append(item)
        return json.dumps(result)

    def _polygons_to_json(self) -> str:
        """Convert polygons to JSON"""
        result = []
        for poly in self.polygons:
            result.append({'offset': poly.offset, 'points': poly.points})
        return json.dumps(result)

    def render(self, output_path: str = None) -> str:
        """Parse and render to HTML"""
        self.parse()
        html = self.generate_html()

        if output_path is None:
            output_path = Path(self.filepath).stem + '_scene.html'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python vnd_renderer.py <file.vnd> [output.html]")
        sys.exit(1)

    filepath = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None

    renderer = VNDRenderer(filepath)
    output_path = renderer.render(output)

    print(f"Generated: {output_path}")
    print(f"Polygons: {len(renderer.polygons)} (type 105)")
    print(f"Hotspots: {len(renderer.hotspots)}")
    print(f"Linked: {sum(1 for h in renderer.hotspots if h.polygon)}")

    try:
        webbrowser.open(f'file://{os.path.abspath(output_path)}')
    except:
        pass


if __name__ == "__main__":
    main()
