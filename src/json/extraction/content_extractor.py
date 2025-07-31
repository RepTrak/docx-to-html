"""
Service for extracting structured content from chunks using LLM.
"""

import logging
from typing import Optional, Dict
import re

from ...llm import LLMClient
from ...models.parsing_state import ChunkAnalysis, ChunkType, ParsingState
from ...models.questionnaire import FullSectionResponseSchema, FullSectionElementSchema, SectionsListResponseSchema
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
    
    def _detect_fragment_boundaries(self, chunk: str) -> Dict[str, bool]:
        """
        Detect if the chunk starts or ends in the middle of content.
        
        Returns:
            Dict with fragment boundary information
        """
        chunk_lines = chunk.split('\n')
        
        # Check if chunk starts mid-content
        starts_incomplete = False
        if chunk_lines and not chunk_lines[0].strip().startswith(('#', '**', '*', '|', '-')):
            # First line doesn't start with typical markdown markers
            starts_incomplete = True
        
        # Check if chunk ends mid-content
        ends_incomplete = False
        if chunk_lines:
            last_line = chunk_lines[-1].strip()
            # Check for incomplete patterns
            if (last_line and 
                not last_line.endswith(('|', '.', '?', '!', ':')) and
                not re.match(r'^#+\s', last_line) and  # Not a header
                not last_line.startswith('**') and    # Not a bold element start
                not last_line.startswith('*')):       # Not a list item
                ends_incomplete = True
        
        return {
            "starts_incomplete": starts_incomplete,
            "ends_incomplete": ends_incomplete,
            "is_fragment": starts_incomplete or ends_incomplete
        }
    
    def _build_fragment_context(
        self, 
        chunk: str, 
        analysis: ChunkAnalysis, 
        parsing_state: ParsingState
    ) -> Dict[str, str]:
        """Build context information for fragment processing."""
        fragment_info = self._detect_fragment_boundaries(chunk)
        
        context = {
            "chunk_position": f"{analysis.chunk_index + 1}/{parsing_state.total_chunks}",
            "chunk_type": analysis.chunk_type.value,
            "is_fragment": fragment_info["is_fragment"],
            "starts_incomplete": fragment_info["starts_incomplete"],
            "ends_incomplete": fragment_info["ends_incomplete"],
            "previous_context": "",
            "accumulated_content": "",
            "processing_instructions": ""
        }
        
        # Add context based on chunk type
        if analysis.chunk_type in [ChunkType.SECTION_START, ChunkType.SECTION_CONTINUATION]:
            if parsing_state.current_section:
                context["accumulated_content"] = parsing_state.current_section.accumulated_content
                context["previous_context"] = f"Current section: {parsing_state.current_section.code or 'Unknown'}"
            
            if fragment_info["starts_incomplete"]:
                context["processing_instructions"] += "This chunk starts mid-section. "
            if fragment_info["ends_incomplete"]:
                context["processing_instructions"] += "This chunk ends mid-section. "
                
        elif analysis.chunk_type in [ChunkType.ELEMENT_START, ChunkType.ELEMENT_CONTINUATION, ChunkType.ELEMENT_COMPLETE]:
            if parsing_state.current_element:
                context["accumulated_content"] = parsing_state.current_element.accumulated_content
                context["previous_context"] = f"Current element: {parsing_state.current_element.code or 'Unknown'}"
            
            if fragment_info["starts_incomplete"]:
                context["processing_instructions"] += "This chunk starts mid-element. "
            if fragment_info["ends_incomplete"]:
                context["processing_instructions"] += "This chunk ends mid-element. "
        
        return context
    
    def _create_enhanced_prompt(
        self, 
        chunk: str, 
        analysis: ChunkAnalysis, 
        parsing_state: ParsingState
    ) -> str:
        """Create an enhanced prompt that handles chunk fragments."""
        context = self._build_fragment_context(chunk, analysis, parsing_state)
        
        # Determine expected schema
        expected_schema = ""
        if analysis.chunk_type in [ChunkType.SECTION_START, ChunkType.SECTION_CONTINUATION]:
            expected_schema = "FullSectionResponseSchema"
        elif analysis.chunk_type in [ChunkType.ELEMENT_START, ChunkType.ELEMENT_CONTINUATION, ChunkType.ELEMENT_COMPLETE]:
            expected_schema = "FullSectionElementSchema"
        
        enhanced_prompt = f"""
# CHUNK FRAGMENT PROCESSING

## Fragment Context
- **Position**: {context['chunk_position']}
- **Type**: {context['chunk_type']}
- **Is Fragment**: {context['is_fragment']}
- **Starts Incomplete**: {context['starts_incomplete']}
- **Ends Incomplete**: {context['ends_incomplete']}
- **Previous Context**: {context['previous_context']}

## Processing Instructions
{context['processing_instructions']}

**CRITICAL**: This chunk may contain partial content that started in previous chunks or continues in next chunks. Extract what you can identify with certainty, but mark incomplete content appropriately.

## Accumulated Content (from previous chunks)
```
{context['accumulated_content']}
```

## Current Chunk Content
```
{chunk}
```

## Instructions for Fragment Processing
1. **If content starts incomplete**: Treat this as continuation of previous content
2. **If content ends incomplete**: Mark the extracted content as potentially incomplete
3. **Identify complete elements**: Extract any sections/elements that are fully contained
4. **Preserve fragment boundaries**: Don't assume content is complete if it appears cut off
5. **Merge with accumulated content**: Combine with previous chunks when appropriate

## Expected Output Schema
{expected_schema}

## Fragment-Aware Extraction Rules
- Extract only content you can identify with high confidence
- If a section/element appears incomplete, include what you have but mark as partial
- Pay attention to markdown patterns that indicate boundaries (headers, bold text, tables)
- Consider the chunk overlap when determining if content is repeated
- Maintain exact text formatting and codes as they appear

Extract structured content while being aware this is a fragment of larger content.
"""
        
        return enhanced_prompt
    
    def extract_content(
        self, 
        chunk: str, 
        analysis: ChunkAnalysis, 
        parsing_state: ParsingState,
        monitor: Optional[ProcessingMonitor] = None
    ) -> Optional[Dict]:
        """Extract structured content from a chunk based on analysis."""
        
        # Create enhanced prompt for fragment processing
        enhanced_prompt = self._create_enhanced_prompt(chunk, analysis, parsing_state)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        try:
            # Use appropriate response format based on content type
            if analysis.chunk_type in [ChunkType.SECTION_START, ChunkType.SECTION_CONTINUATION]:
                response_format = FullSectionResponseSchema
            else:
                response_format = FullSectionElementSchema
            
            self._log(f"Extracting content from chunk {analysis.chunk_index} (type: {analysis.chunk_type.value})")
            
            response = self.llm_client.completion(
                messages=messages,
                response_format=response_format,
                provider=self.provider,
                model=self.model,
                temperature=0.1,
                max_tokens=8192
            )
            
            if 'parsed' in response and response['parsed']:
                extracted_data = response['parsed'].dict()
                
                # Add fragment metadata to extracted content
                fragment_info = self._detect_fragment_boundaries(chunk)
                extracted_data['_fragment_metadata'] = {
                    'chunk_index': analysis.chunk_index,
                    'is_fragment': fragment_info['is_fragment'],
                    'starts_incomplete': fragment_info['starts_incomplete'],
                    'ends_incomplete': fragment_info['ends_incomplete'],
                    'confidence': analysis.confidence  # Fixed: use 'confidence' not 'confidence_score'
                }
                
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
                
                self._log(f"Successfully extracted content from chunk {analysis.chunk_index}")
                return extracted_data
            
        except Exception as e:
            logging.exception(f"Error extracting content from chunk {analysis.chunk_index}: {e}")
            error_msg = f"Error extracting content from chunk {analysis.chunk_index}: {e}"
            self._log(error_msg)
            if monitor:
                monitor.add_error(error_msg)
        
        return None
    
    def extract_partial_content(
        self,
        chunk: str,
        chunk_index: int,
        total_chunks: int,
        accumulated_content: str = "",
        content_type: str = "UNKNOWN"
    ) -> Optional[Dict]:
        """
        Extract partial content from a chunk fragment.
        Used for emergency content recovery when normal processing fails.
        """
        simple_prompt = f"""
Extract any identifiable questionnaire content from this text fragment.

**Fragment Info**:
- Chunk {chunk_index + 1} of {total_chunks}
- Content Type: {content_type}
- Has Accumulated Content: {bool(accumulated_content)}

**Accumulated Content**:
{accumulated_content}

**Current Fragment**:
{chunk}

**Instructions**:
1. Extract any complete sections
2. Extract any complete elements
3. Extract any partial content that can be identified
4. Preserve exact text and formatting
5. Don't make assumptions about incomplete content

Return any structured content you can identify with confidence.
"""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": simple_prompt}
        ]
        
        try:
            response = self.llm_client.completion(
                messages=messages,
                provider=self.provider,
                model=self.model,
                response_format=SectionsListResponseSchema,
                # temperature=0.0,
                # max_tokens=4096
            )
            
            if response and 'content' in response:
                return {
                    'partial_content': response['content'],
                    'chunk_index': chunk_index,
                    'extraction_method': 'partial_recovery'
                }
                
        except Exception as e:
            self._log(f"Error in partial content extraction: {e}")
        
        return None
