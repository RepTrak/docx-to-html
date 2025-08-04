"""
Processes individual markdown chunks using LLM.
"""

import json
import logging
from typing import Dict, Any, Optional

from ..llm.client import LLMClient
from .schema_models import ChunkExtractionResult, ProcessingStats
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class ChunkProcessor:
    """Processes markdown chunks using LLM to extract structured data."""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        model: str = "gpt-4o-mini",
        provider: str = "openai",
        temperature: float = 0.0,
        max_tokens: int = 4000,
        verbose: bool = True
    ):
        """
        Initialize the chunk processor.
        
        Args:
            llm_client: LLM client instance (creates default if None)
            model: Model to use for processing
            provider: Provider to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
            verbose: Enable verbose logging
        """
        self.llm_client = llm_client or LLMClient()
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose
        self.prompt_builder = PromptBuilder()
    
    def _log(self, message: str, level: str = "info") -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            getattr(logger, level, logger.info)(f"[ChunkProcessor] {message}")
    
    def process_chunk(
        self, 
        chunk_content: str, 
        chunk_index: int, 
        total_chunks: int, 
        context: Dict[str, Any],
        stats: ProcessingStats
    ) -> ChunkExtractionResult:
        """
        Process a single chunk using LLM and return structured data.
        
        Args:
            chunk_content: The markdown chunk to process
            chunk_index: Index of current chunk
            total_chunks: Total number of chunks
            context: Processing context information
            stats: Processing statistics to update
            
        Returns:
            Extraction result with structured data
        """
        try:
            # Create prompt
            user_prompt = self.prompt_builder.create_chunk_prompt(
                chunk_content, chunk_index, total_chunks, context
            )
            
            # Call LLM
            self._log(f"Processing chunk {chunk_index + 1}/{total_chunks} with LLM...")
            
            response = self.llm_client.completion(
                messages=[{"role": "user", "content": user_prompt}],
                model=self.model,
                provider=self.provider,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                system=self.prompt_builder.get_system_prompt(),
                response_format="json"
            )
            
            # Update stats
            stats.llm_calls += 1
            if response.get('usage'):
                stats.total_tokens['input'] += response['usage'].get('prompt_tokens', 0)
                stats.total_tokens['output'] += response['usage'].get('completion_tokens', 0)
            
            # Parse response
            content = response.get('content', '{}')
            if isinstance(content, str):
                result_data = json.loads(content)
            else:
                result_data = content
            
            self._log(f"LLM response for chunk {chunk_index + 1}: {result_data.get('chunk_type', 'unknown')}")
            
            # Create result object
            return ChunkExtractionResult(
                chunk_type=result_data.get('chunk_type', 'unknown'),
                extracted_sections=result_data.get('extracted_sections', []),
                extracted_elements=result_data.get('extracted_elements', []),
                partial_content=result_data.get('partial_content'),
                requires_continuation=result_data.get('requires_continuation', False),
                confidence=result_data.get('confidence', 0.0)
            )
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response from LLM for chunk {chunk_index}: {str(e)}"
            self._log(error_msg, "error")
            stats.errors.append(error_msg)
            return ChunkExtractionResult(chunk_type="error", error=error_msg)
            
        except Exception as e:
            error_msg = f"Error processing chunk {chunk_index} with LLM: {str(e)}"
            self._log(error_msg, "error")
            stats.errors.append(error_msg)
            return ChunkExtractionResult(chunk_type="error", error=error_msg)
