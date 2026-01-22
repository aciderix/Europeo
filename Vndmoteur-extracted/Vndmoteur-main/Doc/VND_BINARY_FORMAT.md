# VND Binary Format Specification (PROVEN)

## Overview

VND files use a hybrid text/binary format with Little Endian integers.
All binary values are uint32 unless otherwise noted.

---

## Record Structure

### Record Separator
Every record is separated by the marker:
```
01 00 00 00  (uint32 = 1)
```

### Text Record Structure
```
[SEPARATOR: 01 00 00 00]
[LENGTH: u32]           - Length of text data
[TYPE: u32]             - Record type identifier
[TEXT DATA: bytes]      - Text content (null-terminated or fixed length)
```

Example (offset 0x1202):
```
01 00 00 00  06 00 00 00  01 00 00 00  34 00 00 00
separator    length=6     type=1       text="4"
```

---

## Record Types Enumeration (COMPLETE)

### Type 0: Metadata/Empty Records
Structure metadata or placeholder records.

### Types 1-2: Scene References
Short scene number references.
- Type 1: Primary scene reference
- Type 2: Secondary/variant scene reference
```
Example: length=6, text="4" or "20" or "39i"
```

### Type 3: Score/Value Records
Numeric values, typically scores.
```
Example: length=16, text="500"
```

### Type 5: Game State ("jeu")
Game state variable references.
```
Example: length=23, text="jeu 1"
```

### Type 6: Flag Records
Boolean state flags.
```
Example: length=1 (single flag byte)
```

### Type 7: Variable Definitions
Complex variable structures.
```
Example: text="fiole 0"
```

### Type 8: Cancel/Activate State
State for cancel/activate actions.
```
Examples: "annule 0", "annule 1", "active 0"
```

### Type 9: Occupied State
Slot occupation tracking.
```
Examples: "occupe 10", "occupe 11", "occupe 12"
```

### Type 10: Cursor/Rollover Definitions
Cursor and rollover visual definitions.
```
Example: text="fleche.cur" or "rollover"
```

### Type 11: WAV Audio Files
Audio file references.
```
Examples: "music.wav 2", "music.wav 2l", "music.wav 6l"
```

### Type 12: Sound Effects
Secondary audio references.
```
Example: "unplus.wav 1"
```

### Type 15: Block Structure
Large block of data (possibly scene definition block).
```
Example: length=635 with binary data
```

### Type 17: Sound Effects (Path)
Sound effects with folder paths.
```
Examples: "bruit\boing.wav 1", "bruit\foret.wav 2"
```

### Type 19: Project References
Links to other VNP project files.
```
Examples: "..\espa\espa.vnp 13d", "..\autr\autr.vnp 12d"
```

### Types 20-24: Multimedia Paths (AVI Videos)
Video file references with path.
- Type 20: Home/museum videos
- Type 21: Departure videos
- Type 22: Secondary location videos
- Type 23: Scene-specific videos (fontaine, vuemusee)
- Type 24: Bibliothèque videos

```
Examples:
- Type 20: "euroland\home2.avi 1", "euroland\musee.avi 1"
- Type 21: "euroland\depart.avi 1"
- Type 22: "euroland\bankbis.avi 1", "euroland\profbis.avi 1"
- Type 23: "euroland\fontaine.avi 1", "euroland\vuemusee.avi 1"
- Type 24: "euroland\bibliobis.avi 1"
```

### Types 25+: Conditional Statements
"if X then Y" logic with various action types.

| Type | Example Action |
|------|----------------|
| 25 | dec_var |
| 26 | font (font settings) |
| 27 | closewav, scene |
| 28 | delbmp, dec_var |
| 29 | hotspot enable/disable |
| 30 | dec_var |
| 31 | rundll |
| 32 | set_var, playtext |
| 33 | dec_var, set_var |
| 34 | rundll, delbmp, dec_var |
| 35 | playavi, playwav |
| 36 | playavi (with coordinates) |
| 37 | set_var, playwav |
| 38 | playtext |
| 39 | runprj, playwav |
| 40 | runprj, rundll |
| 41 | playwav, runprj |
| 42 | runprj, dec_var |
| 43 | runprj |
| 44-45 | runprj |
| 47 | dec_var |
| 48 | font |
| 50 | playavi |
| 51 | playavi |
| 52 | addbmp |
| 54-56 | runprj, addbmp |
| 58-65 | addbmp, playtext |
| 70-75 | playtext, addbmp |
| 89-90 | playtext |

