"""
Service for analyzing markdown chunks using LLM.
"""

import time
import logging
from typing import Optional

from ...llm import LLMClient
from ...models.parsing_state import ChunkAnalysis, ChunkType, ParsingState
from ...models.monitoring import ProcessingMonitor


class ChunkAnalyzer:
    """Service for analyzing chunks to determine their type and content."""
    
    def __init__(
        self, 
        llm_client: LLMClient,
        system_prompt: str,
        analysis_prompt_template: str,
        provider: str = "openai",
        model: str = "gpt-4o-mini-2024-07-18",
        verbose: bool = False
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
        """
        self.llm_client = llm_client
        self.system_prompt = system_prompt
        self.analysis_prompt_template = analysis_prompt_template
        self.provider = provider
        self.model = model
        self.verbose = verbose
    
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
        monitor: Optional[ProcessingMonitor] = None
    ) -> ChunkAnalysis:
        """Analyze a chunk to determine its type and content."""
        
        start_time = time.time()
        
        # Create analysis prompt
        prompt = self.analysis_prompt_template.format(
            parsing_state=parsing_state.parsing_phase,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            previous_chunk_type=parsing_state.last_chunk_type,
            chunk_content=chunk
        )
        
        messages = [
            {"role": "assistant", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
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
            
            if 'parsed' in response and response['parsed']:
                analysis = response['parsed']
                analysis.chunk_index = chunk_index
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
                # Fallback analysis
                if monitor:
                    monitor.complete_chunk_analysis(
                        chunk_index, 
                        ChunkType.UNKNOWN.value, 
                        0.0,
                        processing_time
                    )
                return ChunkAnalysis(
                    chunk_index=chunk_index,
                    chunk_type=ChunkType.UNKNOWN,
                    confidence=0.0
                )
                
        except Exception as e:
            self._log(f"Error analyzing chunk {chunk_index}: {e}")
            if monitor:
                monitor.add_error(f"Analysis error in chunk {chunk_index}: {str(e)}")
            return ChunkAnalysis(
                chunk_index=chunk_index,
                chunk_type=ChunkType.UNKNOWN,
                confidence=0.0
            )
