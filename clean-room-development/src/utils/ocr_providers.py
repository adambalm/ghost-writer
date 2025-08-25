"""
OCR Provider implementations for Ghost Writer with premium accuracy focus
"""

import os
import time
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import pytesseract

from .config import config
from .logging_setup import log_calls
from .debug_helpers import debug_decorator
from .database import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Standardized OCR result across all providers"""
    text: str
    confidence: float  # 0.0 to 1.0
    provider: str
    processing_time: float
    cost: float = 0.0
    word_confidences: List[float] = field(default_factory=list)
    bounding_boxes: List[Dict] = field(default_factory=list)
    raw_response: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class OCRProvider(ABC):
    """Abstract base class for OCR providers"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        self.config = provider_config
        # Normalize provider names properly
        class_name = self.__class__.__name__.lower()
        if class_name.endswith('ocr'):
            self.name = class_name[:-3]  # Remove 'ocr' suffix
        if 'vision' in self.name and 'google' in self.name:
            self.name = 'google_vision'
        elif 'gpt4' in self.name and 'vision' in self.name:
            self.name = 'gpt4_vision'
    
    @abstractmethod
    def extract_text(self, image_path: Union[str, Path]) -> OCRResult:
        """Extract text from image"""
        pass
    
    def preprocess_image(self, image_path: Union[str, Path]) -> Image.Image:
        """Common image preprocessing pipeline"""
        image = Image.open(image_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Apply preprocessing based on config
        if self.config.get('preprocessing', {}).get('enhance_contrast', False):
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
        
        if self.config.get('preprocessing', {}).get('remove_noise', False):
            image = image.filter(ImageFilter.MedianFilter(3))
        
        if self.config.get('preprocessing', {}).get('deskew', False):
            # Simple deskew - could be enhanced with more sophisticated algorithms
            image = ImageOps.autocontrast(image)
        
        return image
    
    def get_cost_estimate(self, image_path: Union[str, Path]) -> float:
        """Estimate cost for processing this image"""
        return self.config.get('cost_per_image', 0.0)
    
    def validate_result(self, result: OCRResult) -> bool:
        """Validate OCR result quality"""
        if not result.text or not result.text.strip():
            return False
        
        # Check if confidence meets threshold
        threshold = self.config.get('confidence_threshold', 0.0)
        return result.confidence >= threshold / 100.0


class TesseractOCR(OCRProvider):
    """Local Tesseract OCR provider"""
    
    @log_calls("ghost_writer")
    @debug_decorator(log_args=False, profile=True)
    def extract_text(self, image_path: Union[str, Path]) -> OCRResult:
        start_time = time.time()
        
        try:
            # Preprocess image
            image = self.preprocess_image(image_path)
            
            # Get tesseract config
            tesseract_config = self.config.get('config', '--oem 3 --psm 6')
            
            # Extract text with confidence data
            text = pytesseract.image_to_string(image, config=tesseract_config)
            
            # Get detailed data for confidence scores
            try:
                data = pytesseract.image_to_data(image, config=tesseract_config, 
                                               output_type=pytesseract.Output.DICT)
                
                # Calculate average confidence (excluding -1 values)
                confidences = [conf for conf in data['conf'] if conf > 0]
                avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0
                
                # Extract word-level confidences and bounding boxes
                word_confidences = [conf / 100.0 for conf in data['conf'] if conf > 0]
                bounding_boxes = []
                
                for i, word in enumerate(data['text']):
                    if word.strip() and i < len(data['conf']) and data['conf'][i] > 0:
                        bounding_boxes.append({
                            'word': word,
                            'confidence': data['conf'][i] / 100.0,
                            'bbox': (data['left'][i], data['top'][i], 
                                   data['width'][i], data['height'][i])
                        })
                
            except Exception as e:
                logger.warning(f"Could not extract detailed confidence data: {e}")
                avg_confidence = 0.7  # Conservative estimate
                word_confidences = []
                bounding_boxes = []
            
            processing_time = time.time() - start_time
            
            result = OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                provider='tesseract',
                processing_time=processing_time,
                cost=0.0,
                word_confidences=word_confidences,
                bounding_boxes=bounding_boxes,
                metadata={
                    'tesseract_version': pytesseract.get_tesseract_version(),
                    'config': tesseract_config
                }
            )
            
            logger.info(f"Tesseract OCR completed - {len(text)} chars, "
                       f"confidence: {avg_confidence:.2f}, time: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Tesseract OCR failed: {e}", exc_info=True)
            
            return OCRResult(
                text="",
                confidence=0.0,
                provider='tesseract',
                processing_time=processing_time,
                cost=0.0,
                metadata={'error': str(e)}
            )


