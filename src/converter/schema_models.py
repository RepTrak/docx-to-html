"""
Data models for markdown to schema conversion process.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..models.questionnaire import (
    FullSurveyResponseSchema, 
    FullSectionResponseSchema, 
    FullSectionElementSchema,
)


@dataclass
class ConversionState:
    """Tracks the current state of chunk processing."""
    current_section: Optional[FullSectionResponseSchema] = None
    current_element: Optional[FullSectionElementSchema] = None
    completed_sections: List[FullSectionResponseSchema] = field(default_factory=list)
    section_position_counter: int = 0
    element_position_counter: int = 0
    accumulated_content: str = ""
    last_chunk_type: str = "unknown"
    processing_errors: List[str] = field(default_factory=list)


@dataclass
class ProcessingStats:
    """Statistics about the processing operation."""
    total_chunks: int = 0
    processed_chunks: int = 0
    sections_created: int = 0
    elements_created: int = 0
    variables_created: int = 0
    columns_created: int = 0
    llm_calls: int = 0
    total_tokens: Dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0})
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ChunkExtractionResult:
    """Result of processing a single chunk."""
    chunk_type: str
    extracted_sections: List[Dict[str, Any]] = field(default_factory=list)
    extracted_elements: List[Dict[str, Any]] = field(default_factory=list)
    partial_content: Optional[str] = None
    requires_continuation: bool = False
    confidence: float = 0.0
    error: Optional[str] = None
