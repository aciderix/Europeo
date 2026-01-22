#!/usr/bin/env python3
"""
Virtual Navigator Engine - VND File Parser and Runtime Engine
==============================================================

Reverse-engineered from vnresmod.dll (Sopra Multimedia, 1999)
This module provides complete parsing and execution of VND game files.

Format: VNFILE v2.136
Project: Europeo (Educational game about European geography/currency)

TECHNICAL DOCUMENTATION
=======================

## VND File Structure

### Header (0x00 - 0x87)
```
Offset  Size  Description
------  ----  -----------
0x00    9     Magic: 3a 01 01 00 00 06 00 00 00
0x09    6     Signature: "VNFILE"
0x0F    1     Version type marker (0x04)
0x10    3     Padding
0x13    6     Version string "2.136\0"
0x19    2     Padding
0x1B    4     Project name length (LE uint32)
0x1F    N     Project name string
...     4     Creator length (LE uint32)
...     N     Creator string
...     4     Checksum length (LE uint32)
...     N     Checksum string (MD5-like)
...     8     Padding/reserved
0x4E    4     Screen width (640)
0x52    4     Screen height (480)
0x56    4     Color depth (16)
0x5A    4     Flag 1 (1)
0x5E    4     Flag 2 (1)
0x62    4     Flag 3 (31)
0x66    4     Padding
0x6A    4     DLL path length
0x6E    N     DLL path string
```

### Resource Directory
After header, contains length-prefixed resource names:
```
4 bytes: name length (LE uint32)
N bytes: resource name (ASCII)
4 bytes: metadata (usually 0x00 0x00 0x00 0x00)
```

### Script Section
Plain text commands, newline or null separated:
- Conditional: `<var> <op> <value> then <action>`
- Set variable: `set_var <name> <value>`
- Inc/Dec variable: `inc_var/dec_var <name> <value>`
- Scene navigation: `scene <id>`
- Project switch: `runprj <path> <scene>`
- Add bitmap: `addbmp <name> <path> <x> <y> <z>`
- Delete bitmap: `delbmp <name>`
- Play video: `playavi <path> <priority> <x> <y> <w> <h>`
- Play text: `playtext <duration> <x> <y> <w> <h> <flags> <text>`
- Add text: `addtext <id> <color> <x> <y> <w> <h> <flags> <text|expr>`

## Script Operators
- = : equals
- != : not equals
- < : less than
- > : greater than
- <= : less than or equal
- >= : greater than or equal

## Hotspot Format
```
X Y W H flags text[suffix]
```
Example: `40 350 125 365 0 L'agenda du banquierj`

## Hotspot Suffixes (OBSERVED - meaning NOT YET PROVEN)
Suffixes observed in VND files (e.g., "SORTIEh", "39i", "Venisej"):
- h, d, f, i, j, k, l : Single letter suffixes appended to hotspot names
- Their exact interpretation by europeo.exe is NOT YET REVERSE-ENGINEERED
- TODO: Find the switch/comparison in europeo.exe that handles these

## Complete Command Table (PROVEN - extracted from europeo.exe)
Navigation: quit, about, prefs, prev, next, zoom, zoomin, zoomout, scene, hotspot, explore
Media:      playavi, playbmp, playwav, playmid, playcda, playseq, playhtml, playcmd, playtext
Close:      closeavi, closewav, closemid, closedll
Bitmap:     addbmp, delbmp, showbmp, hidebmp
Object:     showobj, hideobj, delobj, addtext
Variables:  set_var, inc_var, dec_var, if
Execution:  exec, runprj, rundll, pause
UI:         tiptext, defcursor, font, msgbox, invalidate, update
File:       load, save
Comment:    rem

## Command Dispatch Table (PROVEN - from europeo.exe @ 0x40ba62)
Switch table with 49 entries at 0x40ba69, handler addresses:
```
Index | Command     | Handler Address | Notes
------|-------------|-----------------|------------------
0     | quit        | 0x0040bb2d      | Exit application
1     | about       | 0x0040bb47      | Show about dialog
2     | prefs       | 0x0040bb61      | Preferences
3     | prev        | 0x0040bb7b      | Previous scene
4     | next        | 0x0040bc46      | Next scene
5     | zoom        | 0x0040bd11      | Zoom view
6     | scene       | 0x0040bd2b      | Load scene
7     | hotspot     | 0x0040bef9      | Define hotspot region
8     | tiptext     | 0x0040bf6c      | Tooltip text
9     | playavi     | 0x0040c097      | Play AVI video
10    | playbmp     | 0x0040c134      | Display bitmap
11    | playwav     | 0x0040c4fe      | Play WAV audio
12    | playmid     | 0x0040c5c3      | Play MIDI
13    | playhtml    | 0x0040c661      | Display HTML
14-16 | zoomin/out/pause | 0x0040c82a | Shared handler
17    | exec        | 0x0040c8e7      | Execute command
18    | explore     | 0x0040bf6c      | Same as tiptext
19    | playcda     | 0x0040c70d      | Play CD audio
20    | playseq     | 0x0040c74b      | Play sequence
21    | if          | 0x0040c99c      | Conditional
22    | set_var     | 0x0040ca96      | Set variable
23    | inc_var     | 0x0040cb26      | Increment variable
24    | dec_var     | 0x0040cbd5      | Decrement variable
25    | invalidate  | 0x0040cc84      | Redraw region
26    | defcursor   | 0x0040ccce      | Define cursor
27    | addbmp      | 0x0040c1f3      | Add bitmap
28-30 | delbmp/showbmp/hidebmp | 0x0040c3a6 | Shared handler
31    | runprj      | 0x0040cdee      | Run project
32    | update      | 0x0040ccb5      | Update display
33    | rundll      | 0x0040cf4f      | Run DLL
34    | msgbox      | 0x0040d01d      | Message box
35    | playcmd     | 0x0040d175      | Play command
36    | closewav    | 0x0040c5aa      | Close WAV
37    | closedll    | 0x0040d004      | Close DLL
38    | playtext    | 0x0040d19f      | Display text
39    | font        | 0x0040d23d      | Set font
40    | rem         | 0x0040d6de      | Comment (no-op)
41    | addtext     | 0x0040c2e3      | Add text object
42-44 | delobj/showobj/hideobj | 0x0040c3a6 | Shared handler
45    | load        | 0x0040d2ca      | Load state
46    | save        | 0x0040d4c7      | Save state
47-48 | closeavi/closemid | 0x0040c5aa | Shared close handler
```

## Event Types (PROVEN - from europeo.exe)
- EV_ONFOCUS  : Mouse hover/focus event
- EV_ONCLICK  : Mouse click event
- EV_ONINIT   : Initialization event
- EV_AFTERINIT: Post-initialization event

## vndllapi.dll API (PROVEN - decompiled)
- InitVNCommandMessage(): Registers "wm_vncommand" Windows message
- VNDLLVarFind(list, name): Finds variable by name (case-insensitive)
- VNDLLVarAddModify(list, name, value): Adds/modifies variable

## Variable Structure (PROVEN - from vndllapi.dll)
```c
typedef struct VNDLLVar {
    char name[256];       // 0x00-0xFF: Variable name (uppercase)
    int value;            // 0x100: Variable value
    struct VNDLLVar* next; // 0x104: Next in linked list
} VNDLLVar;  // Total: 264 bytes (0x108)
```

## Hotspot Binary Structure (PROVEN - from europeo.exe @ 0x412168)
Hotspots use polygon regions for hit-testing via Windows GDI TRegion.
```c
typedef struct TPoint {
    int x;    // 4 bytes
    int y;    // 4 bytes
} TPoint;     // 8 bytes

typedef struct HotspotRecord {
    // ... header fields ...
    uint8_t  flags;           // @ +0x31 : flags (bit 1 = special mode)
    uint32_t point_count;     // @ +0x35 : number of polygon points
    TPoint*  points;          // @ +0x39 : pointer to point array
    // ...
} HotspotRecord;
```
Hit-testing: Uses OWL52t.dll TRegion constructor with points array,
then calls GDI32 PtInRegion() to test if mouse is inside polygon.
Key function: fcn.00412168 @ europeo.exe (handles 2-point rect case specially)

## Binary Stream Reading (PROVEN - from europeo.exe)
Uses Borland Data Streaming (bds52t.dll):
- ipstream_readWord32_qv  @ 0x439180 : Read 32-bit LE integer
- ipstream_readWord_qv    @ 0x439186 : Read 16-bit LE word
- ipstream_readBytes_qpvui @ 0x439192 : Read raw bytes
- ipstream_readVersion_qv @ 0x43918c : Read version info

VND Record Reading @ 0x42662b:
```c
void ReadVNDRecord(HotspotRecord* rec, ipstream* stream) {
    ipstream_readBytes(stream, &rec->field_08, 4);  // rect/bounds?
    ipstream_readBytes(stream, &rec->field_0c, 4);
    ipstream_readBytes(stream, &rec->field_10, 4);
    uint32_t flags = ipstream_readWord32(stream);
    rec->field_14 = (flags != 0);
}
```

## Author
Reverse Engineering Project - 2024
"""

