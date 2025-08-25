#!/usr/bin/env python3
"""
Explore what's available in supernotelib
"""

try:
    import supernotelib as sn
    print("✅ supernotelib imported successfully")
    print("📋 Available attributes:")
    
    for attr in dir(sn):
        if not attr.startswith('_'):
            print(f"  - {attr}")
            try:
                obj = getattr(sn, attr)
                print(f"    Type: {type(obj)}")
                if hasattr(obj, '__doc__') and obj.__doc__:
                    doc = obj.__doc__.strip().split('\n')[0]
                    print(f"    Doc: {doc}")
            except:
                pass
            print()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()