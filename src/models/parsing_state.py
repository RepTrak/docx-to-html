from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel
from enum import Enum

from .questionnaire import FullSectionElementSchema, FullSectionResponseSchema, FullSurveyResponseSchema

class ChunkType(str, Enum):
    """Types of content chunks identified by LLM."""
    SECTION_START = "section_start"
    SECTION_CONTINUATION = "section_continuation"
    ELEMENT_START = "element_start" 
    ELEMENT_CONTINUATION = "element_continuation"
    ELEMENT_COMPLETE = "element_complete"
    SECTION_COMPLETE = "section_complete"
    DOCUMENT_END = "document_end"
    UNKNOWN = "unknown"

class ContentBoundary(BaseModel):
    """Represents content boundaries within a chunk."""
    type: Literal["section", "element", "variable", "column"]
    action: Literal["start", "continue", "complete"]
    position: Optional[int] = None
    identifier: Optional[str] = None

class ChunkAnalysis(BaseModel):
    """Analysis result for a markdown chunk."""
    chunk_index: int
    chunk_type: ChunkType
    boundaries: List[ContentBoundary] = []
    extracted_content: Optional[Dict[str, Any]] = None
    is_complete_section: bool = False
    is_complete_element: bool = False
    continuation_context: Optional[str] = None
    next_expected_type: Optional[ChunkType] = None
    confidence: float = 0.0

class PartialSection(BaseModel):
    """Represents a section being built incrementally."""
    code: Optional[str] = None
    label: Optional[str] = None
    notes: Optional[str] = None
    position: Optional[int] = None
    loop: Optional[Dict[str, Any]] = None
    elements: List["PartialElement"] = []
    is_complete: bool = False
    accumulated_content: str = ""

class PartialElement(BaseModel):
    """Represents an element being built incrementally."""
    code: Optional[str] = None
    label: Optional[str] = None
    notes: Optional[str] = None
    type: Optional[str] = None
    position: Optional[int] = None
    revision: Optional[int] = None
    tags: List[Dict[str, str]] = []
    is_loop_target: Optional[bool] = None
    help_text: Optional[str] = None
    variables: List[Dict[str, Any]] = []
    columns: List[Dict[str, Any]] = []
    is_complete: bool = False
    accumulated_content: str = ""

class ParsingState(BaseModel):
    """Overall state of the parsing process."""
    current_chunk_index: int = 0
    total_chunks: int = 0
    current_section: Optional[PartialSection] = None
    current_element: Optional[PartialElement] = None
    completed_sections: List[FullSectionResponseSchema] = []
    parsing_phase: Literal["section", "element", "unknown"] = "unknown"
    last_chunk_type: Optional[ChunkType] = None
    context_buffer: str = ""
    global_position_counters: Dict[str, int] = {"section": 0, "element": 0}

class ProcessingResult(BaseModel):
    """Result of processing a complete document."""
    survey: FullSurveyResponseSchema
    parsing_stats: Dict[str, Any]
    chunks_processed: int
    sections_found: int
    elements_found: int
    total_tokens_used: Dict[str, int]
    errors: List[str] = []
    warnings: List[str] = []