import struct
import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Callable
from enum import Enum, auto
from pathlib import Path


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class VNDHeader:
    """VND File Header (reconstructed from binary analysis)"""
    magic: bytes              # 9 bytes
    signature: str            # "VNFILE"
    version: str              # "2.136"
    project_name: str         # "Europeo"
    creator: str              # "Sopra Multimedia"
    checksum: str             # "5D51F233"
    screen_width: int         # 640
    screen_height: int        # 480
    color_depth: int          # 16
    flags: Tuple[int, int, int]  # (1, 1, 31)
    dll_path: str             # "..\VnStudio\vnresmod.dll"


@dataclass
class VNDResource:
    """A game resource (variable, object, state flag)"""
    name: str
    initial_value: int = 0
    metadata: bytes = b'\x00\x00\x00\x00'


@dataclass
class VNDCommand:
    """A parsed script command"""
    raw: str                  # Original text
    type: str                 # Command type
    condition: Optional[str]  # Condition (for conditionals)
    action: Optional[str]     # Action to execute
    params: List[str]         # Command parameters


@dataclass
class VNDBitmap:
    """Active bitmap on screen"""
    name: str
    path: str
    x: int
    y: int
    z: int  # Layer/priority


@dataclass
class VNDHotspot:
    """Interactive region on screen"""
    id: int
    x: int
    y: int
    width: int
    height: int
    action: str
    cursor: int = 0


@dataclass
class VNDScene:
    """A game scene"""
    id: int
    name: str = ""
    background: str = ""
    scripts: List[str] = field(default_factory=list)
    hotspots: List[VNDHotspot] = field(default_factory=list)
    bitmaps: List[VNDBitmap] = field(default_factory=list)


