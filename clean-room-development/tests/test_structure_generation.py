"""
Tests for Structure Generation from Organized Concepts

Tests the final stage of idea organization: transforming clustered concepts
and relationships into coherent document structures like outlines, mind maps,
timelines, and process flows.
"""

import pytest
from unittest.mock import MagicMock
import re

from src.utils.structure_generator import (
    StructureGenerator, StructureNode, DocumentStructure, StructureType
)
from src.utils.relationship_detector import NoteElement, Relationship, RelationshipType
from src.utils.concept_clustering import Concept, ConceptCluster


class TestStructureGenerator:
    """Test document structure generation"""
    
    def test_outline_structure_generation(self):
        """Test generation of hierarchical outline structure"""
        
        generator = StructureGenerator({'min_confidence': 0.3})
        
        # Create sample clusters representing different topics
        clusters = [
            ConceptCluster(
                cluster_id="ml_cluster",
                concepts=[
                    Concept("ml_1", ["machine", "learning"], ["elem1", "elem2"], 0.9, "topic"),
                    Concept("nn_1", ["neural", "networks"], ["elem3"], 0.85, "topic")
                ],
                theme="Machine Learning",
                confidence=0.87,
                size=2
            ),
            ConceptCluster(
                cluster_id="data_cluster", 
                concepts=[
                    Concept("data_1", ["data", "collection"], ["elem4"], 0.82, "action"),
                    Concept("clean_1", ["clean", "dataset"], ["elem5"], 0.88, "action")
                ],
                theme="Data Processing",
                confidence=0.85,
                size=2
            )
        ]
        
        # Create supporting elements and concepts
        elements = [
            NoteElement("Machine learning algorithms", (10, 20, 150, 15), 0.9, "elem1"),
            NoteElement("Neural networks basics", (10, 40, 140, 15), 0.85, "elem2"),
            NoteElement("Deep neural architectures", (10, 60, 160, 15), 0.88, "elem3"),
            NoteElement("Collect training data", (10, 100, 130, 15), 0.82, "elem4"),
            NoteElement("Clean and preprocess", (10, 120, 140, 15), 0.88, "elem5")
        ]
        
        concepts = []
        for cluster in clusters:
            concepts.extend(cluster.concepts)
        
        relationships = [
            Relationship("elem1", "elem2", RelationshipType.HIERARCHY, 0.8),
            Relationship("elem2", "elem3", RelationshipType.SEQUENCE, 0.7),
            Relationship("elem4", "elem5", RelationshipType.SEQUENCE, 0.75)
        ]
        
        structures = generator.generate_structures(elements, concepts, clusters, relationships)
        
        # Should generate at least one structure
        assert len(structures) > 0
        
        # Should include an outline structure
        outline_structures = [s for s in structures if s.structure_type == StructureType.OUTLINE]
        assert len(outline_structures) > 0
        
        outline = outline_structures[0]
        
        # Should have reasonable confidence
        assert outline.confidence > 0.3
        
        # Should have hierarchical nodes
        assert len(outline.root_nodes) >= 2  # At least 2 main sections
        
        # Verify structure hierarchy
        for root_node in outline.root_nodes:
            assert root_node.level == 1  # Root level
            assert root_node.node_type in ["header", "section"]
            assert len(root_node.content) > 0
            
            # Check for child nodes
            if root_node.children:
                for child in root_node.children:
                    assert child.level > root_node.level
                    assert child.parent_id == root_node.node_id
    
    def test_mindmap_structure_generation(self):
        """Test generation of radial mind map structure"""
        
        generator = StructureGenerator()
        
        # Create a dominant central cluster
        central_cluster = ConceptCluster(
            cluster_id="ai_cluster",
            concepts=[
                Concept("ai_1", ["artificial", "intelligence"], ["elem1"], 0.95, "topic"),
                Concept("ai_2", ["ai", "applications"], ["elem2"], 0.9, "topic")
            ],
            theme="Artificial Intelligence",
            confidence=0.92,
            size=2
        )
        
        # Create related branch clusters
        branch_clusters = [
            ConceptCluster(
                cluster_id="ml_branch",
                concepts=[Concept("ml_1", ["machine", "learning"], ["elem3"], 0.85, "topic")],
                theme="Machine Learning",
                confidence=0.85,
                size=1
            ),
            ConceptCluster(
                cluster_id="vision_branch", 
                concepts=[Concept("cv_1", ["computer", "vision"], ["elem4"], 0.88, "topic")],
                theme="Computer Vision",
                confidence=0.88,
                size=1
            )
        ]
        
        all_clusters = [central_cluster] + branch_clusters
        
        elements = [
            NoteElement("Artificial Intelligence overview", (10, 20, 160, 15), 0.95, "elem1"),
            NoteElement("AI applications in industry", (10, 40, 150, 15), 0.9, "elem2"),
            NoteElement("Machine learning techniques", (100, 20, 140, 15), 0.85, "elem3"),
            NoteElement("Computer vision systems", (100, 60, 130, 15), 0.88, "elem4")
        ]
        
        concepts = []
        for cluster in all_clusters:
            concepts.extend(cluster.concepts)
        
        relationships = [
            Relationship("elem1", "elem3", RelationshipType.SIMILARITY, 0.8),
            Relationship("elem1", "elem4", RelationshipType.SIMILARITY, 0.75)
        ]
        
        structures = generator.generate_structures(elements, concepts, all_clusters, relationships)
        
        # Should include a mind map structure
        mindmap_structures = [s for s in structures if s.structure_type == StructureType.MINDMAP]
        assert len(mindmap_structures) > 0
        
        mindmap = mindmap_structures[0]
        
        # Should have one central node
        assert len(mindmap.root_nodes) == 1
        central_node = mindmap.root_nodes[0]
        
        assert central_node.node_type == "center"
        assert central_node.level == 0
        assert "intelligence" in central_node.content.lower() or "ai" in central_node.content.lower()
        
        # Should have branch nodes
        assert len(central_node.children) >= 2
        
        for branch in central_node.children:
            assert branch.node_type == "branch"
            assert branch.level == 1
            assert branch.parent_id == central_node.node_id
    
    def test_timeline_structure_generation(self):
        """Test generation of chronological timeline structure"""
        
        generator = StructureGenerator()
        
        # Create elements with sequence indicators
        elements = [
            NoteElement("First, analyze requirements", (10, 20, 150, 15), 0.9, "step1"),
            NoteElement("Then, design the system", (10, 40, 140, 15), 0.85, "step2"),
            NoteElement("Next, implement components", (10, 60, 160, 15), 0.88, "step3"),
            NoteElement("Finally, test and deploy", (10, 80, 150, 15), 0.82, "step4"),
            NoteElement("Step 1: Data collection", (200, 20, 130, 15), 0.87, "data_step")
        ]
        
        concepts = [
            Concept("seq_1", ["analyze", "requirements"], ["step1"], 0.9, "action"),
            Concept("seq_2", ["design", "system"], ["step2"], 0.85, "action"),
            Concept("seq_3", ["implement", "components"], ["step3"], 0.88, "action"),
            Concept("seq_4", ["test", "deploy"], ["step4"], 0.82, "action"),
            Concept("data_1", ["data", "collection"], ["data_step"], 0.87, "action")
        ]
        
        # Create sequential relationships
        relationships = [
            Relationship("step1", "step2", RelationshipType.SEQUENCE, 0.9),
            Relationship("step2", "step3", RelationshipType.SEQUENCE, 0.85),
            Relationship("step3", "step4", RelationshipType.SEQUENCE, 0.8),
            Relationship("data_step", "step1", RelationshipType.SEQUENCE, 0.75)
        ]
        
        clusters = [
            ConceptCluster("process", concepts, "Development Process", 0.85, len(concepts))
        ]
        
        structures = generator.generate_structures(elements, concepts, clusters, relationships)
        
        # Should include timeline structure
        timeline_structures = [s for s in structures if s.structure_type == StructureType.TIMELINE]
        assert len(timeline_structures) > 0
        
        timeline = timeline_structures[0]
        
        # Should have sequential steps
        assert len(timeline.root_nodes) >= 3  # At least a few steps
        
        # Verify timeline structure
        for i, node in enumerate(timeline.root_nodes):
            assert node.node_type == "timeline_item"
            assert node.level == 1
            assert "step" in node.content.lower() or any(word in node.content.lower() 
                                                        for word in ["first", "then", "next", "finally"])
    
    def test_process_structure_generation(self):
        """Test generation of process/workflow structure"""
        
        generator = StructureGenerator()
        
        # Create action-oriented concepts
        action_concepts = [
            Concept("act_1", ["implement", "database"], ["elem1"], 0.9, "action"),
            Concept("act_2", ["create", "tests"], ["elem2"], 0.85, "action"),
            Concept("act_3", ["review", "code"], ["elem3"], 0.88, "action"),
            Concept("act_4", ["deploy", "system"], ["elem4"], 0.82, "action")
        ]
        
        # Group into action clusters
        clusters = [
            ConceptCluster(
                cluster_id="dev_actions",
                concepts=[action_concepts[0], action_concepts[1]],
                theme="Development Tasks",
                confidence=0.87,
                size=2
            ),
            ConceptCluster(
                cluster_id="qa_actions",
                concepts=[action_concepts[2], action_concepts[3]], 
                theme="Quality Assurance",
                confidence=0.85,
                size=2
            )
        ]
        
        elements = [
            NoteElement("Need to implement database", (10, 20, 140, 15), 0.9, "elem1"),
            NoteElement("Must create test cases", (10, 40, 130, 15), 0.85, "elem2"),
            NoteElement("Should review the code", (10, 60, 135, 15), 0.88, "elem3"),
            NoteElement("Deploy to production", (10, 80, 125, 15), 0.82, "elem4")
        ]
        
        relationships = [
            Relationship("elem1", "elem2", RelationshipType.SEQUENCE, 0.8),
            Relationship("elem2", "elem3", RelationshipType.SEQUENCE, 0.75)
        ]
        
        structures = generator.generate_structures(elements, action_concepts, clusters, relationships)
        
        # Should include process structure
        process_structures = [s for s in structures if s.structure_type == StructureType.PROCESS]
        assert len(process_structures) > 0
        
        process = process_structures[0]
        
        # Should have process sections
        assert len(process.root_nodes) >= 1
        
        # Verify process structure
        for section in process.root_nodes:
            assert section.node_type == "process_header"
            assert "process" in section.content.lower() or "task" in section.content.lower()
            
            # Should have action items as children
            if section.children:
                for action_item in section.children:
                    assert action_item.node_type == "action_item"
                    assert action_item.level == 2
                    assert action_item.parent_id == section.node_id
    
    def test_structure_quality_scoring(self):
        """Test confidence and quality scoring of generated structures"""
        
        generator = StructureGenerator({'min_confidence': 0.4})
        
        # Create high-quality interconnected content
        high_quality_elements = [
            NoteElement("Main research topic", (10, 20, 120, 15), 0.95, "main"),
            NoteElement("Subtopic A details", (20, 40, 110, 15), 0.9, "sub_a"),
            NoteElement("Subtopic B details", (20, 60, 110, 15), 0.92, "sub_b"),
            NoteElement("Supporting evidence", (30, 80, 120, 15), 0.88, "support")
        ]
        
        high_quality_concepts = [
            Concept("main_1", ["research", "topic"], ["main"], 0.95, "topic"),
            Concept("sub_a1", ["subtopic", "details"], ["sub_a"], 0.9, "topic"),
            Concept("sub_b1", ["subtopic", "analysis"], ["sub_b"], 0.92, "topic")
        ]
        
        high_quality_clusters = [
            ConceptCluster("research", high_quality_concepts, "Research Analysis", 0.92, 3)
        ]
        
        strong_relationships = [
            Relationship("main", "sub_a", RelationshipType.HIERARCHY, 0.9),
            Relationship("main", "sub_b", RelationshipType.HIERARCHY, 0.85),
            Relationship("sub_a", "support", RelationshipType.ARROW, 0.8)
        ]
        
        structures = generator.generate_structures(
            high_quality_elements, high_quality_concepts, high_quality_clusters, strong_relationships
        )
        
        # Should generate high-quality structures
        assert len(structures) > 0
        
        # Check structure quality metrics
        for structure in structures:
            assert structure.confidence >= generator.min_confidence
            assert structure.coherence_score >= 0.0
            assert structure.completeness_score >= 0.0
            
            # High-quality input should produce reasonable scores
            if structure.confidence > 0.7:
                assert structure.coherence_score > 0.3
                assert structure.completeness_score > 0.3
    
    def test_structure_text_export(self):
        """Test export of structures as formatted text"""
        
        generator = StructureGenerator()
        
        # Create simple structure for testing
        root_node = StructureNode(
            node_id="root",
            content="Main Topic",
            node_type="header", 
            level=1,
            confidence=0.8
        )
        
        child_node = StructureNode(
            node_id="child1",
            content="Subtopic Details",
            node_type="subheader",
            level=2,
            parent_id="root",
            confidence=0.75
        )
        
        root_node.children = [child_node]
        
        structure = DocumentStructure(
            structure_id="test_structure",
            structure_type=StructureType.OUTLINE,
            title="Test Document",
            root_nodes=[root_node],
            confidence=0.8,
            coherence_score=0.7,
            completeness_score=0.6
        )
        
        # Export as text
        text_output = generator.export_structure_as_text(structure)
        
        # Should contain expected elements
        assert "# Test Document" in text_output  # Title
        assert "## Main Topic" in text_output    # Main header
        assert "Subtopic Details" in text_output  # Child content
        assert "Confidence: 0.80" in text_output  # Metrics
        assert "Coherence: 0.70" in text_output
        assert "Completeness: 0.60" in text_output
        
        # Should be well-formatted
        lines = text_output.split('\n')
        assert len(lines) > 5  # Should have multiple lines
        assert any(line.startswith('#') for line in lines)  # Headers
    
    def test_structure_summary_generation(self):
        """Test generation of structure summaries"""
        
        generator = StructureGenerator()
        
        # Create structure with nested content
        nodes = [
            StructureNode("node1", "Topic A", "header", 1, confidence=0.8),
            StructureNode("node2", "Topic B", "header", 1, confidence=0.75)
        ]
        
        # Add children to first node
        nodes[0].children = [
            StructureNode("child1", "Subtopic A1", "subheader", 2, parent_id="node1", confidence=0.7),
            StructureNode("child2", "Subtopic A2", "subheader", 2, parent_id="node1", confidence=0.72)
        ]
        
        structure = DocumentStructure(
            structure_id="summary_test",
            structure_type=StructureType.OUTLINE,
            title="Summary Test Document", 
            root_nodes=nodes,
            confidence=0.77,
            coherence_score=0.65,
            completeness_score=0.8
        )
        
        summary = generator.get_structure_summary(structure)
        
        # Verify summary structure
        assert summary['structure_id'] == "summary_test"
        assert summary['type'] == "outline"
        assert summary['title'] == "Summary Test Document"
        assert summary['confidence'] == 0.77
        assert summary['coherence_score'] == 0.65
        assert summary['completeness_score'] == 0.8
        assert summary['total_nodes'] == 4  # 2 root + 2 children
        assert summary['root_sections'] == 2


