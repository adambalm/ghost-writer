"""
Relationship Detection for Handwritten Note Organization

Detects visual and semantic relationships between ideas in handwritten notes
to help organize scattered thoughts into coherent structures.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between note elements"""
    ARROW = "arrow"              # Visual arrows connecting ideas
    PROXIMITY = "proximity"      # Ideas close together spatially
    HIERARCHY = "hierarchy"      # Indentation/numbering patterns
    SIMILARITY = "similarity"    # Semantic similarity
    SEQUENCE = "sequence"        # Temporal or logical sequence
    GROUPING = "grouping"        # Visual grouping (boxes, circles)
    REFERENCE = "reference"      # Cross-references or citations


@dataclass
class NoteElement:
    """A single element (word, phrase, or concept) in handwritten notes"""
    text: str
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    element_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """A detected relationship between note elements"""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    confidence: float
    evidence: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class RelationshipDetector:
    """Detects relationships between elements in handwritten notes"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.proximity_threshold = self.config.get('proximity_threshold', 50)
        self.arrow_patterns = self._compile_arrow_patterns()
        self.hierarchy_patterns = self._compile_hierarchy_patterns()
        
    def _compile_arrow_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for arrow detection"""
        arrow_symbols = [
            r'→', r'->', r'=>', r'⇒', r'↦',  # Right arrows
            r'←', r'<-', r'<=', r'⇐', r'↤',  # Left arrows  
            r'↑', r'↓', r'⇑', r'⇓',          # Vertical arrows
            r'↗', r'↘', r'↙', r'↖',          # Diagonal arrows
        ]
        
        patterns = []
        for arrow in arrow_symbols:
            patterns.append(re.compile(f'{arrow}'))
            patterns.append(re.compile(f'\\s+{arrow}\\s+'))  # Arrows with spaces
            
        return patterns
    
    def _compile_hierarchy_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for hierarchy detection"""
        return [
            re.compile(r'^\s*(\d+\.)\s+'),           # 1. 2. 3.
            re.compile(r'^\s*([a-zA-Z]\.)\s+'),      # a. b. c.
            re.compile(r'^\s*([ivx]+\.)\s+'),        # i. ii. iii.
            re.compile(r'^\s*([•\-\*])\s+'),         # Bullet points
            re.compile(r'^\s{2,}'),                  # Indentation
        ]
    
    def detect_relationships(self, elements: List[NoteElement]) -> List[Relationship]:
        """Main method to detect all relationships between note elements"""
        relationships = []
        
        # Detect different types of relationships
        relationships.extend(self._detect_arrows(elements))
        relationships.extend(self._detect_proximity(elements))
        relationships.extend(self._detect_hierarchy(elements))
        relationships.extend(self._detect_grouping(elements))
        relationships.extend(self._detect_sequences(elements))
        
        # Remove duplicates and sort by confidence
        relationships = self._deduplicate_relationships(relationships)
        relationships.sort(key=lambda r: r.confidence, reverse=True)
        
        logger.info(f"Detected {len(relationships)} relationships between {len(elements)} elements")
        return relationships
    
    def _detect_arrows(self, elements: List[NoteElement]) -> List[Relationship]:
        """Detect arrow-based relationships between elements"""
        relationships = []
        
        for element in elements:
            for pattern in self.arrow_patterns:
                if pattern.search(element.text):
                    # Find nearby elements that this arrow might connect
                    nearby_elements = self._find_nearby_elements(element, elements, radius=100)
                    
                    for target in nearby_elements:
                        if target.element_id != element.element_id:
                            # Determine arrow direction and create relationship
                            relationship = self._create_arrow_relationship(element, target, pattern)
                            if relationship:
                                relationships.append(relationship)
        
        return relationships
    
    def _detect_proximity(self, elements: List[NoteElement]) -> List[Relationship]:
        """Detect relationships based on spatial proximity"""
        relationships = []
        
        for i, element1 in enumerate(elements):
            for element2 in elements[i+1:]:
                distance = self._calculate_distance(element1.bbox, element2.bbox)
                
                if distance < self.proximity_threshold:
                    confidence = max(0.1, 1.0 - (distance / self.proximity_threshold))
                    
                    relationship = Relationship(
                        source_id=element1.element_id,
                        target_id=element2.element_id,
                        relationship_type=RelationshipType.PROXIMITY,
                        confidence=confidence,
                        evidence={
                            'distance': distance,
                            'threshold': self.proximity_threshold
                        }
                    )
                    relationships.append(relationship)
        
        return relationships
    
    def _detect_hierarchy(self, elements: List[NoteElement]) -> List[Relationship]:
        """Detect hierarchical relationships (indentation, numbering)"""
        relationships = []
        
        # Sort elements by vertical position (top to bottom)
        sorted_elements = sorted(elements, key=lambda e: e.bbox[1])
        
        for i, element in enumerate(sorted_elements):
            hierarchy_level = self._determine_hierarchy_level(element)
            
            if hierarchy_level > 0:
                # Find parent element (previous element with lower hierarchy)
                for j in range(i-1, -1, -1):
                    parent_level = self._determine_hierarchy_level(sorted_elements[j])
                    
                    if parent_level < hierarchy_level:
                        confidence = 0.8 - (0.1 * abs(hierarchy_level - parent_level - 1))
                        
                        relationship = Relationship(
                            source_id=sorted_elements[j].element_id,
                            target_id=element.element_id,
                            relationship_type=RelationshipType.HIERARCHY,
                            confidence=max(0.3, confidence),
                            evidence={
                                'parent_level': parent_level,
                                'child_level': hierarchy_level,
                                'pattern_match': True
                            }
                        )
                        relationships.append(relationship)
                        break
        
        return relationships
    
    def _detect_grouping(self, elements: List[NoteElement]) -> List[Relationship]:
        """Detect visual grouping relationships (boxes, circles, etc.)"""
        relationships = []
        
        # Look for grouping indicators in text
        grouping_patterns = [
            r'\[.*?\]',     # Square brackets
            r'\(.*?\)',     # Parentheses  
            r'\{.*?\}',     # Curly braces
            r'\".*?\"',     # Quotes
        ]
        
        for pattern_str in grouping_patterns:
            pattern = re.compile(pattern_str, re.DOTALL)
            
            for element in elements:
                matches = pattern.finditer(element.text)
                for match in matches:
                    # Find other elements within this grouping
                    grouped_elements = self._find_elements_in_range(
                        elements, element.bbox, match.span()
                    )
                    
                    # Create grouping relationships
                    for target in grouped_elements:
                        if target.element_id != element.element_id:
                            relationship = Relationship(
                                source_id=element.element_id,
                                target_id=target.element_id,
                                relationship_type=RelationshipType.GROUPING,
                                confidence=0.7,
                                evidence={
                                    'pattern': pattern_str,
                                    'match_text': match.group()
                                }
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def _detect_sequences(self, elements: List[NoteElement]) -> List[Relationship]:
        """Detect sequential relationships (temporal, logical flow)"""
        relationships = []
        
        sequence_indicators = [
            r'\bthen\b', r'\bnext\b', r'\bafter\b', r'\bbefore\b',
            r'\bfirst\b', r'\bsecond\b', r'\bthird\b', r'\blast\b',
            r'\bfinally\b', r'\bstep\s+\d+\b'
        ]
        
        for element in elements:
            for indicator in sequence_indicators:
                if re.search(indicator, element.text, re.IGNORECASE):
                    # Find contextually related elements
                    nearby_elements = self._find_nearby_elements(element, elements, radius=150)
                    
                    for target in nearby_elements:
                        if target.element_id != element.element_id:
                            confidence = 0.6 + (0.2 * element.confidence)
                            
                            relationship = Relationship(
                                source_id=element.element_id,
                                target_id=target.element_id,
                                relationship_type=RelationshipType.SEQUENCE,
                                confidence=min(0.9, confidence),
                                evidence={
                                    'sequence_indicator': indicator,
                                    'context_match': True
                                }
                            )
                            relationships.append(relationship)
        
        return relationships
    
    def _create_arrow_relationship(self, source: NoteElement, target: NoteElement, 
                                 pattern: re.Pattern) -> Optional[Relationship]:
        """Create an arrow relationship with proper direction"""
        # Determine arrow direction based on pattern and spatial relationship
        match = pattern.search(source.text)
        if not match:
            return None
        arrow_text = match.group()
        
        # Simple direction detection based on arrow symbols
        if any(symbol in arrow_text for symbol in ['→', '->', '=>', '⇒']):
            # Right-pointing arrow
            if target.bbox[0] > source.bbox[0]:  # Target is to the right
                confidence = 0.8
            else:
                confidence = 0.4  # Arrow points right but target is left
        elif any(symbol in arrow_text for symbol in ['←', '<-', '<=', '⇐']):
            # Left-pointing arrow  
            if target.bbox[0] < source.bbox[0]:  # Target is to the left
                confidence = 0.8
            else:
                confidence = 0.4
        else:
            confidence = 0.6  # Other arrow types
        
        return Relationship(
            source_id=source.element_id,
            target_id=target.element_id,
            relationship_type=RelationshipType.ARROW,
            confidence=confidence,
            evidence={
                'arrow_symbol': arrow_text,
                'spatial_match': confidence > 0.6
            }
        )
    
    def _find_nearby_elements(self, center: NoteElement, elements: List[NoteElement], 
                            radius: int = 100) -> List[NoteElement]:
        """Find elements within radius of center element"""
        nearby = []
        center_x, center_y = center.bbox[0] + center.bbox[2]//2, center.bbox[1] + center.bbox[3]//2
        
        for element in elements:
            if element.element_id == center.element_id:
                continue
                
            elem_x = element.bbox[0] + element.bbox[2]//2
            elem_y = element.bbox[1] + element.bbox[3]//2
            
            distance = np.sqrt((elem_x - center_x)**2 + (elem_y - center_y)**2)
            if distance <= radius:
                nearby.append(element)
        
        return nearby
    
    def _calculate_distance(self, bbox1: Tuple[int, int, int, int], 
                          bbox2: Tuple[int, int, int, int]) -> float:
        """Calculate distance between two bounding boxes"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate center points
        center1_x, center1_y = x1 + w1//2, y1 + h1//2
        center2_x, center2_y = x2 + w2//2, y2 + h2//2
        
        return np.sqrt((center2_x - center1_x)**2 + (center2_y - center1_y)**2)
    
    def _determine_hierarchy_level(self, element: NoteElement) -> int:
        """Determine the hierarchy level of an element (0 = top level)"""
        original_text = element.text
        text = original_text.lstrip()
        
        # Count leading spaces for indentation level
        leading_spaces = len(original_text) - len(text)
        
        # Base indentation level (0-3 based on spaces)
        indent_level = 0
        if leading_spaces >= 8:
            indent_level = 3
        elif leading_spaces >= 4:
            indent_level = 2
        elif leading_spaces >= 2:
            indent_level = 1
        
        # Check for list markers and adjust level
        if re.match(r'^\d+\.', text):  # 1. 2. 3.
            return max(1, indent_level)
        elif re.match(r'^[a-zA-Z]\.', text):  # a. b. c.
            return max(2, indent_level) 
        elif re.match(r'^[ivx]+\.', text):  # i. ii. iii.
            return max(3, indent_level)
        elif re.match(r'^[•\-\*]', text):  # Bullets
            return max(1, indent_level)
        
        # Pure indentation-based level
        return indent_level
    
    def _find_elements_in_range(self, elements: List[NoteElement], 
                              bbox: Tuple[int, int, int, int], 
                              text_range: Tuple[int, int]) -> List[NoteElement]:
        """Find elements that fall within a text range"""
        # This is a simplified implementation
        # In practice, you'd need more sophisticated text-to-spatial mapping
        nearby = self._find_nearby_elements(
            NoteElement("temp", bbox, 1.0, "temp"), elements, radius=50
        )
        return nearby[:3]  # Return up to 3 nearby elements
    
    def _deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Remove duplicate relationships, keeping highest confidence"""
        seen = set()
        deduplicated = []
        
        for rel in sorted(relationships, key=lambda r: r.confidence, reverse=True):
            key = (rel.source_id, rel.target_id, rel.relationship_type.value)
            if key not in seen:
                seen.add(key)
                deduplicated.append(rel)
        
        return deduplicated
    
    def get_relationship_graph(self, relationships: List[Relationship]) -> Dict[str, List[str]]:
        """Convert relationships to a simple adjacency graph"""
        graph: Dict[str, List[str]] = {}
        
        for rel in relationships:
            if rel.source_id not in graph:
                graph[rel.source_id] = []
            graph[rel.source_id].append(rel.target_id)
        
        return graph
    
    def find_clusters(self, elements: List[NoteElement], 
                     relationships: List[Relationship]) -> List[List[str]]:
        """Find clusters of related elements"""
        # Simple clustering based on relationship connections
        clusters = []
        visited: Set[str] = set()
        
        graph = self.get_relationship_graph(relationships)
        
        for element in elements:
            if element.element_id not in visited:
                cluster = self._dfs_cluster(element.element_id, graph, visited)
                if len(cluster) > 1:  # Only keep clusters with multiple elements
                    clusters.append(cluster)
        
        return clusters
    
    def _dfs_cluster(self, node_id: str, graph: Dict[str, List[str]], 
                    visited: Set[str]) -> List[str]:
        """Depth-first search to find connected components"""
        if node_id in visited:
            return []
        
        visited.add(node_id)
        cluster = [node_id]
        
        # Add all connected nodes
        for neighbor in graph.get(node_id, []):
            cluster.extend(self._dfs_cluster(neighbor, graph, visited))
        
        return cluster