class VNDCommandType(Enum):
    """All supported command types"""
    SET_VAR = "set_var"
    INC_VAR = "inc_var"
    DEC_VAR = "dec_var"
    IF_THEN = "conditional"
    SCENE = "scene"
    RUNPRJ = "runprj"
    ADDBMP = "addbmp"
    DELBMP = "delbmp"
    PLAYAVI = "playavi"
    PLAYWAV = "playwav"
    RUNDLL = "rundll"
    PLAYTEXT = "playtext"
    ADDTEXT = "addtext"
    DEFCURSOR = "defcursor"
    HOTSPOT = "hotspot"
    MEDIA_REF = "media_reference"
    UNKNOWN = "unknown"


# Hotspot suffixes - UNPROVEN, may be artifacts
# TODO: Remove if no proof found in binaries
HOTSPOT_SUFFIXES = {}


# ============================================================================
# VND PARSER
# ============================================================================

class VNDParser:
    """
    Parser for Virtual Navigator Data (.vnd) files

    Usage:
        parser = VNDParser("game.vnd")
        parser.parse()
        print(parser.get_summary())
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data: bytes = b''
        self.header: Optional[VNDHeader] = None
        self.resources: Dict[str, VNDResource] = {}
        self.scripts: List[str] = []
        self.commands: List[VNDCommand] = []

    def _read_uint32(self, offset: int) -> Tuple[int, int]:
        """Read little-endian 32-bit unsigned integer"""
        if offset + 4 > len(self.data):
            return 0, offset
        value = struct.unpack_from('<I', self.data, offset)[0]
        return value, offset + 4

    def _read_string(self, offset: int, length: int) -> str:
        """Read fixed-length string"""
        if offset + length > len(self.data):
            return ""
        return self.data[offset:offset + length].decode('latin-1', errors='replace').rstrip('\x00')

    def _read_length_prefixed_string(self, offset: int) -> Tuple[str, int]:
        """Read length-prefixed string (4-byte LE length + chars)"""
        length, offset = self._read_uint32(offset)
        if length == 0 or length > 256 or offset + length > len(self.data):
            return "", offset
        s = self._read_string(offset, length)
        return s, offset + length

    def parse_header(self) -> int:
        """Parse VND file header, returns offset after header"""
        # Magic bytes (9 bytes)
        magic = self.data[0:9]

        # Signature "VNFILE" at offset 9
        signature = self._read_string(9, 6)
        if signature != "VNFILE":
            raise ValueError(f"Invalid signature: {signature}")

        # Version marker (1 byte) + padding (3 bytes) + version string
        # Version is at 0x13, null-terminated
        version = self._read_string(0x13, 6).rstrip('\x00')

        # Project name (length-prefixed at 0x1B)
        project_name, offset = self._read_length_prefixed_string(0x1B)

        # Creator (length-prefixed)
        creator, offset = self._read_length_prefixed_string(offset)

        # Checksum (length-prefixed)
        checksum, offset = self._read_length_prefixed_string(offset)

        # Skip to screen dimensions (at known offset 0x4E from analysis)
        # Actually, let's calculate properly
        screen_offset = offset + 8  # Skip 8 bytes of padding

        screen_width, _ = self._read_uint32(screen_offset)
        screen_height, _ = self._read_uint32(screen_offset + 4)
        color_depth, _ = self._read_uint32(screen_offset + 8)
        flag1, _ = self._read_uint32(screen_offset + 12)
        flag2, _ = self._read_uint32(screen_offset + 16)
        flag3, _ = self._read_uint32(screen_offset + 20)

        # DLL path
        dll_offset = screen_offset + 28
        dll_path, end_offset = self._read_length_prefixed_string(dll_offset)

        self.header = VNDHeader(
            magic=magic,
            signature=signature,
            version=version,
            project_name=project_name,
            creator=creator,
            checksum=checksum,
            screen_width=screen_width if screen_width < 10000 else 640,
            screen_height=screen_height if screen_height < 10000 else 480,
            color_depth=color_depth if color_depth < 100 else 16,
            flags=(flag1, flag2, flag3),
            dll_path=dll_path
        )

        return end_offset

    def parse_resources(self, start_offset: int) -> int:
        """Parse resource declarations section"""
        offset = start_offset

        while offset < len(self.data) - 8:
            length, _ = self._read_uint32(offset)

            # Valid resource name is 1-50 characters
            if length == 0 or length > 50:
                break

            if offset + 4 + length + 4 > len(self.data):
                break

            name = self._read_string(offset + 4, length)
            metadata = self.data[offset + 4 + length:offset + 4 + length + 4]

            # Check if metadata looks right (usually all zeros)
            if metadata != b'\x00\x00\x00\x00':
                # Might be end of resources
                if not name.isalnum() and '_' not in name:
                    break

            self.resources[name] = VNDResource(
                name=name,
                initial_value=0,
                metadata=metadata
            )

            offset += 4 + length + 4

            # Safety check - stop at script content
            if offset < len(self.data) - 10:
                peek = self.data[offset:offset + 10]
                if b' then ' in peek or b'scene ' in peek:
                    break

        return offset

    def parse_scripts(self, start_offset: int):
        """Parse script section"""
        script_data = self.data[start_offset:]

        # Extract readable text blocks
        current = []
        for byte in script_data:
            if 32 <= byte <= 126 or byte in [0x0a, 0x0d, 0x09]:
                current.append(chr(byte))
            else:
                if len(current) > 3:
                    text = ''.join(current).strip()
                    if text:
                        self.scripts.append(text)
                current = []

        if current:
            text = ''.join(current).strip()
            if text and len(text) > 3:
                self.scripts.append(text)

        # Parse each script into commands
        for script in self.scripts:
            cmd = self._parse_command(script)
            if cmd:
                self.commands.append(cmd)

    def _parse_command(self, line: str) -> Optional[VNDCommand]:
        """Parse a single script line into a command"""
        line = line.strip()
        if not line:
            return None

        cmd = VNDCommand(
            raw=line,
            type="unknown",
            condition=None,
            action=None,
            params=[]
        )

        line_lower = line.lower()

        # Conditional: <condition> then <action>
        if ' then ' in line_lower:
            parts = line.split(' then ', 1)
            cmd.type = "conditional"
            cmd.condition = parts[0].strip()
            if len(parts) > 1:
                cmd.action = parts[1].strip()
                # Parse the action part
                action_parts = cmd.action.split(None)
                if action_parts:
                    cmd.params = action_parts
            return cmd

        # Other commands
        parts = line.split(None)
        if not parts:
            return cmd

        first = parts[0].lower()

        if first == 'set_var':
            cmd.type = "set_var"
            cmd.params = parts[1:]
        elif first == 'inc_var':
            cmd.type = "inc_var"
            cmd.params = parts[1:]
        elif first == 'dec_var':
            cmd.type = "dec_var"
            cmd.params = parts[1:]
        elif first == 'scene':
            cmd.type = "scene"
            cmd.params = parts[1:]
        elif first == 'runprj':
            cmd.type = "runprj"
            cmd.params = parts[1:]
        elif first == 'addbmp':
            cmd.type = "addbmp"
            cmd.params = parts[1:]
        elif first == 'delbmp':
            cmd.type = "delbmp"
            cmd.params = parts[1:]
        elif first == 'playavi':
            cmd.type = "playavi"
            cmd.params = parts[1:]
        elif first == 'playwav':
            cmd.type = "playwav"
            cmd.params = parts[1:]
        elif first == 'rundll':
            cmd.type = "rundll"
            cmd.params = parts[1:]
        elif first == 'playtext':
            cmd.type = "playtext"
            cmd.params = parts[1:]
        elif first == 'addtext':
            cmd.type = "addtext"
            cmd.params = parts[1:]
        elif first == 'defcursor':
            cmd.type = "defcursor"
            cmd.params = parts[1:]
        elif first == 'hotspot':
            cmd.type = "hotspot"
            cmd.params = parts[1:]
        elif '.bmp' in line_lower or '.avi' in line_lower or '.wav' in line_lower:
            cmd.type = "media_reference"
            cmd.params = parts

        return cmd

    def parse(self):
        """Parse the entire VND file"""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()

        header_end = self.parse_header()
        resources_end = self.parse_resources(header_end)
        self.parse_scripts(resources_end)

    def get_summary(self) -> str:
        """Get a human-readable summary of the parsed file"""
        lines = []
        lines.append("=" * 70)
        lines.append("VND FILE ANALYSIS REPORT")
        lines.append("=" * 70)

        if self.header:
            lines.append("\n[FILE HEADER]")
            lines.append(f"  Signature:    {self.header.signature}")
            lines.append(f"  Version:      {self.header.version}")
            lines.append(f"  Project:      {self.header.project_name}")
            lines.append(f"  Creator:      {self.header.creator}")
            lines.append(f"  Checksum:     {self.header.checksum}")
            lines.append(f"  Resolution:   {self.header.screen_width}x{self.header.screen_height}")
            lines.append(f"  Color Depth:  {self.header.color_depth} bits")
            lines.append(f"  DLL Path:     {self.header.dll_path}")

        lines.append(f"\n[RESOURCES] ({len(self.resources)} total)")
        for i, name in enumerate(list(self.resources.keys())[:20]):
            lines.append(f"  {i+1:3}. {name}")
        if len(self.resources) > 20:
            lines.append(f"  ... and {len(self.resources) - 20} more")

        lines.append(f"\n[SCRIPTS] ({len(self.scripts)} lines)")

        # Count command types
        cmd_counts = {}
        for cmd in self.commands:
            cmd_counts[cmd.type] = cmd_counts.get(cmd.type, 0) + 1

        lines.append("\n[COMMAND TYPES]")
        for ctype, count in sorted(cmd_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {ctype}: {count}")

        # Extract unique scenes
        scenes = set()
        for cmd in self.commands:
            if cmd.type == "scene" and cmd.params:
                try:
                    scenes.add(int(cmd.params[0]))
                except:
                    pass
            if cmd.type == "runprj" and len(cmd.params) >= 2:
                try:
                    scenes.add(int(cmd.params[-1]))
                except:
                    pass

        lines.append(f"\n[SCENES REFERENCED] ({len(scenes)} unique)")
        for scene_id in sorted(scenes):
            lines.append(f"  Scene {scene_id}")

        lines.append("\n" + "=" * 70)
        return '\n'.join(lines)


# ============================================================================
# VND ENGINE (Runtime)
# ============================================================================

class VNDEngine:
    """
    Runtime engine for executing VND scripts

    This class reconstructs the behavior of vnresmod.dll to:
    - Manage game state (variables)
    - Handle scene navigation
    - Execute conditional scripts
    - Manage bitmaps and visual elements

    Usage:
        engine = VNDEngine()
        engine.load_vnd("game.vnd")
        engine.run()
    """

    def __init__(self):
        self.variables: Dict[str, int] = {}
        self.current_scene: int = 1
        self.bitmaps: Dict[str, VNDBitmap] = {}
        self.scripts: List[str] = []
        self.parser: Optional[VNDParser] = None
        self.running: bool = False
        self.event_handlers: Dict[str, List[Callable]] = {}

    def load_vnd(self, filepath: str):
        """Load and parse a VND file"""
        self.parser = VNDParser(filepath)
        self.parser.parse()

        # Initialize variables from resources
        for name in self.parser.resources:
            self.variables[name] = 0

        # Load scripts
        self.scripts = self.parser.scripts.copy()

    def set_var(self, name: str, value: int):
        """Set a variable value (equivalent to set_var command)"""
        self.variables[name] = value
        self._trigger_event('var_changed', name, value)

    def get_var(self, name: str) -> int:
        """Get a variable value (0 if undefined)"""
        return self.variables.get(name, 0)

    def inc_var(self, name: str, amount: int = 1):
        """Increment a variable (equivalent to inc_var command)"""
        self.variables[name] = self.get_var(name) + amount
        self._trigger_event('var_changed', name, self.variables[name])

    def dec_var(self, name: str, amount: int = 1):
        """Decrement a variable (equivalent to dec_var command)"""
        self.variables[name] = self.get_var(name) - amount
        self._trigger_event('var_changed', name, self.variables[name])

    def evaluate_condition(self, condition: str) -> bool:
        """
        Evaluate a conditional expression

        Supports: =, !=, <, >, <=, >=
        Example: "score >= 100" -> True if score variable >= 100
        """
        condition = condition.strip()

        # Parse operators (order matters - >= before >, etc.)
        operators = [
            ('>=', lambda a, b: a >= b),
            ('<=', lambda a, b: a <= b),
            ('!=', lambda a, b: a != b),
            ('=', lambda a, b: a == b),
            ('>', lambda a, b: a > b),
            ('<', lambda a, b: a < b),
        ]

        for op_str, op_func in operators:
            if op_str in condition:
                parts = condition.split(op_str, 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    try:
                        value = int(parts[1].strip())
                    except ValueError:
                        return False

                    var_value = self.get_var(var_name)
                    return op_func(var_value, value)

        return False

    def navigate_to_scene(self, scene_id: int):
        """
        Navigate to a different scene

        Equivalent to the scene <id> command.
        Triggers scene_exit and scene_enter events.
        """
        old_scene = self.current_scene

        self._trigger_event('scene_exit', old_scene)

        # Clear active bitmaps on scene change
        self.bitmaps.clear()

        self.current_scene = scene_id

        self._trigger_event('scene_enter', scene_id)

        print(f"[ENGINE] Scene transition: {old_scene} -> {scene_id}")

    def add_bitmap(self, name: str, path: str, x: int, y: int, z: int = 0):
        """
        Add a bitmap to the display

        Equivalent to: addbmp <name> <path> <x> <y> <z>
        """
        self.bitmaps[name] = VNDBitmap(
            name=name,
            path=path,
            x=x,
            y=y,
            z=z
        )
        self._trigger_event('bitmap_added', name, path, x, y, z)
        print(f"[ENGINE] Bitmap added: {name} = {path} at ({x}, {y}, z={z})")

    def del_bitmap(self, name: str):
        """
        Remove a bitmap from the display

        Equivalent to: delbmp <name>
        """
        if name in self.bitmaps:
            del self.bitmaps[name]
            self._trigger_event('bitmap_removed', name)
            print(f"[ENGINE] Bitmap removed: {name}")

    def play_avi(self, path: str, priority: int, x: int, y: int, w: int, h: int):
        """
        Play a video file

        Equivalent to: playavi <path> <priority> <x> <y> <w> <h>
        """
        self._trigger_event('play_video', path, priority, x, y, w, h)
        print(f"[ENGINE] Play video: {path} at ({x}, {y}, {w}x{h})")

    def play_wav(self, path: str, loop: int = 0):
        """
        Play a WAV audio file

        Equivalent to: playwav <path> <loop>
        """
        self._trigger_event('play_audio', path, loop)
        print(f"[ENGINE] Play audio: {path} (loop={loop})")

    def run_dll(self, dll_name: str):
        """
        Execute an external DLL module

        Equivalent to: rundll <dllname.dll>
        This was used for mini-games like the wheel (roue.dll)
        """
        self._trigger_event('run_dll', dll_name)
        print(f"[ENGINE] Execute DLL: {dll_name}")

    def run_project(self, path: str, scene: int):
        """
        Load and run another VND project

        Equivalent to: runprj <path> <scene>
        """
        self._trigger_event('run_project', path, scene)
        print(f"[ENGINE] Run project: {path} scene {scene}")

    def execute_command(self, command: str) -> bool:
        """
        Execute a single script command

        Returns True if command was executed successfully.
        """
        command = command.strip()
        if not command:
            return False

        command_lower = command.lower()

        # Handle conditional: <condition> then <action> [else <action2>]
        if ' then ' in command_lower:
            parts = command.split(' then ', 1)
            condition = parts[0].strip()
            action_part = parts[1].strip() if len(parts) > 1 else ""

            # Handle "if <condition>" prefix
            if condition.lower().startswith('if '):
                condition = condition[3:].strip()

            # Check for else clause
            action = action_part
            else_action = None
            if ' else ' in action_part.lower():
                action_parts = action_part.split(' else ', 1)
                action = action_parts[0].strip()
                else_action = action_parts[1].strip() if len(action_parts) > 1 else None

            if self.evaluate_condition(condition):
                return self.execute_command(action)
            elif else_action:
                return self.execute_command(else_action)
            return True  # Condition evaluated, just false

        # Parse command
        parts = command.split(None)
        if not parts:
            return False

        cmd = parts[0].lower()

        try:
            if cmd == 'set_var' and len(parts) >= 3:
                self.set_var(parts[1], int(parts[2]))

            elif cmd == 'inc_var' and len(parts) >= 3:
                self.inc_var(parts[1], int(parts[2]))

            elif cmd == 'dec_var' and len(parts) >= 3:
                self.dec_var(parts[1], int(parts[2]))

            elif cmd == 'scene' and len(parts) >= 2:
                self.navigate_to_scene(int(parts[1]))

            elif cmd == 'runprj' and len(parts) >= 3:
                self.run_project(parts[1], int(parts[2]))

            elif cmd == 'addbmp' and len(parts) >= 5:
                z = int(parts[5]) if len(parts) > 5 else 0
                self.add_bitmap(parts[1], parts[2], int(parts[3]), int(parts[4]), z)

            elif cmd == 'delbmp' and len(parts) >= 2:
                self.del_bitmap(parts[1])

            elif cmd == 'playavi' and len(parts) >= 6:
                self.play_avi(
                    parts[1],
                    int(parts[2]),
                    int(parts[3]),
                    int(parts[4]),
                    int(parts[5]),
                    int(parts[6]) if len(parts) > 6 else 0
                )

            elif cmd == 'playwav' and len(parts) >= 2:
                loop = int(parts[2]) if len(parts) > 2 else 0
                self.play_wav(parts[1], loop)

            elif cmd == 'rundll' and len(parts) >= 2:
                self.run_dll(parts[1])

            else:
                return False  # Unknown command

        except (ValueError, IndexError) as e:
            print(f"[ENGINE] Command error: {command} - {e}")
            return False

        return True

    def run_scripts(self, scripts: List[str]):
        """Execute a list of scripts in order"""
        for script in scripts:
            self.execute_command(script)

    def on(self, event: str, handler: Callable):
        """Register an event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def _trigger_event(self, event: str, *args):
        """Trigger an event"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(*args)
                except Exception as e:
                    print(f"[ENGINE] Event handler error: {e}")

    def get_state(self) -> Dict[str, Any]:
        """Get current engine state"""
        return {
            'current_scene': self.current_scene,
            'variables': dict(self.variables),
            'bitmaps': {name: vars(bmp) for name, bmp in self.bitmaps.items()},
            'running': self.running
        }

    def print_state(self):
        """Print current engine state"""
        print("\n" + "=" * 50)
        print("ENGINE STATE")
        print("=" * 50)
        print(f"Current Scene: {self.current_scene}")
        print(f"Variables ({len(self.variables)}):")
        for name, value in sorted(self.variables.items()):
            if value != 0:  # Only show non-zero
                print(f"  {name} = {value}")
        print(f"Active Bitmaps ({len(self.bitmaps)}):")
        for name, bmp in self.bitmaps.items():
            print(f"  {name}: {bmp.path} at ({bmp.x}, {bmp.y})")
        print("=" * 50)


# ============================================================================
# PSEUDO-CODE RECONSTRUCTION
# ============================================================================

VNRESMOD_PSEUDOCODE = """
================================================================================
VNRESMOD.DLL RECONSTRUCTED PSEUDO-CODE
================================================================================

