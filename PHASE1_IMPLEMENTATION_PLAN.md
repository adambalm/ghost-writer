# Phase 1 Implementation Plan - Ghost Writer MVP (Hybrid OCR)

## Phase 1 Overview (2 Weeks)
**Goal**: Build core OCR → Storage → Index pipeline with hybrid OCR providers

**Success Criteria**:
- Process .note and PNG files via multiple OCR backends
- Tesseract: ≥80% accuracy, zero cost, full privacy
- Cloud Vision: ≥90% accuracy, cost-controlled, premium option
- Store notes in SQLite with proper schema
- Generate semantic embeddings and FAISS index
- CLI search returns relevant notes with similarity scores

## Hybrid OCR Architecture

### OCR Provider Abstraction
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class OCRResult:
    text: str
    confidence: float
    word_confidences: List[float]
    processing_time: float
    provider: str
    cost: float

class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, image_path: str) -> OCRResult:
        pass
    
    @abstractmethod
    def get_cost_estimate(self, image_path: str) -> float:
        pass
```

### Provider Implementations
- **TesseractOCR**: Local processing, $0 cost, good privacy
- **CloudVisionOCR**: Google API, $1.50/1000 images, superior accuracy
- **HybridOCR**: Intelligent routing based on confidence/cost thresholds

## Week 1: Foundation & OCR Pipeline

### Day 1-2: Project Bootstrap
**Tasks**:
- [ ] Install Tesseract OCR locally
- [ ] Set up Google Cloud Vision API credentials (optional)
- [ ] Set up Python virtual environment
- [ ] Install hybrid requirements (updated requirements.txt)
- [ ] Download Ollama llama3.2:3b model
- [ ] Create project directory structure
- [ ] Initialize SQLite database with schema
- [ ] Create configuration system with OCR provider selection

**Updated Requirements.txt**:
```
pytesseract==3.10.1
google-cloud-vision==3.4.4  # Optional for premium OCR
sentence-transformers==2.2.2
faiss-cpu==1.7.4
ollama==0.1.7
Pillow==10.0.1
numpy==1.24.3
PyYAML==6.0.1
click==8.1.7
```

**Enhanced Config.yaml**:
```yaml
ocr:
  default_provider: "tesseract"  # Options: tesseract, cloud_vision, hybrid
  providers:
    tesseract:
      config: "--oem 3 --psm 6"
      confidence_threshold: 60
    cloud_vision:
      credentials_path: "config/google_cloud_credentials.json"
      language_hints: ["en"]
      confidence_threshold: 70
    hybrid:
      low_confidence_threshold: 75  # Switch to cloud if tesseract < 75%
      cost_limit_per_day: 5.00      # Max daily spend on cloud OCR
      prefer_local: true             # Try tesseract first
```

### Day 3-5: Hybrid OCR Processing Module
**Tasks**:
- [ ] Implement `src/utils/ocr_providers.py` with provider abstraction
- [ ] Implement `TesseractOCR` with preprocessing pipeline
- [ ] Implement `CloudVisionOCR` with Google API integration  
- [ ] Implement `HybridOCR` with intelligent routing
- [ ] Add cost tracking and daily spend monitoring
- [ ] Create comprehensive error handling for both providers
- [ ] Write unit tests for all OCR providers

**Files to Create**:
```
src/utils/ocr_providers.py
src/utils/cost_tracker.py
tests/test_ocr_providers.py
config/google_cloud_credentials.json.example
```

**OCR Providers API**:
```python
class TesseractOCR(OCRProvider):
    def extract_text(self, image_path: str) -> OCRResult:
        # Local processing, preprocessing pipeline
        
class CloudVisionOCR(OCRProvider):
    def extract_text(self, image_path: str) -> OCRResult:
        # Google Cloud Vision API call
        
class HybridOCR(OCRProvider):
    def extract_text(self, image_path: str) -> OCRResult:
        # Try tesseract first, fallback to cloud if needed
        
class CostTracker:
    def track_usage(self, provider: str, cost: float) -> None:
    def get_daily_spend(self) -> float:
    def check_budget_limit(self) -> bool:
