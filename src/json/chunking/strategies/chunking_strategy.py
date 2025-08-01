"""
Abstract base class for text chunking strategies.
"""

from abc import ABC, abstractmethod
from typing import List


class ChunkingStrategy(ABC):
    """Abstract base class for text chunking strategies."""
    
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def chunk_text(self, content: str) -> List[str]:
        """
        Split content into chunks using the specific strategy.
        
        Args:
            content: Text content to split
            
        Returns:
            List of text chunks
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of the chunking strategy."""
        pass
