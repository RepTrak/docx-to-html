"""
Character-based chunking strategy.
"""

from typing import List
from .chunking_strategy import ChunkingStrategy


class CharacterStrategy(ChunkingStrategy):
    """Chunking strategy based on character count with word boundary awareness."""
    
    def chunk_text(self, content: str) -> List[str]:
        """Split content using character-based chunking with word boundaries."""
        if len(content) <= self.chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            chunk = content[start:end]
            
            # Try to end at a word boundary if we're not at the end of content
            if end < len(content) and not content[end].isspace():
                # Look backwards for a space within the last 20% of the chunk
                search_start = max(start + int(self.chunk_size * 0.8), start)
                last_space = content.rfind(' ', search_start, end)
                if last_space > start:
                    end = last_space + 1
                    chunk = content[start:end]
            
            if chunk.strip():
                chunks.append(chunk.strip())
            
            # Move start position with overlap
            start = max(start + self.chunk_size - self.chunk_overlap, end)
            
            # Prevent infinite loop
            if start >= len(content):
                break
        
        return chunks
    
    def get_strategy_name(self) -> str:
        return "character"
