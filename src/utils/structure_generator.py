"""
Structure Generator for Handwritten Note Organization

Transforms clustered concepts and relationships into coherent document structures,
helping users organize scattered thoughts into logical outlines and hierarchies.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from collections import defaultdict
import numpy as np

from .relationship_detector import NoteElement, Relationship, RelationshipType
from .concept_clustering import Concept, ConceptCluster

logger = logging.getLogger(__name__)


class StructureType(Enum):
    """Types of document structures"""
    OUTLINE = "outline"              # Traditional hierarchical outline
    MINDMAP = "mindmap"             # Radial mind map structure
    TIMELINE = "timeline"           # Chronological sequence
    PROCESS = "process"             # Step-by-step process flow
    COMPARISON = "comparison"       # Comparative analysis
    ARGUMENT = "argument"           # Argumentative structure
    NARRATIVE = "narrative"         # Story-like structure


@dataclass
class StructureNode:
    """A node in the generated structure"""
    node_id: str
    content: str
    node_type: str                  # header, subheader, bullet, content
    level: int                      # Hierarchy level (0 = root)
    children: List['StructureNode'] = field(default_factory=list)
    parent_id: Optional[str] = None
    confidence: float = 0.0
    source_elements: List[str] = field(default_factory=list)
    source_concepts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentStructure:
    """A complete document structure"""
    structure_id: str
    structure_type: StructureType
    title: str
    root_nodes: List[StructureNode]
    confidence: float
    completeness_score: float = 0.0
    coherence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class StructureGenerator:
    """Generates document structures from concepts and relationships"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.min_confidence = self.config.get('min_confidence', 0.3)
        self.max_depth = self.config.get('max_depth', 4)
        
    def generate_structures(self, elements: List[NoteElement],
                          concepts: List[Concept],
                          clusters: List[ConceptCluster],
                          relationships: List[Relationship]) -> List[DocumentStructure]:
        """Generate multiple document structures from the input data"""
        
        structures = []
        
        # Try different structure types
        structure_generators = {
            StructureType.OUTLINE: self._generate_outline,
            StructureType.MINDMAP: self._generate_mindmap,
            StructureType.TIMELINE: self._generate_timeline,
            StructureType.PROCESS: self._generate_process,
        }
        
        for structure_type, generator_func in structure_generators.items():
            try:
                structure = generator_func(elements, concepts, clusters, relationships)
                if structure and structure.confidence >= self.min_confidence:
                    structures.append(structure)
            except Exception as e:
                logger.warning(f"Failed to generate {structure_type.value} structure: {e}")
        
        # Sort by confidence and coherence
        structures.sort(key=lambda s: (s.confidence, s.coherence_score), reverse=True)
        
        logger.info(f"Generated {len(structures)} document structures")
        return structures
    
    def _generate_outline(self, elements: List[NoteElement],
                         concepts: List[Concept],
                         clusters: List[ConceptCluster],
                         relationships: List[Relationship]) -> Optional[DocumentStructure]:
        """Generate a traditional hierarchical outline"""
        
        if not clusters:
            return None
        
        # Create main sections from clusters
        root_nodes = []
        
        for cluster in clusters[:5]:  # Limit to top 5 clusters
            # Create section header
            section_node = StructureNode(
                node_id=f"section_{cluster.cluster_id}",
                content=cluster.theme,
                node_type="header",
                level=1,
                confidence=cluster.confidence,
                source_concepts=[c.concept_id for c in cluster.concepts]
            )
            
            # Add subsections from concepts
            for concept in cluster.concepts:
                if concept.confidence >= 0.4:  # Only high-confidence concepts
                    subsection = self._create_concept_node(concept, level=2)
                    section_node.children.append(subsection)
                    subsection.parent_id = section_node.node_id
            
            # Add supporting content from relationships
            self._add_relationship_content(section_node, relationships, elements)
            
            root_nodes.append(section_node)
        
        # Generate title
        title = self._generate_document_title(clusters, concepts)
        
        # Calculate scores
        confidence = np.mean([node.confidence for node in root_nodes]) if root_nodes else 0.0
        coherence_score = self._calculate_coherence_score(root_nodes, relationships)
        completeness_score = self._calculate_completeness_score(root_nodes, elements)
        
        return DocumentStructure(
            structure_id="outline_001",
            structure_type=StructureType.OUTLINE,
            title=title,
            root_nodes=root_nodes,
            confidence=confidence,
            coherence_score=coherence_score,
            completeness_score=completeness_score,
            metadata={
                'cluster_count': len(clusters),
                'total_nodes': sum(1 + len(node.children) for node in root_nodes)
            }
        )
    
    def _generate_mindmap(self, elements: List[NoteElement],
                         concepts: List[Concept],
                         clusters: List[ConceptCluster],
                         relationships: List[Relationship]) -> Optional[DocumentStructure]:
        """Generate a radial mind map structure"""
        
        if not clusters:
            return None
        
        # Find central theme/cluster
        central_cluster = max(clusters, key=lambda c: c.confidence * c.size)
        
        # Create central node
        central_node = StructureNode(
            node_id="mindmap_center",
            content=central_cluster.theme,
            node_type="center",
            level=0,
            confidence=central_cluster.confidence,
            source_concepts=[c.concept_id for c in central_cluster.concepts]
        )
        
        # Create branches for other clusters and strong relationships
        for cluster in clusters:
            if cluster.cluster_id != central_cluster.cluster_id:
                branch_node = StructureNode(
                    node_id=f"branch_{cluster.cluster_id}",
                    content=cluster.theme,
                    node_type="branch",
                    level=1,
                    confidence=cluster.confidence,
                    source_concepts=[c.concept_id for c in cluster.concepts],
                    parent_id=central_node.node_id
                )
                
                # Add sub-branches for concepts
                for concept in cluster.concepts[:3]:  # Limit sub-branches
                    sub_branch = self._create_concept_node(concept, level=2)
                    sub_branch.parent_id = branch_node.node_id
                    branch_node.children.append(sub_branch)
                
                central_node.children.append(branch_node)
        
        title = f"Mind Map: {central_cluster.theme}"
        confidence = central_cluster.confidence
        coherence_score = self._calculate_coherence_score([central_node], relationships)
        
        return DocumentStructure(
            structure_id="mindmap_001",
            structure_type=StructureType.MINDMAP,
            title=title,
            root_nodes=[central_node],
            confidence=confidence,
            coherence_score=coherence_score,
            completeness_score=0.8,  # Mind maps are naturally selective
            metadata={
                'central_theme': central_cluster.theme,
                'branch_count': len(central_node.children)
            }
        )
    
    def _generate_timeline(self, elements: List[NoteElement],
                          concepts: List[Concept],
                          clusters: List[ConceptCluster],
                          relationships: List[Relationship]) -> Optional[DocumentStructure]:
        """Generate a chronological timeline structure"""
        
        # Look for temporal indicators and sequence relationships
        sequential_rels = [r for r in relationships 
                          if r.relationship_type == RelationshipType.SEQUENCE]
        
        if not sequential_rels:
            return None
        
        # Build timeline from sequential relationships
        timeline_nodes = []
        processed_elements = set()
        
        # Sort relationships by confidence
        sequential_rels.sort(key=lambda r: r.confidence, reverse=True)
        
        step_counter = 1
        for rel in sequential_rels:
            if rel.source_id not in processed_elements:
                source_element = self._find_element_by_id(elements, rel.source_id)
                if source_element:
                    timeline_node = StructureNode(
                        node_id=f"timeline_step_{step_counter}",
                        content=f"Step {step_counter}: {source_element.text}",
                        node_type="timeline_item",
                        level=1,
                        confidence=rel.confidence,
                        source_elements=[rel.source_id]
                    )
                    timeline_nodes.append(timeline_node)
                    processed_elements.add(rel.source_id)
                    step_counter += 1
        
        if not timeline_nodes:
            return None
        
        title = "Timeline: Process Flow"
        confidence = np.mean([node.confidence for node in timeline_nodes])
        
        return DocumentStructure(
            structure_id="timeline_001",
            structure_type=StructureType.TIMELINE,
            title=title,
            root_nodes=timeline_nodes,
            confidence=confidence,
            coherence_score=0.7,  # Timelines are inherently coherent
            completeness_score=min(1.0, len(timeline_nodes) / 5),  # Based on step count
            metadata={
                'step_count': len(timeline_nodes),
                'sequence_relationships': len(sequential_rels)
            }
        )
    
    def _generate_process(self, elements: List[NoteElement],
                         concepts: List[Concept],
                         clusters: List[ConceptCluster],
                         relationships: List[Relationship]) -> Optional[DocumentStructure]:
        """Generate a process/workflow structure"""
        
        # Look for action-oriented concepts and hierarchical relationships
        action_concepts = [c for c in concepts if c.concept_type == "action"]
        
        if not action_concepts:
            return None
        
        # Group actions by cluster
        clustered_actions = defaultdict(list)
        for concept in action_concepts:
            # Find which cluster this concept belongs to
            for cluster in clusters:
                if any(cc.concept_id == concept.concept_id for cc in cluster.concepts):
                    clustered_actions[cluster.cluster_id].append(concept)
                    break
        
        # Create process sections
        root_nodes = []
        
        for cluster_id, actions in clustered_actions.items():
            cluster = next(c for c in clusters if c.cluster_id == cluster_id)
            
            process_section = StructureNode(
                node_id=f"process_{cluster_id}",
                content=f"Process: {cluster.theme}",
                node_type="process_header",
                level=1,
                confidence=cluster.confidence,
                source_concepts=[a.concept_id for a in actions]
            )
            
            # Add action items
            for i, action in enumerate(actions, 1):
                action_node = StructureNode(
                    node_id=f"action_{action.concept_id}",
                    content=f"{i}. {' '.join(action.keywords)}",
                    node_type="action_item",
                    level=2,
                    confidence=action.confidence,
                    source_concepts=[action.concept_id],
                    parent_id=process_section.node_id
                )
                process_section.children.append(action_node)
            
            root_nodes.append(process_section)
        
        title = "Process Documentation"
        confidence = np.mean([node.confidence for node in root_nodes]) if root_nodes else 0.0
        
        return DocumentStructure(
            structure_id="process_001",
            structure_type=StructureType.PROCESS,
            title=title,
            root_nodes=root_nodes,
            confidence=confidence,
            coherence_score=0.8,  # Processes are usually coherent
            completeness_score=min(1.0, len(action_concepts) / 8),  # Based on action count
            metadata={
                'action_count': len(action_concepts),
                'process_sections': len(root_nodes)
            }
        )
    
    def _create_concept_node(self, concept: Concept, level: int = 1) -> StructureNode:
        """Create a structure node from a concept"""
        content = ' '.join(concept.keywords) if concept.keywords else f"Concept {concept.concept_id}"
        
        return StructureNode(
            node_id=f"concept_{concept.concept_id}",
            content=content,
            node_type="concept",
            level=level,
            confidence=concept.confidence,
            source_concepts=[concept.concept_id],
            source_elements=concept.elements
        )
    
    def _add_relationship_content(self, node: StructureNode, 
                                relationships: List[Relationship],
                                elements: List[NoteElement]):
        """Add content to a node based on relationships"""
        # Find relationships involving this node's source elements
        relevant_rels = []
        node_elements = set(node.source_elements)
        
        for rel in relationships:
            if rel.source_id in node_elements or rel.target_id in node_elements:
                relevant_rels.append(rel)
        
        # Add high-confidence relationship content as sub-items
        for rel in relevant_rels[:3]:  # Limit to top 3
            if rel.confidence >= 0.6:
                target_element = self._find_element_by_id(elements, rel.target_id)
                if target_element and target_element.element_id not in node_elements:
                    sub_node = StructureNode(
                        node_id=f"rel_{rel.source_id}_{rel.target_id}",
                        content=target_element.text[:100] + "..." if len(target_element.text) > 100 
                                else target_element.text,
                        node_type="supporting",
                        level=node.level + 1,
                        confidence=rel.confidence,
                        source_elements=[target_element.element_id],
                        parent_id=node.node_id
                    )
                    node.children.append(sub_node)
    
    def _find_element_by_id(self, elements: List[NoteElement], element_id: str) -> Optional[NoteElement]:
        """Find an element by its ID"""
        for element in elements:
            if element.element_id == element_id:
                return element
        return None
    
    def _generate_document_title(self, clusters: List[ConceptCluster], 
                               concepts: List[Concept]) -> str:
        """Generate a title for the document"""
        if not clusters:
            return "Document Structure"
        
        # Use the most confident cluster's theme
        main_cluster = max(clusters, key=lambda c: c.confidence)
        
        # Check for title-like concepts
        title_concepts = [c for c in concepts if c.concept_type == "topic" and c.confidence > 0.7]
        
        if title_concepts:
            title_concept = max(title_concepts, key=lambda c: c.confidence)
            return ' '.join(title_concept.keywords)
        else:
            return main_cluster.theme
    
    def _calculate_coherence_score(self, nodes: List[StructureNode], 
                                 relationships: List[Relationship]) -> float:
        """Calculate how coherent the structure is"""
        if not nodes:
            return 0.0
        
        # Count internal connections vs total possible connections
        node_elements = set()
        for node in nodes:
            node_elements.update(node.source_elements)
        
        internal_connections = 0
        total_relationships = 0
        
        for rel in relationships:
            if rel.source_id in node_elements or rel.target_id in node_elements:
                total_relationships += 1
                if rel.source_id in node_elements and rel.target_id in node_elements:
                    internal_connections += 1
        
        if total_relationships == 0:
            return 0.5  # Neutral score when no relationships
        
        return internal_connections / total_relationships
    
    def _calculate_completeness_score(self, nodes: List[StructureNode], 
                                    elements: List[NoteElement]) -> float:
        """Calculate how much of the original content is covered"""
        if not elements:
            return 1.0
        
        covered_elements = set()
        for node in nodes:
            covered_elements.update(node.source_elements)
            for child in node.children:
                covered_elements.update(child.source_elements)
        
        total_elements = {elem.element_id for elem in elements}
        coverage = len(covered_elements) / len(total_elements)
        
        return min(1.0, coverage)
    
    def export_structure_as_text(self, structure: DocumentStructure) -> str:
        """Export structure as formatted text"""
        lines = [f"# {structure.title}\n"]
        
        for node in structure.root_nodes:
            lines.extend(self._format_node_as_text(node, prefix=""))
        
        lines.append("\n---")
        lines.append(f"Structure Type: {structure.structure_type.value}")
        lines.append(f"Confidence: {structure.confidence:.2f}")
        lines.append(f"Coherence: {structure.coherence_score:.2f}")
        lines.append(f"Completeness: {structure.completeness_score:.2f}")
        
        return "\n".join(lines)
    
    def _format_node_as_text(self, node: StructureNode, prefix: str = "") -> List[str]:
        """Format a node and its children as text"""
        lines = []
        
        # Format based on node type and level
        if node.node_type == "header":
            indent = "#" * (node.level + 1)
            lines.append(f"{prefix}{indent} {node.content}")
        elif node.node_type == "center":
            lines.append(f"{prefix}**{node.content}** (Central Theme)")
        elif node.node_type == "branch":
            lines.append(f"{prefix}- **{node.content}**")
        elif node.node_type == "timeline_item":
            lines.append(f"{prefix}{node.content}")
        else:
            bullet = "  " * (node.level - 1) + "- " if node.level > 1 else "- "
            lines.append(f"{prefix}{bullet}{node.content}")
        
        # Add children with increased indentation
        child_prefix = prefix + ("  " if node.node_type in ["branch", "header"] else "    ")
        for child in node.children:
            lines.extend(self._format_node_as_text(child, child_prefix))
        
        return lines
    
    def get_structure_summary(self, structure: DocumentStructure) -> Dict[str, Any]:
        """Get a summary of the structure"""
        def count_nodes(nodes):
            count = len(nodes)
            for node in nodes:
                count += count_nodes(node.children)
            return count
        
        total_nodes = count_nodes(structure.root_nodes)
        
        return {
            'structure_id': structure.structure_id,
            'type': structure.structure_type.value,
            'title': structure.title,
            'confidence': structure.confidence,
            'coherence_score': structure.coherence_score,
            'completeness_score': structure.completeness_score,
            'total_nodes': total_nodes,
            'root_sections': len(structure.root_nodes),
            'metadata': structure.metadata
        }