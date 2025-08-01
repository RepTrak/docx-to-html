"""
Monitoring schemas for tracking processing states and partial reports.
"""

from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field

class ProcessingPhase(str, Enum):
    """Processing phases for monitoring."""
    INITIALIZING = "initializing"
    CHUNKING = "chunking"
    ANALYZING = "analyzing"
    EXTRACTING = "extracting"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    ERROR = "error"

class ChunkProgress(BaseModel):
    """Progress information for a single chunk."""
    chunk_index: int
    chunk_size: int
    analysis_completed: bool = False
    extraction_completed: bool = False
    chunk_type: Optional[str] = None
    confidence: Optional[float] = None
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None

class ProcessingProgress(BaseModel):
    """Overall processing progress information."""
    current_phase: ProcessingPhase
    total_chunks: int
    chunks_completed: int
    sections_found: int
    elements_found: int
    variables_found: int
    columns_found: int
    start_time: datetime
    last_update: datetime
    estimated_completion: Optional[datetime] = None
    processing_rate_chunks_per_minute: Optional[float] = None
    current_chunk: Optional[ChunkProgress] = None

class PartialReport(BaseModel):
    """Partial processing report that can be generated during processing."""
    file_path: str
    progress: ProcessingProgress
    completed_sections: List[Dict[str, Any]] = Field(default_factory=list)
    current_section_preview: Optional[Dict[str, Any]] = None
    current_element_preview: Optional[Dict[str, Any]] = None
    chunk_summaries: List[ChunkProgress] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    
    # Add checkpoint tracking
    checkpoint_info: Optional[Dict[str, Any]] = None
    sections_checkpointed: int = 0
    elements_checkpointed: int = 0
    last_checkpoint_time: Optional[datetime] = None
    
    def get_completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.progress.total_chunks == 0:
            return 0.0
        return (self.progress.chunks_completed / self.progress.total_chunks) * 100