```

## Week 2: Database Integration & Search

### Day 6-8: Enhanced Database Operations
**Tasks**:
- [ ] Extend database schema to include OCR provider metadata
- [ ] Add cost tracking table for API usage monitoring
- [ ] Implement provider-specific confidence scoring
- [ ] Add OCR result comparison and quality metrics
- [ ] Create data validation for multiple OCR sources
- [ ] Write integration tests with both providers

**Enhanced Database Schema**:
```sql
CREATE TABLE notes (
    note_id TEXT PRIMARY KEY,
    source_file TEXT,
    raw_text TEXT,
    clean_text TEXT,
    ocr_provider TEXT,
    ocr_confidence REAL,
    processing_cost REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ocr_usage (
    usage_id TEXT PRIMARY KEY,
    provider TEXT,
    cost REAL,
    images_processed INTEGER,
    date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Day 9-10: Search with Provider Metadata
**Tasks**:
- [ ] Extend search to include OCR confidence filtering
- [ ] Add provider-based result ranking
- [ ] Implement cost-aware search suggestions
- [ ] Create provider performance analytics
- [ ] Add search result metadata (provider, confidence, cost)

### Day 11-14: Enhanced CLI Interface
**Tasks**:
- [ ] Update `ingest.py` with provider selection options
- [ ] Add cost monitoring and budget alerts to CLI
- [ ] Implement provider comparison mode
- [ ] Create OCR quality assessment tools
- [ ] Add provider switching based on confidence scores

**Enhanced CLI Examples**:
```bash
# Use specific provider
python src/ingest.py --file sample.png --provider tesseract
python src/ingest.py --file sample.png --provider cloud_vision

# Hybrid mode with cost control
python src/ingest.py --directory notes/ --provider hybrid --budget-limit 5.00

# Compare providers on same image
python src/ingest.py --file sample.png --compare-providers --output-report

# Search with confidence filtering
python src/query.py --text "notes" --min-confidence 0.8 --provider-preference local
```

## Cost Analysis & Monitoring

### Provider Cost Comparison
| Provider | Cost per Image | Accuracy | Privacy | Speed | Use Case |
|----------|----------------|----------|---------|--------|----------|
| **Tesseract** | $0.00 | 80-85% | Full | Fast | Daily notes, drafts |
| **Cloud Vision** | $0.0015 | 90-95% | Limited | Medium | Important documents |
| **Hybrid** | $0.00-0.0015 | 85-95% | Mixed | Variable | Intelligent routing |

### Budget Control Features
- **Daily Spend Limits**: Hard stop at configured budget
- **Smart Routing**: Use expensive provider only when needed
- **Cost Alerts**: Warnings at 50%, 75%, 90% of budget
- **Usage Analytics**: Track accuracy vs cost trends

### Provider Selection Logic
```python
def select_provider(image_path: str, config: dict) -> str:
    # 1. Check budget remaining
    if daily_spend >= config['cost_limit']:
        return 'tesseract'
    
    # 2. Try tesseract first (if hybrid mode)
    result = tesseract_ocr.extract_text(image_path)
    if result.confidence >= config['confidence_threshold']:
        return 'tesseract'
    
    # 3. Use cloud vision for low-confidence results
    if config['fallback_to_cloud']:
        return 'cloud_vision'
    
    return 'tesseract'  # Default fallback
```

## Risk Mitigation Updates

### Technical Risks
1. **Cloud Vision API Costs Exceed Budget**
   - Mitigation: Hard daily spend limits with automatic fallback
   - Monitoring: Real-time cost tracking with alerts

2. **Cloud Vision API Unavailable**
   - Mitigation: Graceful degradation to Tesseract
   - Fallback: Local processing always available

3. **Network Connectivity Issues**
   - Mitigation: Offline mode with Tesseract only
   - Recovery: Queue cloud processing when connectivity returns

### Enhanced Acceptance Criteria

### Functional Requirements ✅/❌
- [ ] Support both Tesseract and Cloud Vision OCR
- [ ] Intelligent provider routing based on confidence/cost
- [ ] Real-time cost tracking and budget enforcement
- [ ] Provider comparison and quality assessment
- [ ] Graceful fallback when cloud services unavailable
- [ ] Search results include OCR provider metadata

### Cost Management Requirements ✅/❌
- [ ] Daily spend tracking with <$5 default limit
- [ ] Budget alerts at 50%, 75%, 90% thresholds  
- [ ] Automatic fallback to free provider at budget limit
- [ ] Cost per note tracking and analytics
- [ ] Monthly cost reporting and trends

## Optional Setup: Google Cloud Vision

### Prerequisites (Optional)
```bash
# 1. Create Google Cloud Project
# 2. Enable Vision API
# 3. Create service account key
# 4. Download credentials JSON

# 5. Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="config/google_cloud_credentials.json"

# 6. Install Google Cloud SDK (optional)
curl https://sdk.cloud.google.com | bash
gcloud auth application-default login
```

### Verification
```bash
# Test Tesseract (required)
python -c "import pytesseract; print('Tesseract ready')"

# Test Cloud Vision (optional)  
python -c "from google.cloud import vision; print('Cloud Vision ready')"

# Test hybrid setup
python src/ingest.py --file test.png --provider hybrid --dry-run
```

This hybrid approach gives you **best of both worlds**: privacy and cost control with Tesseract, plus premium accuracy with Cloud Vision when needed.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "1", "content": "Update implementation plan with hybrid OCR approach", "status": "completed"}, {"id": "2", "content": "Design OCR provider abstraction layer", "status": "completed"}, {"id": "3", "content": "Add Google Cloud Vision configuration options", "status": "completed"}, {"id": "4", "content": "Update cost analysis and requirements", "status": "completed"}]