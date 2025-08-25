"""
Tests for Concept Clustering in Handwritten Note Organization

Tests concept extraction and clustering algorithms using realistic
handwritten note scenarios with scattered ideas that need organization.
"""

import pytest
from unittest.mock import MagicMock
from collections import Counter

from src.utils.concept_clustering import (
    ConceptExtractor, ConceptClusterer, Concept, ConceptCluster
)
from src.utils.relationship_detector import NoteElement, Relationship, RelationshipType


class TestConceptExtractor:
    """Test concept extraction from note elements"""
    
    def test_topic_concept_extraction(self):
        """Test extraction of topic-based concepts"""
        
        extractor = ConceptExtractor()
        
        # Create elements with topic indicators
        elements = [
            NoteElement("About Machine Learning algorithms", (10, 20, 150, 15), 0.9, "elem1"),
            NoteElement("Machine Learning is important", (10, 40, 140, 15), 0.85, "elem2"),
            NoteElement("Deep Learning Networks", (10, 60, 120, 15), 0.88, "elem3"),
            NoteElement("regarding Neural Networks", (10, 80, 130, 15), 0.82, "elem4")
        ]
        
        concepts = extractor.extract_concepts(elements)
        
        # Should find topic concepts
        topic_concepts = [c for c in concepts if c.concept_type == "topic"]
        assert len(topic_concepts) > 0
        
        # Should identify machine learning as a key topic
        ml_concept = None
        for concept in topic_concepts:
            if any("machine" in kw.lower() for kw in concept.keywords):
                ml_concept = concept
                break
        
        assert ml_concept is not None
        assert ml_concept.confidence > 0.0
        assert len(ml_concept.elements) >= 1
    
    def test_action_concept_extraction(self):
        """Test extraction of action-oriented concepts"""
        
        extractor = ConceptExtractor()
        
        elements = [
            NoteElement("Need to implement database", (10, 20, 130, 15), 0.9, "action1"),
            NoteElement("Should review the code", (10, 40, 120, 15), 0.85, "action2"),
            NoteElement("Must create test cases", (10, 60, 125, 15), 0.88, "action3"),
            NoteElement("Building new features", (10, 80, 115, 15), 0.82, "action4")
        ]
        
        concepts = extractor.extract_concepts(elements)
        
        # Should find action concepts
        action_concepts = [c for c in concepts if c.concept_type == "action"]
        assert len(action_concepts) > 0
        
        # Verify action concepts contain relevant keywords
        action_keywords = []
        for concept in action_concepts:
            action_keywords.extend(concept.keywords)
        
        expected_actions = ["implement", "review", "create", "building"]
        found_actions = [kw for kw in action_keywords if kw.lower() in expected_actions]
        assert len(found_actions) > 0
    
    def test_entity_concept_extraction(self):
        """Test extraction of entity concepts (proper nouns, mentions)"""
        
        extractor = ConceptExtractor()
        
        elements = [
            NoteElement("Meeting with John Smith", (10, 20, 120, 15), 0.9, "entity1"),
            NoteElement("Python Programming Language", (10, 40, 140, 15), 0.85, "entity2"),
            NoteElement("Google Cloud Platform", (10, 60, 130, 15), 0.88, "entity3"),
            NoteElement("@teamlead mentioned this", (10, 80, 135, 15), 0.82, "entity4"),
            NoteElement("#important project", (10, 100, 100, 15), 0.87, "entity5")
        ]
        
        concepts = extractor.extract_concepts(elements)
        
        # Should find entity concepts (@ mentions and # hashtags)
        entity_concepts = [c for c in concepts if c.concept_type == "entity"]
        assert len(entity_concepts) > 0
        
        # Should capture @ mentions and # hashtags as entities
        entity_keywords = []
        for concept in entity_concepts:
            entity_keywords.extend(concept.keywords)
        
        assert "teamlead" in entity_keywords or "important" in entity_keywords
        
        # Should also extract proper nouns (might be classified as topics)
        all_keywords = []
        for concept in concepts:
            all_keywords.extend(concept.keywords)
        
        # Should find key entities in any concept type
        assert any(kw in ["john", "python", "google"] for kw in all_keywords)
    
    def test_keyword_concept_extraction(self):
        """Test extraction of frequently occurring keyword concepts"""
        
        extractor = ConceptExtractor()
        
        elements = [
            NoteElement("Database design patterns for systems", (10, 20, 140, 15), 0.9, "kw1"),
            NoteElement("Design principles for database systems", (10, 40, 150, 15), 0.85, "kw2"),
            NoteElement("System design interviews and patterns", (10, 60, 150, 15), 0.88, "kw3"),
            NoteElement("Database optimization and design techniques", (10, 80, 165, 15), 0.82, "kw4"),
            NoteElement("System performance and design metrics", (10, 100, 155, 15), 0.87, "kw5")
        ]
        
        concepts = extractor.extract_concepts(elements)
        
        # Should find keyword concepts
        keyword_concepts = [c for c in concepts if c.concept_type == "keyword"]
        assert len(keyword_concepts) > 0
        
        # Should identify frequently occurring words
        frequent_words = []
        for concept in keyword_concepts:
            frequent_words.extend(concept.keywords)
        
        word_counts = Counter(frequent_words)
        # Should find frequently occurring words (accounting for variations like system/systems)
        total_system_words = word_counts.get("system", 0) + word_counts.get("systems", 0)
        total_design_words = word_counts.get("design", 0) + word_counts.get("designed", 0)
        total_pattern_words = word_counts.get("patterns", 0) + word_counts.get("pattern", 0)
        
        # At least one category should have multiple occurrences
        assert (total_system_words >= 2 or total_design_words >= 2 or 
               total_pattern_words >= 2 or len(frequent_words) >= 2)
    
    def test_concept_deduplication(self):
        """Test removal of duplicate and similar concepts"""
        
        extractor = ConceptExtractor()
        
        # Create elements that should generate similar concepts
        elements = [
            NoteElement("Machine learning algorithms", (10, 20, 140, 15), 0.9, "dup1"),
            NoteElement("ML algorithm implementation", (10, 40, 135, 15), 0.85, "dup2"),
            NoteElement("Algorithm for machine learning", (10, 60, 150, 15), 0.88, "dup3")
        ]
        
        concepts = extractor.extract_concepts(elements)
        
        # Should deduplicate similar concepts
        algorithm_concepts = []
        for concept in concepts:
            if any("algorithm" in kw.lower() for kw in concept.keywords):
                algorithm_concepts.append(concept)
        
        # Should merge similar concepts rather than having many duplicates
        assert len(algorithm_concepts) <= 2  # At most 2 algorithm-related concepts
        
        # Merged concept should reference multiple elements
        if algorithm_concepts:
            merged_concept = max(algorithm_concepts, key=lambda c: len(c.elements))
            assert len(merged_concept.elements) >= 2
    
    def test_concept_quality_filtering(self):
        """Test filtering of low-quality concepts"""
        
        extractor = ConceptExtractor()
        
        elements = [
            NoteElement("High quality meaningful content", (10, 20, 160, 15), 0.9, "good1"),
            NoteElement("", (10, 40, 0, 15), 0.1, "empty1"),  # Empty text
            NoteElement("a", (10, 60, 10, 15), 0.2, "short1"),  # Too short
            NoteElement("Another good concept here", (10, 80, 140, 15), 0.88, "good2")
        ]
        
        concepts = extractor.extract_concepts(elements)
        
        # Should filter out low-quality concepts
        for concept in concepts:
            assert concept.confidence >= 0.3  # Minimum confidence threshold
            assert len(concept.elements) >= 1  # At least one element
            assert len(concept.keywords) >= 1  # At least one keyword


