"""
Chunk processor for boundary adjustment and content preservation.
"""

import re
from typing import List, Dict
from ..analyzers.boundary_detector import BoundaryDetector


class ChunkProcessor:
    """Processes chunks to improve boundaries and preserve content structure."""
    
    def __init__(self, chunk_size: int, chunk_overlap: int, verbose: bool = False):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.verbose = verbose
        self.boundary_detector = BoundaryDetector(verbose)
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[ChunkProcessor] {message}")
    
    def adjust_chunk_boundaries(self, chunks: List[str], original_content: str) -> List[str]:
        """
        Adjust chunk boundaries to respect questionnaire structure when possible.
        """
        if len(chunks) <= 1:
            return chunks
        
        # Detect questionnaire structures
        structures = self.boundary_detector.detect_questionnaire_structure(original_content)
        self._log(f"Detected structures: {len(structures['sections'])} sections, {len(structures['elements'])} elements")
        
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
                best_boundary = self._find_best_boundary(
                    chunk_start, chunk_end, structures, original_content
                )
                
                # Apply the best boundary found
                if best_boundary and best_boundary > chunk_start:
                    adjusted_chunk = original_content[chunk_start:best_boundary].strip()
                    if adjusted_chunk:
                        adjusted_chunks.append(adjusted_chunk)
                        current_pos = best_boundary
                        continue
            
            # Use original chunk if no better boundary found
            adjusted_chunks.append(chunk.strip())
            current_pos = chunk_end
        
        # Remove empty chunks and log results
        final_chunks = [chunk for chunk in adjusted_chunks if chunk.strip()]
        self._log(f"Boundary adjustment: {len(chunks)} -> {len(final_chunks)} chunks")
        return final_chunks
    
    def _find_best_boundary(self, chunk_start: int, chunk_end: int, structures: Dict, original_content: str) -> int:
        """Find the best boundary position for a chunk."""
        # Define search region for better boundaries
        min_chunk_size = max(self.chunk_size - self.chunk_overlap, self.chunk_size // 2)
        search_start = max(chunk_start + min_chunk_size, chunk_start)
        search_end = min(chunk_end + self.chunk_overlap, len(original_content))
        
        best_boundary = None
        boundary_type = None
        
        # Priority 1: Section boundaries
        for section in structures['sections']:
            if search_start <= section['start'] <= search_end:
                if not best_boundary or section['start'] < best_boundary:
                    best_boundary = section['start']
                    boundary_type = f"section_{section['code']}"
        
        # Priority 2: Element boundaries (if no section found)
        if not best_boundary:
            for element in structures['elements']:
                if search_start <= element['start'] <= search_end:
                    if not best_boundary or element['start'] < best_boundary:
                        best_boundary = element['start']
                        boundary_type = f"element_{element['code']}"
        
        # Priority 3: Table boundaries (if no element found)
        if not best_boundary:
            for table_start in structures['tables']:
                if search_start <= table_start <= search_end:
                    # Check if this table is part of current element
                    prev_element = None
                    for element in structures['elements']:
                        if element['start'] < table_start:
                            prev_element = element
                    
                    # Only break at table if it's not variables/columns for current element
                    if (not prev_element or 
                        table_start - prev_element['start'] > self.chunk_size):
                        if not best_boundary or table_start < best_boundary:
                            best_boundary = table_start
                            boundary_type = "table"
        
        # Priority 4: Paragraph breaks
        if not best_boundary:
            search_region = original_content[search_start:search_end]
            para_matches = list(re.finditer(r'\n\n+', search_region))
            if para_matches:
                best_boundary = search_start + para_matches[0].start()
                boundary_type = "paragraph"
        
        if best_boundary and boundary_type:
            self._log(f"Found {boundary_type} boundary at position {best_boundary}")
        
        return best_boundary
    
    def preserve_critical_content(self, chunks: List[str]) -> List[str]:
        """
        Ensure critical questionnaire structures are not split inappropriately.
        """
        preserved_chunks = []
        
        for i, chunk in enumerate(chunks):
            lines = chunk.split('\n')
            if not lines:
                continue
            
            # Detect content type and add markers
            chunk_markers = self._detect_content_markers(lines)
            
            # Add markers to chunk if any found
            if chunk_markers:
                marked_chunk = '\n'.join(chunk_markers) + '\n' + chunk
            else:
                marked_chunk = chunk
            
            preserved_chunks.append(marked_chunk)
            
            if chunk_markers and self.verbose:
                self._log(f"Chunk {i} marked with: {', '.join(chunk_markers)}")
        
        return preserved_chunks
    
    def _detect_content_markers(self, lines: List[str]) -> List[str]:
        """Detect and return appropriate content markers for a chunk."""
        chunk_markers = []
        
        if not lines:
            return chunk_markers
        
        first_line = lines[0].strip()
        
        # Check if chunk starts mid-table
        if first_line.startswith('|') and '|' in first_line:
            # Look for table headers in previous context
            has_variables_header = any('Variable' in line for line in lines[:3])
            has_columns_header = any('Value' in line or 'Code' in line for line in lines[:3])
            
            if has_variables_header:
                chunk_markers.append("[VARIABLES_TABLE_CONTINUATION]")
            elif has_columns_header:
                chunk_markers.append("[COLUMNS_TABLE_CONTINUATION]")
            else:
                chunk_markers.append("[TABLE_CONTINUATION]")
        
        # Check if chunk starts mid-element (no clear header)
        elif (first_line and 
              not first_line.startswith(('#', '**', '*', '|', '-')) and
              not re.match(r'^[A-Z][a-z]+:', first_line)):
            # Check if it looks like element content continuation
            if any(keyword in first_line.lower() for keyword in 
                   ['single answer', 'programmer', 'randomize', 'multicode']):
                chunk_markers.append("[ELEMENT_INSTRUCTIONS_CONTINUATION]")
            else:
                chunk_markers.append("[CONTENT_CONTINUATION]")
        
        # Check for element headers at chunk start
        elif re.match(r'^\*\*[^*\n]+\*\*\s*:', first_line):
            element_match = re.match(r'^\*\*([^*\n]+)\*\*\s*:', first_line)
            if element_match:
                element_code = element_match.group(1)
                chunk_markers.append(f"[ELEMENT_START:{element_code}]")
        
        # Check for section headers at chunk start
        elif re.match(r'^#+\s+Section\s+\d+', first_line, re.IGNORECASE):
            section_match = re.match(r'^#+\s+Section\s+(\d+)', first_line, re.IGNORECASE)
            if section_match:
                section_code = section_match.group(1)
                chunk_markers.append(f"[SECTION_START:{section_code}]")
        
        return chunk_markers
    
    def validate_questionnaire_integrity(self, chunks: List[str], original_content: str) -> List[str]:
        """
        Validate that questionnaire structure is preserved across chunks.
        """
        structures = self.boundary_detector.detect_questionnaire_structure(original_content)
        
        # Track which structures appear in which chunks
        current_pos = 0
        
        for i, chunk in enumerate(chunks):
            # Clean chunk for finding in original content
            clean_chunk = self._clean_chunk_for_position_finding(chunk)
            
            chunk_start = original_content.find(clean_chunk, current_pos)
            if chunk_start == -1:
                chunk_start = current_pos
            
            chunk_end = chunk_start + len(clean_chunk)
            
            # Find structures in this chunk for logging
            if self.verbose:
                self._log_chunk_structures(i, chunk_start, chunk_end, structures)
            
            current_pos = chunk_end
        
        return chunks
    
    def _clean_chunk_for_position_finding(self, chunk: str) -> str:
        """Clean chunk markers for finding position in original content."""
        clean_chunk = chunk
        for marker in ['[SECTION_START:', '[ELEMENT_START:', '[TABLE_CONTINUATION]', '[CONTENT_CONTINUATION]']:
            if marker in clean_chunk:
                clean_chunk = '\n'.join([line for line in clean_chunk.split('\n') 
                                       if not line.strip().startswith('[') or not line.strip().endswith(']')])
        return clean_chunk
    
    def _log_chunk_structures(self, chunk_index: int, chunk_start: int, chunk_end: int, structures: Dict) -> None:
        """Log structures found in a chunk."""
        chunk_sections = []
        chunk_elements = []
        
        # Check for sections
        for section in structures['sections']:
            if chunk_start <= section['start'] < chunk_end:
                chunk_sections.append(section['code'])
        
        # Check for elements
        for element in structures['elements']:
            if chunk_start <= element['start'] < chunk_end:
                chunk_elements.append(element['code'])
        
        if chunk_sections or chunk_elements:
            self._log(f"Chunk {chunk_index}: sections={chunk_sections}, elements={chunk_elements}")
    
    def preprocess_questionnaire_content(self, content: str) -> str:
        """
        Preprocess content to improve chunking for questionnaire structures.
        """
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            # Add extra spacing before sections to encourage breaks
            if re.match(r'^#+\s+Section\s+\d+', line, re.IGNORECASE):
                processed_lines.append('\n')  # Extra newline before sections
                processed_lines.append(line)
            # Add spacing before elements
            elif re.match(r'^\*\*[^*\n]+\*\*\s*:', line):
                if processed_lines and processed_lines[-1].strip():
                    processed_lines.append('')  # Extra newline before elements
                processed_lines.append(line)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
