"""
Supernote .note file parser

Supernote .note files are binary files containing vector graphics and handwriting data.
This module provides parsing capabilities to extract images and convert them for OCR processing.

Note: This is a reverse-engineered parser based on community research.
The format may change with Supernote firmware updates.
"""

import io
import logging
import struct
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


@dataclass
class SupernoteStroke:
    """Represents a single stroke in a Supernote file"""
    points: List[Tuple[float, float]]
    pressure: List[float]
    timestamp: int
    pen_type: int
    color: int
    thickness: float


@dataclass 
class SupernotePage:
    """Represents a single page in a Supernote file"""
    page_id: int
    width: int
    height: int
    strokes: List[SupernoteStroke]
    background_type: int = 0
    metadata: Dict[str, Any] = None


class SupernoteParser:
    """Parser for Supernote .note files"""
    
    # Known magic bytes and signatures for .note files
    MAGIC_SIGNATURE = b'NOTE'
    VERSION_SIGNATURES = {
        b'v1.0': 1,
        b'v2.0': 2,
        b'v3.0': 3
    }
    
    def __init__(self):
        self.pages: List[SupernotePage] = []
        self.metadata: Dict[str, Any] = {}
        self.version: int = 0
    
    def parse_file(self, file_path: Path) -> List[SupernotePage]:
        """Parse a Supernote .note file and return list of pages"""
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.suffix.lower() == ".note":
            raise ValueError(f"Not a .note file: {file_path}")
        
        logger.info(f"Parsing Supernote file: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Check magic signature
            if not data.startswith(self.MAGIC_SIGNATURE):
                # Try fallback parsing for older formats
                return self._parse_fallback(data)
            
            # Parse header
            self._parse_header(data)
            
            # Parse pages based on version
            if self.version == 3:
                return self._parse_v3_format(data)
            elif self.version == 2:
                return self._parse_v2_format(data)
            else:
                return self._parse_v1_format(data)
                
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            # Try to extract as generic binary format
            return self._parse_fallback(data)
    
    def _parse_header(self, data: bytes):
        """Parse the file header to determine version and metadata"""
        
        offset = len(self.MAGIC_SIGNATURE)
        
        # Look for version signature
        for sig, version in self.VERSION_SIGNATURES.items():
            if data[offset:offset+len(sig)] == sig:
                self.version = version
                offset += len(sig)
                break
        else:
            # Unknown version, assume v1
            self.version = 1
        
        logger.info(f"Detected Supernote format version: v{self.version}")
        
        # Parse basic metadata (this is format-specific)
        try:
            if self.version >= 2:
                # Newer formats have structured metadata
                metadata_length = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4
                
                if metadata_length > 0 and metadata_length < 10000:  # Sanity check
                    metadata_bytes = data[offset:offset+metadata_length]
                    # TODO: Parse structured metadata
                    self.metadata = {"raw_metadata": metadata_bytes}
        except Exception as e:
            logger.warning(f"Could not parse metadata: {e}")
    
    def _parse_v3_format(self, data: bytes) -> List[SupernotePage]:
        """Parse version 3 format (most recent)"""
        logger.info("Parsing v3 format")
        # TODO: Implement v3 parsing based on reverse engineering
        return self._parse_fallback(data)
    
    def _parse_v2_format(self, data: bytes) -> List[SupernotePage]:
        """Parse version 2 format"""
        logger.info("Parsing v2 format")
        # TODO: Implement v2 parsing
        return self._parse_fallback(data)
    
    def _parse_v1_format(self, data: bytes) -> List[SupernotePage]:
        """Parse version 1 format (oldest)"""
        logger.info("Parsing v1 format")
        # TODO: Implement v1 parsing
        return self._parse_fallback(data)
    
    def _parse_fallback(self, data: bytes) -> List[SupernotePage]:
        """Fallback parser that attempts to extract basic structure"""
        logger.warning("Using fallback parser - limited functionality")
        
        # Smart content detection - look for actual meaningful data
        has_content = self._detect_content_in_data(data)
        
        # Create a single page with basic metadata
        page = SupernotePage(
            page_id=0,
            width=1872,  # Standard Supernote A5X dimensions
            height=1404,
            strokes=[],
            metadata={
                "parser": "fallback",
                "file_size": len(data),
                "has_content": has_content
            }
        )
        
        return [page]
    
    def _detect_content_in_data(self, data: bytes) -> bool:
        """
        Smart content detection - looks for actual meaningful data rather than just file size.
        Returns True if the data appears to contain actual note content.
        """
        if len(data) < 16:  # Too small to be a valid note file
            return False
            
        # Check for data beyond just header/magic bytes
        # Look for patterns that suggest actual content:
        
        # 1. Check for sufficient data beyond known headers
        known_headers = [b"SNSV", b"NOTE", b"UNKNOWN_FORMAT"]
        min_content_size = 0
        for header in known_headers:
            if data.startswith(header):
                min_content_size = len(header) + 8  # Header + some metadata
                break
        
        if len(data) <= min_content_size:
            return False
            
        # 2. Look for patterns that suggest stroke data or content
        # Check for non-zero bytes in the data portion (after headers)
        content_portion = data[min_content_size:]
        non_zero_bytes = sum(1 for byte in content_portion if byte != 0)
        
        # If more than 10% of content portion has non-zero bytes, likely has content
        if len(content_portion) > 0 and (non_zero_bytes / len(content_portion)) > 0.1:
            return True
            
        # 3. Check for repeated patterns that might indicate stroke data
        # Simple heuristic: if we see varied byte values, it's likely content
        if len(set(content_portion[:100])) > 10:  # Check first 100 bytes for variety
            return True
            
        # 4. Fallback: if file is reasonably sized and not all zeros/same byte
        if len(data) > 50 and len(set(data)) > 5:
            return True
            
        return False
    
    def render_page_to_image(self, 
                           page: SupernotePage, 
                           output_path: Optional[Path] = None,
                           scale: float = 1.0,
                           background_color: str = "white") -> Image.Image:
        """Render a page to a PIL Image for OCR processing"""
        
        # Create image with page dimensions
        width = int(page.width * scale)
        height = int(page.height * scale)
        
        image = Image.new("RGB", (width, height), background_color)
        draw = ImageDraw.Draw(image)
        
        # Render strokes
        for stroke in page.strokes:
            if len(stroke.points) < 2:
                continue
            
            # Convert stroke points to image coordinates
            stroke_points = [
                (int(x * scale), int(y * scale)) 
                for x, y in stroke.points
            ]
            
            # Draw stroke as connected lines
            for i in range(len(stroke_points) - 1):
                draw.line(
                    [stroke_points[i], stroke_points[i + 1]],
                    fill="black",
                    width=max(1, int(stroke.thickness * scale))
                )
        
        # Save if output path provided
        if output_path:
            image.save(output_path)
            logger.info(f"Rendered page to: {output_path}")
        
        return image
    
    def extract_text_regions(self, page: SupernotePage) -> List[Tuple[int, int, int, int]]:
        """Extract potential text regions from a page (bounding boxes)"""
        
        if not page.strokes:
            return []
        
        # Group strokes into potential text regions
        # This is a simplified implementation
        regions = []
        
        for stroke in page.strokes:
            if not stroke.points:
                continue
            
            # Calculate stroke bounding box
            xs = [p[0] for p in stroke.points]
            ys = [p[1] for p in stroke.points]
            
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            # Add some padding
            padding = 10
            bbox = (
                max(0, int(min_x - padding)),
                max(0, int(min_y - padding)),
                int(max_x + padding),
                int(max_y + padding)
            )
            
            regions.append(bbox)
        
        # Merge overlapping regions
        merged_regions = self._merge_overlapping_boxes(regions)
        
        return merged_regions
    
    def _merge_overlapping_boxes(self, boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """Merge overlapping bounding boxes"""
        
        if not boxes:
            return []
        
        # Simple greedy merging
        merged = []
        
        for box in sorted(boxes):
            x1, y1, x2, y2 = box
            
            # Check if it overlaps with any existing merged box
            merged_with_existing = False
            
            for i, (mx1, my1, mx2, my2) in enumerate(merged):
                # Check overlap
                if (x1 <= mx2 and x2 >= mx1 and y1 <= my2 and y2 >= my1):
                    # Merge boxes
                    merged[i] = (
                        min(x1, mx1),
                        min(y1, my1),
                        max(x2, mx2),
                        max(y2, my2)
                    )
                    merged_with_existing = True
                    break
            
            if not merged_with_existing:
                merged.append(box)
        
        return merged


def convert_note_to_images(note_file: Path, output_dir: Path) -> List[Path]:
    """
    Convert a Supernote .note file to images for OCR processing
    
    Returns list of generated image file paths
    """
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    
    parser = SupernoteParser()
    
    try:
        pages = parser.parse_file(note_file)
        
        if not pages:
            logger.warning(f"No pages found in {note_file}")
            return []
        
        image_paths = []
        
        for i, page in enumerate(pages):
            # Generate output filename
            output_path = output_dir / f"{note_file.stem}_page_{i+1:03d}.png"
            
            # Render page to image
            try:
                image = parser.render_page_to_image(page, output_path, scale=2.0)
                image_paths.append(output_path)
                logger.info(f"Converted page {i+1}/{len(pages)}: {output_path}")
                
            except Exception as e:
                logger.error(f"Failed to render page {i+1}: {e}")
                continue
        
        return image_paths
        
    except Exception as e:
        logger.error(f"Failed to convert {note_file}: {e}")
        return []


def is_supernote_file(file_path: Path) -> bool:
    """Check if a file is a Supernote .note file"""
    
    if file_path.suffix.lower() != ".note":
        return False
    
    try:
        with open(file_path, 'rb') as f:
            # Check first few bytes
            header = f.read(16)
            
            # Look for known signatures
            if header.startswith(SupernoteParser.MAGIC_SIGNATURE):
                return True
            
            # Check for other patterns that might indicate a .note file
            # This is format-specific and may need updates
            return len(header) >= 16 and any(
                sig in header for sig in SupernoteParser.VERSION_SIGNATURES.keys()
            )
            
    except Exception:
        return False