Based on reverse engineering of vnresmod.dll (Sopra Multimedia, 1996-1999)
Borland C++ compiled, 32-bit Windows DLL

--------------------------------------------------------------------------------
1. DLL INITIALIZATION (DllMain)
--------------------------------------------------------------------------------

BOOL DllMain(HINSTANCE hDll, DWORD reason, LPVOID reserved) {
    if (reason == DLL_PROCESS_ATTACH) {
        // Initialize TLS (Thread Local Storage)
        tlsIndex = TlsAlloc();

        // Check Windows version
        DWORD version = GetVersion();
        if (version & 0x80000000) {
            // Win32s not supported
            MessageBoxA(NULL, "Nonshared DATA segment required", "Error", MB_OK);
            return FALSE;
        }

        // Initialize critical section for thread safety
        InitializeCriticalSection(&cs);

        // Allocate memory for engine state
        engineState = VirtualAlloc(NULL, ENGINE_STATE_SIZE,
                                    MEM_COMMIT, PAGE_READWRITE);
    }
    else if (reason == DLL_PROCESS_DETACH) {
        // Cleanup
        VirtualFree(engineState, 0, MEM_RELEASE);
        DeleteCriticalSection(&cs);
        TlsFree(tlsIndex);
    }
    return TRUE;
}

