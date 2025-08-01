"""
Content analysis for questionnaire chunks.
"""

import re
from typing import List, Dict


class ContentAnalyzer:
    """Analyzes content types and patterns in questionnaire chunks."""
    
    def detect_chunk_type(self, chunk: str) -> str:
        """Detect the primary type of content in a chunk."""
        if re.search(r'^#+\s+Section\s+\d+', chunk, re.MULTILINE | re.IGNORECASE):
            return "SECTION_START"
        elif re.search(r'^\*\*[^*\n]+\*\*\s*:', chunk, re.MULTILINE):
            return "ELEMENT_START"
        elif chunk.strip().startswith('|') and '|' in chunk:
            return "TABLE_DATA"
        elif re.search(r'^\*\s*\*\*[^*]+\*\*', chunk, re.MULTILINE):
            return "PROGRAMMING_NOTES"
        elif chunk.strip().startswith('[') and 'CONTINUATION' in chunk:
            return "CONTINUATION"
        else:
            return "MIXED_CONTENT"
    
    def extract_chunk_markers(self, chunk: str) -> List[str]:
        """Extract chunk markers added during preprocessing."""
        markers = []
        lines = chunk.split('\n')
        
        for line in lines[:5]:  # Check first few lines for markers
            if line.strip().startswith('[') and line.strip().endswith(']'):
                markers.append(line.strip())
        
        return markers
    
    def analyze_chunks_for_debug(self, chunks: List[str], original_content: str, structures: Dict) -> Dict:
        """Create detailed analysis of chunks for debugging."""
        analysis = {
            "original_stats": {
                "total_characters": len(original_content),
                "total_lines": len(original_content.split('\n')),
                "sections_detected": len(structures['sections']),
                "elements_detected": len(structures['elements']),
                "tables_detected": len(structures['tables'])
            },
            "chunk_stats": {
                "total_chunks": len(chunks),
                "avg_chunk_size": sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0,
                "min_chunk_size": min(len(chunk) for chunk in chunks) if chunks else 0,
                "max_chunk_size": max(len(chunk) for chunk in chunks) if chunks else 0,
                "chunks_with_sections": sum(1 for chunk in chunks if re.search(r'^#+\s+Section\s+\d+', chunk, re.MULTILINE | re.IGNORECASE)),
                "chunks_with_elements": sum(1 for chunk in chunks if re.search(r'^\*\*[^*\n]+\*\*\s*:', chunk, re.MULTILINE)),
                "chunks_with_tables": sum(1 for chunk in chunks if '|' in chunk),
                "chunks_with_markers": sum(1 for chunk in chunks if '[' in chunk and 'CONTINUATION' in chunk)
            },
            "structure_distribution": {
                "sections": structures['sections'],
                "elements": structures['elements'][:10],  # Limit for readability
                "total_elements": len(structures['elements'])
            },
            "chunk_details": []
        }
        
        # Analyze each chunk
        for i, chunk in enumerate(chunks):
            chunk_detail = {
                "index": i,
                "size": len(chunk),
                "type": self.detect_chunk_type(chunk),
                "markers": self.extract_chunk_markers(chunk),
                "has_section": bool(re.search(r'^#+\s+Section\s+\d+', chunk, re.MULTILINE | re.IGNORECASE)),
                "has_element": bool(re.search(r'^\*\*[^*\n]+\*\*\s*:', chunk, re.MULTILINE)),
                "has_table": '|' in chunk,
                "starts_with_table": chunk.strip().startswith('|'),
                "line_count": len(chunk.split('\n')),
                "preview": chunk[:200] + "..." if len(chunk) > 200 else chunk
            }
            
            # Extract section/element codes if present
            section_match = re.search(r'^#+\s+Section\s+(\d+)', chunk, re.MULTILINE | re.IGNORECASE)
            if section_match:
                chunk_detail["section_code"] = section_match.group(1)
            
            element_match = re.search(r'^\*\*([^*\n]+)\*\*\s*:', chunk, re.MULTILINE)
            if element_match:
                chunk_detail["element_code"] = element_match.group(1)
            
            analysis["chunk_details"].append(chunk_detail)
        
        return analysis
