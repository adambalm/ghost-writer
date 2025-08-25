"""OCR provider factory with singleton/caching pattern."""

import logging
from typing import Dict, Optional, Any
from .ocr_providers import HybridOCR, OCRResult
from .exceptions import OCRConfigurationError, OCRError

logger = logging.getLogger(__name__)


class OCRProviderFactory:
    """Factory for creating and caching OCR provider instances."""
    
    _instances: Dict[str, HybridOCR] = {}
    
    @classmethod
    def get_provider(cls, provider_config: Optional[Dict[str, Any]] = None) -> HybridOCR:
        """
        Get an OCR provider instance, creating and caching if necessary.
        
        Args:
            provider_config: OCR provider configuration
            
        Returns:
            HybridOCR instance
            
        Raises:
            OCRConfigurationError: If configuration is invalid
        """
        # Create a cache key based on configuration
        if provider_config is None:
            provider_config = {}
        
        # Use a simplified hash for caching (just the keys that matter)
        cache_key = cls._create_cache_key(provider_config)
        
        if cache_key not in cls._instances:
            try:
                logger.debug(f"Creating new OCR provider instance for key: {cache_key}")
                cls._instances[cache_key] = HybridOCR(provider_config=provider_config)
            except Exception as e:
                raise OCRConfigurationError("ocr.providers", f"Failed to create OCR provider: {e}")
        
        return cls._instances[cache_key]
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached OCR provider instances."""
        cls._instances.clear()
        logger.debug("OCR provider cache cleared")
    
    @classmethod
    def _create_cache_key(cls, config: Dict[str, Any]) -> str:
        """Create a cache key from configuration."""
        # Only include configuration that affects provider behavior
        key_parts = []
        
        if "providers" in config:
            providers = config["providers"]
            if "tesseract" in providers:
                key_parts.append(f"tesseract:{providers['tesseract'].get('confidence_threshold', 60)}")
            if "google_vision" in providers:
                key_parts.append(f"gv:{providers['google_vision'].get('confidence_threshold', 80)}")
            if "gpt4_vision" in providers:
                key_parts.append(f"gpt4:{providers['gpt4_vision'].get('confidence_threshold', 85)}")
        
        if "hybrid" in config:
            hybrid = config["hybrid"]
            key_parts.append(f"mode:{hybrid.get('quality_mode', 'balanced')}")
            key_parts.append(f"limit:{hybrid.get('cost_limit_per_day', 5.0)}")
        
        return "|".join(key_parts) if key_parts else "default"


def create_ocr_result_without_extraction(text: str, provider: str, confidence: float, 
                                       cost: float = 0.0) -> OCRResult:
    """
    Create an OCRResult instance without performing actual OCR extraction.
    Useful for combining multi-page results.
    
    Args:
        text: The extracted text
        provider: Name of the OCR provider
        confidence: OCR confidence score (0.0 to 1.0)
        cost: Processing cost in dollars
        
    Returns:
        OCRResult instance
    """
    return OCRResult(
        text=text,
        confidence=confidence,
        provider=provider,
        processing_time=0.0,  # No processing time for combined results
        cost=cost,
        bounding_boxes=[],  # Empty for combined results
        word_confidences=[]  # Empty for combined results
    )