#!/usr/bin/env python3

"""
VND File Parser - Virtual Navigator Engine Resource File Format
Reverse-engineered from vnresmod.dll (Sopra Multimedia, 1999)
Format Version: 2.136
Author: Reverse Engineering Project
UPDATED: Based on VND Binary Format Specification Rev. 2
"""

import struct
import os
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum, auto
import re

class VNDCommand(Enum):
    """Commands supported by the VN scripting language (UPDATED)"""
    SET_VAR = "set_var"
    INC_VAR = "inc_var"
    DEC_VAR = "dec_var"  # NEW
    IF = "if"
    SCENE = "scene"
    ADDBMP = "addbmp"
    DELBMP = "delbmp"
    ADDTEXT = "addtext"
    PLAYTEXT = "playtext"
    RUNPRJ = "runprj"
    RUNDLL = "rundll"  # NEW
    DEFCURSOR = "defcursor"
    HOTSPOT = "hotspot"
    PLAYAVI = "playavi"  # NEW
    PLAYWAV = "playwav"  # NEW
    CLOSEWAV = "closewav"  # NEW
    FONT = "font"  # NEW
    UNKNOWN = "unknown"

@dataclass
class VNDHeader:
    """VND File Header Structure"""
    magic: bytes
    signature: str  # "VNFILE"
    version: str  # e.g., "2.136"
    project_name: str
    creator: str
    checksum: str
    screen_width: int
    screen_height: int
    flags: int
    dll_path: str

@dataclass
class VNDResource:
    """A resource/variable in the VND file"""
    name: str
    resource_type: int
    value: int
    offset: int

