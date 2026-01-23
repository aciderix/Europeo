#!/usr/bin/env python3
"""
VND Strict Parser - Lecture stricte du format binaire

Principe: Lire EXACTEMENT ce qui est déclaré dans le binaire:
- Scene Count du header
- objCount hotspots par scène
- cmdCount commandes par hotspot
- pointCount points par géométrie

Pas de gap recovery, pas de coalescing, pas d'heuristiques.
Si le format est invalide → erreur explicite.
"""

import struct
import json
import sys
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Command:
    id: int
    subtype: int
    param: str


@dataclass
class Hotspot:
    index: int
    offset: int
    cmdCount: int
    commands: List[Command] = field(default_factory=list)
    cursorId: int = 0
    pointCount: int = 0
    points: List[Point] = field(default_factory=list)


@dataclass
class Scene:
    id: int
    offset: int
    objCount: int
    hotspots: List[Hotspot] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class VndHeader:
    magic: str
    version: str
    scene_count: int
    exit_id: int
    index_id: int


class StrictVNDParser:
    """Parser VND strict - lecture exacte du format binaire"""

    def __init__(self, data: bytes):
        self.data = data
        self.logs = []

    def log(self, msg: str):
        self.logs.append(msg)
        print(msg)

    def readU32(self, offset: int) -> int:
        if offset + 4 > len(self.data):
            raise ValueError(f"Lecture U32 hors limites @ 0x{offset:X}")
        return struct.unpack_from('<I', self.data, offset)[0]

    def readI32(self, offset: int) -> int:
        if offset + 4 > len(self.data):
            raise ValueError(f"Lecture I32 hors limites @ 0x{offset:X}")
        return struct.unpack_from('<i', self.data, offset)[0]

    def readString(self, offset: int) -> tuple[str, int]:
        """Lire Pascal string (4 bytes length + data)"""
        if offset + 4 > len(self.data):
            raise ValueError(f"Lecture string length hors limites @ 0x{offset:X}")

        length = self.readU32(offset)

        if length > 10000:
            raise ValueError(f"String trop longue ({length} bytes) @ 0x{offset:X}")

        if offset + 4 + length > len(self.data):
            raise ValueError(f"String data hors limites @ 0x{offset:X} (length={length})")

        data = self.data[offset + 4:offset + 4 + length]
        text = data.decode('cp1252', errors='replace')

        return text, offset + 4 + length

    def parseHeader(self) -> VndHeader:
        """Parser le header VND (offsets validés)"""
        # Magic
        magic, _ = self.readString(5)

        # Version
        version, _ = self.readString(15)

        # Scene count (offset 98)
        scene_count = struct.unpack_from('<H', self.data, 98)[0]

        # EXIT_ID (offset 100)
        exit_id = struct.unpack_from('<H', self.data, 100)[0]

        # INDEX_ID (offset 102)
        index_id = struct.unpack_from('<H', self.data, 102)[0]

        return VndHeader(
            magic=magic,
            version=version,
            scene_count=scene_count,
            exit_id=exit_id,
            index_id=index_id
        )

    def findSignature(self, start: int, limit: int) -> Optional[int]:
        """Trouver signature 0xFFFFFFxx entre start et limit"""
        for offset in range(start, min(limit, len(self.data) - 4)):
            value = self.readU32(offset)
            # Pattern 0xFFFFFF00 à 0xFFFFFFFF
            if (value & 0xFFFFFF00) == 0xFFFFFF00:
                return offset
        return None

    def parseHotspotStrict(self, offset: int, index: int, scene_limit: int) -> tuple[Hotspot, int]:
        """
        Parser un hotspot en mode STRICT

        Lit EXACTEMENT:
        - cmdCount commandes
        - cursorId + pointCount
        - pointCount points

        Lève une exception si erreur (pas de break silencieux)
        """
        hotspot_start = offset

        # 1. cmdCount
        cmdCount = self.readU32(offset)
        offset += 4

        self.log(f"    Hotspot {index}: cmdCount={cmdCount}")

        if cmdCount > 200:
            raise ValueError(f"cmdCount invalide ({cmdCount}) @ 0x{hotspot_start:X}")

        # 2. Lire EXACTEMENT cmdCount commandes
        commands = []
        for c in range(cmdCount):
            cmdId = self.readU32(offset)
            offset += 4

            if cmdId > 50000:
                raise ValueError(f"cmdId invalide ({cmdId}) @ 0x{offset-4:X}")

            subtype = self.readU32(offset)
            offset += 4

            param, offset = self.readString(offset)

            commands.append(Command(id=cmdId, subtype=subtype, param=param))

        # 3. Géométrie: cursorId + pointCount
        if offset + 8 > scene_limit:
            raise ValueError(f"Géométrie hors limites @ 0x{offset:X}")

        cursorId = self.readU32(offset)
        offset += 4

        pointCount = self.readU32(offset)
        offset += 4

        self.log(f"      cursorId={cursorId}, pointCount={pointCount}")

        if pointCount > 500:
            raise ValueError(f"pointCount invalide ({pointCount}) @ 0x{offset-4:X}")

        # 4. Lire EXACTEMENT pointCount points
        points = []
        for p in range(pointCount):
            if offset + 8 > scene_limit:
                raise ValueError(f"Point {p} hors limites @ 0x{offset:X}")

            x = self.readI32(offset)
            offset += 4

            y = self.readI32(offset)
            offset += 4

            # Validation stricte des coordonnées
            if abs(x) > 2000 or abs(y) > 2000:
                raise ValueError(f"Coordonnées invalides ({x}, {y}) @ 0x{offset-8:X}")

            points.append(Point(x=x, y=y))

        # 5. Extra flag (4 bytes)
        if offset + 4 <= scene_limit:
            offset += 4

        return Hotspot(
            index=index,
            offset=hotspot_start,
            cmdCount=cmdCount,
            commands=commands,
            cursorId=cursorId,
            pointCount=pointCount,
            points=points
        ), offset

    def parseSceneStrict(self, scene_id: int, start: int, end: int) -> Scene:
        """
        Parser une scène en mode STRICT

        Trouve la signature, lit objCount, puis lit EXACTEMENT objCount hotspots.
        """
        self.log(f"\n=== Scene {scene_id} @ 0x{start:X} -> 0x{end:X} ===")

        scene = Scene(id=scene_id, offset=start, objCount=0)

        try:
            # 1. Trouver signature de config
            sig_offset = self.findSignature(start, end)

            if sig_offset is None:
                raise ValueError(f"Pas de signature trouvée dans [0x{start:X}, 0x{end:X}]")

            self.log(f"  Signature @ 0x{sig_offset:X}")

            # 2. Hotspot table commence 24 bytes après signature
            hotspot_offset = sig_offset + 24

            if hotspot_offset >= end:
                raise ValueError(f"Hotspot table hors limites @ 0x{hotspot_offset:X}")

            # 3. Lire objCount
            objCount = self.readU32(hotspot_offset)
            scene.objCount = objCount
            hotspot_offset += 4

            self.log(f"  objCount = {objCount}")

            if objCount > 100:
                raise ValueError(f"objCount trop grand ({objCount})")

            # 4. Lire EXACTEMENT objCount hotspots
            for i in range(objCount):
                hotspot, hotspot_offset = self.parseHotspotStrict(
                    hotspot_offset, i, end
                )
                scene.hotspots.append(hotspot)

            self.log(f"  ✓ {len(scene.hotspots)} hotspots parsés (objCount={objCount})")

            # Validation finale
            if len(scene.hotspots) != objCount:
                raise ValueError(
                    f"Mismatch: parsé {len(scene.hotspots)}, attendu {objCount}"
                )

        except Exception as e:
            error_msg = f"ERREUR @ 0x{start:X}: {e}"
            self.log(f"  {error_msg}")
            scene.errors.append(error_msg)

        return scene

    def parse(self) -> dict:
        """Parser le VND complet en mode strict"""
        self.log("="*60)
        self.log("STRICT VND PARSER")
        self.log("="*60)

        # 1. Parser header
        header = self.parseHeader()
        self.log(f"\nHeader:")
        self.log(f"  Magic: {header.magic}")
        self.log(f"  Version: {header.version}")
        self.log(f"  Scene Count: {header.scene_count}")
        self.log(f"  EXIT_ID: {header.exit_id}")
        self.log(f"  INDEX_ID: {header.index_id}")

        # 2. Trouver toutes les signatures (scène offsets)
        self.log(f"\nRecherche de {header.scene_count} scènes...")

        scene_offsets = []
        search_start = 104  # Après header

        while len(scene_offsets) < header.scene_count + 10:  # +10 marge
            sig = self.findSignature(search_start, len(self.data))
            if sig is None:
                break
            scene_offsets.append(sig - 24)  # Scène commence 24 bytes avant signature
            search_start = sig + 4

        self.log(f"  Trouvé {len(scene_offsets)} offsets potentiels")

        # 3. Parser exactement header.scene_count scènes
        scenes = []

        for i in range(min(header.scene_count, len(scene_offsets))):
            start = scene_offsets[i]
            end = scene_offsets[i + 1] if i < len(scene_offsets) - 1 else len(self.data)

            scene = self.parseSceneStrict(i, start, end)
            scenes.append(scene)

        # 4. Statistiques
        self.log("\n" + "="*60)
        self.log("RÉSULTATS")
        self.log("="*60)
        self.log(f"Scènes parsées: {len(scenes)}/{header.scene_count}")

        total_hotspots_declared = sum(s.objCount for s in scenes)
        total_hotspots_parsed = sum(len(s.hotspots) for s in scenes)

        self.log(f"Hotspots déclarés: {total_hotspots_declared}")
        self.log(f"Hotspots parsés: {total_hotspots_parsed}")

        perfect_match = sum(1 for s in scenes if len(s.hotspots) == s.objCount)
        errors = sum(1 for s in scenes if s.errors)

        self.log(f"Match parfait: {perfect_match}/{len(scenes)} scènes")
        self.log(f"Erreurs: {errors}/{len(scenes)} scènes")

        return {
            'header': {
                'magic': header.magic,
                'version': header.version,
                'scene_count': header.scene_count,
                'exit_id': header.exit_id,
                'index_id': header.index_id,
            },
            'scenes': [
                {
                    'id': s.id,
                    'offset': f"0x{s.offset:X}",
                    'objCount': s.objCount,
                    'hotspotsCount': len(s.hotspots),
                    'match': len(s.hotspots) == s.objCount,
                    'errors': s.errors,
                }
                for s in scenes
            ],
            'stats': {
                'scenes_parsed': len(scenes),
                'scenes_expected': header.scene_count,
                'hotspots_declared': total_hotspots_declared,
                'hotspots_parsed': total_hotspots_parsed,
                'perfect_match': perfect_match,
                'errors': errors,
            }
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 strict_vnd_parser.py <vnd_file>")
        sys.exit(1)

    vnd_path = sys.argv[1]

    with open(vnd_path, 'rb') as f:
        data = f.read()

    parser = StrictVNDParser(data)
    result = parser.parse()

    # Sauvegarder résultat
    output_path = vnd_path + '.strict.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nRésultat sauvegardé: {output_path}")


if __name__ == '__main__':
    main()
