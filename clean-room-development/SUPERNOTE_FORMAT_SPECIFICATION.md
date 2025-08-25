# SUPERNOTE .NOTE FILE FORMAT SPECIFICATION
## Independent Binary Analysis Results

**Date**: August 18, 2025  
**Source**: Direct binary analysis of joe.note (1,084,128 bytes)  
**Method**: Hex dump analysis, string extraction, address verification  
**Legal Status**: Clean room research - NO AGPL contamination

---

## FILE STRUCTURE OVERVIEW

### Header Format
```
Offset 0x00-0x0F: "noteSN_FILE_VER_" (ASCII signature)
Offset 0x10-0x17: "20230015" (version identifier)
Offset 0x18-0x1B: Length field (little-endian)
```

### Metadata Format
XML-like tag structure throughout file:
- `<MODULE_LABEL:SNFILE_FEATURE>`
- `<FILE_TYPE:NOTE>`
- `<APPLY_EQUIPMENT:N6>`

---

## LAYER STRUCTURE ANALYSIS

### Layer Metadata Pattern
Each layer contains these tags:
```xml
<LAYERTYPE:NOTE>
<LAYERPROTOCOL:RATTA_RLE>
<LAYERNAME:MAINLAYER|BGLAYER>
<LAYERPATH:0>
<LAYERBITMAP:ADDRESS>
<LAYERVECTORGRAPH:0>
<LAYERRECOGN:0>
```

### Discovered Layer Addresses

**PAGE 1**:
- MAINLAYER bitmap: Address 768, Length: 141,890 bytes
- BGLAYER bitmap: Address 440, Length: 324 bytes

**PAGE 2**:
- MAINLAYER bitmap: Address 847,208, Length: 40,750 bytes  
- BGLAYER bitmap: Address 440, Length: 324 bytes (shared)

### Layer Information JSON
```json
"LAYERINFO": [
  {"layerId": 3, "name": "Layer 3", "isDeleted": true},
  {"layerId": 2, "name": "Layer 2", "isDeleted": true}, 
  {"layerId": 1, "name": "Layer 1", "isDeleted": true},
  {"layerId": 0, "name": "Main Layer", "isCurrentLayer": true, "isVisible": true},
  {"layerId": -1, "name": "Background Layer", "isBackgroundLayer": true, "isVisible": true}
]
```

---

## RLE COMPRESSION FORMAT

### Address-Based Extraction Method
1. **Locate LAYERBITMAP:ADDRESS in metadata**
2. **Read 4-byte length field at address** (little-endian)
3. **Extract RLE data starting at address + 4**
4. **Decode using RATTA_RLE protocol**

### RLE Color Code Patterns
From binary analysis at bitmap addresses:

**Primary Color Codes**: 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68
- **0x61**: Grayscale level (observed with length values)
- **0x62**: Dominant color (most frequent in data)
- **0xFF**: Special length marker patterns

**Example RLE Sequence**:
```
62 ff 62 ff 62 ff  -> Color 0x62, lengths 0xFF, 0xFF, 0xFF
61 05 0f 00 7f 00  -> Color 0x61, length 5, skip 15, length 127
62 89 62 6d cf 00  -> Color 0x62, various length encodings
```

### Length Encoding Analysis
- **Single byte lengths**: 0x01-0x7F
- **Multi-byte patterns**: 0xFF markers
- **Skip patterns**: 0x00 values interleaved
- **Complex sequences**: Multiple bytes per pixel run

---

## MULTI-LAYER COMPOSITION STRATEGY

### Layer Extraction Requirements
Based on discovered structure, comprehensive extraction requires:

1. **MAINLAYER Processing**:
   - Address: Variable per page
   - Size: 40K-140K bytes per page
   - Content: Primary handwritten content

2. **BGLAYER Processing**:
   - Address: 440 (shared across pages)
   - Size: 324 bytes
   - Content: Background/template data

3. **Additional Layers** (LAYER1, LAYER2, LAYER3):
   - Most marked as deleted in test file
   - Addresses: 0 (no bitmap data)
   - Future expansion capability

### Performance Implications
**Current baseline**: 95,031 pixels from MAINLAYER only  
**Target improvement**: Access BGLAYER + additional processing

**Projected improvements**:
- BGLAYER addition: +324 bytes of compressed data
- Enhanced RLE decoding: Better length interpretation
- Multi-layer composition: Layer blending algorithms

---

## INDEPENDENT ALGORITHM DESIGN

### Enhanced RLE Decoder Requirements

1. **Address Resolution**: Correct interpretation of LAYERBITMAP tags as addresses
2. **Length Field Reading**: 4-byte little-endian at bitmap address
3. **Multi-Pattern RLE**: Handle complex length encoding sequences
4. **Color Code Mapping**: Support all 0x61-0x68 patterns
5. **Layer Composition**: Blend multiple bitmap sources

### Commercial Performance Target
**Current**: 95K pixels in 0.058s  
**Required**: 2.6M+ pixels in <0.5s  
**Strategy**: Multi-address extraction + optimized RLE algorithms

---

## TECHNICAL VALIDATION APPROACH

### Binary Analysis Validation
All findings derived from direct hex dump analysis:
- File signature confirmation: ✓
- Address verification: ✓  
- Length field validation: ✓
- RLE pattern identification: ✓

### Independence Verification
- **NO access** to AGPL reference implementations
- **NO algorithm derivation** from external sources
- **ONLY binary analysis** of actual .note files
- **Clean room protocols** maintained throughout

---

## NEXT PHASE REQUIREMENTS

### Algorithm Development Priorities
1. **Multi-Address Bitmap Extraction**: Access all layer addresses
2. **Enhanced RLE Length Decoding**: Handle complex patterns
3. **Layer Composition System**: Blend MAINLAYER + BGLAYER
4. **Performance Optimization**: Achieve 27x pixel improvement

### Success Metrics
- **Pixel extraction**: 2.6M+ pixels (commercial threshold)
- **Processing speed**: <0.5s per page maintained
- **Legal compliance**: Zero AGPL contamination verified
- **Format compatibility**: Handle various .note file versions

---

**CRITICAL SUCCESS FACTOR**: This specification provides the foundation for developing a commercially viable, AGPL-free Supernote decoder through independent research and clean room implementation protocols.