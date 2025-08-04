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
from .extraction_logger import ExtractionLogger


class ContentExtractor:
    """Service for extracting structured content from chunks."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        extraction_prompt_template: str,
        provider: str = "openai",
        model: str = "gpt-4o-mini-2024-07-18",
        verbose: bool = True,
        debug_prompts: bool = True,
        prompt_log_dir: str = "extraction_debug_logs"
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
            debug_prompts: Enable prompt debugging/logging
            prompt_log_dir: Directory for saving debug logs
        """
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.extraction_prompt_template = extraction_prompt_template
        self.provider = provider
        self.model = model
        self.verbose = verbose
        self.debug_prompts = debug_prompts
        self.extraction_logger = ExtractionLogger(prompt_log_dir, enabled=debug_prompts)
        
        # Counters for debugging session
        self.fragment_count = 0
        self.continuity_decisions = 0
        self.successful_extractions = 0
        self.failed_extractions = 0
        self.total_token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        
        if self.debug_prompts:
            self._log(f"Extraction debugging enabled. Logs will be saved to: {self.extraction_logger.get_session_path()}")
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def _detect_fragment_boundaries(self, chunk: str) -> Dict[str, bool]:
        """
        Detect fragment boundaries for delimiter-based chunks.
        """
        # For delimiter strategy, chunks are typically complete units
        # separated by *** so they should be less fragmented
        
        chunk_lines = chunk.split('\n')
        
        # Check if chunk starts with typical content markers
        starts_incomplete = False
        if chunk_lines:
            first_line = chunk_lines[0].strip()
            # If it doesn't start with clear markers, it might be incomplete
            if (first_line and 
                not first_line.startswith(('#', '**', '*', '|', '-')) and
                not re.match(r'^[A-Z_]+:', first_line)):  # Check for element codes
                starts_incomplete = True
        
        # Check if chunk ends incomplete
        ends_incomplete = False
        if chunk_lines:
            last_line = chunk_lines[-1].strip()
            # For delimiter chunks, they should typically be complete
            # But check for obvious incomplete patterns
            if (last_line and 
                not last_line.endswith(('|', '.', '?', '!', ':')) and
                last_line.count('|') == 1):  # Incomplete table row
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
        
        # Log fragment processing if debugging enabled
        if self.debug_prompts:
            self.fragment_count += 1
            self.extraction_logger.log_fragment_processing(
                chunk_index=analysis.chunk_index,
                fragment_context={
                    "chunk_position": f"{analysis.chunk_index + 1}/{parsing_state.total_chunks}",
                    "chunk_type": analysis.chunk_type.value,
                    "parsing_phase": parsing_state.parsing_phase
                },
                boundary_detection=fragment_info,
                continuity_analysis={
                    "current_section_code": parsing_state.current_section.code if parsing_state.current_section else None,
                    "current_element_code": parsing_state.current_element.code if parsing_state.current_element else None,
                    "has_accumulated_section_content": bool(parsing_state.current_section and parsing_state.current_section.accumulated_content),
                    "has_accumulated_element_content": bool(parsing_state.current_element and parsing_state.current_element.accumulated_content)
                }
            )
        
        context = {
            "chunk_position": f"{analysis.chunk_index + 1}/{parsing_state.total_chunks}",
            "chunk_type": analysis.chunk_type.value,
            "is_fragment": fragment_info["is_fragment"],
            "starts_incomplete": fragment_info["starts_incomplete"],
            "ends_incomplete": fragment_info["ends_incomplete"],
            "previous_context": "",
            "accumulated_content": "",
            "processing_instructions": "",
            "completion_guidance": "",
            "continuity_info": ""
        }
        
        # Detect table content
        has_table = '|' in chunk
        is_table_continuation = (has_table and 
                                fragment_info["starts_incomplete"] and 
                                not chunk.strip().startswith('#') and 
                                not re.match(r'^\*\*[^*]+\*\*:', chunk.strip()))
        
        # Add context based on chunk type and current state
        if analysis.chunk_type in [ChunkType.SECTION_START, ChunkType.SECTION_CONTINUATION]:
            if parsing_state.current_section:
                context["accumulated_content"] = parsing_state.current_section.accumulated_content
                context["previous_context"] = f"Current section: {parsing_state.current_section.code or 'Unknown'}"
                
                # Add completion guidance
                if parsing_state.current_section.starts_incomplete:
                    context["completion_guidance"] += "Continue building on incomplete section from previous chunks. "
                if fragment_info["ends_incomplete"]:
                    context["completion_guidance"] += "Mark section as incomplete if it appears to continue in next chunk. "
            
            if fragment_info["starts_incomplete"]:
                context["processing_instructions"] += "This chunk starts mid-section. Merge with accumulated content. "
            if fragment_info["ends_incomplete"]:
                context["processing_instructions"] += "This chunk ends mid-section. Extract partial content. "
                
        elif analysis.chunk_type in [ChunkType.ELEMENT_START, ChunkType.ELEMENT_CONTINUATION, ChunkType.ELEMENT_COMPLETE]:
            if parsing_state.current_element:
                context["accumulated_content"] = parsing_state.current_element.accumulated_content
                context["previous_context"] = f"Current element: {parsing_state.current_element.code or 'Unknown'}"
                
                # Add completion guidance
                if parsing_state.current_element.starts_incomplete:
                    context["completion_guidance"] += "Continue building on incomplete element from previous chunks. "
                if fragment_info["ends_incomplete"]:
                    context["completion_guidance"] += "Mark element as incomplete if it appears to continue in next chunk. "
            
            if fragment_info["starts_incomplete"]:
                context["processing_instructions"] += "This chunk starts mid-element. Merge with accumulated content. "
            if fragment_info["ends_incomplete"]:
                context["processing_instructions"] += "This chunk ends mid-element. Extract partial content. "
        
        elif analysis.chunk_type == ChunkType.UNKNOWN:
            # Special handling for unknown chunks that might be table continuations
            if is_table_continuation:
                context["continuity_info"] = "LIKELY TABLE CONTINUATION: "
                if parsing_state.current_element:
                    context["accumulated_content"] = parsing_state.current_element.accumulated_content
                    context["previous_context"] = f"Current element: {parsing_state.current_element.code or 'Unknown'}"
                    context["processing_instructions"] += "This appears to be a table continuation for the current element. "
                    context["completion_guidance"] += "Add variables/columns to the current element. "
                elif parsing_state.current_section:
                    context["accumulated_content"] = parsing_state.current_section.accumulated_content
                    context["previous_context"] = f"Current section: {parsing_state.current_section.code or 'Unknown'}"
                    context["processing_instructions"] += "This appears to be element content for the current section. "
                    context["completion_guidance"] += "Create or continue an element within the current section. "
            else:
                context["processing_instructions"] += "Unknown chunk type - extract any identifiable content. "
        
        # Log continuity decisions
        if self.debug_prompts and fragment_info["is_fragment"]:
            self.continuity_decisions += 1
            decision_type = "fragment_processing"
            reasoning = f"Fragment detected: starts_incomplete={fragment_info['starts_incomplete']}, ends_incomplete={fragment_info['ends_incomplete']}"
            
            context_factors = {
                "has_table": '|' in chunk,
                "current_section": parsing_state.current_section.code if parsing_state.current_section else None,
                "current_element": parsing_state.current_element.code if parsing_state.current_element else None,
                "chunk_type": analysis.chunk_type.value
            }
            
            outcome = {
                "processing_instructions": context["processing_instructions"],
                "completion_guidance": context["completion_guidance"],
                "continuity_info": context["continuity_info"]
            }
            
            self.extraction_logger.log_continuity_decision(
                chunk_index=analysis.chunk_index,
                decision_type=decision_type,
                reasoning=reasoning,
                context_factors=context_factors,
                outcome=outcome
            )
        
        return context
    
    def _create_enhanced_prompt(
        self, 
        chunk: str, 
        analysis: ChunkAnalysis, 
        parsing_state: ParsingState
    ) -> str:
        """Create enhanced prompt for delimiter-based chunks."""
        context = self._build_fragment_context(chunk, analysis, parsing_state)
        
        # For delimiter chunks, provide specific guidance
        delimiter_guidance = """
## DELIMITER CHUNK PROCESSING

This chunk was separated by `***` delimiter from the original document.
Each delimiter-separated chunk typically contains:
- A complete element (question, instruction, or content block)
- Complete table sections with variables or columns
- Programming notes and instructions

**Processing Instructions for Delimiter Chunks:**
1. Treat each chunk as a potentially complete unit
2. Look for element headers: `**ElementCode**:` 
3. Extract complete variable/column tables
4. Preserve all programming notes and instructions
5. Maintain exact formatting and codes
"""
        
        enhanced_prompt = f"""
{delimiter_guidance}

## Fragment Context
- **Position**: {context['chunk_position']}
- **Type**: {context['chunk_type']}
- **Previous Context**: {context['previous_context']}

## Current Delimiter-Separated Chunk
```
{chunk}
```

## Processing Notes
- This chunk was separated by *** delimiter
- Extract all identifiable content structures
- Preserve exact codes and formatting
- Handle complete elements when possible

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
        
        system_prompt = f"""
{self.system_prompt}
# QUESTIONNAIRE CHUNK PROCESSING WITH CONTINUITY

