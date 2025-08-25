"""Custom exception classes for Ghost Writer application."""

from typing import Optional, Any


class GhostWriterError(Exception):
    """Base exception class for all Ghost Writer exceptions."""
    
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class OCRError(GhostWriterError):
    """Base exception for OCR-related errors."""
    pass


class OCRProviderError(OCRError):
    """Exception raised when an OCR provider fails."""
    
    def __init__(self, provider: str, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.provider = provider


class OCRConfigurationError(OCRError):
    """Exception raised for OCR configuration issues."""
    pass


class OCRBudgetExceededError(OCRError):
    """Exception raised when OCR budget limit is exceeded."""
    
    def __init__(self, current_cost: float, limit: float, message: Optional[str] = None):
        msg = message or f"OCR budget exceeded: ${current_cost:.2f} > ${limit:.2f}"
        super().__init__(msg, {"current_cost": current_cost, "limit": limit})
        self.current_cost = current_cost
        self.limit = limit


class FileProcessingError(GhostWriterError):
    """Exception raised during file processing."""
    
    def __init__(self, file_path: str, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.file_path = file_path


class SupernoteParsingError(FileProcessingError):
    """Exception raised when parsing Supernote files."""
    pass


class DatabaseError(GhostWriterError):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    pass


class DatabaseOperationError(DatabaseError):
    """Exception raised when a database operation fails."""
    
    def __init__(self, operation: str, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.operation = operation


class ConceptClusteringError(GhostWriterError):
    """Exception raised during concept clustering."""
    pass


class RelationshipDetectionError(GhostWriterError):
    """Exception raised during relationship detection."""
    pass


class StructureGenerationError(GhostWriterError):
    """Exception raised during structure generation."""
    pass


class ConfigurationError(GhostWriterError):
    """Exception raised for configuration issues."""
    
    def __init__(self, config_key: str, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.config_key = config_key


class ValidationError(GhostWriterError):
    """Exception raised for validation failures."""
    
    def __init__(self, field: str, value: Any, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, details)
        self.field = field
        self.value = value