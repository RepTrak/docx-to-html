"""
Service for managing parsing state during chunk processing.
"""

from typing import Optional, Dict

from ...models.parsing_state import (
    ChunkAnalysis, ChunkType, ParsingState, PartialSection, PartialElement
)
from ...models.monitoring import ProcessingMonitor


class StateManager:
    """Service for managing parsing state during chunk processing."""
    
    def __init__(self, chunk_overlap: int = 200, verbose: bool = False):
        """
        Initialize the state manager.
        
        Args:
            chunk_overlap: Overlap size for context buffer
            verbose: Enable verbose logging
        """
        self.chunk_overlap = chunk_overlap
        self.verbose = verbose
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def update_parsing_state(
        self, 
        chunk: str, 
        analysis: ChunkAnalysis, 
        extracted_content: Optional[Dict],
        parsing_state: ParsingState,
        monitor: Optional[ProcessingMonitor] = None
    ) -> None:
        """Update parsing state based on chunk analysis and extracted content."""
        
        parsing_state.current_chunk_index = analysis.chunk_index
        parsing_state.last_chunk_type = analysis.chunk_type
        
        # Handle section-level changes
        if analysis.chunk_type == ChunkType.SECTION_START:
            self._handle_section_start(chunk, extracted_content, parsing_state)
        elif analysis.chunk_type == ChunkType.SECTION_CONTINUATION:
            self._handle_section_continuation(chunk, extracted_content, parsing_state)
        elif analysis.chunk_type == ChunkType.ELEMENT_START:
            self._handle_element_start(chunk, extracted_content, parsing_state)
        elif analysis.chunk_type == ChunkType.ELEMENT_CONTINUATION:
            self._handle_element_continuation(chunk, extracted_content, parsing_state)
        elif analysis.chunk_type == ChunkType.ELEMENT_COMPLETE:
            self._handle_element_complete(chunk, extracted_content, parsing_state)
        elif analysis.chunk_type == ChunkType.SECTION_COMPLETE:
            self._handle_section_complete(parsing_state)
        
        # Update context buffer
        parsing_state.context_buffer = chunk[-self.chunk_overlap:] if len(chunk) > self.chunk_overlap else chunk
        
        # Update monitoring with current previews
        if monitor:
            self._update_monitoring(parsing_state, monitor)
    
    def _handle_section_start(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState
    ) -> None:
        """Handle start of a new section."""
        # Complete current section if exists
        if parsing_state.current_section and parsing_state.current_section.is_complete:
            # This would be handled by finalizer
            pass
        
        # Start new section
        parsing_state.current_section = PartialSection(
            accumulated_content=chunk
        )
        parsing_state.parsing_phase = "section"
        parsing_state.global_position_counters["section"] += 1
        
        if extracted_content:
            self._merge_section_content(parsing_state.current_section, extracted_content)
    
    def _handle_section_continuation(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState
    ) -> None:
        """Handle continuation of current section."""
        if parsing_state.current_section:
            parsing_state.current_section.accumulated_content += "\n" + chunk
            if extracted_content:
                self._merge_section_content(parsing_state.current_section, extracted_content)
    
    def _handle_element_start(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState
    ) -> None:
        """Handle start of a new element."""
        # Complete current element if exists
        if parsing_state.current_element and parsing_state.current_element.is_complete:
            # This would be handled by finalizer
            pass
        
        # Start new element
        parsing_state.current_element = PartialElement(
            accumulated_content=chunk
        )
        parsing_state.parsing_phase = "element"
        parsing_state.global_position_counters["element"] += 1
        
        if extracted_content:
            self._merge_element_content(parsing_state.current_element, extracted_content)
    
    def _handle_element_continuation(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState
    ) -> None:
        """Handle continuation of current element."""
        if parsing_state.current_element:
            parsing_state.current_element.accumulated_content += "\n" + chunk
            if extracted_content:
                self._merge_element_content(parsing_state.current_element, extracted_content)
    
    def _handle_element_complete(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState
    ) -> None:
        """Handle completion of current element."""
        if parsing_state.current_element:
            parsing_state.current_element.accumulated_content += "\n" + chunk
            if extracted_content:
                self._merge_element_content(parsing_state.current_element, extracted_content)
            parsing_state.current_element.is_complete = True
    
    def _handle_section_complete(self, parsing_state: ParsingState) -> None:
        """Handle completion of current section."""
        if parsing_state.current_section:
            parsing_state.current_section.is_complete = True
    
    def _merge_section_content(self, partial_section: PartialSection, content: Dict) -> None:
        """Merge extracted content into partial section."""
        for key, value in content.items():
            if value is not None:
                if key == "elements":
                    # Handle elements separately
                    continue
                setattr(partial_section, key, value)
    
    def _merge_element_content(self, partial_element: PartialElement, content: Dict) -> None:
        """Merge extracted content into partial element."""
        for key, value in content.items():
            if value is not None:
                if key in ["variables", "columns"]:
                    # Merge lists
                    current_list = getattr(partial_element, key, [])
                    if isinstance(value, list):
                        # Merge by code/id to avoid duplicates
                        existing_codes = {item.get('code') for item in current_list if isinstance(item, dict)}
                        for item in value:
                            if isinstance(item, dict) and item.get('code') not in existing_codes:
                                current_list.append(item)
                        setattr(partial_element, key, current_list)
                else:
                    setattr(partial_element, key, value)
    
    def _update_monitoring(self, parsing_state: ParsingState, monitor: ProcessingMonitor) -> None:
        """Update monitoring with current state previews."""
        section_preview = None
        element_preview = None
        
        if parsing_state.current_section:
            section_preview = {
                "code": parsing_state.current_section.code,
                "label": parsing_state.current_section.label,
                "elements_count": len(parsing_state.current_section.elements or [])
            }
        
        if parsing_state.current_element:
            element_preview = {
                "code": parsing_state.current_element.code,
                "label": parsing_state.current_element.label,
                "type": parsing_state.current_element.type,
                "variables_count": len(parsing_state.current_element.variables or []),
                "columns_count": len(parsing_state.current_element.columns or [])
            }
        
        monitor.update_current_previews(section_preview, element_preview)
        
        # Update content counts
        total_elements = sum(len(section.elements or []) for section in parsing_state.completed_sections)
        if parsing_state.current_section and parsing_state.current_section.elements:
            total_elements += len(parsing_state.current_section.elements)
        
        total_variables = 0
        total_columns = 0
        for section in parsing_state.completed_sections:
            for element in section.elements or []:
                total_variables += len(element.variables or [])
                total_columns += len(element.columns or [])
        
        monitor.update_content_counts(
            len(parsing_state.completed_sections),
            total_elements,
            total_variables,
            total_columns
        )