class TestStructureComparison:
    """Test comparison and ranking of different structure types"""
    
    def test_structure_type_selection(self):
        """Test that appropriate structure types are selected for different content"""
        
        generator = StructureGenerator()
        
        # Content with strong sequential indicators
        sequential_elements = [
            NoteElement("Step 1: Initialize", (10, 20, 100, 15), 0.9, "seq1"),
            NoteElement("Step 2: Process", (10, 40, 90, 15), 0.85, "seq2"),
            NoteElement("Step 3: Finalize", (10, 60, 95, 15), 0.88, "seq3")
        ]
        
        sequential_concepts = [
            Concept("s1", ["initialize"], ["seq1"], 0.9, "action"),
            Concept("s2", ["process"], ["seq2"], 0.85, "action"),
            Concept("s3", ["finalize"], ["seq3"], 0.88, "action")
        ]
        
        sequential_relationships = [
            Relationship("seq1", "seq2", RelationshipType.SEQUENCE, 0.9),
            Relationship("seq2", "seq3", RelationshipType.SEQUENCE, 0.85)
        ]
        
        clusters = [ConceptCluster("proc", sequential_concepts, "Process Steps", 0.88, 3)]
        
        structures = generator.generate_structures(
            sequential_elements, sequential_concepts, clusters, sequential_relationships
        )
        
        # Should generate timeline/process structures for sequential content
        structure_types = {s.structure_type for s in structures}
        assert StructureType.TIMELINE in structure_types or StructureType.PROCESS in structure_types
        
        # Sequential structures should have high confidence for this content type
        sequential_structures = [s for s in structures 
                               if s.structure_type in [StructureType.TIMELINE, StructureType.PROCESS]]
        
        if sequential_structures:
            best_sequential = max(sequential_structures, key=lambda s: s.confidence)
            assert best_sequential.confidence > 0.6
    
    def test_structure_ranking(self):
        """Test that structures are ranked by quality and appropriateness"""
        
        generator = StructureGenerator({'min_confidence': 0.2})
        
        # Mixed content that could support multiple structure types
        mixed_elements = [
            NoteElement("Central AI concept", (50, 50, 100, 15), 0.95, "center"),
            NoteElement("First, collect data", (10, 20, 90, 15), 0.8, "step1"),
            NoteElement("Machine learning branch", (100, 30, 120, 15), 0.85, "ml"),
            NoteElement("Then, train models", (10, 40, 95, 15), 0.82, "step2"),
            NoteElement("Neural networks branch", (100, 70, 125, 15), 0.88, "nn")
        ]
        
        mixed_concepts = [
            Concept("ai", ["artificial", "intelligence"], ["center"], 0.95, "topic"),
            Concept("data", ["collect", "data"], ["step1"], 0.8, "action"), 
            Concept("ml", ["machine", "learning"], ["ml"], 0.85, "topic"),
            Concept("train", ["train", "models"], ["step2"], 0.82, "action"),
            Concept("nn", ["neural", "networks"], ["nn"], 0.88, "topic")
        ]
        
        mixed_clusters = [
            ConceptCluster("ai_main", [mixed_concepts[0], mixed_concepts[2], mixed_concepts[4]], "AI Topics", 0.9, 3),
            ConceptCluster("actions", [mixed_concepts[1], mixed_concepts[3]], "Action Items", 0.81, 2)
        ]
        
        mixed_relationships = [
            Relationship("center", "ml", RelationshipType.SIMILARITY, 0.8),
            Relationship("center", "nn", RelationshipType.SIMILARITY, 0.75),
            Relationship("step1", "step2", RelationshipType.SEQUENCE, 0.7)
        ]
        
        structures = generator.generate_structures(
            mixed_elements, mixed_concepts, mixed_clusters, mixed_relationships
        )
        
        # Should generate multiple structure types
        assert len(structures) >= 2
        
        # Should be ranked by confidence (highest first)
        confidences = [s.confidence for s in structures]
        assert confidences == sorted(confidences, reverse=True)
        
        # Best structure should have reasonable quality scores
        best_structure = structures[0]
        assert best_structure.confidence > 0.3
        assert best_structure.coherence_score >= 0.0
        assert best_structure.completeness_score >= 0.0