@dataclass
class VNDPolygon:
    """Polygon definition for hotspot hit-testing (Type 105)"""
    point_count: int
    points: List[Tuple[int, int]]
    offset: int = 0  # NEW: track offset in file

    @property
    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (min_x, min_y, max_x, max_y)"""
        if not self.points:
            return (0, 0, 0, 0)
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

@dataclass
class VNDRectangle:
    """Rectangular clickable zone (Type 2) - NEW"""
    x1: int
    y1: int
    x2: int
    y2: int
    offset: int = 0

@dataclass
class VNDHotspot:
    """Interactive hotspot definition (UPDATED)

    Can be either:
    - Type 38 text definition (optionally followed by Type 105 polygon)
    - Type 2 rectangle
    """
    id: int
    x: int
    y: int
    width: int
    height: int
    name: str = ""
    action: str = ""
    polygon: Optional[VNDPolygon] = None
    rectangle: Optional[VNDRectangle] = None  # NEW
    hotspot_type: int = 0  # NEW: 2 for rectangle, 38 for text+polygon
    layer: int = 0  # NEW: from Type 38 format
    target_scene: int = -1
    offset: int = 0  # NEW: track offset in file

@dataclass
class VNDRecord:
    """Standard VND record structure - NEW"""
    separator: int  # Should be 1
    length: int
    record_type: int
    data: bytes
    offset: int

@dataclass
class VNDScript:
    """A script/command block"""
    condition: str
    commands: List[Tuple[str, List[str]]]

@dataclass
class VNDScene:
    """A scene definition"""
    id: int
    name: str = ""
    background: str = ""
    hotspots: List[VNDHotspot] = field(default_factory=list)
    scripts: List[VNDScript] = field(default_factory=list)
    on_enter: List[str] = field(default_factory=list)
    on_exit: List[str] = field(default_factory=list)

class VNDParser:
    """
    Parser for Virtual Navigator (.vnd) files
    UPDATED: Now follows VND Binary Format Specification Rev. 2
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data: bytes = b''
        self.header: Optional[VNDHeader] = None
        self.resources: Dict[str, VNDResource] = {}
        self.scenes: Dict[int, VNDScene] = {}
        self.scripts: List[str] = []
        self.raw_strings: List[str] = []
        self.records: List[VNDRecord] = []  # NEW

    # ... [keep existing helper methods: read_uint32, read_int32, etc.] ...

    def parse_record(self, offset: int) -> Tuple[Optional[VNDRecord], int]:
        """Parse standard record structure: [SEPARATOR][LENGTH][TYPE][DATA] - NEW"""
        if offset + 12 > len(self.data):
            return None, offset

        separator, offset_tmp = self.read_uint32(offset)
        if separator != 1:
            return None, offset

        length, offset_tmp = self.read_uint32(offset_tmp)
        if length > 10000 or length == 0:
            return None, offset

        record_type, offset_tmp = self.read_uint32(offset_tmp)

        # Read data
        if offset_tmp + length > len(self.data):
            return None, offset

        data = self.data[offset_tmp:offset_tmp + length]

        record = VNDRecord(
            separator=separator,
            length=length,
            record_type=record_type,
            data=data,
            offset=offset
        )

        return record, offset_tmp + length

    def parse_type2_rectangle(self, offset: int) -> Tuple[Optional[VNDRectangle], int]:
        """Parse Type 2 rectangular clickable zone - NEW

        Binary format: [02:u32] [x1:u32] [y1:u32] [x2:u32] [y2:u32]
        """
        if offset + 20 > len(self.data):
            return None, offset

        type_marker, pos = self.read_uint32(offset)
        if type_marker != 2:
            return None, offset

        x1, pos = self.read_uint32(pos)
        y1, pos = self.read_uint32(pos)
        x2, pos = self.read_uint32(pos)
        y2, pos = self.read_uint32(pos)

        # Validate coordinates (screen bounds with margin)
        if not (-100 <= x1 <= 2000 and -100 <= y1 <= 1000 and 
                -100 <= x2 <= 2000 and -100 <= y2 <= 1000):
            return None, offset

        rectangle = VNDRectangle(x1=x1, y1=y1, x2=x2, y2=y2, offset=offset)
        return rectangle, pos

    def parse_type105_polygon(self, offset: int) -> Tuple[Optional[VNDPolygon], int]:
        """Parse Type 105 polygon structure - CORRECTED

        IMPORTANT: Type 105 does NOT have a [length] field!
        Binary format: [105:u32] [count:u32] [x1:i32][y1:i32]...[xN:i32][yN:i32]
        """
        if offset + 8 > len(self.data):
            return None, offset

        # Check for Type 105 marker
        type_marker, pos = self.read_uint32(offset)
        if type_marker != 105:
            return None, offset

        # Read point count
        point_count, pos = self.read_uint32(pos)

        # Validate point count
        if point_count < 3 or point_count > 30:
            return None, offset

        # Check if we have enough data for all points
        if pos + point_count * 8 > len(self.data):
            return None, offset

        points = []
        for _ in range(point_count):
            x, pos = self.read_int32(pos)
            y, pos = self.read_int32(pos)

            # Validate screen coordinates (with margin)
            if not (-100 <= x <= 2000 and -100 <= y <= 1000):
                return None, offset

            points.append((x, y))

        polygon = VNDPolygon(point_count=point_count, points=points, offset=offset)
        return polygon, pos

    def parse_type38_hotspot(self, record: VNDRecord) -> Optional[VNDHotspot]:
        """Parse Type 38 hotspot text definition - NEW

        Format: "X Y W H layer text"
        Example: "40 350 125 365 0 Sortie"
        """
        try:
            text = record.data.decode('latin-1').strip('\x00')
            parts = text.split(None, 5)

            if len(parts) < 6:
                return None

            x = int(parts[0])
            y = int(parts[1])
            width = int(parts[2])
            height = int(parts[3])
            layer = int(parts[4])
            name = parts[5]

            hotspot = VNDHotspot(
                id=0,  # Will be set later
                x=x,
                y=y,
                width=width,
                height=height,
                name=name,
                layer=layer,
                hotspot_type=38,
                offset=record.offset
            )

            return hotspot

        except (ValueError, UnicodeDecodeError):
            return None

    def find_all_hotspots(self) -> List[VNDHotspot]:
        """Find all hotspots (Type 2 rectangles and Type 38+105 combinations) - NEW"""
        hotspots = []
        hotspot_id = 0
        offset = 0

        while offset < len(self.data) - 20:
            # Try to parse as Type 2 rectangle
            rectangle, new_offset = self.parse_type2_rectangle(offset)
            if rectangle:
                hotspot = VNDHotspot(
                    id=hotspot_id,
                    x=rectangle.x1,
                    y=rectangle.y1,
                    width=rectangle.x2 - rectangle.x1,
                    height=rectangle.y2 - rectangle.y1,
                    rectangle=rectangle,
                    hotspot_type=2,
                    offset=rectangle.offset
                )
                hotspots.append(hotspot)
                hotspot_id += 1
                offset = new_offset
                continue

            # Try to parse as standard record
            record, new_offset = self.parse_record(offset)
            if record and record.record_type == 38:
                hotspot = self.parse_type38_hotspot(record)
                if hotspot:
                    hotspot.id = hotspot_id

                    # Check if immediately followed by Type 105 polygon
                    polygon, poly_offset = self.parse_type105_polygon(new_offset)
                    if polygon:
                        hotspot.polygon = polygon
                        new_offset = poly_offset

                    hotspots.append(hotspot)
                    hotspot_id += 1
                    offset = new_offset
                    continue

            offset += 1

        return hotspots

    # ... [keep other existing methods with updates] ...

