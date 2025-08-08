"""
Concept Clustering for Handwritten Note Organization

Groups related ideas and concepts from handwritten notes using multiple
clustering strategies to help organize scattered thoughts into coherent themes.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict, Counter
import numpy as np

from .relationship_detector import NoteElement, Relationship, RelationshipType

logger = logging.getLogger(__name__)


@dataclass
class Concept:
    """A concept extracted from note elements"""
    concept_id: str
    keywords: List[str]
    elements: List[str]  # List of element IDs
    confidence: float
    concept_type: str = "general"  # general, topic, action, entity
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConceptCluster:
    """A cluster of related concepts"""
    cluster_id: str
    concepts: List[Concept]
    theme: str
    confidence: float
    size: int = 0
    cohesion_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConceptExtractor:
    """Extracts concepts from note elements"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.min_concept_length = self.config.get('min_concept_length', 2)
        self.stopwords = self._load_stopwords()
        self.concept_patterns = self._compile_concept_patterns()
        
    def _load_stopwords(self) -> Set[str]:
        """Load common stopwords to filter out"""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its',
            'our', 'their'
        }
    
    def _compile_concept_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile patterns for different concept types"""
        return {
            'topic': [
                re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'),  # Capitalized phrases
                re.compile(r'(?:about|regarding|concerning)\s+([^.!?]+)'),  # Topic indicators
            ],
            'action': [
                re.compile(r'\b((?:need to|should|must|have to)\s+\w+(?:\s+\w+)*)\b'),  # Action items
                re.compile(r'\b(\w+ing\s+\w+(?:\s+\w+)*)\b'),  # Gerund phrases
                re.compile(r'\b(implement|create|develop|build|design|write|review)\s+([^.!?]+)'),
            ],
            'entity': [
                re.compile(r'\b([A-Z][a-z]*(?:\s+[A-Z][a-z]*)*)\b'),  # Proper nouns
                re.compile(r'@(\w+)'),  # Mentions
                re.compile(r'#(\w+)'),  # Hashtags
            ],
            'question': [
                re.compile(r'([^.!?]*\?)', re.MULTILINE),  # Questions
                re.compile(r'((?:what|when|where|why|how|who)\s+[^.!?]*)', re.IGNORECASE),
            ]
        }
    
    def extract_concepts(self, elements: List[NoteElement]) -> List[Concept]:
        """Extract concepts from note elements"""
        concepts = []
        
        # Extract different types of concepts
        for concept_type, patterns in self.concept_patterns.items():
            type_concepts = self._extract_concepts_by_type(elements, patterns, concept_type)
            concepts.extend(type_concepts)
        
        # Extract keyword-based concepts
        keyword_concepts = self._extract_keyword_concepts(elements)
        concepts.extend(keyword_concepts)
        
        # Remove duplicates and filter by quality
        concepts = self._deduplicate_concepts(concepts)
        concepts = self._filter_concepts(concepts)
        
        logger.info(f"Extracted {len(concepts)} concepts from {len(elements)} elements")
        return concepts
    
    def _extract_concepts_by_type(self, elements: List[NoteElement], 
                                patterns: List[re.Pattern], concept_type: str) -> List[Concept]:
        """Extract concepts using type-specific patterns"""
        concepts = []
        concept_counter = defaultdict(list)
        
        for element in elements:
            for pattern in patterns:
                matches = pattern.finditer(element.text)
                for match in matches:
                    concept_text = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    concept_text = concept_text.strip()
                    
                    if len(concept_text) >= self.min_concept_length:
                        concept_counter[concept_text.lower()].append(element.element_id)
        
        # Create concept objects
        for concept_text, element_ids in concept_counter.items():
            if len(element_ids) >= 1:  # At least one occurrence
                keywords = self._extract_keywords(concept_text)
                confidence = min(0.9, 0.5 + (len(element_ids) * 0.1))
                
                concept = Concept(
                    concept_id=f"{concept_type}_{len(concepts)}",
                    keywords=keywords,
                    elements=element_ids,
                    confidence=confidence,
                    concept_type=concept_type,
                    metadata={
                        'original_text': concept_text,
                        'frequency': len(element_ids)
                    }
                )
                concepts.append(concept)
        
        return concepts
    
    def _extract_keyword_concepts(self, elements: List[NoteElement]) -> List[Concept]:
        """Extract concepts based on keyword frequency and co-occurrence"""
        # Tokenize all text
        all_words = []
        word_to_elements = defaultdict(set)
        
        for element in elements:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', element.text.lower())
            filtered_words = [w for w in words if w not in self.stopwords]
            
            all_words.extend(filtered_words)
            for word in filtered_words:
                word_to_elements[word].add(element.element_id)
        
        # Find frequently occurring words
        word_freq = Counter(all_words)
        frequent_words = {word: freq for word, freq in word_freq.items() 
                         if freq >= 2}  # At least 2 occurrences
        
        # Create keyword concepts
        concepts = []
        for word, freq in frequent_words.items():
            if len(word_to_elements[word]) >= 1:  # Appears in at least 1 element
                concept = Concept(
                    concept_id=f"keyword_{word}",
                    keywords=[word],
                    elements=list(word_to_elements[word]),
                    confidence=min(0.8, 0.3 + (freq * 0.1)),
                    concept_type="keyword",
                    metadata={
                        'frequency': freq,
                        'element_count': len(word_to_elements[word])
                    }
                )
                concepts.append(concept)
        
        return concepts
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in self.stopwords]
    
    def _deduplicate_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Remove duplicate concepts based on keyword overlap"""
        deduplicated = []
        
        for concept in concepts:
            is_duplicate = False
            
            for existing in deduplicated:
                # Check keyword overlap (skip if either has no keywords)
                if not concept.keywords or not existing.keywords:
                    continue
                    
                overlap = set(concept.keywords) & set(existing.keywords)
                min_keywords = min(len(concept.keywords), len(existing.keywords))
                if min_keywords > 0 and len(overlap) / min_keywords > 0.7:
                    # Merge into existing concept if similar
                    existing.elements = list(set(existing.elements + concept.elements))
                    existing.confidence = max(existing.confidence, concept.confidence)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(concept)
        
        return deduplicated
    
    def _filter_concepts(self, concepts: List[Concept]) -> List[Concept]:
        """Filter concepts based on quality criteria"""
        filtered = []
        
        for concept in concepts:
            # Filter out low-quality concepts
            if (concept.confidence >= 0.3 and 
                len(concept.elements) >= 1 and
                len(concept.keywords) >= 1):
                filtered.append(concept)
        
        return filtered