**Chunks have overlapping content and may start or end mid-section/element, and the first content is the same of the las part of the content of the previous chunk**

## CRITICAL CONTINUITY RULES

### Parent-Child Relationships:
1. **Variables and Columns ALWAYS belong to the current/last element**
2. **Elements ALWAYS belong to the current/last section**
3. **If processing table data without clear element header, continue the last element**
4. **Maintain exact codes and positioning from accumulated content**

### Content Continuation Strategy:
- **Table Continuation**: If chunk contains `|` characters and starts incomplete, treat as variable/column data for current element
- **Element Continuation**: If no new element header (`**code**:`), continue building current element
- **Section Continuation**: If no new section header (`# Section`), continue building current section

## Fragment Processing Priorities
1. **Merge with accumulated content** when starts_incomplete=true
2. **Extract complete structures** when identifiable
3. **Preserve exact formatting** and codes as written
4. **Maintain parent-child relationships** (variables→element→section)
5. **Handle table continuations** by adding to current element

**IMPORTANT**: If this chunk appears to be a table continuation (has `|` characters and starts incomplete), focus on extracting variables/columns and adding them to the current element context from accumulated content.


## SPECIFIC EXTRACTION RULES

### For Table Continuations:
- Identify if this is a **VARIABLES TABLE** (with columns like "Variable Name", "Variable Label")
- Identify if this is a **COLUMNS TABLE** (with columns like "Value Code", "Value Label")
- Extract rows and add to current element's variables or columns array
- Preserve exact codes and labels as they appear
- Maintain position ordering