class ProcessingMonitor:
    """Monitor for tracking processing progress and generating partial reports."""
    
    def __init__(
        self,
        progress_callback: Optional[Callable[[PartialReport], None]] = None,
        save_interval_chunks: int = 10,
        auto_save_dir: Optional[str] = None
    ):
        self.progress_callback = progress_callback
        self.save_interval_chunks = save_interval_chunks
        self.auto_save_dir = auto_save_dir
        self.partial_report: Optional[PartialReport] = None
        
    def initialize(self, file_path: str, total_chunks: int) -> None:
        """Initialize monitoring for a new processing session."""
        now = datetime.now()
        self.partial_report = PartialReport(
            file_path=file_path,
            progress=ProcessingProgress(
                current_phase=ProcessingPhase.INITIALIZING,
                total_chunks=total_chunks,
                chunks_completed=0,
                sections_found=0,
                elements_found=0,
                variables_found=0,
                columns_found=0,
                start_time=now,
                last_update=now
            )
        )
    
    def update_phase(self, phase: ProcessingPhase) -> None:
        """Update the current processing phase."""
        if self.partial_report:
            self.partial_report.progress.current_phase = phase
            self.partial_report.progress.last_update = datetime.now()
            self._trigger_callback()
    
    def start_chunk(self, chunk_index: int, chunk_size: int) -> None:
        """Start processing a new chunk."""
        if not self.partial_report:
            return
            
        chunk_progress = ChunkProgress(
            chunk_index=chunk_index,
            chunk_size=chunk_size
        )
        
        self.partial_report.progress.current_chunk = chunk_progress
        self.partial_report.progress.last_update = datetime.now()
        self._update_processing_rate()
    
    def complete_chunk_analysis(
        self, 
        chunk_index: int, 
        chunk_type: str, 
        confidence: float,
        processing_time_ms: int
    ) -> None:
        """Mark chunk analysis as completed."""
        if not self.partial_report or not self.partial_report.progress.current_chunk:
            return
            
        current_chunk = self.partial_report.progress.current_chunk
        if current_chunk.chunk_index == chunk_index:
            current_chunk.analysis_completed = True
            current_chunk.chunk_type = chunk_type
            current_chunk.confidence = confidence
            current_chunk.processing_time_ms = processing_time_ms
    
    def complete_chunk_extraction(self, chunk_index: int) -> None:
        """Mark chunk extraction as completed."""
        if not self.partial_report or not self.partial_report.progress.current_chunk:
            return
            
        current_chunk = self.partial_report.progress.current_chunk
        if current_chunk.chunk_index == chunk_index:
            current_chunk.extraction_completed = True
    
    def complete_chunk(self, chunk_index: int, error_message: Optional[str] = None) -> None:
        """Complete processing of a chunk."""
        if not self.partial_report:
            return
            
        current_chunk = self.partial_report.progress.current_chunk
        if current_chunk and current_chunk.chunk_index == chunk_index:
            if error_message:
                current_chunk.error_message = error_message
                self.partial_report.errors.append(f"Chunk {chunk_index}: {error_message}")
            
            # Add to summaries
            self.partial_report.chunk_summaries.append(current_chunk)
            
            # Update progress
            self.partial_report.progress.chunks_completed += 1
            self.partial_report.progress.last_update = datetime.now()
            self._update_processing_rate()
            
            # Auto-save if interval reached
            if (self.partial_report.progress.chunks_completed % self.save_interval_chunks == 0 
                and self.auto_save_dir):
                self._auto_save()
            
            self._trigger_callback()
    
    def update_content_counts(
        self, 
        sections_found: int, 
        elements_found: int, 
        variables_found: int = 0, 
        columns_found: int = 0
    ) -> None:
        """Update content counts."""
        if not self.partial_report:
            return
            
        progress = self.partial_report.progress
        progress.sections_found = sections_found
        progress.elements_found = elements_found
        progress.variables_found = variables_found
        progress.columns_found = columns_found
        progress.last_update = datetime.now()
    
    def add_completed_section(self, section_data: Dict[str, Any]) -> None:
        """Add a completed section to the partial report."""
        if not self.partial_report:
            return
            
        self.partial_report.completed_sections.append(section_data)
        self.partial_report.progress.sections_found = len(self.partial_report.completed_sections)
    
    def update_current_previews(
        self, 
        section_preview: Optional[Dict[str, Any]] = None,
        element_preview: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update current section/element previews."""
        if not self.partial_report:
            return
            
        if section_preview:
            self.partial_report.current_section_preview = section_preview
        if element_preview:
            self.partial_report.current_element_preview = element_preview
    
    def add_error(self, error_message: str) -> None:
        """Add an error message."""
        if self.partial_report:
            self.partial_report.errors.append(error_message)
    
    def add_warning(self, warning_message: str) -> None:
        """Add a warning message."""
        if self.partial_report:
            self.partial_report.warnings.append(warning_message)
    
    def update_token_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Update token usage statistics."""
        if not self.partial_report:
            return
            
        self.partial_report.token_usage["input"] = self.partial_report.token_usage.get("input", 0) + input_tokens
        self.partial_report.token_usage["output"] = self.partial_report.token_usage.get("output", 0) + output_tokens
    
    def get_current_report(self) -> Optional[PartialReport]:
        """Get the current partial report."""
        return self.partial_report
    
    def _update_processing_rate(self) -> None:
        """Update processing rate calculation."""
        if not self.partial_report:
            return
            
        progress = self.partial_report.progress
        elapsed = (progress.last_update - progress.start_time).total_seconds()
        
        if elapsed > 0 and progress.chunks_completed > 0:
            rate = (progress.chunks_completed / elapsed) * 60  # chunks per minute
            progress.processing_rate_chunks_per_minute = rate
            
            # Estimate completion time
            if rate > 0:
                remaining_chunks = progress.total_chunks - progress.chunks_completed
                remaining_minutes = remaining_chunks / rate
                progress.estimated_completion = progress.last_update + timedelta(minutes=remaining_minutes)
    
    def _trigger_callback(self) -> None:
        """Trigger the progress callback if set."""
        if self.progress_callback and self.partial_report:
            self.progress_callback(self.partial_report)
    
    def _auto_save(self) -> None:
        """Auto-save the current partial report."""
        if not self.auto_save_dir or not self.partial_report:
            return
            
        from pathlib import Path
        import json
        
        save_dir = Path(self.auto_save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"partial_report_{timestamp}.json"
        filepath = save_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.partial_report.dict(), f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            self.add_error(f"Failed to auto-save partial report: {e}")
    
    def update_checkpoint_info(
        self, 
        sections_checkpointed: int, 
        elements_checkpointed: int,
        checkpoint_summary: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update checkpoint information."""
        if not self.partial_report:
            return
            
        self.partial_report.sections_checkpointed = sections_checkpointed
        self.partial_report.elements_checkpointed = elements_checkpointed
        self.partial_report.last_checkpoint_time = datetime.now()
        
        if checkpoint_summary:
            self.partial_report.checkpoint_info = checkpoint_summary