class TestStructureEdgeCases:
    """Test structure generation edge cases and error handling"""
    
    def test_empty_input_handling(self):
        """Test structure generation with empty or minimal input"""
        
        generator = StructureGenerator()
        
        # Empty inputs
        empty_structures = generator.generate_structures([], [], [], [])
        assert empty_structures == []
        
        # Single element
        single_element = [NoteElement("Lone note", (10, 20, 60, 15), 0.8, "single")]
        single_concept = [Concept("single_c", ["lone", "note"], ["single"], 0.8, "topic")]
        single_cluster = [ConceptCluster("single_cl", single_concept, "Single Topic", 0.8, 1)]
        
        single_structures = generator.generate_structures(
            single_element, single_concept, single_cluster, []
        )
        
        # Should handle gracefully (might create simple structure or none)
        assert isinstance(single_structures, list)
        for structure in single_structures:
            assert structure.confidence > 0.0
            assert len(structure.root_nodes) >= 1
    
    def test_low_confidence_filtering(self):
        """Test filtering of low-confidence structures"""
        
        generator = StructureGenerator({'min_confidence': 0.7})  # High threshold
        
        # Low-confidence content
        low_conf_elements = [
            NoteElement("Unclear text", (10, 20, 80, 15), 0.3, "low1"),
            NoteElement("Another unclear", (10, 40, 90, 15), 0.25, "low2")
        ]
        
        low_conf_concepts = [
            Concept("low_c1", ["unclear"], ["low1"], 0.3, "topic"),
            Concept("low_c2", ["another"], ["low2"], 0.25, "topic")
        ]
        
        low_conf_clusters = [
            ConceptCluster("low_cluster", low_conf_concepts, "Unclear Topics", 0.28, 2)
        ]
        
        structures = generator.generate_structures(
            low_conf_elements, low_conf_concepts, low_conf_clusters, []
        )
        
        # Should filter out low-confidence structures
        for structure in structures:
            assert structure.confidence >= generator.min_confidence
    
    def test_structure_generation_robustness(self):
        """Test robustness to malformed or inconsistent input"""
        
        generator = StructureGenerator()
        
        # Inconsistent references (concept references non-existent element)
        elements = [NoteElement("Real element", (10, 20, 80, 15), 0.8, "real")]
        
        concepts = [
            Concept("real_c", ["real"], ["real"], 0.8, "topic"),
            Concept("fake_c", ["fake"], ["nonexistent"], 0.7, "topic")  # Bad reference
        ]
        
        clusters = [ConceptCluster("mixed", concepts, "Mixed Content", 0.75, 2)]
        
        relationships = [
            Relationship("real", "nonexistent", RelationshipType.ARROW, 0.6)  # Bad reference
        ]
        
        # Should handle gracefully without crashing
        structures = generator.generate_structures(elements, concepts, clusters, relationships)
        
        assert isinstance(structures, list)
        # Should produce some structures despite inconsistent data
        for structure in structures:
            assert len(structure.root_nodes) >= 0
            assert structure.confidence >= 0.0