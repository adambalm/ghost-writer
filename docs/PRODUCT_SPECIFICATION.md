# Ghost Writer v2.0 – Product Specification

**Version**: 2.0  
**Date**: 2025-08-08  
**Status**: Draft Specification

---

## EXECUTIVE SUMMARY

Ghost Writer is a handwritten note processing system that addresses note transcription and organization needs:

1. **Privacy-Conscious Processing** – Transcription of meeting notes, research, and documents using hybrid OCR with local-first processing
2. **Idea Organization** – Semantic relationship detection and structure generation to help organize thoughts into coherent documents

The system leverages unified OCR pipeline with Qwen2.5-VL (primary), Tesseract, Google Cloud Vision, and GPT-4 Vision with cost controls and local fallbacks, providing transcription and idea organization capabilities.

## TARGET USE CASES

### Primary Use Cases:
- **Privacy-focused transcription**: Local-first processing for sensitive content
- **Idea organization**: Help users organize scattered thoughts and notes
- **Document structure**: Generate structured output from handwritten notes

### Competitive Context:
- **Existing OCR tools**: Primarily literal transcription without semantic understanding
- **Note applications**: Linear organization without relationship detection
- **Academic tools**: Research-focused but limited practical application

## USER PROFILES

### Profile 1: Privacy-Conscious Professional
**Description**: Professionals handling sensitive information
**Need**: Accurate transcription without cloud exposure of confidential content
**Use Case**: Meeting notes, research annotations, planning documents
**Benefit**: Local-first privacy with transcription capability

### Profile 2: Idea Organizer
**Description**: Users who generate scattered ideas and need organization help
**Need**: Help organizing disconnected thoughts into coherent documents
**Use Case**: Research notes, creative projects, complex analysis
**Benefit**: Relationship detection and structure generation

## CORE ARCHITECTURE

### Unified OCR Pipeline:
```
Primary: Qwen2.5-VL (Local Vision LLM) ─┐
Fallback: Tesseract (Local Traditional) ─┤
                                          ├─── Smart Router ───> Best Result
Premium: Google Vision (Cloud API) ──────┤
Premium: GPT-4 Vision (Cloud API) ───────┘
```

**OCR Providers** (Priority Order):
- **Qwen2.5-VL**: Primary provider, local vision language model via Ollama (superior handwriting recognition, 2-4 second response)
- **Tesseract**: Local fallback, free, privacy-safe (baseline traditional OCR)
- **Google Cloud Vision**: Premium accuracy, $0.0015/image
- **GPT-4 Vision**: Semantic understanding, $0.01/image  
- **Hybrid Router**: Cost-aware quality selection with automatic fallbacks

**Cost Controls**:
- Daily budget limits with automatic fallbacks
- Confidence-based provider selection
- Real-time cost tracking and alerting

### Idea Organization Pipeline:
```
OCR Text ─> Relationship Detection ─> Concept Clustering ─> Structure Generation ─> Organized Document
```

**Relationship Detection**:
- Visual arrows and connections
- Spatial proximity analysis
- Hierarchical patterns (indentation, numbering)
- Semantic similarity clustering

**Structure Generation**:
- Hierarchical outlines
- Mind map structures  
- Process flows and timelines
- Comparative analysis frameworks

## FUNCTIONAL REQUIREMENTS

### FR-001: Premium OCR Processing
**Trigger**: User uploads handwritten note image
**Behavior**:
- Smart routing between OCR providers based on quality mode and budget
- Image preprocessing for enhanced accuracy
- Confidence scoring and provider fallbacks
- Cost tracking with daily budget enforcement
**Performance**: <30s per page, high transcription accuracy

### FR-002: Relationship Detection
**Trigger**: OCR processing complete with bounding box data
**Behavior**:
- Detect visual relationships (arrows, groupings, proximity)
- Identify hierarchical structures (indentation, numbering)
- Find semantic connections between concepts
- Generate confidence-scored relationship graph
**Performance**: <10s per page, detect explicit relationships

### FR-003: Concept Clustering  
**Trigger**: Relationship detection complete
**Behavior**:
- Extract concepts from note elements using multiple strategies
- Group related concepts into coherent themes
- Calculate cluster confidence and cohesion scores
- Support different concept types (topics, actions, entities)
**Performance**: <5s per page, create meaningful content clusters

### FR-004: Structure Generation
**Trigger**: Concept clustering complete  
**Behavior**:
- Generate multiple document structures (outline, mindmap, timeline, process)
- Rank structures by confidence and coherence
- Export as formatted text with proper hierarchy
- Provide completeness and coherence metrics
**Performance**: <5s per page, generate multiple structure options

### FR-005: Privacy & Cost Controls
**Behavior**:
- Local-first processing with encrypted storage
- Real-time cost monitoring with budget alerts  
- Automatic fallback to local providers when over budget
- Audit logging for all processing decisions
**Performance**: Zero data leakage, costs stay within daily limits

## DATA SCHEMA & STORAGE

**Database**: SQLite with privacy-first design

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `notes` | Core note storage | `note_id`, `source_file`, `raw_text`, `clean_text`, `ocr_provider`, `ocr_confidence`, `processing_cost` |
| `elements` | Note elements with bounding boxes | `element_id`, `note_id`, `text`, `bbox`, `confidence` |  
| `relationships` | Detected relationships | `rel_id`, `source_id`, `target_id`, `relationship_type`, `confidence` |
| `concepts` | Extracted concepts | `concept_id`, `keywords`, `concept_type`, `confidence` |
| `clusters` | Concept clusters | `cluster_id`, `theme`, `confidence`, `cohesion_score` |
| `structures` | Generated structures | `structure_id`, `structure_type`, `title`, `confidence`, `structure_data` |
| `cost_tracking` | Usage monitoring | `date`, `provider`, `usage_count`, `total_cost` |