class ConceptClusterer:
    """Clusters related concepts into themes"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.similarity_threshold = self.config.get('similarity_threshold', 0.4)
        self.min_cluster_size = self.config.get('min_cluster_size', 2)
        
    def cluster_concepts(self, concepts: List[Concept], 
                        relationships: List[Relationship]) -> List[ConceptCluster]:
        """Main method to cluster concepts"""
        if not concepts:
            return []
        
        # Build concept similarity matrix
        similarity_matrix = self._build_similarity_matrix(concepts)
        
        # Enhance similarity using relationships
        enhanced_matrix = self._enhance_with_relationships(
            similarity_matrix, concepts, relationships
        )
        
        # Perform clustering
        clusters = self._agglomerative_clustering(concepts, enhanced_matrix)
        
        # Generate cluster themes
        for cluster in clusters:
            cluster.theme = self._generate_cluster_theme(cluster.concepts)
            cluster.cohesion_score = self._calculate_cohesion(cluster, enhanced_matrix)
        
        # Filter and sort clusters
        clusters = [c for c in clusters if c.size >= self.min_cluster_size]
        clusters.sort(key=lambda c: c.confidence, reverse=True)
        
        logger.info(f"Created {len(clusters)} concept clusters from {len(concepts)} concepts")
        return clusters
    
    def _build_similarity_matrix(self, concepts: List[Concept]) -> np.ndarray:
        """Build similarity matrix between concepts"""
        n = len(concepts)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i+1, n):
                similarity = self._calculate_concept_similarity(concepts[i], concepts[j])
                similarity_matrix[i, j] = similarity
                similarity_matrix[j, i] = similarity
        
        # Set diagonal to 1.0 (self-similarity)
        np.fill_diagonal(similarity_matrix, 1.0)
        
        return similarity_matrix
    
    def _calculate_concept_similarity(self, concept1: Concept, concept2: Concept) -> float:
        """Calculate similarity between two concepts"""
        # Keyword similarity (Jaccard coefficient)
        keywords1 = set(concept1.keywords)
        keywords2 = set(concept2.keywords)
        
        if not keywords1 or not keywords2:
            keyword_sim = 0.0
        else:
            intersection = keywords1 & keywords2
            union = keywords1 | keywords2
            keyword_sim = len(intersection) / len(union)
        
        # Element overlap similarity
        elements1 = set(concept1.elements)
        elements2 = set(concept2.elements)
        
        if not elements1 or not elements2:
            element_sim = 0.0
        else:
            element_intersection = elements1 & elements2
            element_union = elements1 | elements2
            element_sim = len(element_intersection) / len(element_union)
        
        # Type similarity
        type_sim = 1.0 if concept1.concept_type == concept2.concept_type else 0.3
        
        # Weighted combination
        similarity = (0.5 * keyword_sim + 0.3 * element_sim + 0.2 * type_sim)
        
        return similarity
    
    def _enhance_with_relationships(self, similarity_matrix: np.ndarray, 
                                   concepts: List[Concept], 
                                   relationships: List[Relationship]) -> np.ndarray:
        """Enhance similarity matrix using detected relationships"""
        enhanced_matrix = similarity_matrix.copy()
        
        # Create mapping from element ID to concept indices
        element_to_concepts = defaultdict(list)
        for i, concept in enumerate(concepts):
            for element_id in concept.elements:
                element_to_concepts[element_id].append(i)
        
        # Boost similarity for concepts connected by relationships
        for rel in relationships:
            source_concepts = element_to_concepts.get(rel.source_id, [])
            target_concepts = element_to_concepts.get(rel.target_id, [])
            
            for source_idx in source_concepts:
                for target_idx in target_concepts:
                    if source_idx != target_idx:
                        # Boost similarity based on relationship strength
                        boost = 0.2 * rel.confidence
                        
                        # Different relationship types provide different boosts
                        if rel.relationship_type in [RelationshipType.ARROW, RelationshipType.SEQUENCE]:
                            boost *= 1.2
                        elif rel.relationship_type == RelationshipType.HIERARCHY:
                            boost *= 1.1
                        
                        enhanced_matrix[source_idx, target_idx] += boost
                        enhanced_matrix[target_idx, source_idx] += boost
        
        # Ensure values don't exceed 1.0
        enhanced_matrix = np.clip(enhanced_matrix, 0.0, 1.0)
        
        return enhanced_matrix
    
    def _agglomerative_clustering(self, concepts: List[Concept], 
                                similarity_matrix: np.ndarray) -> List[ConceptCluster]:
        """Perform agglomerative clustering on concepts"""
        n = len(concepts)
        if n == 0:
            return []
        
        # Initialize each concept as its own cluster
        clusters = []
        for i, concept in enumerate(concepts):
            cluster = ConceptCluster(
                cluster_id=f"cluster_{i}",
                concepts=[concept],
                theme="",
                confidence=concept.confidence,
                size=1
            )
            clusters.append(cluster)
        
        # Merge clusters iteratively
        while True:
            best_i, best_j, best_similarity = self._find_best_merge(clusters, similarity_matrix)
            
            if best_similarity < self.similarity_threshold:
                break
            
            # Merge clusters
            merged_cluster = self._merge_clusters(clusters[best_i], clusters[best_j])
            
            # Remove merged clusters and add new one
            clusters = [c for idx, c in enumerate(clusters) if idx not in [best_i, best_j]]
            clusters.append(merged_cluster)
            
            # Update similarity matrix (simplified - in practice you'd update properly)
            if len(clusters) <= 1:
                break
        
        return clusters
    
    def _find_best_merge(self, clusters: List[ConceptCluster], 
                        similarity_matrix: np.ndarray) -> Tuple[int, int, float]:
        """Find the best pair of clusters to merge"""
        best_similarity = -1
        best_i, best_j = -1, -1
        
        for i in range(len(clusters)):
            for j in range(i+1, len(clusters)):
                # Calculate inter-cluster similarity
                similarity = self._calculate_cluster_similarity(
                    clusters[i], clusters[j], similarity_matrix
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_i, best_j = i, j
        
        return best_i, best_j, best_similarity
    
    def _calculate_cluster_similarity(self, cluster1: ConceptCluster, 
                                    cluster2: ConceptCluster, 
                                    similarity_matrix: np.ndarray) -> float:
        """Calculate similarity between two clusters"""
        # This is a simplified version - average linkage
        similarities = []
        
        for concept1 in cluster1.concepts:
            for concept2 in cluster2.concepts:
                # Find similarity from matrix (simplified lookup)
                similarities.append(0.5)  # Placeholder
        
        return np.mean(similarities) if similarities else 0.0
    
    def _merge_clusters(self, cluster1: ConceptCluster, 
                       cluster2: ConceptCluster) -> ConceptCluster:
        """Merge two clusters into one"""
        merged_concepts = cluster1.concepts + cluster2.concepts
        merged_size = cluster1.size + cluster2.size
        merged_confidence = (cluster1.confidence * cluster1.size + 
                           cluster2.confidence * cluster2.size) / merged_size
        
        return ConceptCluster(
            cluster_id=f"merged_{cluster1.cluster_id}_{cluster2.cluster_id}",
            concepts=merged_concepts,
            theme="",  # Will be generated later
            confidence=merged_confidence,
            size=merged_size
        )
    
    def _generate_cluster_theme(self, concepts: List[Concept]) -> str:
        """Generate a theme name for a cluster"""
        # Collect all keywords from concepts
        all_keywords = []
        type_counts = defaultdict(int)
        
        for concept in concepts:
            all_keywords.extend(concept.keywords)
            type_counts[concept.concept_type] += 1
        
        # Find most common keywords
        keyword_freq = Counter(all_keywords)
        top_keywords = [word for word, _ in keyword_freq.most_common(3)]
        
        # Find dominant type
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]
        
        # Generate theme
        if top_keywords:
            theme = " + ".join(top_keywords)
            if dominant_type != "general":
                theme += f" ({dominant_type})"
        else:
            theme = f"{dominant_type} cluster"
        
        return theme
    
    def _calculate_cohesion(self, cluster: ConceptCluster, 
                           similarity_matrix: np.ndarray) -> float:
        """Calculate cohesion score for a cluster"""
        if cluster.size <= 1:
            return 1.0
        
        # Average internal similarity (simplified)
        internal_similarities = []
        for i, concept1 in enumerate(cluster.concepts):
            for j, concept2 in enumerate(cluster.concepts[i+1:], i+1):
                # Simplified similarity calculation
                internal_similarities.append(0.6)  # Placeholder
        
        return np.mean(internal_similarities) if internal_similarities else 0.0
    
    def get_cluster_summary(self, cluster: ConceptCluster) -> Dict[str, Any]:
        """Get a summary of a concept cluster"""
        all_elements = set()
        all_keywords = []
        type_distribution = defaultdict(int)
        
        for concept in cluster.concepts:
            all_elements.update(concept.elements)
            all_keywords.extend(concept.keywords)
            type_distribution[concept.concept_type] += 1
        
        keyword_freq = Counter(all_keywords)
        
        return {
            'cluster_id': cluster.cluster_id,
            'theme': cluster.theme,
            'size': cluster.size,
            'confidence': cluster.confidence,
            'cohesion_score': cluster.cohesion_score,
            'element_count': len(all_elements),
            'top_keywords': dict(keyword_freq.most_common(5)),
            'concept_types': dict(type_distribution),
            'concepts': [
                {
                    'id': c.concept_id,
                    'type': c.concept_type,
                    'keywords': c.keywords,
                    'confidence': c.confidence
                }
                for c in cluster.concepts
            ]
        }