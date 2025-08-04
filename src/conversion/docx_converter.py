"""
DOCX to Markdown conversion service using MarkItDown.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from markitdown import MarkItDown
from .markdown_splitter import MarkdownTextSplitter, SplitResult

logger = logging.getLogger(__name__)

MARKITDOWN_AVAILABLE = True

@dataclass
class ConversionResult:
    """Result of a document conversion operation."""
    success: bool
    markdown_content: Optional[str] = None
    original_file_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    conversion_stats: Optional[Dict[str, Any]] = None


class DocxToMarkdownConverter:
    """Service for converting DOCX files to Markdown using MarkItDown."""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the converter.
        
        Args:
            verbose: Whether to enable verbose logging
        """
        self.verbose = verbose
        self._markitdown_instance = None
        
        if not MARKITDOWN_AVAILABLE:
            logger.error("MarkItDown library is not available. Please install it with: pip install markitdown")
            raise ImportError("MarkItDown library is required for DOCX conversion")
    
    @property
    def markitdown(self) -> MarkItDown:
        """Get or create MarkItDown instance."""
        if self._markitdown_instance is None:
            self._markitdown_instance = MarkItDown()
        return self._markitdown_instance
    
    def _log(self, message: str, level: str = "info") -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            getattr(logger, level)(message)
    
    def convert_file(self, file_path: Union[str, Path]) -> ConversionResult:
        """
        Convert a DOCX file to Markdown.
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            ConversionResult with the conversion outcome
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            self._log(error_msg, "error")
            return ConversionResult(
                success=False,
                original_file_path=str(file_path),
                error_message=error_msg
            )
        
        if not file_path.suffix.lower() == '.docx':
            error_msg = f"File is not a DOCX file: {file_path}"
            self._log(error_msg, "error")
            return ConversionResult(
                success=False,
                original_file_path=str(file_path),
                error_message=error_msg
            )
        
        try:
            self._log(f"Converting DOCX file to Markdown: {file_path}")
            
            # Convert using MarkItDown
            result = self.markitdown.convert(str(file_path))
            
            if not result or not hasattr(result, 'text_content'):
                error_msg = "MarkItDown conversion returned invalid result"
                self._log(error_msg, "error")
                return ConversionResult(
                    success=False,
                    original_file_path=str(file_path),
                    error_message=error_msg
                )
            
            markdown_content = result.text_content
            
            if not markdown_content or not markdown_content.strip():
                error_msg = "Conversion resulted in empty content"
                self._log(error_msg, "warning")
                return ConversionResult(
                    success=False,
                    original_file_path=str(file_path),
                    error_message=error_msg
                )
            
            # Calculate conversion statistics
            conversion_stats = {
                'original_file_size': file_path.stat().st_size,
                'markdown_length': len(markdown_content),
                'markdown_lines': len(markdown_content.split('\n')),
                'markdown_words': len(markdown_content.split()),
                'conversion_tool': 'MarkItDown'
            }
            
            # Extract metadata if available
            metadata = {}
            if hasattr(result, '__dict__'):
                for key, value in result.__dict__.items():
                    if key != 'text_content' and not key.startswith('_'):
                        try:
                            # Only include serializable metadata
                            import json
                            json.dumps(value)
                            metadata[key] = value
                        except (TypeError, ValueError):
                            # Skip non-serializable attributes
                            continue
            
            self._log(f"Successfully converted DOCX to Markdown: {conversion_stats['markdown_length']:,} characters")
            
            return ConversionResult(
                success=True,
                markdown_content=markdown_content,
                original_file_path=str(file_path),
                metadata=metadata,
                conversion_stats=conversion_stats
            )
            
        except Exception as e:
            error_msg = f"Error converting DOCX file: {str(e)}"
            self._log(error_msg, "error")
            return ConversionResult(
                success=False,
                original_file_path=str(file_path),
                error_message=error_msg
            )
    
    def convert_bytes(self, file_bytes: bytes, filename: str) -> ConversionResult:
        """
        Convert DOCX bytes to Markdown.
        
        Args:
            file_bytes: DOCX file content as bytes
            filename: Original filename for reference
            
        Returns:
            ConversionResult with the conversion outcome
        """
        import tempfile
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = Path(tmp_file.name)
            
            # Convert the temporary file
            result = self.convert_file(tmp_file_path)
            
            # Update the original file path in the result
            if result.success:
                result.original_file_path = filename
            
            return result
            
        except Exception as e:
            error_msg = f"Error converting DOCX bytes: {str(e)}"
            self._log(error_msg, "error")
            return ConversionResult(
                success=False,
                original_file_path=filename,
                error_message=error_msg
            )
        finally:
            # Cleanup temporary file
            if 'tmp_file_path' in locals() and tmp_file_path.exists():
                try:
                    tmp_file_path.unlink()
                except Exception as cleanup_error:
                    self._log(f"Warning: Failed to cleanup temporary file: {cleanup_error}", "warning")
    
    def save_markdown(self, result: ConversionResult, output_path: Union[str, Path]) -> bool:
        """
        Save conversion result to a Markdown file.
        
        Args:
            result: ConversionResult from a successful conversion
            output_path: Path where to save the Markdown file
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not result.success or not result.markdown_content:
            self._log("Cannot save: conversion was not successful or no content available", "error")
            return False
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.markdown_content)
            
            self._log(f"Markdown content saved to: {output_path}")
            return True
            
        except Exception as e:
            self._log(f"Error saving Markdown file: {str(e)}", "error")
            return False
    
    def get_conversion_info(self) -> Dict[str, Any]:
        """
        Get information about the converter capabilities.
        
        Returns:
            Dictionary with converter information
        """
        return {
            'converter_name': 'DocxToMarkdownConverter',
            'conversion_tool': 'MarkItDown',
            'markitdown_available': MARKITDOWN_AVAILABLE,
            'supported_formats': ['docx'],
            'output_format': 'markdown',
            'features': [
                'Text extraction',
                'Table conversion',
                'Image references',
                'Formatting preservation',
                'Metadata extraction'
            ]
        }
    
    @staticmethod
    def is_docx_file(file_path: Union[str, Path]) -> bool:
        """
        Check if a file is a DOCX file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file appears to be a DOCX file
        """
        file_path = Path(file_path)
        return file_path.suffix.lower() == '.docx'
    
    @staticmethod
    def is_available() -> bool:
        """
        Check if the converter is available (MarkItDown is installed).
        
        Returns:
            True if the converter can be used
        """
        return True

    def convert_and_split(self, 
                         file_path: Union[str, Path],
                         split_delimiter: str = r'\\\*\\\*\\\*',
                         fallback_chunk_size: int = 2000,
                         save_chunks: bool = False,
                         output_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Convert DOCX to Markdown and split into chunks in one operation.
        
        Args:
            file_path: Path to the DOCX file
            split_delimiter: Delimiter pattern for splitting
            fallback_chunk_size: Size for fallback chunking
            save_chunks: Whether to save individual chunks to files
            output_dir: Directory to save chunks (if save_chunks=True)
            
        Returns:
            Dictionary with conversion and split results
        """
        # First convert to markdown
        conversion_result = self.convert_file(file_path)
        
        if not conversion_result.success:
            return {
                'conversion_success': False,
                'split_success': False,
                'conversion_result': conversion_result,
                'error_message': conversion_result.error_message
            }
        
        # Then split the markdown content
        splitter = MarkdownTextSplitter(
            primary_delimiter=split_delimiter,
            fallback_chunk_size=fallback_chunk_size,
            verbose=self.verbose
        )
        
        split_result = splitter.split_text(conversion_result.markdown_content)
        
        # Save chunks if requested
        if save_chunks and output_dir and split_result.success:
            splitter.save_chunks(split_result, output_dir)
        
        return {
            'conversion_success': True,
            'split_success': split_result.success,
            'conversion_result': conversion_result,
            'split_result': split_result,
            'chunks': split_result.chunks if split_result.success else None,
            'structure_map': split_result.structure_map if split_result.success else None,
            'total_chunks': len(split_result.chunks) if split_result.success else 0,
            'split_summary': splitter.get_split_summary(split_result)
        }
