"""
Service for extracting structured content from chunks using LLM.
"""

from typing import Optional, Dict

from ...llm import LLMClient
from ...models.parsing_state import ChunkAnalysis, ChunkType, ParsingState
from ...models.questionnaire import FullSectionResponseSchema, FullSectionElementSchema
from ...models.monitoring import ProcessingMonitor


class ContentExtractor:
    """Service for extracting structured content from chunks."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        extraction_prompt_template: str,
        provider: str = "openai",
        model: str = "gpt-4o-mini-2024-07-18",
        verbose: bool = False
    ):
        """
        Initialize the content extractor.
        
        Args:
            llm_client: LLM client instance
            system_prompt: System prompt for extraction
            extraction_prompt_template: Template for extraction prompts
            provider: LLM provider to use
            model: LLM model to use
            verbose: Enable verbose logging
        """
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.extraction_prompt_template = extraction_prompt_template
        self.provider = provider
        self.model = model
        self.verbose = verbose
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def extract_content(
        self, 
        chunk: str, 
        analysis: ChunkAnalysis, 
        parsing_state: ParsingState,
        monitor: Optional[ProcessingMonitor] = None
    ) -> Optional[Dict]:
        """Extract structured content from a chunk based on analysis."""
        
        context = f"Chunk {analysis.chunk_index}, Type: {analysis.chunk_type}"
        accumulated_content = ""
        expected_schema = ""
        
        if analysis.chunk_type in [ChunkType.SECTION_START, ChunkType.SECTION_CONTINUATION]:
            if parsing_state.current_section:
                accumulated_content = parsing_state.current_section.accumulated_content
            expected_schema = "FullSectionResponseSchema"
        elif analysis.chunk_type in [ChunkType.ELEMENT_START, ChunkType.ELEMENT_CONTINUATION, ChunkType.ELEMENT_COMPLETE]:
            if parsing_state.current_element:
                accumulated_content = parsing_state.current_element.accumulated_content
            expected_schema = "FullSectionElementSchema"
        
        prompt = self.extraction_prompt_template.format(
            context=context,
            content_type=analysis.chunk_type,
            accumulated_content=accumulated_content,
            chunk_content=chunk,
            expected_schema=expected_schema
        )
        
        messages = [
            {"role": "assistant", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Use appropriate response format based on content type
            if analysis.chunk_type in [ChunkType.SECTION_START, ChunkType.SECTION_CONTINUATION]:
                response_format = FullSectionResponseSchema
            else:
                response_format = FullSectionElementSchema
            
            response = self.llm_client.completion(
                messages=messages,
                response_format=response_format,
                provider=self.provider,
                model=self.model,
                temperature=0.1,
                max_tokens=8192
            )
            
            if 'parsed' in response and response['parsed']:
                # Update monitoring if provided
                if monitor:
                    monitor.complete_chunk_extraction(analysis.chunk_index)
                    
                    # Track token usage if available
                    if 'usage' in response:
                        usage = response['usage']
                        monitor.update_token_usage(
                            usage.get('prompt_tokens', 0),
                            usage.get('completion_tokens', 0)
                        )
                
                return response['parsed'].dict()
            
        except Exception as e:
            self._log(f"Error extracting content from chunk {analysis.chunk_index}: {e}")
            if monitor:
                monitor.add_error(f"Extraction error in chunk {analysis.chunk_index}: {str(e)}")
        
        return None