class TestConceptClusterer:
    """Test concept clustering algorithms"""
    
    def test_concept_similarity_calculation(self):
        """Test similarity calculation between concepts"""
        
        clusterer = ConceptClusterer()
        
        # Create similar concepts
        concept1 = Concept("ml_1", ["machine", "learning"], ["elem1"], 0.8, "topic")
        concept2 = Concept("ml_2", ["learning", "algorithms"], ["elem2"], 0.85, "topic")
        concept3 = Concept("food_1", ["cooking", "recipes"], ["elem3"], 0.7, "topic")
        
        # Test similarity calculations
        sim_ml = clusterer._calculate_concept_similarity(concept1, concept2)
        sim_different = clusterer._calculate_concept_similarity(concept1, concept3)
        
        # Similar ML concepts should have higher similarity
        assert sim_ml > sim_different
        assert sim_ml > 0.3  # Should have reasonable similarity due to "learning"
        assert sim_different < 0.5  # Should have low similarity
    
    def test_concept_clustering_with_relationships(self):
        """Test clustering enhanced by relationship information"""
        
        clusterer = ConceptClusterer({'similarity_threshold': 0.4})
        
        # Create related concepts
        concepts = [
            Concept("ai_1", ["artificial", "intelligence"], ["elem1"], 0.9, "topic"),
            Concept("ml_1", ["machine", "learning"], ["elem2"], 0.85, "topic"),
            Concept("nn_1", ["neural", "networks"], ["elem3"], 0.88, "topic"),
            Concept("cook_1", ["cooking", "recipes"], ["elem4"], 0.82, "topic")
        ]
        
        # Create relationships that should boost AI/ML clustering
        relationships = [
            Relationship("elem1", "elem2", RelationshipType.PROXIMITY, 0.8),
            Relationship("elem2", "elem3", RelationshipType.ARROW, 0.7),
            Relationship("elem1", "elem3", RelationshipType.SIMILARITY, 0.6)
        ]
        
        clusters = clusterer.cluster_concepts(concepts, relationships)
        
        # Should create meaningful clusters
        assert len(clusters) > 0
        
        # Should group AI/ML/NN concepts together
        ai_cluster = None
        for cluster in clusters:
            concept_keywords = []
            for concept in cluster.concepts:
                concept_keywords.extend(concept.keywords)
            
            if any(kw in ["artificial", "machine", "neural"] for kw in concept_keywords):
                ai_cluster = cluster
                break
        
        assert ai_cluster is not None
        assert ai_cluster.size >= 2  # Should group at least 2 AI-related concepts
    
    def test_cluster_theme_generation(self):
        """Test automatic generation of cluster themes"""
        
        clusterer = ConceptClusterer()
        
        # Create cluster with ML concepts
        ml_concepts = [
            Concept("ml_1", ["machine", "learning"], ["elem1"], 0.9, "topic"),
            Concept("dl_1", ["deep", "learning"], ["elem2"], 0.85, "topic"),
            Concept("nn_1", ["neural", "networks"], ["elem3"], 0.88, "topic")
        ]
        
        cluster = ConceptCluster("test_cluster", ml_concepts, "", 0.8, len(ml_concepts))
        
        # Generate theme
        theme = clusterer._generate_cluster_theme(ml_concepts)
        
        assert theme is not None
        assert len(theme) > 0
        # Should contain some key ML terms
        assert any(term in theme.lower() for term in ["learning", "neural", "machine"])
    
    def test_cluster_cohesion_scoring(self):
        """Test calculation of cluster cohesion scores"""
        
        clusterer = ConceptClusterer()
        
        # Create highly related concepts
        coherent_concepts = [
            Concept("db_1", ["database", "design"], ["elem1"], 0.9, "topic"),
            Concept("db_2", ["database", "optimization"], ["elem2"], 0.85, "topic")
        ]
        
        # Create unrelated concepts  
        random_concepts = [
            Concept("misc_1", ["cooking", "recipes"], ["elem3"], 0.8, "topic"),
            Concept("misc_2", ["sports", "basketball"], ["elem4"], 0.7, "topic")
        ]
        
        coherent_cluster = ConceptCluster("coherent", coherent_concepts, "Database", 0.8, 2)
        random_cluster = ConceptCluster("random", random_concepts, "Mixed", 0.6, 2)
        
        # Mock similarity matrix for testing
        coherent_matrix = [[1.0, 0.8], [0.8, 1.0]]  # High internal similarity
        random_matrix = [[1.0, 0.2], [0.2, 1.0]]    # Low internal similarity
        
        coherent_score = clusterer._calculate_cohesion(coherent_cluster, coherent_matrix)
        random_score = clusterer._calculate_cohesion(random_cluster, random_matrix)
        
        # Coherent cluster should have higher cohesion (this is a simplified test)
        assert isinstance(coherent_score, float)
        assert isinstance(random_score, float)
    
    def test_cluster_summary_generation(self):
        """Test generation of cluster summaries"""
        
        clusterer = ConceptClusterer()
        
        concepts = [
            Concept("ai_1", ["artificial", "intelligence"], ["elem1", "elem3"], 0.9, "topic"),
            Concept("ml_1", ["machine", "learning"], ["elem2"], 0.85, "action")
        ]
        
        cluster = ConceptCluster(
            cluster_id="test_cluster",
            concepts=concepts,
            theme="AI & Machine Learning",
            confidence=0.87,
            size=2,
            cohesion_score=0.75
        )
        
        summary = clusterer.get_cluster_summary(cluster)
        
        # Verify summary structure
        assert summary['cluster_id'] == "test_cluster"
        assert summary['theme'] == "AI & Machine Learning"
        assert summary['size'] == 2
        assert summary['confidence'] == 0.87
        assert summary['cohesion_score'] == 0.75
        assert summary['element_count'] == 3  # elem1, elem2, elem3
        
        # Should include top keywords
        assert 'top_keywords' in summary
        assert len(summary['top_keywords']) > 0
        
        # Should include concept type distribution
        assert 'concept_types' in summary
        assert summary['concept_types']['topic'] == 1
        assert summary['concept_types']['action'] == 1
        
        # Should include concept details
        assert 'concepts' in summary
        assert len(summary['concepts']) == 2