## TECHNICAL IMPLEMENTATION

### Unified OCR Stack:
- **Qwen2.5-VL via Ollama**: Primary local vision model with superior handwriting recognition
- **Tesseract**: Local fallback with image preprocessing pipeline
- **Google Cloud Vision API**: Premium cloud provider for high-accuracy fallback
- **OpenAI GPT-4 Vision**: Premium semantic transcription with context understanding  
- **Hybrid Router**: Cost-aware provider selection with quality thresholds

### Idea Organization Stack:
- **Relationship Detection**: Pattern matching + spatial analysis + semantic similarity
- **Concept Extraction**: NLP + frequency analysis + type classification
- **Clustering**: Agglomerative clustering enhanced with relationship data
- **Structure Generation**: Template-based generation with multiple output formats

### Dependencies:
```
# OCR & Vision
google-cloud-vision>=3.4.0
openai>=1.0.0  
pytesseract>=0.3.10
Pillow>=10.0.0

# ML & Clustering
numpy>=1.24.0
sentence-transformers>=2.2.0
faiss-cpu>=1.7.0

# Local LLM (future)
ollama>=0.1.0

# Core Infrastructure  
PyYAML>=6.0.1
click>=8.1.6
pytest>=7.0.0 (testing)
```

## QUALITY TARGETS

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| **OCR Accuracy** | High character accuracy | Ground truth comparison on diverse samples |
| **Relationship Detection** | Good precision on explicit relationships | Manual annotation of note samples |
| **Concept Quality** | Meaningful extracted concepts | Expert evaluation of concept clusters |
| **Structure Coherence** | Good structure rating | User studies with target users |
| **Cost Control** | Budget compliance | Automated monitoring and alerts |
| **Privacy Compliance** | No data leakage in local mode | Security audit and testing |

## EVALUATION FRAMEWORK

### Phase 1: Technical Validation
- OCR accuracy benchmarking across provider combinations
- Relationship detection precision/recall analysis
- Concept clustering quality assessment
- Structure generation coherence evaluation

### Phase 2: User Validation  
- Privacy-conscious professionals: User testing with sensitive documents
- Idea organizers: Testing with scattered idea sets
- Usability testing with user feedback
- Cost effectiveness analysis vs manual transcription

### Phase 3: System Validation
- Beta deployment with multiple user types
- Usage analytics and retention measurement
- Feature adoption and workflow integration analysis  
- System performance and reliability testing

## DEVELOPMENT ROADMAP

### Phase 1: Core OCR Infrastructure (Weeks 1-3)
- Database schema and configuration system
- OCR provider implementations  
- Hybrid routing with cost controls
- Comprehensive testing framework

### Phase 2: Idea Organization Engine (Weeks 4-6)  
- Relationship detection algorithms
- Concept clustering implementation
- Structure generation with multiple formats
- Integration testing and optimization

### Phase 3: User Interface & Deployment (Weeks 7-9)
- CLI interface with rich output formatting
- Web interface for document review and editing
- Deployment packaging and user onboarding
- Documentation and tutorial creation

### Phase 4: Market Validation (Weeks 10-12)
- Beta user recruitment and onboarding
- Usage data collection and analysis
- User feedback integration and iteration
- Go-to-market strategy development

## PRICING CONSIDERATIONS

### Potential Pricing Tiers:
- **Local Tier**: Basic pricing (Tesseract only, unlimited usage)
- **Hybrid Tier**: Enhanced pricing (includes API credits, improved accuracy)  
- **Enterprise**: Custom pricing for bulk processing and integration

### Value Considerations:
- **Efficiency**: Faster than manual transcription with privacy protection
- **Organization**: Transform scattered thoughts into structured content
- **Cost Control**: Predictable pricing with automatic budget management

## SUCCESS METRICS

### Product Success Indicators:
- **Usage Retention**: Good monthly active user retention
- **User Satisfaction**: Positive feedback from target users
- **Feature Adoption**: Users utilizing both OCR and idea organization features
- **System Performance**: Reliable operation within performance targets

### Development Metrics:  
- **System Stability**: Consistent operation without critical failures
- **Test Coverage**: Comprehensive test suite with high pass rates
- **Performance**: Meeting response time and accuracy targets
- **Integration**: Successful integration of system components

## NEXT STEPS

### Immediate (Week 1):
1. Complete idea organization implementation
2. Build comprehensive test suite for end-to-end workflows
3. Create demonstration materials showcasing core features
4. Prepare system for user testing

### Short-term (Weeks 2-4):
1. Develop CLI and web interfaces with good user experience
2. Deploy testing version with monitoring
3. Conduct user interviews and workflow observations
4. Iterate based on usage patterns

### Medium-term (Weeks 5-8):  
1. Expand testing program to multiple active users
2. Evaluate system performance and user satisfaction
3. Consider integration opportunities with productivity tools
4. Develop deployment strategy and materials

---

**Document Status**: Draft – Ready for Phase 2 Implementation

**Key Changes from v1.0**:
- Added dual-use strategy focusing on privacy and organization
- Upgraded from basic OCR to hybrid approach with multiple providers
- Added comprehensive idea organization features
- Integrated privacy-first design with cost controls
- Established clear user profiles and use cases
- Defined measurable success criteria and development strategy

This specification outlines the Ghost Writer system for handwritten note processing with privacy and organization capabilities.