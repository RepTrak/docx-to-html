"""
Service for analyzing markdown chunks using LLM.
"""

import time
import logging
import re
from typing import Optional

from ...llm import LLMClient
from ...models.parsing_state import ChunkAnalysis, ChunkType, ParsingState
from ...models.monitoring import ProcessingMonitor
from .prompt_logger import PromptLogger


class ChunkAnalyzer:
    """Service for analyzing chunks to determine their type and content."""
    
    def __init__(
        self, 
        llm_client: LLMClient,
        system_prompt: str,
        analysis_prompt_template: str,
        provider: str = "openai",
        model: str = "gpt-4o-mini-2024-07-18",
        verbose: bool = True,
        debug_prompts: bool = True,
        prompt_log_dir: str = "debug_chunk_logs"
    ):
        """
        Initialize the chunk analyzer.
        
        Args:
            llm_client: LLM client instance
            system_prompt: System prompt for analysis
            analysis_prompt_template: Template for analysis prompts
            provider: LLM provider to use
            model: LLM model to use
            verbose: Enable verbose logging
            debug_prompts: Enable prompt debugging/logging
            prompt_log_dir: Directory for saving debug logs
        """
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.analysis_prompt_template = analysis_prompt_template
        self.provider = provider
        self.model = model
        self.verbose = verbose
        self.debug_prompts = debug_prompts
        self.prompt_logger = PromptLogger(prompt_log_dir, enabled=debug_prompts)
        
        if self.debug_prompts:
            self._log(f"Prompt debugging enabled. Logs will be saved to: {self.prompt_logger.get_session_path()}")
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def analyze_chunk(
        self, 
        chunk: str, 
        chunk_index: int, 
        total_chunks: int,
        parsing_state: ParsingState,
        prev_chunk: Optional[ChunkAnalysis] = None,
        prev_chunk_raw: Optional[str] = None,
        monitor: Optional[ProcessingMonitor] = None
    ) -> ChunkAnalysis:
        """Analyze a chunk to determine its type and content."""
        
        start_time = time.time()
        
        # Enhanced context with continuity information
        continuity_context = ""
        if parsing_state.current_section:
            continuity_context += f"Current Section: {parsing_state.current_section.code or 'Unknown'}\n"
        if parsing_state.current_element:
            continuity_context += f"Current Element: {parsing_state.current_element.code or 'Unknown'}\n"
        
        # Detect table content patterns
        has_table = '|' in chunk
        table_pattern = "Contains table data" if has_table else "No table data"
        prev_chunk_content = prev_chunk.extracted_content if prev_chunk else ""
        # Create analysis prompt with enhanced context
        prompt = self.analysis_prompt_template.format(
            parsing_state=parsing_state.parsing_phase,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            previous_chunk_type=parsing_state.last_chunk_type,
            chunk_content=chunk
        ) + f"""
# PREVIOUS CHUNK DATA EXTRACTED
{prev_chunk_content}
# PREVIOUS CHUNK RAW
{prev_chunk_raw[:-100] if prev_chunk_raw else ''}
## CONTINUITY CONTEXT
{continuity_context}

## CONTENT PATTERNS
- Table Content: {table_pattern}
- Processing Table: {getattr(parsing_state, 'processing_table', False)}

## ANALYSIS GUIDANCE
- If chunk contains `|` and no clear headers, likely table continuation
- If chunk starts without clear markers and we have current element, likely element continuation
- If chunk starts without clear markers and we have current section, likely section continuation
- Pay attention to **ElementCode**: patterns for new elements
- Pay attention to # Section patterns for new sections

Consider continuity when determining chunk type.
"""
        
        messages = [
            {"role": "assistant", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Log prompt if debugging is enabled
        if self.debug_prompts:
            metadata = {
                "provider": self.provider,
                "model": self.model,
                "parsing_phase": parsing_state.parsing_phase,
                "current_section": parsing_state.current_section.code if parsing_state.current_section else None,
                "current_element": parsing_state.current_element.code if parsing_state.current_element else None,
                "last_chunk_type": parsing_state.last_chunk_type,
                "processing_table": getattr(parsing_state, 'processing_table', False),
                "has_table": '|' in chunk,
                "total_chunks": total_chunks
            }
            
            self.prompt_logger.log_prompt(
                prompt_type="chunk_analysis",
                messages=messages,
                chunk_index=chunk_index,
                chunk_content=chunk,
                metadata=metadata
            )
        
        try:
            response = self.llm_client.completion(
                messages=messages,
                response_format=ChunkAnalysis,
                provider=self.provider,
                model=self.model,
                temperature=0.1,
                max_tokens=8192
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Log response if debugging is enabled
            if self.debug_prompts:
                self.prompt_logger.log_prompt(
                    prompt_type="chunk_analysis",
                    messages=messages,
                    chunk_index=chunk_index,
                    chunk_content=chunk,
                    response=response,
                    metadata={
                        **metadata,
                        "processing_time_ms": processing_time,
                        "success": True
                    }
                )
            
            if 'parsed' in response and response['parsed']:
                analysis = response['parsed']
                analysis.chunk_index = chunk_index
                
                # Post-process analysis based on context
                analysis = self._refine_analysis_with_context(analysis, chunk, parsing_state)
                
                logging.info(f"Chunk {chunk_index} analysis: {analysis}")
                
                # Update monitoring if provided
                if monitor:
                    monitor.complete_chunk_analysis(
                        chunk_index, 
                        analysis.chunk_type.value, 
                        analysis.confidence,
                        processing_time
                    )
                    
                    # Track token usage if available
                    if 'usage' in response:
                        usage = response['usage']
                        monitor.update_token_usage(
                            usage.get('prompt_tokens', 0),
                            usage.get('completion_tokens', 0)
                        )
                
                return analysis
            else:
                # Enhanced fallback analysis
                fallback_analysis = self._fallback_analysis(chunk, chunk_index, parsing_state)
                if monitor:
                    monitor.complete_chunk_analysis(
                        chunk_index, 
                        fallback_analysis.chunk_type.value, 
                        fallback_analysis.confidence,
                        processing_time
                    )
                return fallback_analysis
                
        except Exception as e:
            # Log error if debugging is enabled
            if self.debug_prompts:
                self.prompt_logger.log_prompt(
                    prompt_type="chunk_analysis",
                    messages=messages,
                    chunk_index=chunk_index,
                    chunk_content=chunk,
                    response={"error": str(e)},
                    metadata={
                        **metadata,
                        "processing_time_ms": processing_time,
                        "success": False,
                        "error": str(e)
                    }
                )
            
            self._log(f"Error analyzing chunk {chunk_index}: {e}")
            if monitor:
                monitor.add_error(f"Analysis error in chunk {chunk_index}: {str(e)}")
            return self._fallback_analysis(chunk, chunk_index, parsing_state)
    
    def _refine_analysis_with_context(
        self, 
        analysis: ChunkAnalysis, 
        chunk: str, 
        parsing_state: ParsingState
    ) -> ChunkAnalysis:
        """Refine analysis based on parsing context and continuity."""
        
        # Check for table continuation patterns
        has_table = '|' in chunk
        starts_with_table = chunk.strip().startswith('|')
        has_element_header = bool(re.search(r'^\*\*[^*]+\*\*:', chunk, re.MULTILINE))
        has_section_header = bool(re.search(r'^#+\s+Section', chunk, re.MULTILINE | re.IGNORECASE))
        
        # Refine UNKNOWN chunks based on context
        if analysis.chunk_type == ChunkType.UNKNOWN:
            if has_table and parsing_state.current_element and not has_element_header and not has_section_header:
                # Likely table continuation for current element
                analysis.chunk_type = ChunkType.ELEMENT_CONTINUATION
                analysis.confidence = min(analysis.confidence + 0.2, 1.0)
                self._log(f"Refined UNKNOWN to ELEMENT_CONTINUATION (table data)")
            
            elif parsing_state.current_section and not has_section_header:
                # Likely section continuation
                analysis.chunk_type = ChunkType.SECTION_CONTINUATION
                analysis.confidence = min(analysis.confidence + 0.1, 1.0)
                self._log(f"Refined UNKNOWN to SECTION_CONTINUATION")
        
        # Adjust confidence based on continuity indicators
        if parsing_state.current_element and analysis.chunk_type == ChunkType.ELEMENT_CONTINUATION:
            if has_table:
                analysis.confidence = min(analysis.confidence + 0.1, 1.0)
        
        if parsing_state.current_section and analysis.chunk_type == ChunkType.SECTION_CONTINUATION:
            analysis.confidence = min(analysis.confidence + 0.1, 1.0)
        
        return analysis
    
    def _fallback_analysis(self, chunk: str, chunk_index: int, parsing_state: ParsingState) -> ChunkAnalysis:
        """Create fallback analysis based on simple pattern matching."""
        
        # Pattern-based analysis
        if re.search(r'^#+\s+Section', chunk, re.MULTILINE | re.IGNORECASE):
            chunk_type = ChunkType.SECTION_START
            confidence = 0.8
        elif re.search(r'^\*\*[^*]+\*\*:', chunk, re.MULTILINE):
            chunk_type = ChunkType.ELEMENT_START
            confidence = 0.7
        elif '|' in chunk and parsing_state.current_element:
            chunk_type = ChunkType.ELEMENT_CONTINUATION
            confidence = 0.6
        elif parsing_state.current_section:
            chunk_type = ChunkType.SECTION_CONTINUATION
            confidence = 0.5
        else:
            chunk_type = ChunkType.UNKNOWN
            confidence = 0.3
        
        return ChunkAnalysis(
            chunk_index=chunk_index,
            chunk_type=chunk_type,
            confidence=confidence
        )
    
    def finalize_debugging_session(self, total_chunks: int, success_count: int, error_count: int) -> None:
        """Finalize the debugging session with summary information."""
        if not self.debug_prompts:
            return
        
        summary = {
            "session_completed": datetime.now().isoformat(),
            "total_chunks": total_chunks,
            "successful_analyses": success_count,
            "failed_analyses": error_count,
            "total_prompts": self.prompt_logger.prompt_count,
            "provider": self.provider,
            "model": self.model,
            "session_path": self.prompt_logger.get_session_path()
        }
        
        self.prompt_logger.log_analysis_summary(summary)
        self._log(f"Debugging session completed. Summary saved to: {self.prompt_logger.get_session_path()}")
