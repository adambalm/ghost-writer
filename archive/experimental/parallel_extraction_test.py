#!/usr/bin/env python3
"""
Parallel testing: sn2md approach vs our custom parser approach
"""

import sys
from pathlib import Path
import time
import json
from datetime import datetime

# Add project paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "sn2md"))

def test_sn2md_approach(note_path):
    """Test extraction using sn2md/supernotelib approach"""
    
    print("🔧 Testing sn2md/supernotelib Approach")
    print("=" * 45)
    
    results = {"approach": "sn2md", "success": False, "pages": [], "errors": []}
    
    try:
        from sn2md.importers.note import load_notebook
        import supernotelib as sn
        from supernotelib.converter import ImageConverter, VisibilityOverlay
        
        start_time = time.time()
        
        # Load notebook
        notebook = load_notebook(str(note_path))
        converter = ImageConverter(notebook)
        
        results["total_pages"] = notebook.get_total_pages()
        results["dimensions"] = f"{notebook.get_width()}x{notebook.get_height()}"
        
        print(f"✅ Loaded: {results['total_pages']} pages, {results['dimensions']}")
        
        # Test visibility settings
        visibility_options = [
            ("INVISIBLE", VisibilityOverlay.INVISIBLE),
            ("DEFAULT", VisibilityOverlay.DEFAULT),
            ("VISIBLE", VisibilityOverlay.VISIBLE)
        ]
        
        for vis_name, vis_option in visibility_options:
            print(f"\n📄 Testing {vis_name}:")
            
            try:
                vo = sn.converter.build_visibility_overlay(background=vis_option)
                
                for page_idx in range(results["total_pages"]):
                    img = converter.convert(page_idx, vo)
                    
                    # Analyze content
                    import numpy as np
                    arr = np.array(img)
                    mean_val = arr.mean()
                    non_white = np.sum(arr < 250)
                    
                    page_result = {
                        "page": page_idx + 1,
                        "visibility": vis_name,
                        "content_pixels": int(non_white),
                        "mean_brightness": float(round(mean_val, 2)),
                        "has_content": bool(non_white > 1000),
                        "image_mode": img.mode,
                        "image_size": img.size
                    }
                    
                    results["pages"].append(page_result)
                    
                    status = "✅" if page_result["has_content"] else "❌"
                    print(f"  Page {page_idx + 1}: {non_white:,} pixels {status}")
                    
            except Exception as e:
                error = f"{vis_name}: {str(e)}"
                results["errors"].append(error)
                print(f"  ❌ {error}")
        
        results["processing_time"] = time.time() - start_time
        results["success"] = len([p for p in results["pages"] if p["has_content"]]) > 0
        
        print(f"\n📊 sn2md Summary:")
        print(f"  ⏱️  Time: {results['processing_time']:.2f}s")
        print(f"  ✅ Content found: {len([p for p in results['pages'] if p['has_content']])} extractions")
        
    except Exception as e:
        results["errors"].append(f"Failed to load: {str(e)}")
        print(f"❌ sn2md approach failed: {e}")
    
    return results

def test_our_custom_approach(note_path):
    """Test extraction using our custom parser approach"""
    
    print("\n🛠️ Testing Our Custom Parser Approach")
    print("=" * 45)
    
    results = {"approach": "custom", "success": False, "pages": [], "errors": []}
    
    try:
        from utils.supernote_parser import SupernoteParser
        
        start_time = time.time()
        
        # Use our custom parser
        parser = SupernoteParser()
        pages = parser.parse_file(note_path)
        
        results["total_pages"] = len(pages)
        
        print(f"✅ Parsed: {len(pages)} pages with custom parser")
        
        if not pages:
            results["errors"].append("No pages parsed")
            print("❌ No pages found")
            return results
        
        # Analyze each page
        for i, page in enumerate(pages):
            print(f"\n📄 Page {i + 1}:")
            print(f"  Metadata: {page.metadata}")
            
            page_result = {
                "page": i + 1,
                "visibility": "custom",
                "metadata": page.metadata,
                "has_content": False,
                "content_pixels": 0,
                "image_size": None
            }
            
            # Check if we can render this page
            if page.metadata.get("status") == "unsupported":
                error = f"Page {i + 1}: {page.metadata.get('message', 'Unsupported format')}"
                results["errors"].append(error)
                print(f"  ❌ {error}")
                page_result["error"] = error
            else:
                try:
                    # Try to render the page
                    image = parser.render_page_to_image(page)
                    
                    # Analyze content
                    import numpy as np
                    arr = np.array(image)
                    non_white = np.sum(arr < 250)
                    
                    page_result.update({
                        "has_content": bool(non_white > 1000),
                        "content_pixels": int(non_white),
                        "mean_brightness": float(round(arr.mean(), 2)),
                        "image_size": image.size,
                        "image_mode": image.mode
                    })
                    
                    status = "✅" if page_result["has_content"] else "❌"
                    print(f"  Content: {non_white:,} pixels {status}")
                    
                except Exception as e:
                    error = f"Page {i + 1} render failed: {str(e)}"
                    results["errors"].append(error)
                    page_result["error"] = error
                    print(f"  ❌ {error}")
            
            results["pages"].append(page_result)
        
        results["processing_time"] = time.time() - start_time
        results["success"] = len([p for p in results["pages"] if p["has_content"]]) > 0
        
        print(f"\n📊 Custom Parser Summary:")
        print(f"  ⏱️  Time: {results['processing_time']:.2f}s")
        print(f"  ✅ Content found: {len([p for p in results['pages'] if p['has_content']])} pages")
        
    except Exception as e:
        results["errors"].append(f"Custom parser failed: {str(e)}")
        print(f"❌ Custom approach failed: {e}")
        import traceback
        traceback.print_exc()
    
    return results