class GoogleVisionOCR(OCRProvider):
    """Google Cloud Vision API OCR provider"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Vision client"""
        try:
            from google.cloud import vision
            
            # Set credentials if specified
            credentials_path = self.config.get('credentials_path')
            if credentials_path and Path(credentials_path).exists():
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            self.client = vision.ImageAnnotatorClient()
            logger.info("Google Vision client initialized successfully")
            
        except ImportError:
            logger.error("google-cloud-vision not installed. Run: pip install google-cloud-vision")
            self.client = None
        except Exception as e:
            logger.warning(f"Google Vision client not available: {e}")
            self.client = None
    
    @log_calls("ghost_writer")
    @debug_decorator(log_args=False, profile=True)
    def extract_text(self, image_path: Union[str, Path]) -> OCRResult:
        start_time = time.time()
        
        if not self.client:
            raise RuntimeError("Google Vision client not initialized")
        
        try:
            from google.cloud import vision
            
            # Preprocess and prepare image
            image = self.preprocess_image(image_path)
            
            # Convert PIL image to bytes
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            content = img_byte_arr.getvalue()
            
            # Create Vision API image object
            vision_image = vision.Image(content=content)
            
            # Perform OCR
            features = self.config.get('features', ['DOCUMENT_TEXT_DETECTION'])
            feature_objects = [vision.Feature(type_=getattr(vision.Feature.Type, feature)) 
                             for feature in features]
            
            request = vision.AnnotateImageRequest(
                image=vision_image,
                features=feature_objects
            )
            
            response = self.client.annotate_image(request=request)
            
            # Handle errors
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            # Extract text and confidence
            if response.full_text_annotation:
                text = response.full_text_annotation.text
                
                # Calculate confidence from pages
                total_confidence = 0
                word_count = 0
                word_confidences = []
                bounding_boxes = []
                
                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                if hasattr(word, 'confidence'):
                                    total_confidence += word.confidence
                                    word_confidences.append(word.confidence)
                                    word_count += 1
                                    
                                    # Extract word text and bounding box
                                    word_text = ''.join([symbol.text for symbol in word.symbols])
                                    vertices = word.bounding_box.vertices
                                    if vertices:
                                        x_coords = [v.x for v in vertices]
                                        y_coords = [v.y for v in vertices]
                                        bounding_boxes.append({
                                            'word': word_text,
                                            'confidence': word.confidence,
                                            'bbox': (min(x_coords), min(y_coords),
                                                   max(x_coords) - min(x_coords),
                                                   max(y_coords) - min(y_coords))
                                        })
                
                avg_confidence = total_confidence / word_count if word_count > 0 else 0.8
                
            else:
                text = ""
                avg_confidence = 0.0
                word_confidences = []
                bounding_boxes = []
            
            processing_time = time.time() - start_time
            cost = self.get_cost_estimate(image_path)
            
            result = OCRResult(
                text=text.strip() if text else "",
                confidence=avg_confidence,
                provider='google_vision',
                processing_time=processing_time,
                cost=cost,
                word_confidences=word_confidences,
                bounding_boxes=bounding_boxes,
                raw_response=response,
                metadata={
                    'api_features': features,
                    'response_time': processing_time
                }
            )
            
            logger.info(f"Google Vision OCR completed - {len(result.text)} chars, "
                       f"confidence: {avg_confidence:.2f}, cost: ${cost:.4f}, "
                       f"time: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Google Vision OCR failed: {e}", exc_info=True)
            
            return OCRResult(
                text="",
                confidence=0.0,
                provider='google_vision',
                processing_time=processing_time,
                cost=self.get_cost_estimate(image_path),
                metadata={'error': str(e)}
            )


