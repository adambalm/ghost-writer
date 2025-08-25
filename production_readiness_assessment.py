#!/usr/bin/env python3
"""
Production Readiness Assessment for RLE Decoder Improvements

Simplified assessment focused on core validation metrics.
"""

import sys
import time
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "sn2md"))

def assess_production_readiness():
    """Assess production readiness of RLE decoder improvements"""
    
    print("🚀 Production Readiness Assessment")
    print("=" * 50)
    
    note_path = project_root / "joe.note"
    if not note_path.exists():
        print(f"❌ Note file not found: {note_path}")
        return
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "baseline_metrics": {},
        "improved_metrics": {},
        "original_metrics": {},
        "analysis": {},
        "production_readiness": {}
    }
    
    # 1. Test sn2md baseline
    print("\n📊 Testing sn2md baseline...")
    baseline = test_sn2md_extraction(note_path)
    results["baseline_metrics"] = baseline
    
    # 2. Test improved custom decoder
    print("\n🛠️ Testing improved custom decoder...")
    improved = test_improved_custom_extraction(note_path)
    results["improved_metrics"] = improved
    
    # 3. Test original custom decoder
    print("\n🔧 Testing original custom decoder...")
    original = test_original_custom_extraction(note_path)
    results["original_metrics"] = original
    
    # 4. Analysis
    print("\n📈 Performance Analysis...")
    analysis = analyze_improvements(baseline, improved, original)
    results["analysis"] = analysis
    
    # 5. Production readiness score
    print("\n🎯 Production Readiness Score...")
    readiness = calculate_readiness_score(baseline, improved, original, analysis)
    results["production_readiness"] = readiness
    
    # 6. Save results
    report_path = project_root / f"production_readiness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # 7. Summary
    print_summary(results)
    print(f"\n📄 Full report: {report_path}")
    
    return results

def test_sn2md_extraction(note_path):
    """Test sn2md extraction method"""
    
    try:
        from sn2md.importers.note import load_notebook
        import supernotelib as sn
        from supernotelib.converter import ImageConverter, VisibilityOverlay
        
        start_time = time.time()
        
        notebook = load_notebook(str(note_path))
        converter = ImageConverter(notebook)
        vo = sn.converter.build_visibility_overlay(background=VisibilityOverlay.INVISIBLE)
        
        total_pixels = 0
        pages_with_content = 0
        
        for page_idx in range(notebook.get_total_pages()):
            img = converter.convert(page_idx, vo)
            arr = np.array(img)
            content_pixels = int(np.sum(arr < 250))
            total_pixels += content_pixels
            
            if content_pixels > 1000:
                pages_with_content += 1
            
            print(f"   Page {page_idx + 1}: {content_pixels:,} pixels")
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "processing_time": processing_time,
            "total_pixels": total_pixels,
            "pages_with_content": pages_with_content,
            "total_pages": notebook.get_total_pages(),
            "meets_performance_target": processing_time < 0.5,
            "method": "sn2md"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "method": "sn2md"
        }

def test_improved_custom_extraction(note_path):
    """Test improved custom extraction method"""
    
    try:
        from utils.supernote_parser import SupernoteParser
        
        start_time = time.time()
        
        parser = SupernoteParser()
        pages = parser.parse_file(note_path)
        
        total_pixels = 0
        pages_with_content = 0
        
        for i, page in enumerate(pages):
            try:
                image = parser.render_page_to_image(page)
                arr = np.array(image)
                content_pixels = int(np.sum(arr < 250))
                total_pixels += content_pixels
                
                if content_pixels > 1000:
                    pages_with_content += 1
                
                print(f"   Page {i + 1}: {content_pixels:,} pixels")
                
            except Exception as e:
                print(f"   Page {i + 1}: Error - {e}")
        
        processing_time = time.time() - start_time
        
        return {
            "success": pages_with_content > 0,
            "processing_time": processing_time,
            "total_pixels": total_pixels,
            "pages_with_content": pages_with_content,
            "total_pages": len(pages),
            "meets_performance_target": processing_time < 0.5,
            "method": "improved_custom"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "method": "improved_custom"
        }

def test_original_custom_extraction(note_path):
    """Simulate original custom extraction method results"""
    
    # Based on previous test results: 188 + 606 = 794 pixels total
    return {
        "success": False,  # Below 1000 pixel threshold
        "processing_time": 0.016,
        "total_pixels": 794,
        "pages_with_content": 0,
        "total_pages": 2,
        "meets_performance_target": True,
        "method": "original_custom"
    }

def analyze_improvements(baseline, improved, original):
    """Analyze improvements between methods"""
    
    analysis = {}
    
    # Improvement factor
    if original.get("total_pixels", 0) > 0:
        improvement_factor = improved.get("total_pixels", 0) / original.get("total_pixels", 1)
        analysis["improvement_factor"] = improvement_factor
    else:
        analysis["improvement_factor"] = 0
    
    # Gap to baseline
    baseline_pixels = baseline.get("total_pixels", 1)
    improved_pixels = improved.get("total_pixels", 0)
    gap_ratio = improved_pixels / baseline_pixels
    analysis["baseline_gap_ratio"] = gap_ratio
    analysis["remaining_gap"] = 1 - gap_ratio
    
    # Performance comparison
    analysis["performance_comparison"] = {
        "sn2md_time": baseline.get("processing_time", 0),
        "improved_time": improved.get("processing_time", 0),
        "original_time": original.get("processing_time", 0),
        "improved_faster_than_sn2md": improved.get("processing_time", 999) < baseline.get("processing_time", 0)
    }
    
    # Success rates
    analysis["success_rates"] = {
        "sn2md": baseline.get("success", False),
        "improved": improved.get("success", False),
        "original": original.get("success", False)
    }
    
    return analysis

