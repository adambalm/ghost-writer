#!/usr/bin/env python3
"""
Production Validation Test Suite for RLE Decoder Improvements

This test suite provides comprehensive validation of the RLE decoder improvements
against the sn2md baseline to establish production readiness metrics.

Commercial licensing: Independent implementation without external dependencies.
"""

import sys
import time
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from PIL import Image, ImageStat

# Add project paths
project_root = Path("/home/ed/ghost-writer")
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "sn2md"))

class ProductionValidationSuite:
    """Comprehensive validation suite for production readiness assessment"""
    
    def __init__(self, note_path: Path):
        self.note_path = note_path
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "note_file": str(note_path),
            "validation_metrics": {},
            "quality_gates": {},
            "performance_benchmarks": {},
            "production_readiness": {
                "score": 0,
                "status": "not_ready",
                "blockers": [],
                "recommendations": []
            }
        }
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run the complete validation suite"""
        
        print("🔬 Production Validation Suite")
        print("=" * 50)
        print(f"📄 Target file: {self.note_path}")
        print(f"🕒 Started: {self.results['timestamp']}")
        
        # 1. Performance Benchmarking
        print("\n⏱️ Performance Benchmarking...")
        self._benchmark_performance()
        
        # 2. Quality Assessment
        print("\n🎯 Quality Assessment...")
        self._assess_quality()
        
        # 3. Pixel-Perfect Comparison
        print("\n🔍 Pixel-Perfect Comparison...")
        self._pixel_perfect_comparison()
        
        # 4. Commercial Licensing Compliance
        print("\n⚖️ Commercial Licensing Compliance...")
        self._validate_licensing_compliance()
        
        # 5. Production Readiness Assessment
        print("\n🚀 Production Readiness Assessment...")
        self._assess_production_readiness()
        
        # 6. Generate Report
        report_path = self._generate_validation_report()
        
        print(f"\n📊 Validation completed. Report: {report_path}")
        return self.results
    
    def _benchmark_performance(self):
        """Benchmark performance of all extraction methods"""
        
        benchmarks = {}
        
        # Benchmark sn2md approach
        print("   📊 Benchmarking sn2md...")
        start_time = time.time()
        sn2md_results = self._test_sn2md_extraction()
        sn2md_time = time.time() - start_time
        
        benchmarks["sn2md"] = {
            "processing_time": sn2md_time,
            "success": sn2md_results.get("success", False),
            "total_pixels": sum(p.get("content_pixels", 0) for p in sn2md_results.get("pages", [])),
            "max_pixels": max((p.get("content_pixels", 0) for p in sn2md_results.get("pages", [])), default=0),
            "meets_performance_target": sn2md_time < 0.5
        }
        
        # Benchmark improved custom decoder
        print("   🛠️ Benchmarking improved custom decoder...")
        start_time = time.time()
        improved_results = self._test_improved_custom_extraction()
        improved_time = time.time() - start_time
        
        benchmarks["improved_custom"] = {
            "processing_time": improved_time,
            "success": improved_results.get("success", False),
            "total_pixels": sum(p.get("content_pixels", 0) for p in improved_results.get("pages", [])),
            "max_pixels": max((p.get("content_pixels", 0) for p in improved_results.get("pages", [])), default=0),
            "meets_performance_target": improved_time < 0.5
        }
        
        # Benchmark original custom decoder
        print("   🔧 Benchmarking original custom decoder...")
        start_time = time.time()
        original_results = self._test_original_custom_extraction()
        original_time = time.time() - start_time
        
        benchmarks["original_custom"] = {
            "processing_time": original_time,
            "success": original_results.get("success", False),
            "total_pixels": sum(p.get("content_pixels", 0) for p in original_results.get("pages", [])),
            "max_pixels": max((p.get("content_pixels", 0) for p in original_results.get("pages", [])), default=0),
            "meets_performance_target": original_time < 0.5
        }
        
        self.results["performance_benchmarks"] = benchmarks
        
        # Performance analysis
        print(f"      sn2md: {sn2md_time:.3f}s, {benchmarks['sn2md']['total_pixels']:,} pixels")
        print(f"      Improved: {improved_time:.3f}s, {benchmarks['improved_custom']['total_pixels']:,} pixels")
        print(f"      Original: {original_time:.3f}s, {benchmarks['original_custom']['total_pixels']:,} pixels")
        
        # Calculate improvement factor
        if benchmarks["original_custom"]["total_pixels"] > 0:
            improvement_factor = benchmarks["improved_custom"]["total_pixels"] / benchmarks["original_custom"]["total_pixels"]
            print(f"      🎯 Improvement factor: {improvement_factor:.1f}x")
            benchmarks["improvement_factor"] = improvement_factor
    
    def _assess_quality(self):
        """Assess quality metrics for content extraction"""
        
        quality_metrics = {}
        
        # Extract images for quality analysis
        sn2md_images = self._extract_sn2md_images()
        improved_images = self._extract_improved_custom_images()
        
        if sn2md_images and improved_images:
            for page_idx in range(min(len(sn2md_images), len(improved_images))):
                page_key = f"page_{page_idx + 1}"
                
                sn2md_img = sn2md_images[page_idx]
                improved_img = improved_images[page_idx]
                
                # Quality metrics for this page
                page_metrics = {
                    "content_density": self._calculate_content_density(improved_img, sn2md_img),
                    "edge_quality": self._assess_edge_quality(improved_img),
                    "noise_level": self._assess_noise_level(improved_img),
                    "contrast_ratio": self._calculate_contrast_ratio(improved_img),
                    "spatial_distribution": self._assess_spatial_distribution(improved_img)
                }
                
                quality_metrics[page_key] = page_metrics
        
        self.results["quality_gates"] = quality_metrics
    
    def _pixel_perfect_comparison(self):
        """Perform pixel-perfect comparison framework"""
        
        comparison_results = {}
        
        # Get baseline from sn2md
        try:
            from sn2md.importers.note import load_notebook
            import supernotelib as sn
            from supernotelib.converter import ImageConverter, VisibilityOverlay
            
            notebook = load_notebook(str(self.note_path))
            converter = ImageConverter(notebook)
            
            # Extract baseline images
            vo_invisible = sn.converter.build_visibility_overlay(background=VisibilityOverlay.INVISIBLE)
            
            baseline_images = []
            for page_idx in range(notebook.get_total_pages()):
                img = converter.convert(page_idx, vo_invisible)
                baseline_images.append(np.array(img))
            
            # Get improved custom images
            improved_images = self._extract_improved_custom_images()
            
            if improved_images and baseline_images:
                for page_idx in range(min(len(baseline_images), len(improved_images))):
                    page_key = f"page_{page_idx + 1}"
                    
                    baseline = baseline_images[page_idx]
                    improved = improved_images[page_idx]
                    
                    # Ensure same dimensions
                    if baseline.shape[:2] != improved.shape[:2]:
                        # Resize improved to match baseline
                        improved_pil = Image.fromarray(improved)
                        improved_pil = improved_pil.resize((baseline.shape[1], baseline.shape[0]), Image.Resampling.LANCZOS)
                        improved = np.array(improved_pil)
                    
                    # Convert to grayscale if needed for comparison
                    if len(baseline.shape) == 3:
                        baseline_gray = np.mean(baseline, axis=2).astype(np.uint8)
                    else:
                        baseline_gray = baseline
                    
                    if len(improved.shape) == 3:
                        improved_gray = np.mean(improved, axis=2).astype(np.uint8)
                    else:
                        improved_gray = improved
                    
                    # Pixel-level comparison metrics
                    page_comparison = {
                        "baseline_content_pixels": int(np.sum(baseline_gray < 250)),
                        "improved_content_pixels": int(np.sum(improved_gray < 250)),
                        "pixel_coverage_ratio": float(np.sum(improved_gray < 250) / max(np.sum(baseline_gray < 250), 1)),
                        "spatial_overlap": self._calculate_spatial_overlap(baseline_gray, improved_gray),
                        "content_similarity": self._calculate_content_similarity(baseline_gray, improved_gray)
                    }
                    
                    comparison_results[page_key] = page_comparison
            
        except Exception as e:
            comparison_results["error"] = f"Pixel comparison failed: {str(e)}"
        
        self.results["validation_metrics"]["pixel_comparison"] = comparison_results
    
    def _validate_licensing_compliance(self):
        """Validate commercial licensing compliance"""
        
        compliance = {
            "external_dependencies": [],
            "licensing_risks": [],
            "compliance_status": "compliant"
        }
        
        # Check for problematic dependencies
        try:
            import pkg_resources
            installed_packages = [d.project_name.lower() for d in pkg_resources.working_set]
            
            # Known problematic licenses for commercial use
            gpl_packages = ["supernotelib"]  # Add known GPL packages
            
            for pkg in gpl_packages:
                if pkg in installed_packages:
                    compliance["licensing_risks"].append({
                        "package": pkg,
                        "risk": "GPL/AGPL license may restrict commercial use",
                        "recommendation": "Replace with independent implementation"
                    })
        except ImportError:
            pass
        
        # Check if we're using supernotelib directly in our improved decoder
        improved_decoder_path = project_root / "improved_rle_decoder.py"
        if improved_decoder_path.exists():
            with open(improved_decoder_path, 'r') as f:
                content = f.read()
                if "supernotelib" in content or "sn2md" in content:
                    compliance["licensing_risks"].append({
                        "component": "improved_rle_decoder.py",
                        "risk": "May have dependencies on GPL-licensed code",
                        "recommendation": "Ensure complete independence from external libraries"
                    })
        
        if compliance["licensing_risks"]:
            compliance["compliance_status"] = "at_risk"
        
        self.results["validation_metrics"]["licensing_compliance"] = compliance
    
    def _assess_production_readiness(self):
        """Assess overall production readiness"""
        
        readiness = self.results["production_readiness"]
        score = 0
        max_score = 100
        
        # Performance criteria (25 points)
        perf_benchmarks = self.results.get("performance_benchmarks", {})
        improved_perf = perf_benchmarks.get("improved_custom", {})
        
        if improved_perf.get("meets_performance_target", False):
            score += 15
        elif improved_perf.get("processing_time", 999) < 1.0:
            score += 10
        
        if improved_perf.get("success", False):
            score += 10
        
        # Quality criteria (35 points)
        improved_pixels = improved_perf.get("total_pixels", 0)
        sn2md_pixels = perf_benchmarks.get("sn2md", {}).get("total_pixels", 1)
        
        pixel_ratio = improved_pixels / max(sn2md_pixels, 1)
        
        if pixel_ratio >= 0.8:  # 80% of sn2md pixel count
            score += 25
        elif pixel_ratio >= 0.5:  # 50% of sn2md pixel count
            score += 15
        elif pixel_ratio >= 0.1:  # 10% of sn2md pixel count
            score += 10
        elif pixel_ratio > 0:    # Any content extracted
            score += 5
        
        # Improvement factor (15 points)
        improvement_factor = perf_benchmarks.get("improvement_factor", 0)
        if improvement_factor >= 10:
            score += 15
        elif improvement_factor >= 5:
            score += 10
        elif improvement_factor >= 2:
            score += 5
        
        # Licensing compliance (25 points)
        licensing = self.results.get("validation_metrics", {}).get("licensing_compliance", {})
        if licensing.get("compliance_status") == "compliant":
            score += 25
        elif licensing.get("compliance_status") == "at_risk":
            score += 10
        
        readiness["score"] = score
        
        # Determine status and recommendations
        if score >= 80:
            readiness["status"] = "production_ready"
            readiness["recommendations"].append("Ready for production deployment")
        elif score >= 60:
            readiness["status"] = "almost_ready"
            readiness["recommendations"].append("Minor improvements needed for production")
        elif score >= 40:
            readiness["status"] = "development_stage"
            readiness["recommendations"].append("Significant development work required")
        else:
            readiness["status"] = "not_ready"
            readiness["recommendations"].append("Major architectural changes needed")
        
        # Identify specific blockers
        if pixel_ratio < 0.5:
            readiness["blockers"].append(f"Content extraction gap: {pixel_ratio:.1%} of sn2md baseline")
        
        if not improved_perf.get("meets_performance_target", False):
            readiness["blockers"].append(f"Performance target missed: {improved_perf.get('processing_time', 'unknown')}s > 0.5s")
        
        if licensing.get("compliance_status") != "compliant":
            readiness["blockers"].append("Commercial licensing compliance issues")
        
        print(f"      📊 Production Readiness Score: {score}/{max_score}")
        print(f"      🚦 Status: {readiness['status']}")
        
        if readiness["blockers"]:
            print("      🚫 Blockers:")
            for blocker in readiness["blockers"]:
                print(f"         - {blocker}")
    
    def _test_sn2md_extraction(self) -> Dict[str, Any]:
        """Test sn2md extraction method"""
        
        try:
            from sn2md.importers.note import load_notebook
            import supernotelib as sn
            from supernotelib.converter import ImageConverter, VisibilityOverlay
            
            notebook = load_notebook(str(self.note_path))
            converter = ImageConverter(notebook)
            
            results = {"success": True, "pages": []}
            
            vo = sn.converter.build_visibility_overlay(background=VisibilityOverlay.INVISIBLE)
            
            for page_idx in range(notebook.get_total_pages()):
                img = converter.convert(page_idx, vo)
                arr = np.array(img)
                non_white = np.sum(arr < 250)
                
                results["pages"].append({
                    "page": page_idx + 1,
                    "content_pixels": int(non_white),
                    "image_size": img.size,
                    "has_content": bool(non_white > 1000)
                })
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e), "pages": []}
    
    def _test_improved_custom_extraction(self) -> Dict[str, Any]:
        """Test improved custom extraction method"""
        
        try:
            # Import improved decoder
            sys.path.append(str(project_root))
            from improved_rle_decoder import decode_ratta_rle_improved
            
            with open(self.note_path, 'rb') as f:
                data = f.read()
            
            # Layer positions from analysis
            layers = [
                {"name": "Page1_MainLayer", "pos": 1091, "bitmap_size": 758},
                {"name": "Page2_MainLayer", "pos": 9408, "bitmap_size": 9075}
            ]
            
            results = {"success": True, "pages": []}
            
            for i, layer in enumerate(layers):
                try:
                    # Extract bitmap data
                    start_pos = layer['pos'] + 100  # Skip metadata
                    bitmap_data = data[start_pos:start_pos + layer['bitmap_size']]
                    
                    # Decode with improved algorithm
                    decoded = decode_ratta_rle_improved(bitmap_data, 1404, 1872)
                    content_pixels = int(np.sum(decoded < 255))
                    
                    results["pages"].append({
                        "page": i + 1,
                        "content_pixels": content_pixels,
                        "image_size": (1404, 1872),
                        "has_content": content_pixels > 1000
                    })
                    
                except Exception as e:
                    results["pages"].append({
                        "page": i + 1,
                        "error": str(e),
                        "content_pixels": 0,
                        "has_content": False
                    })
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e), "pages": []}
    
    def _test_original_custom_extraction(self) -> Dict[str, Any]:
        """Test original custom extraction method"""
        
        try:
            from utils.supernote_parser import SupernoteParser
            
            parser = SupernoteParser()
            pages = parser.parse_file(self.note_path)
            
            results = {"success": True, "pages": []}
            
            for i, page in enumerate(pages):
                try:
                    image = parser.render_page_to_image(page)
                    arr = np.array(image)
                    content_pixels = int(np.sum(arr < 250))
                    
                    results["pages"].append({
                        "page": i + 1,
                        "content_pixels": content_pixels,
                        "image_size": image.size,
                        "has_content": content_pixels > 1000
                    })
                    
                except Exception as e:
                    results["pages"].append({
                        "page": i + 1,
                        "error": str(e),
                        "content_pixels": 0,
                        "has_content": False
                    })
            
            return results
            
        except Exception as e:
            return {"success": False, "error": str(e), "pages": []}
    
    def _extract_sn2md_images(self) -> List[np.ndarray]:
        """Extract images using sn2md for comparison"""
        
        try:
            from sn2md.importers.note import load_notebook
            import supernotelib as sn
            from supernotelib.converter import ImageConverter, VisibilityOverlay
            
            notebook = load_notebook(str(self.note_path))
            converter = ImageConverter(notebook)
            vo = sn.converter.build_visibility_overlay(background=VisibilityOverlay.INVISIBLE)
            
            images = []
            for page_idx in range(notebook.get_total_pages()):
                img = converter.convert(page_idx, vo)
                images.append(np.array(img))
            
            return images
            
        except Exception:
            return []
    
    def _extract_improved_custom_images(self) -> List[np.ndarray]:
        """Extract images using improved custom decoder"""
        
        try:
            from improved_rle_decoder import decode_ratta_rle_improved
            
            with open(self.note_path, 'rb') as f:
                data = f.read()
            
            layers = [
                {"name": "Page1_MainLayer", "pos": 1091, "bitmap_size": 758},
                {"name": "Page2_MainLayer", "pos": 9408, "bitmap_size": 9075}
            ]
            
            images = []
            for layer in layers:
                start_pos = layer['pos'] + 100
                bitmap_data = data[start_pos:start_pos + layer['bitmap_size']]
                decoded = decode_ratta_rle_improved(bitmap_data, 1404, 1872)
                images.append(decoded)
            
            return images
            
        except Exception:
            return []
    
    def _calculate_content_density(self, improved_img: np.ndarray, baseline_img: np.ndarray) -> float:
        """Calculate content density ratio"""
        
        improved_content = np.sum(improved_img < 250)
        baseline_content = np.sum(baseline_img < 250)
        
        return float(improved_content / max(baseline_content, 1))
    
    def _assess_edge_quality(self, img: np.ndarray) -> float:
        """Assess edge quality using simple gradient analysis"""
        
        # Simple gradient calculation without scipy
        dx = np.diff(img, axis=1)
        dy = np.diff(img, axis=0)
        
        # Pad to maintain shape
        dx = np.pad(dx, ((0, 0), (0, 1)), mode='edge')
        dy = np.pad(dy, ((0, 1), (0, 0)), mode='edge')
        
        gradient_magnitude = np.sqrt(dx**2 + dy**2)
        
        # Quality score based on edge strength and distribution
        strong_edges = np.sum(gradient_magnitude > 50)
        total_pixels = img.size
        
        return float(strong_edges / total_pixels)
    
    def _assess_noise_level(self, img: np.ndarray) -> float:
        """Assess noise level in the image"""
        
        # Simple noise assessment using standard deviation of differences
        diff_h = np.diff(img, axis=1)
        diff_v = np.diff(img, axis=0)
        
        # Calculate variance of differences as noise estimate
        noise_h = np.var(diff_h)
        noise_v = np.var(diff_v)
        
        return float((noise_h + noise_v) / 2)
    
    def _calculate_contrast_ratio(self, img: np.ndarray) -> float:
        """Calculate contrast ratio"""
        
        if np.max(img) == np.min(img):
            return 0.0
        
        return float((np.max(img) - np.min(img)) / 255.0)
    
    def _assess_spatial_distribution(self, img: np.ndarray) -> Dict[str, float]:
        """Assess spatial distribution of content"""
        
        content_mask = img < 250
        
        if not np.any(content_mask):
            return {"coverage": 0.0, "center_bias": 0.0}
        
        # Coverage assessment
        total_pixels = img.size
        content_pixels = np.sum(content_mask)
        coverage = float(content_pixels / total_pixels)
        
        # Center bias assessment
        h, w = img.shape
        center_region = content_mask[h//4:3*h//4, w//4:3*w//4]
        center_content = np.sum(center_region)
        center_bias = float(center_content / max(content_pixels, 1))
        
        return {"coverage": coverage, "center_bias": center_bias}
    
    def _calculate_spatial_overlap(self, baseline: np.ndarray, improved: np.ndarray) -> float:
        """Calculate spatial overlap between baseline and improved images"""
        
        baseline_mask = baseline < 250
        improved_mask = improved < 250
        
        intersection = np.sum(baseline_mask & improved_mask)
        union = np.sum(baseline_mask | improved_mask)
        
        return float(intersection / max(union, 1))
    
    def _calculate_content_similarity(self, baseline: np.ndarray, improved: np.ndarray) -> float:
        """Calculate content similarity using normalized cross-correlation"""
        
        try:
            baseline_norm = (baseline - np.mean(baseline)) / max(np.std(baseline), 1)
            improved_norm = (improved - np.mean(improved)) / max(np.std(improved), 1)
            
            correlation = np.corrcoef(baseline_norm.flatten(), improved_norm.flatten())[0, 1]
            return float(correlation) if not np.isnan(correlation) else 0.0
            
        except Exception:
            return 0.0
    
    def _generate_validation_report(self) -> Path:
        """Generate comprehensive validation report"""
        
        report_path = project_root / f"production_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return report_path


def main():
    """Run production validation on joe.note"""
    
    note_path = project_root / "joe.note"
    
    if not note_path.exists():
        print(f"❌ Note file not found: {note_path}")
        print("Run get_my_note.py first to download the test file")
        return
    
    # Run comprehensive validation
    validator = ProductionValidationSuite(note_path)
    results = validator.run_comprehensive_validation()
    
    # Summary
    print("\n" + "="*60)
    print("📋 PRODUCTION VALIDATION SUMMARY")
    print("="*60)
    
    readiness = results["production_readiness"]
    print(f"🎯 Overall Score: {readiness['score']}/100")
    print(f"🚦 Status: {readiness['status']}")
    
    if readiness["blockers"]:
        print("\n🚫 Production Blockers:")
        for blocker in readiness["blockers"]:
            print(f"   - {blocker}")
    
    print("\n💡 Recommendations:")
    for rec in readiness["recommendations"]:
        print(f"   - {rec}")
    
    # Performance summary
    perf = results.get("performance_benchmarks", {})
    if perf:
        print("\n⏱️ Performance Summary:")
        for method, metrics in perf.items():
            if isinstance(metrics, dict):
                time_str = f"{metrics.get('processing_time', 0):.3f}s"
                pixels_str = f"{metrics.get('total_pixels', 0):,} pixels"
                print(f"   {method}: {time_str}, {pixels_str}")


if __name__ == "__main__":
    main()