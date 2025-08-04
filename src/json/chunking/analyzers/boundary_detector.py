"""
Boundary detection for questionnaire content.
"""

import re
from typing import List, Dict


class BoundaryDetector:
    """Detects semantic boundaries in questionnaire content."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        
        # Enhanced questionnaire-specific patterns
        self.section_pattern = re.compile(r'^#+\s+Section\s+\d+', re.MULTILINE | re.IGNORECASE)
        self.element_pattern = re.compile(r'^\*\*[^*\n]+\*\*\s*:', re.MULTILINE)
        self.table_start_pattern = re.compile(r'^\|[^|]*\|[^|]*\|', re.MULTILINE)
        self.strong_boundary_pattern = re.compile(r'^#+\s+', re.MULTILINE)
        
        # Patterns for questionnaire content preservation
        self.questionnaire_patterns = {
            'section_header': re.compile(r'^#+\s+Section\s+\d+\s*[-–—]\s*(.+)', re.MULTILINE | re.IGNORECASE),
            'element_header': re.compile(r'^\*\*([^*\n]+)\*\*\s*:\s*(.+)', re.MULTILINE),
            'variables_table': re.compile(r'\*\*VARIABLES?\s+TABLE\*\*', re.IGNORECASE),
            'columns_table': re.compile(r'\*\*COLUMNS?\s+TABLE\*\*', re.IGNORECASE),
            'table_row': re.compile(r'^\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', re.MULTILINE),
            'programming_note': re.compile(r'^\*\s*\*\*[^*]+\*\*', re.MULTILINE),
            'list_item': re.compile(r'^\s*[\*\+\-]\s+', re.MULTILINE)
        }
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[BoundaryDetector] {message}")
    
    def find_semantic_boundaries(self, content: str) -> List[int]:
        """
        Find positions in the content that represent good semantic boundaries.
        
        Returns:
            List of character positions that are good split points
        """
        boundaries = []
        
        # Priority 1: Section headers (strongest boundaries)
        for match in self.section_pattern.finditer(content):
            boundaries.append(match.start())
            self._log(f"Found section boundary at position {match.start()}: {match.group()[:50]}...")
        
        # Priority 2: Element headers
        for match in self.element_pattern.finditer(content):
            boundaries.append(match.start())
            self._log(f"Found element boundary at position {match.start()}: {match.group()[:50]}...")
        
        # Priority 3: Strong headers (any # header)
        for match in self.strong_boundary_pattern.finditer(content):
            if match.start() not in boundaries:  # Avoid duplicates
                boundaries.append(match.start())
                self._log(f"Found header boundary at position {match.start()}")
        
        # Priority 4: Table boundaries (start of tables)
        table_starts = []
        for match in self.table_start_pattern.finditer(content):
            table_starts.append(match.start())
        
        # Only add table boundaries if they're not too close to other boundaries
        for table_start in table_starts:
            if not any(abs(table_start - b) < 50 for b in boundaries):
                boundaries.append(table_start)
                self._log(f"Found table boundary at position {table_start}")
        
        # Priority 5: Double newlines (paragraph breaks)
        para_breaks = [m.start() for m in re.finditer(r'\n\n+', content)]
        for para_break in para_breaks:
            if not any(abs(para_break - b) < 20 for b in boundaries):
                boundaries.append(para_break)
        
        # Sort and deduplicate
        final_boundaries = sorted(list(set(boundaries)))
        self._log(f"Found {len(final_boundaries)} semantic boundaries")
        return final_boundaries
    
    def detect_questionnaire_structure(self, content: str) -> Dict[str, List]:
        """
        Detect questionnaire-specific structures and their positions.
        
        Returns:
            Dictionary mapping structure types to their positions
        """
        structures = {
            'sections': [],
            'elements': [],
            'tables': [],
            'variable_tables': [],
            'column_tables': []
        }
        
        # Find sections
        for match in self.questionnaire_patterns['section_header'].finditer(content):
            structures['sections'].append({
                'start': match.start(),
                'code': match.group().split()[1] if len(match.group().split()) > 1 else 'unknown',
                'text': match.group()[:100]
            })
        
        # Find elements
        for match in self.questionnaire_patterns['element_header'].finditer(content):
            structures['elements'].append({
                'start': match.start(),
                'code': match.group(1) if match.groups() else 'unknown',
                'text': match.group()[:100]
            })
        
        # Find variable tables
        for match in self.questionnaire_patterns['variables_table'].finditer(content):
            structures['variable_tables'].append(match.start())
        
        # Find column tables
        for match in self.questionnaire_patterns['columns_table'].finditer(content):
            structures['column_tables'].append(match.start())
        
        # Find general tables
        for match in self.table_start_pattern.finditer(content):
            structures['tables'].append(match.start())
        
        return structures