def calculate_readiness_score(baseline, improved, original, analysis):
    """Calculate production readiness score"""
    
    score = 0
    max_score = 100
    blockers = []
    recommendations = []
    
    # Performance criteria (20 points)
    if improved.get("meets_performance_target", False):
        score += 15
    elif improved.get("processing_time", 999) < 1.0:
        score += 10
    
    if improved.get("success", False):
        score += 5
    
    # Content extraction quality (40 points)
    gap_ratio = analysis.get("baseline_gap_ratio", 0)
    
    if gap_ratio >= 0.8:  # 80% of baseline
        score += 35
    elif gap_ratio >= 0.5:  # 50% of baseline
        score += 25
    elif gap_ratio >= 0.2:  # 20% of baseline
        score += 15
    elif gap_ratio >= 0.05:  # 5% of baseline
        score += 10
    elif gap_ratio > 0:  # Any content
        score += 5
    
    # Improvement factor (25 points)
    improvement_factor = analysis.get("improvement_factor", 0)
    if improvement_factor >= 100:
        score += 25
    elif improvement_factor >= 50:
        score += 20
    elif improvement_factor >= 10:
        score += 15
    elif improvement_factor >= 5:
        score += 10
    elif improvement_factor >= 2:
        score += 5
    
    # Technical implementation (15 points)
    if improved.get("processing_time", 999) < baseline.get("processing_time", 999):
        score += 5  # Faster than baseline
    
    if improved.get("success", False) and original.get("success", False) == False:
        score += 10  # Fixed functionality that was broken
    
    # Determine status
    if score >= 80:
        status = "production_ready"
        recommendations.append("Ready for production deployment")
    elif score >= 60:
        status = "almost_ready"
        recommendations.append("Minor improvements needed")
        blockers.append(f"Content gap: {(1-gap_ratio)*100:.1f}% below baseline")
    elif score >= 40:
        status = "development_stage"
        recommendations.append("Significant development work required")
        blockers.append(f"Major content gap: {(1-gap_ratio)*100:.1f}% below baseline")
    else:
        status = "not_ready"
        recommendations.append("Major architectural changes needed")
        blockers.append(f"Critical content gap: {(1-gap_ratio)*100:.1f}% below baseline")
    
    # Specific blockers
    if gap_ratio < 0.5:
        blockers.append(f"Content extraction below 50% of baseline ({gap_ratio:.1%})")
    
    if not improved.get("meets_performance_target", False):
        blockers.append(f"Performance target missed: {improved.get('processing_time', 'unknown')}s > 0.5s")
    
    return {
        "score": score,
        "max_score": max_score,
        "status": status,
        "blockers": blockers,
        "recommendations": recommendations,
        "metrics": {
            "content_gap_percentage": (1 - gap_ratio) * 100,
            "improvement_factor": improvement_factor,
            "performance_ratio": improved.get("processing_time", 999) / max(baseline.get("processing_time", 0.001), 0.001)
        }
    }

def print_summary(results):
    """Print summary of results"""
    
    print("\n" + "="*60)
    print("📋 PRODUCTION READINESS SUMMARY")
    print("="*60)
    
    readiness = results["production_readiness"]
    analysis = results["analysis"]
    
    print(f"🎯 Overall Score: {readiness['score']}/{readiness['max_score']}")
    print(f"🚦 Status: {readiness['status']}")
    
    print(f"\n📊 Key Metrics:")
    print(f"   Improvement Factor: {analysis.get('improvement_factor', 0):.1f}x")
    print(f"   Baseline Gap: {readiness['metrics']['content_gap_percentage']:.1f}%")
    print(f"   Performance Ratio: {readiness['metrics']['performance_ratio']:.2f}x baseline time")
    
    print(f"\n⏱️ Performance Summary:")
    baseline = results["baseline_metrics"]
    improved = results["improved_metrics"]
    original = results["original_metrics"]
    
    print(f"   sn2md baseline: {baseline.get('processing_time', 0):.3f}s, {baseline.get('total_pixels', 0):,} pixels")
    print(f"   Improved custom: {improved.get('processing_time', 0):.3f}s, {improved.get('total_pixels', 0):,} pixels")
    print(f"   Original custom: {original.get('processing_time', 0):.3f}s, {original.get('total_pixels', 0):,} pixels")
    
    if readiness["blockers"]:
        print("\n🚫 Production Blockers:")
        for blocker in readiness["blockers"]:
            print(f"   - {blocker}")
    
    print("\n💡 Recommendations:")
    for rec in readiness["recommendations"]:
        print(f"   - {rec}")
    
    # Next steps
    gap_ratio = analysis.get("baseline_gap_ratio", 0)
    if gap_ratio < 0.5:
        print("\n🎯 Next Steps to Close Gap:")
        print("   1. Investigate sn2md's INVISIBLE layer extraction method")
        print("   2. Analyze bitmap data extraction differences")
        print("   3. Improve RLE decoding algorithms")
        print("   4. Consider hybrid approach: sn2md + custom enhancements")

if __name__ == "__main__":
    assess_production_readiness()