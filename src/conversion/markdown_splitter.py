"""
Markdown text splitter for structured questionnaire documents.
"""

import re
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass


@dataclass
class SplitResult:
    """Result of a markdown splitting operation."""
    success: bool
    chunks: List[str] = None
    structure_map: Dict[str, Any] = None
    error_message: Optional[str] = None
    split_stats: Optional[Dict[str, Any]] = None


class MarkdownTextSplitter:
    """
    Markdown text splitter for structured questionnaire documents.
    Based on delimiter strategy with markdown structure awareness.
    """
    
    def __init__(self, 
                 primary_delimiter: str = r'\\\*\\\*\\\*',
                 fallback_chunk_size: int = 2000,
                 fallback_overlap: int = 200,
                 verbose: bool = True):
        """
        Initialize the markdown splitter.
        
        Args:
            primary_delimiter: Primary regex delimiter pattern
            fallback_chunk_size: Size for fallback chunking if delimiter fails
            fallback_overlap: Overlap for fallback chunking
            verbose: Whether to enable verbose logging
        """
        self.primary_delimiter = primary_delimiter
        self.fallback_chunk_size = fallback_chunk_size
        self.fallback_overlap = fallback_overlap
        self.verbose = verbose
        self.structure_map: Dict[str, Any] = {}
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[MarkdownSplitter] {message}")
    
    def split_text(self, markdown_content: str) -> SplitResult:
        """
        Split markdown content into chunks using delimiter-based strategy.
        
        Args:
            markdown_content: The markdown content to split
            
        Returns:
            SplitResult with chunks and metadata
        """
        if not markdown_content or not markdown_content.strip():
            return SplitResult(
                success=False,
                error_message="Empty or invalid markdown content"
            )
        
        try:
            self._log("Starting markdown content splitting...")
            
            # Try primary delimiter strategy first
            chunks = self._split_by_delimiter(markdown_content)
            
            # If delimiter strategy fails or produces too few chunks, try fallback
            if not chunks or len(chunks) < 2:
                self._log("Primary delimiter strategy produced insufficient chunks, trying fallback...")
                chunks = self._split_by_structure_fallback(markdown_content)
                strategy_used = "structure_fallback"
            else:
                strategy_used = "delimiter"
            
            # Create structure map first to get position information
            self.structure_map = self._create_structure_map(chunks, strategy_used)
            
            # Add position metadata to chunks
            chunks_with_metadata = self._add_position_metadata_to_chunks(chunks)
            
            # Calculate split statistics
            split_stats = self._calculate_split_stats(markdown_content, chunks_with_metadata, strategy_used)
            
            self._log(f"Successfully split into {len(chunks_with_metadata)} chunks using {strategy_used} strategy")
            
            return SplitResult(
                success=True,
                chunks=chunks_with_metadata,
                structure_map=self.structure_map,
                split_stats=split_stats
            )
            
        except Exception as e:
            error_msg = f"Error splitting markdown content: {str(e)}"
            self._log(error_msg)
            return SplitResult(
                success=False,
                error_message=error_msg
            )

    def _add_position_metadata_to_chunks(self, chunks: List[str]) -> List[str]:
        """Add position metadata to the end of each chunk."""
        chunks_with_metadata = []
        
        for i, chunk in enumerate(chunks):
            chunk_info = self.structure_map["chunks_info"][i]
            
            # Create metadata footer
            metadata_lines = [
                "",
                "<!-- CHUNK METADATA -->",
                f"<!-- Chunk Index: {chunk_info['chunk_index']} -->",
                f"<!-- Total Chunks: {self.structure_map['total_chunks']} -->",
            ]
            
            # Add section information if available
            if chunk_info.get('has_section_header'):
                metadata_lines.extend([
                    f"<!-- Section Position: {chunk_info.get('section_position', 'unknown')} -->",
                    f"<!-- Section Title: {chunk_info.get('section_title', 'unknown')} -->",
                    f"<!-- Next Element Position: 1 -->"
                ])
            
            # Add element positioning information
            if chunk_info.get('elements'):
                first_element = chunk_info['elements'][0]
                last_element = chunk_info['elements'][-1]
                metadata_lines.extend([
                    f"<!-- Elements in Chunk: {len(chunk_info['elements'])} -->",
                    f"<!-- First Element Position: {first_element['section_relative_position']} -->",
                    f"<!-- Last Element Position: {last_element['section_relative_position']} -->",
                    f"<!-- Next Element Position: {last_element['section_relative_position'] + 1} -->"
                ])
            elif chunk_info['processing_hints'].get('next_section_element_position'):
                metadata_lines.append(f"<!-- Next Element Position: {chunk_info['processing_hints']['next_section_element_position']} -->")
            
            # Add table information
            if chunk_info.get('table_info', {}).get('has_value_table'):
                metadata_lines.append("<!-- Contains Value Table: Variables/Options -->")
            if chunk_info.get('table_info', {}).get('has_variable_table'):
                metadata_lines.append("<!-- Contains Variable Table: Grid Questions -->")
            
            # Add processing hints
            metadata_lines.extend([
                f"<!-- Chunk Type: {self._determine_chunk_type(chunk_info)} -->",
                f"<!-- Processing Priority: {self._determine_processing_priority(chunk_info)} -->",
                "<!-- END METADATA -->"
            ])
            
            # Combine original chunk with metadata
            chunk_with_metadata = chunk + "\n" + "\n".join(metadata_lines)
            chunks_with_metadata.append(chunk_with_metadata)
        
        return chunks_with_metadata

    def _determine_chunk_type(self, chunk_info: Dict[str, Any]) -> str:
        """Determine the type of chunk based on its content."""
        if chunk_info.get('has_section_header'):
            if chunk_info.get('elements'):
                return "section_with_elements"
            else:
                return "section_header_only"
        elif chunk_info.get('elements'):
            return "elements_only"
        elif chunk_info.get('table_info', {}).get('has_value_table') or chunk_info.get('table_info', {}).get('has_variable_table'):
            return "table_content"
        else:
            return "content_fragment"

    def _determine_processing_priority(self, chunk_info: Dict[str, Any]) -> str:
        """Determine processing priority based on chunk content."""
        if chunk_info.get('has_section_header'):
            return "high"
        elif chunk_info.get('elements'):
            return "high" 
        elif chunk_info.get('table_info', {}).get('table_row_count', 0) > 0:
            return "medium"
        else:
            return "low"

    def _split_by_delimiter(self, content: str) -> List[str]:
        """Split content using the primary delimiter pattern."""
        # Use regex to split by the delimiter
        elements = re.split(self.primary_delimiter, content)
        if not elements:
            return []
        
        # Remove leading/trailing whitespace from each element
        elements = [element.strip() for element in elements if element.strip()]
        if not elements:
            return []
        
        # Clean elements and filter out empty ones - keep section headers
        chunks = []
        for element in elements:
            element = element.strip()
            
            # Keep the element as is, including section headers
            if element:
                chunks.append(element)
        
        return chunks

    def _split_by_structure_fallback(self, content: str) -> List[str]:
        """Fallback splitting strategy based on markdown structure."""
        chunks = []
        
        # Try splitting by major section headers first
        section_pattern = r'^# .+$'
        sections = re.split(f'({section_pattern})', content, flags=re.MULTILINE)
        
        if len(sections) > 3:  # We have actual sections
            current_chunk = ""
            for i, section in enumerate(sections):
                if re.match(section_pattern, section.strip(), re.IGNORECASE):
                    # This is a section header - start new chunk with this header
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = section + "\n"
                else:
                    current_chunk += section
            
            # Add the last chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
        
        # If still no good chunks, use size-based chunking
        if not chunks or len(chunks) < 2:
            chunks = self._split_by_size(content)
        
        return [chunk for chunk in chunks if chunk.strip()]

    def _split_by_size(self, content: str) -> List[str]:
        """Size-based chunking as last resort."""
        chunks = []
        lines = content.split('\n')
        current_chunk = ""
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            
            if current_size + line_size > self.fallback_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                overlap_lines = current_chunk.split('\n')[-self.fallback_overlap//50:]  # Rough estimate
                current_chunk = '\n'.join(overlap_lines) + '\n' + line
                current_size = len(current_chunk)
            else:
                current_chunk += line + '\n'
                current_size += line_size + 1
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _calculate_split_stats(self, original_content: str, chunks: List[str], strategy: str) -> Dict[str, Any]:
        """Calculate statistics about the splitting operation."""
        return {
            'original_length': len(original_content),
            'original_lines': len(original_content.split('\n')),
            'original_words': len(original_content.split()),
            'total_chunks': len(chunks),
            'average_chunk_size': sum(len(chunk) for chunk in chunks) // len(chunks) if chunks else 0,
            'min_chunk_size': min(len(chunk) for chunk in chunks) if chunks else 0,
            'max_chunk_size': max(len(chunk) for chunk in chunks) if chunks else 0,
            'strategy_used': strategy,
            'delimiter_pattern': self.primary_delimiter
        }
    
    def _create_structure_map(self, chunks: List[str], strategy: str) -> Dict[str, Any]:
        """Create a structure map of the split content."""
        structure_info = {
            "document_type": "questionnaire_markdown",
            "total_chunks": len(chunks),
            "splitting_strategy": strategy,
            "delimiter": self.primary_delimiter if strategy == "delimiter" else None,
            "chunks_info": []
        }
        
        # Track global positions across all chunks
        global_section_position = 0
        global_element_position = 0
        current_section_element_position = 0
        
        for i, chunk in enumerate(chunks):
            # Extract section title if present
            section_title = None
            section_match = re.search(r'^# (.+)$', chunk, re.MULTILINE)
            if section_match:
                section_title = section_match.group(1).strip()
                global_section_position += 1
                current_section_element_position = 0  # Reset element position for new section
            
            # Find all element patterns in this chunk
            element_matches = list(re.finditer(r'\*\*([^*]+)\*\*\s*(?:\[([^\]]+)\])?:', chunk))
            elements_in_chunk = []
            
            for match in element_matches:
                current_section_element_position += 1
                global_element_position += 1
                
                element_code = match.group(1).strip()
                element_type = match.group(2).strip() if match.group(2) else "CHOICE"
                
                elements_in_chunk.append({
                    "code": element_code,
                    "type": element_type,
                    "global_position": global_element_position,
                    "section_relative_position": current_section_element_position,
                    "start_char": match.start(),
                    "end_char": match.end()
                })
            
            # Check for table patterns (variables/columns)
            table_patterns = {
                "has_value_table": bool(re.search(r'\|\s*(?:Value\s*)?Code\s*\|\s*(?:Value\s*)?Label', chunk, re.IGNORECASE)),
                "has_variable_table": bool(re.search(r'\|\s*Variable\s*Name\s*\|\s*Variable\s*Label', chunk, re.IGNORECASE)),
                "table_row_count": len(re.findall(r'^\s*\|.*\|.*\|', chunk, re.MULTILINE))
            }
            
            chunk_info = {
                "chunk_index": i,
                "size": len(chunk),
                "lines": len(chunk.split('\n')),
                "has_section_header": bool(section_match),
                "section_title": section_title,
                "section_position": global_section_position if section_match else None,
                "elements_count": len(elements_in_chunk),
                "elements": elements_in_chunk,
                "table_info": table_patterns,
                "has_element_pattern": len(elements_in_chunk) > 0,
                "has_table": bool('|' in chunk),
                "starts_with": chunk[:50].replace('\n', ' ') if chunk else "",
                "processing_hints": {
                    "next_section_element_position": current_section_element_position + 1,
                    "chunk_contains_section_start": bool(section_match),
                    "estimated_elements_to_process": len(elements_in_chunk)
                }
            }
            structure_info["chunks_info"].append(chunk_info)
        
        return structure_info
    
    def get_structure_map(self) -> Dict[str, Any]:
        """Return the structure map created during splitting."""
        return self.structure_map
    
    def save_structure_map(self, output_path: Union[str, Path]) -> bool:
        """
        Save the structure map to a JSON file.
        
        Args:
            output_path: Path where to save the structure map
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.structure_map, f, indent=2, ensure_ascii=False)
            
            self._log(f"Structure map saved to: {output_path}")
            return True
            
        except Exception as e:
            self._log(f"Error saving structure map: {str(e)}")
            return False
    
    def save_chunks(self, split_result: SplitResult, output_dir: Union[str, Path]) -> bool:
        """
        Save individual chunks to separate files for debugging.
        
        Args:
            split_result: Result from split_text()
            output_dir: Directory where to save chunk files
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not split_result.success or not split_result.chunks:
            self._log("Cannot save chunks: split was not successful or no chunks available")
            return False
        
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for i, chunk in enumerate(split_result.chunks):
                chunk_file = output_dir / f"chunk_{i:03d}.md"
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    f.write(chunk)
            
            # Also save the structure map
            self.save_structure_map(output_dir / "structure_map.json")
            
            self._log(f"Saved {len(split_result.chunks)} chunks to: {output_dir}")
            return True
            
        except Exception as e:
            self._log(f"Error saving chunks: {str(e)}")
            return False
    
    def get_split_summary(self, split_result: SplitResult) -> str:
        """
        Get a human-readable summary of the split operation.
        
        Args:
            split_result: Result from split_text()
            
        Returns:
            Summary string
        """
        if not split_result.success:
            return f"Split failed: {split_result.error_message}"
        
        stats = split_result.split_stats or {}
        summary_lines = [
            "Markdown Split Summary:",
            f"- Strategy Used: {stats.get('strategy_used', 'unknown')}",
            f"- Total Chunks: {stats.get('total_chunks', 0)}",
            f"- Original Content: {stats.get('original_length', 0):,} chars, {stats.get('original_lines', 0):,} lines",
            f"- Average Chunk Size: {stats.get('average_chunk_size', 0):,} chars",
            f"- Size Range: {stats.get('min_chunk_size', 0):,} - {stats.get('max_chunk_size', 0):,} chars"
        ]
        
        if stats.get('delimiter_pattern'):
            summary_lines.append(f"- Delimiter Pattern: {stats['delimiter_pattern']}")
        
        return "\n".join(summary_lines)
