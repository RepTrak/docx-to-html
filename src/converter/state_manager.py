"""
Manages the state of markdown to schema conversion process.
"""

import logging
from typing import List, Optional

from ..models.questionnaire import (
    FullSectionResponseSchema, 
    FullSectionElementSchema,
    VariableResponseSchema,
    GridColumnSchema
)
from .schema_models import ConversionState, ProcessingStats, ChunkExtractionResult

logger = logging.getLogger(__name__)


class StateManager:
    """Manages conversion state and updates based on chunk extractions."""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the state manager.
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.state = ConversionState()
        
    def _log(self, message: str, level: str = "info") -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            getattr(logger, level, logger.info)(f"[StateManager] {message}")
    
    def reset_state(self) -> None:
        """Reset the conversion state."""
        self.state = ConversionState()
    
    def get_context(self) -> dict:
        """Get current context for chunk processing."""
        return {
            'last_chunk_type': self.state.last_chunk_type,
            'current_section_code': self.state.current_section.code if self.state.current_section else None,
            'current_element_code': self.state.current_element.code if self.state.current_element else None,
            'accumulated_content': self.state.accumulated_content
        }
    
    def update_from_extraction(
        self, 
        extraction: ChunkExtractionResult, 
        chunk_content: str, 
        stats: ProcessingStats
    ) -> None:
        """
        Update processing state based on LLM extraction.
        
        Args:
            extraction: The extraction result from chunk processing
            chunk_content: Original chunk content
            stats: Processing statistics to update
        """
        if extraction.error:
            return
            
        # Update chunk type tracking
        self.state.last_chunk_type = extraction.chunk_type
        
        # Handle accumulated content
        if extraction.requires_continuation:
            self.state.accumulated_content += "\n" + chunk_content
        elif extraction.partial_content:
            self.state.accumulated_content = extraction.partial_content
        else:
            self.state.accumulated_content = ""
        
        # Process extracted sections
        self._process_sections(extraction.extracted_sections, stats)
        
        # Process extracted elements
        self._process_elements(extraction.extracted_elements, stats)
    
    def _process_sections(self, sections_data: List[dict], stats: ProcessingStats) -> None:
        """Process extracted sections data."""
        for section_data in sections_data:
            try:
                section = FullSectionResponseSchema(
                    code=section_data['code'],
                    label=section_data['label'],
                    notes=section_data.get('notes'),
                    position=section_data.get('position', self.state.section_position_counter + 1),
                    elements=[]
                )
                
                # Finalize current section if exists
                if self.state.current_section:
                    self.state.completed_sections.append(self.state.current_section)
                
                self.state.current_section = section
                self.state.section_position_counter += 1
                # Reset element position counter for new section
                self.state.element_position_counter = 0
                stats.sections_created += 1
                
                self._log(f"Created section: {section.code}")
                
            except Exception as e:
                error_msg = f"Error creating section from extraction: {str(e)}"
                self._log(error_msg, "error")
                stats.errors.append(error_msg)
    
    def _process_elements(self, elements_data: List[dict], stats: ProcessingStats) -> None:
        """Process extracted elements data."""
        for element_data in elements_data:
            try:
                # Create variables
                variables = self._create_variables(element_data.get('variables', []), stats)
                
                # Create columns
                columns = self._create_columns(element_data.get('columns', []), stats)
                
                # Calculate position relative to current section
                next_position = self.state.element_position_counter + 1
                
                # Create element
                element = FullSectionElementSchema(
                    code=element_data['code'],
                    label=element_data['label'],
                    type=element_data.get('type', 'CHOICE'),
                    position=element_data.get('position', next_position),
                    notes=element_data.get('notes'),
                    help_text=element_data.get('help_text'),
                    variables=variables if variables else None,
                    columns=columns if columns else None,
                    section=None  # Will be set when added to section
                )
                
                # Add to current section
                if self.state.current_section:
                    if not self.state.current_section.elements:
                        self.state.current_section.elements = []
                    self.state.current_section.elements.append(element)
                    self.state.element_position_counter += 1
                    stats.elements_created += 1
                    
                    self._log(f"Created element: {element.code} (position {element.position}) in section {self.state.current_section.code}")
                else:
                    warning_msg = f"Element {element.code} created but no current section available"
                    self._log(warning_msg, "warning")
                    stats.warnings.append(warning_msg)
                
            except Exception as e:
                error_msg = f"Error creating element from extraction: {str(e)}"
                self._log(error_msg, "error")
                stats.errors.append(error_msg)
    
    def _create_variables(self, variables_data: List[dict], stats: ProcessingStats) -> List[VariableResponseSchema]:
        """Create variable objects from data."""
        variables = []
        for var_data in variables_data:
            variable = VariableResponseSchema(
                code=var_data['code'],
                label=var_data['label'],
                notes=var_data.get('notes'),
                position=var_data.get('position')
            )
            variables.append(variable)
            stats.variables_created += 1
        return variables
    
    def _create_columns(self, columns_data: List[dict], stats: ProcessingStats) -> List[GridColumnSchema]:
        """Create column objects from data."""
        columns = []
        for col_data in columns_data:
            column = GridColumnSchema(
                code=int(col_data['code']),
                label=col_data['label'],
                position=col_data.get('position', len(columns) + 1),
                notes=col_data.get('notes')
            )
            columns.append(column)
            stats.columns_created += 1
        return columns
    
    def finalize_conversion(self) -> List[FullSectionResponseSchema]:
        """Finalize conversion and return all sections."""
        # Add any remaining current section
        if self.state.current_section:
            self.state.completed_sections.append(self.state.current_section)
            self.state.current_section = None
        
        return self.state.completed_sections
    
    def get_state(self) -> ConversionState:
        """Get current conversion state."""
        return self.state
