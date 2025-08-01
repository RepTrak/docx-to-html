"""
Service for managing parsing state during chunk processing.
"""

from typing import Optional, Dict, List
import re
import logging
from ...models.parsing_state import (
    ChunkAnalysis, ChunkType, ParsingState, PartialSection, PartialElement
)
from ...models.monitoring import ProcessingMonitor
from ..checkpoints.checkpoint_manager import CheckpointManager


class StateManager:
    """Service for managing parsing state during chunk processing."""
    
    def __init__(
        self, 
        chunk_overlap: int = 200, 
        verbose: bool = False,
        checkpoint_manager: Optional[CheckpointManager] = None
    ):
        """
        Initialize the state manager.
        
        Args:
            chunk_overlap: Overlap size for context buffer
            verbose: Enable verbose logging
            checkpoint_manager: Optional checkpoint manager for saving state
        """
        self.chunk_overlap = chunk_overlap
        self.verbose = verbose
        self.checkpoint_manager = checkpoint_manager
        # Track continuity across chunks
        self.last_section_code = None
        self.last_element_code = None
        self.processing_table = False  # Track if we're in middle of a table
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def _detect_completion_boundaries(self, chunk: str, extracted_content: Optional[Dict]) -> Dict[str, bool]:
        """
        Detect if sections or elements are complete in delimiter-based chunks.
        """
        # In delimiter strategy, each chunk is typically a complete unit
        chunk_lines = chunk.split('\n')
        
        section_complete = False
        element_complete = False
        new_section_found = False
        new_element_found = False
        
        # Check for section headers
        for line in chunk_lines:
            line = line.strip()
            if re.match(r'^#+\s+Section\s+\d+', line, re.IGNORECASE):
                new_section_found = True
                section_complete = True
        
        # Check for element headers
        for line in chunk_lines:
            line = line.strip()
            if re.match(r'^\*\*[^*]+\*\*:', line):
                new_element_found = True
                element_complete = True
                break
        
        # For delimiter chunks, if we don't find new markers, 
        # assume content is complete within this chunk
        if not new_section_found and not new_element_found:
            # This might be continuation content - mark as complete
            # since delimiter chunks are separated by ***
            element_complete = True
        
        return {
            "section_complete": section_complete,
            "element_complete": element_complete,
            "new_section_found": new_section_found,
            "new_element_found": new_element_found
        }
    
    def _should_finalize_section(self, parsing_state: ParsingState, chunk_analysis: ChunkAnalysis) -> bool:
        """Determine if current section should be finalized."""
        if not parsing_state.current_section:
            return False
        
        # Finalize if we're starting a new section
        if chunk_analysis.chunk_type == ChunkType.SECTION_START:
            return True
        
        # Finalize if section is marked complete and has content
        if (parsing_state.current_section.is_complete and 
            parsing_state.current_section.code and 
            not parsing_state.current_section.ends_incomplete):
            return True
        
        # Finalize if we detect a new section in boundaries
        completion_info = self._detect_completion_boundaries("", None)  # Will be called with proper args
        if completion_info.get("new_section_found", False):
            return True
        
        return False
    
    def _should_finalize_element(self, parsing_state: ParsingState, chunk_analysis: ChunkAnalysis) -> bool:
        """Determine if current element should be finalized."""
        if not parsing_state.current_element:
            return False
        
        # Finalize if we're starting a new element or section
        if chunk_analysis.chunk_type in [ChunkType.ELEMENT_START, ChunkType.SECTION_START]:
            return True
        
        # Finalize if element is marked complete and has content
        if (parsing_state.current_element.is_complete and 
            parsing_state.current_element.code and 
            not parsing_state.current_element.ends_incomplete):
            return True
        
        # Finalize if we detect a new element in boundaries
        completion_info = self._detect_completion_boundaries("", None)  # Will be called with proper args
        if completion_info.get("new_element_found", False):
            return True
        
        return False
    
    def _ensure_continuity_context(self, parsing_state: ParsingState) -> None:
        """Ensure proper context for delimiter-based chunks."""
        # For delimiter strategy, we need less complex continuity management
        # since chunks are separated cleanly by ***
        
        # If no current section, create a default one
        if not parsing_state.current_section:
            parsing_state.current_section = PartialSection(
                code=f"section_{parsing_state.global_position_counters['section'] + 1}",
                label="Default Section",
                accumulated_content="",
                starts_incomplete=False
            )
            parsing_state.global_position_counters["section"] += 1
            self._log("Created default section for delimiter-based processing")
    
    def update_parsing_state(
        self, 
        chunk: str, 
        analysis: ChunkAnalysis, 
        extracted_content: Optional[Dict],
        parsing_state: ParsingState,
        monitor: Optional[ProcessingMonitor] = None
    ) -> None:
        """Update parsing state based on chunk analysis and extracted content."""
        
        self._log(f"Updating state for chunk {analysis.chunk_index}, type: {analysis.chunk_type.value}")
        
        parsing_state.current_chunk_index = analysis.chunk_index
        parsing_state.last_chunk_type = analysis.chunk_type
        
        # Ensure continuity context before processing
        self._ensure_continuity_context(parsing_state)
        
        # Detect completion boundaries
        completion_info = self._detect_completion_boundaries(chunk, extracted_content)
        
        # Finalize current element if needed
        if self._should_finalize_element(parsing_state, analysis):
            self._finalize_current_element(parsing_state)
        
        # Finalize current section if needed  
        if self._should_finalize_section(parsing_state, analysis):
            self._finalize_current_section(parsing_state)
        
        # Handle chunk type specific processing
        if analysis.chunk_type == ChunkType.SECTION_START:
            self._handle_section_start(chunk, extracted_content, parsing_state, completion_info)
        elif analysis.chunk_type == ChunkType.SECTION_CONTINUATION:
            self._handle_section_continuation(chunk, extracted_content, parsing_state, completion_info)
        elif analysis.chunk_type == ChunkType.ELEMENT_START:
            self._handle_element_start(chunk, extracted_content, parsing_state, completion_info)
        elif analysis.chunk_type == ChunkType.ELEMENT_CONTINUATION:
            self._handle_element_continuation(chunk, extracted_content, parsing_state, completion_info)
        elif analysis.chunk_type == ChunkType.ELEMENT_COMPLETE:
            self._handle_element_complete(chunk, extracted_content, parsing_state, completion_info)
        elif analysis.chunk_type == ChunkType.SECTION_COMPLETE:
            self._handle_section_complete(parsing_state, completion_info)
        elif analysis.chunk_type == ChunkType.UNKNOWN:
            self._handle_unknown_chunk(chunk, extracted_content, parsing_state, completion_info)
        
        # Update continuity tracking
        self._update_continuity_tracking(parsing_state)
        
        # Update context buffer
        parsing_state.context_buffer = chunk[-self.chunk_overlap:] if len(chunk) > self.chunk_overlap else chunk
        
        # Update monitoring with current previews
        if monitor:
            self._update_monitoring(parsing_state, monitor)
    
    def _handle_unknown_chunk(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState,
        completion_info: Dict[str, bool]
    ) -> None:
        """Handle unknown chunks in delimiter strategy - likely complete elements."""
        # In delimiter strategy, unknown chunks are often complete elements
        # separated by *** delimiter
        
        # Ensure we have a section
        if not parsing_state.current_section:
            parsing_state.current_section = PartialSection(
                code=f"section_{parsing_state.global_position_counters['section'] + 1}",
                label="Auto-created Section",
                accumulated_content=""
            )
            parsing_state.global_position_counters["section"] += 1
        
        # Try to extract content as a complete element
        if extracted_content and isinstance(extracted_content, dict):
            # Create new element for this chunk
            parsing_state.current_element = PartialElement(
                accumulated_content=chunk,
                is_complete=True  # Delimiter chunks are typically complete
            )
            parsing_state.global_position_counters["element"] += 1
            
            # Update element with extracted content
            parsing_state.current_element.update_from_extraction(extracted_content)
            
            # Mark as complete and finalize
            self._finalize_current_element(parsing_state)
        else:
            # If no extracted content, add to current section as raw content
            if parsing_state.current_section:
                parsing_state.current_section.accumulated_content += "\n" + chunk
    
    def _update_continuity_tracking(self, parsing_state: ParsingState) -> None:
        """Update continuity tracking for next chunk."""
        if parsing_state.current_section:
            self.last_section_code = parsing_state.current_section.code
        
        if parsing_state.current_element:
            self.last_element_code = parsing_state.current_element.code
        
        self._log(f"Updated continuity: section={self.last_section_code}, element={self.last_element_code}")
    
    def _handle_section_start(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState,
        completion_info: Dict[str, bool]
    ) -> None:
        """Handle start of a new section."""
        # Start new section
        parsing_state.current_section = PartialSection(
            accumulated_content=chunk
        )
        parsing_state.parsing_phase = "section"
        parsing_state.global_position_counters["section"] += 1
        
        if extracted_content:
            parsing_state.current_section.update_from_extraction(extracted_content)
        
        # Mark as complete if boundary detection indicates so
        if completion_info["section_complete"]:
            parsing_state.current_section.is_complete = True
        
        # Reset table processing state
        self.processing_table = False
    
    def _handle_section_continuation(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState,
        completion_info: Dict[str, bool]
    ) -> None:
        """Handle continuation of current section."""
        if not parsing_state.current_section:
            # Create section if it doesn't exist
            parsing_state.current_section = PartialSection(
                code=self.last_section_code or f"section_{parsing_state.global_position_counters['section']}",
                accumulated_content=chunk,
                starts_incomplete=True
            )
            parsing_state.global_position_counters["section"] += 1
        else:
            parsing_state.current_section.accumulated_content += "\n" + chunk
        
        if extracted_content:
            parsing_state.current_section.update_from_extraction(extracted_content)
        
        # Update completion status
        if completion_info["section_complete"]:
            parsing_state.current_section.is_complete = True
    
    def _handle_element_start(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState,
        completion_info: Dict[str, bool]
    ) -> None:
        """Handle start of a new element."""
        # Ensure we have a section for this element
        if not parsing_state.current_section:
            parsing_state.current_section = PartialSection(
                code=self.last_section_code or f"section_{parsing_state.global_position_counters['section']}",
                label="Auto-created Section for Element",
                accumulated_content=""
            )
            parsing_state.global_position_counters["section"] += 1
        
        # Start new element
        parsing_state.current_element = PartialElement(
            accumulated_content=chunk
        )
        parsing_state.parsing_phase = "element"
        parsing_state.global_position_counters["element"] += 1
        
        if extracted_content:
            parsing_state.current_element.update_from_extraction(extracted_content)
        
        # Mark as complete if boundary detection indicates so
        if completion_info["element_complete"]:
            parsing_state.current_element.is_complete = True
        
        # Reset table processing state for new element
        self.processing_table = False
    
    def _handle_element_continuation(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState,
        completion_info: Dict[str, bool]
    ) -> None:
        """Handle continuation of current element."""
        if not parsing_state.current_element:
            # Ensure we have a section first
            if not parsing_state.current_section:
                parsing_state.current_section = PartialSection(
                    code=self.last_section_code or f"section_{parsing_state.global_position_counters['section']}",
                    label="Auto-created Section",
                    accumulated_content=""
                )
                parsing_state.global_position_counters["section"] += 1
            
            # Create element if it doesn't exist
            parsing_state.current_element = PartialElement(
                code=self.last_element_code or f"element_{parsing_state.global_position_counters['element']}",
                accumulated_content=chunk,
                starts_incomplete=True
            )
            parsing_state.global_position_counters["element"] += 1
        else:
            parsing_state.current_element.accumulated_content += "\n" + chunk
        
        if extracted_content:
            parsing_state.current_element.update_from_extraction(extracted_content)
        
        # Update completion status
        if completion_info["element_complete"]:
            parsing_state.current_element.is_complete = True
    
    def _handle_element_complete(
        self, 
        chunk: str, 
        extracted_content: Optional[Dict], 
        parsing_state: ParsingState,
        completion_info: Dict[str, bool]
    ) -> None:
        """Handle a complete element in a single chunk."""
        # Ensure we have a section for this element
        if not parsing_state.current_section:
            parsing_state.current_section = PartialSection(
                code=self.last_section_code or f"section_{parsing_state.global_position_counters['section']}",
                label="Auto-created Section for Complete Element",
                accumulated_content=""
            )
            parsing_state.global_position_counters["section"] += 1
        
        # Create a complete element
        parsing_state.current_element = PartialElement(
            accumulated_content=chunk,
            is_complete=True
        )
        parsing_state.parsing_phase = "element"
        parsing_state.global_position_counters["element"] += 1
        
        if extracted_content:
            parsing_state.current_element.update_from_extraction(extracted_content)
        
        # Since it's complete, finalize it immediately
        self._finalize_current_element(parsing_state)
        
        # Reset table processing state
        self.processing_table = False
    
    def _finalize_current_element(self, parsing_state: ParsingState) -> None:
        """Finalize the current element and add it to current section."""
        if not parsing_state.current_element:
            return
        
        self._log(f"Finalizing element: {parsing_state.current_element.code}")
        
        # Ensure we have a current section to add the element to
        if not parsing_state.current_section:
            parsing_state.current_section = PartialSection(
                code=f"section_{parsing_state.global_position_counters['section']}",
                label="Unlabeled Section",
                accumulated_content=""
            )
        
        # Convert PartialElement to dict and add to section
        if not parsing_state.current_section.elements:
            parsing_state.current_section.elements = []
        
        element_dict = parsing_state.current_element.dict(exclude={'accumulated_content', 'fragment_metadata'})
        
        # Save element checkpoint before adding to section
        if self.checkpoint_manager:
            try:
                from ...models.questionnaire import FullSectionElementSchema
                element_schema = FullSectionElementSchema(**element_dict)
                self.checkpoint_manager.save_element_checkpoint(
                    element_schema,
                    parsing_state.current_section.code or "unknown_section",
                    parsing_state.current_chunk_index,
                    additional_metadata={
                        "processing_phase": parsing_state.parsing_phase,
                        "global_element_position": parsing_state.global_position_counters["element"]
                    }
                )
            except Exception as e:
                self._log(f"Error saving element checkpoint: {e}")
        
        parsing_state.current_section.elements.append(element_dict)
        
        # Clear current element
        parsing_state.current_element = None
        parsing_state.parsing_phase = "section"
    
    def _finalize_current_section(self, parsing_state: ParsingState) -> None:
        """Finalize the current section and add it to completed sections."""
        if not parsing_state.current_section:
            return
        
        self._log(f"Finalizing section: {parsing_state.current_section.code}")
        
        # Finalize any remaining element
        if parsing_state.current_element:
            self._finalize_current_element(parsing_state)
        
        # Convert PartialSection to FullSectionResponseSchema and add to completed
        section_dict = parsing_state.current_section.dict(exclude={'accumulated_content', 'fragment_metadata'})
        
        # Create proper schema instance
        from ...models.questionnaire import FullSectionResponseSchema
        try:
            completed_section = FullSectionResponseSchema(**section_dict)
            
            # Save section checkpoint before adding to completed sections
            if self.checkpoint_manager:
                self.checkpoint_manager.save_section_checkpoint(
                    completed_section,
                    parsing_state.current_chunk_index,
                    additional_metadata={
                        "processing_phase": parsing_state.parsing_phase,
                        "global_section_position": parsing_state.global_position_counters["section"],
                        "elements_count": len(completed_section.elements or [])
                    }
                )
            
        except Exception as e:
            logging.exception(f"Error converting section to FullSectionResponseSchema: {e}")
            self._log(f"Error converting section to FullSectionResponseSchema: {e}")
            completed_section = FullSectionResponseSchema(
                code=parsing_state.current_section.code or f"section_{parsing_state.global_position_counters['section']}",
                label=parsing_state.current_section.label or "Untitled Section",
                position=parsing_state.current_section.position,
                notes=parsing_state.current_section.notes,
                elements=[]
            )
        
        parsing_state.completed_sections.append(completed_section)
        
        # Clear current section
        parsing_state.current_section = None
        parsing_state.parsing_phase = "global"
    
    def _handle_section_complete(
        self, 
        parsing_state: ParsingState,
        completion_info: Dict[str, bool]
    ) -> None:
        """Handle completion of current section."""
        if parsing_state.current_section:
            parsing_state.current_section.is_complete = True
        
        # Finalize the section
        self._finalize_current_section(parsing_state)
    
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
        
        # Update checkpoint information if checkpoint manager is available
        if self.checkpoint_manager and monitor:
            checkpoint_summary = self.checkpoint_manager.get_checkpoint_summary()
            monitor.update_checkpoint_info(
                checkpoint_summary["sections_saved"],
                checkpoint_summary["elements_saved"],
                checkpoint_summary
            )