### Type 26: Font Definitions
Font settings for text display.
```
Format: "SIZE STYLE #COLOR FONTNAME"
Examples:
- "18 0 #0000ff Comic sans MS"
- "18 0 #ffffff Comic sans MS"
```

---

## Hotspot/Polygon Structure (PROVEN)

### Text Format
```
[X1] [Y1] [X2] [Y2] 0 [Name][Suffix]
```
Where:
- X1, Y1, X2, Y2: Text label bounding box (not polygon!)
- 0: Separator
- Name: Hotspot identifier
- Suffix: Optional single character

### Binary Format (immediately after text)
```
[NULL_PADDING: 00 00 00]
[POINT_COUNT: u32]
[COORDINATES: (u32 x, u32 y) × point_count]
```

### Complete Example: "Quitter" Button

**Text at offset 0x11f70:**
```
"455 430 125 480 0 Quitteri"
```
- Label bounding box: (455, 430) to (125, 480)
- Name: "Quitter" with suffix 'i'

**Binary at offset 0x11f8b:**
```
00 00 00        - Null padding
08 00 00 00     - Point count = 8
06 02 00 00     - X1 = 518
c9 01 00 00     - Y1 = 457
08 02 00 00     - X2 = 520
a0 01 00 00     - Y2 = 416
16 02 00 00     - X3 = 534
78 01 00 00     - Y3 = 376
2e 02 00 00     - X4 = 558
64 01 00 00     - Y4 = 356
5c 02 00 00     - X5 = 604
69 01 00 00     - Y5 = 361
6d 02 00 00     - X6 = 621
92 01 00 00     - Y6 = 402
70 02 00 00     - X7 = 624
c9 01 00 00     - Y7 = 457
50 02 00 00     - X8 = 592
da 01 00 00     - Y8 = 474
```

**Decoded Polygon:**
```
(518, 457) → (520, 416) → (534, 376) → (558, 356) →
(604, 361) → (621, 402) → (624, 457) → (592, 474)
```

**Bounding Box (calculated):**
```
Min: (518, 356)
Max: (624, 474)
```

---

## Binary Pattern Statistics (couleurs1.vnd)

### Most Common Values
| Value | Occurrences | Meaning |
|-------|-------------|---------|
| 0 | 1530 | Null/padding |
| 1 | 215 | Record separator / type 1 |
| 21 | 151 | Conditional length |
| 2 | 61 | Type 2 |
| 83 | 44 | Unknown |
| 38 | 39 | Conditional type |
| 3 | 38 | Type 3 |

### Common Sequences
| Sequence | Count | Interpretation |
|----------|-------|----------------|
| (0, 0, 0) | 798 | Null padding |
| (1, 0, 0) | 21 | Separator + zeros |
| (0, 39, 26) | 21 | Font records |
| (1, 21, 32) | 17 | Conditional + set_var |
| (1, 6, 2) | 13 | Scene type 2 refs |
| (1, 23, 5) | 9 | Game state records |

---

## Complete File Structure (PROVEN)

### Header (offset 0x00)
```
Offset  Size  Field
------  ----  -----
0x00    9     Magic: 3a 01 01 00 00 06 00 00 00
0x09    6     Signature: "VNFILE"
0x0f    4     Version length (uint32)
0x13    n     Version string (e.g., "2.136" + padding)
...     4     Project name length
...     n     Project name (e.g., "Europeo")
...     4     Creator length
...     n     Creator (e.g., "Sopra Multimedia")
...     4     Checksum length
...     n     Checksum (e.g., "5D51F233")
...     8     Padding (zeros)
...     4     Screen width (uint32) = 640
...     4     Screen height (uint32) = 480
...     4     Color depth (uint32) = 16
...     4     Flags (uint32)
...     4     Flags2 (uint32)
...     4     Flags3 (uint32)
...     4     Reserved
...     4     DLL path length
...     n     DLL path (e.g., "..\VnStudio\vnresmod.dll")
```