def compare_results(sn2md_results, custom_results):
    """Compare the two approaches"""
    
    print("\n📊 Parallel Testing Comparison")
    print("=" * 50)
    
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "sn2md": sn2md_results,
        "custom": custom_results,
        "winner": None,
        "analysis": {}
    }
    
    # Success comparison
    sn2md_success = sn2md_results.get("success", False)
    custom_success = custom_results.get("success", False)
    
    print(f"🏆 Success Rate:")
    print(f"  sn2md: {'✅' if sn2md_success else '❌'}")
    print(f"  Custom: {'✅' if custom_success else '❌'}")
    
    # Content comparison
    sn2md_content = len([p for p in sn2md_results.get("pages", []) if p.get("has_content", False)])
    custom_content = len([p for p in custom_results.get("pages", []) if p.get("has_content", False)])
    
    print(f"\n📄 Content Extraction:")
    print(f"  sn2md: {sn2md_content} extractions with content")
    print(f"  Custom: {custom_content} pages with content")
    
    # Performance comparison
    sn2md_time = sn2md_results.get("processing_time", 0)
    custom_time = custom_results.get("processing_time", 0)
    
    print(f"\n⏱️ Performance:")
    print(f"  sn2md: {sn2md_time:.2f}s")
    print(f"  Custom: {custom_time:.2f}s")
    
    # Error comparison
    sn2md_errors = len(sn2md_results.get("errors", []))
    custom_errors = len(custom_results.get("errors", []))
    
    print(f"\n❌ Errors:")
    print(f"  sn2md: {sn2md_errors} errors")
    print(f"  Custom: {custom_errors} errors")
    
    # Determine winner
    if sn2md_success and not custom_success:
        comparison["winner"] = "sn2md"
        print(f"\n🏆 Winner: sn2md (only working approach)")
    elif custom_success and not sn2md_success:
        comparison["winner"] = "custom"
        print(f"\n🏆 Winner: Custom parser (only working approach)")
    elif sn2md_success and custom_success:
        if sn2md_content > custom_content:
            comparison["winner"] = "sn2md"
            print(f"\n🏆 Winner: sn2md (more content extracted)")
        elif custom_content > sn2md_content:
            comparison["winner"] = "custom"
            print(f"\n🏆 Winner: Custom parser (more content extracted)")
        else:
            comparison["winner"] = "tie"
            print(f"\n🤝 Result: Tie (both approaches work similarly)")
    else:
        comparison["winner"] = "none"
        print(f"\n😞 Result: Neither approach successfully extracted content")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if comparison["winner"] == "sn2md":
        print("  - Use sn2md/supernotelib as primary extraction method")
        print("  - Focus on building advanced features on top of sn2md")
        print("  - Keep custom parser as backup for unsupported formats")
    elif comparison["winner"] == "custom":
        print("  - Our custom parser handles your format better")
        print("  - Continue developing custom RLE decoder improvements")
        print("  - Consider contributing fixes back to supernotelib")
    elif comparison["winner"] == "tie":
        print("  - Both approaches work - choose based on other factors")
        print("  - sn2md: More mature, community support")
        print("  - Custom: More control, can add custom features")
    else:
        print("  - Neither approach works with this file format")
        print("  - May need to investigate Supernote Cloud export API")
        print("  - Consider photo-based workflow as alternative")
    
    # Save detailed results
    results_file = project_root / "parallel_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    
    return comparison

def main():
    """Run parallel testing on your note file"""
    
    print("🔬 Parallel Extraction Testing")
    print("=" * 40)
    
    # Use joe.note if it exists, otherwise ask user
    note_path = project_root / "joe.note"
    
    if not note_path.exists():
        print(f"❌ joe.note not found at {note_path}")
        print("Run get_my_note.py first to download your note file")
        return
    
    print(f"📄 Testing with: {note_path}")
    
    # Run both approaches
    sn2md_results = test_sn2md_approach(note_path)
    custom_results = test_our_custom_approach(note_path)
    
    # Compare and analyze
    comparison = compare_results(sn2md_results, custom_results)
    
    return comparison

if __name__ == "__main__":
    main()