### For Element Continuations:
- Build upon existing element data from accumulated content
- Add any new variables/columns found
- Update notes with additional programming instructions
- Preserve element type and core properties

### For Section Continuations:
- Add any new elements found to current section
- Update section notes with additional content
- Maintain section hierarchy and positioning
        """
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": enhanced_prompt}
        ]
        
        # Log extraction prompt if debugging enabled
        if self.debug_prompts:
            parsing_state_dict = {
                "parsing_phase": parsing_state.parsing_phase,
                "total_chunks": getattr(parsing_state, 'total_chunks', 0),
                "current_section": {
                    "code": parsing_state.current_section.code if parsing_state.current_section else None,
                    "accumulated_content": parsing_state.current_section.accumulated_content if parsing_state.current_section else None,
                    "starts_incomplete": getattr(parsing_state.current_section, 'starts_incomplete', False) if parsing_state.current_section else False
                },
                "current_element": {
                    "code": parsing_state.current_element.code if parsing_state.current_element else None,
                    "accumulated_content": parsing_state.current_element.accumulated_content if parsing_state.current_element else None,
                    "starts_incomplete": getattr(parsing_state.current_element, 'starts_incomplete', False) if parsing_state.current_element else False
                },
                "last_chunk_type": parsing_state.last_chunk_type
            }
            
            analysis_result = {
                "chunk_type": analysis.chunk_type.value,
                "confidence": analysis.confidence,
                "chunk_index": analysis.chunk_index
            }
            
            fragment_metadata = self._detect_fragment_boundaries(chunk)
            
            self.extraction_logger.log_extraction_prompt(
                chunk_index=analysis.chunk_index,
                chunk_content=chunk,
                analysis_result=analysis_result,
                parsing_state=parsing_state_dict,
                enhanced_prompt=enhanced_prompt,
                messages=messages,
                fragment_metadata=fragment_metadata
            )
        
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
            
            # Log response if debugging enabled
            if self.debug_prompts:
                self.extraction_logger.log_extraction_prompt(
                    chunk_index=analysis.chunk_index,
                    chunk_content=chunk,
                    analysis_result=analysis_result,
                    parsing_state=parsing_state_dict,
                    enhanced_prompt=enhanced_prompt,
                    messages=messages,
                    response=response,
                    fragment_metadata=fragment_metadata
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
                    'confidence': analysis.confidence,
                    'parsing_phase': parsing_state.parsing_phase,
                    'has_accumulated_content': bool(
                        (parsing_state.current_section and parsing_state.current_section.accumulated_content) or
                        (parsing_state.current_element and parsing_state.current_element.accumulated_content)
                    )
                }
                
                # Update monitoring and debugging counters
                if monitor:
                    monitor.complete_chunk_extraction(analysis.chunk_index)
                    
                    # Track token usage if available
                    if 'usage' in response:
                        usage = response['usage']
                        monitor.update_token_usage(
                            usage.get('prompt_tokens', 0),
                            usage.get('completion_tokens', 0)
                        )
                        
                        # Update debugging token usage
                        if self.debug_prompts:
                            self.total_token_usage['prompt_tokens'] += usage.get('prompt_tokens', 0)
                            self.total_token_usage['completion_tokens'] += usage.get('completion_tokens', 0)
                
                if self.debug_prompts:
                    self.successful_extractions += 1
                
                self._log(f"Successfully extracted content from chunk {analysis.chunk_index}")
                return extracted_data
            
        except Exception as e:
            if self.debug_prompts:
                self.failed_extractions += 1
                
                # Log error response
                self.extraction_logger.log_extraction_prompt(
                    chunk_index=analysis.chunk_index,
                    chunk_content=chunk,
                    analysis_result=analysis_result,
                    parsing_state=parsing_state_dict,
                    enhanced_prompt=enhanced_prompt,
                    messages=messages,
                    response={"error": str(e)},
                    fragment_metadata=fragment_metadata
                )
            
            logging.exception(f"Error extracting content from chunk {analysis.chunk_index}: {e}")
            error_msg = f"Error extracting content from chunk {analysis.chunk_index}: {e}"
            self._log(error_msg)
            if monitor:
                monitor.add_error(error_msg)
        
        return None
    
    def finalize_debugging_session(self, total_chunks: int) -> None:
        """Finalize the extraction debugging session with summary information."""
        if not self.debug_prompts:
            return
        
        self.extraction_logger.log_extraction_summary(
            total_chunks=total_chunks,
            successful_extractions=self.successful_extractions,
            failed_extractions=self.failed_extractions,
            fragment_count=self.fragment_count,
            continuity_decisions=self.continuity_decisions,
            token_usage=self.total_token_usage
        )
        
        self._log(f"Extraction debugging session completed. Logs saved to: {self.extraction_logger.get_session_path()}")