class GPT4VisionOCR(OCRProvider):
    """OpenAI GPT-4 Vision OCR provider"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            import openai
            
            # Get API key from environment
            api_key_env = self.config.get('api_key_env', 'OPENAI_API_KEY')
            api_key = os.getenv(api_key_env)
            
            if not api_key:
                logger.warning(f"No API key found in {api_key_env} environment variable")
                return
            
            self.client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI GPT-4 Vision client initialized successfully")
            
        except ImportError:
            logger.error("openai not installed. Run: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    @log_calls("ghost_writer")
    @debug_decorator(log_args=False, profile=True)
    def extract_text(self, image_path: Union[str, Path]) -> OCRResult:
        start_time = time.time()
        
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        try:
            # Preprocess image
            image = self.preprocess_image(image_path)
            
            # Encode image to base64
            import io
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            base64_image = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            
            # Prepare system prompt
            system_prompt = self.config.get('system_prompt', 
                "Transcribe this handwritten text exactly as written. "
                "Preserve structure and formatting. Mark unclear text with [unclear].")
            
            # Call GPT-4 Vision
            response = self.client.chat.completions.create(
                model=self.config.get('model', 'gpt-4o'),
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text",
                                "text": "Please transcribe this handwritten text:"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.config.get('max_tokens', 4000)
            )
            
            # Extract response
            if response.choices and response.choices[0].message:
                text = response.choices[0].message.content.strip()
                
                # GPT-4 Vision doesn't provide confidence scores directly
                # Estimate based on response characteristics
                unclear_count = text.count('[unclear]')
                total_words = len(text.split())
                
                if total_words == 0:
                    confidence = 0.0
                elif unclear_count == 0:
                    confidence = 0.9  # High confidence when no unclear markers
                else:
                    confidence = max(0.5, 1.0 - (unclear_count / total_words))
                
            else:
                text = ""
                confidence = 0.0
            
            processing_time = time.time() - start_time
            cost = self.get_cost_estimate(image_path)
            
            result = OCRResult(
                text=text,
                confidence=confidence,
                provider='gpt4_vision',
                processing_time=processing_time,
                cost=cost,
                raw_response=response,
                metadata={
                    'model': self.config.get('model', 'gpt-4o'),
                    'tokens_used': response.usage.total_tokens if response.usage else 0,
                    'unclear_markers': text.count('[unclear]') if text else 0
                }
            )
            
            logger.info(f"GPT-4 Vision OCR completed - {len(text)} chars, "
                       f"confidence: {confidence:.2f}, cost: ${cost:.4f}, "
                       f"time: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"GPT-4 Vision OCR failed: {e}", exc_info=True)
            
            return OCRResult(
                text="",
                confidence=0.0,
                provider='gpt4_vision',
                processing_time=processing_time,
                cost=self.get_cost_estimate(image_path),
                metadata={'error': str(e)}
            )


class HybridOCR(OCRProvider):
    """Intelligent routing between OCR providers"""
    
    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all available OCR providers"""
        # Get provider configurations
        ocr_config = config.get('ocr', {})
        
        # Initialize Tesseract (always available)
        if 'tesseract' in ocr_config.get('providers', {}):
            self.providers['tesseract'] = TesseractOCR(
                ocr_config['providers']['tesseract']
            )
        
        # Initialize Google Vision (if configured)
        if 'google_vision' in ocr_config.get('providers', {}):
            try:
                self.providers['google_vision'] = GoogleVisionOCR(
                    ocr_config['providers']['google_vision']
                )
            except Exception as e:
                logger.warning(f"Could not initialize Google Vision: {e}")
        
        # Initialize GPT-4 Vision (if configured)
        if 'gpt4_vision' in ocr_config.get('providers', {}):
            try:
                self.providers['gpt4_vision'] = GPT4VisionOCR(
                    ocr_config['providers']['gpt4_vision']
                )
            except Exception as e:
                logger.warning(f"Could not initialize GPT-4 Vision: {e}")
        
        logger.info(f"Initialized hybrid OCR with providers: {list(self.providers.keys())}")
    
    @log_calls("ghost_writer")
    @debug_decorator(log_args=False, profile=True)
    def extract_text(self, image_path: Union[str, Path]) -> OCRResult:
        """Smart routing between providers based on configuration"""
        
        # Check daily budget
        db = DatabaseManager()
        daily_cost = sum(costs.get('cost', 0) for costs in db.get_daily_ocr_cost().values())
        budget_limit = self.config.get('cost_limit_per_day', 5.0)
        
        # Determine provider priority based on mode and budget
        quality_mode = self.config.get('quality_mode', 'balanced')
        provider_priority = self._get_provider_priority(quality_mode, daily_cost, budget_limit)
        
        logger.info(f"Hybrid OCR routing - mode: {quality_mode}, "
                   f"daily_cost: ${daily_cost:.4f}, budget: ${budget_limit}, "
                   f"priority: {provider_priority}")
        
        # Try providers in priority order
        last_result = None
        for provider_name in provider_priority:
            if provider_name not in self.providers:
                continue
            
            provider = self.providers[provider_name]
            
            try:
                result = provider.extract_text(image_path)
                
                # Track usage in database
                db.track_ocr_usage(provider_name, result.cost)
                
                # Check if result meets quality threshold
                threshold = self.config.get('confidence_thresholds', {}).get(provider_name, 0.75)
                
                if result.confidence >= threshold / 100.0:
                    logger.info(f"Hybrid OCR success with {provider_name} - "
                               f"confidence: {result.confidence:.2f} >= {threshold/100.0:.2f}")
                    return result
                else:
                    logger.info(f"Hybrid OCR {provider_name} below threshold - "
                               f"confidence: {result.confidence:.2f} < {threshold/100.0:.2f}, trying next")
                    last_result = result
                    
            except Exception as e:
                logger.error(f"Hybrid OCR {provider_name} failed: {e}")
                continue
        
        # If all providers failed or didn't meet threshold, return best result
        if last_result:
            logger.warning("Hybrid OCR: No provider met threshold, returning best result")
            return last_result
        
        # Final fallback - return empty result
        logger.error("Hybrid OCR: All providers failed")
        return OCRResult(
            text="",
            confidence=0.0,
            provider='hybrid_failed',
            processing_time=0.0,
            cost=0.0,
            metadata={'error': 'All OCR providers failed'}
        )
    
    def _get_provider_priority(self, quality_mode: str, daily_cost: float, budget_limit: float) -> List[str]:
        """Determine provider priority based on mode and budget constraints"""
        
        # If over budget, use only free providers
        if daily_cost >= budget_limit:
            return ['tesseract']
        
        # Get base priority from config
        base_priority = self.config.get('provider_priority', ['tesseract', 'google_vision', 'gpt4_vision'])
        
        # Adjust based on quality mode
        if quality_mode == 'fast':
            # Prioritize speed - local first, then fastest cloud
            return ['tesseract', 'google_vision', 'gpt4_vision']
        
        elif quality_mode == 'premium':
            # Prioritize quality - best cloud providers first
            return ['gpt4_vision', 'google_vision', 'tesseract']
        
        else:  # balanced
            # Good balance - try local first, fallback to cloud
            return base_priority
    
    def get_available_providers(self) -> List[str]:
        """Get list of available initialized providers"""
        return list(self.providers.keys())


# Factory function to create OCR providers
def create_ocr_provider(provider_name: str) -> OCRProvider:
    """Factory function to create OCR provider instances"""
    
    ocr_config = config.get('ocr', {})
    providers_config = ocr_config.get('providers', {})
    
    if provider_name not in providers_config:
        raise ValueError(f"Unknown OCR provider: {provider_name}")
    
    provider_config = providers_config[provider_name]
    
    if provider_name == 'tesseract':
        return TesseractOCR(provider_config)
    elif provider_name == 'google_vision':
        return GoogleVisionOCR(provider_config)
    elif provider_name == 'gpt4_vision':
        return GPT4VisionOCR(provider_config)
    elif provider_name == 'hybrid':
        return HybridOCR(provider_config)
    else:
        raise ValueError(f"Unknown OCR provider: {provider_name}")