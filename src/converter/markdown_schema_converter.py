"""
Converts markdown chunks to FullSurveyResponseSchema using LLM providers.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime

from ..llm.client import LLMClient
from ..models.questionnaire import FullSurveyResponseSchema, FullSectionResponseSchema
from ..conversion.markdown_splitter import MarkdownTextSplitter, SplitResult

from .schema_models import ProcessingStats
from .chunk_processor import ChunkProcessor
from .state_manager import StateManager, ConversionState
from .result_saver import ResultSaver

logger = logging.getLogger(__name__)


class MarkdownToSchemaConverter:
    """Converts markdown content to FullSurveyResponseSchema using LLM providers."""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        model: str = "gpt-4o-mini",
        provider: str = "openai",
        temperature: float = 0.0,
        max_tokens: int = 4000,
        verbose: bool = True,
        progress_callback: Optional[Callable[[ProcessingStats], None]] = None
    ):
        """
        Initialize the converter.
        
        Args:
            llm_client: LLM client instance (creates default if None)
            model: Model to use for processing
            provider: Provider to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
            verbose: Enable verbose logging
            progress_callback: Function to call with progress updates
        """
        self.verbose = verbose
        self.progress_callback = progress_callback
        
        # Initialize components
        self.chunk_processor = ChunkProcessor(
            llm_client=llm_client,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            verbose=verbose
        )
        self.state_manager = StateManager(verbose=verbose)
        self.result_saver = ResultSaver(verbose=verbose)
        
        # Processing statistics
        self.stats = ProcessingStats()
    
    def _log(self, message: str, level: str = "info") -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            getattr(logger, level, logger.info)(f"[MarkdownConverter] {message}")
    
    def convert_from_split_result(self, split_result: SplitResult) -> FullSurveyResponseSchema:
        """
        Convert chunks from a SplitResult to FullSurveyResponseSchema.
        
        Args:
            split_result: Result from MarkdownTextSplitter
            
        Returns:
            Complete survey schema
        """
        if not split_result.success or not split_result.chunks:
            raise ValueError("Invalid split result provided")
        
        return self.convert_from_chunks(split_result.chunks, split_result.structure_map)

    def _sort_and_reorder_positions(self, sections: List[FullSectionResponseSchema]) -> List[FullSectionResponseSchema]:
        """
        Sort sections and elements by position and renumber them sequentially.
        
        Args:
            sections: List of sections to sort and reorder
            
        Returns:
            Sections with sorted and renumbered positions
        """
        # Sort sections by position (handle None positions by putting them at the end)
        sections.sort(key=lambda s: s.position if s.position is not None else float('inf'))
        
        # Renumber section positions starting from 1
        for i, section in enumerate(sections, 1):
            section.position = i
            
            # Sort and renumber elements within each section
            if section.elements:
                # Sort elements by position (handle None positions by putting them at the end)
                section.elements.sort(key=lambda e: e.position if e.position is not None else float('inf'))
                
                # Renumber element positions starting from 1
                for j, element in enumerate(section.elements, 1):
                    element.position = j
                    
                    # Sort and renumber variables within each element
                    if element.variables:
                        element.variables.sort(key=lambda v: v.position if v.position is not None else float('inf'))
                        for k, variable in enumerate(element.variables, 1):
                            variable.position = k
                    
                    # Sort and renumber columns within each element
                    if element.columns:
                        element.columns.sort(key=lambda c: c.position if c.position is not None else float('inf'))
                        for k, column in enumerate(element.columns, 1):
                            column.position = k
        
        self._log(f"Sorted and reordered {len(sections)} sections with their elements")
        return sections

    def convert_from_chunks(self, chunks: List[str], structure_map: Optional[Dict[str, Any]] = None) -> FullSurveyResponseSchema:
        """
        Convert markdown chunks to FullSurveyResponseSchema.
        
        Args:
            chunks: List of markdown chunks
            structure_map: Optional structure information
            
        Returns:
            Complete survey schema
        """
        start_time = datetime.now()
        
        # Initialize processing
        self.stats = ProcessingStats()
        self.stats.total_chunks = len(chunks)
        self.state_manager.reset_state()
        
        self._log(f"Starting conversion of {len(chunks)} chunks to survey schema")
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            try:
                self._log(f"Processing chunk {i + 1}/{len(chunks)}")
                
                # Get current context
                context = self.state_manager.get_context()
                
                # Process chunk with LLM
                extraction = self.chunk_processor.process_chunk(
                    chunk, i, len(chunks), context, self.stats
                )
                
                # Update state based on extraction
                if extraction.chunk_type != 'error':
                    self.state_manager.update_from_extraction(extraction, chunk, self.stats)
                
                self.stats.processed_chunks += 1
                
                # Call progress callback if provided
                if self.progress_callback:
                    self.progress_callback(self.stats)
                    
            except Exception as e:
                error_msg = f"Error processing chunk {i}: {str(e)}"
                self._log(error_msg, "error")
                self.stats.errors.append(error_msg)
                continue
        
        # Finalize conversion
        completed_sections = self.state_manager.finalize_conversion()
        
        # Sort and reorder positions before creating final schema
        completed_sections = self._sort_and_reorder_positions(completed_sections)
        
        # Calculate processing time
        self.stats.processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create final survey schema
        survey = FullSurveyResponseSchema(sections=completed_sections)
        
        self._log(f"Conversion completed: {len(completed_sections)} sections, "
                 f"{self.stats.elements_created} elements, {self.stats.processing_time:.2f}s")
        
        return survey

    def convert_markdown_content(self, markdown_content: str, split_delimiter: str = r'\\\*\\\*\\\*') -> FullSurveyResponseSchema:
        """
        Convert markdown content to schema by first splitting then processing.
        
        Args:
            markdown_content: Raw markdown content
            split_delimiter: Delimiter pattern for splitting
            
        Returns:
            Complete survey schema
        """
        # Split the content
        splitter = MarkdownTextSplitter(
            primary_delimiter=split_delimiter,
            verbose=self.verbose
        )
        
        split_result = splitter.split_text(markdown_content)
        
        if not split_result.success:
            raise ValueError(f"Failed to split markdown content: {split_result.error_message}")
        
        # Convert the chunks
        return self.convert_from_split_result(split_result)

    def get_processing_stats(self) -> ProcessingStats:
        """Get current processing statistics."""
        return self.stats

    def get_conversion_state(self):
        """Get current conversion state."""
        return self.state_manager.get_state()

    def save_results(self, survey: FullSurveyResponseSchema, output_dir: Union[str, Path], filename_prefix: str = "survey") -> Dict[str, Path]:
        """
        Save conversion results to files.
        
        Args:
            survey: The converted survey schema
            output_dir: Directory to save files
            filename_prefix: Prefix for output files
            
        Returns:
            Dictionary of saved file paths
        """
        return self.result_saver.save_results(survey, self.stats, output_dir, filename_prefix)
