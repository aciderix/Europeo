# VND Loading Flow - Complete Disassembly

## 1. TEventHandler::Dispatch (Event Router)

**Location**: `@TEventHandler@Dispatch$qr24TEventHandler@TEventInfouil` @ 0x0041A32B

**Purpose**: Routes Windows messages and VND events to appropriate handlers

**Key Calls**: 0 function calls

## 2. ipstream::readWord32 (Read 32-bit Integer)

**Location**: `@ipstream@readWord32$qv` @ 0x00403C74

**Purpose**: Reads a 32-bit little-endian integer from stream

**Instructions**: 28

## 3. ipstream::readBytes (Read Byte Array)

**Location**: `@ipstream@readBytes$qpvui` @ 0x00403B6C

**Purpose**: Reads N bytes from stream into buffer

**Instructions**: 29

## Complete VND Loading Flow

```
1. User Action → Windows Event
   ↓
2. TEventHandler::Dispatch (owl52t.dll)
   - Routes event to appropriate handler
   ↓
3. TFileDocument::InStream / fpbase::open
   - Opens .vnd file
   - Creates ipstream object
   ↓
4. Parse VND Header (12 bytes)
   - ipstream::readWord32() × 3
   ↓
5. Find 'VNFILE' Signature
   - ipstream::readBytes(6)
   ↓
6. Parse Length-Prefixed Strings
   Loop:
     - ipstream::readWord32() → length
     - ipstream::readBytes(length) → string data
   Reads:
     a) Version
     b) Application
     c) Symbol Table (200+ vars)
     d) Metadata (13+ vars + resources)
   ↓
7. Parse Script Section
   - Remaining bytes as ASCII text
   ↓
8. TEventHandler::Dispatch
   - Execute script commands
   - Route to UI handlers
```

