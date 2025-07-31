"""
Service for converting HTML files to Markdown format.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union
from html_to_markdown import convert_to_markdown


class HtmlToMarkdownService:
    """Service for converting HTML files to Markdown."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the HTML to Markdown service.
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
            
    def _convert_html_content(self, html_content: str) -> str:
        """
        Convert HTML content to Markdown.
        
        Args:
            html_content: HTML content as string
            
        Returns:
            Converted markdown content
        """
        # Configure html_to_markdown to preserve HTML structure as closely as possible
        markdown_content = convert_to_markdown(
            html_content,
            # Document processing - preserve original structure
            extract_metadata=True,  # Extract metadata as comment header
            convert_as_inline=False,  # Treat as block-level content
            strip_newlines=False,  # Preserve original newlines
            # Formatting options - match common HTML styling
            heading_style="atx",  # Use # style headers (closest to HTML h1-h6)
            strong_em_symbol="*",  # Use * for bold/italic (standard markdown)
            bullets="*+-",  # Support multiple bullet styles
            highlight_style="double-equal",  # Use == for highlighted text
            # Text processing - preserve formatting
            wrap=False,  # Don't wrap text to preserve original line breaks
            escape_asterisks=True,  # Escape * characters in content
            escape_underscores=True,  # Escape _ characters in content
            escape_misc=True,  # Escape other special characters
            # Code blocks - preserve code formatting
            code_language="",  # Don't assume language for code blocks
            # Memory efficiency for large documents
            stream_processing=False,  # Use standard processing for better control
            chunk_size=1024,  # Chunk size if streaming needed
        )
        
        # Post-process to clean up while preserving structure
        lines = markdown_content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.rstrip()
            is_empty = not line.strip()
            
            # Limit consecutive empty lines to max 2 (preserve paragraph spacing)
            if is_empty:
                if prev_empty:
                    # Skip if we already have one empty line
                    continue
                else:
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
                
            prev_empty = is_empty
            
        return '\n'.join(cleaned_lines).strip()
    
    def convert_file(self, input_path: Path, output_dir: Optional[Path] = None) -> Path:
        """
        Convert a single HTML file to Markdown.
        
        Args:
            input_path: Path to the HTML file
            output_dir: Optional output directory (defaults to same directory as input)
            
        Returns:
            Path to the created markdown file
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If input file is not an HTML file
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        if input_path.suffix.lower() not in ['.html', '.htm']:
            raise ValueError(f"Input file must be an HTML file: {input_path}")
            
        self._log(f"Converting: {input_path}")
        
        # Read HTML content
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Convert to markdown
        markdown_content = self._convert_html_content(html_content)
        
        # Determine output path
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{input_path.stem}.md"
        else:
            output_path = input_path.with_suffix('.md')
            
        # Write markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
        self._log(f"Created: {output_path}")
        return output_path
    
    def convert_batch(self, input_dir: Path, output_dir: Optional[Path] = None) -> List[Dict[str, Union[str, Path]]]:
        """
        Convert all HTML files in a directory to Markdown.
        
        Args:
            input_dir: Directory containing HTML files
            output_dir: Optional output directory
            
        Returns:
            List of conversion results with status information
        """
        input_dir = Path(input_dir)
        
        if not input_dir.exists() or not input_dir.is_dir():
            raise ValueError(f"Input directory not found: {input_dir}")
            
        # Find all HTML files
        html_files = list(input_dir.glob("*.html")) + list(input_dir.glob("*.htm"))
        
        if not html_files:
            self._log(f"No HTML files found in: {input_dir}")
            return []
            
        self._log(f"Found {len(html_files)} HTML files to convert")
        
        results = []
        
        for html_file in html_files:
            try:
                output_path = self.convert_file(html_file, output_dir)
                results.append({
                    'file': html_file,
                    'output': output_path,
                    'status': 'success'
                })
            except Exception as e:
                self._log(f"Error converting {html_file}: {e}")
                results.append({
                    'file': html_file,
                    'error': str(e),
                    'status': 'error'
                })
                
        return results
    
    def convert_from_mapping(self, mapping_file: Path, output_dir: Optional[Path] = None) -> Dict[str, any]:
        """
        Convert HTML files to Markdown based on a mapping file.
        
        Args:
            mapping_file: Path to the sections_questions_mapping.json file
            output_dir: Optional output directory for markdown files
            
        Returns:
            New mapping structure with markdown file paths
        """
        mapping_file = Path(mapping_file)
        
        if not mapping_file.exists():
            raise FileNotFoundError(f"Mapping file not found: {mapping_file}")
        
        # Read the original mapping
        with open(mapping_file, 'r', encoding='utf-8') as f:
            original_mapping = json.load(f)
        
        self._log(f"Processing mapping from: {mapping_file}")
        
        # Determine paths
        html_base_dir = mapping_file.parent
        sections_dir = html_base_dir / "sections"
        questions_dir = html_base_dir / "questions"
        
        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = html_base_dir
            
        md_sections_dir = output_dir / "sections_md"
        md_questions_dir = output_dir / "questions_md"
        
        # Create output directories
        md_sections_dir.mkdir(parents=True, exist_ok=True)
        md_questions_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize new mapping
        md_mapping = {
            "metadata": {
                "source_mapping": str(mapping_file),
                "html_source_file": original_mapping["metadata"]["source_file"],
                "total_sections": original_mapping["metadata"]["total_sections"],
                "total_questions": original_mapping["metadata"]["total_questions"],
                "conversion_timestamp": None
            },
            "sections": []
        }
        
        conversion_stats = {"sections_converted": 0, "questions_converted": 0, "errors": []}
        
        # Process each section
        for section in original_mapping["sections"]:
            section_html_file = sections_dir / section["filename"]
            section_md_filename = f"{Path(section['filename']).stem}.md"
            section_md_file = md_sections_dir / section_md_filename
            
            # Convert section file
            try:
                if section_html_file.exists():
                    self.convert_file(section_html_file, md_sections_dir)
                    conversion_stats["sections_converted"] += 1
                    self._log(f"Converted section: {section['title']}")
                else:
                    self._log(f"Warning: Section file not found: {section_html_file}")
            except Exception as e:
                error_msg = f"Error converting section {section['title']}: {e}"
                self._log(error_msg)
                conversion_stats["errors"].append(error_msg)
            
            # Process questions in this section
            md_questions = []
            for question in section["questions"]:
                question_html_file = questions_dir / question["filename"]
                question_md_filename = f"{Path(question['filename']).stem}.md"
                question_md_file = md_questions_dir / question_md_filename
                
                # Convert question file
                try:
                    if question_html_file.exists():
                        self.convert_file(question_html_file, md_questions_dir)
                        conversion_stats["questions_converted"] += 1
                        self._log(f"Converted question: {question['label']}")
                    else:
                        self._log(f"Warning: Question file not found: {question_html_file}")
                except Exception as e:
                    error_msg = f"Error converting question {question['label']}: {e}"
                    self._log(error_msg)
                    conversion_stats["errors"].append(error_msg)
                
                # Add to markdown mapping
                md_questions.append({
                    "index": question["index"],
                    "label": question["label"],
                    "html_filename": question["filename"],
                    "md_filename": question_md_filename
                })
            
            # Add section to markdown mapping
            md_mapping["sections"].append({
                "index": section["index"],
                "title": section["title"],
                "html_filename": section["filename"],
                "md_filename": section_md_filename,
                "question_count": section["question_count"],
                "questions": md_questions
            })
        
        # Add conversion timestamp and stats
        from datetime import datetime
        md_mapping["metadata"]["conversion_timestamp"] = datetime.now().isoformat()
        md_mapping["metadata"]["conversion_stats"] = conversion_stats
        
        # Save the markdown mapping
        md_mapping_file = output_dir / "sections_questions_mapping_markdown.json"
        with open(md_mapping_file, 'w', encoding='utf-8') as f:
            json.dump(md_mapping, f, indent=2, ensure_ascii=False)
        
        self._log(f"✓ Markdown mapping saved to: {md_mapping_file}")
        self._log(f"✓ Converted {conversion_stats['sections_converted']} sections and {conversion_stats['questions_converted']} questions")
        
        if conversion_stats["errors"]:
            self._log(f"⚠ {len(conversion_stats['errors'])} errors occurred during conversion")
        
        return md_mapping