### Variable Table (follows header)
```
Offset  Size  Field
------  ----  -----
...     4     Section size (uint32)
        Repeating for each variable:
...     4     Variable name length
...     n     Variable name (null-terminated, uppercase)
...     4     Initial value (uint32)
```

**Example Variables from couleurs1.vnd:**
```
SACADOS, JEU, BIDON, MILLEEURO, CALC, TELEPHONE, ACTIVE, FRANCS,
DELPHITEST1, DELPHITEST2, CPAYS, CMENU1, CMENU2, CMENU3,
COMPTEUR1, COMPTEUR2, COMPTEUR3, RAQUETTE, REPONSEM, AFFICHEM,
PIECE, DICO, BEETHOVEN, PHOTO, SCOTCH, QUESTION, REPONSE, NOTE,
MAUVAISENOTE, TAILLEPIERRE, EXPO, CHEVAL, SABOT2, RIZ, CLE, SCORE,
SIROP, LEVURE, CAPITALE, CISEAUX, MENU, PIZZA, COSTUME, LOUPE,
PALME, BOUEE, RESSORT, NUMERO, HARPON, MASQUE, BOUT_PLO, BALLON1,
... (240+ variables total)
```

### Scene/Resource Data
```
[RECORD]
  01 00 00 00     - Record separator
  [LENGTH: u32]   - Length of data
  [TYPE: u32]     - Record type (see enumeration above)
  [DATA: bytes]   - Text command or binary data

[HOTSPOT WITH POLYGON]
  Text: "X Y W H 0 Name"
  00 00 00        - Null padding
  [POINT_COUNT: u32]
  [X1: u32] [Y1: u32]
  [X2: u32] [Y2: u32]
  ... (point_count pairs)
```

### Scene Structure Pattern (PROVEN)

**Scene Header:**
```
Offset  Size  Field
------  ----  -----
...     4     Scene name length
...     n     Scene name (e.g., "Village")
...     12    Flags/metadata (usually zeros with 0x01 marker)
...     4     Separator: 01 00 00 00
...     8     Padding
```

**Scene Content:**
```
1. Audio reference:
   [LENGTH: u32] [TYPE: u32] [PATH: "music.wav" + flags]

2. Background image:
   [LENGTH: u32] [PATH: "euroland\face.bmp"]
   [PADDING: ~16 bytes]
   [COLOR_KEY: db ff ff ff = magenta transparency]

3. Hotspot definitions (repeating):
   - Text format: "X Y W H 0 HotspotName"
   - Binary polygon data
   - Conditional logic

4. Conditional commands:
   - "variable = value then action"
   - Actions: scene, hotspot, addbmp, delbmp, playwav, etc.
```

**Example Scene (couleurs1.vnd offset 0x1145):**
```
07 00 00 00 "Village"        - Scene name (length 7)
00 00 00 00 00 00 00         - Padding
01 00 00 00                  - Separator
00 00 00 00 00 00 00         - Padding
08 00 00 00 09 00 00 00      - Audio header
"music.wav" 02 00 00 00      - Audio path + flags
11 00 00 00                  - BG length = 17
"euroland\face.bmp"          - Background path
[padding + color key]
[hotspot definitions...]
```

**Event Handling:**
Events (EV_ONCLICK, EV_ONFOCUS, EV_ONINIT, EV_AFTERINIT) are NOT stored in VND files.
They are defined in the engine (europeo.exe at 0x43f8cf).
VND files use implicit event binding through:
- Hotspot polygon = clickable area (triggers EV_ONCLICK)
- Conditional commands = actions to execute

---

*Document generated from reverse engineering analysis*
*Last updated: VND binary deep analysis session*
