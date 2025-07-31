"""
Text chunking service for markdown content.
"""

from typing import List


class TextChunker:
    """Service for splitting text into overlapping chunks."""
    
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_markdown(self, content: str) -> List[str]:
        """Split markdown content into overlapping chunks."""
        if len(content) <= self.chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # If not the last chunk, try to break at a good boundary
            if end < len(content):
                # Look for section breaks (## headers) within overlap distance
                section_break = content.rfind('\n# ', start, end)
                if section_break > start:
                    end = section_break
                else:
                    # Look for element breaks (**bold**) within overlap distance
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
