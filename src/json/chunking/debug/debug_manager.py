"""
Debug output manager for chunk analysis.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict
from ..analyzers.content_analyzer import ContentAnalyzer
import re


class DebugManager:
    """Manages debug output for chunk analysis."""
    
    def __init__(self, debug_output_dir: Optional[str] = None, verbose: bool = False):
        self.debug_output_dir = debug_output_dir
        self.verbose = verbose
        self.content_analyzer = ContentAnalyzer()
        
        # Create debug directory if specified
        if self.debug_output_dir:
            Path(self.debug_output_dir).mkdir(parents=True, exist_ok=True)
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[DebugManager] {message}")
    
    def save_chunks_for_debugging(
        self, 
        chunks: List[str], 
        original_content: str,
        structures: Dict,
        chunking_config: Dict,
        source_file: Optional[str] = None
    ) -> None:
        """
        Save chunks to files for debugging purposes.
        """
        if not self.debug_output_dir:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(source_file).stem if source_file else "unknown"
        debug_base_name = f"{source_name}_{timestamp}"
        
        debug_dir = Path(self.debug_output_dir) / debug_base_name
        debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual chunks
        for i, chunk in enumerate(chunks):
            chunk_file = debug_dir / f"chunk_{i:03d}.md"
            
            # Detect patterns for metadata
            has_section = bool(re.search(r'^#+\s+Section\s+\d+', chunk, re.MULTILINE | re.IGNORECASE))
            has_element = bool(re.search(r'^\*\*[^*\n]+\*\*\s*:', chunk, re.MULTILINE))
            has_table = '|' in chunk
            chunk_type = self.content_analyzer.detect_chunk_type(chunk)
            markers = self.content_analyzer.extract_chunk_markers(chunk)
            
            # Add chunk metadata header
            chunk_header = f"""<!-- CHUNK DEBUG INFO
Index: {i}
Size: {len(chunk)} characters
Original Position: Estimated
Chunk Type: {chunk_type}
Contains Section: {has_section}
Contains Element: {has_element}
Contains Table: {has_table}
Markers: {markers}
-->

"""
            
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk_header + chunk)
        
        # Save chunk analysis
        analysis = self.content_analyzer.analyze_chunks_for_debug(chunks, original_content, structures)
        analysis["chunking_config"] = chunking_config
        
        analysis_file = debug_dir / "chunk_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        # Save chunk overview
        overview_file = debug_dir / "chunks_overview.md"
        self._save_chunks_overview(chunks, overview_file, source_file)
        
        # Save original content for reference
        original_file = debug_dir / "original_content.md"
        with open(original_file, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        self._log(f"Debug chunks saved to: {debug_dir}")
    
    def _save_chunks_overview(self, chunks: List[str], overview_file: Path, source_file: Optional[str] = None) -> None:
        """Save a markdown overview of all chunks."""
        with open(overview_file, 'w', encoding='utf-8') as f:
            f.write("# Chunks Overview\n\n")
            
            if source_file:
                f.write(f"**Source File**: {source_file}\n")
            
            f.write(f"**Total Chunks**: {len(chunks)}\n")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"**Generated**: {timestamp}\n\n")
            
            f.write("## Chunk Summary\n\n")
            f.write("| Index | Size | Type | Has Section | Has Element | Has Table | Preview |\n")
            f.write("|-------|------|------|-------------|-------------|-----------|----------|\n")
            
            for i, chunk in enumerate(chunks):
                chunk_type = self.content_analyzer.detect_chunk_type(chunk)
                has_section = bool(re.search(r'^#+\s+Section\s+\d+', chunk, re.MULTILINE | re.IGNORECASE))
                has_element = bool(re.search(r'^\*\*[^*\n]+\*\*\s*:', chunk, re.MULTILINE))
                has_table = '|' in chunk
                
                # Clean preview text to avoid issues
                clean_chunk = chunk.replace('\n', ' ').replace('|', ' ').strip()
                preview = clean_chunk[:50] + "..." if len(clean_chunk) > 50 else clean_chunk
                
                f.write(f"| {i:03d} | {len(chunk)} | {chunk_type} | {has_section} | {has_element} | {has_table} | {preview} |\n")
            
            f.write("\n## Detailed Chunks\n\n")
            
            for i, chunk in enumerate(chunks):
                f.write(f"### Chunk {i:03d}\n\n")
                f.write(f"**Size**: {len(chunk)} characters\n")
                f.write(f"**Type**: {self.content_analyzer.detect_chunk_type(chunk)}\n")
                
                markers = self.content_analyzer.extract_chunk_markers(chunk)
                if markers:
                    markers_str = ', '.join(markers)
                    f.write(f"**Markers**: {markers_str}\n")
                
                f.write("**Preview**:\n")
                f.write("```markdown\n")
                preview_chunk = chunk[:500] + ("..." if len(chunk) > 500 else "")
                f.write(preview_chunk)
                f.write("\n```\n\n")
                f.write("---\n\n")