--------------------------------------------------------------------------------
2. VND FILE LOADING
--------------------------------------------------------------------------------

typedef struct {
    char signature[6];      // "VNFILE"
    char version[6];        // "2.136"
    char* projectName;      // Length-prefixed string
    char* creator;          // Length-prefixed string
    char* checksum;         // MD5-like hash
    int screenWidth;        // 640
    int screenHeight;       // 480
    int colorDepth;         // 16
    char* dllPath;          // Path to this DLL
    ResourceEntry* resources;
    ScriptEntry* scripts;
} VNDFile;

BOOL VND_LoadFile(const char* filepath, VNDFile* outFile) {
    HANDLE hFile = CreateFileA(filepath, GENERIC_READ, FILE_SHARE_READ,
                               NULL, OPEN_EXISTING, 0, NULL);
    if (hFile == INVALID_HANDLE_VALUE) {
        return FALSE;
    }

    // Read header
    BYTE header[256];
    DWORD bytesRead;
    ReadFile(hFile, header, 256, &bytesRead, NULL);

    // Validate signature
    if (memcmp(header + 9, "VNFILE", 6) != 0) {
        CloseHandle(hFile);
        return FALSE;
    }

    // Parse header fields
    outFile->version = ParseLengthPrefixedString(header, 0x0F);
    outFile->projectName = ParseLengthPrefixedString(header, 0x1B);
    // ... etc

    // Parse resources
    offset = headerEnd;
    while (TRUE) {
        int nameLen = *(int*)(data + offset);
        if (nameLen == 0 || nameLen > 256) break;

        ResourceEntry* res = AllocResource();
        res->name = AllocString(nameLen);
        memcpy(res->name, data + offset + 4, nameLen);
        res->value = 0;

        AddResource(outFile, res);
        offset += 4 + nameLen + 4;
    }

    // Parse scripts
    while (offset < fileSize) {
        char* line = ExtractTextLine(data, offset);
        if (line) {
            AddScript(outFile, line);
        }
    }

    CloseHandle(hFile);
    return TRUE;
}

