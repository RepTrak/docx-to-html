"""
Text chunking service for markdown content using configurable strategies.
"""

from typing import List, Optional
from .strategies.chunking_strategy import ChunkingStrategy
from .strategies.sentence_transformer_strategy import SentenceTransformerStrategy
from .strategies.character_strategy import CharacterStrategy
from .strategies.delimiter_strategy import DelimiterStrategy
from .analyzers.boundary_detector import BoundaryDetector
from .processors.chunk_processor import ChunkProcessor
from .debug.debug_manager import DebugManager


class TextChunker:
    """Service for splitting text into semantically-aware overlapping chunks."""
    
    def __init__(
        self, 
        chunk_size: int = 2000, 
        chunk_overlap: int = 200,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        mode: str = "delimiter",
        verbose: bool = True,
        debug_output_dir: Optional[str] = None
    ):
        """
        Initialize the text chunker with configurable chunking mode.
        
        Args:
            chunk_size: Target size of each chunk (tokens for sentence_transformer, chars for character)
            chunk_overlap: Overlap between chunks (tokens for sentence_transformer, chars for character)
            model_name: SentenceTransformers model for tokenization (only used in sentence_transformer mode)
            mode: Chunking mode - "sentence_transformer", "character", or "delimiter"
            verbose: Enable verbose logging
            debug_output_dir: Directory to save debug chunks (optional)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        self.mode = mode
        self.verbose = verbose
        
        # Validate mode
        if mode not in ["sentence_transformer", "character", "delimiter"]:
            raise ValueError(f"Invalid mode '{mode}'. Must be 'sentence_transformer', 'character', or 'delimiter'")
        
        # Initialize components
        self.boundary_detector = BoundaryDetector(verbose)
        self.chunk_processor = ChunkProcessor(chunk_size, chunk_overlap, verbose)
        self.debug_manager = DebugManager(debug_output_dir, verbose)
        
        # Initialize chunking strategy
        self.strategy = self._create_chunking_strategy()
    
    def _create_chunking_strategy(self) -> ChunkingStrategy:
        """Create the appropriate chunking strategy based on mode."""
        if self.mode == "sentence_transformer":
            return SentenceTransformerStrategy(self.chunk_size, self.chunk_overlap, self.model_name)
        elif self.mode == "delimiter":
            return DelimiterStrategy(self.chunk_size, self.chunk_overlap)
        else:
            return CharacterStrategy(self.chunk_size, self.chunk_overlap)
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            mode_prefix = self.mode.upper()
            print(f"[TextChunker:{mode_prefix}] {message}")
    
    def chunk_markdown(self, content: str, source_file: Optional[str] = None) -> List[str]:
        """
        Split markdown content into semantically-aware overlapping chunks.
        
        Args:
            content: Markdown content to split
            source_file: Optional source file path for debugging context
            
        Returns:
            List of text chunks optimized for questionnaire processing, ordered by appearance in source
        """
        if not content.strip():
            return []
        
        self._log(f"Starting questionnaire-aware chunking of {len(content)} characters using {self.mode} mode")
        
        try:
            # Choose chunking strategy based on mode
            if self.mode == "delimiter":
                # Use delimiter-based chunking for structured documents
                initial_chunks = self.strategy.chunk_text(content)
                self._log(f"Delimiter-based chunking created {len(initial_chunks)} chunks")
            elif self.mode == "character":
                # Use character-based chunking with boundary awareness
                initial_chunks = self._character_aware_chunking(content)
                self._log(f"Character-aware chunking created {len(initial_chunks)} initial chunks")
            else:
                # Use SentenceTransformers chunking with preprocessing
                processed_content = self.chunk_processor.preprocess_questionnaire_content(content)
                initial_chunks = self.strategy.chunk_text(processed_content)
                self._log(f"SentenceTransformers created {len(initial_chunks)} initial chunks")
                
                # Adjust boundaries to respect questionnaire structure
                initial_chunks = self.chunk_processor.adjust_chunk_boundaries(initial_chunks, processed_content)
                self._log(f"Adjusted to {len(initial_chunks)} chunks with better boundaries")
            
            # Skip boundary adjustment and validation for delimiter mode as it's already structure-aware
            if self.mode != "delimiter":
                # Preserve critical content structures (applies to both modes)
                # preserved_chunks = self.chunk_processor.preserve_critical_content(initial_chunks)
                self._log(f"Preserved critical structures in {len(initial_chunks)} chunks")
                
                # Validate questionnaire integrity
                final_chunks = self.chunk_processor.validate_questionnaire_integrity(initial_chunks, content)
            else:
                final_chunks = initial_chunks
            
            # Ensure chunks are ordered by their position in the original content
            # final_chunks = self._ensure_sequential_order(final_chunks, content)
            
            # Save chunks for debugging if enabled
            if self.debug_manager.debug_output_dir:
                structures = self.boundary_detector.detect_questionnaire_structure(content)
                chunking_config = {
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap,
                    "mode": self.mode,
                    "model_name": self.model_name if self.mode == "sentence_transformer" else None
                }
                self.debug_manager.save_chunks_for_debugging(
                    final_chunks, content, structures, chunking_config, source_file
                )
            
            # Log chunk size statistics if verbose
            self._log_chunk_statistics(final_chunks)
            
            return final_chunks
            
        except Exception as e:
            self._log(f"Error during chunking: {e}")
            # Fallback to questionnaire-aware chunking (except for delimiter mode)
            if self.mode == "delimiter":
                # For delimiter mode, return simple line-based splitting as fallback
                fallback_chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]
            else:
                fallback_chunks = self._questionnaire_aware_chunking(content)
            return self._ensure_sequential_order(fallback_chunks, content)
    
    def _character_aware_chunking(self, content: str) -> List[str]:
        """
        Character-based chunking that respects questionnaire structure.
        """
        self._log("Using character-aware chunking with questionnaire boundaries")
        
        if len(content) <= self.chunk_size:
            return [content]
        
        # Find semantic boundaries for better splitting
        boundaries = self.boundary_detector.find_semantic_boundaries(content)
        
        chunks = []
        start = 0
        
        while start < len(content):
            # Calculate target end position
            target_end = min(start + self.chunk_size, len(content))
            
            # Find the best boundary within acceptable range
            best_boundary = target_end
            min_acceptable = start + max(self.chunk_size - self.chunk_overlap, self.chunk_size // 2)
            max_acceptable = min(start + self.chunk_size + self.chunk_overlap, len(content))
            
            # Look for semantic boundaries in the acceptable range
            for boundary in boundaries:
                if min_acceptable <= boundary <= max_acceptable:
                    best_boundary = boundary
                    break
            
            # If no semantic boundary found, try word boundary
            if best_boundary == target_end and target_end < len(content):
                search_start = max(min_acceptable, start)
                last_space = content.rfind(' ', search_start, target_end)
                if last_space > start:
                    best_boundary = last_space + 1
            
            chunk = content[start:best_boundary].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calculate next start position with proper overlap
            if best_boundary < len(content):
                # Move start back by overlap amount to create overlapping content
                next_start = best_boundary - self.chunk_overlap
                # Ensure we don't go backwards past the current chunk start
                next_start = max(next_start, start + 1)
                # Ensure we make progress
                if next_start <= start:
                    next_start = start + max(1, self.chunk_size - self.chunk_overlap)
            else:
                next_start = len(content)  # We've reached the end
            
            start = next_start
            
            # Safety check to prevent infinite loops
            if start >= len(content):
                break
        
        return chunks
    
    def _questionnaire_aware_chunking(self, content: str) -> List[str]:
        """
        Fallback chunking method specifically designed for questionnaire content.
        """
        self._log("Using questionnaire-aware fallback chunking method")
        
        if len(content) <= self.chunk_size:
            return [content]
        
        # Find all major boundaries
        boundaries = self.boundary_detector.find_semantic_boundaries(content)
        boundaries.append(len(content))  # Add end boundary
        
        chunks = []
        start = 0
        
        for boundary in boundaries:
            if boundary - start >= self.chunk_size - self.chunk_overlap:
                # Create chunk from start to current boundary
                chunk = content[start:boundary].strip()
                if chunk:
                    chunks.append(chunk)
                    # Next chunk starts with overlap
                    start = max(start + self.chunk_size - self.chunk_overlap, boundary)
            elif boundary == boundaries[-1]:  # Last boundary
                # Add remaining content
                remaining = content[start:boundary].strip()
                if remaining:
                    chunks.append(remaining)
        
        return chunks
    
    def _log_chunk_statistics(self, final_chunks: List[str]) -> None:
        """Log chunk size statistics if verbose mode is enabled."""
        if self.verbose and final_chunks:
            sizes = [len(chunk) for chunk in final_chunks]
            avg_size = sum(sizes) / len(sizes)
            unit = "tokens" if self.mode == "sentence_transformer" else "characters"
            self._log(f"Final chunks - Count: {len(final_chunks)}")
            self._log(f"Chunk sizes ({unit}) - Min: {min(sizes)}, "
                     f"Max: {max(sizes)}, "
                     f"Avg: {avg_size:.1f}")
            
            if self.debug_manager.debug_output_dir:
                self._log(f"Debug output saved to: {self.debug_manager.debug_output_dir}")
    
    def get_chunk_info(self, chunks: List[str]) -> dict:
        """
        Get information about the chunks for monitoring and debugging.
        
        Args:
            chunks: List of chunks
            
        Returns:
            Dictionary with chunk statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_characters": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "mode": self.mode
            }
        
        sizes = [len(chunk) for chunk in chunks]
        
        info = {
            "total_chunks": len(chunks),
            "total_characters": sum(sizes),
            "avg_chunk_size": sum(sizes) / len(sizes),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes),
            "chunk_size_target": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "mode": self.mode
        }
        
        # Add model name only for sentence_transformer mode
        if self.mode == "sentence_transformer":
            info["model_name"] = self.model_name
        
        return info

    def _ensure_sequential_order(self, chunks: List[str], original_content: str) -> List[str]:
        """
        Ensure chunks are ordered by their position in the original content.
        
        Args:
            chunks: List of text chunks
            original_content: Original content string
            
        Returns:
            Chunks sorted by their first appearance position in the original content
        """
        if not chunks:
            return chunks
        
        # Create list of (position, chunk) tuples
        positioned_chunks = []
        for chunk in chunks:
            if chunk.strip():
                # Find the first occurrence of a substantial portion of the chunk
                search_text = chunk.strip()[:100]  # Use first 100 chars for position lookup
                position = original_content.find(search_text)
                if position == -1:
                    # If exact match not found, try with cleaned text
                    cleaned_search = search_text.replace('\n', ' ').replace('  ', ' ')
                    cleaned_content = original_content.replace('\n', ' ').replace('  ', ' ')
                    position = cleaned_content.find(cleaned_search)
                
                # If still not found, place at end with high position value
                if position == -1:
                    position = len(original_content) + len(positioned_chunks)
                
                positioned_chunks.append((position, chunk))
        
        # Sort by position and return chunks
        positioned_chunks.sort(key=lambda x: x[0])
        ordered_chunks = [chunk for _, chunk in positioned_chunks]
        
        if self.verbose and len(ordered_chunks) != len(chunks):
            self._log(f"Ordering verification: {len(chunks)} input chunks, {len(ordered_chunks)} output chunks")
        
        return ordered_chunks
