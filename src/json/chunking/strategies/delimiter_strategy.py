"""
Delimiter-based chunking strategy for structured documents.
"""

import json
from typing import List, Dict, Any
from .chunking_strategy import ChunkingStrategy
import re


class DelimiterStrategy(ChunkingStrategy):
    """Chunking strategy based on *** delimiter."""
    
    def __init__(self, chunk_size: int = 0, chunk_overlap: int = 0):
        super().__init__(chunk_size, chunk_overlap)
        self.structure_map: Dict[str, Any] = {}
    
    def chunk_text(self, content: str) -> List[str]:
        """Split content by regex `\\\*\\\*\\\*` delimiter."""
        # Use regex to split by the delimiter
        elements = re.split(r'\\\*\\\*\\\*', content)
        if not elements:
            return []
        # Remove leading/trailing whitespace from each element
        elements = [element.strip() for element in elements if element.strip()]
        if not elements:
            return []      
        
        # Clean elements and filter out empty ones
        chunks = []
        for element in elements:
            element = element.strip()
            # check if first line is section header and remove it
            if element.startswith('#'):
                lines = element.split('\n')
                # Remove first line if it's a section header
                if lines and re.match(r'^\s*#', lines[0]):
                    element = '\n'.join(lines[1:]).strip()
                    
            if element:
                chunks.append(element)
        
        # Create simple structure map
        self.structure_map = {
            "document_type": "questionnaire",
            "total_elements": len(chunks),
            "delimiter": "***"
        }
        
        return chunks
    
    def get_strategy_name(self) -> str:
        return "delimiter"
    
    def get_structure_map(self) -> Dict[str, Any]:
        """Return the structure map created during chunking."""
        return self.structure_map
    
    def save_structure_map(self, output_path: str) -> None:
        """Save the structure map to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.structure_map, f, indent=2, ensure_ascii=False)
    
    def get_structure_summary(self) -> str:
        """Get a summary of the document structure."""
        if not self.structure_map:
            return "No structure map available. Run chunk_text() first."
        
        return f"Document Structure Summary:\n- Total Elements: {self.structure_map['total_elements']}\n- Delimiter: {self.structure_map['delimiter']}"