--------------------------------------------------------------------------------
3. SCRIPT EXECUTION ENGINE
--------------------------------------------------------------------------------

typedef struct {
    int variables[MAX_VARIABLES];
    int currentScene;
    BitmapEntry bitmaps[MAX_BITMAPS];
    int bitmapCount;
} EngineState;

void VN_ExecuteScript(EngineState* state, const char* script) {
    // Check for conditional
    char* thenPos = strstr(script, " then ");
    if (thenPos) {
        // Parse condition
        char condition[256];
        strncpy(condition, script, thenPos - script);
        condition[thenPos - script] = '\0';

        // Skip "if " prefix if present
        char* condStart = condition;
        if (strncmp(condStart, "if ", 3) == 0) {
            condStart += 3;
        }

        // Evaluate condition
        if (VN_EvaluateCondition(state, condStart)) {
            // Execute action
            VN_ExecuteScript(state, thenPos + 6);
        }
        return;
    }

    // Parse command
    char cmd[64];
    sscanf(script, "%s", cmd);

    if (strcmp(cmd, "set_var") == 0) {
        char varName[64];
        int value;
        sscanf(script, "set_var %s %d", varName, &value);
        VN_SetVariable(state, varName, value);
    }
    else if (strcmp(cmd, "inc_var") == 0) {
        char varName[64];
        int amount;
        sscanf(script, "inc_var %s %d", varName, &amount);
        VN_IncVariable(state, varName, amount);
    }
    else if (strcmp(cmd, "dec_var") == 0) {
        char varName[64];
        int amount;
        sscanf(script, "dec_var %s %d", varName, &amount);
        VN_DecVariable(state, varName, amount);
    }
    else if (strcmp(cmd, "scene") == 0) {
        int sceneId;
        sscanf(script, "scene %d", &sceneId);
        VN_NavigateToScene(state, sceneId);
    }
    else if (strcmp(cmd, "addbmp") == 0) {
        char name[64], path[256];
        int x, y, z;
        sscanf(script, "addbmp %s %s %d %d %d", name, path, &x, &y, &z);
        VN_AddBitmap(state, name, path, x, y, z);
    }
    else if (strcmp(cmd, "delbmp") == 0) {
        char name[64];
        sscanf(script, "delbmp %s", name);
        VN_DeleteBitmap(state, name);
    }
    else if (strcmp(cmd, "playavi") == 0) {
        char path[256];
        int priority, x, y, w, h;
        sscanf(script, "playavi %s %d %d %d %d %d",
               path, &priority, &x, &y, &w, &h);
        VN_PlayVideo(state, path, priority, x, y, w, h);
    }
    else if (strcmp(cmd, "runprj") == 0) {
        char path[256];
        int scene;
        sscanf(script, "runprj %s %d", path, &scene);
        VN_RunProject(state, path, scene);
    }
}

