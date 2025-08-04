"""
SentenceTransformers-based chunking strategy.
"""

from typing import List
from langchain_text_splitters.sentence_transformers import SentenceTransformersTokenTextSplitter
from .chunking_strategy import ChunkingStrategy


class SentenceTransformerStrategy(ChunkingStrategy):
    """Chunking strategy using SentenceTransformers for token-aware splitting."""
    
    def __init__(self, chunk_size: int, chunk_overlap: int, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        super().__init__(chunk_size, chunk_overlap)
        self.model_name = model_name
        self.splitter = SentenceTransformersTokenTextSplitter(
            model_name=model_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            tokens_per_chunk=chunk_size
        )
    
    def chunk_text(self, content: str) -> List[str]:
        """Split content using SentenceTransformers tokenization."""
        try:
            return self.splitter.split_text(content)
        except Exception as e:
            raise RuntimeError(f"SentenceTransformers chunking failed: {e}")
    
    def get_strategy_name(self) -> str:
        return "sentence_transformer"
