#!/usr/bin/env python3
"""Test ChatGPT's updated holder/queue RLE decoder"""

import sys
sys.path.insert(0, '/home/ed/ghost-writer/src')

# ChatGPT's updated implementation
DEFAULT_PALETTE = {
    0x61: 0x00,  # black
    0x62: 0xFF,  # background/paper
    0x63: 0x70,  # dark gray
    0x64: 0xA0,  # gray
    0x65: 0xC0,
    0x66: 0xD0,
    0x67: 0xE0,
    0x68: 0xF0,  # lightest
}

class RLEError(ValueError):
    pass

def _emit_run(out, pos, run, color_val, total):
    """Emit a run, bounds-checked, returns new pos."""
    if run <= 0 or pos + run > total:
        raise RLEError(f"RLE overflow/underflow (pos={pos}, run={run}, total={total})")
    out[pos:pos+run] = bytes([color_val]) * run
    return pos + run

def decode_ratta_rle_holder(payload, width, height, palette=None, ff_value_mode="auto"):
    """ChatGPT's holder/queue implementation"""
    if palette is None:
        palette = DEFAULT_PALETTE

    total = width * height
    out = bytearray(total)
    pos = 0

    it = iter(payload)
    held = None  # (colorcode, lenbyte_with_highbit)

    def high_from_lenbyte(lb):
        return ((lb & 0x7F) + 1) << 7

    def ff_value_for(pos, total):
        if ff_value_mode == "4000":
            return 0x4000
        if ff_value_mode == "0400":
            return 0x0400
        # auto: prefer 0x4000; if it would overflow, use 0x0400
        return 0x4000 if pos + 0x4000 <= total else 0x0400

    try:
        while pos < total:
            color = next(it)
            try:
                lb = next(it)
            except StopIteration:
                raise RLEError("Unexpected EOF: missing length byte for color") from None

            # If we have a held command, decide whether to emit it before handling current
            if held is not None:
                h_color, h_lb = held
                # Case 1: same color and current is NORMAL -> combine and emit single run
                if color == h_color and lb != 0xFF and (lb & 0x80) == 0:
                    run = high_from_lenbyte(h_lb) + (lb + 1)
                    pos = _emit_run(out, pos, run, palette.get(color, 0x00), total)
                    held = None
                    continue
                else:
                    # Emit held alone with HIGH bits only
                    run = high_from_lenbyte(h_lb)
                    pos = _emit_run(out, pos, run, palette.get(h_color, 0x00), total)
                    held = None

            # Process current command
            if lb == 0xFF:
                run = ff_value_for(pos, total)
                pos = _emit_run(out, pos, run, palette.get(color, 0x00), total)
            elif (lb & 0x80) != 0:
                # Hold high bits for potential combination with next normal of same color
                held = (color, lb)
            else:
                # Normal run
                run = lb + 1
                pos = _emit_run(out, pos, run, palette.get(color, 0x00), total)

    except StopIteration:
        raise RLEError("Unexpected EOF while reading commands")

    return out

def test_implementations():
    # Read joe.note bitmap data
    with open('/home/ed/ghost-writer/joe.note', 'rb') as f:
        data = f.read()
    
    # Page 1 MAINLAYER
    address = 768
    length = int.from_bytes(data[address:address+4], 'little')
    bitmap_data = data[address+4:address+4+length]
    
    print(f"Testing ChatGPT's holder/queue decoder on {length:,} bytes")
    print("=" * 70)
    
    # Test ChatGPT's holder implementation
    print("\n1. ChatGPT's Holder/Queue Decoder:")
    try:
        result = decode_ratta_rle_holder(bitmap_data, 1404, 1872, ff_value_mode="auto")
        import numpy as np
        arr = np.frombuffer(result, dtype=np.uint8).reshape((1872, 1404))
        non_white = np.sum(arr < 255)
        print(f"   SUCCESS: {non_white:,} non-white pixels")
        print(f"   Total pixels: {len(result):,}")
        print(f"   Target: 2,859,430 pixels")
        print(f"   Achievement: {non_white/2859430*100:.1f}% of sn2md target")
        
        # Test with different ff modes
        for ff_mode in ["4000", "0400"]:
            try:
                result_mode = decode_ratta_rle_holder(bitmap_data, 1404, 1872, ff_value_mode=ff_mode)
                arr_mode = np.frombuffer(result_mode, dtype=np.uint8).reshape((1872, 1404))
                non_white_mode = np.sum(arr_mode < 255)
                print(f"   With ff_mode='{ff_mode}': {non_white_mode:,} pixels")
            except Exception as e:
                print(f"   With ff_mode='{ff_mode}': FAILED - {e}")
        
    except Exception as e:
        print(f"   FAILED: {e}")
    
    # Compare with our current implementation
    print("\n2. Our Current Decoder:")
    try:
        from utils.supernote_parser import SupernoteParser
        parser = SupernoteParser()
        result = parser._decode_ratta_rle(bitmap_data, 1404, 1872)
        non_white = np.sum(result < 255)
        print(f"   Our result: {non_white:,} non-white pixels")
    except Exception as e:
        print(f"   FAILED: {e}")
    
    # Test Page 2 as well
    print("\n3. Testing Page 2 (smaller dataset):")
    address_p2 = 847208
    length_p2 = int.from_bytes(data[address_p2:address_p2+4], 'little')
    bitmap_data_p2 = data[address_p2+4:address_p2+4+length_p2]
    
    try:
        result_p2 = decode_ratta_rle_holder(bitmap_data_p2, 1404, 1872, ff_value_mode="auto")
        arr_p2 = np.frombuffer(result_p2, dtype=np.uint8).reshape((1872, 1404))
        non_white_p2 = np.sum(arr_p2 < 255)
        print(f"   Page 2: {non_white_p2:,} non-white pixels")
        print(f"   Target: 2,693,922 pixels (sn2md INVISIBLE)")
        print(f"   Achievement: {non_white_p2/2693922*100:.1f}% of target")
    except Exception as e:
        print(f"   Page 2 FAILED: {e}")

if __name__ == "__main__":
    test_implementations()