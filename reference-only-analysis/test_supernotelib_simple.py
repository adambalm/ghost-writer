#!/usr/bin/env python3
"""
Simple test of supernotelib conversion
"""

try:
    import supernotelib as sn
    from supernotelib.converter import ImageConverter
    
    note_path = "/home/ed/ghost-writer/temp_20250807_035920.note"
    notebook = sn.load_notebook(note_path)
    
    print(f"✅ Notebook loaded: {notebook.get_total_pages()} pages")
    print(f"📐 Notebook dimensions: {notebook.get_width()} x {notebook.get_height()}")
    
    # Try different converter approaches
    converter = ImageConverter(notebook)
    
    # Try with additional parameters to avoid the error
    for i in range(notebook.get_total_pages()):
        output_path = f"/home/ed/ghost-writer/supernotelib_page_{i+1}.png"
        print(f"\n🖼️  Converting page {i+1}...")
        
        try:
            # Try basic conversion
            converter.convert(i, output_path)
            print(f"✅ Basic conversion successful")
        except Exception as e1:
            print(f"❌ Basic conversion failed: {e1}")
            
            try:
                # Try with empty options
                converter.convert(i, output_path, {})
                print(f"✅ Conversion with empty options successful")
            except Exception as e2:
                print(f"❌ Conversion with options failed: {e2}")
                
                try:
                    # Try with different parameters
                    converter.convert(i, output_path, highres_grayscale=False)
                    print(f"✅ Conversion with highres_grayscale=False successful")
                except Exception as e3:
                    print(f"❌ All conversion attempts failed: {e3}")
                    continue
        
        # Check result
        from pathlib import Path
        if Path(output_path).exists():
            size = Path(output_path).stat().st_size
            print(f"   📊 Image size: {size:,} bytes")
            
            # Quick check if image has content
            from PIL import Image
            import numpy as np
            img = Image.open(output_path)
            arr = np.array(img)
            print(f"   📈 Mean pixel value: {arr.mean():.1f} ({'Content!' if arr.mean() < 250 else 'Blank'})")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()