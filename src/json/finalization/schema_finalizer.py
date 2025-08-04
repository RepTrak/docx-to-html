"""
Service for finalizing partial objects into complete schemas.
"""

from typing import Optional

from ...models.parsing_state import ParsingState, PartialElement
from ...models.questionnaire import FullSectionResponseSchema, FullSectionElementSchema
from ...models.monitoring import ProcessingMonitor


class SchemaFinalizer:
    """Service for finalizing partial objects into complete schemas."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the schema finalizer.
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def finalize_current_element(
        self, 
        parsing_state: ParsingState,
        monitor: Optional[ProcessingMonitor] = None
    ) -> None:
        """Finalize current element and add to current section."""
        if not parsing_state.current_element:
            return
        
        # Convert partial element to full schema
        element_data = {
            "code": parsing_state.current_element.code or f"element_{parsing_state.global_position_counters['element']}",
            "label": parsing_state.current_element.label or "Untitled Element",
            "type": parsing_state.current_element.type or "CHOICE",
            "position": parsing_state.current_element.position or parsing_state.global_position_counters["element"],
            "notes": parsing_state.current_element.notes,
            "revision": parsing_state.current_element.revision,
            "tags": parsing_state.current_element.tags,
            "is_loop_target": parsing_state.current_element.is_loop_target,
            "help_text": parsing_state.current_element.help_text,
            "variables": parsing_state.current_element.variables,
            "columns": parsing_state.current_element.columns
        }
        
        try:
            element = FullSectionElementSchema(**element_data)
            
            # Add to current section
            if parsing_state.current_section:
                if not hasattr(parsing_state.current_section, 'elements') or parsing_state.current_section.elements is None:
                    parsing_state.current_section.elements = []
                parsing_state.current_section.elements.append(PartialElement(**element.dict()))
            
        except Exception as e:
            self._log(f"Error finalizing element: {e}")
            if monitor:
                monitor.add_error(f"Error finalizing element: {str(e)}")
        
        # Clear current element
        parsing_state.current_element = None
    
    def finalize_current_section(
        self, 
        parsing_state: ParsingState,
        monitor: Optional[ProcessingMonitor] = None
    ) -> None:
        """Finalize current section and add to completed sections."""
        if not parsing_state.current_section:
            return
        
        # Finalize any pending element
        if parsing_state.current_element:
            self.finalize_current_element(parsing_state, monitor)
        
        # Convert partial elements to full schemas
        elements = []
        if parsing_state.current_section.elements:
            for partial_elem in parsing_state.current_section.elements:
                if isinstance(partial_elem, PartialElement):
                    elem_data = {
                        "code": partial_elem.code or f"element_{len(elements) + 1}",
                        "label": partial_elem.label or "Untitled Element",
                        "type": partial_elem.type or "CHOICE",
                        "position": partial_elem.position or len(elements) + 1,
                        "notes": partial_elem.notes,
                        "revision": partial_elem.revision,
                        "tags": partial_elem.tags,
                        "is_loop_target": partial_elem.is_loop_target,
                        "help_text": partial_elem.help_text,
                        "variables": partial_elem.variables,
                        "columns": partial_elem.columns
                    }
                    try:
                        elements.append(FullSectionElementSchema(**elem_data))
                    except Exception as e:
                        self._log(f"Error converting partial element: {e}")
                        if monitor:
                            monitor.add_error(f"Error converting partial element: {str(e)}")
        
        # Create full section
        section_data = {
            "code": parsing_state.current_section.code or f"section_{parsing_state.global_position_counters['section']}",
            "label": parsing_state.current_section.label or "Untitled Section",
            "position": parsing_state.current_section.position or parsing_state.global_position_counters["section"],
            "notes": parsing_state.current_section.notes,
            "loop": parsing_state.current_section.loop,
            "elements": elements
        }
        
        try:
            section = FullSectionResponseSchema(**section_data)
            parsing_state.completed_sections.append(section)
            
            # Update monitoring
            if monitor:
                monitor.add_completed_section(section.dict())
            
        except Exception as e:
            self._log(f"Error finalizing section: {e}")
            if monitor:
                monitor.add_error(f"Error finalizing section: {str(e)}")
        
        # Clear current section
        parsing_state.current_section = None
