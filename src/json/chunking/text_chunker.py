"""
Text chunking service for markdown content using SentenceTransformers.
"""

from typing import List, Optional
import re
from langchain_text_splitters.sentence_transformers import SentenceTransformersTokenTextSplitter


class TextChunker:
    """Service for splitting text into semantically-aware overlapping chunks."""
    
    def __init__(
        self, 
        chunk_size: int = 256, 
        chunk_overlap: int = 20,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        verbose: bool = False
    ):
        """
        Initialize the text chunker with SentenceTransformers tokenizer.
        
        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Overlap between chunks in tokens
            model_name: SentenceTransformers model for tokenization
            verbose: Enable verbose logging
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        self.verbose = verbose
        
        # Initialize the SentenceTransformers-based splitter
        self.splitter = SentenceTransformersTokenTextSplitter(
            model_name=model_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokens_per_chunk=chunk_size
        )
        
        # Markdown-specific patterns for intelligent splitting
        self.section_pattern = re.compile(r'^#+\s+', re.MULTILINE)
        # elements normally are : `**Q215**: The next questions concern...`
        self.element_pattern = re.compile(r'^\*\*[^*]+\*\*:', re.MULTILINE)
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[TextChunker] {message}")
    
    def _find_semantic_boundaries(self, content: str) -> List[int]:
        """
        Find positions in the content that represent good semantic boundaries.
        
        Returns:
            List of character positions that are good split points
        """
        boundaries = []
        
        # Find section headers (# Section)
        for match in self.section_pattern.finditer(content):
            boundaries.append(match.start())
        
        # Find element headers (**ElementCode**:)
        for match in self.element_pattern.finditer(content):
            boundaries.append(match.start())
        
        # Find paragraph breaks (double newlines)
        para_breaks = [m.start() for m in re.finditer(r'\n\n+', content)]
        boundaries.extend(para_breaks)
        
        # Sort and deduplicate
        return sorted(list(set(boundaries)))
    
    def _adjust_chunk_boundaries(self, chunks: List[str], original_content: str) -> List[str]:
        """
        Adjust chunk boundaries to respect markdown structure when possible.
        
        Args:
            chunks: Initial chunks from the splitter
            original_content: Original content for boundary analysis
            
        Returns:
            Adjusted chunks with better boundaries
        """
        if len(chunks) <= 1:
            return chunks
        
        adjusted_chunks = []
        current_pos = 0
        
        for i, chunk in enumerate(chunks):
            chunk_start = original_content.find(chunk, current_pos)
            if chunk_start == -1:
                # Fallback: use original chunk if we can't find it
                adjusted_chunks.append(chunk)
                continue
            
            chunk_end = chunk_start + len(chunk)
            
            # For all chunks except the last, try to find a better boundary
            if i < len(chunks) - 1:
                # Look for semantic boundaries near the current end
                search_start = max(chunk_start + self.chunk_size - self.chunk_overlap, chunk_start)
                search_end = min(chunk_end + self.chunk_overlap, len(original_content))
                search_region = original_content[search_start:search_end]
                
                # Find the best boundary within the search region
                best_boundary = None
                
                # Priority 1: Section headers
                section_matches = list(self.section_pattern.finditer(search_region))
                if section_matches:
                    best_boundary = search_start + section_matches[0].start()
                
                # Priority 2: Element headers
                if best_boundary is None:
                    element_matches = list(self.element_pattern.finditer(search_region))
                    if element_matches:
                        best_boundary = search_start + element_matches[0].start()
                
                # Priority 3: Paragraph breaks
                if best_boundary is None:
                    para_match = re.search(r'\n\n+', search_region)
                    if para_match:
                        best_boundary = search_start + para_match.start()
                
                # Priority 4: Table row boundaries
                if best_boundary is None:
                    table_match = re.search(r'\|\s*\n', search_region)
                    if table_match:
                        best_boundary = search_start + table_match.end()
                
                # Adjust chunk if we found a better boundary
                if best_boundary and best_boundary > chunk_start:
                    adjusted_chunk = original_content[chunk_start:best_boundary]
                    adjusted_chunks.append(adjusted_chunk.strip())
                    current_pos = best_boundary
                    continue
            
            # Use original chunk if no better boundary found
            adjusted_chunks.append(chunk.strip())
            current_pos = chunk_end
        
        # Remove empty chunks
        return [chunk for chunk in adjusted_chunks if chunk.strip()]
    
    def _preserve_critical_content(self, chunks: List[str]) -> List[str]:
        """
        Ensure critical markdown structures are not split inappropriately.
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            Validated chunks with critical content preserved
        """
        preserved_chunks = []
        
        for chunk in chunks:
            # Check if chunk starts mid-table and try to include table header
            lines = chunk.split('\n')
            if lines and lines[0].strip().startswith('|') and '|' in lines[0]:
                # This might be a table continuation
                # Mark it clearly for the processor
                chunk = f"[TABLE_CONTINUATION]\n{chunk}"
            
            # Check if chunk starts mid-element
            if lines and not lines[0].strip().startswith(('#', '**', '*', '|', '-')):
                first_line = lines[0].strip()
                if first_line and not first_line[0].isupper():
                    # Likely continuation of previous content
                    chunk = f"[CONTENT_CONTINUATION]\n{chunk}"
            
            preserved_chunks.append(chunk)
        
        return preserved_chunks
    
    def chunk_markdown(self, content: str) -> List[str]:
        """
        Split markdown content into semantically-aware overlapping chunks.
        
        Args:
            content: Markdown content to split
            
        Returns:
            List of text chunks optimized for questionnaire processing
        """
        if not content.strip():
            return []
        
        self._log(f"Starting chunking of {len(content)} characters")
        
        # Use SentenceTransformers splitter for initial chunking
        try:
            initial_chunks = self.splitter.split_text(content)
            self._log(f"SentenceTransformers created {len(initial_chunks)} initial chunks")
        except Exception as e:
            self._log(f"Error with SentenceTransformers splitter: {e}")
            # Fallback to simple chunking
            return self._fallback_chunking(content)
        
        # Adjust boundaries to respect markdown structure
        adjusted_chunks = self._adjust_chunk_boundaries(initial_chunks, content)
        self._log(f"Adjusted to {len(adjusted_chunks)} chunks with better boundaries")
        
        # Preserve critical content structures
        final_chunks = self._preserve_critical_content(adjusted_chunks)
        self._log(f"Final output: {len(final_chunks)} chunks")
        
        # Log chunk size statistics if verbose
        if self.verbose:
            sizes = [len(chunk) for chunk in final_chunks]
            avg_size = sum(sizes) / len(sizes) if sizes else 0
            self._log(f"Chunk sizes - Min: {min(sizes) if sizes else 0}, "
                     f"Max: {max(sizes) if sizes else 0}, "
                     f"Avg: {avg_size:.1f}")
        
        return final_chunks
    
    def _fallback_chunking(self, content: str) -> List[str]:
        """
        Fallback chunking method if SentenceTransformers fails.
        
        Args:
            content: Content to chunk
            
        Returns:
            List of chunks using simple character-based splitting
        """
        self._log("Using fallback chunking method")
        
        if len(content) <= self.chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # If not the last chunk, try to break at a good boundary
            if end < len(content):
                # Look for section breaks within overlap distance
                section_break = content.rfind('\n# ', start, end)
                if section_break > start:
                    end = section_break
                else:
                    # Look for element breaks
                    element_break = content.rfind('\n**', start, end)
                    if element_break > start:
                        end = element_break
                    else:
                        # Look for paragraph breaks
                        para_break = content.rfind('\n\n', start, end)
                        if para_break > start:
                            end = para_break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calculate next start position with overlap
            if end >= len(content):
                break
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
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
                "max_chunk_size": 0
            }
        
        sizes = [len(chunk) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_characters": sum(sizes),
            "avg_chunk_size": sum(sizes) / len(sizes),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes),
            "chunk_size_target": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "model_name": self.model_name
        }