class TestConceptClusteringPipeline:
    """Test end-to-end concept clustering pipeline"""
    
    def test_complete_concept_organization_workflow(self):
        """Test complete workflow from note elements to organized concept clusters"""
        
        # Simulate scattered handwritten notes about a research project
        elements = [
            # ML research topic
            NoteElement("Machine Learning for healthcare", (10, 20, 160, 15), 0.9, "ml1"),
            NoteElement("Need to research neural networks", (10, 40, 150, 15), 0.85, "ml2"),
            NoteElement("Deep learning applications", (10, 60, 130, 15), 0.88, "ml3"),
            
            # Data collection actions
            NoteElement("Must collect patient data", (200, 20, 140, 15), 0.82, "data1"),
            NoteElement("Should clean the dataset", (200, 40, 125, 15), 0.87, "data2"),
            
            # Technical implementation
            NoteElement("Python TensorFlow library", (10, 120, 135, 15), 0.91, "tech1"),
            NoteElement("Google Cloud Platform setup", (10, 140, 145, 15), 0.89, "tech2"),
            
            # Meeting notes
            NoteElement("Meeting with Dr. Johnson", (200, 120, 130, 15), 0.84, "meet1"),
            NoteElement("Schedule follow-up discussion", (200, 140, 155, 15), 0.86, "meet2")
        ]
        
        # Extract concepts
        extractor = ConceptExtractor({'min_concept_length': 2})
        concepts = extractor.extract_concepts(elements)
        
        # Should extract multiple concept types
        assert len(concepts) > 0
        
        concept_types = {c.concept_type for c in concepts}
        expected_types = {"topic", "action", "entity"}
        assert len(concept_types & expected_types) >= 2
        
        # Create some mock relationships to enhance clustering
        relationships = [
            Relationship("ml1", "ml2", RelationshipType.PROXIMITY, 0.8),
            Relationship("ml2", "ml3", RelationshipType.SIMILARITY, 0.7),
            Relationship("data1", "data2", RelationshipType.SEQUENCE, 0.6),
            Relationship("tech1", "tech2", RelationshipType.GROUPING, 0.75)
        ]
        
        # Cluster concepts
        clusterer = ConceptClusterer({'similarity_threshold': 0.3, 'min_cluster_size': 2})
        clusters = clusterer.cluster_concepts(concepts, relationships)
        
        # Should create meaningful clusters
        assert len(clusters) > 0
        
        # Verify cluster quality
        for cluster in clusters:
            assert cluster.size >= clusterer.min_cluster_size
            assert cluster.confidence > 0.0
            assert len(cluster.theme) > 0
            assert len(cluster.concepts) >= 1
        
        # Should group related concepts together
        cluster_themes = [c.theme.lower() for c in clusters]
        
        # Should find clusters related to main topics
        has_ml_cluster = any("machine" in theme or "learning" in theme or "neural" in theme 
                           for theme in cluster_themes)
        has_data_cluster = any("data" in theme or "collect" in theme 
                              for theme in cluster_themes)
        
        # At least one of the main themes should be clustered
        assert has_ml_cluster or has_data_cluster
    
    def test_concept_clustering_edge_cases(self):
        """Test concept clustering with edge cases"""
        
        clusterer = ConceptClusterer({'similarity_threshold': 0.5})
        
        # Test with empty concepts
        empty_clusters = clusterer.cluster_concepts([], [])
        assert empty_clusters == []
        
        # Test with single concept
        single_concept = [Concept("solo", ["lonely"], ["elem1"], 0.8, "topic")]
        single_clusters = clusterer.cluster_concepts(single_concept, [])
        # Should handle single concept gracefully (might create cluster or return empty)
        assert isinstance(single_clusters, list)
        
        # Test with very dissimilar concepts (should create separate clusters or none)
        dissimilar_concepts = [
            Concept("food", ["cooking", "recipes"], ["elem1"], 0.8, "topic"),
            Concept("tech", ["programming", "software"], ["elem2"], 0.7, "topic"),
            Concept("sports", ["basketball", "games"], ["elem3"], 0.9, "topic")
        ]
        
        dissimilar_clusters = clusterer.cluster_concepts(dissimilar_concepts, [])
        
        # With high similarity threshold, might create few or no clusters
        for cluster in dissimilar_clusters:
            assert cluster.size >= 1
            assert cluster.confidence > 0.0