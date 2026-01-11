# VND Metadata Section - Complete Analysis

## Overview

- **Location**: 0x1059 - 0x1276
- **Size**: 541 bytes
- **Structure**: Length-prefixed text entries (same format as main symbol table)
- **Purpose**: Extended symbols, commands, and resource references

## Contents

Total entries found: **15**

### Variable Names

Additional variable names not in main symbol table:

- `CASTA`
- `EAUPAIN`
- `PAINOK`
- `VINCI`
- `VA`
- `VF`
- `VE`
- `BONUS29`
- `BONUS22`
- `BOUCHE`
- `LAPIN`
- `ANNULE`
- `Village`

### File Paths / Resources

- `euroland\face.bmp`

### Commands / Other

- `4`

## Interpretation

The metadata section appears to contain:

1. **Dynamic variable names**: Variables created at runtime or specific to this scene
2. **Resource references**: Paths to BMP, WAV, AVI files used in the scene
3. **UI commands**: Text display commands, positioning, etc.

## How It's Used

The engine reads this section after loading the main symbol table.
Each entry is processed and likely:
- Registered in a runtime symbol map
- Used to pre-load resources
- Set up UI elements