BOOL VN_EvaluateCondition(EngineState* state, const char* condition) {
    char varName[64];
    char op[4];
    int value;

    // Parse: varName op value
    if (sscanf(condition, "%s >= %d", varName, &value) == 2) {
        return VN_GetVariable(state, varName) >= value;
    }
    else if (sscanf(condition, "%s <= %d", varName, &value) == 2) {
        return VN_GetVariable(state, varName) <= value;
    }
    else if (sscanf(condition, "%s != %d", varName, &value) == 2) {
        return VN_GetVariable(state, varName) != value;
    }
    else if (sscanf(condition, "%s = %d", varName, &value) == 2) {
        return VN_GetVariable(state, varName) == value;
    }
    else if (sscanf(condition, "%s > %d", varName, &value) == 2) {
        return VN_GetVariable(state, varName) > value;
    }
    else if (sscanf(condition, "%s < %d", varName, &value) == 2) {
        return VN_GetVariable(state, varName) < value;
    }

    return FALSE;
}

--------------------------------------------------------------------------------
4. SCENE NAVIGATION
--------------------------------------------------------------------------------

void VN_NavigateToScene(EngineState* state, int targetScene) {
    // 1. Execute exit scripts for current scene
    VN_ExecuteSceneExitScripts(state, state->currentScene);

    // 2. Clear current scene resources
    VN_ClearBitmaps(state);
    VN_ClearHotspots(state);

    // 3. Load new scene
    state->currentScene = targetScene;

    // 4. Execute enter scripts for new scene
    VN_ExecuteSceneEnterScripts(state, targetScene);

    // 5. Render initial frame
    VN_RenderFrame(state);
}

--------------------------------------------------------------------------------
5. GRAPHICS RENDERING
--------------------------------------------------------------------------------

void VN_AddBitmap(EngineState* state, const char* name,
                  const char* path, int x, int y, int z) {
    BitmapEntry* entry = &state->bitmaps[state->bitmapCount++];
    strcpy(entry->name, name);
    strcpy(entry->path, path);
    entry->x = x;
    entry->y = y;
    entry->z = z;  // Layer priority

    // Load bitmap from file
    entry->hBitmap = LoadBitmapFromFile(path);

    // Sort by Z-order
    SortBitmapsByZ(state);

    // Trigger redraw
    InvalidateRect(hwnd, NULL, FALSE);
}

void VN_RenderFrame(EngineState* state) {
    HDC hdc = GetDC(hwnd);
    HDC hdcMem = CreateCompatibleDC(hdc);

    // Create back buffer
    HBITMAP hBackBuffer = CreateCompatibleBitmap(hdc,
                                                  state->screenWidth,
                                                  state->screenHeight);
    SelectObject(hdcMem, hBackBuffer);

    // Render all bitmaps in Z-order
    for (int i = 0; i < state->bitmapCount; i++) {
        BitmapEntry* bmp = &state->bitmaps[i];
        HDC hdcBmp = CreateCompatibleDC(hdc);
        SelectObject(hdcBmp, bmp->hBitmap);
        BitBlt(hdcMem, bmp->x, bmp->y, bmp->width, bmp->height,
               hdcBmp, 0, 0, SRCCOPY);
        DeleteDC(hdcBmp);
    }

    // Copy to screen
    BitBlt(hdc, 0, 0, state->screenWidth, state->screenHeight,
           hdcMem, 0, 0, SRCCOPY);

    DeleteDC(hdcMem);
    DeleteObject(hBackBuffer);
    ReleaseDC(hwnd, hdc);
}

--------------------------------------------------------------------------------
6. MULTIMEDIA (VIDEO/AUDIO)
--------------------------------------------------------------------------------

void VN_PlayVideo(EngineState* state, const char* path,
                  int priority, int x, int y, int w, int h) {
    // Uses Windows MCI (Media Control Interface)
    char command[512];

    sprintf(command, "open %s type avivideo alias video", path);
    mciSendString(command, NULL, 0, NULL);

    sprintf(command, "window video handle %d", hwnd);
    mciSendString(command, NULL, 0, NULL);

    sprintf(command, "put video window at %d %d %d %d", x, y, w, h);
    mciSendString(command, NULL, 0, NULL);

    mciSendString("play video", NULL, 0, NULL);
}

void VN_PlaySound(EngineState* state, const char* path) {
    PlaySound(path, NULL, SND_FILENAME | SND_ASYNC);
}

================================================================================
END OF PSEUDO-CODE
================================================================================
"""


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    import sys

    print(__doc__)

    # Parse command line
    if len(sys.argv) < 2:
        vnd_path = "couleurs1.vnd"
        if not os.path.exists(vnd_path):
            print("\nUsage: python vnengine.py <file.vnd>")
            print("\nOptions:")
            print("  --summary     Show file summary only")
            print("  --pseudocode  Show reconstructed DLL pseudo-code")
            print("  --simulate    Run engine simulation")
            sys.exit(0)
    else:
        vnd_path = sys.argv[1]

    # Check for pseudo-code option
    if '--pseudocode' in sys.argv:
        print(VNRESMOD_PSEUDOCODE)
        sys.exit(0)

    # Parse VND file
    print(f"\nParsing: {vnd_path}\n")

    parser = VNDParser(vnd_path)
    parser.parse()
    print(parser.get_summary())

    # Show sample scripts
    print("\n[SAMPLE SCRIPTS (first 30)]")
    for i, script in enumerate(parser.scripts[:30]):
        print(f"  {i+1:3}. {script[:70]}{'...' if len(script) > 70 else ''}")

    # Show sample conditionals
    print("\n[SAMPLE CONDITIONALS]")
    conditionals = [cmd for cmd in parser.commands if cmd.type == "conditional"]
    for cmd in conditionals[:15]:
        print(f"  IF: {cmd.condition}")
        print(f"      THEN: {cmd.action}")
        print()

    # Simulation mode
    if '--simulate' in sys.argv:
        print("\n" + "=" * 70)
        print("ENGINE SIMULATION")
        print("=" * 70)

        engine = VNDEngine()
        engine.load_vnd(vnd_path)

        print("\nExecuting first 20 conditional commands...")
        for cmd in conditionals[:20]:
            if cmd.action:
                print(f"\nCondition: {cmd.condition}")
                print(f"Action: {cmd.action}")

                # Set some test conditions
                if cmd.condition:
                    parts = cmd.condition.split()
                    if parts:
                        # Set the variable to trigger the condition
                        engine.set_var(parts[0], 1)

                engine.execute_command(cmd.raw)

        engine.print_state()


if __name__ == "__main__":
    main()
